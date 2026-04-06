"""
Module tiền xử lý dữ liệu NSL-KDD cho pipeline QSVM-IDS NISQ.

Pipeline tổng thể:
    NSL-KDD (41 đặc trưng)
    → One-Hot Encoding (122 chiều, zero-leakage)
    → MinMaxScaler [0, 1]
    → Lưu CSV + artifact

Tất cả cấu hình được import từ config.py — không có đường dẫn cứng.
"""

import os
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))

from config import (
    ATTACK_CATEGORY_MAP,
    CATEGORICAL_COLS,
    COLUMNS,
    DATA_PROCESSED_DIR,
    LABEL_COLS,
    MIN_RARE,
    MULTI_RUN_DIR,
    N_RUNS,
    NSLKDD_TEST_RAW,
    NSLKDD_TRAIN_RAW,
    RANDOM_STATE,
    RUN_SIZE,
    SCALER_PATH,
    TEST_SIZES,
    TRAIN_SIZES,
)

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Hằng số nội bộ
# ---------------------------------------------------------------------------

# Các cột nhãn không được dùng làm đặc trưng đầu vào
_EXCLUDED_FROM_FEATURES = set(LABEL_COLS) | {"label", "difficulty_level"}


# ---------------------------------------------------------------------------
# Lớp DataLoader — tải và làm sạch dữ liệu thô
# ---------------------------------------------------------------------------

class DataLoader:
    """Tải dữ liệu thô NSL-KDD và thêm các cột nhãn dẫn xuất."""

    def __init__(self, train_path=None, test_path=None):
        # Sử dụng đường dẫn mặc định từ config nếu không truyền vào
        self.train_path = train_path or NSLKDD_TRAIN_RAW
        self.test_path = test_path or NSLKDD_TEST_RAW

    def load_raw(self, path):
        """
        Đọc một file NSL-KDD (không có header) và gán tên cột.

        Parameters
        ----------
        path : str hoặc Path
            Đường dẫn đến file .txt của NSL-KDD.

        Returns
        -------
        pd.DataFrame
            DataFrame thô với 42 cột (đã bỏ difficulty_level).
        """
        df = pd.read_csv(str(path), names=COLUMNS, header=None)
        # Bỏ cột difficulty_level — không có ý nghĩa mô hình
        df.drop(columns=["difficulty_level"], inplace=True)
        return df

    def add_label_columns(self, df):
        """
        Tạo ba cột nhãn dẫn xuất từ cột 'label' gốc.

        Các cột được tạo:
        - label_binary     : 0 = Normal, 1 = Attack
        - label_multiclass : giữ nguyên tên attack type gốc
        - attack_category  : nhóm lớn (Normal/DoS/Probe/R2L/U2R)

        Nếu có attack type chưa có trong ATTACK_CATEGORY_MAP,
        attack_category sẽ được điền 'Unknown'.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame đã có cột 'label'.

        Returns
        -------
        pd.DataFrame
            DataFrame gốc với ba cột nhãn bổ sung.
        """
        df = df.copy()
        df["label_binary"] = (df["label"] != "normal").astype(int)
        df["label_multiclass"] = df["label"].copy()
        df["attack_category"] = df["label"].map(ATTACK_CATEGORY_MAP)

        # Điền Unknown cho các attack type chưa được map
        unknown_mask = df["attack_category"].isna()
        if unknown_mask.any():
            df.loc[unknown_mask, "attack_category"] = "Unknown"

        return df

    def load_both(self):
        """
        Tải và gán nhãn cho cả hai tập train và test.

        Returns
        -------
        train_df, test_df : tuple of pd.DataFrame
            Hai DataFrame đã có đầy đủ cột nhãn, chưa qua OHE hay scale.
        """
        train_df = self.load_raw(self.train_path)
        test_df = self.load_raw(self.test_path)

        train_df = self.add_label_columns(train_df)
        test_df = self.add_label_columns(test_df)

        return train_df, test_df


# ---------------------------------------------------------------------------
# Lớp OHETransformer — One-Hot Encoding zero-leakage
# ---------------------------------------------------------------------------

class OHETransformer:
    """
    Thực hiện One-Hot Encoding (OHE) đảm bảo nguyên tắc zero-leakage.

    Quy tắc:
    - fit() CHỈ được gọi trên tập train.
    - transform() áp dụng schema của train lên mọi tập khác.
      + Category có trong train nhưng không trong test → điền 0.
      + Category chỉ có trong test → bị bỏ hoàn toàn (tránh rò rỉ).
    """

    def __init__(self):
        # Danh sách cột sau OHE, được xác định khi fit()
        self._ohe_columns = None

    def fit(self, df):
        """
        Học schema OHE từ tập train.

        Parameters
        ----------
        df : pd.DataFrame
            Tập train chứa các cột CATEGORICAL_COLS.

        Returns
        -------
        self
        """
        encoded = pd.get_dummies(df, columns=CATEGORICAL_COLS, dtype=float)
        self._ohe_columns = encoded.columns.tolist()
        return self

    def transform(self, df):
        """
        Áp dụng schema OHE đã học lên một DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame cần encode (train hoặc test).

        Returns
        -------
        pd.DataFrame
            DataFrame đã OHE với đúng tập cột của train.
        """
        if self._ohe_columns is None:
            raise RuntimeError("OHETransformer chưa được fit(). Gọi fit() trước.")

        encoded = pd.get_dummies(df, columns=CATEGORICAL_COLS, dtype=float)
        # Căn chỉnh cột về schema train — thêm cột thiếu và bỏ cột thừa
        encoded = encoded.reindex(columns=self._ohe_columns, fill_value=0.0)
        return encoded

    def fit_transform(self, df):
        """Kết hợp fit() và transform() trên cùng một DataFrame."""
        return self.fit(df).transform(df)

    @property
    def ohe_columns(self):
        """Danh sách cột sau OHE (None nếu chưa fit)."""
        return self._ohe_columns


# ---------------------------------------------------------------------------
# Các hàm pipeline chính
# ---------------------------------------------------------------------------

def preprocess_nsl_kdd(train_path=None, test_path=None):
    """
    Chạy toàn bộ pipeline tiền xử lý NSL-KDD.

    Các bước:
    1. Tải dữ liệu thô và gán nhãn.
    2. Tách features khỏi nhãn (tránh rò rỉ nhãn vào encoder/scaler).
    3. OHE cho CATEGORICAL_COLS — fit chỉ trên train.
    4. MinMaxScaler [0, 1] — fit chỉ trên train.
    5. Ghép features đã xử lý với các cột nhãn.

    Parameters
    ----------
    train_path : str hoặc Path, tùy chọn
        Đường dẫn file train; mặc định lấy từ config.
    test_path : str hoặc Path, tùy chọn
        Đường dẫn file test; mặc định lấy từ config.

    Returns
    -------
    train_proc : pd.DataFrame
        Tập train đã xử lý (features + nhãn).
    test_proc : pd.DataFrame
        Tập test đã xử lý (features + nhãn).
    scaler : MinMaxScaler
        Scaler đã fit trên train, dùng để áp lên dữ liệu mới.
    ohe : OHETransformer
        Transformer OHE đã fit, dùng lại cho inference.
    """
    loader = DataLoader(train_path, test_path)
    train_df, test_df = loader.load_both()

    # Tách features và nhãn trước khi encode / scale
    label_cols_present = [c for c in LABEL_COLS if c in train_df.columns]
    feature_cols = [c for c in train_df.columns if c not in _EXCLUDED_FROM_FEATURES]

    train_feat = train_df[feature_cols].copy()
    test_feat = test_df[feature_cols].copy()
    train_lbl = train_df[label_cols_present].reset_index(drop=True)
    test_lbl = test_df[label_cols_present].reset_index(drop=True)

    # OHE — fit CHỈ trên train
    ohe = OHETransformer()
    train_enc = ohe.fit_transform(train_feat)
    test_enc = ohe.transform(test_feat)

    # MinMaxScaler — fit CHỈ trên train
    numeric_cols = train_enc.select_dtypes(include=[np.number]).columns.tolist()
    scaler = MinMaxScaler()
    train_enc[numeric_cols] = scaler.fit_transform(train_enc[numeric_cols])
    test_enc[numeric_cols] = np.clip(
        scaler.transform(test_enc[numeric_cols]), 0.0, 1.0
    )

    # Ghép features đã xử lý với nhãn
    train_proc = pd.concat(
        [train_enc.reset_index(drop=True), train_lbl], axis=1
    )
    test_proc = pd.concat(
        [test_enc.reset_index(drop=True), test_lbl], axis=1
    )

    return train_proc, test_proc, scaler, ohe


def get_feature_columns(df):
    """
    Trả về danh sách cột đặc trưng (loại bỏ các cột nhãn).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame đã xử lý (đầu ra của preprocess_nsl_kdd).

    Returns
    -------
    list of str
    """
    return [c for c in df.columns if c not in _EXCLUDED_FROM_FEATURES]


# ---------------------------------------------------------------------------
# Hàm lấy mẫu stratified cho QSVM
# ---------------------------------------------------------------------------

def stratified_sample_for_qsvm(
    df,
    n_samples=1000,
    min_rare=30,
    rare_categories=("U2R", "R2L"),
    random_state=RANDOM_STATE,
):
    """
    Lấy mẫu có kiểm soát để đảm bảo rare attacks (U2R, R2L) có đủ đại diện.

    Chiến lược:
    - Bước 1: Đảm bảo tối thiểu `min_rare` mẫu cho mỗi rare category
      (oversample nếu pool không đủ).
    - Bước 2: Chia phần còn lại theo tỷ lệ tự nhiên của các category khác.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame nguồn có cột 'attack_category'.
    n_samples : int
        Tổng số mẫu mong muốn.
    min_rare : int
        Số mẫu tối thiểu cho mỗi rare category.
    rare_categories : tuple of str
        Tên các category được ưu tiên.
    random_state : int
        Seed để đảm bảo tái lặp.

    Returns
    -------
    pd.DataFrame
        Subset đã được lấy mẫu và xáo trộn.
    """
    rng = np.random.RandomState(random_state)
    sampled = []

    # Phân loại categories
    rare_cats = [
        c for c in rare_categories if c in df["attack_category"].unique()
    ]
    other_cats = [
        c for c in df["attack_category"].unique() if c not in rare_cats
    ]

    # Bước 1: Lấy mẫu tối thiểu cho rare categories
    rare_budget = 0
    for cat in rare_cats:
        pool = df[df["attack_category"] == cat]
        n_take = max(min_rare, min(min_rare, len(pool)))
        replace = len(pool) < n_take  # oversample khi pool không đủ
        idx = pool.sample(
            n=n_take, replace=replace, random_state=rng.randint(int(1e6))
        )
        sampled.append(idx)
        rare_budget += n_take

    # Bước 2: Chia phần còn lại theo tỷ lệ gốc
    remaining = n_samples - rare_budget
    other_df = df[df["attack_category"].isin(other_cats)]
    other_total = len(other_df)

    for cat in other_cats:
        pool = df[df["attack_category"] == cat]
        weight = len(pool) / other_total
        n_take = max(1, int(remaining * weight))
        n_take = min(n_take, len(pool))
        idx = pool.sample(n=n_take, random_state=rng.randint(int(1e6)))
        sampled.append(idx)

    result = pd.concat(sampled).sample(frac=1, random_state=random_state)
    return result.reset_index(drop=True)


def make_disjoint_runs(
    df,
    n_runs=N_RUNS,
    run_size=RUN_SIZE,
    min_rare=MIN_RARE,
    base_seed=0,
):
    """
    Chia DataFrame thành `n_runs` tập không giao nhau, mỗi tập `run_size` mẫu.

    Dùng cho kiểm định thống kê đa lần chạy (C1 multi-run validation).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame nguồn (train hoặc test đã xử lý).
    n_runs : int
        Số lần chạy.
    run_size : int
        Số mẫu mỗi lần chạy.
    min_rare : int
        Số mẫu tối thiểu cho rare category mỗi run.
    base_seed : int
        Seed gốc; seed của run thứ i = base_seed + i.

    Returns
    -------
    list of pd.DataFrame
        Danh sách `n_runs` DataFrame không trùng nhau.
    """
    # Xáo trộn toàn bộ trước khi chia partition
    df_shuffled = df.sample(frac=1, random_state=base_seed).reset_index(drop=True)
    total = len(df_shuffled)
    part_size = total // n_runs

    runs = []
    for i in range(n_runs):
        start = i * part_size
        end = (i + 1) * part_size if i < n_runs - 1 else total
        partition = df_shuffled.iloc[start:end].copy()

        run_df = stratified_sample_for_qsvm(
            partition,
            n_samples=run_size,
            min_rare=min_rare,
            random_state=base_seed + i,
        )
        runs.append(run_df)

    return runs


# ---------------------------------------------------------------------------
# Hàm kiểm tra sanity
# ---------------------------------------------------------------------------

def run_sanity_checks(train_proc, test_proc, sample_df=None):
    """
    Chạy các kiểm tra cơ bản trên dữ liệu đã xử lý.

    Parameters
    ----------
    train_proc : pd.DataFrame
        Tập train đã xử lý.
    test_proc : pd.DataFrame
        Tập test đã xử lý.
    sample_df : pd.DataFrame hoặc None
        Tập mẫu bổ sung (ví dụ: Sample1000) để kiểm tra phân bố.

    Returns
    -------
    dict
        Kết quả từng check: {tên_check: bool}.

    Raises
    ------
    AssertionError
        Nếu bất kỳ check nào thất bại.
    """
    feat_cols = get_feature_columns(train_proc)
    results = {}

    # Kiểm tra phạm vi đặc trưng [0, 1]
    feat_min = train_proc[feat_cols].min().min()
    feat_max = train_proc[feat_cols].max().max()
    results["feature_range_0_1"] = (
        abs(feat_min) < 1e-9 and abs(feat_max - 1.0) < 1e-9
    )

    # Không có NaN trong features
    nan_count = train_proc[feat_cols].isna().sum().sum()
    results["no_nan_in_features"] = nan_count == 0

    # label_binary chỉ chứa {0, 1}
    binary_vals = set(train_proc["label_binary"].unique())
    results["label_binary_valid"] = binary_vals == {0, 1}

    # Không có NaN trong attack_category
    nan_cat = train_proc["attack_category"].isna().sum()
    results["no_nan_in_attack_category"] = nan_cat == 0

    # Số cột features train = test
    test_feat_cols = get_feature_columns(test_proc)
    results["train_test_columns_match"] = feat_cols == test_feat_cols

    # label_binary nhất quán với label_multiclass
    inconsistent = (
        (train_proc["label_multiclass"] == "normal")
        & (train_proc["label_binary"] == 1)
    ).sum()
    results["label_consistency"] = inconsistent == 0

    # Kiểm tra sample_df có đủ 5 attack categories
    if sample_df is not None:
        n_cats = sample_df["attack_category"].nunique()
        results["sample_has_5_categories"] = n_cats == 5

    # Ném lỗi nếu có check thất bại
    failed = [k for k, v in results.items() if not v]
    if failed:
        raise AssertionError(
            f"Sanity checks thất bại: {failed}"
        )

    return results


# ---------------------------------------------------------------------------
# Hàm lưu artifact
# ---------------------------------------------------------------------------

def save_all_artifacts(
    train_proc,
    test_proc,
    scaler,
    sample_1000=None,
    train_samples=None,
    test_samples=None,
    train_runs=None,
    test_runs=None,
):
    """
    Lưu tất cả CSV và artifact của pipeline tiền xử lý.

    Sử dụng cơ chế skip-if-exists để tránh ghi đè dữ liệu đã có.

    Parameters
    ----------
    train_proc : pd.DataFrame
        Tập train đầy đủ đã xử lý.
    test_proc : pd.DataFrame
        Tập test đầy đủ đã xử lý.
    scaler : MinMaxScaler
        Scaler đã fit.
    sample_1000 : pd.DataFrame hoặc None
        Tập mẫu 1000 mẫu stratified.
    train_samples : dict hoặc None
        {n: DataFrame} cho các tập train kích thước nhỏ.
    test_samples : dict hoặc None
        {n: DataFrame} cho các tập test kích thước nhỏ.
    train_runs : list of pd.DataFrame hoặc None
        Danh sách N_RUNS tập train disjoint.
    test_runs : list of pd.DataFrame hoặc None
        Danh sách N_RUNS tập test disjoint.
    """
    os.makedirs(str(DATA_PROCESSED_DIR), exist_ok=True)
    os.makedirs(str(MULTI_RUN_DIR), exist_ok=True)

    feat_cols = get_feature_columns(train_proc)

    # Danh sách (đường dẫn, DataFrame) cần lưu
    saves = [
        (DATA_PROCESSED_DIR / "NSL_KDD_Train_Cleaned.csv", train_proc),
        (DATA_PROCESSED_DIR / "NSL_KDD_Test_Cleaned.csv", test_proc),
    ]

    if sample_1000 is not None:
        saves.append(
            (DATA_PROCESSED_DIR / "NSL_KDD_Train_Sample1000.csv", sample_1000)
        )

    if train_samples:
        for n, df in train_samples.items():
            saves.append(
                (DATA_PROCESSED_DIR / f"NSL_KDD_Train_Sample{n}.csv", df)
            )

    if test_samples:
        for n, df in test_samples.items():
            saves.append(
                (DATA_PROCESSED_DIR / f"NSL_KDD_Test_Sample{n}.csv", df)
            )

    # Lưu CSV — bỏ qua nếu đã tồn tại
    for path, df_obj in saves:
        if not path.exists():
            df_obj.to_csv(str(path), index=False)

    # Lưu multi-run sets
    if train_runs and test_runs:
        for i, (tr, te) in enumerate(zip(train_runs, test_runs), start=1):
            tr_path = MULTI_RUN_DIR / f"train_run{i}.csv"
            te_path = MULTI_RUN_DIR / f"test_run{i}.csv"
            if not tr_path.exists():
                tr.to_csv(str(tr_path), index=False)
            if not te_path.exists():
                te.to_csv(str(te_path), index=False)

    # Lưu scaler artifact
    scaler_path = DATA_PROCESSED_DIR / "minmax_scaler.joblib"
    if not scaler_path.exists():
        joblib.dump(scaler, str(scaler_path))

    # Lưu danh sách feature columns
    feat_path = DATA_PROCESSED_DIR / "feature_columns.csv"
    if not feat_path.exists():
        pd.Series(feat_cols).to_csv(str(feat_path), index=False, header=["feature"])


# ---------------------------------------------------------------------------
# Hàm tải lại multi-run sets từ file
# ---------------------------------------------------------------------------

def load_multi_run_sets(n_runs=N_RUNS):
    """
    Tải lại các tập train/test disjoint đã lưu từ thư mục multi_run.

    Parameters
    ----------
    n_runs : int
        Số lần chạy (mặc định từ config).

    Returns
    -------
    train_runs, test_runs : tuple of list
        Mỗi phần tử là pd.DataFrame tương ứng với một run.

    Raises
    ------
    FileNotFoundError
        Nếu bất kỳ file nào chưa được tạo.
    """
    train_runs, test_runs = [], []

    for i in range(1, n_runs + 1):
        tr_path = MULTI_RUN_DIR / f"train_run{i}.csv"
        te_path = MULTI_RUN_DIR / f"test_run{i}.csv"

        if not tr_path.exists() or not te_path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy file multi-run: {tr_path} hoặc {te_path}. "
                "Chạy save_all_artifacts() với train_runs và test_runs trước."
            )

        train_runs.append(pd.read_csv(str(tr_path)))
        test_runs.append(pd.read_csv(str(te_path)))

    return train_runs, test_runs


# ---------------------------------------------------------------------------
# Hàm phân tích attack type giữa train và test
# ---------------------------------------------------------------------------

def get_attack_type_split_info(train_proc, test_proc):
    """
    Phân tích sự khác biệt về attack types giữa train và test.

    Dùng để ghi nhận limitations trong phần Experimental Setup của paper
    (các attack type chỉ trong test là zero-shot attacks).

    Parameters
    ----------
    train_proc : pd.DataFrame
    test_proc : pd.DataFrame

    Returns
    -------
    dict với các khóa:
        - 'in_both'       : set — attack types có trong cả hai tập
        - 'only_in_train' : set — attack types chỉ có trong train
        - 'only_in_test'  : set — attack types chỉ có trong test (zero-shot)
    """
    train_types = set(train_proc["label_multiclass"].unique())
    test_types = set(test_proc["label_multiclass"].unique())

    return {
        "in_both": sorted(train_types & test_types),
        "only_in_train": sorted(train_types - test_types),
        "only_in_test": sorted(test_types - train_types),
    }
