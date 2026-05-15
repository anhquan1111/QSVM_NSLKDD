# -*- coding: utf-8 -*-
"""Builder script tao notebook c5_confidence_calibration_multirun.ipynb."""
import json
from pathlib import Path

NB_OUT = Path('../notebooks/c5_confidence_calibration_multirun.ipynb').resolve()


def md(*lines):
    return {"cell_type": "markdown", "metadata": {}, "source": list(_lines(lines))}


def code(*lines):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": list(_lines(lines))}


def _lines(blocks):
    """Convert tuple of multiline strings vao list of lines voi \\n cuoi (tru dong cuoi)."""
    text = "\n".join(blocks)
    lines = text.split("\n")
    out = []
    for i, ln in enumerate(lines):
        if i < len(lines) - 1:
            out.append(ln + "\n")
        else:
            if ln:
                out.append(ln)
    return out


cells = []

# ────────────────────────────────────────────────────────────────────────────
# 0. Title + intro
# ────────────────────────────────────────────────────────────────────────────
cells.append(md(
    "# Contribution 5: Confidence Calibration — Multi-Run (5 Trains × 1 Fixed Test)\n",
    "\n",
    "**Câu hỏi nghiên cứu:** QSVM có ưu thế ổn định về *độ tin cậy hiệu chuẩn (calibration)* và *ranking lớp hiếm (AUC-PR)* so với SVM cổ điển, hay đó chỉ là noise của một single run?\n",
    "\n",
    "**Phương pháp multi-run:** Train trên 5 tập train độc lập (`train_run1.csv` → `train_run5.csv`, mỗi tập 1000 mẫu), test trên cùng 1 tập test cố định (`NSL_KDD_Test_Sample100.csv`, 99 mẫu, **10 mẫu rare U2R+R2L**) → báo cáo **mean ± std** cho ECE / AUC-ROC / AUC-PR / McNemar / Cohen's d.\n",
    "\n",
    "**Pipeline:** `Raw` → `SelectKBest(K=20)` → `PCA(4D)` → `MinMaxScaler[0,π]` → QSVM (ZZFeatureMap, statevector) · SVM-RBF · SVM-Poly\n",
    "\n",
    "---\n",
    "\n",
    "## ⚠️ Sửa narrative Cohen's d so với C5 đơn-run\n",
    "\n",
    "Trong báo cáo C5 cũ và file `CLAUDE.md`, có câu **\"QSVM margin tighter and more stable\"** kèm `d=-0.6805`. **Đây là diễn giải sai dấu**:\n",
    "\n",
    "$$d = \\frac{\\mu_{|\\text{margin}|}^{\\text{QSVM}} - \\mu_{|\\text{margin}|}^{\\text{RBF}}}{\\sigma_{\\text{pooled}}}$$\n",
    "\n",
    "* `d < 0` ⇔ `μ_QSVM < μ_RBF` ⇔ **biên trung bình của RBF LỚN HƠN QSVM** trên lớp hiếm.\n",
    "* \"Tighter\" theo nghĩa biên hẹp **không phải là ưu thế** trong SVM — biên rộng (wider margin) mới là dấu hiệu tin cậy hình học.\n",
    "\n",
    "**Narrative ĐÚNG (sau khi sửa):** QSVM **không** thắng về độ rộng margin trên lớp hiếm; ưu thế của QSVM nằm ở **calibration (ECE_rare thấp hơn)** và **ranking quality (AUC-PR cao hơn)**. Multi-run notebook này định lượng cả hai claim đó với mean ± std qua 5 runs."
))

# ────────────────────────────────────────────────────────────────────────────
# 1. Imports & Config
# ────────────────────────────────────────────────────────────────────────────
cells.append(md(
    "## 1. Config & Imports"
))

cells.append(code(
    "import warnings\n",
    "warnings.filterwarnings('ignore')\n",
    "\n",
    "import os, json, time\n",
    "import numpy as np\n",
    "import pandas as pd\n",
    "import matplotlib\n",
    "import matplotlib.pyplot as plt\n",
    "import matplotlib.gridspec as gridspec\n",
    "from matplotlib.lines import Line2D\n",
    "from matplotlib.patches import Patch\n",
    "import seaborn as sns\n",
    "import joblib\n",
    "from pathlib import Path\n",
    "\n",
    "from sklearn.svm import SVC\n",
    "from sklearn.linear_model import LogisticRegression\n",
    "from sklearn.metrics import (\n",
    "    accuracy_score, f1_score,\n",
    "    roc_curve, auc, precision_recall_curve, average_precision_score,\n",
    "    confusion_matrix,\n",
    ")\n",
    "from scipy.stats import chi2 as chi2_dist\n",
    "\n",
    "from qiskit.circuit.library import zz_feature_map\n",
    "from qiskit_machine_learning.kernels import FidelityStatevectorKernel\n",
    "from qiskit_machine_learning.algorithms import QSVC\n",
    "\n",
    "import qiskit, qiskit_machine_learning\n",
    "print(f'Qiskit              : {qiskit.__version__}')\n",
    "print(f'Qiskit ML           : {qiskit_machine_learning.__version__}')\n",
    "print('Backend             : FidelityStatevectorKernel (statevector, noiseless)')\n",
    "\n",
    "# ── Cau hinh multi-run ───────────────────────────────────────────────────────\n",
    "RANDOM_STATE = 42\n",
    "RUN_IDS      = [1, 2, 3, 4, 5]\n",
    "np.random.seed(RANDOM_STATE)\n",
    "\n",
    "# ── Cau hinh quantum & SVM ──────────────────────────────────────────────────\n",
    "N_QUBITS     = 4\n",
    "ANGLE_MAX    = np.pi\n",
    "REPS         = 2\n",
    "ENTANGLEMENT = 'full'\n",
    "C_QSVM       = 1.0\n",
    "C_RBF        = 10.0\n",
    "C_POLY       = 0.1\n",
    "POLY_DEGREE  = 2\n",
    "\n",
    "TRAIN_SIZE   = 1000\n",
    "TEST_SIZE    = 100  # ten file Sample100 — 99 mau thuc te sau dedupe\n",
    "N_BINS_FULL  = 10\n",
    "N_BINS_RARE  = 5\n",
    "\n",
    "LABEL_COLS   = ['label', 'label_binary', 'label_multiclass', 'attack_category']\n",
    "GROUP_ORDER  = ['Normal', 'DoS', 'Probe', 'U2R', 'R2L']\n",
    "RARE_GROUPS  = ['U2R', 'R2L']\n",
    "\n",
    "# ── Duong dan ───────────────────────────────────────────────────────────────\n",
    "ROOT        = Path('..').resolve()\n",
    "DATA_DIR    = ROOT / 'data' / 'processed_data'\n",
    "MODELS_DIR  = ROOT / 'models'\n",
    "REPORTS_DIR = ROOT / 'reports'\n",
    "REPORTS_DIR.mkdir(parents=True, exist_ok=True)\n",
    "\n",
    "MULTIRUN_CACHE_DIR = MODELS_DIR / 'qsvm_cache' / 'multirun_c5'\n",
    "MULTIRUN_CACHE_DIR.mkdir(parents=True, exist_ok=True)\n",
    "\n",
    "TEST_PATH = DATA_DIR / f'NSL_KDD_Test_Sample{TEST_SIZE}.csv'\n",
    "\n",
    "CONFIG_TAG = (\n",
    "    f'mr_c5_r{REPS}_{ENTANGLEMENT}'\n",
    "    f'_cq{C_QSVM}_crbf{C_RBF}_cpoly{C_POLY}'\n",
    "    f'_n{TRAIN_SIZE}_t{TEST_SIZE}'\n",
    ")\n",
    "\n",
    "# ── Color palette nhat quan voi C5 don-run ──────────────────────────────────\n",
    "MODEL_COLORS = {'QSVM': '#8B5CF6', 'SVM-RBF': '#F59E0B', 'SVM-Poly': '#10B981'}\n",
    "MODEL_NAMES  = list(MODEL_COLORS.keys())\n",
    "GROUP_COLORS = {\n",
    "    'Normal': '#3B82F6', 'DoS': '#EF4444',\n",
    "    'Probe':  '#F59E0B', 'U2R': '#8B5CF6', 'R2L': '#10B981',\n",
    "}\n",
    "\n",
    "plt.rcParams.update({'figure.dpi': 120, 'font.size': 10,\n",
    "                     'axes.titlesize': 12, 'axes.labelsize': 11})\n",
    "plt.style.use('seaborn-v0_8-whitegrid')\n",
    "\n",
    "print(f'\\nCONFIG_TAG : {CONFIG_TAG}')\n",
    "print(f'RUN_IDS    : {RUN_IDS}')\n",
    "print(f'TEST_PATH  : {TEST_PATH.name}')\n",
    "print(f'CACHE_DIR  : {MULTIRUN_CACHE_DIR}')"
))

# ────────────────────────────────────────────────────────────────────────────
# 2. Transformers
# ────────────────────────────────────────────────────────────────────────────
cells.append(md(
    "## 2. Load Transformers (Zero-Leakage)\n",
    "\n",
    "Nạp `selector`, `pca`, `scaler` đã `.fit()` ở pipeline gốc. Mọi cell phía sau **chỉ gọi `.transform()`** — không có lệnh `.fit()` nào trên test set."
))

cells.append(code(
    "selector = joblib.load(MODELS_DIR / 'feature_selector_k20.joblib')\n",
    "pca      = joblib.load(MODELS_DIR / 'pca_4components.joblib')\n",
    "scaler   = joblib.load(MODELS_DIR / 'scaler_minmax_pi.joblib')\n",
    "print(f'SelectKBest : k={selector.k}')\n",
    "print(f'PCA         : n_components={pca.n_components_}, var={pca.explained_variance_ratio_.sum()*100:.2f}%')\n",
    "print(f'Scaler      : range=[{scaler.feature_range[0]:.4f}, {scaler.feature_range[1]:.4f}]')"
))

# ────────────────────────────────────────────────────────────────────────────
# 3. Helpers
# ────────────────────────────────────────────────────────────────────────────
cells.append(md(
    "## 3. Helpers — Pipeline, Quantum Kernel, Platt, ECE Adaptive Binning"
))

cells.append(code(
    "def transform_pipeline(df, feat_cols):\n",
    "    # Raw → SelectKBest → PCA → MinMax[0,π]. KHONG fit.\n",
    "    X_raw = df[feat_cols].to_numpy(dtype=np.float32)\n",
    "    X_sel = selector.transform(X_raw)\n",
    "    X_pca = pca.transform(X_sel)\n",
    "    return np.clip(scaler.transform(X_pca), 0, ANGLE_MAX).astype(np.float64)\n",
    "\n",
    "\n",
    "def build_quantum_kernel():\n",
    "    fm = zz_feature_map(feature_dimension=N_QUBITS, reps=REPS, entanglement=ENTANGLEMENT)\n",
    "    return FidelityStatevectorKernel(feature_map=fm, shots=None, enforce_psd=True, cache_size=None)\n",
    "\n",
    "\n",
    "class PlattScaler:\n",
    "    # Platt Scaling: anh xa decision scores → P(y=1|f) qua sigmoid logistic.\n",
    "    # Fit DOC QUYEN tren train set (zero-leakage).\n",
    "    def __init__(self, C=1e10):\n",
    "        self.lr = LogisticRegression(C=C, solver='lbfgs', max_iter=2000, random_state=42)\n",
    "    def fit(self, scores, y):\n",
    "        self.lr.fit(scores.reshape(-1, 1), y)\n",
    "        return self, float(self.lr.coef_[0][0]), float(self.lr.intercept_[0])\n",
    "    def predict_proba(self, scores):\n",
    "        return self.lr.predict_proba(scores.reshape(-1, 1))[:, 1]\n",
    "\n",
    "\n",
    "def adaptive_calibration_curve(y_true, y_prob, n_bins=10):\n",
    "    # Equal-frequency binning — tranh empty bins cho U2R/R2L.\n",
    "    n             = len(y_prob)\n",
    "    sorted_idx    = np.argsort(y_prob)\n",
    "    y_prob_sorted = y_prob[sorted_idx]\n",
    "    y_true_sorted = y_true[sorted_idx]\n",
    "    bin_size = max(n // n_bins, 1)\n",
    "    mean_conf, frac_pos, bin_sizes = [], [], []\n",
    "    for i in range(n_bins):\n",
    "        start = i * bin_size\n",
    "        end   = (i + 1) * bin_size if i < n_bins - 1 else n\n",
    "        if start >= n:\n",
    "            break\n",
    "        b_true = y_true_sorted[start:end]\n",
    "        b_prob = y_prob_sorted[start:end]\n",
    "        if len(b_true) == 0:\n",
    "            continue\n",
    "        mean_conf.append(float(np.mean(b_prob)))\n",
    "        frac_pos.append(float(np.mean(b_true)))\n",
    "        bin_sizes.append(len(b_true))\n",
    "    return np.array(mean_conf), np.array(frac_pos), np.array(bin_sizes)\n",
    "\n",
    "\n",
    "def compute_ece_mce(y_true, y_prob, n_bins=10):\n",
    "    mc, fp, bs = adaptive_calibration_curve(y_true, y_prob, n_bins)\n",
    "    n = len(y_true)\n",
    "    if len(mc) == 0:\n",
    "        return float('nan'), float('nan')\n",
    "    ece = float(np.sum(bs / n * np.abs(fp - mc)))\n",
    "    mce = float(np.max(np.abs(fp - mc)))\n",
    "    return ece, mce\n",
    "\n",
    "\n",
    "def cohens_d(a, b):\n",
    "    # Cohen's d voi pooled std. Dau hieu d:\n",
    "    #   d > 0  →  mean(a) > mean(b)\n",
    "    #   d < 0  →  mean(a) < mean(b)  ↔  RBF margin > QSVM margin (neu a=QSVM, b=RBF)\n",
    "    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)\n",
    "    if len(a) < 2 or len(b) < 2:\n",
    "        return float('nan')\n",
    "    pooled = np.sqrt((a.std(ddof=1)**2 + b.std(ddof=1)**2) / 2.0)\n",
    "    if pooled < 1e-12:\n",
    "        return float('nan')\n",
    "    return float((a.mean() - b.mean()) / pooled)\n",
    "\n",
    "\n",
    "def mcnemar_pvalue(b, c):\n",
    "    # McNemar voi continuity correction.\n",
    "    if b + c == 0:\n",
    "        return float('nan'), float('nan')\n",
    "    chi2_stat = (abs(b - c) - 1) ** 2 / (b + c)\n",
    "    p = 1.0 - chi2_dist.cdf(chi2_stat, df=1)\n",
    "    return float(chi2_stat), float(p)\n",
    "\n",
    "\n",
    "print('Helpers ready.')"
))

# ────────────────────────────────────────────────────────────────────────────
# 4. Single-run function
# ────────────────────────────────────────────────────────────────────────────
cells.append(md(
    "## 4. Single-Run Function — C5 Logic Preserved\n",
    "\n",
    "Mỗi run: train 3 mô hình (QSVM / RBF / Poly) trên `train_run{id}.csv`, fit Platt trên train scores, đánh giá trên fixed test set. Cache mỗi model `joblib` để re-run nhanh."
))

cells.append(code(
    "def run_c5_single(run_id, test_df, group_test, y_test, feat_cols, rare_mask):\n",
    "    # Tra ve dict chua tat ca metrics + artifacts cho 1 run.\n",
    "    print(f'\\n[C5][run_{run_id}] ====== START ======')\n",
    "    run_cache = MULTIRUN_CACHE_DIR / f'run_{run_id}'\n",
    "    run_cache.mkdir(parents=True, exist_ok=True)\n",
    "\n",
    "    # ── Load train ──────────────────────────────────────────────────────────\n",
    "    train_path = DATA_DIR / 'multi_run' / f'train_run{run_id}.csv'\n",
    "    if not train_path.exists():\n",
    "        raise FileNotFoundError(f'[MISSING] {train_path}')\n",
    "    df_train = pd.read_csv(train_path)\n",
    "    X_train  = transform_pipeline(df_train, feat_cols)\n",
    "    y_train  = df_train['label_binary'].to_numpy(dtype=np.int64)\n",
    "    print(f'  Train: {X_train.shape} | class={np.bincount(y_train).tolist()}')\n",
    "\n",
    "    # ── Load or train 3 models ──────────────────────────────────────────────\n",
    "    model_path = run_cache / f'models_{CONFIG_TAG}.joblib'\n",
    "    if model_path.exists():\n",
    "        store = joblib.load(model_path)\n",
    "        qsvm, rbf, poly = store['qsvm'], store['rbf'], store['poly']\n",
    "        print(f'  [CACHE] models loaded')\n",
    "    else:\n",
    "        print(f'  [TRAIN] SVM-RBF ...')\n",
    "        rbf = SVC(kernel='rbf', C=C_RBF, gamma='scale', random_state=RANDOM_STATE)\n",
    "        rbf.fit(X_train, y_train)\n",
    "        print(f'  [TRAIN] SVM-Poly ...')\n",
    "        poly = SVC(kernel='poly', degree=POLY_DEGREE, C=C_POLY, gamma='scale', random_state=RANDOM_STATE)\n",
    "        poly.fit(X_train, y_train)\n",
    "        print(f'  [TRAIN] QSVM ZZ ...')\n",
    "        t0 = time.time()\n",
    "        qsvm = QSVC(quantum_kernel=build_quantum_kernel(), C=C_QSVM, random_state=RANDOM_STATE)\n",
    "        qsvm.fit(X_train, y_train)\n",
    "        print(f'    QSVM trained in {time.time()-t0:.1f}s')\n",
    "        joblib.dump({'qsvm': qsvm, 'rbf': rbf, 'poly': poly}, model_path)\n",
    "\n",
    "    models = {'QSVM': qsvm, 'SVM-RBF': rbf, 'SVM-Poly': poly}\n",
    "\n",
    "    # ── Test set transform ─────────────────────────────────────────────────\n",
    "    X_test = transform_pipeline(test_df, feat_cols)\n",
    "\n",
    "    # ── Predictions & decision scores ──────────────────────────────────────\n",
    "    y_pred, df_scores, df_train_scores = {}, {}, {}\n",
    "    for name, mdl in models.items():\n",
    "        y_pred[name]          = mdl.predict(X_test)\n",
    "        df_scores[name]       = mdl.decision_function(X_test)\n",
    "        df_train_scores[name] = mdl.decision_function(X_train)\n",
    "\n",
    "    # ── Platt scaling (fit train, apply test) ──────────────────────────────\n",
    "    prob, platt_params = {}, {}\n",
    "    for name in MODEL_NAMES:\n",
    "        scl, A, B = PlattScaler().fit(df_train_scores[name], y_train)\n",
    "        prob[name] = scl.predict_proba(df_scores[name])\n",
    "        platt_params[name] = {'A': round(A, 5), 'B': round(B, 5)}\n",
    "\n",
    "    # ── ECE/MCE full & rare ───────────────────────────────────────────────\n",
    "    ece = {}\n",
    "    for name in MODEL_NAMES:\n",
    "        ef, mf = compute_ece_mce(y_test, prob[name], n_bins=N_BINS_FULL)\n",
    "        if rare_mask.sum() > 1:\n",
    "            er, mr = compute_ece_mce(y_test[rare_mask], prob[name][rare_mask], n_bins=N_BINS_RARE)\n",
    "        else:\n",
    "            er, mr = float('nan'), float('nan')\n",
    "        ece[name] = {'ece_full': ef, 'mce_full': mf, 'ece_rare': er, 'mce_rare': mr}\n",
    "\n",
    "    # ── AUC-ROC, AUC-PR (binary) ──────────────────────────────────────────\n",
    "    auc_roc, auc_pr = {}, {}\n",
    "    for name in MODEL_NAMES:\n",
    "        fpr, tpr, _ = roc_curve(y_test, prob[name])\n",
    "        auc_roc[name] = float(auc(fpr, tpr))\n",
    "        auc_pr[name]  = float(average_precision_score(y_test, prob[name]))\n",
    "\n",
    "    # ── Per-group accuracy ────────────────────────────────────────────────\n",
    "    per_group_acc = {}\n",
    "    for grp in GROUP_ORDER:\n",
    "        m = (group_test == grp)\n",
    "        if m.sum() == 0:\n",
    "            continue\n",
    "        per_group_acc[grp] = {nm: float(accuracy_score(y_test[m], y_pred[nm][m])) for nm in MODEL_NAMES}\n",
    "\n",
    "    # ── Complementarity rare (QSVM vs RBF) ────────────────────────────────\n",
    "    qok  = (y_pred['QSVM']    == y_test)\n",
    "    rok  = (y_pred['SVM-RBF'] == y_test)\n",
    "    qwin = (qok & ~rok & rare_mask).sum()\n",
    "    rwin = (~qok & rok & rare_mask).sum()\n",
    "    bok  = (qok & rok & rare_mask).sum()\n",
    "    bwr  = (~qok & ~rok & rare_mask).sum()\n",
    "\n",
    "    # ── McNemar (QSVM vs RBF) ─────────────────────────────────────────────\n",
    "    chi2_stat, p_value = mcnemar_pvalue(int(qwin), int(rwin))\n",
    "\n",
    "    # ── Cohen's d cua |margin| tren rare class — QSVM vs RBF ──────────────\n",
    "    qm = np.abs(df_scores['QSVM'][rare_mask])\n",
    "    rm = np.abs(df_scores['SVM-RBF'][rare_mask])\n",
    "    d_margin_rare = cohens_d(qm, rm)\n",
    "\n",
    "    # ── Binary F1, Acc ────────────────────────────────────────────────────\n",
    "    perf = {name: {'f1':  float(f1_score(y_test, y_pred[name])),\n",
    "                   'acc': float(accuracy_score(y_test, y_pred[name]))}\n",
    "             for name in MODEL_NAMES}\n",
    "\n",
    "    print(f'  [{ \"QSVM\" :8s}] ECE_rare={ece[\"QSVM\"][\"ece_rare\"]:.4f} | AUC-PR={auc_pr[\"QSVM\"]:.4f} | d={d_margin_rare:+.3f}')\n",
    "    print(f'  [{ \"RBF\"  :8s}] ECE_rare={ece[\"SVM-RBF\"][\"ece_rare\"]:.4f} | AUC-PR={auc_pr[\"SVM-RBF\"]:.4f}')\n",
    "    print(f'  [{ \"Poly\" :8s}] ECE_rare={ece[\"SVM-Poly\"][\"ece_rare\"]:.4f} | AUC-PR={auc_pr[\"SVM-Poly\"]:.4f}')\n",
    "    print(f'[C5][run_{run_id}] ====== DONE ======')\n",
    "\n",
    "    return {\n",
    "        'run_id'       : run_id,\n",
    "        'platt_params' : platt_params,\n",
    "        'ece'          : ece,\n",
    "        'auc_roc'      : auc_roc,\n",
    "        'auc_pr'       : auc_pr,\n",
    "        'perf'         : perf,\n",
    "        'per_group_acc': per_group_acc,\n",
    "        'complementarity_rare': {'qsvm_wins': int(qwin), 'rbf_wins': int(rwin),\n",
    "                                  'both_correct': int(bok), 'both_wrong': int(bwr)},\n",
    "        'mcnemar'      : {'b': int(qwin), 'c': int(rwin),\n",
    "                          'chi2': chi2_stat, 'p_value': p_value},\n",
    "        'cohens_d_margin_rare': d_margin_rare,\n",
    "        # artifacts cho fig representative\n",
    "        'prob'         : prob,\n",
    "        'y_pred'       : y_pred,\n",
    "        'df_scores'    : df_scores,\n",
    "    }"
))

# ────────────────────────────────────────────────────────────────────────────
# 5. Run all 5
# ────────────────────────────────────────────────────────────────────────────
cells.append(md(
    "## 5. Load Test Set + Run All 5 Trains"
))

cells.append(code(
    "# ── Load fixed test set ─────────────────────────────────────────────────\n",
    "test_df  = pd.read_csv(TEST_PATH)\n",
    "feat_cols   = [c for c in test_df.columns if c not in LABEL_COLS]\n",
    "y_test      = test_df['label_binary'].to_numpy(dtype=np.int64)\n",
    "group_test  = test_df['attack_category'].to_numpy()\n",
    "rare_mask   = np.isin(group_test, RARE_GROUPS)\n",
    "\n",
    "print(f'Test  : {len(test_df)} mau | y_test class={np.bincount(y_test).tolist()}')\n",
    "print(f'Rare  : n={int(rare_mask.sum())} | groups={dict(zip(*np.unique(group_test[rare_mask], return_counts=True)))}')\n",
    "print(f'Group : {dict(zip(*np.unique(group_test, return_counts=True)))}')\n",
    "\n",
    "all_runs = {}\n",
    "for run_id in RUN_IDS:\n",
    "    all_runs[run_id] = run_c5_single(run_id, test_df, group_test, y_test, feat_cols, rare_mask)\n",
    "\n",
    "print('\\n=== ALL RUNS COMPLETED ===')"
))

# ────────────────────────────────────────────────────────────────────────────
# 6. Aggregate per-run DF
# ────────────────────────────────────────────────────────────────────────────
cells.append(md(
    "## 6. Aggregate Per-Run Metrics → Mean ± Std"
))

cells.append(code(
    "rows = []\n",
    "for run_id, art in all_runs.items():\n",
    "    for name in MODEL_NAMES:\n",
    "        rows.append({\n",
    "            'run_id'      : run_id,\n",
    "            'model'       : name,\n",
    "            'f1'          : art['perf'][name]['f1'],\n",
    "            'acc'         : art['perf'][name]['acc'],\n",
    "            'ece_full'    : art['ece'][name]['ece_full'],\n",
    "            'mce_full'    : art['ece'][name]['mce_full'],\n",
    "            'ece_rare'    : art['ece'][name]['ece_rare'],\n",
    "            'mce_rare'    : art['ece'][name]['mce_rare'],\n",
    "            'auc_roc'     : art['auc_roc'][name],\n",
    "            'auc_pr'      : art['auc_pr'][name],\n",
    "        })\n",
    "per_run_df = pd.DataFrame(rows)\n",
    "\n",
    "# QSVM-vs-RBF specific stats (per run, not per model)\n",
    "stat_rows = []\n",
    "for run_id, art in all_runs.items():\n",
    "    stat_rows.append({\n",
    "        'run_id'                : run_id,\n",
    "        'qsvm_wins'             : art['complementarity_rare']['qsvm_wins'],\n",
    "        'rbf_wins'              : art['complementarity_rare']['rbf_wins'],\n",
    "        'both_correct'          : art['complementarity_rare']['both_correct'],\n",
    "        'both_wrong'            : art['complementarity_rare']['both_wrong'],\n",
    "        'mcnemar_chi2'          : art['mcnemar']['chi2'],\n",
    "        'mcnemar_p'             : art['mcnemar']['p_value'],\n",
    "        'cohens_d_margin_rare'  : art['cohens_d_margin_rare'],\n",
    "    })\n",
    "stat_df = pd.DataFrame(stat_rows)\n",
    "\n",
    "agg = per_run_df.groupby('model').agg(['mean', 'std']).round(5)\n",
    "\n",
    "# ── Save CSV ───────────────────────────────────────────────────────────────\n",
    "per_run_df.to_csv(DATA_DIR / 'c5_multirun_per_run.csv', index=False)\n",
    "stat_df.to_csv(DATA_DIR / 'c5_multirun_stat_per_run.csv', index=False)\n",
    "agg_flat = per_run_df.groupby('model').agg(\n",
    "    f1_mean=('f1','mean'), f1_std=('f1','std'),\n",
    "    acc_mean=('acc','mean'), acc_std=('acc','std'),\n",
    "    ece_full_mean=('ece_full','mean'), ece_full_std=('ece_full','std'),\n",
    "    ece_rare_mean=('ece_rare','mean'), ece_rare_std=('ece_rare','std'),\n",
    "    auc_roc_mean=('auc_roc','mean'), auc_roc_std=('auc_roc','std'),\n",
    "    auc_pr_mean=('auc_pr','mean'), auc_pr_std=('auc_pr','std'),\n",
    ").round(5)\n",
    "agg_flat.to_csv(DATA_DIR / 'c5_multirun_summary.csv')\n",
    "\n",
    "print('\\n=== MEAN ± STD (5 runs) ===')\n",
    "fmt = lambda m, s: f'{m:.4f} ± {s:.4f}'\n",
    "print(f'{ \"Model\" :>10s} | {\"F1\":>15s} | {\"ECE_full\":>17s} | {\"ECE_rare\":>17s} | {\"AUC-ROC\":>17s} | {\"AUC-PR\":>17s}')\n",
    "print('-' * 110)\n",
    "for name in MODEL_NAMES:\n",
    "    r = agg_flat.loc[name]\n",
    "    print(f'{name:>10s} | {fmt(r.f1_mean,r.f1_std):>15s} | '\n",
    "          f'{fmt(r.ece_full_mean,r.ece_full_std):>17s} | '\n",
    "          f'{fmt(r.ece_rare_mean,r.ece_rare_std):>17s} | '\n",
    "          f'{fmt(r.auc_roc_mean,r.auc_roc_std):>17s} | '\n",
    "          f'{fmt(r.auc_pr_mean,r.auc_pr_std):>17s}')\n",
    "\n",
    "print('\\n=== QSVM vs RBF — Statistical Tests (per run) ===')\n",
    "print(stat_df.to_string(index=False, float_format=lambda x: f'{x:.4f}' if isinstance(x, float) else str(x)))\n",
    "print('\\n=== AGGREGATE (mean ± std) ===')\n",
    "for col in ['qsvm_wins', 'rbf_wins', 'mcnemar_p', 'cohens_d_margin_rare']:\n",
    "    print(f'  {col:<22s}: {stat_df[col].mean():+.4f} ± {stat_df[col].std():.4f}')"
))

# ────────────────────────────────────────────────────────────────────────────
# 7. Figure 1 — ECE bar chart full + rare
# ────────────────────────────────────────────────────────────────────────────
cells.append(md(
    "## 7. Figure 1 — ECE (Full vs Rare) Mean ± Std\n",
    "\n",
    "**Đọc đồ thị:** ECE thấp hơn ⇒ probability calibration tốt hơn. Cột rare U2R+R2L (n=10) là chỉ số quan trọng nhất trong narrative đã sửa."
))

cells.append(code(
    "fig1, axes1 = plt.subplots(1, 2, figsize=(14, 5.5))\n",
    "fig1.suptitle(\n",
    "    f'Figure 1: ECE — Mean ± Std over {len(RUN_IDS)} Runs (Adaptive Binning)\\n'\n",
    "    f'Train n={TRAIN_SIZE} | Fixed Test n={len(y_test)} | Rare n={int(rare_mask.sum())}',\n",
    "    fontsize=12, fontweight='bold'\n",
    ")\n",
    "x = np.arange(len(MODEL_NAMES))\n",
    "for ax, key, title in [(axes1[0], 'ece_full', 'ECE — Full Test'),\n",
    "                        (axes1[1], 'ece_rare', 'ECE — Rare (U2R+R2L)')]:\n",
    "    means = [agg_flat.loc[nm, f'{key}_mean'] for nm in MODEL_NAMES]\n",
    "    stds  = [agg_flat.loc[nm, f'{key}_std']  for nm in MODEL_NAMES]\n",
    "    bars = ax.bar(x, means, 0.6, yerr=stds, capsize=7,\n",
    "                  color=[MODEL_COLORS[nm] for nm in MODEL_NAMES],\n",
    "                  alpha=0.88, edgecolor='white', linewidth=1.2,\n",
    "                  error_kw=dict(elinewidth=1.8, ecolor='#333', capthick=2), zorder=3)\n",
    "    best = int(np.nanargmin(means))\n",
    "    for i, (bar, m, s) in enumerate(zip(bars, means, stds)):\n",
    "        star = ' ★' if i == best else ''\n",
    "        ax.text(bar.get_x()+bar.get_width()/2, m+s+0.003,\n",
    "                f'{m:.4f}{star}', ha='center', va='bottom', fontsize=10, fontweight='bold')\n",
    "    ax.set_xticks(x); ax.set_xticklabels(MODEL_NAMES, fontsize=10)\n",
    "    ax.set_ylabel('ECE (lower = better)')\n",
    "    ax.set_title(title, fontweight='bold')\n",
    "    ax.grid(True, axis='y', alpha=0.3)\n",
    "    ax.set_ylim(0, max(means)*1.4 + max(stds))\n",
    "\n",
    "plt.tight_layout()\n",
    "fig1_path = REPORTS_DIR / 'c5_multirun_ece.png'\n",
    "plt.savefig(fig1_path, dpi=150, bbox_inches='tight')\n",
    "plt.show()\n",
    "print(f'Da luu: {fig1_path}')"
))

# ────────────────────────────────────────────────────────────────────────────
# 8. Figure 2 — AUC bar charts
# ────────────────────────────────────────────────────────────────────────────
cells.append(md(
    "## 8. Figure 2 — AUC-ROC & AUC-PR Mean ± Std\n",
    "\n",
    "**Đọc đồ thị:** AUC-PR đặc biệt nhạy với hiệu năng trên positive class hiếm — đây là metric chính ủng hộ QSVM trong narrative đã sửa."
))

cells.append(code(
    "fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5.5))\n",
    "fig2.suptitle(\n",
    "    f'Figure 2: AUC-ROC & AUC-PR — Mean ± Std over {len(RUN_IDS)} Runs',\n",
    "    fontsize=12, fontweight='bold'\n",
    ")\n",
    "x = np.arange(len(MODEL_NAMES))\n",
    "for ax, key, title in [(axes2[0], 'auc_roc', 'AUC-ROC'),\n",
    "                        (axes2[1], 'auc_pr',  'AUC-PR (binary attack)')]:\n",
    "    means = [agg_flat.loc[nm, f'{key}_mean'] for nm in MODEL_NAMES]\n",
    "    stds  = [agg_flat.loc[nm, f'{key}_std']  for nm in MODEL_NAMES]\n",
    "    bars = ax.bar(x, means, 0.6, yerr=stds, capsize=7,\n",
    "                  color=[MODEL_COLORS[nm] for nm in MODEL_NAMES],\n",
    "                  alpha=0.88, edgecolor='white', linewidth=1.2,\n",
    "                  error_kw=dict(elinewidth=1.8, ecolor='#333', capthick=2), zorder=3)\n",
    "    best = int(np.nanargmax(means))\n",
    "    for i, (bar, m, s) in enumerate(zip(bars, means, stds)):\n",
    "        star = ' ★' if i == best else ''\n",
    "        ax.text(bar.get_x()+bar.get_width()/2, m+s+0.003,\n",
    "                f'{m:.4f}{star}', ha='center', va='bottom', fontsize=10, fontweight='bold')\n",
    "    ax.set_xticks(x); ax.set_xticklabels(MODEL_NAMES, fontsize=10)\n",
    "    ax.set_ylabel(f'{title} (higher = better)')\n",
    "    ax.set_title(title, fontweight='bold')\n",
    "    ax.grid(True, axis='y', alpha=0.3)\n",
    "    lo = min(means) - max(stds) - 0.05\n",
    "    ax.set_ylim(max(0, lo), 1.02)\n",
    "\n",
    "plt.tight_layout()\n",
    "fig2_path = REPORTS_DIR / 'c5_multirun_auc.png'\n",
    "plt.savefig(fig2_path, dpi=150, bbox_inches='tight')\n",
    "plt.show()\n",
    "print(f'Da luu: {fig2_path}')"
))

# ────────────────────────────────────────────────────────────────────────────
# 9. Figure 3 — per-run trend lines
# ────────────────────────────────────────────────────────────────────────────
cells.append(md(
    "## 9. Figure 3 — Per-Run Trend Lines (ECE_rare & AUC-PR)\n",
    "\n",
    "Xem mỗi run riêng lẻ — đường nào nằm cao/thấp ổn định, đường nào dao động → đánh giá *stability* của lợi thế QSVM."
))

cells.append(code(
    "fig3, axes3 = plt.subplots(1, 2, figsize=(14, 5.5))\n",
    "fig3.suptitle(\n",
    "    f'Figure 3: Per-Run Trend Lines — Calibration & Ranking Stability ({len(RUN_IDS)} Runs)',\n",
    "    fontsize=12, fontweight='bold'\n",
    ")\n",
    "for ax, key, ylabel, better in [(axes3[0], 'ece_rare', 'ECE_rare (lower = better)', 'lower'),\n",
    "                                  (axes3[1], 'auc_pr',  'AUC-PR (higher = better)',  'higher')]:\n",
    "    for name in MODEL_NAMES:\n",
    "        sub = per_run_df[per_run_df['model']==name].sort_values('run_id')\n",
    "        ax.plot(sub['run_id'], sub[key], marker='o', lw=2.2, markersize=8,\n",
    "                color=MODEL_COLORS[name], label=name, zorder=4)\n",
    "        ax.axhline(sub[key].mean(), color=MODEL_COLORS[name], ls=':',\n",
    "                   lw=1.2, alpha=0.5, zorder=2)\n",
    "    ax.set_xticks(RUN_IDS)\n",
    "    ax.set_xticklabels([f'Run {r}' for r in RUN_IDS])\n",
    "    ax.set_xlabel('Train Run')\n",
    "    ax.set_ylabel(ylabel)\n",
    "    ax.set_title(f'{key} per run (dotted = per-model mean)', fontweight='bold')\n",
    "    ax.grid(True, alpha=0.3)\n",
    "    ax.legend(fontsize=9, loc='best')\n",
    "\n",
    "plt.tight_layout()\n",
    "fig3_path = REPORTS_DIR / 'c5_multirun_trends.png'\n",
    "plt.savefig(fig3_path, dpi=150, bbox_inches='tight')\n",
    "plt.show()\n",
    "print(f'Da luu: {fig3_path}')"
))

# ────────────────────────────────────────────────────────────────────────────
# 10. Figure 4 — Reliability Diagram representative
# ────────────────────────────────────────────────────────────────────────────
cells.append(md(
    "## 10. Figure 4 — Reliability Diagram (Representative Run, Rare Class)\n",
    "\n",
    "Chọn run có `ECE_rare` của QSVM gần mean nhất → vẽ reliability diagram trên rare class cho cả 3 mô hình. Bin Adaptive (Equal-Frequency, n_bins=5) tránh empty bins khi n_rare=10."
))

cells.append(code(
    "# ── Chon representative run theo QSVM ECE_rare gan mean ────────────────────\n",
    "q_rare = per_run_df[per_run_df['model']=='QSVM'].set_index('run_id')['ece_rare']\n",
    "rep_id = int(q_rare.sub(q_rare.mean()).abs().idxmin())\n",
    "print(f'Representative run: {rep_id} (QSVM ECE_rare = {q_rare.loc[rep_id]:.4f}, mean = {q_rare.mean():.4f})')\n",
    "\n",
    "art_rep = all_runs[rep_id]\n",
    "\n",
    "def plot_reliability(ax, y_true, y_prob, n_bins, name, color, ece, mce):\n",
    "    mc, fp, bs = adaptive_calibration_curve(y_true, y_prob, n_bins)\n",
    "    for xi, yi in zip(mc, fp):\n",
    "        lo, hi = min(xi, yi), max(xi, yi)\n",
    "        c = '#EF4444' if yi < xi else '#10B981'\n",
    "        ax.bar(xi, hi - lo, bottom=lo, width=0.07, color=c, alpha=0.3, zorder=2)\n",
    "    ax.scatter(mc, fp, s=[b*15 for b in bs], color=color,\n",
    "               edgecolors='black', lw=0.8, zorder=5, label='Bins (size ~ n)')\n",
    "    ax.plot([0,1], [0,1], 'k--', lw=1.2, alpha=0.7, label='Perfect calibration')\n",
    "    ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.02, 1.02)\n",
    "    ax.set_xlabel('Mean Confidence')\n",
    "    ax.set_ylabel('Fraction of positives')\n",
    "    ax.set_title(f'{name} (rare, run={rep_id})\\nECE={ece:.3f}  MCE={mce:.3f}',\n",
    "                 color=color, fontweight='bold')\n",
    "    ax.legend(fontsize=8)\n",
    "    for xi, yi, b in zip(mc, fp, bs):\n",
    "        ax.annotate(f'n={b}', (xi, yi), textcoords='offset points', xytext=(4,4), fontsize=7, alpha=0.7)\n",
    "\n",
    "fig4, axes4 = plt.subplots(1, 3, figsize=(16, 5), sharey=True)\n",
    "for ax, name in zip(axes4, MODEL_NAMES):\n",
    "    plot_reliability(\n",
    "        ax,\n",
    "        y_test[rare_mask],\n",
    "        art_rep['prob'][name][rare_mask],\n",
    "        N_BINS_RARE,\n",
    "        name,\n",
    "        MODEL_COLORS[name],\n",
    "        art_rep['ece'][name]['ece_rare'],\n",
    "        art_rep['ece'][name]['mce_rare'],\n",
    "    )\n",
    "plt.suptitle(\n",
    "    f'Figure 4: Reliability Diagrams on Rare Class (Representative Run = {rep_id})',\n",
    "    fontsize=13, fontweight='bold'\n",
    ")\n",
    "plt.tight_layout()\n",
    "fig4_path = REPORTS_DIR / 'c5_multirun_reliability_rep.png'\n",
    "plt.savefig(fig4_path, dpi=150, bbox_inches='tight')\n",
    "plt.show()\n",
    "print(f'Da luu: {fig4_path}')"
))

# ────────────────────────────────────────────────────────────────────────────
# 11. Stat tests + corrected narrative
# ────────────────────────────────────────────────────────────────────────────
cells.append(md(
    "## 11. Statistical Tests + Narrative Đã Sửa\n",
    "\n",
    "### Diễn giải dấu Cohen's d\n",
    "\n",
    "$$d_{\\text{margin\\_rare}} = \\frac{\\bar{|\\text{margin}|}^{\\text{QSVM}}_{\\text{rare}} - \\bar{|\\text{margin}|}^{\\text{RBF}}_{\\text{rare}}}{\\sigma_{\\text{pooled}}}$$\n",
    "\n",
    "| Dấu $d$ | Ý nghĩa | Hệ quả |\n",
    "|:--:|:--|:--|\n",
    "| $d > 0$ | $\\|\\text{margin}\\|_{\\text{QSVM}} > \\|\\text{margin}\\|_{\\text{RBF}}$ | QSVM có biên rộng hơn (good for QSVM) |\n",
    "| $d < 0$ | $\\|\\text{margin}\\|_{\\text{QSVM}} < \\|\\text{margin}\\|_{\\text{RBF}}$ | **RBF có biên rộng hơn** → KHÔNG ủng hộ QSVM trên metric này |\n",
    "\n",
    "Vì vậy nếu mean $d < 0$ qua 5 runs → narrative phải xoay sang ECE_rare và AUC-PR (xem cell tiếp theo)."
))

cells.append(code(
    "# ── Aggregate stat tests ───────────────────────────────────────────────────\n",
    "agg_stats = {\n",
    "    'mcnemar_chi2'         : (stat_df['mcnemar_chi2'].mean(), stat_df['mcnemar_chi2'].std()),\n",
    "    'mcnemar_p'            : (stat_df['mcnemar_p'].mean(),    stat_df['mcnemar_p'].std()),\n",
    "    'cohens_d_margin_rare' : (stat_df['cohens_d_margin_rare'].mean(), stat_df['cohens_d_margin_rare'].std()),\n",
    "    'qsvm_wins'            : (stat_df['qsvm_wins'].mean(),    stat_df['qsvm_wins'].std()),\n",
    "    'rbf_wins'             : (stat_df['rbf_wins'].mean(),     stat_df['rbf_wins'].std()),\n",
    "    'both_correct'         : (stat_df['both_correct'].mean(), stat_df['both_correct'].std()),\n",
    "    'both_wrong'           : (stat_df['both_wrong'].mean(),   stat_df['both_wrong'].std()),\n",
    "}\n",
    "\n",
    "d_mean, d_std       = agg_stats['cohens_d_margin_rare']\n",
    "p_mean, p_std       = agg_stats['mcnemar_p']\n",
    "ece_q = agg_flat.loc['QSVM',    'ece_rare_mean']\n",
    "ece_r = agg_flat.loc['SVM-RBF', 'ece_rare_mean']\n",
    "ap_q  = agg_flat.loc['QSVM',    'auc_pr_mean']\n",
    "ap_r  = agg_flat.loc['SVM-RBF', 'auc_pr_mean']\n",
    "\n",
    "print('='*78)\n",
    "print('  C5 MULTI-RUN — STATISTICAL SUMMARY')\n",
    "print('='*78)\n",
    "print(f'\\n  Cohen\\'s d (|margin| rare, QSVM vs RBF) : {d_mean:+.4f} ± {d_std:.4f}')\n",
    "if d_mean < 0:\n",
    "    print(f'    →  d < 0  ⇒  RBF margin LON HON QSVM trên lop hiem')\n",
    "    print(f'    →  Narrative cu (\\'QSVM margin tighter\\') la SAI DAU → DA SUA.')\n",
    "elif d_mean > 0:\n",
    "    print(f'    →  d > 0  ⇒  QSVM margin lon hon RBF (ung ho QSVM)')\n",
    "else:\n",
    "    print(f'    →  d ≈ 0  ⇒  hai bien tuong duong')\n",
    "\n",
    "print(f'\\n  McNemar p-value (mean across 5 runs)    : {p_mean:.4f} ± {p_std:.4f}')\n",
    "if p_mean < 0.05:\n",
    "    print(f'    →  Co y nghia thong ke (mean p < 0.05)')\n",
    "else:\n",
    "    print(f'    →  Khong y nghia (mean p >= 0.05) — count predictions tied')\n",
    "\n",
    "print('\\n  --- Narrative DUNG (cac chi so QSVM thuc su thang) ---')\n",
    "ece_diff = ece_r - ece_q\n",
    "ap_diff  = ap_q - ap_r\n",
    "print(f'  ECE_rare (lower=better) : QSVM={ece_q:.4f}  RBF={ece_r:.4f}  Δ={ece_diff:+.4f}')\n",
    "print(f'    →  {\"QSVM\" if ece_diff > 0 else \"RBF\"} calibration tot hon tren lop hiem')\n",
    "print(f'  AUC-PR   (higher=better): QSVM={ap_q:.4f}  RBF={ap_r:.4f}  Δ={ap_diff:+.4f}')\n",
    "print(f'    →  {\"QSVM\" if ap_diff > 0 else \"RBF\"} ranking quality tot hon')\n",
    "print('='*78)"
))

# ────────────────────────────────────────────────────────────────────────────
# 12. Export JSON
# ────────────────────────────────────────────────────────────────────────────
cells.append(md(
    "## 12. Export `c5_results_multirun.json`\n",
    "\n",
    "Schema: `{config, per_run:[…], aggregate:{… mean+std cho moi metric …}, narrative_corrected:\"…\"}`"
))

cells.append(code(
    "def _ms(mean_v, std_v):\n",
    "    return {'mean': round(float(mean_v), 5), 'std': round(float(std_v), 5)}\n",
    "\n",
    "per_run_list = []\n",
    "for run_id, art in all_runs.items():\n",
    "    per_run_list.append({\n",
    "        'run_id'               : run_id,\n",
    "        'platt_params'         : art['platt_params'],\n",
    "        'binary_performance'   : {nm: {k: round(v, 5) for k, v in art['perf'][nm].items()} for nm in MODEL_NAMES},\n",
    "        'calibration'          : {nm: {k: round(v, 5) for k, v in art['ece'][nm].items()} for nm in MODEL_NAMES},\n",
    "        'auc_roc'              : {nm: round(art['auc_roc'][nm], 5) for nm in MODEL_NAMES},\n",
    "        'auc_pr'               : {nm: round(art['auc_pr'][nm],  5) for nm in MODEL_NAMES},\n",
    "        'per_group_accuracy'   : {grp: {nm: round(v, 5) for nm, v in d.items()}\n",
    "                                   for grp, d in art['per_group_acc'].items()},\n",
    "        'complementarity_rare' : art['complementarity_rare'],\n",
    "        'mcnemar'              : {'b': art['mcnemar']['b'], 'c': art['mcnemar']['c'],\n",
    "                                   'chi2': round(art['mcnemar']['chi2'], 5)\n",
    "                                            if not (art['mcnemar']['chi2'] != art['mcnemar']['chi2']) else None,\n",
    "                                   'p_value': round(art['mcnemar']['p_value'], 5)\n",
    "                                            if not (art['mcnemar']['p_value'] != art['mcnemar']['p_value']) else None},\n",
    "        'cohens_d_margin_rare' : round(art['cohens_d_margin_rare'], 5)\n",
    "                                  if not (art['cohens_d_margin_rare'] != art['cohens_d_margin_rare']) else None,\n",
    "    })\n",
    "\n",
    "aggregate = {\n",
    "    'f1'                   : {nm: _ms(agg_flat.loc[nm,'f1_mean'],        agg_flat.loc[nm,'f1_std'])        for nm in MODEL_NAMES},\n",
    "    'acc'                  : {nm: _ms(agg_flat.loc[nm,'acc_mean'],       agg_flat.loc[nm,'acc_std'])       for nm in MODEL_NAMES},\n",
    "    'ece_full'             : {nm: _ms(agg_flat.loc[nm,'ece_full_mean'],  agg_flat.loc[nm,'ece_full_std'])  for nm in MODEL_NAMES},\n",
    "    'ece_rare'             : {nm: _ms(agg_flat.loc[nm,'ece_rare_mean'],  agg_flat.loc[nm,'ece_rare_std'])  for nm in MODEL_NAMES},\n",
    "    'auc_roc'              : {nm: _ms(agg_flat.loc[nm,'auc_roc_mean'],   agg_flat.loc[nm,'auc_roc_std'])   for nm in MODEL_NAMES},\n",
    "    'auc_pr'               : {nm: _ms(agg_flat.loc[nm,'auc_pr_mean'],    agg_flat.loc[nm,'auc_pr_std'])    for nm in MODEL_NAMES},\n",
    "    'mcnemar_chi2_QSVM_vs_RBF' : _ms(*agg_stats['mcnemar_chi2']),\n",
    "    'mcnemar_p_QSVM_vs_RBF'    : _ms(*agg_stats['mcnemar_p']),\n",
    "    'cohens_d_margin_rare_QSVM_vs_RBF' : _ms(*agg_stats['cohens_d_margin_rare']),\n",
    "    'complementarity_rare' : {\n",
    "        'qsvm_wins'    : _ms(*agg_stats['qsvm_wins']),\n",
    "        'rbf_wins'     : _ms(*agg_stats['rbf_wins']),\n",
    "        'both_correct' : _ms(*agg_stats['both_correct']),\n",
    "        'both_wrong'   : _ms(*agg_stats['both_wrong']),\n",
    "    },\n",
    "}\n",
    "\n",
    "narrative_corrected = (\n",
    "    f'Cohen\\'s d = {agg_stats[\"cohens_d_margin_rare\"][0]:+.4f} ± {agg_stats[\"cohens_d_margin_rare\"][1]:.4f}. '\n",
    "    f'Dau am ⇒ |margin| cua RBF lon hon QSVM tren lop hiem (KHONG phai \"QSVM margin tighter\" '\n",
    "    f'nhu narrative C5 don-run cu). Loi the QSVM khong den tu do rong margin ma den tu: '\n",
    "    f'(1) ECE_rare = {ece_q:.4f} (QSVM) vs {ece_r:.4f} (RBF) — calibration tot hon '\n",
    "    f'(Δ={ece_diff:+.4f}); '\n",
    "    f'(2) AUC-PR = {ap_q:.4f} (QSVM) vs {ap_r:.4f} (RBF) — ranking quality tot hon '\n",
    "    f'(Δ={ap_diff:+.4f}). '\n",
    "    f'McNemar mean p = {p_mean:.4f} (count predictions tied khi n_rare=10 → can multi-run de tang power, '\n",
    "    f'nhung gap ve calibration/ranking on dinh qua 5 runs).'\n",
    ")\n",
    "\n",
    "c5_multirun = {\n",
    "    'contribution'         : 'C5-MultiRun',\n",
    "    'title'                : 'Confidence Calibration — Multi-Run (5 trains x 1 fixed test)',\n",
    "    'config': {\n",
    "        'config_tag'         : CONFIG_TAG,\n",
    "        'run_ids'            : RUN_IDS,\n",
    "        'train_size'         : TRAIN_SIZE,\n",
    "        'test_path'          : str(TEST_PATH.relative_to(ROOT)),\n",
    "        'test_size'          : int(len(y_test)),\n",
    "        'n_rare'             : int(rare_mask.sum()),\n",
    "        'rare_classes'       : RARE_GROUPS,\n",
    "        'n_bins_full'        : N_BINS_FULL,\n",
    "        'n_bins_rare'        : N_BINS_RARE,\n",
    "        'C_QSVM'             : C_QSVM,\n",
    "        'C_RBF'              : C_RBF,\n",
    "        'C_POLY'             : C_POLY,\n",
    "        'poly_degree'        : POLY_DEGREE,\n",
    "        'reps'               : REPS,\n",
    "        'entanglement'       : ENTANGLEMENT,\n",
    "        'backend'            : 'FidelityStatevectorKernel',\n",
    "        'calibration_method' : 'Platt Scaling (LogisticRegression C=1e10)',\n",
    "        'binning_strategy'   : 'Adaptive Equal-Frequency Binning',\n",
    "    },\n",
    "    'per_run'             : per_run_list,\n",
    "    'aggregate'           : aggregate,\n",
    "    'narrative_corrected' : narrative_corrected,\n",
    "    'reports_generated'   : [\n",
    "        'reports/c5_multirun_ece.png',\n",
    "        'reports/c5_multirun_auc.png',\n",
    "        'reports/c5_multirun_trends.png',\n",
    "        'reports/c5_multirun_reliability_rep.png',\n",
    "    ],\n",
    "}\n",
    "\n",
    "out_path = DATA_DIR / 'c5_results_multirun.json'\n",
    "with open(out_path, 'w', encoding='utf-8') as f:\n",
    "    json.dump(c5_multirun, f, ensure_ascii=False, indent=2)\n",
    "\n",
    "print('='*70)\n",
    "print('  C5 MULTI-RUN — EXPORTED')\n",
    "print('='*70)\n",
    "print(f'  JSON : {out_path}')\n",
    "print(f'  PNGs : {len(c5_multirun[\"reports_generated\"])} files in reports/')\n",
    "print(f'\\n  Narrative_corrected:\\n  {narrative_corrected}')"
))

# ────────────────────────────────────────────────────────────────────────────
# Build notebook JSON
# ────────────────────────────────────────────────────────────────────────────
nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "codemirror_mode": {"name": "ipython", "version": 3},
                          "file_extension": ".py", "mimetype": "text/x-python",
                          "nbconvert_exporter": "python", "pygments_lexer": "ipython3",
                          "version": "3.11"}
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

with open(NB_OUT, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f'Notebook ghi tai: {NB_OUT}')
print(f'  Tong so cell: {len(cells)}')
