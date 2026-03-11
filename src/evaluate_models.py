"""
evaluate_models.py
==================
Phase 3 -- Evaluation & Tuning pipeline for the NSL-KDD QSVM project.

Purpose
-------
This script performs three tasks against the models trained in Phase 2:
  1. Hyperparameter tuning  -- applied ONLY to the Classical SVM.
  2. Inference benchmarking -- latency profiling for both models.
  3. Visual evaluation      -- Confusion Matrices and ROC Curves saved
                               to reports/ as publication-quality PNGs.

Asymmetric Tuning Strategy (Why we tune CSVM but not QSVM)
----------------------------------------------------------
GridSearchCV with K-fold cross-validation requires re-fitting the model
K * |param_grid| times.  For the Classical SVM with the RBF kernel this
is cheap: the kernel matrix is an O(N^2) inner product that takes
microseconds per pair on a CPU.

For the Quantum SVM the story is radically different.  Each kernel
evaluation K(x_i, x_j) = |<0| U†(x_j) U(x_i) |0>|^2 requires running
a 4-qubit circuit.  On the local StatevectorSampler simulator, computing
the 1000x1000 training Gram matrix alone takes ~75 minutes (see Phase 2).
A GridSearchCV with 16 parameter combinations and 5-fold CV would demand:
    16 combinations * 5 folds = 80 full Gram matrix computations
    80 * 75 min = 6,000 minutes  ~= 100 hours
This is obviously intractable on local simulation hardware.  The correct
strategy for quantum kernel tuning is either:
  a) Use a quantum cloud backend (IBM Quantum, IonQ) where circuits run
     in parallel across QPUs.
  b) Use kernel alignment methods that tune the feature map without
     repeating the full Gram matrix computation.
  c) Freeze the quantum kernel and tune only C (the SVM regularisation
     parameter) on a pre-computed Gram matrix -- feasible, but requires
     storing and re-using the exact Gram matrix from Phase 2.
We adopt option (c) as a future extension; for this script we skip QSVM
tuning entirely and evaluate the Phase 2 baseline.

Why Recall is the primary metric for IDS
-----------------------------------------
In an Intrusion Detection System (IDS), the cost asymmetry between error
types is extreme:
  - False Negative (FN): an attack is classified as normal traffic.
    Consequence: the intrusion succeeds; data is compromised.
  - False Positive (FP): normal traffic is flagged as an attack.
    Consequence: a security alert is raised; an analyst reviews it.
The cost of a FN vastly exceeds the cost of a FP.  Therefore we optimise
for Recall (= TP / (TP + FN)) -- the fraction of true attacks detected --
as the primary metric, accepting some precision loss.

Exact Subsample Reconstruction (Why this is critical)
------------------------------------------------------
The QSVM was trained in Phase 2 with kernel='precomputed'.  Sklearn's SVC
in precomputed mode does NOT store support vectors; instead it stores the
INTEGER INDICES of the support vectors within the training matrix that was
passed to fit().  Specifically, self.support_ contains indices into the
1000-row training subsample.

At inference time, predict(K_test) requires K_test to have shape
(N_test, N_train) where N_train is the EXACT same 1000 samples used during
fit().  If even one training sample is different, the support vector indices
will reference wrong rows in the kernel matrix, producing completely garbage
predictions without any error being raised.

Reconstruction guarantee: we use the identical call to train_test_split
with the same random_state=42, which makes the split deterministic.
"""

from __future__ import annotations

import logging
import sys
import time
import warnings
from pathlib import Path
from typing import Tuple

import joblib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import seaborn as sns
from qiskit.circuit.library import zz_feature_map
from qiskit.primitives import StatevectorSampler
from qiskit_machine_learning.kernels import FidelityQuantumKernel
from qiskit_machine_learning.state_fidelities import ComputeUncompute
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.svm import SVC

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"
MODELS_DIR: Path = PROJECT_ROOT / "models"
REPORTS_DIR: Path = PROJECT_ROOT / "reports"

# ---------------------------------------------------------------------------
# Experiment constants  -- MUST match Phase 2 exactly
# ---------------------------------------------------------------------------
N_QUBITS: int = 4
ZZ_REPS: int = 2
ZZ_ENTANGLEMENT: str = "linear"

# These sizes and the random state MUST be identical to train_qsvm.py,
# otherwise the reconstructed training subsample will differ from the one
# stored inside the QSVM's support_ indices.
N_TRAIN_SUB: int = 1000
N_TEST_SUB: int = 300
RANDOM_STATE: int = 42

# ---------------------------------------------------------------------------
# GridSearchCV hyper-parameter grid for the Classical SVM
# ---------------------------------------------------------------------------
# C     : regularisation strength inverse (lower C = more margin violations
#         allowed = softer boundary = better generalisation on noisy data).
# gamma : RBF kernel bandwidth parameter 1/(2*sigma^2).
#         'scale' = 1 / (n_features * X.var()) -- auto-adapts to feature scale.
#         Large gamma -> narrow Gaussian -> only very nearby points influence
#         the boundary (high variance, potential overfit).
#         Small gamma -> wide Gaussian -> distant points matter (high bias).
CSVM_PARAM_GRID: dict[str, list] = {
    "C":     [0.1, 1, 10, 100],
    "gamma": [1, 0.1, 0.01, "scale"],
}
CV_FOLDS: int = 5
CV_SCORING: str = "recall"

# matplotlib style settings
FIGURE_DPI: int = 300
CMAP_CM: str = "Blues"


# ---------------------------------------------------------------------------
# Step 1 -- Data loading & exact subsample reconstruction
# ---------------------------------------------------------------------------
def load_and_reconstruct_subsamples() -> (
    Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
):
    """Load the processed arrays and reconstruct the exact Phase 2 subsamples.

    The reconstruction uses the IDENTICAL train_test_split call as Phase 2
    (same sizes, same stratify=y, same random_state=42).  This is mandatory
    for correct QSVM inference -- see the module docstring for a detailed
    explanation of why the training subsample must match exactly.

    Returns
    -------
    X_train_sub : np.ndarray, shape (1000, 4), float64
    y_train_sub : np.ndarray, shape (1000,),   int64
    X_test_sub  : np.ndarray, shape (300, 4),  float64
    y_test_sub  : np.ndarray, shape (300,),    int64

    Raises
    ------
    FileNotFoundError
        If any processed .npy file is missing.
    AssertionError
        If the reconstructed shapes do not match expected sizes.
    """
    required = {
        "X_train": PROCESSED_DIR / "X_train.npy",
        "y_train": PROCESSED_DIR / "y_train.npy",
        "X_test":  PROCESSED_DIR / "X_test.npy",
        "y_test":  PROCESSED_DIR / "y_test.npy",
    }
    for name, path in required.items():
        if not path.exists():
            raise FileNotFoundError(
                f"Missing file '{name}' at: {path}. "
                "Run src/data_preprocessing.py first."
            )

    logger.info("Loading full processed arrays from %s ...", PROCESSED_DIR)
    X_full = np.load(required["X_train"]).astype(np.float64)
    y_full = np.load(required["y_train"])
    X_te_full = np.load(required["X_test"]).astype(np.float64)
    y_te_full = np.load(required["y_test"])

    logger.info(
        "  Full sizes -- X_train: %s | X_test: %s",
        X_full.shape, X_te_full.shape,
    )

    # ---------------------------------------------------------------------------
    # Reconstruct the Phase 2 training subsample.
    # train_test_split(test_size=discard_fraction, stratify=y, random_state=42)
    # is deterministic: for the same inputs it always produces the same split.
    # The fraction (1 - N_TRAIN_SUB / len(y)) is discarded; we keep the rest.
    # ---------------------------------------------------------------------------
    train_discard = 1.0 - N_TRAIN_SUB / len(y_full)
    X_train_sub, _, y_train_sub, _ = train_test_split(
        X_full, y_full,
        test_size=train_discard,
        stratify=y_full,
        random_state=RANDOM_STATE,
    )

    test_discard = 1.0 - N_TEST_SUB / len(y_te_full)
    X_test_sub, _, y_test_sub, _ = train_test_split(
        X_te_full, y_te_full,
        test_size=test_discard,
        stratify=y_te_full,
        random_state=RANDOM_STATE,
    )

    assert X_train_sub.shape == (N_TRAIN_SUB, N_QUBITS), (
        f"Train subsample shape mismatch: {X_train_sub.shape}"
    )
    assert X_test_sub.shape == (N_TEST_SUB, N_QUBITS), (
        f"Test subsample shape mismatch: {X_test_sub.shape}"
    )

    tr_dist = dict(zip(*np.unique(y_train_sub, return_counts=True)))
    te_dist = dict(zip(*np.unique(y_test_sub, return_counts=True)))
    logger.info("  Train subsample: %d samples | class dist: %s", len(y_train_sub), tr_dist)
    logger.info("  Test  subsample: %d samples | class dist: %s", len(y_test_sub),  te_dist)
    return X_train_sub, y_train_sub, X_test_sub, y_test_sub


# ---------------------------------------------------------------------------
# Step 2 -- Quantum environment reconstruction
# ---------------------------------------------------------------------------
def build_quantum_kernel() -> FidelityQuantumKernel:
    """Recreate the exact ZZ quantum kernel used in Phase 2.

    Why reconstruction is needed rather than loading a serialised kernel
    ---------------------------------------------------------------------
    FidelityQuantumKernel wraps a live Qiskit circuit + sampler backend.
    These objects contain multiprocessing locks and GPU handles that cannot
    be reliably serialised via joblib/pickle across Python sessions.  The
    correct pattern is to rebuild the lightweight kernel descriptor (the
    QuantumCircuit has no state) and reuse the HEAVY artefact (the trained
    SVC with its learned support vector coefficients) from disk.

    The kernel evaluation K(x, z) = |<0|U†(z)U(x)|0>|^2 is a pure function
    of the inputs and the fixed feature map -- it has no trainable parameters
    that need to be restored from Phase 2.

    Returns
    -------
    FidelityQuantumKernel
        Configured and ready for .evaluate() calls.
    """
    logger.info(
        "Rebuilding ZZFeatureMap: n_qubits=%d | reps=%d | entanglement=%s",
        N_QUBITS, ZZ_REPS, ZZ_ENTANGLEMENT,
    )

    # Function-based API (Qiskit >= 2.1; class-based ZZFeatureMap is
    # deprecated in 2.1 and removed in 3.0).
    feature_map = zz_feature_map(
        feature_dimension=N_QUBITS,
        reps=ZZ_REPS,
        entanglement=ZZ_ENTANGLEMENT,
    )

    # StatevectorSampler: noiseless, exact simulation.  No shot noise means
    # K(x, z) values are the true fidelity probabilities, not Monte-Carlo
    # estimates.  This is the correct backend for research-grade benchmarking.
    sampler = StatevectorSampler()
    fidelity = ComputeUncompute(sampler=sampler)

    # enforce_psd=True clips tiny negative eigenvalues arising from floating-
    # point arithmetic (the true quantum kernel is always PSD; numerical
    # errors can produce eigenvalues of order -1e-3 to -1e-6).
    quantum_kernel = FidelityQuantumKernel(
        feature_map=feature_map,
        fidelity=fidelity,
        enforce_psd=True,
    )
    logger.info(
        "  Quantum kernel ready -- Hilbert space: C^%d  | circuit depth: %d",
        2 ** N_QUBITS,
        feature_map.decompose().depth(),
    )
    return quantum_kernel


# ---------------------------------------------------------------------------
# Step 3 -- Precompute test kernel matrix
# ---------------------------------------------------------------------------
def compute_test_kernel(
    quantum_kernel: FidelityQuantumKernel,
    X_test: np.ndarray,
    X_train: np.ndarray,
) -> Tuple[np.ndarray, float]:
    """Evaluate K_test = K(X_test, X_train) with wall-clock timing.

    Shape and semantics
    -------------------
    K_test has shape (N_test, N_train) = (300, 1000).  Entry K_test[i, j]
    is the quantum fidelity between the i-th test point and the j-th
    training point:
        K_test[i, j] = |<phi(x_test_i)|phi(x_train_j)>|^2

    During QSVM.predict(K_test), sklearn computes the SVM decision function:
        f(x_test_i) = SUM_{j in SVs}  alpha_j * y_j * K_test[i, j]  +  b
    where alpha_j are the learned dual coefficients for support vector j.
    The classification is sign(f(x_test_i)).

    This is the ONLY valid way to use a precomputed-kernel SVC for inference.
    Passing raw features X_test would cause a silent wrong-answer bug because
    sklearn would interpret the raw feature values as kernel matrix entries.

    Parameters
    ----------
    quantum_kernel : FidelityQuantumKernel
    X_test  : np.ndarray, shape (N_test,  4)  -- test feature vectors
    X_train : np.ndarray, shape (N_train, 4)  -- EXACT Phase 2 training vectors

    Returns
    -------
    K_test   : np.ndarray, shape (N_test, N_train)
    elapsed  : float  -- wall-clock seconds
    """
    n_test, n_train = len(X_test), len(X_train)
    n_circuits = n_test * n_train
    logger.info(
        "Computing K_test: (%d x %d) -- %d circuit evaluations ...",
        n_test, n_train, n_circuits,
    )
    t0 = time.perf_counter()
    K_test = quantum_kernel.evaluate(x_vec=X_test, y_vec=X_train)
    elapsed = time.perf_counter() - t0
    logger.info(
        "  K_test computed in %.1f s (%.1f min) | shape: %s",
        elapsed, elapsed / 60.0, K_test.shape,
    )
    logger.info(
        "  K_test stats: min=%.4f | max=%.4f | mean=%.4f",
        K_test.min(), K_test.max(), K_test.mean(),
    )
    return K_test, elapsed


# ---------------------------------------------------------------------------
# Step 4 -- Load baseline models
# ---------------------------------------------------------------------------
def load_models() -> Tuple[SVC, SVC]:
    """Deserialise the two Phase 2 trained SVC objects from models/.

    Returns
    -------
    qsvm : SVC  -- quantum kernel ('precomputed'), as trained in Phase 2
    csvm : SVC  -- classical RBF kernel, baseline from Phase 2

    Raises
    ------
    FileNotFoundError
        If either .pkl file is absent.
    """
    paths = {
        "qsvm": MODELS_DIR / "qsvm_model.pkl",
        "csvm": MODELS_DIR / "csvm_model.pkl",
    }
    for name, path in paths.items():
        if not path.exists():
            raise FileNotFoundError(
                f"Missing model file '{name}' at: {path}. "
                "Run src/train_qsvm.py first."
            )

    logger.info("Loading baseline models from %s ...", MODELS_DIR)
    qsvm: SVC = joblib.load(paths["qsvm"])
    csvm: SVC = joblib.load(paths["csvm"])

    logger.info(
        "  QSVM loaded -- kernel=%s | C=%.1f | n_support=%s",
        qsvm.kernel, qsvm.C, qsvm.n_support_,
    )
    logger.info(
        "  CSVM loaded -- kernel=%s | C=%.1f | gamma=%s | n_support=%s",
        csvm.kernel, csvm.C, csvm.gamma, csvm.n_support_,
    )
    return qsvm, csvm


# ---------------------------------------------------------------------------
# Step 5 -- Hyperparameter tuning (Classical SVM only)
# ---------------------------------------------------------------------------
def tune_classical_svm(
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> Tuple[SVC, dict]:
    """Run GridSearchCV on the Classical RBF-SVM and return the best estimator.

    Tuning strategy
    ---------------
    We optimise for Recall (attack class = 1) as the primary scoring metric.
    GridSearchCV maximises mean CV Recall across the 5 folds by varying C and
    gamma.  The best combination is then used to refit a new SVC on the full
    1000-sample training set (sklearn does this automatically with refit=True).

    Why 5-fold CV on 1000 samples?
    Each fold trains on 800 samples and validates on 200.  This gives reliable
    generalisation estimates for our sub-sampled regime without requiring a
    separate validation split that would further shrink the training set.

    Note on QSVM tuning
    -------------------
    As documented in the module docstring, QSVM hyperparameter tuning is
    computationally intractable on local simulation hardware.  This function
    is intentionally NOT called for the quantum model.

    Parameters
    ----------
    X_train : np.ndarray, shape (1000, 4)
    y_train : np.ndarray, shape (1000,)

    Returns
    -------
    best_csvm : SVC
        New SVC refitted on all 1000 training samples with the best params.
    best_params : dict
        The winning hyperparameter combination.
    """
    logger.warning(
        "Skipping Hyperparameter Tuning for QSVM due to O(N^2) computational "
        "bottlenecks on local simulation hardware.  The Phase 2 baseline QSVM "
        "will be used directly for evaluation."
    )
    logger.info(
        "Starting GridSearchCV for Classical SVM | "
        "param_grid=%s | cv=%d | scoring='%s' ...",
        CSVM_PARAM_GRID, CV_FOLDS, CV_SCORING,
    )

    n_combinations = len(CSVM_PARAM_GRID["C"]) * len(CSVM_PARAM_GRID["gamma"])
    logger.info(
        "  %d parameter combinations x %d folds = %d fits",
        n_combinations, CV_FOLDS, n_combinations * CV_FOLDS,
    )

    t0 = time.perf_counter()
    grid_search = GridSearchCV(
        estimator=SVC(kernel="rbf", class_weight="balanced", random_state=RANDOM_STATE),
        param_grid=CSVM_PARAM_GRID,
        scoring=CV_SCORING,
        cv=CV_FOLDS,
        refit=True,    # automatically refit best params on full X_train
        n_jobs=-1,     # parallelise across all CPU cores
        verbose=0,
    )
    grid_search.fit(X_train, y_train)
    elapsed = time.perf_counter() - t0

    best_params = grid_search.best_params_
    best_score = grid_search.best_score_

    logger.info(
        "  GridSearchCV complete in %.1f s | best params: %s | "
        "best CV Recall: %.4f",
        elapsed, best_params, best_score,
    )

    # Retrieve the already-refitted estimator (no extra fit() call needed).
    best_csvm: SVC = grid_search.best_estimator_
    return best_csvm, best_params


# ---------------------------------------------------------------------------
# Step 6 -- Inference with timing
# ---------------------------------------------------------------------------
def run_inference(
    qsvm: SVC,
    csvm_tuned: SVC,
    K_test: np.ndarray,
    X_test: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float, float]:
    """Generate predictions and decision scores for both models.

    For the QSVM
    ------------
    Input to predict() is K_test -- the precomputed (300, 1000) kernel matrix.
    Input to decision_function() is the same K_test.  The decision function:
        f(i) = SUM_{j in SVs}  alpha_j * y_j * K_test[i, j]  +  b
    gives a real-valued score; sign(f(i)) is the class prediction.

    For the Tuned CSVM
    ------------------
    Input to predict() and decision_function() is the raw feature matrix
    X_test of shape (300, 4).  Sklearn internally computes the RBF kernel
    between X_test and the stored support vectors.

    Using decision_function() rather than predict_proba()
    ------------------------------------------------------
    sklearn.svm.SVC does not expose calibrated probabilities by default
    (predict_proba requires probability=True at construction time, which
    triggers expensive Platt scaling and changes the decision boundary).
    decision_function() returns the signed distance from the hyperplane,
    which is a valid ranking score for ROC AUC computation.

    Parameters
    ----------
    qsvm      : fitted QSVM (kernel='precomputed')
    csvm_tuned: fitted tuned CSVM (kernel='rbf')
    K_test    : np.ndarray, shape (300, 1000) -- QSVM test kernel matrix
    X_test    : np.ndarray, shape (300, 4)   -- raw features for CSVM

    Returns
    -------
    y_pred_qsvm  : np.ndarray, shape (300,) -- QSVM class predictions
    y_pred_csvm  : np.ndarray, shape (300,) -- CSVM class predictions
    scores_qsvm  : np.ndarray, shape (300,) -- QSVM decision function values
    scores_csvm  : np.ndarray, shape (300,) -- CSVM decision function values
    t_qsvm       : float -- QSVM inference time in seconds
    t_csvm       : float -- CSVM inference time in seconds
    """
    # QSVM inference
    logger.info("Running QSVM inference on K_test (%s) ...", K_test.shape)
    t0 = time.perf_counter()
    y_pred_qsvm = qsvm.predict(K_test)
    scores_qsvm = qsvm.decision_function(K_test)
    t_qsvm = time.perf_counter() - t0
    logger.info("  QSVM inference time: %.4f s", t_qsvm)

    # Classical SVM inference
    logger.info("Running Tuned CSVM inference on X_test (%s) ...", X_test.shape)
    t0 = time.perf_counter()
    y_pred_csvm = csvm_tuned.predict(X_test)
    scores_csvm = csvm_tuned.decision_function(X_test)
    t_csvm = time.perf_counter() - t0
    logger.info("  CSVM inference time: %.4f s", t_csvm)

    return y_pred_qsvm, y_pred_csvm, scores_qsvm, scores_csvm, t_qsvm, t_csvm


# ---------------------------------------------------------------------------
# Step 7 -- Classification report with Recall highlight
# ---------------------------------------------------------------------------
def print_classification_reports(
    y_true: np.ndarray,
    y_pred_qsvm: np.ndarray,
    y_pred_csvm: np.ndarray,
    best_params: dict,
) -> None:
    """Print full sklearn classification reports with attack-class Recall callout.

    The Recall for class 1 (attack) is the fraction of true attacks that
    the model correctly detected.  A Recall of 0.90 means 10% of attacks
    slipped through as False Negatives -- undetected intrusions.

    Parameters
    ----------
    y_true       : ground-truth binary labels for the test set
    y_pred_qsvm  : QSVM predictions
    y_pred_csvm  : Tuned CSVM predictions
    best_params  : dict of best GridSearchCV parameters (for display)
    """
    sep = "=" * 68
    thin = "-" * 68

    # ------------------------------------------------------------------ QSVM
    qsvm_report = classification_report(
        y_true, y_pred_qsvm,
        target_names=["Normal (0)", "Attack (1)"],
        digits=4,
    )
    q_recall_attack = float(
        classification_report(
            y_true, y_pred_qsvm,
            target_names=["Normal", "Attack"],
            output_dict=True,
        )["Attack"]["recall"]
    )

    # ------------------------------------------------------------------ CSVM
    csvm_report = classification_report(
        y_true, y_pred_csvm,
        target_names=["Normal (0)", "Attack (1)"],
        digits=4,
    )
    c_recall_attack = float(
        classification_report(
            y_true, y_pred_csvm,
            target_names=["Normal", "Attack"],
            output_dict=True,
        )["Attack"]["recall"]
    )

    lines = [
        "",
        sep,
        "  Phase 3 Evaluation -- Classification Reports",
        sep,
        "",
        f"  [1/2] Baseline QSVM  (ZZFeatureMap, kernel='precomputed', C=1.0)",
        thin,
        qsvm_report,
        f"  >>> Attack-class Recall: {q_recall_attack:.4f}  "
        f"({q_recall_attack*100:.1f}% of attacks detected) <<<",
        "",
        f"  [2/2] Tuned Classical SVM  (RBF kernel, best params: {best_params})",
        thin,
        csvm_report,
        f"  >>> Attack-class Recall: {c_recall_attack:.4f}  "
        f"({c_recall_attack*100:.1f}% of attacks detected) <<<",
        "",
        sep,
        "",
    ]
    print("\n".join(lines))

    # Also surface via the logger so the recall numbers appear in any log file.
    logger.info(
        "Attack Recall -- QSVM: %.4f | Tuned CSVM: %.4f",
        q_recall_attack, c_recall_attack,
    )


# ---------------------------------------------------------------------------
# Step 8 -- Confusion Matrix plot
# ---------------------------------------------------------------------------
def plot_confusion_matrices(
    y_true: np.ndarray,
    y_pred_qsvm: np.ndarray,
    y_pred_csvm: np.ndarray,
    best_params: dict,
) -> Path:
    """Save a side-by-side Confusion Matrix figure to reports/.

    Layout
    ------
    1 row x 2 columns:
      - Left  : Baseline QSVM
      - Right : Tuned Classical SVM

    Each subplot shows:
    - Raw counts as the primary annotation.
    - Row-normalised percentage in parentheses (so cells are comparable
      despite class imbalance in the 300-sample test set).

    Parameters
    ----------
    y_true      : ground-truth labels
    y_pred_qsvm : QSVM predictions
    y_pred_csvm : CSVM predictions
    best_params : GridSearchCV best parameters (for subplot title)

    Returns
    -------
    Path
        Absolute path to the saved PNG.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / "confusion_matrix.png"

    sns.set_theme(style="whitegrid", font_scale=1.1)

    class_names = ["Normal", "Attack"]
    cm_qsvm = confusion_matrix(y_true, y_pred_qsvm)
    cm_csvm = confusion_matrix(y_true, y_pred_csvm)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.suptitle(
        "NSL-KDD Intrusion Detection -- Confusion Matrices\n"
        "Test set: 300 stratified samples | Primary metric: Attack Recall",
        fontsize=13, fontweight="bold", y=1.02,
    )

    for ax, cm, title in zip(
        axes,
        [cm_qsvm, cm_csvm],
        [
            f"Baseline QSVM\n(ZZFeatureMap, reps=2, C=1.0, kernel=precomputed)",
            f"Tuned Classical SVM\n(RBF kernel, {best_params})",
        ],
    ):
        # Build annotation: "count\n(row%)" for each cell.
        # Row normalisation makes it easy to read per-class accuracy.
        cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)
        annot = np.empty_like(cm, dtype=object)
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                annot[i, j] = f"{cm[i, j]}\n({cm_norm[i, j]*100:.1f}%)"

        sns.heatmap(
            cm,
            annot=annot,
            fmt="",
            cmap=CMAP_CM,
            ax=ax,
            linewidths=0.5,
            linecolor="grey",
            xticklabels=class_names,
            yticklabels=class_names,
            cbar_kws={"shrink": 0.75},
            vmin=0,
        )
        ax.set_title(title, fontsize=10, pad=10)
        ax.set_xlabel("Predicted Label", fontsize=10)
        ax.set_ylabel("True Label", fontsize=10)

        # Rotate tick labels for readability.
        ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0)

        # Highlight the FN cell (True=Attack, Pred=Normal) in red to draw
        # attention to the cost-critical error type.
        ax.add_patch(plt.Rectangle((0, 1), 1, 1, fill=False,
                                   edgecolor="red", lw=2.5, zorder=5))

    plt.tight_layout()
    fig.savefig(out_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    logger.info("Confusion matrix saved -> %s", out_path)
    return out_path


# ---------------------------------------------------------------------------
# Step 9 -- ROC Curve plot
# ---------------------------------------------------------------------------
def plot_roc_curves(
    y_true: np.ndarray,
    scores_qsvm: np.ndarray,
    scores_csvm: np.ndarray,
    best_params: dict,
) -> Path:
    """Save a combined ROC Curve figure comparing QSVM and Tuned CSVM.

    ROC Curve interpretation for IDS
    ---------------------------------
    The ROC curve plots True Positive Rate (= Recall) vs False Positive Rate
    (= FP / (FP + TN)) across all possible decision thresholds.  For an IDS:
    - We want TPR close to 1.0 (catch all attacks) ...
    - ... while keeping FPR low (avoid overwhelming analysts with false alerts).
    - The Area Under the Curve (AUC) summarises this tradeoff in a single
      threshold-independent number.  AUC = 1.0 is perfect; AUC = 0.5 is random.

    Score source
    ------------
    Both models use decision_function() values as ranking scores.
    Higher decision_function values indicate stronger prediction of class 1
    (attack).  sklearn's roc_curve() internally thresholds these scores to
    produce the (FPR, TPR) curve.

    Note: decision_function() is preferred over predict_proba() here because:
    - SVC was constructed without probability=True, so predict_proba is
      unavailable without refitting.
    - The relative ranking of decision_function scores is identical to
      the ranking of class-1 probabilities, so AUC values are the same.

    Parameters
    ----------
    y_true      : ground-truth binary labels
    scores_qsvm : QSVM decision_function output
    scores_csvm : Tuned CSVM decision_function output
    best_params : GridSearchCV best parameters (for legend label)

    Returns
    -------
    Path
        Absolute path to the saved PNG.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / "roc_curve.png"

    sns.set_theme(style="whitegrid", font_scale=1.15)

    fpr_q, tpr_q, _ = roc_curve(y_true, scores_qsvm, pos_label=1)
    fpr_c, tpr_c, _ = roc_curve(y_true, scores_csvm, pos_label=1)
    auc_q = roc_auc_score(y_true, scores_qsvm)
    auc_c = roc_auc_score(y_true, scores_csvm)

    fig, ax = plt.subplots(figsize=(8, 6.5))

    ax.plot(
        fpr_q, tpr_q,
        color="#4C72B0",    # seaborn deep blue
        lw=2.2,
        label=f"Baseline QSVM  (AUC = {auc_q:.4f})",
    )
    ax.plot(
        fpr_c, tpr_c,
        color="#DD8452",    # seaborn deep orange
        lw=2.2,
        linestyle="--",
        label=f"Tuned CSVM  (AUC = {auc_c:.4f})  |  {best_params}",
    )
    # Random classifier reference line.
    ax.plot(
        [0, 1], [0, 1],
        color="grey",
        lw=1.2,
        linestyle=":",
        label="Random classifier (AUC = 0.50)",
    )

    # Mark the operating point chosen by each model's default threshold (0.0).
    def_tpr_q = np.mean(y_true[scores_qsvm >= 0] == 1) if np.any(scores_qsvm >= 0) else 0
    def_fpr_q = np.mean(y_true[scores_qsvm >= 0] == 0) if np.any(scores_qsvm >= 0) else 0
    def_tpr_c = np.mean(y_true[scores_csvm >= 0] == 1) if np.any(scores_csvm >= 0) else 0
    def_fpr_c = np.mean(y_true[scores_csvm >= 0] == 0) if np.any(scores_csvm >= 0) else 0

    ax.scatter(
        [def_fpr_q], [def_tpr_q],
        color="#4C72B0", s=90, zorder=5, marker="o", label="QSVM default threshold",
    )
    ax.scatter(
        [def_fpr_c], [def_tpr_c],
        color="#DD8452", s=90, zorder=5, marker="s", label="CSVM default threshold",
    )

    # Shade the AUC area under the QSVM curve for visual emphasis.
    ax.fill_between(fpr_q, tpr_q, alpha=0.08, color="#4C72B0")

    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.05)
    ax.set_xlabel("False Positive Rate  (FP / (FP + TN))", fontsize=12)
    ax.set_ylabel("True Positive Rate  (Recall = TP / (TP + FN))", fontsize=12)
    ax.set_title(
        "ROC Curves -- QSVM vs Tuned Classical SVM\n"
        "NSL-KDD Binary Intrusion Detection  |  Test set: 300 samples",
        fontsize=12, fontweight="bold",
    )
    ax.legend(loc="lower right", fontsize=9, framealpha=0.9)
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))

    plt.tight_layout()
    fig.savefig(out_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    logger.info("ROC curve saved -> %s", out_path)
    return out_path


# ---------------------------------------------------------------------------
# Master pipeline
# ---------------------------------------------------------------------------
def run_pipeline() -> None:
    """Execute the full Phase 3 evaluation pipeline end-to-end.

    Order of operations
    -------------------
    1. Load data + reconstruct exact Phase 2 subsamples.
    2. Rebuild quantum kernel environment.
    3. Precompute K_test = K(X_test_sub, X_train_sub).
    4. Load Phase 2 baseline models from disk.
    5. Tune Classical SVM via GridSearchCV (QSVM skipped -- O(N^2) reason).
    6. Run inference for both models; time each stage.
    7. Print classification reports with Recall callouts.
    8. Save Confusion Matrix figure (reports/confusion_matrix.png).
    9. Save ROC Curve figure (reports/roc_curve.png).
    """
    logger.info("=" * 68)
    logger.info("NSL-KDD QSVM Phase 3 -- Evaluation & Tuning Pipeline START")
    logger.info("=" * 68)

    # ------------------------------------------------------------------
    # 1. Data loading + exact subsample reconstruction
    # ------------------------------------------------------------------
    X_train_sub, y_train_sub, X_test_sub, y_test_sub = (
        load_and_reconstruct_subsamples()
    )

    # ------------------------------------------------------------------
    # 2. Quantum kernel reconstruction
    # ------------------------------------------------------------------
    quantum_kernel = build_quantum_kernel()

    # ------------------------------------------------------------------
    # 3. Precompute K_test  (300 x 1000 = 300,000 circuit evaluations)
    # ------------------------------------------------------------------
    K_test, kernel_time = compute_test_kernel(
        quantum_kernel, X_test_sub, X_train_sub
    )

    # ------------------------------------------------------------------
    # 4. Load baseline models
    # ------------------------------------------------------------------
    qsvm, csvm_baseline = load_models()

    # ------------------------------------------------------------------
    # 5. Tune Classical SVM (QSVM is intentionally skipped)
    # ------------------------------------------------------------------
    csvm_tuned, best_params = tune_classical_svm(X_train_sub, y_train_sub)

    # ------------------------------------------------------------------
    # 6. Inference with timing
    # ------------------------------------------------------------------
    y_pred_qsvm, y_pred_csvm, scores_qsvm, scores_csvm, t_q, t_c = (
        run_inference(qsvm, csvm_tuned, K_test, X_test_sub)
    )

    logger.info(
        "Inference summary -- QSVM: %.4f s (excl. %.1f s kernel compute) | "
        "CSVM: %.4f s",
        t_q, kernel_time, t_c,
    )

    # ------------------------------------------------------------------
    # 7. Classification reports
    # ------------------------------------------------------------------
    print_classification_reports(
        y_test_sub, y_pred_qsvm, y_pred_csvm, best_params
    )

    # ------------------------------------------------------------------
    # 8. Confusion Matrix visualisation
    # ------------------------------------------------------------------
    cm_path = plot_confusion_matrices(
        y_test_sub, y_pred_qsvm, y_pred_csvm, best_params
    )

    # ------------------------------------------------------------------
    # 9. ROC Curve visualisation
    # ------------------------------------------------------------------
    roc_path = plot_roc_curves(
        y_test_sub, scores_qsvm, scores_csvm, best_params
    )

    # ------------------------------------------------------------------
    # Final summary
    # ------------------------------------------------------------------
    logger.info("=" * 68)
    logger.info("Phase 3 complete.  Artifacts saved:")
    logger.info("  %s", cm_path)
    logger.info("  %s", roc_path)
    logger.info(
        "Tuned CSVM best params: %s | GridSearchCV scoring: %s",
        best_params, CV_SCORING,
    )
    logger.info(
        "Kernel pre-computation time: %.1f s (%.1f min)",
        kernel_time, kernel_time / 60.0,
    )
    logger.info("=" * 68)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_pipeline()
