"""
Module đặc trưng cho Contribution 1 (C1): Tối ưu hóa nhúng lượng tử có ràng buộc phần cứng.

Gộp logic từ hai notebook:
  - notebooks/selectkbest_nslkdd.ipynb  →  SelectKBestOptimizer
  - notebooks/pca.ipynb                 →  ParetoOptimalPCA

Pipeline hoàn chỉnh:
  NSL-KDD (122D) → SelectKBest (K_FINAL D) → PCA Pareto (4D) → MinMax[0, π]

Quy tắc zero-leakage bắt buộc:
  selector.fit_transform(X_train, y_train)   ← chỉ fit trên train
  selector.transform(X_test)                 ← KHÔNG fit trên test
  pca.fit_transform(X_train_sel)             ← eigenvectors từ train
  pca.transform(X_test_sel)                  ← KHÔNG fit trên test
  scaler.fit_transform(X_train_pca)          ← min/max từ train
  np.clip(scaler.transform(X_test_pca), 0, π) ← clip OOD
"""

import sys
from pathlib import Path

# -- Cho phép import config từ thư mục gốc khi chạy từ src/ --
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import joblib

from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score

from config import (
    DATA_PROCESSED_DIR,
    MODELS_DIR,
    NSLKDD_TRAIN_CLEAN,
    NSLKDD_TEST_CLEAN,
    FEATURE_SELECTOR_PATHS,
    PCA_MODEL_PATH,
    SCALER_PATH,
    LABEL_COLS,
    RANDOM_STATE,
    K_CANDIDATES,
    K_FINAL,
    PLATEAU_THRESHOLD,
    N_CV_SUBSAMPLE,
    N_CV_FOLDS,
    VARIANCE_THRESHOLD,
    N_RANGE,
    GRID_RESOLUTION,
    N_BOOTSTRAP,
    BOOTSTRAP_SAMPLE,
    ANGLE_MAX,
    N_ABL,
    N_QUBITS,
    ZZ_REPS,
)


# ════════════════════════════════════════════════════════════
# 1. HÀM TIỆN ÍCH CHUNG
# ════════════════════════════════════════════════════════════

def get_feature_columns(df: pd.DataFrame) -> list[str]:
    """Trả về danh sách cột đặc trưng (loại bỏ tất cả cột nhãn)."""
    return [c for c in df.columns if c not in LABEL_COLS]


def stratified_sample_for_cv(
    df: pd.DataFrame,
    n_samples: int = N_CV_SUBSAMPLE,
    rare_categories: tuple = ("U2R", "R2L"),
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """
    Lấy mẫu phân tầng cho CV: giữ TOÀN BỘ rare categories, phần còn lại
    sample theo tỉ lệ gốc. KHÔNG oversample để tránh duplicate leakage giữa các fold.

    Tham số:
        df             : DataFrame đã có cột 'attack_category' và 'label_binary'
        n_samples      : Tổng số mẫu cần lấy
        rare_categories: Nhóm tấn công hiếm cần giữ toàn bộ (U2R, R2L < 1%)
        random_state   : Seed cho tính tái lập

    Trả về:
        DataFrame đã sample, reset_index.
    """
    rng = np.random.RandomState(random_state)
    rare_df = df[df["attack_category"].isin(rare_categories)].copy()
    other_df = df[~df["attack_category"].isin(rare_categories)].copy()
    n_rare = len(rare_df)

    # Nếu rare đã đủ n_samples thì chỉ lấy đủ số
    if n_rare >= n_samples:
        return rare_df.sample(
            n=n_samples, replace=False, random_state=random_state
        ).reset_index(drop=True)

    remaining = n_samples - n_rare
    counts = other_df["attack_category"].value_counts().sort_index()
    weights = counts / counts.sum()
    raw_alloc = weights * remaining
    alloc = np.floor(raw_alloc).astype(int)

    # Phân phối phần dư (làm tròn)
    remainder = remaining - alloc.sum()
    frac_part = (raw_alloc - alloc).sort_values(ascending=False)
    for cat in frac_part.index[:remainder]:
        alloc.loc[cat] += 1

    parts = [rare_df]
    for cat, n_take in alloc.items():
        pool = other_df[other_df["attack_category"] == cat]
        n_actual = min(n_take, len(pool))
        if n_actual > 0:
            parts.append(
                pool.sample(n=n_actual, replace=False,
                            random_state=rng.randint(1_000_000))
            )

    return (
        pd.concat(parts)
        .sample(frac=1, random_state=random_state)
        .reset_index(drop=True)
    )


# ════════════════════════════════════════════════════════════
# 2. SELECTKBEST OPTIMIZATION  (từ selectkbest_nslkdd.ipynb)
# ════════════════════════════════════════════════════════════

class SelectKBestOptimizer:
    """
    Tối ưu hóa K cho SelectKBest(f_classif) bằng CV elbow criterion.

    Thuật toán:
      1. Tạo subset CV phân tầng (đảm bảo U2R/R2L có mặt).
      2. Với mỗi K trong K_CANDIDATES: chạy N_CV_FOLDS-fold CV với proxy SVM-linear.
      3. Elbow criterion: chọn K nhỏ nhất mà F1 ≥ (F1_max - PLATEAU_THRESHOLD).
      4. Fit SelectKBest trên TOÀN BỘ tập train (không phải subset CV).

    Lưu ý:
      SVM-linear làm proxy để chọn K (nhanh hơn QSVM ~1000x).
      f_classif nhất quán với selector cuối cùng → tránh selection bias.
    """

    def __init__(
        self,
        k_candidates: list[int] = None,
        plateau_threshold: float = PLATEAU_THRESHOLD,
        n_cv_subsample: int = N_CV_SUBSAMPLE,
        n_cv_folds: int = N_CV_FOLDS,
        random_state: int = RANDOM_STATE,
    ):
        self.k_candidates = k_candidates or K_CANDIDATES
        self.plateau_threshold = plateau_threshold
        self.n_cv_subsample = n_cv_subsample
        self.n_cv_folds = n_cv_folds
        self.random_state = random_state

        # Kết quả sau khi fit
        self.k_final_: int | None = None
        self.k_optimal_: int | None = None
        self.cv_results_: pd.DataFrame | None = None
        self.selector_: SelectKBest | None = None
        self.selected_features_: list[str] | None = None

    def _run_cv(
        self,
        X_cv: np.ndarray,
        y_cv: np.ndarray,
        y_cv_multiclass: np.ndarray,
    ) -> pd.DataFrame:
        """
        Chạy cross-validation cho từng K, trả về DataFrame kết quả.
        Stratify theo multiclass để đảm bảo U2R/R2L phân đều giữa các fold.
        """
        min_class = pd.Series(y_cv_multiclass).value_counts().min()
        n_splits = min(self.n_cv_folds, int(min_class))
        cv_fold = StratifiedKFold(
            n_splits=n_splits, shuffle=True, random_state=self.random_state
        )
        cv_splits = list(cv_fold.split(X_cv, y_cv_multiclass))

        # Lọc K không vượt quá số features thực tế
        valid_ks = [k for k in self.k_candidates if k <= X_cv.shape[1]]

        records = []
        for k in valid_ks:
            pipe = Pipeline([
                ("sel", SelectKBest(score_func=f_classif, k=k)),
                ("clf", SVC(kernel="linear", C=1.0)),
            ])
            np.random.seed(self.random_state)
            scores = cross_val_score(
                pipe, X_cv, y_cv,
                cv=cv_splits,
                scoring="f1_macro",
                n_jobs=-1,
            )
            records.append({
                "K": k,
                "f1_mean": scores.mean(),
                "f1_std": scores.std(),
            })

        return pd.DataFrame(records)

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        train_df: pd.DataFrame,
        feature_cols: list[str],
    ) -> "SelectKBestOptimizer":
        """
        Tìm K_FINAL bằng elbow criterion, sau đó fit selector trên toàn bộ train.

        Tham số:
            X_train     : Ma trận đặc trưng train (đã MinMaxScale [0,1])
            y_train     : Nhãn nhị phân train
            train_df    : DataFrame gốc để lấy cột 'attack_category' cho stratified CV
            feature_cols: Danh sách tên features theo thứ tự cột trong X_train

        Trả về:
            self (để chain nếu cần)
        """
        # -- Tạo subset CV phân tầng --
        cv_subset = stratified_sample_for_cv(
            train_df,
            n_samples=self.n_cv_subsample,
            random_state=self.random_state,
        )
        X_cv = cv_subset[feature_cols].to_numpy(dtype=np.float32)
        y_cv = cv_subset["label_binary"].to_numpy(dtype=np.int64)
        y_cv_multiclass = cv_subset["attack_category"].values

        # -- Chạy CV --
        self.cv_results_ = self._run_cv(X_cv, y_cv, y_cv_multiclass)

        # -- Elbow criterion --
        best_f1 = self.cv_results_["f1_mean"].max()
        self.k_optimal_ = int(
            self.cv_results_.loc[self.cv_results_["f1_mean"].idxmax(), "K"]
        )
        plateau_mask = self.cv_results_["f1_mean"] >= (
            best_f1 - self.plateau_threshold
        )
        self.k_final_ = int(
            self.cv_results_.loc[plateau_mask, "K"].min()
        )

        # -- Fit SelectKBest trên TOÀN BỘ train (không phải subset CV) --
        np.random.seed(self.random_state)
        self.selector_ = SelectKBest(score_func=f_classif, k=self.k_final_)
        self.selector_.fit(X_train, y_train)

        # -- Lưu tên features được chọn --
        mask = self.selector_.get_support()
        self.selected_features_ = [
            feature_cols[i] for i in range(len(feature_cols)) if mask[i]
        ]

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Áp dụng selector đã fit để giảm chiều.
        KHÔNG fit lại — tuân thủ zero-leakage.
        """
        if self.selector_ is None:
            raise RuntimeError("Cần gọi fit() trước khi transform().")
        return self.selector_.transform(X)

    def fit_transform(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        train_df: pd.DataFrame,
        feature_cols: list[str],
    ) -> np.ndarray:
        """
        Fit rồi transform X_train. Shortcut tiện ích.
        Trả về X_train đã giảm chiều.
        """
        self.fit(X_train, y_train, train_df, feature_cols)
        return self.selector_.transform(X_train)

    def get_score_dataframe(self, feature_cols: list[str]) -> pd.DataFrame:
        """
        Trả về DataFrame chứa f_score và f_pvalue của TẤT CẢ features,
        sắp xếp theo f_score giảm dần.
        """
        if self.selector_ is None:
            raise RuntimeError("Cần gọi fit() trước.")
        return (
            pd.DataFrame({
                "feature": feature_cols,
                "f_score": self.selector_.scores_,
                "f_pvalue": self.selector_.pvalues_,
            })
            .sort_values("f_score", ascending=False)
            .reset_index(drop=True)
        )


def run_selectkbest_ablation(
    train_df: pd.DataFrame,
    feature_cols: list[str],
    k_final: int,
    n_abl: int = N_ABL,
    n_pca_components: int = N_QUBITS,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """
    Ablation study so sánh 5 pipeline để chứng minh SelectKBest + PCA tốt nhất.

    Các cấu hình so sánh:
      (1) Baseline: toàn bộ features
      (2) PCA 95% variance (ngưỡng cố định)
      (3) SelectKBest only (K=k_final)
      (4) PCA only (n_pca_components D) — same-dimension baseline
      (5) SelectKBest (K=k_final) + PCA (n_pca_components D)  [C1 pipeline]

    Zero-leakage được đảm bảo bởi sklearn.Pipeline: fit/transform theo fold.

    Tham số:
        train_df          : DataFrame train đã có 'attack_category', 'label_binary'
        feature_cols      : Danh sách tên features
        k_final           : K đã chọn từ SelectKBestOptimizer
        n_abl             : Số mẫu cho ablation subset
        n_pca_components  : Số PC (= số qubit, hard constraint)
        random_state      : Seed

    Trả về:
        DataFrame với cột: Config, F1-macro, Std
    """
    abl_sub = stratified_sample_for_cv(
        train_df, n_samples=n_abl, random_state=random_state
    )
    X_abl = abl_sub[feature_cols].to_numpy(dtype=np.float32)
    y_abl = abl_sub["label_binary"].to_numpy(dtype=np.int64)

    cv5 = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)

    ablation_configs = [
        (
            "(1) Baseline: tất cả features",
            Pipeline([("clf", SVC(kernel="linear", C=1.0,
                                  random_state=random_state))]),
        ),
        (
            "(2) PCA 95% variance — ngưỡng cố định",
            Pipeline([
                ("pca", PCA(n_components=0.95, random_state=random_state)),
                ("clf", SVC(kernel="linear", C=1.0, random_state=random_state)),
            ]),
        ),
        (
            f"(3) SelectKBest only (K={k_final})",
            Pipeline([
                ("sel", SelectKBest(score_func=f_classif, k=k_final)),
                ("clf", SVC(kernel="linear", C=1.0, random_state=random_state)),
            ]),
        ),
        (
            f"(4) PCA only ({n_pca_components}D) — không có SelectKBest",
            Pipeline([
                ("pca", PCA(n_components=n_pca_components,
                            random_state=random_state)),
                ("clf", SVC(kernel="linear", C=1.0, random_state=random_state)),
            ]),
        ),
        (
            f"(5) SelectKBest (K={k_final}) + PCA ({n_pca_components}D)  [C1 pipeline]",
            Pipeline([
                ("sel", SelectKBest(score_func=f_classif, k=k_final)),
                ("pca", PCA(n_components=n_pca_components,
                            random_state=random_state)),
                ("clf", SVC(kernel="linear", C=1.0, random_state=random_state)),
            ]),
        ),
    ]

    records = []
    for name, pipe in ablation_configs:
        np.random.seed(random_state)
        scores = cross_val_score(
            pipe, X_abl, y_abl, cv=cv5, scoring="f1_macro", n_jobs=-1
        )
        records.append({
            "Config": name,
            "F1-macro": scores.mean(),
            "Std": scores.std(),
        })

    return pd.DataFrame(records)


# ════════════════════════════════════════════════════════════
# 3. HÀM TIỆN ÍCH CHO PARETO PCA  (từ pca.ipynb)
# ════════════════════════════════════════════════════════════

def calculate_fisher_score(
    X_pca: np.ndarray,
    y: np.ndarray,
) -> tuple[np.ndarray, float]:
    """
    Tính Fisher Score cho từng PC riêng lẻ — hỗ trợ binary và multi-class.

    Công thức:
        S_k = S_B_k / (S_W_k + ε)
        Trong đó S_B là between-class scatter, S_W là within-class scatter.

    Tham số:
        X_pca : Ma trận PCA shape (N, n_components)
        y     : Nhãn (binary hoặc multiclass)

    Trả về:
        (scores, mean_score) — scores.shape = (n_components,)
    """
    labels = np.unique(y)
    if len(labels) < 2:
        raise ValueError(
            f"Cần ít nhất 2 lớp để tính Fisher Score, nhận được {len(labels)}."
        )

    mu_all = np.mean(X_pca, axis=0)
    S_B = np.zeros(X_pca.shape[1])
    S_W = np.zeros(X_pca.shape[1])

    for lbl in labels:
        Xk = X_pca[y == lbl]
        nk = len(Xk)
        mu_k = np.mean(Xk, axis=0)
        S_B += nk * (mu_k - mu_all) ** 2
        S_W += nk * np.var(Xk, axis=0)

    scores = S_B / (S_W + 1e-8)
    return scores, float(np.mean(scores))


def quantum_hardware_cost(
    n: int,
    reps: int = ZZ_REPS,
    normalize_max: int = 10,
) -> float:
    """
    Chi phí phần cứng ZZFeatureMap thực tế (chuẩn hóa):
      - 1-qubit gates : n * reps           [O(n)]
      - 2-qubit gates : n*(n-1)/2 * reps   [O(n²)] — penalty ×5

    Lý do penalty ×5: Error rate cổng 2-qubit cao hơn 1-qubit ~5-10× trên NISQ hardware
    (IBM Quantum / Google Sycamore calibration data).

    Tham số:
        n             : Số qubit
        reps          : Số lần lặp circuit
        normalize_max : n_max để chuẩn hóa về [0, 1]

    Trả về:
        Chi phí chuẩn hóa trong [0, 1].
    """
    n1q = n * reps
    n2q = (n * (n - 1) // 2) * reps
    raw = n1q + 5 * n2q

    n1q_max = normalize_max * reps
    n2q_max = (normalize_max * (normalize_max - 1) // 2) * reps
    raw_max = n1q_max + 5 * n2q_max
    return raw / raw_max


def simplex_grid(resolution: int) -> np.ndarray:
    """
    Sinh các điểm (α, β, γ) đều trên simplex α + β + γ = 1.

    Tham số:
        resolution : Độ phân giải lưới (số bước trên mỗi cạnh)

    Trả về:
        Array shape (N_points, 3).
    """
    points = []
    for i in range(resolution + 1):
        for j in range(resolution + 1 - i):
            k = resolution - i - j
            points.append((i / resolution, j / resolution, k / resolution))
    return np.array(points)


def find_optimal_weights_grid(
    candidates: list[dict],
    grid_resolution: int = GRID_RESOLUTION,
) -> tuple[dict, list[dict], float]:
    """
    Grid search trên simplex để tìm trọng số (α, β, γ) tối ưu hóa DBI.

    Hàm mục tiêu: F(n) = α·V(n) + β·S_norm(n) − γ·Q(n)
    Metric đánh giá: Davies-Bouldin Index (O(k·n), nhanh hơn Silhouette ~100×).

    Ràng buộc tìm kiếm: α ≥ 0.05, β ≥ 0.05, γ ≤ 0.5 (tránh degenerate weights).

    Tham số:
        candidates      : Danh sách dict chứa 'V_n', 'S_norm', 'Q_n', 'DBI', 'n'
        grid_resolution : Độ phân giải simplex grid

    Trả về:
        (best_weights, weight_log, best_dbi)
        best_weights: dict {'alpha', 'beta', 'gamma'}
        weight_log  : list[dict] — toàn bộ lịch sử grid search
        best_dbi    : float — DBI nhỏ nhất tìm được
    """
    grid = simplex_grid(grid_resolution)
    best_dbi = np.inf
    best_weights = None
    weight_log = []

    for alpha, beta, gamma in grid:
        # Tránh degenerate weights
        if alpha < 0.05 or beta < 0.05 or gamma > 0.5:
            continue

        f_scores = [
            alpha * r["V_n"] + beta * r["S_norm"] - gamma * r["Q_n"]
            for r in candidates
        ]
        best_idx = int(np.argmax(f_scores))
        best_n = candidates[best_idx]["n"]
        dbi = candidates[best_idx]["DBI"]

        weight_log.append({
            "alpha": alpha,
            "beta": beta,
            "gamma": gamma,
            "best_n": best_n,
            "dbi": dbi,
            "f_score": f_scores[best_idx],
        })

        if dbi < best_dbi:
            best_dbi = dbi
            best_weights = {"alpha": alpha, "beta": beta, "gamma": gamma}

    return best_weights, weight_log, best_dbi


def compute_pareto_frontier(candidates: list[dict]) -> list[dict]:
    """
    Tính Pareto frontier trên ba mục tiêu:
      maximize V(n), maximize S_norm(n), minimize Q(n).

    Một điểm bị dominated nếu tồn tại điểm khác tốt hơn hoặc bằng
    trên cả ba mục tiêu và tốt hơn ít nhất một.

    Tham số:
        candidates: Danh sách dict chứa 'V_n', 'S_norm', 'Q_n', 'n'

    Trả về:
        Danh sách dict các điểm Pareto-optimal.
    """
    pareto = []
    for i, ri in enumerate(candidates):
        dominated = False
        for j, rj in enumerate(candidates):
            if i == j:
                continue
            geq = (
                rj["V_n"] >= ri["V_n"]
                and rj["S_norm"] >= ri["S_norm"]
                and rj["Q_n"] <= ri["Q_n"]
            )
            strict = (
                rj["V_n"] > ri["V_n"]
                or rj["S_norm"] > ri["S_norm"]
                or rj["Q_n"] < ri["Q_n"]
            )
            if geq and strict:
                dominated = True
                break
        if not dominated:
            pareto.append(ri)
    return pareto


def bootstrap_metrics(
    results_cands: list[dict],
    y: np.ndarray,
    s_min_g: float,
    s_denom: float,
    alpha: float,
    gamma: float,
    n_bootstrap: int = N_BOOTSTRAP,
    sample_size: int = BOOTSTRAP_SAMPLE,
    seed: int = RANDOM_STATE,
) -> dict[int, dict]:
    """
    Tính Bootstrap 95% Confidence Intervals cho F(n) và Silhouette.

    Mỗi iteration: resample y và các X_pca tương ứng, tính lại F(n) và Silhouette.
    Dùng percentile bootstrap (2.5%, 97.5%).

    Tham số:
        results_cands : Candidates (danh sách dict từ ParetoOptimalPCA)
        y             : Nhãn train (binary)
        s_min_g, s_denom: Tham số chuẩn hóa S_norm (toàn cục)
        alpha, gamma  : Trọng số tối ưu từ grid search (beta = 1 - alpha - gamma)
        n_bootstrap   : Số lần bootstrap
        sample_size   : Kích thước mẫu mỗi bootstrap
        seed          : Seed

    Trả về:
        Dict mapping n → dict chứa 'F_mean', 'F_ci', 'F_std',
                                    'sil_mean', 'sil_ci', 'sil_std'
    """
    # Tính beta từ alpha và gamma (vì alpha + beta + gamma = 1)
    beta = 1.0 - alpha - gamma

    rng = np.random.default_rng(seed)
    N = len(y)
    bs_results = {r["n"]: {"F_vals": [], "sil_vals": []} for r in results_cands}

    for i in range(n_bootstrap):
        idx = rng.choice(N, size=min(sample_size, N), replace=True)
        y_bs = y[idx]

        for r in results_cands:
            X_bs = r["X_pca"][idx]
            _, S_bs = calculate_fisher_score(X_bs, y_bs)
            S_norm_bs = (S_bs - s_min_g) / s_denom
            F_bs = alpha * r["V_n"] + beta * S_norm_bs - gamma * r["Q_n"]
            bs_results[r["n"]]["F_vals"].append(F_bs)

            try:
                sil_bs = silhouette_score(
                    X_bs, y_bs,
                    sample_size=min(1000, len(y_bs)),
                    random_state=int(i),
                )
                bs_results[r["n"]]["sil_vals"].append(sil_bs)
            except Exception:
                pass  # Bỏ qua nếu chỉ có 1 lớp trong bootstrap sample

    ci_results = {}
    for n_val, data in bs_results.items():
        f_arr = np.array(data["F_vals"])
        s_arr = np.array(data["sil_vals"]) if data["sil_vals"] else np.array([np.nan])
        ci_results[n_val] = {
            "F_mean": float(np.mean(f_arr)),
            "F_ci": (float(np.percentile(f_arr, 2.5)),
                     float(np.percentile(f_arr, 97.5))),
            "F_std": float(np.std(f_arr)),
            "sil_mean": float(np.mean(s_arr)),
            "sil_ci": (float(np.nanpercentile(s_arr, 2.5)),
                       float(np.nanpercentile(s_arr, 97.5))),
            "sil_std": float(np.nanstd(s_arr)),
        }

    return ci_results


# ════════════════════════════════════════════════════════════
# 4. PARETO OPTIMAL PCA  (từ pca.ipynb)
# ════════════════════════════════════════════════════════════

class ParetoOptimalPCA:
    """
    Tối ưu hóa PCA đa mục tiêu có ràng buộc phần cứng lượng tử (C1).

    Hàm mục tiêu: F(n) = α·V(n) + β·S_norm(n) − γ·Q(n)
    Ràng buộc cứng: V(n) ≥ VARIANCE_THRESHOLD

    Quy trình:
      1. Với mỗi n trong N_RANGE: fit PCA trên train, tính V(n), S(n), Q(n), DBI.
      2. Loại các n không thỏa V(n) ≥ variance_threshold (hard constraint).
      3. Grid search trên simplex để tìm (α, β, γ) tối thiểu hóa DBI của n được chọn.
      4. Tính F(n) cho candidates, chọn n có F(n) cao nhất.
      5. Fit PCA và MinMaxScaler([0, π]) cuối cùng trên train. Transform test (clip OOD).
      6. Bootstrap CI để định lượng độ tin cậy.

    Zero-leakage:
      Mọi PCA và scaler đều chỉ fit trên X_train. Test data chỉ được transform.
    """

    def __init__(
        self,
        variance_threshold: float = VARIANCE_THRESHOLD,
        n_range: range = N_RANGE,
        grid_resolution: int = GRID_RESOLUTION,
        n_bootstrap: int = N_BOOTSTRAP,
        bootstrap_sample: int = BOOTSTRAP_SAMPLE,
        angle_max: float = ANGLE_MAX,
        reps: int = ZZ_REPS,
        random_state: int = RANDOM_STATE,
    ):
        self.variance_threshold = variance_threshold
        self.n_range = n_range
        self.grid_resolution = grid_resolution
        self.n_bootstrap = n_bootstrap
        self.bootstrap_sample = bootstrap_sample
        self.angle_max = angle_max
        self.reps = reps
        self.random_state = random_state

        # Kết quả sau fit
        self.n_chosen_: int | None = None
        self.pca_: PCA | None = None
        self.scaler_: MinMaxScaler | None = None
        self.results_all_: list[dict] | None = None
        self.results_candidates_: list[dict] | None = None
        self.pareto_points_: list[dict] | None = None
        self.best_weights_: dict | None = None
        self.ci_: dict | None = None
        self.weight_log_: list[dict] | None = None

    def _collect_raw_metrics(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
    ) -> list[dict]:
        """
        Thu thập chỉ số thô cho toàn bộ N_RANGE.
        Mỗi PCA được fit trên X_train (zero-leakage).
        """
        results = []
        for n in self.n_range:
            pca_tmp = PCA(n_components=n, random_state=self.random_state)
            # Fit trên train ONLY
            X_pca = pca_tmp.fit_transform(X_train)
            V_n = float(np.sum(pca_tmp.explained_variance_ratio_))

            per_pc_scores, S_n = calculate_fisher_score(X_pca, y_train)
            Q_n = quantum_hardware_cost(n, reps=self.reps)
            dbi = davies_bouldin_score(X_pca, y_train)
            passes = V_n >= self.variance_threshold

            results.append({
                "n": n,
                "V_n": V_n,
                "S_n": S_n,
                "per_pc_scores": per_pc_scores,
                "Q_n": Q_n,
                "DBI": dbi,
                "passes_hard": passes,
                "X_pca": X_pca,
                "pca_obj": pca_tmp,
            })

        return results

    def _normalize_scores(self, results_all: list[dict]) -> None:
        """
        Chuẩn hóa S_norm và DBI_norm toàn cục (inplace).
        S_norm: global min-max normalization.
        DBI_norm: 1 - normalized DBI (đảo chiều vì DBI thấp là tốt).
        """
        s_all = [r["S_n"] for r in results_all]
        s_min_g = min(s_all)
        s_max_g = max(s_all)
        s_denom = (s_max_g - s_min_g) if s_max_g > s_min_g else 1.0

        dbi_all = [r["DBI"] for r in results_all]
        dbi_min_g = min(dbi_all)
        dbi_max_g = max(dbi_all)
        dbi_denom = (dbi_max_g - dbi_min_g) if dbi_max_g > dbi_min_g else 1.0

        for r in results_all:
            r["S_norm"] = (r["S_n"] - s_min_g) / s_denom
            r["DBI_norm"] = 1.0 - (r["DBI"] - dbi_min_g) / dbi_denom

        # Lưu tham số chuẩn hóa để dùng trong bootstrap
        self._s_min_g = s_min_g
        self._s_denom = s_denom

    def fit(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
    ) -> "ParetoOptimalPCA":
        """
        Chạy toàn bộ pipeline Pareto PCA.

        Tham số:
            X_train : Ma trận train sau SelectKBest transform (zero-leakage đã đảm bảo)
            X_test  : Ma trận test sau SelectKBest transform
            y_train : Nhãn binary train

        Trả về:
            self
        """
        # Bước 1: Thu thập chỉ số thô
        self.results_all_ = self._collect_raw_metrics(X_train, y_train)

        # Bước 2: Chuẩn hóa scores
        self._normalize_scores(self.results_all_)

        # Bước 3: Lọc candidates (thỏa ràng buộc cứng)
        self.results_candidates_ = [
            r for r in self.results_all_ if r["passes_hard"]
        ]
        if not self.results_candidates_:
            raise ValueError(
                f"Không có n nào thỏa V(n) >= {self.variance_threshold:.0%}. "
                f"Thử giảm variance_threshold."
            )

        # Bước 4: Grid search tìm trọng số tối ưu
        self.best_weights_, self.weight_log_, best_dbi = find_optimal_weights_grid(
            self.results_candidates_,
            grid_resolution=self.grid_resolution,
        )
        alpha = self.best_weights_["alpha"]
        beta = self.best_weights_["beta"]
        gamma = self.best_weights_["gamma"]

        # Bước 5: Tính F(n) và chọn n tối ưu
        for r in self.results_candidates_:
            r["F_n"] = alpha * r["V_n"] + beta * r["S_norm"] - gamma * r["Q_n"]

        best_candidate = max(self.results_candidates_, key=lambda r: r["F_n"])
        self.n_chosen_ = best_candidate["n"]

        # Bước 6: Silhouette Score để validate (chạy 1 lần)
        for r in self.results_candidates_:
            r["silhouette"] = silhouette_score(
                r["X_pca"], y_train,
                sample_size=min(5000, len(y_train)),
                random_state=self.random_state,
            )

        # Bước 7: Pareto frontier
        self.pareto_points_ = compute_pareto_frontier(self.results_candidates_)

        # Bước 8: Bootstrap CI
        self.ci_ = bootstrap_metrics(
            self.results_candidates_,
            y_train,
            s_min_g=self._s_min_g,
            s_denom=self._s_denom,
            alpha=alpha,
            gamma=gamma,
            n_bootstrap=self.n_bootstrap,
            sample_size=self.bootstrap_sample,
            seed=self.random_state,
        )

        # Bước 9: Fit PCA cuối cùng trên train ONLY
        self.pca_ = PCA(n_components=self.n_chosen_, random_state=self.random_state)
        X_train_pca = self.pca_.fit_transform(X_train)    # fit trên train ONLY
        X_test_pca = self.pca_.transform(X_test)           # KHÔNG fit trên test

        # Bước 10: Fit MinMaxScaler([0, π]) trên train ONLY
        self.scaler_ = MinMaxScaler(feature_range=(0.0, self.angle_max))
        self._X_train_final = self.scaler_.fit_transform(X_train_pca)
        X_test_scaled = self.scaler_.transform(X_test_pca)
        self._X_test_final = np.clip(X_test_scaled, 0.0, self.angle_max)

        return self

    def get_train_data(self) -> np.ndarray:
        """Trả về X_train đã qua PCA + MinMax scale [0, π]."""
        if self._X_train_final is None:
            raise RuntimeError("Cần gọi fit() trước.")
        return self._X_train_final

    def get_test_data(self) -> np.ndarray:
        """Trả về X_test đã qua PCA + MinMax scale + clip OOD về [0, π]."""
        if self._X_test_final is None:
            raise RuntimeError("Cần gọi fit() trước.")
        return self._X_test_final

    def transform(
        self,
        X: np.ndarray,
        clip: bool = True,
    ) -> np.ndarray:
        """
        Áp dụng PCA và scaler đã fit để transform dữ liệu mới.
        KHÔNG fit lại — tuân thủ zero-leakage.

        Tham số:
            X    : Ma trận đầu vào (đã qua SelectKBest transform)
            clip : Nếu True, clip giá trị ngoài [0, angle_max]
        """
        if self.pca_ is None or self.scaler_ is None:
            raise RuntimeError("Cần gọi fit() trước khi transform().")
        X_pca = self.pca_.transform(X)
        X_scaled = self.scaler_.transform(X_pca)
        if clip:
            X_scaled = np.clip(X_scaled, 0.0, self.angle_max)
        return X_scaled

    def get_results_dataframe(self) -> pd.DataFrame:
        """
        Trả về DataFrame tóm tắt tất cả n trong N_RANGE với các chỉ số:
        n, V(n), S(n), S_norm, DBI, Q(n), Status, F(n).
        """
        if self.results_all_ is None:
            raise RuntimeError("Cần gọi fit() trước.")
        rows = []
        for r in self.results_all_:
            rows.append({
                "n": r["n"],
                "V(n)": r["V_n"],
                "S(n)": r["S_n"],
                "S_norm": r["S_norm"],
                "DBI": r["DBI"],
                "Q(n)": r["Q_n"],
                "Status": (
                    "candidate"
                    if r["passes_hard"]
                    else f"loai (V<{self.variance_threshold:.0%})"
                ),
                "F(n)": r.get("F_n", float("nan")),
            })
        return pd.DataFrame(rows)

    def get_spearman_pc_correlations(
        self,
        X_train_final: np.ndarray,
    ) -> pd.DataFrame:
        """
        Tính Spearman correlation giữa các PC trong không gian [0, π].
        Các cặp có |r| > 0.2 là tiền đề cho ZZFeatureMap (mã hóa tương tác cặp).

        Tham số:
            X_train_final : Ma trận train đã scale [0, π], shape (N, n_chosen)

        Trả về:
            DataFrame Spearman correlation (n×n).
        """
        if self.n_chosen_ is None:
            raise RuntimeError("Cần gọi fit() trước.")
        pc_cols = [f"PC{i + 1}" for i in range(self.n_chosen_)]
        pca_df = pd.DataFrame(X_train_final, columns=pc_cols)
        return pca_df.corr(method="spearman")


# ════════════════════════════════════════════════════════════
# 5. HÀM PIPELINE TỔNG HỢP
# ════════════════════════════════════════════════════════════

def run_c1_feature_pipeline(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    run_ablation: bool = True,
) -> dict:
    """
    Chạy toàn bộ C1 pipeline từ đầu đến cuối:
      train_df (đã OHE, MinMax [0,1])
      → SelectKBestOptimizer → ParetoOptimalPCA
      → X_train_final, X_test_final đã scale [0, π]

    Tham số:
        train_df     : DataFrame train sạch (đầu ra của preprocess.py)
        test_df      : DataFrame test sạch
        run_ablation : Nếu True, chạy ablation study (chậm hơn ~1-2 phút)

    Trả về:
        dict chứa:
          'X_train'        : np.ndarray shape (N_train, n_qubits)
          'X_test'         : np.ndarray shape (N_test, n_qubits)
          'y_train'        : np.ndarray nhãn binary train
          'y_test'         : np.ndarray nhãn binary test
          'selector'       : SelectKBest đã fit
          'pca'            : PCA đã fit
          'scaler'         : MinMaxScaler([0,π]) đã fit
          'k_final'        : int K đã chọn
          'n_chosen'       : int số qubit đã chọn
          'cv_results'     : DataFrame CV SelectKBest
          'ablation_df'    : DataFrame ablation (None nếu run_ablation=False)
          'pareto_results' : DataFrame tóm tắt Pareto PCA
          'ci'             : Bootstrap CI dict
          'optimizer'      : SelectKBestOptimizer object
          'pareto_pca'     : ParetoOptimalPCA object
    """
    feature_cols = get_feature_columns(train_df)

    X_train_raw = train_df[feature_cols].to_numpy(dtype=np.float32)
    X_test_raw = test_df[feature_cols].to_numpy(dtype=np.float32)
    y_train = train_df["label_binary"].to_numpy(dtype=np.int64)
    y_test = test_df["label_binary"].to_numpy(dtype=np.int64)

    # --- Bước 1: SelectKBest ---
    skb_optimizer = SelectKBestOptimizer(random_state=RANDOM_STATE)
    X_train_sel = skb_optimizer.fit_transform(
        X_train_raw, y_train, train_df, feature_cols
    )
    X_test_sel = skb_optimizer.transform(X_test_raw)
    k_final = skb_optimizer.k_final_

    # --- Ablation study (tuỳ chọn) ---
    ablation_df = None
    if run_ablation:
        ablation_df = run_selectkbest_ablation(
            train_df, feature_cols, k_final
        )

    # --- Bước 2: Pareto PCA ---
    pareto_pca = ParetoOptimalPCA(random_state=RANDOM_STATE)
    pareto_pca.fit(X_train_sel, X_test_sel, y_train)

    X_train_final = pareto_pca.get_train_data()
    X_test_final = pareto_pca.get_test_data()

    return {
        "X_train": X_train_final,
        "X_test": X_test_final,
        "y_train": y_train,
        "y_test": y_test,
        "selector": skb_optimizer.selector_,
        "pca": pareto_pca.pca_,
        "scaler": pareto_pca.scaler_,
        "k_final": k_final,
        "n_chosen": pareto_pca.n_chosen_,
        "cv_results": skb_optimizer.cv_results_,
        "ablation_df": ablation_df,
        "pareto_results": pareto_pca.get_results_dataframe(),
        "ci": pareto_pca.ci_,
        "optimizer": skb_optimizer,
        "pareto_pca": pareto_pca,
    }


# ════════════════════════════════════════════════════════════
# 6. LƯU ARTIFACTS
# ════════════════════════════════════════════════════════════

def save_features_artifacts(
    selector: SelectKBest,
    pca: PCA,
    scaler: MinMaxScaler,
    k_final: int,
    n_chosen: int,
    cv_results: pd.DataFrame | None = None,
    ablation_df: pd.DataFrame | None = None,
    pareto_results: pd.DataFrame | None = None,
    selected_feature_names: list[str] | None = None,
) -> None:
    """
    Lưu tất cả artifacts C1 vào thư mục models/ và data/processed_data/.

    Bỏ qua nếu file đã tồn tại (idempotent).

    Tham số:
        selector               : SelectKBest đã fit
        pca                    : PCA đã fit
        scaler                 : MinMaxScaler([0,π]) đã fit
        k_final                : K đã chọn
        n_chosen               : Số qubit đã chọn
        cv_results             : DataFrame CV SelectKBest (tuỳ chọn)
        ablation_df            : DataFrame ablation (tuỳ chọn)
        pareto_results         : DataFrame tóm tắt Pareto (tuỳ chọn)
        selected_feature_names : Danh sách tên features được chọn (tuỳ chọn)
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # -- Transformers --
    selector_path = MODELS_DIR / f"feature_selector_k{k_final}.joblib"
    if not selector_path.exists():
        joblib.dump(selector, selector_path)

    pca_path = MODELS_DIR / f"pca_{n_chosen}components.joblib"
    if not pca_path.exists():
        joblib.dump(pca, pca_path)

    scaler_path = SCALER_PATH
    if not scaler_path.exists():
        joblib.dump(scaler, scaler_path)

    # -- CSV metadata --
    if cv_results is not None:
        p = DATA_PROCESSED_DIR / "selectkbest_cv_results.csv"
        if not p.exists():
            cv_results.to_csv(p, index=False)

    if ablation_df is not None:
        p = DATA_PROCESSED_DIR / "ablation_study_results.csv"
        if not p.exists():
            ablation_df.to_csv(p, index=False)

    if pareto_results is not None:
        p = DATA_PROCESSED_DIR / "pca_pareto_results.csv"
        if not p.exists():
            pareto_results.to_csv(p, index=False)

    if selected_feature_names is not None:
        p = DATA_PROCESSED_DIR / "selected_feature_names.csv"
        if not p.exists():
            pd.Series(selected_feature_names).to_csv(
                p, index=False, header=["feature"]
            )
