"""C4 (revision) — sample-complexity sweep + rare-attack margin analysis.

Module dùng chung cho notebook C4 trên NSL-KDD và (giai đoạn sau) UNSW-NB15.

Thiết kế bám sát ba ràng buộc:

1. **Khớp hợp đồng C2/C3.** Model, scaler, grid, seed, quy tắc chọn
   hyperparameter và công thức thống kê đều sao y `C2_revision.ipynb` /
   `C3_revision.ipynb`, để số của C4 so sánh chéo được với hai contribution kia.
   Gate G2 (`reproduce_c2_gate`) kiểm chứng điều này bằng số.

2. **Kernel tính qua statevector cache.** `FidelityStatevectorKernel.evaluate()`
   mô phỏng lại statevector ở mỗi lần gọi. Ở đây statevector Psi (N x 2^n) được
   mô phỏng một lần rồi Gram = |Psi_a^dagger Psi_b|^2 chỉ là một matmul với inner
   dim 2^n. Kết quả trùng `FidelityStatevectorKernel` tới ~1e-15
   (xem `verify_kernel_equivalence`).

3. **Rare-attack dùng signed margin.** `docs/revision/c4_claim_audit.md` cho thấy
   C5/C6 cũ tính effect size trên `|decision_function|`, đại lượng đo độ *tự tin*
   chứ không đo *đúng/sai*. Ở đây signed margin `y_pm * f(x)` là primary,
   `|margin|` chỉ giữ để bắc cầu với số cũ.

Protocol: `configs/c4_protocol.json`.
"""

from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t
from scipy.stats import wilcoxon
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.svm import SVC

try:  # xgboost là dependency bắt buộc của protocol, nhưng không để import lỗi làm chết module
    from xgboost import XGBClassifier

    XGBOOST_AVAILABLE = True
    XGBOOST_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover
    XGBClassifier = None
    XGBOOST_AVAILABLE = False
    XGBOOST_IMPORT_ERROR = repr(exc)


# ---------------------------------------------------------------------------
# 0. Hằng số và tiện ích chung
# ---------------------------------------------------------------------------

ANGLE_MAX = float(np.pi)

# Khớp config.py của repo. Khai báo lại ở đây để module không phụ thuộc thứ tự
# import/cwd; `load_data` sẽ kiểm tra lại với config.py nếu import được.
LABEL_COLS = ["label", "label_binary", "label_multiclass", "attack_category"]

ALL_MODELS = [
    "QSVM_ZZ",
    "QSVM_Z",
    "SVM_Linear",
    "SVM_Poly2",
    "SVM_RBF",
    "RandomForest",
    "XGBoost",
]
ALL_BASELINES = [m for m in ALL_MODELS if m != "QSVM_ZZ"]

# Cùng phân họ với C3 để Holm correction áp trên đúng family như nhau.
INFERENTIAL_FAMILIES = {
    "entanglement": ["QSVM_Z"],
    "strong_tabular": ["RandomForest", "XGBoost"],
    "classical_kernel": ["SVM_RBF", "SVM_Poly2", "SVM_Linear"],
}
BASELINE_FAMILY_BY_MODEL = {
    model: family for family, models in INFERENTIAL_FAMILIES.items() for model in models
}

QUANTUM_MODELS = ("QSVM_ZZ", "QSVM_Z")
SVM_MODELS = ("SVM_Linear", "SVM_Poly2", "SVM_RBF")
TREE_MODELS = ("RandomForest", "XGBoost")

RARE_CATEGORIES = ("U2R", "R2L")


@dataclass(frozen=True)
class DatasetSpec:
    """Mô tả một dataset để pipeline dùng chung cho NSL-KDD và UNSW-NB15.

    `stratify_groups` gộp các lớp tấn công thành nhãn phân tầng: lớp hiếm phải được
    gộp lại, nếu không thì ở N nhỏ chúng biến mất khỏi tập con (xem
    `configs/c4_protocol.json`, changelog S0.2).
    """

    name: str
    processed_dir: str
    train_file: str
    test_file: str
    fixed_test_file: str | None
    reader: str                      # "csv" hoặc "parquet"
    rare_categories: tuple[str, ...]
    stratify_groups: dict            # tên nhóm -> danh sách attack_category
    n_qubits: int
    select_k: int
    anchor_run_files: str | None     # thư mục chứa train_run{i}, None nếu không có
    tuning_file: str | None


DATASETS = {
    "nslkdd": DatasetSpec(
        name="NSL-KDD",
        processed_dir="data/nslkdd/processed_data",
        train_file="NSL_KDD_Train_Cleaned.csv",
        test_file="NSL_KDD_Test_Cleaned.csv",
        fixed_test_file="NSL_KDD_Test_Sample300.csv",
        reader="csv",
        rare_categories=("U2R", "R2L"),
        stratify_groups={"Normal": ["Normal"], "DoS": ["DoS"], "Probe": ["Probe"],
                         "Rare": ["R2L", "U2R"]},
        n_qubits=4,
        select_k=20,
        anchor_run_files="multi_run",
        tuning_file="c2_tuning/train_tuning_2000.csv",
    ),
    "unsw": DatasetSpec(
        name="UNSW-NB15",
        processed_dir="data/unsw/processed_data",
        train_file="UNSW_Train_Cleaned.parquet",
        test_file="UNSW_Test_Cleaned.parquet",
        fixed_test_file=None,
        reader="parquet",
        # 4 lớp hiếm nhất: 2.86% train / 2.04% test
        rare_categories=("Worms", "Shellcode", "Backdoor", "Analysis"),
        # gộp 10 lớp thành 5 nhóm phân tầng
        stratify_groups={"Normal": ["Normal"], "Generic": ["Generic"],
                         "Exploits": ["Exploits"],
                         "Frequent": ["Fuzzers", "DoS", "Reconnaissance"],
                         "Rare": ["Worms", "Shellcode", "Backdoor", "Analysis"]},
        n_qubits=6,      # từ U1: luật C1 chạy độc lập trên UNSW cho n*=6
        select_k=35,     # từ U1: elbow delta=0.01 trên đường cong CV
        anchor_run_files=None,
        tuning_file=None,
    ),
}


def get_spec(dataset) -> DatasetSpec:
    if isinstance(dataset, DatasetSpec):
        return dataset
    if dataset not in DATASETS:
        raise ValueError(f"Dataset không hợp lệ: {dataset!r}. Có: {list(DATASETS)}")
    return DATASETS[dataset]


def read_table(path: Path):
    return pd.read_parquet(path) if str(path).endswith(".parquet") else pd.read_csv(path)


def find_project_root(start: Path | str | None = None) -> Path:
    """Tìm root repo bằng sự hiện diện của config.py (giống C2/C3)."""
    here = Path(start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "config.py").exists():
            return candidate
    raise FileNotFoundError("Không tìm thấy config.py trong cwd hoặc parent directories.")


def file_sha256(path: Path | str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_protocol(root: Path | None = None) -> dict:
    root = root or find_project_root()
    with open(root / "configs" / "c4_protocol.json", encoding="utf-8") as fp:
        return json.load(fp)


def row_signatures(df: pd.DataFrame, feature_cols: list[str]) -> np.ndarray:
    """Chữ ký hàng để ghép/loại trùng giữa các CSV không có cột id.

    Dùng đúng cách C2 kiểm tra disjointness (`pd.util.hash_pandas_object`).
    """
    return pd.util.hash_pandas_object(
        df[feature_cols + ["label_binary"]], index=False
    ).to_numpy(dtype=np.uint64)


def stratify_label(df: pd.DataFrame, dataset="nslkdd") -> np.ndarray:
    """Nhãn phân tầng theo nhóm của dataset, lớp hiếm được gộp thành một nhóm.

    NSL-KDD dùng 4 nhóm {Normal, DoS, Probe, Rare}; UNSW-NB15 dùng 5 nhóm
    {Normal, Generic, Exploits, Frequent, Rare}. Gộp lớp hiếm là bắt buộc: nếu phân
    tầng theo `attack_category` gốc thì ở N nhỏ các lớp hiếm bị làm tròn về 0 và bảng
    rare-attack sẽ rỗng.
    """
    spec = get_spec(dataset)
    cat = df["attack_category"].to_numpy()
    out = np.array(["Other"] * len(cat), dtype=object)
    for group, members in spec.stratify_groups.items():
        out[np.isin(cat, members)] = group
    return out


def four_way_label(df: pd.DataFrame) -> np.ndarray:
    """Tương thích ngược: nhãn phân tầng 4 lớp của NSL-KDD."""
    return stratify_label(df, "nslkdd")


def rare_mask(df: pd.DataFrame, dataset="nslkdd") -> np.ndarray:
    """Mặt nạ các mẫu thuộc lớp tấn công hiếm của dataset."""
    return df["attack_category"].isin(get_spec(dataset).rare_categories).to_numpy()


# ---------------------------------------------------------------------------
# 1. Lấy mẫu lồng nhau (nested subsampling)
# ---------------------------------------------------------------------------


def stratified_indices(labels: np.ndarray, n_samples: int, seed: int) -> np.ndarray:
    """Chọn `n_samples` chỉ số phân tầng theo `labels`, largest-remainder allocation.

    Sao y `stratified_binary_indices` của C2 nhưng nhận nhãn nhiều lớp, để phân bổ
    lớp hiếm không bị làm tròn xuống 0.
    """
    rng = np.random.RandomState(seed)
    labels = np.asarray(labels)
    classes, counts = np.unique(labels, return_counts=True)
    exact = counts / counts.sum() * n_samples
    allocations = np.floor(exact).astype(int)
    # Largest remainder: phân phần dư cho lớp có phần thập phân lớn nhất còn lại.
    while allocations.sum() < n_samples:
        allocations[np.argmax(exact - allocations)] += 1
    while allocations.sum() > n_samples:
        eligible = np.where(allocations > 0)[0]
        allocations[eligible[np.argmin((exact - allocations)[eligible])]] -= 1

    selected: list[int] = []
    for cls, n_take in zip(classes, allocations):
        pool = np.where(labels == cls)[0]
        take = min(int(n_take), len(pool))
        if take > 0:
            selected.extend(rng.choice(pool, size=take, replace=False).tolist())
    selected_arr = np.asarray(selected, dtype=int)
    rng.shuffle(selected_arr)
    return selected_arr


@dataclass
class DataBundle:
    """Toàn bộ dữ liệu NSL-KDD cần cho C4, nạp một lần rồi tái dùng."""

    feature_cols: list[str]
    run_frames: dict[int, pd.DataFrame]
    df_tune: pd.DataFrame
    df_test_300: pd.DataFrame
    df_test_full: pd.DataFrame
    df_train_all: pd.DataFrame
    df_pool: pd.DataFrame  # train_clean \ tuning — pool hợp lệ để rút mẫu train
    spec: "DatasetSpec | None" = None
    anchor_size: int = 1000


def load_data(root: Path | None = None, verbose: bool = True,
              dataset="nslkdd") -> DataBundle:
    """Nạp dữ liệu của một dataset: pool huấn luyện, tuning set, các tập test.

    `df_pool` = train \ tuning. Với NSL-KDD, cố ý KHÔNG loại các `train_run*` khác ra
    khỏi pool: 10 run của C2 vốn không rời nhau (overlap cặp đôi trung bình 17.5 dòng,
    riêng phần rare là 11/100), chúng chỉ được yêu cầu rời với tuning set. Loại hết mọi
    run ra khỏi pool sẽ vét cạn lớp hiếm (chỉ còn 223/1047 mẫu rare).

    Với UNSW-NB15 không có sẵn tuning set; hàm tự dựng một tuning set phân tầng cỡ
    `tuning_size` bằng seed cố định, và pool là phần còn lại.
    """
    spec = get_spec(dataset)
    root = root or find_project_root()
    processed = root / spec.processed_dir

    df_train_all = read_table(processed / spec.train_file)
    df_test_full = read_table(processed / spec.test_file)
    feature_cols = [c for c in df_train_all.columns if c not in LABEL_COLS]

    if spec.tuning_file is not None:
        df_tune = read_table(processed / spec.tuning_file)
    else:
        # UNSW: dựng tuning set phân tầng, seed cố định, rời hoàn toàn với pool
        idx = stratified_indices(stratify_label(df_train_all, spec), 2000, seed=200)
        df_tune = df_train_all.iloc[np.sort(idx)].reset_index(drop=True)

    if spec.anchor_run_files is not None:
        run_frames = {
            run_id: read_table(processed / spec.anchor_run_files
                               / f"train_run{run_id}.{'parquet' if spec.reader=='parquet' else 'csv'}")
            for run_id in range(1, 11)
        }
    else:
        run_frames = {}

    if spec.fixed_test_file is not None:
        df_test_300 = read_table(processed / spec.fixed_test_file)
    else:
        idx = stratified_indices(stratify_label(df_test_full, spec), 300, seed=777)
        df_test_300 = df_test_full.iloc[np.sort(idx)].reset_index(drop=True)

    tune_sig = set(row_signatures(df_tune, feature_cols).tolist())
    all_sig = row_signatures(df_train_all, feature_cols)
    df_pool = df_train_all.loc[
        ~pd.Series(all_sig).isin(tune_sig).to_numpy()
    ].reset_index(drop=True)

    if verbose:
        print(f"dataset      : {spec.name}  (n_qubits={spec.n_qubits}, K={spec.select_k})")
        print(f"feature_cols : {len(feature_cols)}")
        print(f"tuning       : {df_tune.shape}")
        print(f"run frames   : {len(run_frames)}")
        print(f"test fixed   : {df_test_300.shape}")
        print(f"test full    : {df_test_full.shape}")
        print(f"train all    : {df_train_all.shape}")
        print(f"pool         : {df_pool.shape}")
        print(f"  rare trong pool: {int(rare_mask(df_pool, spec).sum())}")

    return DataBundle(
        feature_cols=feature_cols,
        run_frames=run_frames,
        df_tune=df_tune,
        df_test_300=df_test_300,
        df_test_full=df_test_full,
        df_train_all=df_train_all,
        df_pool=df_pool,
        spec=spec,
    )


# --- Thành phần lớp mục tiêu ------------------------------------------------

def composition_of(df: pd.DataFrame, dataset="nslkdd") -> dict[str, float]:
    """Tỉ lệ các nhóm phân tầng của một DataFrame."""
    lab = stratify_label(df, dataset)
    classes, counts = np.unique(lab, return_counts=True)
    return {str(c): float(n) / len(lab) for c, n in zip(classes, counts)}


def allocate(composition: dict[str, float], n: int,
             floor_alloc: dict[str, int] | None = None) -> dict[str, int]:
    """Phân bổ n mẫu theo `composition`, largest-remainder, có sàn tuỳ chọn.

    `floor_alloc` (số đã chọn ở N nhỏ hơn) đảm bảo phân bổ đơn điệu tăng theo N —
    điều kiện cần để chuỗi subset lồng nhau được.
    """
    classes = sorted(composition)
    exact = np.array([composition[c] * n for c in classes], dtype=float)
    alloc = np.floor(exact).astype(int)
    if floor_alloc:
        alloc = np.maximum(alloc, np.array([floor_alloc.get(c, 0) for c in classes]))
    while alloc.sum() < n:
        alloc[np.argmax(exact - alloc)] += 1
    while alloc.sum() > n:
        slack = alloc - np.array([(floor_alloc or {}).get(c, 0) for c in classes])
        eligible = np.where(slack > 0)[0]
        if len(eligible) == 0:
            break
        alloc[eligible[np.argmin((exact - alloc)[eligible])]] -= 1
    return {c: int(a) for c, a in zip(classes, alloc)}


# --- Chuỗi subset lồng nhau -------------------------------------------------

SAMPLING_REGIMES = ("matched", "natural")


def build_nested_chain(data: DataBundle, run_id: int, n_grid: list[int], run_seed: int,
                       regime: str = "matched") -> dict[int, pd.DataFrame]:
    """Dựng chuỗi subset LỒNG NHAU cho một run: D_{N1} ⊂ D_{N2} ⊂ ... ⊂ D_{Nk}.

    Lồng nhau là bắt buộc cho đường cong sample-complexity: nếu mỗi mốc N là một
    mẫu độc lập thì biến thiên giữa các mốc trộn lẫn "thêm dữ liệu" với "đổi mẫu".

    Hai chế độ lấy mẫu, trả lời hai câu hỏi khác nhau:

    - ``matched``: giữ nguyên thành phần lớp của `train_run{i}` (NSL-KDD: Rare ≈ 10%,
      tức **giàu gấp ~12 lần** tỉ lệ tự nhiên 0.83%). Chỉ N thay đổi, nên đây là thí
      nghiệm sample-complexity đúng nghĩa và so sánh trực tiếp được với C2/C3. Neo tại
      N=1000 = đúng `train_run{i}`. Chỉ dùng được khi dataset có sẵn run frames.

    - ``natural``: giữ tỉ lệ lớp tự nhiên của tập train. Không neo. Đi được tới N rất
      lớn mà không vét cạn lớp hiếm, và phản ánh điều kiện triển khai thật.
    """
    if regime not in SAMPLING_REGIMES:
        raise ValueError(f"regime phải thuộc {SAMPLING_REGIMES}, nhận {regime!r}")
    ds = data.spec or get_spec("nslkdd")
    if regime == "matched" and not data.run_frames:
        raise ValueError(
            f"Dataset {ds.name} không có run frames neo sẵn nên không hỗ trợ regime "
            f"'matched'. Dùng regime='natural'."
        )

    n_grid = sorted(int(n) for n in n_grid)
    fc = data.feature_cols
    anchor = data.anchor_size
    base = data.run_frames[int(run_id)].reset_index(drop=True) if data.run_frames else None

    pool = data.df_pool
    pool_lab = stratify_label(pool, ds)
    pool_sig = row_signatures(pool, fc)

    composition = (composition_of(base, ds) if regime == "matched"
                   else composition_of(data.df_train_all, ds))

    chains: dict[int, pd.DataFrame] = {}

    # ---- Nhánh giảm dần: các N nhỏ hơn neo, lấy lồng trong chính run frame ----
    if regime == "matched":
        current = base
        for n in [x for x in n_grid if x < anchor][::-1]:
            lab = stratify_label(current, ds)
            alloc = allocate(composition, n)
            rng = np.random.RandomState(int(run_seed) * 100_000 + n)
            picked: list[int] = []
            for cls, want in alloc.items():
                idx_cls = np.where(lab == cls)[0]
                take = min(want, len(idx_cls))
                if take:
                    picked.extend(rng.choice(idx_cls, size=take, replace=False).tolist())
            if len(picked) < n:
                remaining = np.setdiff1d(np.arange(len(current)), np.asarray(picked, dtype=int))
                picked.extend(rng.choice(remaining, size=n - len(picked), replace=False).tolist())
            current = current.iloc[sorted(picked)].reset_index(drop=True)
            chains[n] = current
        if anchor in n_grid:
            chains[anchor] = base
        ascending = [n for n in n_grid if n > anchor]
        current = base
        # Voi NSL-KDD, base den tu run_frames chu khong tu pool, nen loai theo chu ky
        # la dung (khong co ban sao trong NSL-KDD: 125.973/125.973 chu ky duy nhat).
        used_idx = set(np.where(pd.Series(pool_sig).isin(
            set(row_signatures(base, fc).tolist())).to_numpy())[0].tolist())
    else:
        ascending = list(n_grid)
        current = data.df_train_all.iloc[:0]
        used_idx = set()

    # ---- Nhánh tăng dần: bồi thêm từ pool, giữ nguyên phần đã có ----
    for n in ascending:
        need_total = allocate(composition, n)
        have = composition_of(current, ds) if len(current) else {}
        have_counts = {c: int(round(have.get(c, 0.0) * len(current))) for c in need_total}
        rng = np.random.RandomState(int(run_seed) * 100_000 + n)
        # Loai tru theo CHI SO HANG, khong theo chu ky. UNSW-NB15 co ban sao that su
        # trong du lieu (lop `Generic`: 40.000 hang / 1.800 chu ky duy nhat = trung lap
        # 95,5%). Loai theo chu ky se (a) chan tran N o ~8.000 va (b) am tham khu trung
        # lap tap train, tuc doi phan bo so voi dataset that. Lay mau khong hoan lai theo
        # chi so giu dung phan bo tu nhien. Voi NSL-KDD hai cach la mot vi moi hang deu
        # co chu ky duy nhat.
        avail_mask = np.ones(len(pool), dtype=bool)
        if used_idx:
            avail_mask[np.fromiter(used_idx, dtype=int)] = False
        add_rows: list[int] = []
        for cls, want in need_total.items():
            deficit = want - have_counts.get(cls, 0)
            if deficit <= 0:
                continue
            cand = np.where(avail_mask & (pool_lab == cls))[0]
            take = min(deficit, len(cand))
            if take < deficit:
                raise ValueError(
                    f"Pool hết mẫu nhóm {cls!r} ở N={n} (run {run_id}, regime={regime}, "
                    f"{ds.name}): cần thêm {deficit}, chỉ còn {len(cand)}."
                )
            if take:
                add_rows.extend(rng.choice(cand, size=take, replace=False).tolist())
        shortfall = n - (len(current) + len(add_rows))
        if shortfall > 0:
            cand = np.setdiff1d(np.where(avail_mask)[0], np.asarray(add_rows, dtype=int))
            add_rows.extend(rng.choice(cand, size=shortfall, replace=False).tolist())
        current = pd.concat([current, pool.iloc[sorted(add_rows)]], ignore_index=True)
        used_idx.update(add_rows)
        chains[n] = current

    return {n: chains[n] for n in n_grid if n in chains}


def build_train_subset(data: DataBundle, run_id: int, n: int, run_seed: int,
                       regime: str = "matched", n_grid: list[int] | None = None) -> pd.DataFrame:
    """Tiện ích lấy một mốc N đơn lẻ từ chuỗi lồng nhau.

    Vẫn dựng cả chuỗi để giữ tính lồng nhau; muốn nhiều mốc thì gọi thẳng
    `build_nested_chain` cho hiệu quả.
    """
    grid = sorted(set((n_grid or [n]) + [n]))
    return build_nested_chain(data, run_id, grid, run_seed, regime)[n]


# ---------------------------------------------------------------------------
# 2. Representation: refit-per-N (primary) và frozen-C1 (secondary)
# ---------------------------------------------------------------------------


class Representation:
    """Giao diện chung: `.fit(df_train)` rồi `.transform(df)` -> (X_angles, X_pca).

    `X_pca`   : đầu vào của nhánh classical (SVM tự fit StandardScaler trong Pipeline;
                RF/XGB dùng thẳng).
    `X_angles`: đầu vào của nhánh quantum, đã đưa về [0, pi].
    """

    mode: str

    def fit(self, df_train: pd.DataFrame, feature_cols: list[str]) -> "Representation":
        raise NotImplementedError

    def transform(self, df: pd.DataFrame, feature_cols: list[str]) -> tuple[np.ndarray, np.ndarray]:
        raise NotImplementedError


class RefitPerNRepresentation(Representation):
    """SelectKBest -> PCA -> MinMax[0, pi], fit LẠI trên đúng N dòng train.

    Đây là giao thức của bản đã nộp (Sec. III-F): zero-leakage thật sự, và là điều
    kiện để claim low-data có nghĩa — representation không được hưởng thông tin từ
    125.973 mẫu train đầy đủ.
    """

    mode = "refit_per_N"

    def __init__(self, select_k: int = 20, n_components: int = 4, random_state: int = 42):
        self.select_k = select_k
        self.n_components = n_components
        self.random_state = random_state

    def fit(self, df_train: pd.DataFrame, feature_cols: list[str]) -> "RefitPerNRepresentation":
        X = df_train[feature_cols].to_numpy(dtype=np.float32)
        y = df_train["label_binary"].to_numpy(dtype=np.int64)
        k = min(self.select_k, X.shape[1])
        self.selector_ = SelectKBest(score_func=f_classif, k=k).fit(X, y)
        X_sel = self.selector_.transform(X)
        self.pca_ = PCA(n_components=self.n_components, random_state=self.random_state).fit(X_sel)
        X_pca = self.pca_.transform(X_sel)
        self.angle_scaler_ = MinMaxScaler(feature_range=(0.0, ANGLE_MAX)).fit(X_pca)
        return self

    def transform(self, df: pd.DataFrame, feature_cols: list[str]) -> tuple[np.ndarray, np.ndarray]:
        X = df[feature_cols].to_numpy(dtype=np.float32)
        X_pca = self.pca_.transform(self.selector_.transform(X))
        X_ang = np.clip(self.angle_scaler_.transform(X_pca), 0.0, ANGLE_MAX)
        return X_ang, X_pca


class FrozenC1Representation(Representation):
    """Dùng nguyên artifact đã fit của C1, chỉ transform.

    Đây chính là điều kiện của C2/C3, nên bắt buộc phải có để chạy gate G2.
    """

    mode = "frozen_c1"

    def __init__(self, root: Path | None = None):
        import joblib

        root = root or find_project_root()
        models_dir = root / "models" / "nslkdd"
        self.paths_ = {
            "feature_selector": models_dir / "feature_selector_k20.joblib",
            "pca": models_dir / "pca_4components.joblib",
            "angle_scaler": models_dir / "scaler_minmax_pi.joblib",
        }
        self.hashes_ = {name: file_sha256(p) for name, p in self.paths_.items()}
        self.selector_ = joblib.load(self.paths_["feature_selector"])
        self.pca_ = joblib.load(self.paths_["pca"])
        self.angle_scaler_ = joblib.load(self.paths_["angle_scaler"])

    def fit(self, df_train: pd.DataFrame, feature_cols: list[str]) -> "FrozenC1Representation":
        return self  # đã fit sẵn từ C1; cố tình không fit lại

    def transform(self, df: pd.DataFrame, feature_cols: list[str]) -> tuple[np.ndarray, np.ndarray]:
        X = df[feature_cols].to_numpy(dtype=np.float32)
        X_pca = self.pca_.transform(self.selector_.transform(X))
        X_ang = np.clip(self.angle_scaler_.transform(X_pca), 0.0, ANGLE_MAX)
        return X_ang, X_pca


def make_representation(mode: str, **kwargs) -> Representation:
    if mode == "refit_per_N":
        return RefitPerNRepresentation(**kwargs)
    if mode == "frozen_c1":
        return FrozenC1Representation(**kwargs)
    raise ValueError(f"Chế độ representation không hợp lệ: {mode}")


# ---------------------------------------------------------------------------
# 3. Kernel lượng tử qua statevector cache
# ---------------------------------------------------------------------------


def build_feature_map(kernel: str, n_qubits: int = 4, reps: int = 2, entanglement: str = "full"):
    """ZZFeatureMap (có entangle) hoặc ZFeatureMap (control không entangle)."""
    from qiskit.circuit.library import z_feature_map, zz_feature_map

    if kernel == "ZZ":
        return zz_feature_map(feature_dimension=n_qubits, reps=reps, entanglement=entanglement)
    if kernel == "Z":
        return z_feature_map(feature_dimension=n_qubits, reps=reps)
    raise ValueError(f"Kernel không hợp lệ: {kernel}")


def compute_statevectors(X_angles: np.ndarray, feature_map) -> np.ndarray:
    """Mô phỏng statevector cho từng dòng của `X_angles`. Chi phí O(N)."""
    from qiskit.quantum_info import Statevector

    n = len(X_angles)
    dim = 2 ** feature_map.num_qubits
    out = np.empty((n, dim), dtype=np.complex128)
    for i in range(n):
        out[i] = Statevector(feature_map.assign_parameters(X_angles[i])).data
    return out


def compute_statevectors_fast(X_angles: np.ndarray, kernel: str, n_qubits: int,
                              reps: int = 2) -> np.ndarray:
    """Statevector của Z/ZZFeatureMap tính dạng đóng, vector hoá trên toàn bộ mẫu.

    Sau mỗi lớp Hadamard, phần còn lại của feature map là **đường chéo** trong cơ sở
    tính toán. Với trạng thái cơ sở |z> có bit z_i:

        pha_Z(z)  = sum_i 2*x_i*z_i
        pha_ZZ(z) = pha_Z(z) + sum_{i<j} 2*(pi-x_i)*(pi-x_j) * (z_i XOR z_j)

    Số hạng cặp chỉ áp khi ``z_i XOR z_j = 1`` vì ZZFeatureMap hiện thực tương tác bằng
    chuỗi CNOT–RZ–CNOT. Do đó

        |psi> = (D(x) . H^{⊗n})^reps |0>

    trong đó H^{⊗n} là một phép nhân ma trận 2^n x 2^n. Toàn bộ tính được cho mọi mẫu
    cùng lúc bằng numpy, thay vì gọi `Statevector` từng mẫu một.

    Đo được: nhanh hơn đường Qiskit **457x (n=6)** đến **763x (n=4)**, và Gram khớp tới
    4.4e-15 (n=4) / 6.4e-15 (n=6) — tức trùng ở mức chính xác của số thực máy.
    `verify_kernel_equivalence` kiểm tra lại điều này ở mỗi lần chạy.
    """
    from scipy.linalg import hadamard

    if kernel not in ("ZZ", "Z"):
        raise ValueError(f"Kernel không hợp lệ: {kernel}")
    X = np.asarray(X_angles, dtype=np.float64)
    dim = 2 ** n_qubits
    bits = ((np.arange(dim)[:, None] >> np.arange(n_qubits)[None, :]) & 1).astype(np.float64)
    h_mat = hadamard(dim) / np.sqrt(dim)

    phase = X @ (2.0 * bits.T)
    if kernel == "ZZ":
        for i in range(n_qubits):
            for j in range(i + 1, n_qubits):
                phase += (2.0 * (np.pi - X[:, i]) * (np.pi - X[:, j]))[:, None] \
                         * np.abs(bits[:, i] - bits[:, j])[None, :]
    diag = np.exp(1j * phase)

    state = np.zeros((len(X), dim), dtype=np.complex128)
    state[:, 0] = 1.0
    for _ in range(reps):
        state = (state @ h_mat) * diag
    return state


def gram_from_statevectors(psi_a: np.ndarray, psi_b: np.ndarray | None = None,
                           dtype=np.float64) -> np.ndarray:
    """Gram fidelity |<psi_a|psi_b>|^2 — một phép matmul với inner dim 2^n."""
    if psi_b is None:
        psi_b = psi_a
    return (np.abs(psi_a.conj() @ psi_b.T) ** 2).astype(dtype, copy=False)


class StatevectorCache:
    """Cache statevector, có giới hạn bộ nhớ và chỉ ghi đĩa khi thực sự đáng.

    Hai ràng buộc đã đo được:

    1. **Bộ nhớ.** Một mảng statevector của tập test UNSW đầy đủ là
       82.332 x 2^6 complex128 = **84 MB**. Giữ mọi mảng trong RAM thì sau 60 cell sẽ
       cần ~10 GB và chắc chắn OOM. Vì vậy bộ nhớ chỉ giữ `mem_entries` mục gần nhất
       (LRU), đủ để hai arm trong cùng một cell dùng chung.

    2. **Đĩa.** Sau khi có `compute_statevectors_fast`, tính lại 82.332 mẫu chỉ mất
       ~0,6 giây, trong khi cache đĩa tốn ~2,3 GB cho mỗi 15 cell. Ghi đĩa do đó chỉ
       có lợi cho mảng nhỏ (statevector của tập train, dùng lại giữa các arm), nên
       mảng lớn hơn `disk_max_rows` được tính lại thay vì lưu.
    """

    def __init__(self, cache_dir: Path, n_qubits: int = 4, reps: int = 2,
                 entanglement: str = "full", mem_entries: int = 6,
                 disk_max_rows: int = 20_000):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.n_qubits = n_qubits
        self.reps = reps
        self.entanglement = entanglement
        self.mem_entries = int(mem_entries)
        self.disk_max_rows = int(disk_max_rows)
        self._feature_maps: dict[str, object] = {}
        self._mem: "OrderedDict[str, np.ndarray]" = OrderedDict()

    def feature_map(self, kernel: str):
        if kernel not in self._feature_maps:
            self._feature_maps[kernel] = build_feature_map(
                kernel, self.n_qubits, self.reps, self.entanglement
            )
        return self._feature_maps[kernel]

    def _remember(self, name: str, psi: np.ndarray) -> np.ndarray:
        self._mem[name] = psi
        self._mem.move_to_end(name)
        while len(self._mem) > self.mem_entries:
            self._mem.popitem(last=False)
        return psi

    def get(self, X_angles: np.ndarray, kernel: str, key: str,
            force: bool = False) -> np.ndarray:
        name = f"psi_{kernel}_{key}.npy"
        if not force and name in self._mem:
            self._mem.move_to_end(name)
            return self._mem[name]
        use_disk = len(X_angles) <= self.disk_max_rows
        path = self.cache_dir / name
        if use_disk and path.exists() and not force:
            psi = np.load(path)
            if len(psi) == len(X_angles):
                return self._remember(name, psi)
        psi = compute_statevectors_fast(X_angles, kernel, self.n_qubits, self.reps)
        if use_disk:
            np.save(path, psi)
        return self._remember(name, psi)

    def clear_memory(self) -> None:
        self._mem.clear()


def verify_kernel_equivalence(X_angles: np.ndarray, kernel: str = "ZZ", n_qubits: int = 4,
                              reps: int = 2, entanglement: str = "full",
                              tol: float = 1e-9) -> dict:
    """So Gram tính từ statevector cache với `FidelityStatevectorKernel.evaluate()`.

    Bắt buộc chạy mỗi phiên: nếu Qiskit đổi quy ước gate, kết quả sẽ lệch và ta
    phải biết ngay chứ không phải sau khi đã chạy xong toàn bộ thí nghiệm.
    """
    from qiskit_machine_learning.kernels import FidelityStatevectorKernel

    fmap = build_feature_map(kernel, n_qubits, reps, entanglement)
    reference = FidelityStatevectorKernel(feature_map=fmap, enforce_psd=True).evaluate(X_angles)
    mine = gram_from_statevectors(
        compute_statevectors_fast(X_angles, kernel, n_qubits, reps))
    max_abs_diff = float(np.abs(reference - mine).max())
    return {
        "kernel": kernel,
        "n_samples": int(len(X_angles)),
        "max_abs_diff": max_abs_diff,
        "tolerance": tol,
        "passed": bool(max_abs_diff < tol),
    }


# ---------------------------------------------------------------------------
# 4. Model — khớp chính xác cấu hình của C2
# ---------------------------------------------------------------------------


# Trần số vòng lặp của libsvm. Mặc định của sklearn là -1 (không giới hạn), và trên
# UNSW-NB15 điều đó khiến SVM-Poly2 ở C >= 5 KHÔNG HỘI TỤ trên một số fold: đo được
# C <= 3 chạy tức thì còn C = 5 chạy quá 400 giây mà chưa xong. Đây là bệnh SMO đã biết
# với kernel đa thức ở C lớn. Trần này chỉ dừng sớm những cấu hình vốn không hội tụ —
# chúng sẽ có điểm CV thấp và không được chọn. Đã kiểm chứng không ảnh hưởng NSL-KDD:
# số vòng lặp lớn nhất quan sát được ở đó là 1.692 (C=10), thấp hơn trần hàng nghìn lần.
SVC_MAX_ITER = 2_000_000


def make_svm_estimator(name: str) -> Pipeline:
    """Pipeline StandardScaler -> SVC, giống hệt `svm_estimators` của C2."""
    kernels = {
        "SVM_Linear": dict(kernel="linear"),
        "SVM_Poly2": dict(kernel="poly", degree=2, gamma="scale"),
        "SVM_RBF": dict(kernel="rbf", gamma="scale"),
    }
    if name not in kernels:
        raise ValueError(f"Không phải SVM baseline: {name}")
    return Pipeline([("scaler", StandardScaler()),
                     ("svc", SVC(probability=False, max_iter=SVC_MAX_ITER,
                                 **kernels[name]))])


def make_tree_estimator(name: str, params: dict, run_seed: int):
    """RF / XGB với đúng tham số cố định của C2 (kể cả class_weight và tree_method).

    RandomForest giữ `n_jobs=-1`: đã kiểm chứng tất định (khớp chính xác 10/10 run
    trong gate G2). XGBoost buộc `n_jobs=1`: `tree_method='hist'` gộp histogram theo
    thứ tự thread nên `n_jobs=-1` làm kết quả phụ thuộc số core của máy chạy
    (đo được: 0.8365 với 16 thread vs 0.8533 với 1 thread, cùng seed cùng dữ liệu).
    """
    if name == "RandomForest":
        return RandomForestClassifier(
            random_state=run_seed, n_jobs=-1, class_weight="balanced_subsample", **params
        )
    if name == "XGBoost":
        if not XGBOOST_AVAILABLE:
            raise RuntimeError(f"XGBoost không import được: {XGBOOST_IMPORT_ERROR}")
        return XGBClassifier(
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=run_seed,
            n_jobs=1,
            tree_method="hist",
            **params,
        )
    raise ValueError(f"Không phải tree baseline: {name}")


def make_quantum_svc(C: float, random_state: int = 42) -> SVC:
    """SVC kernel='precomputed' — tương đương QSVC khi Gram giống nhau.

    QSVC của qiskit-machine-learning chính là SVC bọc quanh
    `quantum_kernel.evaluate`. Dùng precomputed cho phép tái dùng Gram đã tính từ
    statevector cache thay vì mô phỏng lại.
    """
    return SVC(kernel="precomputed", C=float(C), probability=False,
               max_iter=SVC_MAX_ITER, random_state=random_state)


# ---------------------------------------------------------------------------
# 5. Chọn hyperparameter — quy tắc 1-SE / best-mean của C2
# ---------------------------------------------------------------------------


def select_one_se(rows: list[dict], score_col: str = "mean_score", se_col: str = "se_score",
                  complexity_col: str = "complexity") -> tuple[dict, dict, float]:
    """1-SE thật: cấu hình đơn giản nhất còn nằm trong best_mean - SE(best)."""
    best = max(rows, key=lambda r: r[score_col])
    threshold = best[score_col] - best[se_col]
    eligible = [r for r in rows if r[score_col] >= threshold]
    return min(eligible, key=lambda r: r[complexity_col]), best, threshold


def select_best_mean(rows: list[dict], score_col: str = "mean_score") -> tuple[dict, dict, None]:
    """RF/XGB: best mean CV, tie-break theo thứ tự xuất hiện trong grid."""
    best_score = max(r[score_col] for r in rows)
    chosen = [r for r in rows if r[score_col] == best_score][0]
    return chosen, chosen, None


def _cv_scores_precomputed(gram: np.ndarray, y: np.ndarray, C: float, cv) -> np.ndarray:
    """CV cho kernel precomputed: slice Gram theo fold, không tính lại kernel."""
    scores = []
    for tr, va in cv.split(gram, y):
        model = SVC(kernel="precomputed", C=float(C), probability=False)
        model.fit(gram[np.ix_(tr, tr)], y[tr])
        pred = model.predict(gram[np.ix_(va, tr)])
        scores.append(f1_score(y[va], pred, average="macro"))
    return np.asarray(scores, dtype=float)


def tune_quantum_C(gram_train: np.ndarray, y: np.ndarray, c_grid: list[float],
                   cv_folds: int = 5, random_state: int = 42) -> dict:
    """Quét lưới C trên Gram đã tính sẵn.

    Kernel không phụ thuộc C nên toàn bộ lưới chỉ tốn `len(c_grid) * cv_folds`
    lần `SVC.fit` trên ma trận đã có — gần như miễn phí.
    """
    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    rows = []
    for c_value in c_grid:
        s = _cv_scores_precomputed(gram_train, y, c_value, cv)
        rows.append(
            {
                "C": float(c_value),
                "mean_score": float(s.mean()),
                "std_score": float(s.std(ddof=1)),
                "se_score": float(s.std(ddof=1) / np.sqrt(len(s))),
                "n_folds": int(len(s)),
                "complexity": float(c_value),
            }
        )
    chosen, best, threshold = select_one_se(rows)
    return {"rows": rows, "chosen": chosen, "best": best, "threshold": threshold,
            "selection": "1SE"}


def tune_estimator(estimator, param_grid: dict, X: np.ndarray, y: np.ndarray,
                   selection: str, complexity_fn=None, cv_folds: int = 5,
                   random_state: int = 42) -> dict:
    """Grid search thủ công để lấy được SE từng cấu hình (GridSearchCV không trả SE)."""
    from itertools import product

    from sklearn.base import clone

    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    keys = list(param_grid)
    rows = []
    for values in product(*(param_grid[k] for k in keys)):
        params = dict(zip(keys, values))
        fold_scores = []
        for tr, va in cv.split(X, y):
            model = clone(estimator).set_params(**params)
            model.fit(X[tr], y[tr])
            fold_scores.append(f1_score(y[va], model.predict(X[va]), average="macro"))
        s = np.asarray(fold_scores, dtype=float)
        row = {
            "params": params,
            "mean_score": float(s.mean()),
            "std_score": float(s.std(ddof=1)),
            "se_score": float(s.std(ddof=1) / np.sqrt(len(s))),
            "n_folds": int(len(s)),
        }
        if complexity_fn is not None:
            row["complexity"] = float(complexity_fn(params))
        rows.append(row)

    if selection == "1SE":
        chosen, best, threshold = select_one_se(rows)
    elif selection == "best_mean":
        chosen, best, threshold = select_best_mean(rows)
    else:
        raise ValueError(f"selection không hợp lệ: {selection}")
    return {"rows": rows, "chosen": chosen, "best": best, "threshold": threshold,
            "selection": selection}


# ---------------------------------------------------------------------------
# 6. Đánh giá — metric toàn tập, metric rare subset, và margin
# ---------------------------------------------------------------------------


def signed_margin(decision: np.ndarray, y_true: np.ndarray) -> np.ndarray:
    """m_i = y_pm_i * f(x_i). Dương = nằm đúng phía biên quyết định.

    Đây là đại lượng thay cho `|decision_function|` mà C5/C6 cũ dùng — xem
    `docs/revision/c4_claim_audit.md` mục K3b.
    """
    y_pm = np.where(np.asarray(y_true) == 0, -1.0, 1.0)
    return y_pm * np.asarray(decision, dtype=float)


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray,
                         decision: np.ndarray | None, is_rare: np.ndarray | None) -> dict:
    """Metric toàn tập + metric trên rare subset + thống kê margin (signed và abs)."""
    out = {
        "f1_macro": float(f1_score(y_true, y_pred, average="macro")),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
    }

    if is_rare is not None and is_rare.any():
        yr, pr = y_true[is_rare], y_pred[is_rare]
        out.update(
            {
                "n_rare": int(is_rare.sum()),
                # Rare subset toàn là attack (nhãn 1) nên macro-F1 không có nghĩa;
                # báo cáo recall/precision/F1 của chính lớp attack.
                "recall_rare": float(recall_score(yr, pr, pos_label=1, zero_division=0)),
                "precision_rare": float(precision_score(yr, pr, pos_label=1, zero_division=0)),
                "f1_rare": float(f1_score(yr, pr, pos_label=1, zero_division=0)),
            }
        )

    if decision is not None:
        m_signed = signed_margin(decision, y_true)
        m_abs = np.abs(np.asarray(decision, dtype=float))
        out.update(
            {
                "margin_signed_mean": float(m_signed.mean()),
                "margin_signed_std": float(m_signed.std()),
                "margin_abs_mean": float(m_abs.mean()),
                "margin_abs_std": float(m_abs.std()),
            }
        )
        if is_rare is not None and is_rare.any():
            out.update(
                {
                    "rare_margin_signed_mean": float(m_signed[is_rare].mean()),
                    "rare_margin_signed_std": float(m_signed[is_rare].std()),
                    "rare_margin_abs_mean": float(m_abs[is_rare].mean()),
                    "rare_margin_abs_std": float(m_abs[is_rare].std()),
                }
            )
    return out


# ---------------------------------------------------------------------------
# 7. Thống kê — sao y công thức của C3 để so sánh chéo được
# ---------------------------------------------------------------------------


def mean_ci95(values) -> tuple[float, float, float]:
    """Mean và CI 95% theo t-distribution trên các paired delta cấp run."""
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return np.nan, np.nan, np.nan
    mean = float(arr.mean())
    if len(arr) < 2:
        return mean, np.nan, np.nan
    half = float(student_t.ppf(0.975, len(arr) - 1) * arr.std(ddof=1) / np.sqrt(len(arr)))
    return mean, mean - half, mean + half


def holm_adjust(p_values) -> pd.Series:
    """Holm step-down trong một family test (giống C3)."""
    p = pd.Series(p_values, dtype=float)
    adjusted = pd.Series(np.nan, index=p.index, dtype=float)
    valid = p.dropna().sort_values()
    m = len(valid)
    running_max = 0.0
    for rank, (idx, value) in enumerate(valid.items(), start=1):
        running_max = max(running_max, min(1.0, (m - rank + 1) * float(value)))
        adjusted.loc[idx] = running_max
    return adjusted


def paired_effect_summary(values) -> dict:
    """Tóm tắt paired cấp run. Giá trị dương LUÔN nghĩa là QSVM-favorable."""
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    mean, ci_low, ci_high = mean_ci95(arr)
    median = float(np.median(arr)) if len(arr) else np.nan
    if len(arr) >= 2 and not np.allclose(arr, 0):
        try:
            p_value = float(wilcoxon(arr, zero_method="wilcox", alternative="two-sided").pvalue)
        except ValueError:
            p_value = np.nan
        std = float(arr.std(ddof=1))
        dz = float(mean / std) if std > 0 else np.nan
    else:
        p_value, dz = np.nan, np.nan
    positive_fraction = float((arr > 0).mean()) if len(arr) else np.nan

    if np.isfinite(ci_low) and ci_low > 0 and np.isfinite(p_value) and p_value < 0.05:
        verdict = "QSVM-favorable"
    elif np.isfinite(ci_high) and ci_high < 0 and np.isfinite(p_value) and p_value < 0.05:
        verdict = "classical-favorable"
    else:
        verdict = "inconclusive"

    return {
        "mean_delta": mean,
        "median_delta": median,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "raw_p": p_value,
        "wilcoxon_p": p_value,
        "effect_size_dz": dz,
        "positive_run_fraction": positive_fraction,
        "verdict_uncorrected": verdict,
        "verdict": verdict,
        "n_runs": int(len(arr)),
    }


def cohens_d_pooled(a, b) -> float:
    """Cohen's d với pooled std = sqrt((s_a^2 + s_b^2) / 2).

    Cố ý KHÔNG cung cấp biến thể Glass's delta: chia cho std của một nhóm chính là
    phép tính đã tạo ra con số +0.68 sai trong bản đã nộp (audit mục K3).
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    pooled = np.sqrt((a.std() ** 2 + b.std() ** 2) / 2.0)
    return float((a.mean() - b.mean()) / pooled) if pooled > 0 else np.nan


def bootstrap_ci_cohens_d(a, b, n_resamples: int = 10000, seed: int = 424242,
                          alpha: float = 0.05) -> tuple[float, float]:
    """Bootstrap percentile CI cho Cohen's d, resample độc lập trong từng nhóm."""
    rng = np.random.default_rng(seed)
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    stats = np.empty(n_resamples)
    for i in range(n_resamples):
        stats[i] = cohens_d_pooled(
            a[rng.integers(0, len(a), len(a))], b[rng.integers(0, len(b), len(b))]
        )
    stats = stats[np.isfinite(stats)]
    return (
        float(np.percentile(stats, 100 * alpha / 2)),
        float(np.percentile(stats, 100 * (1 - alpha / 2))),
    )


def build_pairwise_table(per_run: pd.DataFrame, metric: str, group_cols: list[str],
                         model_col: str = "model", run_col: str = "run_id",
                         reference: str = "QSVM_ZZ",
                         higher_is_better: bool = True) -> pd.DataFrame:
    """Bảng so sánh paired `reference` vs từng baseline, Holm theo từng family.

    Schema tương thích `results/nslkdd/c3_revision/c3_pairwise_statistics.csv`.
    """
    rows = []
    sign = 1.0 if higher_is_better else -1.0
    for keys, block in per_run.groupby(group_cols, dropna=False):
        keys = keys if isinstance(keys, tuple) else (keys,)
        wide = block.pivot_table(index=run_col, columns=model_col, values=metric)
        if reference not in wide.columns:
            continue
        for baseline in ALL_BASELINES:
            if baseline not in wide.columns:
                continue
            paired = (wide[reference] - wide[baseline]).dropna() * sign
            row = dict(zip(group_cols, keys))
            row.update(
                {
                    "comparison": f"{reference}_vs_{baseline}",
                    "baseline": baseline,
                    "baseline_family": BASELINE_FAMILY_BY_MODEL[baseline],
                    "metric": metric,
                }
            )
            row.update(paired_effect_summary(paired.to_numpy()))
            rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Holm trong từng (nhóm điều kiện, family) — cùng định nghĩa family như C3.
    df["holm_p"] = np.nan
    for _, idx in df.groupby(group_cols + ["baseline_family"], dropna=False).groups.items():
        df.loc[idx, "holm_p"] = holm_adjust(df.loc[idx, "raw_p"])

    def _verdict(r):
        if not np.isfinite(r["holm_p"]) or r["holm_p"] >= 0.05:
            return "inconclusive"
        if np.isfinite(r["ci_low"]) and r["ci_low"] > 0:
            return "QSVM-favorable"
        if np.isfinite(r["ci_high"]) and r["ci_high"] < 0:
            return "classical-favorable"
        return "inconclusive"

    df["verdict"] = df.apply(_verdict, axis=1)
    return df


# ---------------------------------------------------------------------------
# 8. Audit gate
# ---------------------------------------------------------------------------


@dataclass
class GateResult:
    name: str
    passed: bool
    detail: dict = field(default_factory=dict)

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.name}: {json.dumps(self.detail, ensure_ascii=False, default=str)}"


def gate_disjointness(data: DataBundle, subsets: dict, run_id: int, dataset=None) -> GateResult:
    """G3: train phải rời TUYỆT ĐỐI với tuning set; với test thì chỉ báo cáo.

    Lưu ý quan trọng về NSL-KDD: KDDTrain+ và KDDTest+ có **610 dòng trùng nhau
    hoàn toàn về feature + nhãn** (2.7% của test). Việc khử trùng lặp của NSL-KDD
    thực hiện *trong* từng split chứ không *giữa* hai split. Đây là thuộc tính của
    bộ dữ liệu, không phải lỗi lấy mẫu — mọi công trình dùng NSL-KDD đều chịu.
    Vì vậy gate chỉ FAIL khi chồng lấn với test **vượt quá** mức nền dự kiến
    (tỉ lệ 610/125973 nhân với N), còn lại thì ghi nhận để công bố minh bạch.
    """
    fc = data.feature_cols
    tune_sig = set(row_signatures(data.df_tune, fc).tolist())
    test_sig = set(row_signatures(data.df_test_full, fc).tolist())
    train_sig_arr = row_signatures(data.df_train_all, fc)
    train_sig = set(train_sig_arr.tolist())
    # Tỉ lệ nền phải tính theo HÀNG, không theo chữ ký duy nhất. UNSW-NB15 trùng lặp
    # nội bộ 47%, nên tỉ lệ theo chữ ký (1.5%) đánh giá thấp tỉ lệ theo hàng (28.5%)
    # gần 20 lần và làm gate báo động giả.
    baseline_rate = float(pd.Series(train_sig_arr).isin(test_sig).mean())

    detail: dict = {"dataset_train_test_dup_rows": len(train_sig & test_sig),
                    "dataset_dup_rate": round(baseline_rate, 6)}
    ok = True
    for n, df in subsets.items():
        sig = set(row_signatures(df, fc).tolist())
        overlap_tune = len(sig & tune_sig)
        overlap_test = len(sig & test_sig)
        # Ngưỡng rộng rãi: 3x mức nền + 5, chỉ để bắt lỗi lấy mẫu thật sự.
        expected = baseline_rate * len(df)
        detail[str(n)] = {
            "vs_tuning": overlap_tune,
            "vs_test": overlap_test,
            "vs_test_expected": round(expected, 2),
        }
        ok = ok and overlap_tune == 0 and overlap_test <= 3 * expected + 5
    return GateResult(f"G3_disjointness_run{run_id}", ok, detail)


def gate_nesting(data: DataBundle, subsets: dict, run_id: int, dataset=None) -> GateResult:
    """G4: D_100 ⊂ D_200 ⊂ ... ⊂ D_max."""
    fc = data.feature_cols
    sizes = sorted(subsets)
    sigs = {n: set(row_signatures(subsets[n], fc).tolist()) for n in sizes}
    detail, ok = {}, True
    for small, large in zip(sizes, sizes[1:]):
        missing = len(sigs[small] - sigs[large])
        detail[f"{small}_in_{large}"] = {"missing": missing}
        ok = ok and missing == 0
    return GateResult(f"G4_nesting_run{run_id}", ok, detail)


def gate_rare_presence(subsets: dict, run_id: int, dataset="nslkdd") -> GateResult:
    """G5 (phần train): mọi subset ở mọi N phải có ≥ 1 mẫu rare."""
    detail = {str(n): int(rare_mask(df, dataset).sum()) for n, df in subsets.items()}
    return GateResult(f"G5_rare_presence_run{run_id}", all(v >= 1 for v in detail.values()), detail)


# Model tất định bit-for-bit khi cho cùng dữ liệu và cùng tham số.
DETERMINISTIC_MODELS = (
    "QSVM_ZZ", "QSVM_Z", "SVM_Linear", "SVM_Poly2", "SVM_RBF", "RandomForest",
)
# XGBoost `tree_method='hist'` gộp histogram theo thứ tự thread, nên kết quả phụ
# thuộc SỐ THREAD của máy chạy chứ không chỉ phụ thuộc seed. Đo được trên máy 16
# core: cùng seed, cùng dữ liệu, n_jobs=-1 cho F1=0.8365 còn n_jobs=1 cho 0.8533.
# Vì vậy XGBoost được báo cáo riêng, không tính vào pass/fail của gate.
NONDETERMINISTIC_MODELS = ("XGBoost",)


def gate_reproduce_c2(observed: pd.DataFrame, root: Path | None = None,
                      tolerance: float = 0.005, min_exact_runs: int = 9) -> GateResult:
    """G2 — gate quan trọng nhất: tái tạo đúng số của C2 tại N=1000.

    `observed` cần các cột `run_id`, `model`, `f1_macro`, chạy ở chế độ
    frozen_c1 + hyperparameter đóng băng của C2 + test 300.

    Gate tách theo bản chất từng model thay vì áp một ngưỡng chung: với model tất
    định, đòi hỏi đúng phải là **trùng khớp chính xác**, chứ 0.005 quá lỏng và sẽ
    che mất lỗi thật. XGBoost tách riêng vì phi tất định theo số thread (xem
    `NONDETERMINISTIC_MODELS`).

    Nếu gate này trượt ở phần tất định thì mọi số C4 về sau đều không so được với
    C2/C3, và bài sẽ tự mâu thuẫn đúng kiểu R1 đã bắt ở Table IV vs VI.
    """
    root = root or find_project_root()
    ref = pd.read_csv(root / "results" / "nslkdd" / "c2_revision" / "c2_per_run.csv")
    merged = observed.merge(ref, on=["run_id", "model"], suffixes=("_new", "_ref"))
    if merged.empty:
        return GateResult("G2_reproduce_c2", False, {"error": "không ghép được với c2_per_run.csv"})

    merged["abs_diff"] = (merged["f1_macro_new"] - merged["f1_macro_ref"]).abs()

    per_model, passed = {}, True
    for model, block in merged.groupby("model"):
        n_exact = int((block["abs_diff"] < 1e-9).sum())
        entry = {
            "n_runs": int(len(block)),
            "n_exact": n_exact,
            "max_abs_diff": float(block["abs_diff"].max()),
            "mean_f1_new": float(block["f1_macro_new"].mean()),
            "mean_f1_ref": float(block["f1_macro_ref"].mean()),
            "mismatched_runs": [
                int(r) for r in block.loc[block["abs_diff"] >= 1e-9, "run_id"]
            ],
        }
        if model in DETERMINISTIC_MODELS:
            entry["role"] = "pass_fail"
            ok = n_exact >= min_exact_runs and entry["max_abs_diff"] < tolerance
            entry["passed"] = bool(ok)
            passed = passed and ok
        else:
            entry["role"] = "report_only"
            entry["note"] = "phi tất định theo số thread; không tính vào pass/fail"
        per_model[str(model)] = entry

    return GateResult(
        "G2_reproduce_c2",
        passed,
        {
            "n_compared": int(len(merged)),
            "tolerance": tolerance,
            "min_exact_runs": min_exact_runs,
            "per_model": per_model,
        },
    )


__all__ = [
    "ALL_MODELS",
    "ALL_BASELINES",
    "INFERENTIAL_FAMILIES",
    "RARE_CATEGORIES",
    "DataBundle",
    "GateResult",
    "Representation",
    "RefitPerNRepresentation",
    "FrozenC1Representation",
    "StatevectorCache",
    "bootstrap_ci_cohens_d",
    "build_feature_map",
    "build_pairwise_table",
    "build_train_subset",
    "cohens_d_pooled",
    "compute_statevectors",
    "compute_statevectors_fast",
    "evaluate_predictions",
    "file_sha256",
    "find_project_root",
    "four_way_label",
    "gate_disjointness",
    "gate_nesting",
    "gate_rare_presence",
    "gate_reproduce_c2",
    "gram_from_statevectors",
    "holm_adjust",
    "load_data",
    "load_protocol",
    "make_quantum_svc",
    "make_representation",
    "make_svm_estimator",
    "make_tree_estimator",
    "mean_ci95",
    "paired_effect_summary",
    "rare_mask",
    "row_signatures",
    "select_best_mean",
    "select_one_se",
    "signed_margin",
    "stratified_indices",
    "tune_estimator",
    "tune_quantum_C",
    "verify_kernel_equivalence",
]
