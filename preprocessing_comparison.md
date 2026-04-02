# Preprocessing Pipeline Comparative Analysis
## `data_preprocessing.py` vs. `preprocess.ipynb`

**Project:** QSVM-IDS on NSL-KDD
**Analysis Date:** 2026-03-30
**Analyst Role:** Expert Data Scientist

---

## Executive Summary

The two pipelines produce **fundamentally incompatible outputs** that cannot be used interchangeably. The accuracy gap (~65% vs. >80%) is not caused by a subtle bug — it is the expected and correct consequence of two pipelines designed for **different end-tasks**. `data_preprocessing.py` produces a 4-dimensional quantum-ready representation for the QSVM circuit; `preprocess.ipynb` produces a high-dimensional classical ML–ready DataFrame as a preliminary step in a multi-notebook workflow. The >80% accuracy observed from the notebook's output comes from retaining ~85 features with full classical information density, while the ~65% accuracy from `data_preprocessing.py` reflects the information cost of compressing 85 features into 4 qubit rotation angles — a cost imposed by the hardware constraint of the 4-qubit circuit, not a flaw in the code.

**Critical finding:** `preprocess.ipynb` contains a latent **data leakage defect** in its `feature_cols` construction (Section 5.1) that, while passively contained by downstream column-selection guards, can cause severe label leakage if those guards are bypassed.

---

## Table of Contents

1. [Pipeline Architecture Overview](#1-pipeline-architecture-overview)
2. [Data Loading and Cleaning](#2-data-loading-and-cleaning)
3. [Label Engineering](#3-label-engineering)
4. [Categorical Encoding (One-Hot)](#4-categorical-encoding-one-hot)
5. [Scaling Strategy](#5-scaling-strategy)
6. [Feature Selection (SelectKBest)](#6-feature-selection-selectkbest)
7. [Dimensionality Reduction (PCA)](#7-dimensionality-reduction-pca)
8. [Output Format and Artifacts](#8-output-format-and-artifacts)
9. [Data Leakage Audit](#9-data-leakage-audit)
10. [Root Cause of the Accuracy Gap](#10-root-cause-of-the-accuracy-gap)
11. [Scientific Rigor Verdict](#11-scientific-rigor-verdict)
12. [Discrepancy Summary Table](#12-discrepancy-summary-table)

---

## 1. Pipeline Architecture Overview

### `data_preprocessing.py` — Complete End-to-End Pipeline

```
Raw CSV (43 cols)
  ↓  Drop difficulty_level
  ↓  Binarize label (0/1)
  ↓  Split → X_train, X_test, y_train, y_test
  ↓  pd.get_dummies (OHE) → ~85 columns
  ↓  SelectKBest(f_classif, k=15) — fit on TRAIN ONLY
  ↓  PCA(n_components=4)          — fit on TRAIN ONLY
  ↓  MinMaxScaler([0, π])         — fit on TRAIN ONLY
  ↓
X_train.npy  (125973, 4) float32 ∈ [0, π]
X_test.npy   (22544,  4) float32 ∈ [0, π]
y_train.npy  (125973,)  int64  ∈ {0,1}
y_test.npy   (22544,)   int64  ∈ {0,1}
```

**Purpose:** Produce QSVM-ready features. Self-contained; no further preprocessing needed.

---

### `preprocess.ipynb` — Stage 1 of a Multi-Notebook Workflow

```
Raw CSV (43 cols)
  ↓  Drop difficulty_level
  ↓  Create 3 label columns (binary, multiclass, attack_category)
  ↓  pd.get_dummies (OHE) → ~85 columns    ← 'label' string column ALSO retained (see §5.1)
  ↓  MinMaxScaler([0, 1])  — fit on TRAIN ONLY
  ↓  Stratified sampling (custom function)
  ↓
NSL_KDD_Train_Cleaned.csv  (~125973, ~89 cols) float64 ∈ [0,1]  + 4 label cols
NSL_KDD_Test_Cleaned.csv   (~22544,  ~89 cols) float64 ∈ [0,1]  + 4 label cols
NSL_KDD_Train_Sample*.csv  (subsets: 100/200/500/1000 rows)
NSL_KDD_Test_Sample*.csv   (subsets: 100/200/300 rows)
minmax_scaler.joblib
```

**Explicit handoff stated in notebook:** `→ Bước tiếp theo: selectkbest_nslkdd.ipynb`
SelectKBest and PCA are intentionally deferred to a downstream notebook.

---

## 2. Data Loading and Cleaning

| Aspect | `data_preprocessing.py` | `preprocess.ipynb` |
|---|---|---|
| Parser | `pd.read_csv(na_values=[" ", ""])` | `pd.read_csv` (no `na_values`) |
| Whitespace NaN detection | Yes — bare spaces become NaN | No — bare spaces kept as-is |
| `difficulty_level` handling | `df.drop(columns=["difficulty_level"], inplace=True)` | `train_df.drop('difficulty_level', axis=1, inplace=True)` |
| NaN audit after load | Implicit (no explicit check pre-OHE) | Explicit: `train_clean.isna().sum().sum()` sanity check |
| Missing value strategy | None declared (none in NSL-KDD) | None declared |

### Assessment

Both pipelines correctly drop `difficulty_level`. The only meaningful difference is that `data_preprocessing.py` treats whitespace tokens (`" "`, `""`) as `NaN` during CSV parsing — a more defensive choice. In practice, NSL-KDD contains no missing values, so this difference has no effect on the numeric output. However, `data_preprocessing.py` is more robust to malformed input.

---

## 3. Label Engineering

This is one of the most significant divergences between the two pipelines.

### `data_preprocessing.py` — Single Binary Label

```python
# Maps 'normal' → 0, everything else → 1
df[LABEL_COL] = series.apply(
    lambda lbl: 0 if str(lbl).strip() == 'normal' else 1
).astype(np.int64)
```

- Produces **one** label column: `label` ∈ {0, 1}
- 23+ attack sub-types are all collapsed into class 1
- `dtype=int64`

### `preprocess.ipynb` — Three-Column Label Structure

```python
df['label_binary']     = (df['label'] != 'normal').astype(int)
df['label_multiclass'] = df['label'].copy()          # raw string: 'neptune', 'smurf', ...
df['attack_category']  = df['label'].map(ATTACK_CATEGORY_MAP)  # DoS/Probe/R2L/U2R/Normal
```

- Produces **three** label columns simultaneously
- `label_binary` uses boolean comparison (semantically equivalent to `data_preprocessing.py`)
- `label_multiclass` preserves all 22 attack sub-types — intended for C4 analysis (per research document)
- `attack_category` maps to 5 macro-categories — used for stratified sampling
- Original `label` string column is **not dropped** after this step (see §5.1)

### Assessment

The binary label encoding is logically equivalent between the two pipelines. The notebook's richer label structure is intentional and scientifically justified: it supports multi-class evaluation (C4 contributions) and enables truly representative stratified sampling via `attack_category`. This is **more complete** but introduces the risk described in Section 5.1.

---

## 4. Categorical Encoding (One-Hot)

### `data_preprocessing.py`

```python
# Separate OHE on train and test, then align test to train vocabulary
X_train_enc = pd.get_dummies(X_train, columns=CATEGORICAL_COLS, dtype=np.float32)
X_test_enc  = pd.get_dummies(X_test,  columns=CATEGORICAL_COLS, dtype=np.float32)
X_test_enc  = X_test_enc.reindex(columns=X_train_enc.columns, fill_value=0.0)
```

- `dtype=np.float32` — memory-efficient
- Applied on feature-only DataFrame (label column already separated)
- `reindex` correctly handles unseen test categories (filled with 0.0)

### `preprocess.ipynb`

```python
# Same structural approach, but applied to feature_cols which still contains 'label' string
X_train_enc = pd.get_dummies(train_feat, columns=CATEGORICAL_COLS, dtype=float)
X_test_enc  = pd.get_dummies(test_feat,  columns=CATEGORICAL_COLS, dtype=float)
X_test_enc  = X_test_enc.reindex(columns=X_train_enc.columns, fill_value=0.0)
```

- `dtype=float` (float64) — 2× more memory than float32
- Applied on `train_feat` which **includes the raw `label` string column** (not encoded by OHE since `label` ∉ `CATEGORICAL_COLS`, but retained as an object column — see §5.1)
- `reindex` alignment logic is identical and correct

### Assessment

The OHE mechanism is structurally identical and correctly implements zero-leakage alignment. The material difference is the presence of the `label` string column in the notebook's input DataFrame (`train_feat`) — this is the source of the latent leakage risk detailed in Section 5.1.

---

## 5. Scaling Strategy

This is the **most impactful technical divergence** between the two pipelines.

### 5.1 — `data_preprocessing.py`: MinMaxScaler to `[0, π]` (Post-PCA)

```python
scaler = MinMaxScaler(feature_range=(0.0, np.pi))  # π ≈ 3.14159

X_train_scaled = scaler.fit_transform(X_train_pca)   # after PCA(4 components)
X_test_scaled  = scaler.transform(X_test_pca)
X_test_scaled  = np.clip(X_test_scaled, 0, np.pi)    # explicit clipping for OOD safety
```

**When applied:** Step 8 — the final step, applied to the 4-dimensional PCA output.
**Why [0, π]:** The ZZFeatureMap uses `RY(xᵢ)|0⟩` gates where xᵢ is a rotation angle. The full [0, π] range exploits the entire upper Bloch hemisphere without angle wrapping (which would corrupt kernel geometry). This is a **physics-driven design constraint**, not an arbitrary choice.
**What is scaled:** Only the 4 final PCA components.

### 5.2 — `preprocess.ipynb`: MinMaxScaler to `[0, 1]` (Post-OHE)

```python
scaler = MinMaxScaler()   # default range=(0, 1)

numeric_cols = train_feat_enc.select_dtypes(include=[np.number]).columns.tolist()
train_feat_enc[numeric_cols] = scaler.fit_transform(train_feat_enc[numeric_cols])
test_feat_enc[numeric_cols]  = np.clip(scaler.transform(test_feat_enc[numeric_cols]), 0, 1)
```

**When applied:** Step 4 — immediately after OHE, before any feature selection or PCA.
**Why [0, 1]:** General-purpose normalization for classical ML algorithms.
**What is scaled:** All ~85 numeric columns simultaneously (OHE binary columns + 38 numeric features). This is the correct step for a general preprocessing stage but **incorrect for quantum encoding**.

### Critical Comparison

| Property | `data_preprocessing.py` | `preprocess.ipynb` |
|---|---|---|
| Scaler type | `MinMaxScaler` | `MinMaxScaler` |
| Target range | **`[0, π]`** | **`[0, 1]`** |
| Position in pipeline | After SelectKBest + PCA (step 8 of 8) | After OHE only (step 4 of 5) |
| Columns scaled | 4 PCA components | ~85 OHE+numeric columns |
| Quantum compatibility | ✓ Correct | ✗ Wrong range for quantum gates |
| OHE binary column scaling | N/A (filtered out by SelectKBest) | Scales 0/1 binary columns — no effect, but wastes computation |

### 5.3 — Latent Data Leakage Defect in `preprocess.ipynb`

**Severity: HIGH (latent — currently contained by downstream guard)**

In `preprocess_nsl_kdd()`, the feature columns are selected as:

```python
# Cell 6, line 3
feature_cols = [c for c in train_df.columns if c not in LABEL_COLS]
```

`LABEL_COLS = ['label_binary', 'label_multiclass', 'attack_category']`

At this point, `train_df` contains the **original `label` string column** (e.g., `'neptune'`, `'normal'`, `'smurf'`). Since `'label'` ∉ `LABEL_COLS`, it is **included in `feature_cols`**. It flows into `train_feat`, survives `get_dummies` as an unconverted object column (it's not in `CATEGORICAL_COLS`), and is excluded from scaling (not in `numeric_cols`). The final output DataFrames `train_clean` and `test_clean` **contain the raw label string as a non-numeric column**.

The defect is *passively mitigated* by:
```python
# Cell 8, correct exclusion
feature_cols_out = [c for c in train_clean.columns if c not in LABEL_COLS and c not in EXCLUDED_COLS]
#                                                                              ↑ EXCLUDED_COLS = ['label']
```

**If `feature_cols_out` is not used when feeding data to a model** (e.g., if someone passes `train_clean.drop(LABEL_COLS, axis=1)` instead), the `label` column with ~22 unique string values is passed to the model, causing catastrophic label leakage that would artifically inflate accuracy to near-100%.

`data_preprocessing.py` has **no such risk**: the label column is separated before OHE and never rejoined to the feature matrix.

---

## 6. Feature Selection (SelectKBest)

This is the **most structurally critical difference** between the two pipelines.

### `data_preprocessing.py`

```python
selector = SelectKBest(score_func=f_classif, k=15)
X_train_sel = selector.fit_transform(X_train_np, y_train_np)  # fit on TRAIN ONLY
X_test_sel  = selector.transform(X_test_np)                    # never fit on test
```

- **ANOVA F-statistic** scores each of ~85 OHE-expanded features by linear separability vs. the binary label
- Retains the **top 15 features** — removes sparse OHE columns and noisy near-zero-variance features
- Result: 85 → 15 features, preparing a clean input for PCA
- Transformer saved as `models/feature_selector.joblib` for reproducible inference
- Zero-leakage: F-statistics computed from training data labels only

### `preprocess.ipynb`

```python
# NO SelectKBest anywhere in this file
# Explicit handoff to next notebook:
print(f'\n→ Bước tiếp theo: selectkbest_nslkdd.ipynb')
```

- **Zero feature selection performed** in this notebook
- All ~85 OHE features pass through to the output CSV
- SelectKBest is deferred to `selectkbest_nslkdd.ipynb` (a separate file)
- This is an explicit design decision, not an omission — the notebook is Stage 1 of a multi-stage workflow

### Assessment

The two pipelines are not comparable at this step: `data_preprocessing.py` is a complete single-pass pipeline; `preprocess.ipynb` is deliberately incomplete. However, this architectural difference directly explains the accuracy gap (see §10).

---

## 7. Dimensionality Reduction (PCA)

### `data_preprocessing.py`

```python
pca = PCA(n_components=4, random_state=42)
X_train_pca = pca.fit_transform(X_train_sel)   # fit on 15 SelectKBest features, TRAIN ONLY
X_test_pca  = pca.transform(X_test_sel)         # never fit on test
```

- **4 components** — hard-coded to match the 4-qubit circuit constraint
- Applied to the 15 SelectKBest features (not to all 85)
- `random_state=42` ensures deterministic eigenvector sign conventions
- Explains variance reported per-component at runtime
- Transformer saved as `models/pca_4components.joblib`

**Design rationale:** With 15 SelectKBest inputs (cleaned of noisy OHE columns), PCA extracts 4 principal components with high cumulative explained variance. Each component becomes a qubit rotation angle θᵢ ∈ [0, π] in the ZZFeatureMap.

### `preprocess.ipynb`

```python
# NO PCA anywhere in this file
# PCA is deferred to selectkbest_nslkdd.ipynb
```

- **Zero PCA performed** — output retains ~85 features
- Not an error; it is a design decision matching the multi-notebook pipeline architecture

### Assessment

`preprocess.ipynb`'s output is dimensionally incompatible with the QSVM circuit, which requires exactly 4 features. Feeding the notebook's ~85-feature CSV directly to the QSVM would fail immediately. The notebook is designed as a general-purpose preprocessing stage from which QSVM-specific reduction happens in a subsequent notebook.

---

## 8. Output Format and Artifacts

### `data_preprocessing.py`

| Artifact | Path | Shape | dtype | Value Range |
|---|---|---|---|---|
| `X_train.npy` | `data/processed/` | (125973, 4) | float32 | [0, π] |
| `X_test.npy` | `data/processed/` | (22544, 4) | float32 | [0, π] ± clip |
| `y_train.npy` | `data/processed/` | (125973,) | int64 | {0, 1} |
| `y_test.npy` | `data/processed/` | (22544,) | int64 | {0, 1} |
| `feature_selector.joblib` | `models/` | SelectKBest | — | — |
| `pca_4components.joblib` | `models/` | PCA | — | — |
| `scaler_minmax_pi.joblib` | `models/` | MinMaxScaler | — | — |

**Key properties:**
- 4D feature arrays directly loadable by `train_qsvm.py` via `np.load()`
- Binary `.npy` format: lossless, compact, type-preserving
- Single output directory (`data/processed/`)

### `preprocess.ipynb`

| Artifact | Path | Shape | dtype | Value Range |
|---|---|---|---|---|
| `NSL_KDD_Train_Cleaned.csv` | `data/processed_data/` | (125973, ~89) | float64/object | [0,1] + strings |
| `NSL_KDD_Test_Cleaned.csv` | `data/processed_data/` | (22544, ~89) | float64/object | [0,1] + strings |
| `NSL_KDD_Train_Sample1000.csv` | `data/processed_data/` | (1000, ~89) | float64/object | [0,1] + strings |
| `NSL_KDD_Train_Sample100/200/500.csv` | `data/processed_data/` | (N, ~89) | float64/object | [0,1] + strings |
| `NSL_KDD_Test_Sample100/200/300.csv` | `data/processed_data/` | (N, ~89) | float64/object | [0,1] + strings |
| `minmax_scaler.joblib` | `data/processed_data/` | MinMaxScaler | — | — |
| `feature_columns.csv` | `data/processed_data/` | (~85, 1) | string | feature names |

**Key properties:**
- ~85 features (NOT reduced to 4)
- Scaled to [0, 1] (NOT to [0, π])
- Retains `label` string column alongside label columns (leakage risk)
- CSV format: human-readable but ~3–4× larger than `.npy` and loses dtype precision for float32
- Output directory is **different** (`data/processed_data/` vs `data/processed/`)
- float64 vs float32 — doubles memory footprint

### Critical Incompatibility

The two pipelines write to **different directories** with **different file names** and **different shapes**. They cannot be used interchangeably with any downstream code without modification.

---

## 9. Data Leakage Audit

### Zero-Leakage Practices — Both Pipelines

Both pipelines correctly implement the fundamental zero-leakage contract:

| Operation | `data_preprocessing.py` | `preprocess.ipynb` |
|---|---|---|
| OHE vocabulary | Train vocabulary only; test aligned via `reindex` | Identical approach |
| SelectKBest F-scores | Fit on train labels only | N/A (not in this file) |
| PCA eigenvectors | Fit on train features only | N/A (not in this file) |
| Scaler min/max | Fit on train features only | Fit on train features only |
| Test set transform | `scaler.transform()` (no fit) | `scaler.transform()` (no fit) |

### Leakage Defect in `preprocess.ipynb` — Latent but Dangerous

As documented in §5.3, the `label` column (raw string) is included in `feature_cols` and flows through to the output DataFrames. This is a **structural defect** in the `preprocess_nsl_kdd()` function.

**Fix (one line):**
```python
# CURRENT (defective):
feature_cols = [c for c in train_df.columns if c not in LABEL_COLS]

# CORRECTED:
feature_cols = [c for c in train_df.columns if c not in LABEL_COLS and c not in EXCLUDED_COLS]
```

Until this is fixed, any code that fails to use the downstream `feature_cols_out` guard (e.g., any contributor who accesses `train_clean.drop(LABEL_COLS, axis=1)` without also dropping `label`) will produce a severely contaminated training set.

---

## 10. Root Cause of the Accuracy Gap

The observed ~65% vs. >80% accuracy difference has four compounding causes:

### Cause 1: Dimensionality (Most Impactful)

| Aspect | `data_preprocessing.py` output | `preprocess.ipynb` output |
|---|---|---|
| Feature count | **4** | **~85** |
| Information retained | Low (lossy 85→15→4 compression) | High (full feature set) |

A classical SVM trained on 4 PCA components of NSL-KDD will always perform worse than one trained on 85 features — not because the pipeline is wrong, but because heavy dimensionality reduction is an inherent information trade-off. The 4-dimensional constraint exists to satisfy the QSVM's 4-qubit hardware limit, not to maximize classical SVM accuracy.

### Cause 2: Scaling Range

Features in [0, 1] (notebook) vs. [0, π] (script) produce different kernel evaluations in classical SVMs with RBF or polynomial kernels. The [0, π] range increases inter-point distances, directly affecting the RBF kernel bandwidth and classification margin. A classical SVM never trained to account for [0, π]-range features will show degraded accuracy compared to the standard [0, 1] range.

### Cause 3: Feature Quality

`data_preprocessing.py` applies SelectKBest (k=15) to remove ~70 low-F-score OHE columns before PCA. While this improves PCA quality, it removes features that may be individually weak but collectively informative for classical SVMs (particularly tree-based models and distance-based classifiers in high dimensions).

### Cause 4: Pipeline Stage Mismatch

If the ~65% result was observed by running `train_qsvm.py` directly on `data_preprocessing.py` outputs, it reflects QSVM performance on 4-dimensional features — which is the intended comparison. If instead someone trained a classical SVM on `data_preprocessing.py`'s 4-dimensional [0, π] features and compared it to a classical SVM trained on the notebook's 85-dimensional [0, 1] features, the gap is expected and does not indicate a bug.

### Summary

```
preprocess.ipynb → 85 features, [0,1] → Classical SVM → ~80%+ accuracy (classical ML regime)
data_preprocessing.py → 4 features, [0,π] → Classical SVM → ~65% accuracy (quantum-compatible regime)
data_preprocessing.py → 4 features, [0,π] → QSVM → competitive accuracy (intended use case)
```

The comparison is not apples-to-apples. Neither result is wrong in context.

---

## 11. Scientific Rigor Verdict

### `data_preprocessing.py` — ✓ More Scientifically Rigorous for QSVM

**Strengths:**
1. **Complete, self-contained pipeline** — one script produces all artifacts needed for QSVM training and evaluation
2. **Strict zero-leakage contract** — enforced at every transformation step with clear documentation
3. **Physics-motivated scaling** — [0, π] range is not arbitrary; it matches the RY gate rotation angle domain for full Bloch hemisphere utilization
4. **Correct dimensionality reduction order** — SelectKBest → PCA ensures PCA operates on clean, high-F signal rather than on a noisy 85-D space
5. **Type discipline** — float32 (not float64) for features, int64 for labels; explicit dtype control
6. **Production-ready artifact serialization** — `.npy` + `.joblib` with correct transformer names for reproducible inference
7. **Explicit sanity assertions** — `assert` statements verify shape and value range post-pipeline
8. **No latent leakage defects** — label column is cleanly separated before any feature transformation

**Weaknesses:**
1. `apply_select_k_best()` contains a `raise RuntimeError` sentinel as its body — the actual implementation is in `_apply_select_k_best_internal()`. This is a confusing design pattern that could mislead contributors.
2. No explicit NaN audit after loading (minor — NSL-KDD has no NaNs).

---

### `preprocess.ipynb` — Rigorous for Stage-1 General Preprocessing; Incomplete for QSVM

**Strengths:**
1. **Richer label structure** — three label columns supporting multi-class analysis (C4) and stratified sampling by attack category
2. **Superior stratified sampling** — `stratified_sample_for_qsvm()` oversamples rare U2R/R2L attacks to prevent them from disappearing in small subsamples; `data_preprocessing.py` has no equivalent
3. **Explicit distribution analysis** — label distribution plots, train/test attack-type overlap analysis — scientifically valuable for understanding dataset bias
4. **Attack-type generalization analysis** — identifies zero-shot test attacks (types only in test set) and documents them for the paper's Limitations section
5. **Correct OHE leakage prevention** — `reindex` alignment is identical to the script

**Weaknesses:**
1. **Latent label leakage defect** — `label` string column included in `feature_cols` (see §5.3, §9)
2. **Incomplete pipeline** — no SelectKBest, no PCA; output is not QSVM-compatible
3. **Wrong scaling range for quantum use** — [0, 1] instead of [0, π]
4. **float64 dtype** — unnecessary precision, doubles memory usage vs float32
5. **Different output directory** — `data/processed_data/` vs. `data/processed/` breaks `train_qsvm.py` compatibility
6. **CSV output format** — slower I/O and loses float32 precision compared to `.npy`
7. **Non-deterministic output volume** — many sample files at different sizes create ambiguity about which to use downstream

---

## 12. Discrepancy Summary Table

| Dimension | `data_preprocessing.py` | `preprocess.ipynb` | Impact |
|---|---|---|---|
| **Purpose** | QSVM-ready end-to-end pipeline | Stage 1 of multi-notebook workflow | Architectural |
| **Output shape (X)** | **(n, 4)** | **(n, ~85)** | CRITICAL — incompatible with QSVM |
| **Output format** | `.npy` (binary) | `.csv` (text) | HIGH — dtype/precision loss |
| **Output directory** | `data/processed/` | `data/processed_data/` | HIGH — breaks downstream scripts |
| **Feature range** | **[0, π]** ≈ [0, 3.14159] | **[0, 1]** | CRITICAL — wrong for quantum gates |
| **SelectKBest** | ✓ k=15, f_classif | ✗ Not applied | CRITICAL — ~70 noisy features retained |
| **PCA** | ✓ n_components=4 | ✗ Not applied | CRITICAL — features not reduced |
| **Scale timing** | After PCA (step 8) | After OHE (step 4) | HIGH — conceptually different |
| **Label encoding** | 1 binary column (int64) | 3 columns (binary/multi/category) | MEDIUM — richer in notebook |
| **Latent label leakage** | ✗ None | ✓ Present (`label` in feature_cols) | HIGH — potential catastrophic leakage |
| **Stratified sampling** | Basic (in `train_qsvm.py`) | Advanced (rare attack oversampling) | MEDIUM — notebook is better |
| **Attack-type analysis** | ✗ Not present | ✓ Full distribution + overlap analysis | LOW (exploratory value) |
| **Sanity assertions** | ✓ `assert` shape + range | ✓ Print-based checks | MEDIUM |
| **Determinism** | ✓ `random_state=42` in PCA | ✓ `random_state=42` in sampling | OK |
| **Transformer persistence** | ✓ 3 `.joblib` files | ✓ 1 `.joblib` (scaler only) | MEDIUM |
| **Whitespace NaN detection** | ✓ `na_values=[" ", ""]` | ✗ Not handled | LOW (no NaNs in NSL-KDD) |
| **Dtype efficiency** | float32 + int64 | float64 + int | LOW |

---

## Recommendations

### Immediate Actions

1. **Fix the latent leakage defect in `preprocess.ipynb`** — change the `feature_cols` filter in `preprocess_nsl_kdd()` to also exclude `EXCLUDED_COLS`. One line change.

2. **Standardize output directory** — either align `preprocess.ipynb` to write to `data/processed/` or update `train_qsvm.py` to support `data/processed_data/`. Currently the two cannot interoperate without manual path changes.

3. **Document the pipeline boundary** — `preprocess.ipynb` should prominently state at the top that it is Stage 1 of N, and that its outputs are NOT suitable for direct QSVM ingestion. The note is buried at the bottom of Cell 19.

### For the Research Paper

When reporting the ~65% vs. >80% accuracy gap, **it must be made explicit** that these numbers come from different model configurations (QSVM on 4D features vs. classical SVM on 85D features), not from the same model on different data. Presenting them as a direct comparison would be methodologically incorrect.

The correct experimental comparison is:
- QSVM on `data_preprocessing.py` output (4D, [0, π]) vs.
- Classical SVM on `data_preprocessing.py` output (4D, [0, π])

This isolates the quantum kernel's contribution and avoids confounding dimensionality with the kernel type.
