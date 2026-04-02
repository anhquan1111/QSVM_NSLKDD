# Data Loading & Subsampling Migration Guide

**Project:** QSVM_NSLKDD — NSL-KDD Intrusion Detection
**Scope:** Phase 2 (`train_qsvm.py`) → Phase 3 (`evaluate_models.py`) pipeline handoff
**Date:** 2026-03-30

---

## 1. Data Paths & File Formats

Both scripts share the same root path resolution strategy (`Path(__file__).resolve().parent.parent`) and read from the same four `.npy` files. The directories and their roles are identical across both scripts.

| Attribute | `train_qsvm.py` (Phase 2) | `evaluate_models.py` (Phase 3) |
|---|---|---|
| **Processed data dir** | `data/processed/` | `data/processed/` |
| **Models dir** | `models/` | `models/` |
| **Reports dir** | *(not used)* | `reports/` *(new)* |
| **Input files** | `X_train.npy`, `y_train.npy`, `X_test.npy`, `y_test.npy` | Same four files |
| **Input dtype at load** | `float32` (NumPy default); cast to `float64` **after** subsampling | Cast to `float64` **at load time**, before subsampling |
| **Output artefacts** | `models/qsvm_model.pkl`, `models/csvm_model.pkl` | Reads those `.pkl` files; writes `reports/*.png` |

**Notable difference:** Phase 3 applies `.astype(np.float64)` immediately on `np.load(...)`, ensuring the full arrays are float64 before any split is computed. Phase 2 casts only the subsampled arrays after the split. This is a safe change because the cast is deterministic, but the placement is now earlier in Phase 3 to prevent any chance of dtype mismatch propagating into the split logic.

---

## 2. Subsampling Logic

### 2.1 Phase 2 — `stratified_subsample()` (Old)

```
load_processed_data()
    → X_train_full, y_train_full  (full train split, ~87,831 rows)
    → X_test_full,  y_test_full   (full test split,  ~22,544 rows)

stratified_subsample(X_train_full, y_train_full, N_TRAIN_SUBSAMPLE=2500)
    → discard_fraction = 1.0 - 2500 / len(y_train_full)
    → train_test_split(..., test_size=discard_fraction, stratify=y, random_state=42)
    → returns FIRST split (size ≈ 2500): X_train, y_train

stratified_subsample(X_test_full, y_test_full, N_TEST_SUBSAMPLE=500)
    → discard_fraction = 1.0 - 500 / len(y_test_full)
    → train_test_split(..., test_size=discard_fraction, stratify=y, random_state=42)
    → returns FIRST split (size ≈ 500): X_test, y_test
```

**Key characteristics:**
- Two-phase design: loading and subsampling are **separate functions**.
- Subsample sizes: **2,500 train / 500 test**.
- `float64` cast happens **after** both subsamples are drawn.
- No shape assertions — the caller trusts the returned sizes implicitly.
- The function is general-purpose (reusable for any `(X, y, sample_size)` tuple).

### 2.2 Phase 3 — `load_and_reconstruct_subsamples()` (New)

```
load_and_reconstruct_subsamples()
    → loads all four .npy files; casts X arrays to float64 immediately
    → train_discard = 1.0 - N_TRAIN_SUB / len(y_full)
    → train_test_split(X_full, y_full,
                       test_size=train_discard,
                       stratify=y_full,
                       random_state=42)
    → keeps first split: X_train_sub (shape: 1000 × 4), y_train_sub

    → test_discard = 1.0 - N_TEST_SUB / len(y_te_full)
    → train_test_split(X_te_full, y_te_full,
                       test_size=test_discard,
                       stratify=y_te_full,
                       random_state=42)
    → keeps first split: X_test_sub (shape: 300 × 4), y_test_sub

    → assert X_train_sub.shape == (1000, 4)
    → assert X_test_sub.shape  == (300,  4)
    → returns X_train_sub, y_train_sub, X_test_sub, y_test_sub
```

**Key characteristics:**
- Loading and subsampling are **unified in one function** — there is a single entry point for data access in Phase 3.
- Subsample sizes: **1,000 train / 300 test** *(different from Phase 2 — see §2.3)*.
- `float64` cast happens **before** the split.
- **Hard assertions** validate output shapes before returning — a broken reconstruction raises `AssertionError` immediately rather than silently producing wrong-shaped data.

### 2.3 Why the Exact Reconstruction with `random_state=42` Is Critical

This is the most important constraint in the entire pipeline. It exists because of how sklearn's `SVC` stores its model state in `kernel='precomputed'` mode.

**The precomputed kernel index problem:**

When `SVC(kernel='precomputed').fit(K_train, y_train)` is called, sklearn does not store the actual support vector feature vectors. Instead, `model.support_` stores **integer row indices** into the `K_train` matrix that was passed to `fit()`. For example, `support_ = [3, 17, 42, ...]` means "row 3, row 17, row 42 of the original training matrix are support vectors."

At inference time, `model.predict(K_test)` requires `K_test` to have shape `(N_test, N_train)` where the **column ordering of `K_test` matches the exact same N_train rows** that were passed during `fit()`. If any sample is different — or in a different order — the support vector indices silently point to wrong columns in `K_test`, producing completely incorrect predictions **without raising any exception**.

**How deterministic reconstruction solves this:**

`sklearn.model_selection.train_test_split` is a **pure, deterministic function** of its inputs and `random_state`. Given the same full arrays, the same `test_size` fraction, and `random_state=42`, it always returns the exact same rows in the exact same order. Phase 3 exploits this guarantee to reconstruct the Phase 2 training subsample from scratch, making it safe to load the saved QSVM and immediately call `.predict()` with a freshly computed `K_test`.

```
Phase 2 training call (train_qsvm.py):
    train_test_split(X_full, y_full, test_size=discard_fraction,
                     stratify=y_full, random_state=42)
                     ↓
    X_train_sub rows: [idx_0, idx_1, idx_2, ... idx_999]

Phase 3 inference call (evaluate_models.py):
    train_test_split(X_full, y_full, test_size=discard_fraction,
                     stratify=y_full, random_state=42)  ← identical call
                     ↓
    X_train_sub rows: [idx_0, idx_1, idx_2, ... idx_999]  ← guaranteed identical

    K_test[i, j] = quantum_kernel(X_test[i], X_train_sub[j])
                               column j maps to the same sample
                               the QSVM was trained on ✓
```

Changing `random_state`, the subsample sizes, or the order of the `train_test_split` arguments even slightly would produce a different subset, silently invalidating all QSVM predictions.

---

## 3. Constant Discrepancies Between the Two Scripts

A significant discovery during this migration analysis: **the two scripts currently use different circuit hyperparameters and subsample sizes**. These must be reconciled before Phase 3 can correctly evaluate the Phase 2 QSVM.

| Constant | `train_qsvm.py` (Phase 2) | `evaluate_models.py` (Phase 3) | Must Match? |
|---|---|---|---|
| `N_TRAIN_SUBSAMPLE` / `N_TRAIN_SUB` | **2,500** | **1,000** | **YES — critical** |
| `N_TEST_SUBSAMPLE` / `N_TEST_SUB` | **500** | **300** | **YES — critical** |
| `ZZ_REPS` | **3** | **2** | YES — kernel identity |
| `ZZ_ENTANGLEMENT` | **"full"** | **"linear"** | YES — kernel identity |
| `RANDOM_STATE` | 42 | 42 | YES — reconstruction |

> **Action required:** Before running Phase 3, either update `evaluate_models.py` constants to match Phase 2 (`N_TRAIN_SUB=2500`, `N_TEST_SUB=500`, `ZZ_REPS=3`, `ZZ_ENTANGLEMENT="full"`), or retrain Phase 2 with the Phase 3 constants. These values must be in sync or the QSVM evaluation will produce garbage results.

---

## 4. Variable Mapping: Old → New

| Stage | `train_qsvm.py` variable | `evaluate_models.py` variable | Notes |
|---|---|---|---|
| Full train features | `X_train_full` | `X_full` | Renamed; scope is local to the load function in Phase 3 |
| Full train labels | `y_train_full` | `y_full` | Same |
| Full test features | `X_test_full` | `X_te_full` | Renamed |
| Full test labels | `y_test_full` | `y_te_full` | Renamed |
| Subsampled train features | `X_train` *(after overwrite)* | `X_train_sub` | Phase 3 uses explicit `_sub` suffix — no variable shadowing |
| Subsampled train labels | `y_train` *(after overwrite)* | `y_train_sub` | Same rationale |
| Subsampled test features | `X_test` *(after overwrite)* | `X_test_sub` | Same |
| Subsampled test labels | `y_test` *(after overwrite)* | `y_test_sub` | Same |
| Train Gram matrix | `K_train` | `K_train` | No rename |
| Test Gram matrix | `K_test` | `K_test` | No rename |

**Design improvement in Phase 3:** Phase 2 overwrites `X_train` / `X_test` with the subsampled versions (the full arrays are discarded after the subsample call). Phase 3 uses the `_sub` suffix throughout, making it immediately clear which arrays are subsampled. This eliminates the ambiguity risk of accidentally using the full-size array where the subsampled one is expected.

---

## 5. Required Dependencies

### 5.1 Shared (present in both scripts)

```python
import joblib
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from qiskit.circuit.library import zz_feature_map
from qiskit.primitives import StatevectorSampler
from qiskit_machine_learning.kernels import FidelityQuantumKernel
from qiskit_machine_learning.state_fidelities import ComputeUncompute
```

> Note: `joblib` and `train_test_split` already exist in `train_qsvm.py` — they are not new additions for Phase 3.

### 5.2 New in Phase 3 Only

| Import | Purpose |
|---|---|
| `import matplotlib.pyplot as plt` | Confusion matrix and ROC curve plotting |
| `import matplotlib.ticker as mticker` | Axis tick formatting for publication-quality figures |
| `import seaborn as sns` | Heatmap styling for confusion matrix |
| `from sklearn.metrics import ConfusionMatrixDisplay` | Structured confusion matrix rendering |
| `from sklearn.metrics import confusion_matrix` | Raw confusion matrix computation |
| `from sklearn.metrics import roc_auc_score, roc_curve` | ROC/AUC evaluation |
| `from sklearn.model_selection import GridSearchCV` | Classical SVM hyperparameter tuning |
| `import warnings` | Suppressing sklearn convergence warnings during grid search |

### 5.3 Present in Phase 2 but Absent in Phase 3

| Import | Reason absent |
|---|---|
| `from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score` | Phase 3 uses `classification_report` (already imported) and `roc_auc_score` instead of computing individual metrics manually |
| `import time` | Phase 3 still uses `time` (present) — no gap here |

---

## 6. Structural Summary

```
train_qsvm.py                         evaluate_models.py
─────────────────────────────────     ──────────────────────────────────────
load_processed_data()                 ┐
    → X_train_full, y_train_full      │  load_and_reconstruct_subsamples()
    → X_test_full,  y_test_full       │      → X_train_sub, y_train_sub
                                      │      → X_test_sub,  y_test_sub
stratified_subsample(X_train, 2500)   │  (unified: load + split in one call,
stratified_subsample(X_test,   500)   ┘   with assertions and float64 cast)

build_quantum_kernel()                build_quantum_kernel()
    reps=3, entanglement="full"           reps=2, entanglement="linear"  ⚠

precompute_kernel_matrices(...)       quantum_kernel.evaluate(X_test_sub, X_train_sub)
    → K_train, K_test                     → K_test  (test only; K_train from Phase 2)

train_qsvm(K_train, y_train)          joblib.load("models/qsvm_model.pkl")
train_classical_svm(X_train, y_train) joblib.load("models/csvm_model.pkl")

evaluate_model(qsvm, K_test, y_test)  GridSearchCV on csvm (recall scoring)
evaluate_model(csvm, X_test, y_test)  confusion_matrix, roc_curve → reports/*.png

save_models(qsvm, csvm)               (reads saved models; does not save new ones)
```

---

## 7. Migration Checklist

Before refactoring any code, confirm the following:

- [ ] **Constants are synchronised** — `N_TRAIN_SUB`, `N_TEST_SUB`, `ZZ_REPS`, `ZZ_ENTANGLEMENT`, and `RANDOM_STATE` in `evaluate_models.py` match the values used to produce the saved `qsvm_model.pkl`.
- [ ] **`data/processed/*.npy` files are present** — both scripts require the same four Phase 1 outputs.
- [ ] **`models/qsvm_model.pkl` and `models/csvm_model.pkl` are present** — Phase 3 loads these; they must have been produced by the Phase 2 run whose constants you are matching.
- [ ] **`reports/` directory exists** (or is created at runtime) — Phase 3 writes PNG outputs there.
- [ ] **All Phase 3 dependencies are installed** — `matplotlib`, `seaborn`, and `scikit-learn >= 1.2` (for `ConfusionMatrixDisplay`) must be present in the virtual environment.
