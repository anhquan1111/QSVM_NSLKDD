"""
Cấu hình tập trung cho toàn bộ pipeline QSVM-IDS NISQ.
Tất cả các notebook và script đều import từ file này để đảm bảo nhất quán.

Cách dùng trong notebook (chạy từ thư mục notebooks/):
    import sys; sys.path.insert(0, '..')
    from config import *
"""

from pathlib import Path
import numpy as np

# ════════════════════════════════════════════════════════════
# 1. DIRECTORY PATHS
# ════════════════════════════════════════════════════════════

# -- Thư mục gốc của project (nơi đặt file config.py này) --
ROOT_DIR = Path(__file__).parent.resolve()

# -- Thư mục dữ liệu --
DATA_RAW_DIR       = ROOT_DIR / "data" / "raw"
DATA_PROCESSED_DIR = ROOT_DIR / "data" / "processed_data"
MULTI_RUN_DIR      = DATA_PROCESSED_DIR / "multi_run"

# -- Thư mục model và kết quả --
MODELS_DIR    = ROOT_DIR / "models"
QSVM_CACHE_DIR = MODELS_DIR / "qsvm_cache"
REPORTS_DIR   = ROOT_DIR / "reports"

# -- Đường dẫn dữ liệu thô NSL-KDD (đầu vào cho preprocess.ipynb) --
NSLKDD_TRAIN_RAW = DATA_RAW_DIR / "KDDTrain+.txt"
NSLKDD_TEST_RAW  = DATA_RAW_DIR / "KDDTest+.txt"

# -- Đường dẫn dữ liệu đã làm sạch (đầu ra của preprocess.ipynb) --
NSLKDD_TRAIN_CLEAN = DATA_PROCESSED_DIR / "NSL_KDD_Train_Cleaned.csv"
NSLKDD_TEST_CLEAN  = DATA_PROCESSED_DIR / "NSL_KDD_Test_Cleaned.csv"

# -- Đường dẫn đa dataset (dùng cho PCA generalization, C4+) --
TRAIN_DATA_PATHS = {
    "NSL-KDD"  : DATA_PROCESSED_DIR / "NSL_KDD_Train_Cleaned.csv",
    "UNSW-NB15": DATA_PROCESSED_DIR / "UNSW_NB15_Train_Selected.csv",
}
TEST_DATA_PATHS = {
    "NSL-KDD"  : DATA_PROCESSED_DIR / "NSL_KDD_Test_Cleaned.csv",
    "UNSW-NB15": DATA_PROCESSED_DIR / "UNSW_NB15_Test_Selected.csv",
}

# -- Đường dẫn artifact đã lưu --
FEATURE_SELECTOR_PATHS = {
    "NSL-KDD"  : MODELS_DIR / "feature_selector_k20.joblib",
    "UNSW-NB15": MODELS_DIR / "feature_selector_k20.joblib",
}
PCA_MODEL_PATH  = MODELS_DIR / "pca_4components.joblib"
SCALER_PATH     = MODELS_DIR / "scaler_minmax_pi.joblib"
QSVM_MODEL_PATH = MODELS_DIR / "qsvm_model.pkl"
CSVM_MODEL_PATH = MODELS_DIR / "csvm_model.pkl"

# ════════════════════════════════════════════════════════════
# 2. DATA SCHEMA
# ════════════════════════════════════════════════════════════

# -- 43 cột gốc của NSL-KDD (41 features + label + difficulty_level) --
COLUMNS = [
    "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes",
    "land", "wrong_fragment", "urgent", "hot", "num_failed_logins", "logged_in",
    "num_compromised", "root_shell", "su_attempted", "num_root", "num_file_creations",
    "num_shells", "num_access_files", "num_outbound_cmds", "is_host_login",
    "is_guest_login", "count", "srv_count", "serror_rate", "srv_serror_rate",
    "rerror_rate", "srv_rerror_rate", "same_srv_rate", "diff_srv_rate",
    "srv_diff_host_rate", "dst_host_count", "dst_host_srv_count",
    "dst_host_same_srv_rate", "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate", "dst_host_serror_rate", "dst_host_srv_serror_rate",
    "dst_host_rerror_rate", "dst_host_srv_rerror_rate", "label", "difficulty_level",
]

CATEGORICAL_COLS = ["protocol_type", "service", "flag"]
LABEL_COLS       = ["label", "label_binary", "label_multiclass", "attack_category"]
EXCLUDED_COLS    = ["label", "difficulty_level"]

# -- Map attack type → category (nguồn: KDD Cup 1999 + NSL-KDD paper) --
ATTACK_CATEGORY_MAP = {
    # Normal
    "normal"          : "Normal",
    # DoS — Denial of Service
    "neptune"         : "DoS",  "smurf"        : "DoS",
    "pod"             : "DoS",  "teardrop"     : "DoS",
    "back"            : "DoS",  "land"         : "DoS",
    "mailbomb"        : "DoS",  "apache2"      : "DoS",
    "processtable"    : "DoS",  "udpstorm"     : "DoS",
    "worm"            : "DoS",
    # Probe — Surveillance / Scanning
    "ipsweep"         : "Probe", "portsweep"   : "Probe",
    "nmap"            : "Probe", "satan"        : "Probe",
    "mscan"           : "Probe", "saint"        : "Probe",
    # R2L — Remote to Local
    "ftp_write"       : "R2L",  "guess_passwd" : "R2L",
    "imap"            : "R2L",  "multihop"     : "R2L",
    "phf"             : "R2L",  "spy"          : "R2L",
    "warezclient"     : "R2L",  "warezmaster"  : "R2L",
    "sendmail"        : "R2L",  "named"        : "R2L",
    "snmpgetattack"   : "R2L",  "xlock"        : "R2L",
    "xsnoop"          : "R2L",  "httptunnel"   : "R2L",
    "snmpguess"       : "R2L",
    # U2R — User to Root
    "buffer_overflow" : "U2R",  "loadmodule"   : "U2R",
    "perl"            : "U2R",  "rootkit"      : "U2R",
    "sqlattack"       : "U2R",  "xterm"        : "U2R",
    "ps"              : "U2R",
}

# ════════════════════════════════════════════════════════════
# 3. ML PIPELINE PARAMETERS
# ════════════════════════════════════════════════════════════

# -- Reproducibility --
RANDOM_STATE = 42  # dùng thống nhất dưới mọi tên: SEED, GLOBAL_SEED, RANDOM_STATE

# -- C1 SelectKBest (f_classif) --
K_CANDIDATES      = [4, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 70, 100]
K_FINAL           = 20        # xác định bằng elbow/plateau criterion (5-fold CV)
PLATEAU_THRESHOLD = 0.01      # dừng tìm K khi cải thiện F1 < 0.01
N_CV_SUBSAMPLE    = 5000      # số mẫu dùng trong CV tuning SelectKBest
N_CV_FOLDS        = 5         # stratified k-fold cho mọi đánh giá CV

# -- C1 PCA (đa mục tiêu Pareto) --
VARIANCE_THRESHOLD = 0.85     # ràng buộc: V(n) ≥ 85% explained variance
N_RANGE            = range(2, 11)   # không gian tìm kiếm số components
GRID_RESOLUTION    = 30       # độ phân giải lưới cho decision boundary 4D→2D
N_BOOTSTRAP        = 200      # số lần bootstrap để tính CI
BOOTSTRAP_SAMPLE   = 5000     # số mẫu mỗi lần bootstrap (Pareto analysis)

# -- Kích thước ablation và sampling --
N_ABL        = 3000  # mẫu cho ablation study C1
N_QSVM_TRAIN = 100   # mẫu train trong ablation QSVM (C1)
N_QSVM_TEST  = 100   # mẫu test trong ablation QSVM (C1)

# -- Multi-run statistical validation --
TRAIN_SIZES = [100, 200, 500]
TEST_SIZES  = [100, 200, 300]
N_RUNS      = 5
RUN_SIZE    = 100
MIN_RARE    = max(5, RUN_SIZE // 20)  # mẫu tối thiểu cho U2R / R2L mỗi run

# -- Classical SVM baselines (C3) --
C_SVM       = 10.0
POLY_DEGREE = 2
RBF_GAMMA   = "scale"  # thử 'scale', 'auto', hoặc float cụ thể

# -- Nhãn hiển thị cho qubit sweep (PCA) --
QUBIT_MARKS = {4: "4-qubit", 8: "8-qubit", 16: "16-qubit"}

# ════════════════════════════════════════════════════════════
# 4. QUANTUM PARAMETERS (NISQ)
# ════════════════════════════════════════════════════════════

# -- Ràng buộc phần cứng NISQ --
N_QUBITS    = 4               # số qubit = số PCA components (hard constraint)
HILBERT_DIM = 2 ** N_QUBITS   # = 16; kích thước không gian Hilbert
ANGLE_MAX   = np.pi           # giới hạn trên của MinMaxScaler → [0, π]

# -- ZZFeatureMap dùng cho training QSVM (C3, C4, C5, C6) --
ZZ_REPS         = 2       # số lần lặp circuit (reps); thử [1, 2, 3]
ZZ_ENTANGLEMENT = "full"  # kiểu entanglement; thử 'linear', 'circular', 'sca', 'full'
C_QSVM          = 1.0     # regularization C cho QSVM-ZZ; thử [0.1, 1, 10, 100]
SHOTS           = 512     # shots mỗi lần tính kernel; thử [256, 512, 1024]

# -- ZZFeatureMap dùng cho phân tích expressibility (C2) --
ZZ_REPS_TARGET         = 3       # reps trong C2 expressibility sweep
ZZ_ENTANGLEMENT_TARGET = "full"

# -- ZFeatureMap ablation (không có entanglement, so sánh với ZZ trong C3) --
REPS_Z   = 2    # giữ bằng ZZ_REPS để so sánh công bằng
C_QSVM_Z = 1.0  # giữ bằng C_QSVM để so sánh công bằng

# -- C2 Expressibility analysis --
N_SUBSAMPLE  = 300   # mẫu cho kernel matrix chính (~45K evaluations)
N_CONC       = 150   # mẫu nhỏ hơn cho concentration sweep theo reps
N_EXPR_PAIRS = 2000  # số cặp ngẫu nhiên để vẽ histogram expressibility

# -- C3 Kernel geometry --
TRAIN_SIZE     = 100  # mẫu train trong C3 model training
TEST_SIZE      = 100  # mẫu test trong C3
KM_SAMPLE_SIZE = 100  # mẫu để tính kernel matrix n×n (heatmap)
N_GRID_QUANTUM   = 20  # độ phân giải lưới decision boundary cho QSVM (chậm)
N_GRID_CLASSICAL = 40  # độ phân giải lưới decision boundary cho classical SVM

# -- Các cặp qubit được entangle (full entanglement, 4 qubit → 6 cặp) --
ZZ_PAIRS = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]

# -- Tập kernel để so sánh trong C3 --
KERNEL_LABELS_ZZ = ["quantum", "linear", "poly", "rbf"]  # ZZFeatureMap + classical
KERNEL_LABELS_Z  = ["quantum_z"]                          # ZFeatureMap ablation
