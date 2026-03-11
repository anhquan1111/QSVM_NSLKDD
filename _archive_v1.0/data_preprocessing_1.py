"""
data_preprocessing.py
=====================
NSL-KDD preprocessing pipeline for the 4-Qubit Quantum SVM (QSVM) project.

Pipeline summary
----------------
1.  Load raw CSVs (no header) and assign the 43 canonical column names.
2.  Drop the `difficulty_level` column (carries no signal for classification).
3.  Binarise the multi-class attack label  →  0 = normal, 1 = attack.
4.  One-Hot Encode the three categorical columns (protocol_type, service, flag).
5.  Apply SelectKBest(f_classif, k=20) — fit on train only — to eliminate
    sparse/noisy OHE columns while retaining the most discriminative ones.
6.  Apply PCA(n_components=4) — fit on train only — to satisfy the hard
    4-qubit hardware constraint of the quantum circuit simulation.
7.  Apply MinMaxScaler(feature_range=(0, π)) — fit on train only — to map
    every feature value into the rotation angle domain [0, π] used by the
    RX/RY quantum gate embedding layer:
        |ψ⟩ = RY(x_i)|0⟩  where  x_i ∈ [0, π]
    Scaling to π (rather than 1) means the full Bloch-sphere hemisphere
    [|0⟩ … |1⟩] is exploited, maximising the expressibility of amplitude
    encoding without wrapping angles (which would corrupt the kernel geometry).
8.  Persist processed NumPy arrays to data/processed/ and fitted transformer
    artefacts to models/ via joblib for reproducible inference.

Zero-leakage guarantee
----------------------
The contract for every transformer T is:
    T.fit_transform(X_train)   ← learns statistics from training data ONLY
    T.transform(X_test)        ← applies learned statistics; never learns from test

This ensures the test set remains a truly held-out evaluation partition and that
no information from future/unseen data contaminates the training distribution.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.preprocessing import MinMaxScaler

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path constants  (relative to project root; resolved at runtime)
# ---------------------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
RAW_DIR: Path = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"
MODELS_DIR: Path = PROJECT_ROOT / "models"

TRAIN_FILE: Path = RAW_DIR / "KDDTrain+.txt"
TEST_FILE: Path = RAW_DIR / "KDDTest+.txt"

# ---------------------------------------------------------------------------
# NSL-KDD canonical column specification
# ---------------------------------------------------------------------------
# The dataset ships without a header row.  Column order follows the published
# NSL-KDD schema (41 features + label + difficulty score).
NSL_KDD_COLUMNS: list[str] = [
    "duration",
    "protocol_type",        # categorical — 3 unique values
    "service",              # categorical — 70 unique values
    "flag",                 # categorical — 11 unique values
    "src_bytes",
    "dst_bytes",
    "land",
    "wrong_fragment",
    "urgent",
    "hot",
    "num_failed_logins",
    "logged_in",
    "num_compromised",
    "root_shell",
    "su_attempted",
    "num_root",
    "num_file_creations",
    "num_shells",
    "num_access_files",
    "num_outbound_cmds",
    "is_host_login",
    "is_guest_login",
    "count",
    "srv_count",
    "serror_rate",
    "srv_serror_rate",
    "rerror_rate",
    "srv_rerror_rate",
    "same_srv_rate",
    "diff_srv_rate",
    "srv_diff_host_rate",
    "dst_host_count",
    "dst_host_srv_count",
    "dst_host_same_srv_rate",
    "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate",
    "dst_host_srv_serror_rate",
    "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate",
    "label",
    "difficulty_level",     # will be dropped immediately after loading
]

CATEGORICAL_COLS: list[str] = ["protocol_type", "service", "flag"]
LABEL_COL: str = "label"
NORMAL_CLASS: str = "normal"

# Quantum circuit constraint: the simulation uses exactly 4 qubits,
# so the final feature dimensionality must equal 4.
N_QUBITS: int = 4
# Number of best features to retain after OHE before PCA compression.
K_BEST: int = 20
# Rotation angles must lie in [0, π] to correctly parameterise RY gates.
ANGLE_MAX: float = np.pi


# ---------------------------------------------------------------------------
# Step 1 — Data loading
# ---------------------------------------------------------------------------
def load_raw_data(filepath: Path) -> pd.DataFrame:
    """Read a headerless NSL-KDD text file and return a labelled DataFrame.

    Parameters
    ----------
    filepath:
        Absolute path to the raw ``KDDTrain+.txt`` or ``KDDTest+.txt`` file.

    Returns
    -------
    pd.DataFrame
        43-column DataFrame with typed columns; ``difficulty_level`` is
        dropped immediately to prevent it from leaking into feature space.
    """
    logger.info("Loading raw data from: %s", filepath)
    df = pd.read_csv(
        filepath,
        header=None,
        names=NSL_KDD_COLUMNS,
        # Treat bare whitespace tokens as NaN so they can be caught later.
        na_values=[" ", ""],
    )
    logger.info("  Raw shape: %s", df.shape)

    # Drop difficulty_level — it is a meta-annotation added by the dataset
    # authors to indicate attack complexity.  It is NOT a network feature and
    # must never be used as a predictor.
    df.drop(columns=["difficulty_level"], inplace=True)
    logger.info("  Shape after dropping difficulty_level: %s", df.shape)
    return df


# ---------------------------------------------------------------------------
# Step 2 — Label engineering (multi-class → binary)
# ---------------------------------------------------------------------------
def binarise_labels(series: pd.Series) -> pd.Series:
    """Map the multi-class NSL-KDD attack labels to a binary scheme.

    Mapping
    -------
    'normal'  →  0  (benign traffic)
    anything else  →  1  (attack traffic, regardless of attack sub-type)

    This collapses the ~23 distinct attack categories (DoS, Probe, R2L, U2R …)
    into a single positive class, which is the canonical formulation for
    binary intrusion detection benchmarks.

    Parameters
    ----------
    series:
        Raw ``label`` column straight from the CSV.

    Returns
    -------
    pd.Series
        Integer series of dtype int64 with values in {0, 1}.
    """
    return series.apply(lambda lbl: 0 if str(lbl).strip() == NORMAL_CLASS else 1).astype(
        np.int64
    )


# ---------------------------------------------------------------------------
# Step 3 — Feature / label split
# ---------------------------------------------------------------------------
def split_features_labels(
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.Series]:
    """Separate feature matrix from the binarised label vector.

    Parameters
    ----------
    df:
        DataFrame that still contains the ``label`` column (post-binarisation).

    Returns
    -------
    X : pd.DataFrame
        All columns except ``label``.
    y : pd.Series
        The binarised label column.
    """
    y = df[LABEL_COL].copy()
    X = df.drop(columns=[LABEL_COL])
    return X, y


# ---------------------------------------------------------------------------
# Step 4 — One-Hot Encoding for categorical columns
# ---------------------------------------------------------------------------
def one_hot_encode(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Apply pandas get_dummies (equivalent to OHE) to the three categorical
    columns while guaranteeing the test set is aligned to the train vocabulary.

    Why pandas rather than sklearn OHE here?
    -----------------------------------------
    The test split may contain service/flag values absent from the training
    split.  ``pd.get_dummies`` on the combined set followed by ``reindex``
    to the training columns is a clean, zero-leakage approach:
    – Only categories *seen in training* produce output columns.
    – Unseen test categories are silently dropped (their rows stay as all-zeros
      in the columns for the known categories).

    Parameters
    ----------
    X_train, X_test:
        Feature DataFrames still containing the three categorical columns.

    Returns
    -------
    X_train_enc, X_test_enc : pd.DataFrame
        OHE-expanded DataFrames with identical column sets.
    """
    logger.info("Applying One-Hot Encoding to columns: %s", CATEGORICAL_COLS)

    X_train_enc = pd.get_dummies(X_train, columns=CATEGORICAL_COLS, dtype=np.float32)
    X_test_enc = pd.get_dummies(X_test, columns=CATEGORICAL_COLS, dtype=np.float32)

    # Align test to training column layout — fills absent columns with 0.0.
    X_test_enc = X_test_enc.reindex(columns=X_train_enc.columns, fill_value=0.0)

    logger.info(
        "  Post-OHE shape — train: %s | test: %s",
        X_train_enc.shape,
        X_test_enc.shape,
    )
    return X_train_enc, X_test_enc


# ---------------------------------------------------------------------------
# Step 5+6 — Feature selection (SelectKBest)
# ---------------------------------------------------------------------------
def apply_select_k_best(
    X_train: np.ndarray,
    X_test: np.ndarray,
    k: int = K_BEST,
) -> Tuple[np.ndarray, np.ndarray, SelectKBest]:
    """Filter to the ``k`` features with the highest ANOVA F-score.

    One-Hot Encoding inflates the feature space significantly (the three
    categorical columns alone contribute up to ~85 binary columns).  Most of
    these OHE columns are very sparse and carry little discriminative power.
    ``SelectKBest(f_classif)`` uses the univariate ANOVA F-statistic to score
    each feature's linear separability between the two classes and retains only
    the top ``k``.

    Zero-leakage contract
    ---------------------
    ``selector.fit_transform(X_train, y_train)``  ← F-statistics computed on
                                                     training data only.
    ``selector.transform(X_test)``                ← Same column mask applied;
                                                     test labels never seen.

    Parameters
    ----------
    X_train, X_test:
        NumPy arrays from the OHE stage.
    k:
        Number of features to keep.  Default is ``K_BEST`` (20).

    Returns
    -------
    X_train_sel, X_test_sel : np.ndarray
        Reduced arrays with shape (n_samples, k).
    selector : SelectKBest
        Fitted selector object, serialised for inference reuse.
    """
    logger.info("Applying SelectKBest(f_classif, k=%d) …", k)
    # NOTE: y_train must be passed here but is NOT used for X_test transform.
    raise RuntimeError(
        "apply_select_k_best must be called from run_pipeline which supplies y_train; "
        "this sentinel is replaced in run_pipeline."
    )


def _apply_select_k_best_internal(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    k: int = K_BEST,
) -> Tuple[np.ndarray, np.ndarray, SelectKBest]:
    """Internal implementation — separated to keep the public signature clean."""
    selector = SelectKBest(score_func=f_classif, k=k)

    X_train_sel = selector.fit_transform(X_train, y_train)
    X_test_sel = selector.transform(X_test)  # NEVER fit on test

    logger.info(
        "  Post-SelectKBest shape — train: %s | test: %s",
        X_train_sel.shape,
        X_test_sel.shape,
    )
    return X_train_sel, X_test_sel, selector


# ---------------------------------------------------------------------------
# Step 7 — Dimensionality reduction (PCA → 4 components)
# ---------------------------------------------------------------------------
def apply_pca(
    X_train: np.ndarray,
    X_test: np.ndarray,
    n_components: int = N_QUBITS,
) -> Tuple[np.ndarray, np.ndarray, PCA]:
    """Compress feature space to ``n_components`` principal components.

    Why PCA after SelectKBest?
    --------------------------
    SelectKBest retains 20 uncorrelated-ish features.  PCA then extracts the
    *directions of maximum variance* in that 20-D space and projects it onto
    the 4 principal axes.  This two-stage approach (filter → projection) is
    more stable than going directly from ~120 OHE features to 4 components.

    Hardware constraint
    -------------------
    The QSVM uses a 4-qubit variational circuit.  Each data point must be
    encoded as exactly 4 rotation angles (one per qubit), so ``n_components``
    is hard-coded to ``N_QUBITS = 4``.

    Zero-leakage contract
    ---------------------
    ``pca.fit_transform(X_train)``  ← principal axes estimated from train only.
    ``pca.transform(X_test)``       ← projects test onto pre-learnt axes.

    Parameters
    ----------
    X_train, X_test:
        Post-SelectKBest NumPy arrays.
    n_components:
        Target dimensionality.  Must equal the qubit count of the circuit.

    Returns
    -------
    X_train_pca, X_test_pca : np.ndarray
        Shape (n_samples, n_components) arrays.
    pca : PCA
        Fitted PCA object, serialised for inference reuse.
    """
    logger.info("Applying PCA(n_components=%d) …", n_components)
    pca = PCA(n_components=n_components, random_state=42)

    X_train_pca = pca.fit_transform(X_train)  # learns eigenvectors from train
    X_test_pca = pca.transform(X_test)        # NEVER fit on test

    explained = pca.explained_variance_ratio_.sum() * 100
    logger.info(
        "  Cumulative explained variance: %.2f%%  |  "
        "Post-PCA shape — train: %s | test: %s",
        explained,
        X_train_pca.shape,
        X_test_pca.shape,
    )
    return X_train_pca, X_test_pca, pca


# ---------------------------------------------------------------------------
# Step 8 — Quantum-angle scaling  [0, π]
# ---------------------------------------------------------------------------
def apply_quantum_scaler(
    X_train: np.ndarray,
    X_test: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, MinMaxScaler]:
    """Scale each PCA component to the rotation-angle range [0, π].

    Quantum gate motivation
    -----------------------
    In the ZZFeatureMap / angle encoding circuits commonly used for QSVM,
    each classical feature x_i is embedded via a single-qubit rotation gate:

        RY(x_i)|0⟩  =  cos(x_i/2)|0⟩ + sin(x_i/2)|1⟩

    The gate accepts an angle θ.  By constraining θ ∈ [0, π]:
    – θ = 0   →  qubit stays in |0⟩  (zero rotation)
    – θ = π   →  qubit flips to |1⟩  (full half-rotation on Bloch sphere)
    – θ ∈ (0, π) → superposition state on the upper Bloch hemisphere

    Scaling to exactly [0, π] (not, say, [0, 1]) means:
    a) Every part of the accessible Bloch hemisphere is utilised, maximising
       the expressibility of the feature map.
    b) Angles never wrap around (θ > 2π would alias), preserving injectivity
       of the embedding (distinct data points → distinct quantum states).
    c) The inner-product quantum kernel  K(x,z) = |⟨ψ(x)|ψ(z)⟩|²  is a
       monotone function of the Euclidean distance in [0, π]^4 space, which
       aligns nicely with the SVM kernel's geometric interpretation.

    Zero-leakage contract
    ---------------------
    ``scaler.fit_transform(X_train)``  ← min/max statistics from train only.
    ``scaler.transform(X_test)``       ← clips and rescales test data using
                                          the pre-learnt train min/max.

    Parameters
    ----------
    X_train, X_test:
        Post-PCA NumPy arrays with shape (n_samples, 4).

    Returns
    -------
    X_train_scaled, X_test_scaled : np.ndarray
        Arrays with all values in [0, π].
    scaler : MinMaxScaler
        Fitted scaler object, serialised for inference reuse.
    """
    logger.info(
        "Applying MinMaxScaler(feature_range=(0, pi=%.6f)) for quantum angle embedding ...",
        ANGLE_MAX,
    )
    scaler = MinMaxScaler(feature_range=(0.0, ANGLE_MAX))

    X_train_scaled = scaler.fit_transform(X_train)  # learns min/max from train
    X_test_scaled = scaler.transform(X_test)        # NEVER fit on test
    X_test_scaled = np.clip(X_test_scaled, 0, np.pi)
    logger.info(
        "  Train angle range — min: %.6f rad | max: %.6f rad",
        X_train_scaled.min(),
        X_train_scaled.max(),
    )
    logger.info(
        "  Test  angle range — min: %.6f rad | max: %.6f rad",
        X_test_scaled.min(),
        X_test_scaled.max(),
    )
    return X_train_scaled, X_test_scaled, scaler


# ---------------------------------------------------------------------------
# Step 9 — Artifact persistence
# ---------------------------------------------------------------------------
def save_artifacts(
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
    selector: SelectKBest,
    pca: PCA,
    scaler: MinMaxScaler,
) -> None:
    """Persist processed data arrays and fitted transformer objects to disk.

    Processed arrays  →  ``data/processed/*.npy``
    Transformers      →  ``models/*.joblib``

    Using ``.npy`` for NumPy arrays is the most compact, portable, and
    type-preserving format for numerical matrices.  ``joblib`` is the
    sklearn-recommended serialisation backend for estimator objects because it
    handles large internal arrays (e.g. PCA components) more efficiently than
    plain ``pickle``.

    Parameters
    ----------
    X_train, X_test:
        Final scaled feature matrices.
    y_train, y_test:
        Binarised integer label vectors.
    selector, pca, scaler:
        Fitted transformer objects for downstream inference.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # --- Data arrays ---
    data_artifacts = {
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
    }
    for name, array in data_artifacts.items():
        path = PROCESSED_DIR / f"{name}.npy"
        np.save(path, array)
        logger.info("  Saved %-10s -> %s  shape=%s dtype=%s", name, path, array.shape, array.dtype)

    # --- Transformer objects ---
    model_artifacts = {
        "selector_kbest.joblib": selector,
        "pca_4components.joblib": pca,
        "scaler_minmax_pi.joblib": scaler,
    }
    for filename, obj in model_artifacts.items():
        path = MODELS_DIR / filename
        joblib.dump(obj, path)
        logger.info("  Saved transformer -> %s", path)


# ---------------------------------------------------------------------------
# Master pipeline
# ---------------------------------------------------------------------------
def run_pipeline() -> None:
    """Execute the full NSL-KDD → QSVM preprocessing pipeline end-to-end.

    Raises
    ------
    FileNotFoundError
        If either raw data file is missing.
    ValueError
        If the processed arrays violate the expected shape/value constraints.
    """
    logger.info("=" * 70)
    logger.info("NSL-KDD QSVM Preprocessing Pipeline — START")
    logger.info("=" * 70)

    # ------------------------------------------------------------------
    # 1. Load raw data
    # ------------------------------------------------------------------
    for path in (TRAIN_FILE, TEST_FILE):
        if not path.exists():
            raise FileNotFoundError(
                f"Raw data file not found: {path}\n"
                "Please place KDDTrain+.txt and KDDTest+.txt in data/raw/"
            )

    df_train = load_raw_data(TRAIN_FILE)
    df_test = load_raw_data(TEST_FILE)

    # ------------------------------------------------------------------
    # 2. Label engineering
    # ------------------------------------------------------------------
    logger.info("Binarising labels (normal=0, attack=1) …")
    df_train[LABEL_COL] = binarise_labels(df_train[LABEL_COL])
    df_test[LABEL_COL] = binarise_labels(df_test[LABEL_COL])

    train_dist = df_train[LABEL_COL].value_counts().to_dict()
    test_dist = df_test[LABEL_COL].value_counts().to_dict()
    logger.info("  Train label distribution: %s", train_dist)
    logger.info("  Test  label distribution: %s", test_dist)

    # ------------------------------------------------------------------
    # 3. Feature / label split
    # ------------------------------------------------------------------
    logger.info("Splitting features and labels …")
    X_train_raw, y_train = split_features_labels(df_train)
    X_test_raw, y_test = split_features_labels(df_test)

    y_train_np: np.ndarray = y_train.to_numpy(dtype=np.int64)
    y_test_np: np.ndarray = y_test.to_numpy(dtype=np.int64)

    # ------------------------------------------------------------------
    # 4. One-Hot Encoding
    # ------------------------------------------------------------------
    X_train_enc, X_test_enc = one_hot_encode(X_train_raw, X_test_raw)

    # Convert to float32 NumPy for sklearn compatibility.
    X_train_np: np.ndarray = X_train_enc.to_numpy(dtype=np.float32)
    X_test_np: np.ndarray = X_test_enc.to_numpy(dtype=np.float32)

    # ------------------------------------------------------------------
    # 5+6. Feature selection (SelectKBest — fit on train ONLY)
    # ------------------------------------------------------------------
    X_train_sel, X_test_sel, selector = _apply_select_k_best_internal(
        X_train_np, y_train_np, X_test_np, k=K_BEST
    )

    # ------------------------------------------------------------------
    # 7. PCA (fit on train ONLY)
    # ------------------------------------------------------------------
    X_train_pca, X_test_pca, pca = apply_pca(X_train_sel, X_test_sel)

    # ------------------------------------------------------------------
    # 8. Quantum-angle scaling (fit on train ONLY)
    # ------------------------------------------------------------------
    X_train_final, X_test_final, scaler = apply_quantum_scaler(
        X_train_pca, X_test_pca
    )

    # ------------------------------------------------------------------
    # Sanity checks
    # ------------------------------------------------------------------
    logger.info("Running post-processing sanity checks …")

    assert X_train_final.shape[1] == N_QUBITS, (
        f"Expected {N_QUBITS} features, got {X_train_final.shape[1]}"
    )
    assert X_test_final.shape[1] == N_QUBITS, (
        f"Expected {N_QUBITS} features, got {X_test_final.shape[1]}"
    )
    # MinMaxScaler guarantees the training set maps to [0, ANGLE_MAX] but
    # floating-point arithmetic can produce values marginally outside bounds;
    # a tolerance of 1e-6 covers any such precision noise.
    assert X_train_final.min() >= -1e-6, (
        f"Train values below 0 -- scaling error (min={X_train_final.min():.8f})"
    )
    assert X_train_final.max() <= ANGLE_MAX + 1e-6, (
        f"Train values above pi -- scaling error (max={X_train_final.max():.8f})"
    )
    # Test set *may* exceed [0,π] slightly if PCA projections fall outside the
    # training convex hull; log a warning rather than hard-failing.
    if X_test_final.min() < -1e-9 or X_test_final.max() > ANGLE_MAX + 1e-9:
        logger.warning(
            "Test set has values outside [0, pi] -- PCA projections outside "
            "training convex hull (expected for out-of-distribution samples). "
            "Consider clipping before circuit evaluation."
        )

    logger.info("  [OK] X_train shape: %s | dtype: %s", X_train_final.shape, X_train_final.dtype)
    logger.info("  [OK] X_test  shape: %s | dtype: %s", X_test_final.shape, X_test_final.dtype)
    logger.info("  [OK] y_train shape: %s | classes: %s", y_train_np.shape, np.unique(y_train_np))
    logger.info("  [OK] y_test  shape: %s | classes: %s", y_test_np.shape, np.unique(y_test_np))

    # ------------------------------------------------------------------
    # 9. Save artifacts
    # ------------------------------------------------------------------
    logger.info("Persisting processed data and transformer objects …")
    save_artifacts(
        X_train_final, X_test_final,
        y_train_np, y_test_np,
        selector, pca, scaler,
    )

    logger.info("=" * 70)
    logger.info("NSL-KDD QSVM Preprocessing Pipeline — COMPLETE")
    logger.info("=" * 70)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_pipeline()
