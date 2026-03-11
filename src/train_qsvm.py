"""
train_qsvm.py
=============
Phase 2 — Quantum SVM training pipeline for the NSL-KDD binary intrusion
detection task.

Quantum Kernel Mathematics
--------------------------
The ZZFeatureMap embeds a classical vector x in R^n into a quantum state
|phi(x)> living in the 2^n-dimensional complex Hilbert space H = C^(2^n).
For n = 4 qubits this is H = C^16.

Encoding circuit U(x)
~~~~~~~~~~~~~~~~~~~~~~
The circuit alternates between:
  1. A layer of Hadamard gates H^(x4) that creates equal superposition:
         H^(x4)|0000> = (1/sqrt(16)) * SUM_z |z>
  2. Single-qubit diagonal phase gates encoding each feature individually:
         U1(x_i) = exp(i * x_i * Z_i)   (rotation around the Z axis)
  3. Two-qubit ZZ entangling gates encoding feature cross-correlations:
         U2(x_i, x_j) = exp(i * (pi - x_i)(pi - x_j) * Z_i x Z_j)
These three sub-layers are stacked reps=2 times, yielding the full
parameterised unitary:
         U(x) = [H^(x4) . U1(x) . U2(x)]^reps

Quantum kernel function
~~~~~~~~~~~~~~~~~~~~~~~
The quantum kernel between two data points x and z is defined as the
squared Hilbert-space inner product (circuit fidelity):

         K(x, z)  =  |<phi(x)|phi(z)>|^2
                   =  |<0|U†(z) . U(x)|0>|^2

Geometrically: K(x, z) measures how "close" the two 16-dimensional quantum
states are.  K(x, x) = 1 always; K(x, z) -> 0 as x and z diverge in the
feature space defined by U.

This kernel is computed by the ComputeUncompute algorithm:
  - Prepare U(x)|0>
  - Apply U†(z)  (the adjoint of U(z), computed via circuit inversion)
  - Measure the probability of observing the all-zeros bitstring |0000>
  - K(x, z) = P(|0000>)

Why this is powerful
~~~~~~~~~~~~~~~~~~~~
The classical equivalent of this kernel would require storing and computing
with 16-dimensional complex vectors for every pair (x, z).  On a quantum
computer, the evaluation stays within the quantum register and never
requires classical access to the full 16-D state vector.

Why ZZFeatureMap specifically
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The ZZ interaction  Z_i x Z_j  encodes the PRODUCT of features (x_i * x_j)
as a phase.  This creates a non-linear feature map that is hard to
classically simulate (up to polynomial overhead) and has been shown to
produce quantum advantage in certain kernel learning regimes
(Havlicek et al., Nature 2019).

Why reps=2 and linear entanglement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- reps=1  =>  shallow circuit, limited expressibility; may underfit.
- reps>2  =>  deeper circuit; exponentially more parameters; susceptible to
              the Barren Plateau phenomenon (McClean et al., Nat. Comm. 2018),
              where the gradient of the loss landscape vanishes exponentially
              with circuit depth, making optimisation intractable.
- reps=2  =>  sweet spot: sufficient expressibility without Barren Plateaus.
- 'linear' entanglement  =>  only nearest-neighbour pairs (0,1), (1,2), (2,3)
              are connected by ZZ gates.  This keeps the circuit depth O(n)
              (3 two-qubit gates per rep x 2 reps = 6 total) rather than the
              O(n^2) depth of 'full' entanglement, which further mitigates
              Barren Plateau risk and makes statevector simulation faster.

O(N^2) Bottleneck
~~~~~~~~~~~~~~~~~
Computing K(X_train, X_train) for N training samples requires N*(N-1)/2
unique circuit evaluations (the matrix is symmetric by definition).
For N = 125,973:  125,973 * 125,972 / 2 approx 7.93 billion evaluations.
This is computationally intractable on classical simulators.
Solution: sub-sample the training set to N_train = 1000 samples, which
requires only 1000 * 999 / 2 = 499,500 unique evaluations.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
from qiskit.circuit.library import zz_feature_map
from qiskit.primitives import StatevectorSampler
from qiskit_machine_learning.kernels import FidelityQuantumKernel
from qiskit_machine_learning.state_fidelities import ComputeUncompute
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
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
# Path constants
# ---------------------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"
MODELS_DIR: Path = PROJECT_ROOT / "models"

# ---------------------------------------------------------------------------
# Hyper-parameters and hardware constraints
# ---------------------------------------------------------------------------
# 4 qubits => 2^4 = 16 dimensional Hilbert space.
N_QUBITS: int = 4

# Sub-sample sizes that keep kernel matrix computation tractable.
# K_train is (N_TRAIN x N_TRAIN): 1000*999/2 = 499,500 unique evaluations.
# K_test  is (N_TEST  x N_TRAIN): 300*1000   = 300,000 evaluations.
N_TRAIN_SUBSAMPLE: int = 2500
N_TEST_SUBSAMPLE: int = 500

# ZZFeatureMap circuit design choices (see module docstring for rationale).
ZZ_REPS: int = 3
ZZ_ENTANGLEMENT: str = "full"

# Random seed for all stochastic operations.
RANDOM_STATE: int = 42


# ---------------------------------------------------------------------------
# Step 1 — Data loading
# ---------------------------------------------------------------------------
def load_processed_data() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Load the four pre-processed NumPy arrays from ``data/processed/``.

    The arrays were produced by ``src/data_preprocessing.py`` and contain:
    - ``X_train / X_test``: 4-D feature vectors scaled to [0, pi], ready
      for direct use as quantum gate rotation angles.
    - ``y_train / y_test``: binary integer labels  {0 = normal, 1 = attack}.

    Returns
    -------
    X_train, y_train, X_test, y_test : np.ndarray
        Raw (unsubsampled) full-sized arrays.

    Raises
    ------
    FileNotFoundError
        If any of the four expected ``.npy`` files is absent.
    """
    files = {
        "X_train": PROCESSED_DIR / "X_train.npy",
        "y_train": PROCESSED_DIR / "y_train.npy",
        "X_test":  PROCESSED_DIR / "X_test.npy",
        "y_test":  PROCESSED_DIR / "y_test.npy",
    }
    for name, path in files.items():
        if not path.exists():
            raise FileNotFoundError(
                f"Missing processed array '{name}' at {path}. "
                "Run src/data_preprocessing.py first."
            )

    logger.info("Loading processed arrays from: %s", PROCESSED_DIR)
    X_train = np.load(files["X_train"])
    y_train = np.load(files["y_train"])
    X_test  = np.load(files["X_test"])
    y_test  = np.load(files["y_test"])

    logger.info(
        "  Loaded -- X_train: %s | X_test: %s | y_train: %s | y_test: %s",
        X_train.shape, X_test.shape, y_train.shape, y_test.shape,
    )
    return X_train, y_train, X_test, y_test


# ---------------------------------------------------------------------------
# Step 2 — Stratified sub-sampling
# ---------------------------------------------------------------------------
def stratified_subsample(
    X: np.ndarray,
    y: np.ndarray,
    sample_size: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """Draw a class-balanced random subset of exactly ``sample_size`` samples.

    Why stratification is mandatory
    --------------------------------
    The NSL-KDD binary training set is mildly imbalanced
    (~53% normal, ~47% attack).  A pure random sub-sample could produce a
    heavily skewed subset purely by chance, especially at small sample sizes.
    Stratified sampling guarantees that the subset preserves the original
    class proportions (within rounding), so the SVM decision boundary is
    trained on a representative slice of the full distribution.

    Implementation
    --------------
    ``train_test_split(..., stratify=y)`` partitions the dataset while
    maintaining per-class fractions.  We request the discard fraction
    (1 - sample_size / len(y)) and keep the smaller split.

    Parameters
    ----------
    X : np.ndarray, shape (N, 4)
        Feature matrix with values in [0, pi].
    y : np.ndarray, shape (N,)
        Binary integer label vector.
    sample_size : int
        Desired number of samples in the returned subset.

    Returns
    -------
    X_sub, y_sub : np.ndarray
        Stratified subset with exactly ``sample_size`` rows.

    Raises
    ------
    ValueError
        If ``sample_size`` >= len(y) (nothing to subsample).
    """
    if sample_size >= len(y):
        raise ValueError(
            f"sample_size ({sample_size}) must be less than the dataset "
            f"size ({len(y)}).  No sub-sampling needed."
        )

    discard_fraction: float = 1.0 - sample_size / len(y)

    # We keep the FIRST split (size = sample_size) and discard the second.
    X_sub, _, y_sub, _ = train_test_split(
        X, y,
        test_size=discard_fraction,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    unique, counts = np.unique(y_sub, return_counts=True)
    class_dist = dict(zip(unique.tolist(), counts.tolist()))
    logger.info(
        "  Stratified subsample: %d samples | class distribution: %s",
        len(y_sub), class_dist,
    )
    return X_sub, y_sub


# ---------------------------------------------------------------------------
# Step 3 — Quantum environment setup
# ---------------------------------------------------------------------------
def build_quantum_kernel() -> FidelityQuantumKernel:
    """Construct the FidelityQuantumKernel backed by the ZZ feature map.

    Circuit architecture (Qiskit 2.x function-based API)
    -----------------------------------------------------
    zz_feature_map(feature_dimension=4, reps=2, entanglement='linear')

    Produces a 4-qubit circuit of the form:
        |0000> --> H^(x4) --> [RZ(2x_i)] --> [RZZ(2(pi-x_i)(pi-x_j))]
                --> H^(x4) --> [RZ(2x_i)] --> [RZZ(2(pi-x_i)(pi-x_j))]

    With 'linear' entanglement the ZZ interactions are only applied to
    nearest-neighbour pairs: (q0,q1), (q1,q2), (q2,q3).
    Circuit depth = 19 (after 1-layer decomposition).

    Kernel computation via ComputeUncompute fidelity
    ------------------------------------------------
    K(x, z) = |<0000| U†(z) U(x) |0000>|^2

    The StatevectorSampler executes the circuit on a noiseless state-vector
    simulator (exact arithmetic, no shot noise), making it the most accurate
    and fastest simulation backend for small qubit counts.

    Returns
    -------
    FidelityQuantumKernel
        A configured kernel object whose ``.evaluate(X, Y)`` method returns
        the Gram matrix K(X, Y) with shape (len(X), len(Y)).
    """
    logger.info(
        "Building ZZFeatureMap: n_qubits=%d | reps=%d | entanglement=%s",
        N_QUBITS, ZZ_REPS, ZZ_ENTANGLEMENT,
    )

    # Use the function-based API (Qiskit >= 2.1; class-based ZZFeatureMap
    # is deprecated in 2.1 and removed in 3.0).
    feature_map = zz_feature_map(
        feature_dimension=N_QUBITS,
        reps=ZZ_REPS,
        entanglement=ZZ_ENTANGLEMENT,
    )

    # StatevectorSampler: noiseless exact statevector simulation.
    # No shots needed -- the result is the true probability amplitude.
    sampler = StatevectorSampler()

    # ComputeUncompute implements the  U†(z)·U(x)  fidelity circuit,
    # measuring the probability of the |0000> outcome after inversion.
    fidelity = ComputeUncompute(sampler=sampler)

    # FidelityQuantumKernel wraps the fidelity into a scikit-learn-compatible
    # callable.  enforce_psd=True (default) clips negative eigenvalues so
    # the kernel matrix is guaranteed positive semi-definite, a necessary
    # condition for the SVC convex QP to be well-posed.
    quantum_kernel = FidelityQuantumKernel(
        feature_map=feature_map,
        fidelity=fidelity,
        enforce_psd=True,
    )

    logger.info(
        "  Hilbert space dimension: 2^%d = %d  |  "
        "circuit depth (1-decompose): %d",
        N_QUBITS,
        2 ** N_QUBITS,
        feature_map.decompose().depth(),
    )
    return quantum_kernel


# ---------------------------------------------------------------------------
# Step 4 helper — Timed kernel matrix pre-computation
# ---------------------------------------------------------------------------
def precompute_kernel_matrices(
    quantum_kernel: FidelityQuantumKernel,
    X_train: np.ndarray,
    X_test: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, float]:
    """Explicitly evaluate the quantum kernel matrices with wall-clock timing.

    Pre-computing the matrices once before fitting avoids redundant circuit
    evaluations: sklearn's SVC with a callable kernel would otherwise recompute
    the kernel during both ``.fit()`` and ``.predict()`` calls.

    Computational complexity
    ------------------------
    - K_train: shape (N_train, N_train).  The matrix is symmetric, so
      FidelityQuantumKernel only evaluates N*(N+1)/2 unique pairs.
      For N=1000: 500,500 unique circuit evaluations.
    - K_test : shape (N_test, N_train).  All N_test * N_train pairs are
      needed for prediction.  For N_test=300: 300,000 evaluations.

    The quantum kernel K(x,z) lies in [0, 1] by construction (it is a
    probability amplitude squared).  K(x,x) = 1 always.

    Parameters
    ----------
    quantum_kernel : FidelityQuantumKernel
        Configured quantum kernel object.
    X_train, X_test : np.ndarray
        Sub-sampled feature matrices.

    Returns
    -------
    K_train : np.ndarray, shape (N_train, N_train)
        Symmetric PSD training Gram matrix.
    K_test : np.ndarray, shape (N_test, N_train)
        Test-vs-train Gram matrix used for SVC prediction.
    elapsed_seconds : float
        Total wall-clock time for both kernel evaluations combined.
    """
    n_train, n_test = len(X_train), len(X_test)
    n_unique_train = n_train * (n_train + 1) // 2
    n_unique_test  = n_test * n_train

    logger.info(
        "Pre-computing quantum kernel matrices ..."
        "\n    K_train: (%d x %d)  ->  %d unique circuit evaluations"
        "\n    K_test:  (%d x %d)  ->  %d circuit evaluations",
        n_train, n_train, n_unique_train,
        n_test,  n_train, n_unique_test,
    )

    t_start = time.perf_counter()

    logger.info("  Evaluating K_train ...")
    K_train = quantum_kernel.evaluate(X_train)

    logger.info("  Evaluating K_test ...")
    K_test = quantum_kernel.evaluate(X_test, X_train)

    elapsed = time.perf_counter() - t_start

    logger.info(
        "  Kernel matrices computed in %.1f s (%.1f min)",
        elapsed, elapsed / 60.0,
    )
    logger.info(
        "  K_train stats: min=%.4f | max=%.4f | mean=%.4f | diag_min=%.4f",
        K_train.min(), K_train.max(), K_train.mean(),
        np.diag(K_train).min(),
    )
    return K_train, K_test, elapsed


# ---------------------------------------------------------------------------
# Step 4 — Model training
# ---------------------------------------------------------------------------
def train_qsvm(
    K_train: np.ndarray,
    y_train: np.ndarray,
) -> SVC:
    """Fit a Quantum SVM on the pre-computed kernel matrix.

    By passing ``kernel='precomputed'`` and supplying the Gram matrix
    directly, we instruct sklearn to skip its internal kernel computation
    and feed K_train straight into the QP solver.  This is the canonical
    way to use any custom (including quantum) kernel with sklearn.

    The SVC dual problem with a precomputed kernel is:
        max_alpha  SUM_i alpha_i
                   - (1/2) SUM_{i,j} alpha_i * alpha_j * y_i * y_j * K(x_i, x_j)
        s.t.  0 <= alpha_i <= C  for all i
              SUM_i alpha_i * y_i = 0

    The quantum kernel K(x_i, x_j) = |<phi(x_i)|phi(x_j)>|^2 replaces the
    classical RBF kernel, implicitly computing dot products in the 16-D
    Hilbert space.  Points that are "quantum similar" (high fidelity) attract
    large alpha_i, becoming support vectors that define the decision boundary
    in Hilbert space.

    ``class_weight='balanced'`` compensates for the mild class imbalance by
    setting C_i proportional to the inverse class frequency:
        C_i = C * (N / (n_classes * N_i))

    Parameters
    ----------
    K_train : np.ndarray, shape (N_train, N_train)
        Precomputed symmetric Gram matrix.
    y_train : np.ndarray, shape (N_train,)
        Binary class labels.

    Returns
    -------
    SVC
        Fitted Quantum SVM classifier.
    """
    logger.info("Training Quantum SVM (kernel='precomputed') ...")
    t0 = time.perf_counter()

    qsvm = SVC(
        kernel="precomputed",
        class_weight="balanced",
        random_state=RANDOM_STATE,
    )
    qsvm.fit(K_train, y_train)

    elapsed = time.perf_counter() - t0
    logger.info(
        "  QSVM trained in %.2f s  |  support vectors: %d / %d (%.1f%%)",
        elapsed,
        qsvm.support_vectors_.shape[0],
        len(y_train),
        100.0 * qsvm.support_vectors_.shape[0] / len(y_train),
    )
    return qsvm


def train_classical_svm(
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> SVC:
    """Fit a classical RBF-kernel SVM as a performance baseline.

    The RBF kernel K_rbf(x, z) = exp(-gamma * ||x - z||^2) operates in an
    infinite-dimensional RKHS.  It serves as the most competitive classical
    baseline because:
    - It is translation-invariant (like the ZZ quantum kernel).
    - It is non-parametric and makes no distributional assumptions.
    - With class_weight='balanced' it handles the same imbalance correction.

    Comparing QSVM vs CSVM on identical sub-sampled data isolates the
    contribution of the quantum feature map from the SVM machinery itself.

    Parameters
    ----------
    X_train : np.ndarray, shape (N_train, 4)
        Raw feature vectors (not a kernel matrix).
    y_train : np.ndarray, shape (N_train,)
        Binary class labels.

    Returns
    -------
    SVC
        Fitted Classical SVM classifier.
    """
    logger.info("Training Classical RBF-SVM (baseline) ...")
    t0 = time.perf_counter()

    csvm = SVC(
        kernel="rbf",
        class_weight="balanced",
        random_state=RANDOM_STATE,
    )
    csvm.fit(X_train, y_train)

    elapsed = time.perf_counter() - t0
    logger.info(
        "  Classical SVM trained in %.2f s  |  support vectors: %d / %d (%.1f%%)",
        elapsed,
        csvm.support_vectors_.shape[0],
        len(y_train),
        100.0 * csvm.support_vectors_.shape[0] / len(y_train),
    )
    return csvm


# ---------------------------------------------------------------------------
# Step 5 — Evaluation and reporting
# ---------------------------------------------------------------------------
def evaluate_model(
    model: SVC,
    X_or_K: np.ndarray,
    y_true: np.ndarray,
    model_name: str,
) -> dict[str, float]:
    """Compute and return all four classification metrics for a fitted SVC.

    Parameters
    ----------
    model : SVC
        Any fitted SVC instance (precomputed or callable kernel).
    X_or_K : np.ndarray
        For classical SVM: the raw feature matrix X_test.
        For quantum SVM: the precomputed kernel matrix K_test (N_test x N_train).
    y_true : np.ndarray
        Ground-truth binary labels.
    model_name : str
        Label used only for logging.

    Returns
    -------
    dict[str, float]
        Dictionary with keys: accuracy, precision, recall, f1.
    """
    y_pred = model.predict(X_or_K)

    metrics = {
        "accuracy":  accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall":    recall_score(y_true, y_pred, zero_division=0),
        "f1":        f1_score(y_true, y_pred, zero_division=0),
    }
    logger.info(
        "  %s -- Acc: %.4f | Prec: %.4f | Rec: %.4f | F1: %.4f",
        model_name,
        metrics["accuracy"], metrics["precision"],
        metrics["recall"], metrics["f1"],
    )
    return metrics


def print_report(
    qsvm_metrics: dict[str, float],
    csvm_metrics: dict[str, float],
    kernel_time_seconds: float,
    n_train: int,
    n_test: int,
) -> None:
    """Print a clean, aligned evaluation report to stdout.

    Parameters
    ----------
    qsvm_metrics, csvm_metrics : dict[str, float]
        Metric dictionaries returned by ``evaluate_model``.
    kernel_time_seconds : float
        Wall-clock time in seconds for quantum kernel matrix computation.
    n_train, n_test : int
        Sub-sampled sizes used for training and evaluation.
    """
    sep = "=" * 68
    inner_sep = "-" * 68

    report_lines = [
        "",
        sep,
        "  NSL-KDD QSVM vs Classical SVM -- Evaluation Report",
        sep,
        f"  Dataset     : NSL-KDD (binary intrusion detection)",
        f"  Train size  : {n_train} samples (stratified subsample)",
        f"  Test size   : {n_test} samples (stratified subsample)",
        f"  Kernel dim  : 2^{N_QUBITS} = {2**N_QUBITS}-D Hilbert space (ZZFeatureMap, reps={ZZ_REPS})",
        f"  Kernel time : {kernel_time_seconds:.1f} s ({kernel_time_seconds/60:.1f} min)",
        inner_sep,
        f"  {'Metric':<14}  {'Classical SVM':>16}  {'Quantum SVM':>16}",
        inner_sep,
        f"  {'Accuracy':<14}  {csvm_metrics['accuracy']:>16.4f}  {qsvm_metrics['accuracy']:>16.4f}",
        f"  {'Precision':<14}  {csvm_metrics['precision']:>16.4f}  {qsvm_metrics['precision']:>16.4f}",
        f"  {'Recall':<14}  {csvm_metrics['recall']:>16.4f}  {qsvm_metrics['recall']:>16.4f}",
        f"  {'F1-Score':<14}  {csvm_metrics['f1']:>16.4f}  {qsvm_metrics['f1']:>16.4f}",
        inner_sep,
        "  NOTE: QSVM operates in a 16-D quantum Hilbert space.",
        "  Kernel K(x,z) = |<phi(x)|phi(z)>|^2 (state fidelity).",
        "  Classical SVM uses RBF kernel for fair comparison.",
        sep,
        "",
    ]
    print("\n".join(report_lines))


# ---------------------------------------------------------------------------
# Step 5 — Model persistence
# ---------------------------------------------------------------------------
def save_models(qsvm: SVC, csvm: SVC) -> None:
    """Serialise both fitted SVC instances to ``models/`` via joblib.

    joblib is preferred over pickle for sklearn estimators because it uses
    memory-mapped numpy arrays for large attribute tensors (e.g. the support
    vector matrix), resulting in faster serialisation and smaller files.

    Parameters
    ----------
    qsvm : SVC
        Fitted Quantum SVM (kernel='precomputed').
    csvm : SVC
        Fitted Classical SVM (kernel='rbf').
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    paths = {
        "qsvm_model.pkl": qsvm,
        "csvm_model.pkl": csvm,
    }
    for filename, model in paths.items():
        path = MODELS_DIR / filename
        joblib.dump(model, path)
        logger.info("  Saved model -> %s", path)


# ---------------------------------------------------------------------------
# Master pipeline
# ---------------------------------------------------------------------------
def run_pipeline() -> None:
    """Execute the full Phase 2 training pipeline end-to-end.

    Pipeline order
    --------------
    1. Load processed ``.npy`` arrays.
    2. Stratified sub-sample: train -> 1000, test -> 300.
    3. Build the ZZFeatureMap + ComputeUncompute + FidelityQuantumKernel.
    4. Pre-compute quantum Gram matrices (with timing).
    5. Train QSVM on precomputed kernel + Classical SVM on raw features.
    6. Evaluate both models; print formatted report.
    7. Save both fitted SVC objects to ``models/``.
    """
    logger.info("=" * 68)
    logger.info("NSL-KDD QSVM Training Pipeline -- START")
    logger.info("=" * 68)

    # ------------------------------------------------------------------
    # 1. Load data
    # ------------------------------------------------------------------
    X_train_full, y_train_full, X_test_full, y_test_full = load_processed_data()

    # ------------------------------------------------------------------
    # 2. Stratified sub-sampling (O(N^2) bottleneck mitigation)
    # ------------------------------------------------------------------
    logger.info(
        "Stratified sub-sampling: train %d -> %d | test %d -> %d",
        len(y_train_full), N_TRAIN_SUBSAMPLE,
        len(y_test_full),  N_TEST_SUBSAMPLE,
    )

    X_train, y_train = stratified_subsample(
        X_train_full, y_train_full, N_TRAIN_SUBSAMPLE
    )
    X_test, y_test = stratified_subsample(
        X_test_full, y_test_full, N_TEST_SUBSAMPLE
    )

    # Cast to float64 for sklearn / qiskit compatibility (input was float32).
    X_train = X_train.astype(np.float64)
    X_test  = X_test.astype(np.float64)

    # ------------------------------------------------------------------
    # 3. Quantum kernel setup
    # ------------------------------------------------------------------
    quantum_kernel = build_quantum_kernel()

    # ------------------------------------------------------------------
    # 4. Pre-compute kernel matrices (with wall-clock timing)
    # ------------------------------------------------------------------
    K_train, K_test, kernel_time = precompute_kernel_matrices(
        quantum_kernel, X_train, X_test
    )

    # ------------------------------------------------------------------
    # 5. Train both models
    # ------------------------------------------------------------------
    qsvm = train_qsvm(K_train, y_train)
    csvm = train_classical_svm(X_train, y_train)

    # ------------------------------------------------------------------
    # 6. Evaluate
    # ------------------------------------------------------------------
    logger.info("Evaluating on sub-sampled test set (%d samples) ...", len(y_test))

    # QSVM prediction uses the precomputed K_test (shape: N_test x N_train)
    qsvm_metrics = evaluate_model(qsvm, K_test, y_test, "Quantum SVM")
    # Classical SVM prediction uses raw feature vectors
    csvm_metrics = evaluate_model(csvm, X_test,  y_test, "Classical SVM")

    print_report(
        qsvm_metrics, csvm_metrics,
        kernel_time_seconds=kernel_time,
        n_train=len(y_train),
        n_test=len(y_test),
    )

    # ------------------------------------------------------------------
    # 7. Save models
    # ------------------------------------------------------------------
    logger.info("Saving fitted models to: %s", MODELS_DIR)
    save_models(qsvm, csvm)

    logger.info("=" * 68)
    logger.info("NSL-KDD QSVM Training Pipeline -- COMPLETE")
    logger.info("=" * 68)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_pipeline()
