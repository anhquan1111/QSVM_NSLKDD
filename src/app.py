"""
app.py
======
Phase 4 -- NIDS Quantum-Enhanced Monitoring System (QEMS)

A Streamlit-based cybersecurity dashboard for real-time network intrusion
detection using a Quantum SVM (QSVM) trained on the NSL-KDD dataset.

Architecture overview
---------------------
The app is split into four concern layers:

1. Resource layer  -- @st.cache_resource  load_environment()
   Loads all heavy objects exactly once per process lifetime:
   - Full X_train.npy / y_train.npy arrays (125k samples)
   - The exact 1000-sample training subsample used in Phase 2
   - A reconstructed FidelityQuantumKernel (stateless; safe to rebuild)
   - Pre-trained QSVM and CSVM model objects loaded from disk

2. Inference layer -- predict_single() / predict_batch()
   Handles the precomputed-kernel contract for the QSVM:
   - Maps a raw (1, 4) feature vector to a (1, 1000) kernel row vector
   - Passes that row vector to qsvm.predict() / qsvm.decision_function()
   See inline comments for the full mathematical explanation.

3. UI layer -- sidebar, header, KPI row, streaming monitor
   Streamlit widgets, CSS injection, and the real-time loop.

4. PoC IBM Quantum stub
   Since qiskit_ibm_runtime is not installed in this environment, the
   IBM Cloud option is implemented as a truthful Proof-of-Concept that:
   - Shows what the connection interface would look like
   - Explains what would change at the circuit-submission level
   - Gracefully falls back to the local StatevectorSampler with a clear
     disclaimer so the demo remains functional without real credentials.
"""

from __future__ import annotations

import time
import warnings
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
import streamlit as st
from qiskit.circuit.library import zz_feature_map
from qiskit.primitives import StatevectorSampler
from qiskit_machine_learning.kernels import FidelityQuantumKernel
from qiskit_machine_learning.state_fidelities import ComputeUncompute
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import SVC

# Suppress Qiskit deprecation noise in the Streamlit log output.
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent
_MODELS_DIR = _ROOT / "models"
_PROCESSED_DIR = _ROOT / "data" / "processed"

# The EXACT hyper-parameters used in Phase 2 training -- MUST NOT change.
_N_TRAIN_SUB: int = 2500          # <-- SỬA thành 2500
_N_QUBITS: int = 4
_ZZ_REPS: int = 3                 # <-- SỬA thành 3
_ZZ_ENTANGLEMENT: str = "full"    # <-- SỬA thành "full"
_RANDOM_STATE: int = 42

# Number of test samples to stream in the monitoring demo.
_N_STREAM: int = 10  # Reduced to 10 packets to accommodate larger precomputed quantum kernel  # <-- SỬA thành 10 và update comment

# ---------------------------------------------------------------------------
# 1. PAGE CONFIGURATION (must be the very first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="NIDS QEMS",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# 2. CUSTOM CSS -- cybersecurity dark-terminal aesthetic
#    Injects styles on top of the .streamlit/config.toml base theme.
# ---------------------------------------------------------------------------
_CSS = """
<style>
/* ── Main background gradient ── */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(160deg, #050b14 0%, #0a1628 60%, #0d1f35 100%);
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #07101d 0%, #0a1a2e 100%);
    border-right: 1px solid #1a3a5c;
}

/* ── Title styling ── */
h1 { color: #00d4ff !important; letter-spacing: 2px; }
h2 { color: #a0c8e8 !important; }
h3 { color: #7ab3d4 !important; }

/* ── Sidebar label ── */
[data-testid="stSidebar"] label { color: #8ab4d4 !important; }

/* ── Metric boxes ── */
[data-testid="metric-container"] {
    background: rgba(0, 212, 255, 0.06);
    border: 1px solid rgba(0, 212, 255, 0.25);
    border-radius: 8px;
    padding: 12px 16px;
}
[data-testid="stMetricValue"] { color: #00d4ff !important; font-size: 2rem !important; }
[data-testid="stMetricLabel"] { color: #7ab3d4 !important; }

/* ── Attack alert (st.error) ── */
[data-testid="stNotification"][data-type="error"] {
    background: rgba(255, 40, 40, 0.12) !important;
    border-left: 4px solid #ff2828 !important;
    color: #ffaaaa !important;
}
/* ── Normal traffic alert (st.success) ── */
[data-testid="stNotification"][data-type="success"] {
    background: rgba(0, 220, 120, 0.10) !important;
    border-left: 4px solid #00dc78 !important;
    color: #aaffcc !important;
}

/* ── Button ── */
[data-testid="stButton"] > button {
    background: linear-gradient(90deg, #003d5c, #005a8a);
    color: #00d4ff;
    border: 1px solid #00d4ff;
    border-radius: 6px;
    font-weight: 700;
    letter-spacing: 1px;
    transition: all 0.2s;
}
[data-testid="stButton"] > button:hover {
    background: linear-gradient(90deg, #005a8a, #007ab0);
    box-shadow: 0 0 12px rgba(0, 212, 255, 0.5);
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border: 1px solid #1a3a5c; border-radius: 6px; }

/* ── Divider ── */
hr { border-color: #1a3a5c !important; }

/* ── Code / monospace blocks ── */
code { color: #00d4ff !important; background: rgba(0,212,255,0.08) !important; }
</style>
"""
st.markdown(_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 3. RESOURCE LAYER  (@st.cache_resource)
#    Loaded ONCE per Streamlit process; shared across all sessions/reruns.
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading QEMS environment... (one-time setup)")
def load_environment() -> dict:
    """Load all heavy assets and return them in a single cached dict.

    Why @st.cache_resource instead of @st.cache_data?
    --------------------------------------------------
    @st.cache_data serialises return values (pickle round-trip on each
    cache hit).  Sklearn SVC objects, Qiskit QuantumCircuit objects, and
    NumPy arrays are safe to share by reference across Streamlit reruns
    because none of them is mutated during inference.  @st.cache_resource
    stores the Python objects in-memory and returns the SAME reference each
    time -- no serialisation overhead and no deepcopy of large arrays.

    Critical: exact 1000-sample subsample reconstruction
    ---------------------------------------------------
    The QSVM was trained using kernel='precomputed'.  sklearn's SVC in this
    mode stores support vector INDICES (self.support_) that index into the
    training matrix that was passed to fit().  During inference, predict()
    expects a matrix of shape (N_test, N_train_orig) = (N_test, 1000).
    Column j of that matrix must contain K(x_test, x_train_j) where
    x_train_j is the EXACT same j-th training sample used during fit().

    If we used even slightly different training samples, self.support_ would
    reference wrong rows in the kernel matrix, producing silent wrong-answer
    bugs.  We prevent this by reconstructing the subsample with
    train_test_split(train_size=1000, stratify=y, random_state=42) --
    the same call used in train_qsvm.py -- which is fully deterministic.

    Returns
    -------
    dict with keys:
        X_train_sub   : np.ndarray (1000, 4)  -- exact Phase 2 training rows
        y_train_sub   : np.ndarray (1000,)    -- corresponding labels
        X_test_full   : np.ndarray (22544, 4) -- full test set for sampling
        y_test_full   : np.ndarray (22544,)   -- full test labels
        quantum_kernel: FidelityQuantumKernel
        qsvm          : SVC (kernel='precomputed')
        csvm          : SVC (kernel='rbf')
        scaler        : MinMaxScaler          -- fitted to Phase 1 training data
        selector      : SelectKBest           -- fitted SelectKBest(f_classif, k=15)
        pca           : PCA                   -- fitted PCA(n_components=4)
    """
    # ---- Load full arrays ----
    X_train_full = np.load(_PROCESSED_DIR / "X_train.npy").astype(np.float64)
    y_train_full = np.load(_PROCESSED_DIR / "y_train.npy")
    X_test_full = np.load(_PROCESSED_DIR / "X_test.npy").astype(np.float64)
    y_test_full = np.load(_PROCESSED_DIR / "y_test.npy")

    # ---- Reconstruct exact Phase 2 training subsample ----
    # train_size=1000 is equivalent to test_size=(1-1000/N) and produces
    # the byte-identical split (verified: np.allclose = True in both calls).
    X_train_sub, _, y_train_sub, _ = train_test_split(
        X_train_full, y_train_full,
        train_size=_N_TRAIN_SUB,
        stratify=y_train_full,
        random_state=_RANDOM_STATE,
    )

    # ---- Rebuild quantum kernel (stateless; no parameters to restore) ----
    # FidelityQuantumKernel wraps a live Qiskit circuit.  These objects hold
    # multiprocessing locks and are not reliably pickle-able across sessions,
    # so we always rebuild from the fixed hyper-parameters rather than
    # serialising.  Since K(x,z) is a pure function of x, z and the fixed
    # feature map, rebuilding gives identical numerical results.
    feature_map = zz_feature_map(
        feature_dimension=_N_QUBITS,
        reps=_ZZ_REPS,
        entanglement=_ZZ_ENTANGLEMENT,
    )
    sampler = StatevectorSampler()
    fidelity = ComputeUncompute(sampler=sampler)
    quantum_kernel = FidelityQuantumKernel(
        feature_map=feature_map,
        fidelity=fidelity,
        enforce_psd=True,
    )

# ---- 1. Đảm bảo thư mục tồn tại trên Cloud ----
    _MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # ---- 2. Tự động tải Models và Transformers (Chỉ tải nếu CHƯA CÓ) ----
    import gdown
    import streamlit as st
    
    drive_files = {
        "qsvm_model.pkl":          "1i7oHcLcWoaYZFhmENmgQeKtw14-l8vV4",
        "csvm_model.pkl":          "1JalfCdNkcaiawxn3_63hzQNCpDgMT5AX",
        "scaler_minmax_pi.joblib": "1VdVci6owFOXmfO-NNFswmyHv28KUPCuL",
        "feature_selector.joblib": "133cy71t2qrAM24nWHvVzSIGr-B0a-jd6",
        "pca_4components.joblib":  "1indGQgR1Qin6upnceciqJWMQ1Im4nHvE"
    }

    for filename, file_id in drive_files.items():
        file_path = _MODELS_DIR / filename
        # Nếu file CHƯA CÓ mặt trên ổ cứng, thì mới tải từ Drive
        if not file_path.exists():
            with st.spinner(f'Đang tải {filename} từ Google Drive...'):
                gdown.download(id=file_id, output=str(file_path), quiet=False)

    # ---- 3. Load 5 file vào bộ nhớ ----
    qsvm: SVC = joblib.load(_MODELS_DIR / "qsvm_model.pkl")
    csvm: SVC = joblib.load(_MODELS_DIR / "csvm_model.pkl")
    
    scaler:   MinMaxScaler = joblib.load(_MODELS_DIR / "scaler_minmax_pi.joblib")
    selector: SelectKBest  = joblib.load(_MODELS_DIR / "feature_selector.joblib")
    pca:      PCA          = joblib.load(_MODELS_DIR / "pca_4components.joblib")
    return {
        "X_train_sub":    X_train_sub,
        "y_train_sub":    y_train_sub,
        "X_test_full":    X_test_full,
        "y_test_full":    y_test_full,
        "quantum_kernel": quantum_kernel,
        "qsvm":           qsvm,
        "csvm":           csvm,
        "scaler":         scaler,
        "selector":       selector,
        "pca":            pca,
    }


# ---------------------------------------------------------------------------
# 4. INFERENCE LAYER
# ---------------------------------------------------------------------------
def apply_preprocessing_pipeline(
    x_ohe: np.ndarray,
    env: dict,
) -> np.ndarray:
    """Apply the Hybrid Feature Selection pipeline to a raw post-OHE feature vector.

    Use this function to process a live/raw packet (after One-Hot Encoding) before
    passing it to the QSVM or CSVM for inference.  The test data loaded from
    ``X_test.npy`` is already fully processed through this pipeline by
    ``data_preprocessing.py``; call this function only when consuming raw feature
    vectors that have NOT yet been preprocessed.

    Transformation sequence
    -----------------------
    The pipeline sequence MUST be followed exactly to match the training state:

        x_ohe  (N, ~122)
            │
            │  Step 1 — MinMaxScaler [0, π]
            ▼  env["scaler"].transform(x_ohe)
        x_scaled  (N, ~122)
            │
            │  Step 2 — SelectKBest(f_classif, k=15)   ← inserted before PCA
            ▼  env["selector"].transform(x_scaled)
        x_selected  (N, 15)
            │
            │  Step 3 — PCA(n_components=4)
            ▼  env["pca"].transform(x_selected)
        x_pca  (N, 4)   →  QSVM / CSVM predict()

    Zero-leakage guarantee
    ----------------------
    All three transformers were fitted exclusively on the Phase 1 training set.
    ``transform()`` (not ``fit_transform()``) is called here, so no statistics
    are re-learned from the incoming packets — the same contract as the test set
    in data_preprocessing.py.

    Parameters
    ----------
    x_ohe : np.ndarray, shape (N, n_ohe_features)
        Raw feature matrix after One-Hot Encoding, NOT yet scaled or selected.
    env : dict
        The dict returned by load_environment().

    Returns
    -------
    np.ndarray, shape (N, 4)
        Feature matrix ready for QSVM / CSVM inference.
    """
    x_ohe      = np.atleast_2d(x_ohe).astype(np.float64)

    # Step 1: scale raw OHE features to quantum rotation-angle range [0, π].
    x_scaled   = env["scaler"].transform(x_ohe)

    # Step 2: retain top-15 features by ANOVA F-score (SelectKBest, k=15).
    #         This step MUST precede PCA to match the Phase 1 pipeline order.
    x_selected = env["selector"].transform(x_scaled)   # (N, 15)

    # Step 3: compress 15-D selected features to 4 PCA components.
    #         Each component becomes one qubit rotation angle θ_i ∈ [0, π].
    x_pca      = env["pca"].transform(x_selected)      # (N, 4)

    return x_pca


def predict_single(
    x_new: np.ndarray,
    model_choice: str,
    env: dict,
) -> Tuple[int, float]:
    """Classify a single network packet and return (prediction, decision_score).

    Parameters
    ----------
    x_new : np.ndarray, shape (4,) or (1, 4)
        A single pre-processed feature vector with values in [0, pi].
    model_choice : str
        "Quantum SVM" or "Classical SVM".
    env : dict
        The dict returned by load_environment().

    Returns
    -------
    pred : int
        0 = normal, 1 = attack.
    score : float
        Signed distance from the SVM decision hyperplane.
        Positive -> attack, negative -> normal.

    Quantum Kernel Vector Transformation (1 x 1000)
    ------------------------------------------------
    The QSVM was trained with kernel='precomputed'.  sklearn never stores the
    support vectors themselves; it stores their INDICES (self.support_) into
    the ORIGINAL training matrix.  At inference time, predict() must receive a
    precomputed kernel matrix where:

        K_test[i, j] = K(x_test_i, x_train_j)
                     = |<phi(x_test_i)|phi(x_train_j)>|^2

    For a SINGLE test sample, this means we need a ROW VECTOR of shape (1, 1000)
    containing the quantum fidelity between the test point and each of the 1000
    training points.

    Step-by-step:
        x_new  : (1, 4)   -- the raw 4-dimensional feature vector
            |
            v  quantum_kernel.evaluate(x_vec=x_new, y_vec=X_train_sub)
            |  Internally: for each j in 0..999, compute
            |      K[0,j] = |<0000| U†(X_train_sub[j]) U(x_new) |0000>|^2
            |  via the ComputeUncompute circuit with StatevectorSampler
            v
        k_vec  : (1, 1000) -- the kernel similarity row vector
            |
            v  qsvm.predict(k_vec)
            |  Computes f(x_new) = SUM_{j in SVs} alpha_j*y_j*K[0,j] + b
            |  Returns sign(f(x_new)) as the class label {0, 1}
            v
        pred   : (1,)

    The 1000 evaluations take ~14 seconds on the local StatevectorSampler.
    For batch streaming, use predict_batch() which computes all rows at once.
    """
    x_new = np.atleast_2d(x_new).astype(np.float64)  # ensure shape (1, 4)

    if model_choice == "Quantum SVM":
        # Build the (1, 1000) kernel similarity row vector.
        # evaluate(x_vec, y_vec) returns K of shape (len(x_vec), len(y_vec)).
        k_vec = env["quantum_kernel"].evaluate(
            x_vec=x_new,
            y_vec=env["X_train_sub"],
        )  # shape: (1, 1000)
        pred: int = int(env["qsvm"].predict(k_vec)[0])
        score: float = float(env["qsvm"].decision_function(k_vec)[0])
    else:
        # Classical SVM: predict directly from raw 4-D feature vector.
        pred = int(env["csvm"].predict(x_new)[0])
        score = float(env["csvm"].decision_function(x_new)[0])

    return pred, score


def predict_batch(
    X_batch: np.ndarray,
    model_choice: str,
    env: dict,
    progress_callback=None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Classify a batch of samples.  For QSVM, pre-computes the full kernel
    matrix in a single call to minimise circuit compilation overhead.

    Parameters
    ----------
    X_batch : np.ndarray, shape (N, 4)
    model_choice : str
    env : dict
    progress_callback : callable or None
        If provided, called with a float in [0, 1] after kernel computation.

    Returns
    -------
    preds  : np.ndarray (N,)  -- class labels
    scores : np.ndarray (N,)  -- decision function values
    K_batch: np.ndarray (N, 1000) or None
        The quantum kernel matrix (QSVM only), returned so callers can inspect
        individual kernel rows during streaming without recomputing.
    """
    if model_choice == "Quantum SVM":
        # ----------------------------------------------------------------
        # Batch kernel computation: K_batch shape = (N_batch, 1000)
        #
        # This is the ONLY efficient way to run N_batch QSVM inferences:
        # calling predict_single() N times would compile the ZZ circuit
        # N times independently.  evaluate(X_batch, X_train) compiles once
        # and schedules all N * 1000 fidelity circuits together.
        #
        # FidelityQuantumKernel.evaluate(x_vec, y_vec):
        #   Returns K of shape (len(x_vec), len(y_vec))
        #   K[i, j] = |<phi(X_batch[i])|phi(X_train_sub[j])>|^2
        # ----------------------------------------------------------------
        K_batch = env["quantum_kernel"].evaluate(
            x_vec=X_batch,
            y_vec=env["X_train_sub"],
        )  # shape: (N_batch, 1000)

        if progress_callback is not None:
            progress_callback(1.0)

        preds = env["qsvm"].predict(K_batch).astype(int)
        scores = env["qsvm"].decision_function(K_batch)
        return preds, scores, K_batch
    else:
        preds = env["csvm"].predict(X_batch).astype(int)
        scores = env["csvm"].decision_function(X_batch)
        return preds, scores, None


# ---------------------------------------------------------------------------
# 5. SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🛡️ QEMS Control Panel")
    st.divider()

    st.markdown("### Model Selection")
    model_choice: str = st.radio(
        label="Active Inference Engine",
        options=["Quantum SVM", "Classical SVM"],
        index=0,
        help=(
            "**Quantum SVM**: Uses the ZZFeatureMap quantum kernel. "
            "Each inference maps the input to a 16-D Hilbert space "
            "(2^4 qubits) via quantum circuit fidelity. "
            "High accuracy, high latency on classical simulators.\n\n"
            "**Classical SVM**: Uses the RBF (Gaussian) kernel. "
            "Near-instant inference; serves as performance baseline."
        ),
    )

    st.divider()

    st.markdown("### Execution Backend")
    backend_choice: str = st.radio(
        label="Quantum Backend",
        options=["Local Simulator (Statevector)", "IBM Quantum Cloud (PoC)"],
        index=0,
    )

    if backend_choice == "IBM Quantum Cloud (PoC)":
        st.warning(
            "**⚠️ Proof of Concept Notice**\n\n"
            "IBM Quantum Cloud integration requires the "
            "`qiskit_ibm_runtime` package and valid IBM Quantum "
            "credentials.  This is not installed in the current "
            "environment.\n\n"
            "Queue delays of **minutes to hours** are typical on "
            "shared QPUs.  The system will simulate IBM-style job "
            "submission but execute locally.",
            icon="🔬",
        )
        ibm_token = st.text_input(
            "IBM Quantum API Token (optional)",
            type="password",
            placeholder="Paste token for real QPU submission",
            help="Leave blank to run in local-fallback PoC mode.",
        )
    else:
        ibm_token = ""

    st.divider()

    # ---- Runtime status indicators ----
    st.markdown("### System Status")

    # Load environment here so we can show live status in the sidebar.
    try:
        env = load_environment()
        _env_ok = True
    except Exception as _e:
        _env_ok = False
        _env_error = str(_e)

    if _env_ok:
        st.success("✅ Models loaded", icon="🤖")
        st.success("✅ Quantum kernel ready", icon="⚛️")
        st.caption(
            f"Training support vectors: **{env['X_train_sub'].shape[0]}**  \n"
            f"Hilbert space: **C^{2**_N_QUBITS}** ({_N_QUBITS} qubits)  \n"
            f"Feature map depth: **{env['quantum_kernel']._feature_map.decompose().depth()}**"
        )
    else:
        st.error(f"❌ Load failed: {_env_error}")

    st.divider()
    st.caption(
        "NSL-KDD | ZZFeatureMap reps=2 | SelectKBest k=15 → PCA→4D  \n"
        "Preprocessing → Training → Evaluation → **App**"
    )

# ---------------------------------------------------------------------------
# 6. HEADER
# ---------------------------------------------------------------------------
st.markdown(
    "<h1 style='text-align:center; margin-bottom:4px;'>🛡️ NIDS "
    "Quantum-Enhanced Monitoring System</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center; color:#5a8ab0; font-size:0.9rem; "
    "margin-top:0; letter-spacing:1px;'>"
    "NSL-KDD · ZZFeatureMap · 4 Qubits · 16-D Hilbert Space · "
    "Binary Intrusion Classification</p>",
    unsafe_allow_html=True,
)
st.divider()

# ---- KPI / Static metrics row ----
if _env_ok:
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Active Model",    model_choice.split()[0])
    kpi2.metric("Backend",         "Local" if "Local" in backend_choice else "IBM PoC")
    kpi3.metric("Training Set Size", f"{env['X_train_sub'].shape[0]}")
# Hoặc nếu muốn chuyên nghiệp hơn, hiện cả hai:
# kpi3.metric("Train Size (SVs)", f"{env['X_train_sub'].shape[0]} ({env['qsvm'].support_.shape[0]})")
    kpi4.metric("Feature Dimensions",  str(_N_QUBITS))
    kpi5.metric("Hilbert Space Dim",   str(2 ** _N_QUBITS))
    st.divider()

# ---------------------------------------------------------------------------
# 7. REAL-TIME MONITORING SECTION
# ---------------------------------------------------------------------------
st.markdown("## 📡 Real-Time Network Traffic Monitor")
st.markdown(
    f"Streams **{_N_STREAM} randomly selected** packets from the NSL-KDD "
    f"test set (`{env['X_test_full'].shape[0]:,}` total samples).  "
    "Each packet is classified in order to simulate live NIDS operation."
    if _env_ok else ""
)

# ---- Model info expander ----
if _env_ok:
    with st.expander("ℹ️ Inference pipeline detail", expanded=False):
        if model_choice == "Quantum SVM":
            st.markdown(
                f"""
**Full Hybrid Inference Path (raw packet → label)**

```
x_raw_ohe (~122-D)
    → scaler.transform()      MinMaxScaler [0, π]        (~122-D)
    → selector.transform()    SelectKBest(f_classif, k=15)  (15-D)
    → pca.transform()         PCA(n_components=4)            (4-D)
    → quantum_kernel.evaluate(x_pca, X_train_1000)
    → K_row (1, 1000)         [quantum fidelity similarities]
    → qsvm.predict(K_row)
    → label ∈ {{0, 1}}
```

The `(1, 1000)` kernel row `K_row[0, j] = |⟨φ(x_new)|φ(x_train_j)⟩|²`
quantifies how "quantum-similar" the test packet is to each of the 1000
support-vector candidates.  The SVM decision function then computes:

&nbsp;&nbsp;&nbsp;&nbsp;`f(x) = Σ αⱼ yⱼ K_row[0,j] + b`  (sum over support vectors j)

A **batch of {_N_STREAM} packets** is pre-computed as a single
`({_N_STREAM}, 1000)` matrix before streaming starts, avoiding repeated
circuit compilation overhead.  The test packets in this demo are already
preprocessed through the Hybrid pipeline by `data_preprocessing.py`.
                """
            )
        else:
            st.markdown(
                f"""
**Full Hybrid Inference Path (raw packet → label)**

```
x_raw_ohe (~122-D)
    → scaler.transform()      MinMaxScaler [0, π]        (~122-D)
    → selector.transform()    SelectKBest(f_classif, k=15)  (15-D)
    → pca.transform()         PCA(n_components=4)            (4-D)
    → csvm.predict(x_pca)
    → label ∈ {{0, 1}}
```

The RBF kernel `K(x,z) = exp(−γ ‖x−z‖²)` is computed in O(N_sv × D)
per sample against stored support vectors.  Near-instantaneous on CPU.
The test packets in this demo are already preprocessed through the
Hybrid pipeline by `data_preprocessing.py`.
                """
            )

# ---- IBM PoC pre-flight info ----
if backend_choice == "IBM Quantum Cloud (PoC)" and _env_ok:
    with st.expander("🔬 IBM Quantum PoC — Connection Details", expanded=False):
        st.markdown(
            """
**What would change with real IBM Quantum credentials:**

1. Replace `StatevectorSampler` with `qiskit_ibm_runtime.SamplerV2`  
   connected to a real QPU backend (e.g. `ibm_sherbrooke`, 127 qubits).

2. Job submission would look like:
```python
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
service = QiskitRuntimeService(token="<YOUR_TOKEN>")
backend = service.least_busy(min_num_qubits=4)
sampler  = SamplerV2(backend=backend)
fidelity = ComputeUncompute(sampler=sampler)
quantum_kernel = FidelityQuantumKernel(feature_map=fm, fidelity=fidelity)
```

3. Each circuit evaluation submits a **transpiled ZZ circuit** to the QPU.
   Expected queue delay: 1 – 60 minutes depending on backend load.
   Shot noise would be present (default 4096 shots per circuit).

**Current status:** `qiskit_ibm_runtime` not installed — running on  
local `StatevectorSampler` (exact, noise-free) with IBM-style log output.
            """
        )

# ---------------------------------------------------------------------------
# 8. STREAMING MONITOR BUTTON & LOOP
# ---------------------------------------------------------------------------
col_btn, col_info = st.columns([1, 3])
with col_btn:
    start_monitoring = st.button(
        "▶  Start Real-time Monitoring",
        use_container_width=True,
        disabled=not _env_ok,
    )
with col_info:
    if model_choice == "Quantum SVM":
        st.info(
            f"QSVM mode: **{_N_STREAM} × 1000 = {_N_STREAM * 1000:,}** "
            "circuit evaluations will be pre-computed before streaming begins.  "
            "Estimated wait: **~5 min** on local simulator.",
            icon="⚛️",
        )
    else:
        st.info(
            "Classical SVM mode: inference is instantaneous — "
            "each packet is classified in real time with no pre-computation.",
            icon="💡",
        )

# ---- Main streaming loop ----
if start_monitoring and _env_ok:

    # ------------------------------------------------------------------
    # A. Sample _N_STREAM packets from the test set
    # ------------------------------------------------------------------
    rng = np.random.default_rng(seed=int(time.time()) % (2**31))
    indices = rng.choice(len(env["y_test_full"]), size=_N_STREAM, replace=False)
    X_stream = env["X_test_full"][indices]   # shape (_N_STREAM, 4)
    y_stream = env["y_test_full"][indices]   # shape (_N_STREAM,)
    # Note: X_stream samples are already processed through the Hybrid pipeline:
    #   scaler.transform()    → MinMaxScaler [0, π]
    #   selector.transform()  → SelectKBest(f_classif, k=15)   ← inserted before PCA
    #   pca.transform()       → PCA(n_components=4)
    # For raw incoming packets, use apply_preprocessing_pipeline(x_ohe, env) first.

    # ------------------------------------------------------------------
    # B. Pre-compute kernel matrix (QSVM) or skip (CSVM)
    # ------------------------------------------------------------------
    K_batch: np.ndarray | None = None

    if model_choice == "Quantum SVM":
        _ibm_label = (
            "IBM Quantum Cloud (PoC — local fallback)"
            if backend_choice == "IBM Quantum Cloud (PoC)"
            else "Local StatevectorSampler"
        )

        if backend_choice == "IBM Quantum Cloud (PoC)":
            st.toast("🔬 IBM Quantum PoC: submitting circuits locally (no credentials)", icon="🔬")
            with st.status(
                "IBM Quantum PoC — Simulating job submission ...",
                expanded=True,
                state="running",
            ) as ibm_status:
                st.write("📡 Connecting to IBM Quantum Network ...")
                time.sleep(1.0)
                st.write(
                    "⚠️  `qiskit_ibm_runtime` not installed — "
                    "falling back to local StatevectorSampler."
                )
                time.sleep(0.5)
                st.write(
                    f"⚛️  Computing K_batch ({_N_STREAM} × 1000 = "
                    f"{_N_STREAM * 1000:,} circuits) ..."
                )
                _, _, K_batch = predict_batch(X_stream, "Quantum SVM", env)
                ibm_status.update(
                    label="Quantum kernel computed (local fallback)",
                    state="complete",
                )
        else:
            with st.status(
                f"Computing quantum kernel matrix "
                f"({_N_STREAM} × {_N_TRAIN_SUB} = {_N_STREAM * _N_TRAIN_SUB:,} "
                "circuit evaluations) ...",
                expanded=True,
                state="running",
            ) as kernel_status:
                st.write(
                    f"Backend: **{_ibm_label}**  \n"
                    f"Feature map: ZZFeatureMap | reps={_ZZ_REPS} | "
                    f"entanglement='{_ZZ_ENTANGLEMENT}'  \n"
                    f"Hilbert space: C^{2**_N_QUBITS} ({_N_QUBITS} qubits)"
                )
                t_kernel_start = time.perf_counter()
                _, _, K_batch = predict_batch(X_stream, "Quantum SVM", env)
                t_kernel = time.perf_counter() - t_kernel_start
                kernel_status.update(
                    label=f"Kernel matrix ready ({t_kernel:.1f} s)",
                    state="complete",
                )
            st.success(
                f"K_batch shape: {K_batch.shape}  |  "
                f"min={K_batch.min():.4f}  max={K_batch.max():.4f}  "
                f"mean={K_batch.mean():.4f}  |  "
                f"computed in **{t_kernel:.1f} s** ({t_kernel/60:.1f} min)",
                icon="✅",
            )

    # ------------------------------------------------------------------
    # C. Live-stats containers (updated each iteration)
    # ------------------------------------------------------------------
    st.divider()
    st.markdown("### 📊 Live Detection Dashboard")

    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    attacks_metric   = stat_col1.empty()
    normal_metric    = stat_col2.empty()
    accuracy_metric  = stat_col3.empty()
    packets_metric   = stat_col4.empty()

    progress_bar  = st.progress(0, text="Scanning packets ...")
    alert_box     = st.empty()   # shows the CURRENT packet's verdict
    stream_table  = st.empty()   # shows the running log table

    # Accumulator for all results in this run.
    results: list[dict] = []

    # ------------------------------------------------------------------
    # D. Per-packet streaming loop
    # ------------------------------------------------------------------
    for i in range(_N_STREAM):
        x_pkt   = X_stream[i]          # shape (4,)
        y_true  = int(y_stream[i])

        # ---- Inference ----
        if model_choice == "Quantum SVM":
            # K_batch was pre-computed; just index row i.
            # k_row has shape (1, 1000) -- the similarity vector for this packet.
            k_row = K_batch[i : i + 1]      # shape (1, 1000)
            pred  = int(env["qsvm"].predict(k_row)[0])
            score = float(env["qsvm"].decision_function(k_row)[0])
        else:
            # Classical SVM: predict from raw (1, 4) feature vector.
            x_2d = x_pkt.reshape(1, -1)
            pred  = int(env["csvm"].predict(x_2d)[0])
            score = float(env["csvm"].decision_function(x_2d)[0])

        correct = (pred == y_true)

        # ---- Accumulate ----
        results.append({
            "#":          i + 1,
            "Packet":     f"PKT-{i+1:03d}",
            "True Label": "🔴 Attack" if y_true == 1 else "🟢 Normal",
            "Predicted":  "🔴 Attack" if pred   == 1 else "🟢 Normal",
            "Score":      f"{score:+.3f}",
            "Correct":    "✔" if correct else "✘",
        })

        # ---- Running stats ----
        n_done     = len(results)
        n_attacks  = sum(1 for r in results if "Attack" in r["Predicted"])
        n_normal   = n_done - n_attacks
        run_acc    = sum(1 for r in results if r["Correct"] == "✔") / n_done

        # ---- Update stat metrics ----
        attacks_metric.metric("🚨 Attacks Detected",  n_attacks)
        normal_metric.metric("✅ Normal Packets",      n_normal)
        accuracy_metric.metric("🎯 Running Accuracy",  f"{run_acc:.1%}")
        packets_metric.metric("📦 Packets Scanned",    f"{n_done}/{_N_STREAM}")

        # ---- Current-packet alert ----
        with alert_box.container():
            feat_str = "  ".join(
                f"θ{j+1}={x_pkt[j]:.3f}" for j in range(_N_QUBITS)
            )
            if pred == 1:
                st.error(
                    f"🚨 **ATTACK DETECTED**  |  Packet #{i+1}  "
                    f"|  True: {'⚠ Attack' if y_true==1 else '✔ Normal'}  "
                    f"|  Score: {score:+.3f}  |  {feat_str}"
                )
            else:
                st.success(
                    f"✅ **NORMAL TRAFFIC**  |  Packet #{i+1}  "
                    f"|  True: {'⚠ Attack' if y_true==1 else '✔ Normal'}  "
                    f"|  Score: {score:+.3f}  |  {feat_str}"
                )

        # ---- Running log table (last 10 rows) ----
        with stream_table.container():
            df = pd.DataFrame(results[-10:])
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "#":          st.column_config.NumberColumn(width="small"),
                    "Score":      st.column_config.TextColumn(width="small"),
                    "Correct":    st.column_config.TextColumn(width="small"),
                },
            )

        # ---- Progress ----
        progress_bar.progress(
            (i + 1) / _N_STREAM,
            text=f"Scanning packets ... {i+1}/{_N_STREAM}",
        )

        # ---- Simulate inter-packet network delay ----
        time.sleep(0.5)

    # ------------------------------------------------------------------
    # E. Final summary after all _N_STREAM packets
    # ------------------------------------------------------------------
    progress_bar.progress(1.0, text="Scan complete ✔")
    st.divider()
    st.markdown("### 🏁 Monitoring Session Summary")

    df_final = pd.DataFrame(results)
    total       = len(df_final)
    tot_attacks = int((df_final["True Label"].str.contains("Attack")).sum())
    tot_normal  = total - tot_attacks
    det_attacks = int((df_final["Predicted"].str.contains("Attack")).sum())
    final_acc   = sum(1 for r in results if r["Correct"] == "✔") / total
    recall_atk  = (
        df_final[
            df_final["True Label"].str.contains("Attack") &
            df_final["Predicted"].str.contains("Attack")
        ].shape[0] / max(tot_attacks, 1)
    )

    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Total Packets",     total)
    s2.metric("True Attacks",      tot_attacks)
    s3.metric("Attacks Flagged",   det_attacks)
    s4.metric("Final Accuracy",    f"{final_acc:.1%}")
    s5.metric("Attack Recall",     f"{recall_atk:.1%}",
              help="Fraction of true attacks correctly detected. "
                   "Primary IDS metric -- minimises False Negatives.")

    st.dataframe(df_final, use_container_width=True, hide_index=True)

    if recall_atk < 0.5:
        st.warning(
            f"⚠️ Attack Recall is low ({recall_atk:.1%}).  "
            "Consider lowering the SVM decision threshold or increasing "
            "the training sample size for the QSVM.",
            icon="⚠️",
        )
    else:
        st.success(
            f"Session complete.  Model: **{model_choice}**  |  "
            f"Accuracy: **{final_acc:.1%}**  |  "
            f"Attack Recall: **{recall_atk:.1%}**",
            icon="✅",
        )

# ---------------------------------------------------------------------------
# 9. FOOTER
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "NIDS QEMS — Quantum-Enhanced Monitoring System  ·  "
    "NSL-KDD Dataset  ·  ZZFeatureMap (Havlicek et al., Nature 2019)  ·  "
    "4-Qubit Statevector Simulation  ·  scikit-learn SVC"
)
