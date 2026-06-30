"""
Module dùng chung cho Paper 2 — Reliability & Calibration của Quantum Kernel IDS.

Mục tiêu: tái dùng CHÍNH XÁC các hàm calibration đã dùng trong
`notebooks/c5_confidence_calibration_multirun.ipynb` để mọi baseline mới
(RandomForest, XGBoost, MLP) được đo bằng đúng phương pháp như QSVM cũ —
đảm bảo so sánh apples-to-apples.

KHÔNG sửa code cũ; đây là file mới, độc lập.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    auc,
    average_precision_score,
    brier_score_loss,
    f1_score,
    roc_curve,
)

# ---------------------------------------------------------------------------
# Hằng số — giữ trùng khít với C5 multirun để số liệu so sánh được
# ---------------------------------------------------------------------------

ANGLE_MAX = np.pi
N_BINS_FULL = 10          # số bin ECE trên toàn tập
N_BINS_RARE = 5           # số bin ECE trên nhóm rare (ít mẫu)
RARE_GROUPS = ["U2R", "R2L"]
GROUP_ORDER = ["Normal", "DoS", "Probe", "U2R", "R2L"]
LABEL_COLS = ["label", "label_binary", "label_multiclass", "attack_category"]
RANDOM_STATE = 42


# ---------------------------------------------------------------------------
# Tải artifact pipeline giảm chiều (fit-only-on-train đã lưu sẵn)
# ---------------------------------------------------------------------------

def load_pipeline_artifacts(models_dir, data_dir):
    """Tải selector(K=20), PCA(4), scaler[0,π] và danh sách 122 feature chuẩn."""
    models_dir = Path(models_dir)
    data_dir = Path(data_dir)
    selector = joblib.load(models_dir / "feature_selector_k20.joblib")
    pca = joblib.load(models_dir / "pca_4components.joblib")
    scaler = joblib.load(models_dir / "scaler_minmax_pi.joblib")
    feat_cols = pd.read_csv(data_dir / "feature_columns.csv")["feature"].tolist()
    return selector, pca, scaler, feat_cols


def transform_pipeline(df, feat_cols, selector, pca, scaler):
    """Raw → SelectKBest → PCA → MinMax[0,π]. CHỈ transform, không fit (zero-leakage)."""
    X_raw = df[feat_cols].to_numpy(dtype=np.float32)
    X_sel = selector.transform(X_raw)
    X_pca = pca.transform(X_sel)
    return np.clip(scaler.transform(X_pca), 0, ANGLE_MAX).astype(np.float64)


# ---------------------------------------------------------------------------
# Platt scaling — giống hệt C5 (fit độc quyền trên train, áp dụng test)
# ---------------------------------------------------------------------------

class PlattScaler:
    """Ánh xạ score quyết định → P(y=1|f) qua sigmoid logistic, fit trên train."""

    def __init__(self, C=1e10):
        self.lr = LogisticRegression(C=C, solver="lbfgs", max_iter=2000, random_state=42)

    def fit(self, scores, y):
        self.lr.fit(np.asarray(scores).reshape(-1, 1), y)
        return self, float(self.lr.coef_[0][0]), float(self.lr.intercept_[0])

    def predict_proba(self, scores):
        return self.lr.predict_proba(np.asarray(scores).reshape(-1, 1))[:, 1]


# ---------------------------------------------------------------------------
# Calibration — equal-frequency binning + ECE/MCE (trích nguyên từ C5)
# ---------------------------------------------------------------------------

def adaptive_calibration_curve(y_true, y_prob, n_bins=10):
    """Binning theo tần suất bằng nhau — tránh bin rỗng cho nhóm hiếm U2R/R2L."""
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    n = len(y_prob)
    sorted_idx = np.argsort(y_prob)
    y_prob_sorted = y_prob[sorted_idx]
    y_true_sorted = y_true[sorted_idx]
    bin_size = max(n // n_bins, 1)
    mean_conf, frac_pos, bin_sizes = [], [], []
    for i in range(n_bins):
        start = i * bin_size
        end = (i + 1) * bin_size if i < n_bins - 1 else n
        if start >= n:
            break
        b_true = y_true_sorted[start:end]
        b_prob = y_prob_sorted[start:end]
        if len(b_true) == 0:
            continue
        mean_conf.append(float(np.mean(b_prob)))
        frac_pos.append(float(np.mean(b_true)))
        bin_sizes.append(len(b_true))
    return np.array(mean_conf), np.array(frac_pos), np.array(bin_sizes)


def compute_ece_mce(y_true, y_prob, n_bins=10):
    """ECE (trung bình có trọng số) và MCE (sai lệch tối đa) — định nghĩa như C5."""
    mc, fp, bs = adaptive_calibration_curve(y_true, y_prob, n_bins)
    n = len(y_true)
    if len(mc) == 0:
        return float("nan"), float("nan")
    ece = float(np.sum(bs / n * np.abs(fp - mc)))
    mce = float(np.max(np.abs(fp - mc)))
    return ece, mce


def cohens_d(a, b):
    """Cohen's d với pooled std. d>0 ⇒ mean(a)>mean(b)."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    pooled = np.sqrt(((len(a) - 1) * a.std(ddof=1) ** 2 + (len(b) - 1) * b.std(ddof=1) ** 2)
                     / (len(a) + len(b) - 2))
    if pooled == 0:
        return float("nan")
    return float((a.mean() - b.mean()) / pooled)


# ---------------------------------------------------------------------------
# Lấy score thống nhất cho mọi loại model rồi đưa vào Platt
# ---------------------------------------------------------------------------

def get_decision_scores(model, X):
    """Trả về score 1 chiều để đưa vào Platt.

    - Model có `decision_function` (SVM/QSVM): dùng trực tiếp.
    - Model chỉ có `predict_proba` (RF/XGB/MLP): dùng logit của P(y=1) làm score
      (đơn điệu, tương đương về xếp hạng, phù hợp để Platt hiệu chỉnh tiếp).
    """
    if hasattr(model, "decision_function"):
        s = model.decision_function(X)
        return np.asarray(s, dtype=np.float64).ravel()
    p = model.predict_proba(X)[:, 1]
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


# ---------------------------------------------------------------------------
# Tập metric độ tin cậy cho 1 model trên 1 split
# ---------------------------------------------------------------------------

def reliability_metrics(model, X_train, y_train, X_test, y_test, rare_mask):
    """Tính F1, Acc, ECE/Brier (full & rare), AUC-PR, AUC-ROC sau Platt scaling.

    Platt được fit trên score của train (zero-leakage) rồi áp dụng cho test —
    đúng protocol C5 để mọi model được đối xử như nhau.
    """
    y_pred = model.predict(X_test)
    s_train = get_decision_scores(model, X_train)
    s_test = get_decision_scores(model, X_test)

    scl, A, B = PlattScaler().fit(s_train, y_train)
    prob = scl.predict_proba(s_test)

    ece_full, mce_full = compute_ece_mce(y_test, prob, N_BINS_FULL)
    if rare_mask.sum() > 1:
        ece_rare, mce_rare = compute_ece_mce(y_test[rare_mask], prob[rare_mask], N_BINS_RARE)
        brier_rare = float(brier_score_loss(y_test[rare_mask], prob[rare_mask]))
    else:
        ece_rare, mce_rare, brier_rare = float("nan"), float("nan"), float("nan")

    fpr, tpr, _ = roc_curve(y_test, prob)
    return {
        "f1": float(f1_score(y_test, y_pred)),
        "acc": float(accuracy_score(y_test, y_pred)),
        "ece_full": ece_full,
        "mce_full": mce_full,
        "ece_rare": ece_rare,
        "mce_rare": mce_rare,
        "brier_full": float(brier_score_loss(y_test, prob)),
        "brier_rare": brier_rare,
        "auc_roc": float(auc(fpr, tpr)),
        "auc_pr": float(average_precision_score(y_test, prob)),
        "platt_A": round(A, 5),
        "platt_B": round(B, 5),
    }


# ---------------------------------------------------------------------------
# Factory các baseline ML/DL mới
# ---------------------------------------------------------------------------

def make_ml_dl_models(random_state=RANDOM_STATE):
    """Tạo dict các baseline mới: RandomForest, XGBoost, MLP (neural net)."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.neural_network import MLPClassifier

    models = {
        "RandomForest": RandomForestClassifier(
            n_estimators=300, max_depth=None, n_jobs=-1, random_state=random_state,
        ),
        "MLP": MLPClassifier(
            hidden_layer_sizes=(64, 32), activation="relu", alpha=1e-4,
            max_iter=500, random_state=random_state,
        ),
    }
    try:
        from xgboost import XGBClassifier

        models["XGBoost"] = XGBClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.1,
            subsample=0.9, colsample_bytree=0.9, eval_metric="logloss",
            random_state=random_state, n_jobs=-1,
        )
    except ImportError:
        pass
    return models
