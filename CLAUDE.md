# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QSVM_NSLKDD is a Quantum Support Vector Machine (QSVM) applied to network intrusion detection using the NSL-KDD dataset. It demonstrates quantum kernel methods for binary classification (normal vs. attack traffic), benchmarked against classical RBF SVM.

## Commands

### Environment Setup
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt        # core
pip install -r requirements-dev.txt    # full dev environment
```

### Run Pipeline (sequential phases)
```bash
# Phase 1: Preprocess raw NSL-KDD → 4D quantum-ready features
python src/data_preprocessing.py

# Phase 2: Train QSVM + classical SVM baseline (~2+ hours, kernel O(N²))
python src/train_qsvm.py

# Phase 3: Evaluate, tune hyperparameters, generate reports
python src/evaluate_models.py

# Phase 4: Launch Streamlit dashboard (QEMS)
streamlit run src/app.py
```

### Run Notebooks
```bash
jupyter notebook notebooks/
```

## Architecture

### 4-Phase Pipeline

**Phase 1 — `src/data_preprocessing.py`**
Converts raw NSL-KDD (43 features, 125,973 samples) → 4D NumPy arrays in `data/processed/`. Steps:
1. Drop `difficulty_level` column; binarize 23-class labels to 0 (normal) / 1 (attack)
2. One-hot encode 3 categorical columns (protocol_type, service, flag) → ~85 features
3. `SelectKBest(k=15)` via ANOVA F-statistic
4. `PCA(n_components=4)` — **hard constraint driven by the 4-qubit circuit**
5. `MinMaxScaler([0, π])` — maps to quantum gate rotation angle domain
6. Saves arrays to `data/processed/*.npy` and fitted transformers to `models/*.joblib`

**Phase 2 — `src/train_qsvm.py`**
Trains quantum kernel SVM. Key design points:
- Stratified subsample to 2,500 train / 500 test (full 125K → 7.93B circuit evaluations; intractable)
- Quantum kernel: `ZZFeatureMap(4 qubits, reps=3, full entanglement)` + `ComputeUncompute` fidelity → K(x,z) = |⟨φ(x)|φ(z)⟩|²
- Simulator: `StatevectorSampler` (noiseless, exact)
- Pre-computes full Gram matrix (2500×2500), then fits `SVC(kernel='precomputed')`
- Also trains classical RBF SVM for comparison
- Outputs: `models/qsvm_model.pkl`, `models/csvm_model.pkl`

**Phase 3 — `src/evaluate_models.py`**
Hyperparameter tuning and visual evaluation:
- Only tunes classical SVM via `GridSearchCV` (QSVM tuning is intractable: 80 Gram matrix computations × ~75 min = ~100 hours)
- Primary metric is **Recall** (minimize false negatives in IDS context)
- Outputs confusion matrices and ROC curves to `reports/`
- Critical: QSVM uses precomputed kernel with integer support vector indices; must reconstruct the exact 2,500-sample training subsample

**Phase 4 — `src/app.py`**
Streamlit QEMS (Quantum-Enhanced Monitoring System) dashboard:
- `@st.cache_resource` loads full training data and reconstructs the quantum kernel object on startup
- Inference: maps a (1, 4) feature vector → (1, 2500) kernel row → `qsvm.predict()`
- UI: dark cybersecurity theme, sidebar packet controls, KPI metrics, real-time streaming demo
- IBM Quantum stub (shows cloud QPU integration path, falls back to local simulator)

### Key Design Constraints

| Constraint | Reason |
|---|---|
| PCA → exactly 4 components | Matches 4-qubit ZZFeatureMap circuit |
| Scale features to [0, π] | Maximizes Bloch sphere utilization for RY gates |
| SelectKBest k=15 before PCA | Reduces ~85 OHE features to 15 for cleaner PCA signal |
| Subsample 2,500 training points | O(N²) kernel computation; 125K is intractable locally |
| QSVM tuning disabled | Each Gram matrix recomputation ≈ 75 min on CPU |
| ZZFeatureMap reps=3 | Moderate depth avoids Barren Plateau while encoding feature products |

### Data Flow

```
data/raw/KDDTrain+.txt
        │
        ▼ Phase 1 (data_preprocessing.py)
data/processed/{X,y}_{train,test}.npy  +  models/{scaler,pca,selector}.joblib
        │
        ▼ Phase 2 (train_qsvm.py)
models/{qsvm,csvm}_model.pkl  +  data/processed/K_test_baseline.npy
        │
        ▼ Phase 3 (evaluate_models.py)
reports/{confusion_matrix,roc_curve}.png
        │
        ▼ Phase 4 (app.py)
Streamlit dashboard at localhost:8501
```

### Exploratory Notebooks (`notebooks/`)

- `01_EDA_and_PCA_Baseline.ipynb` — EDA, PCA scree plots, classical baseline
- `02_Quantum_Circuit_Architecture.ipynb` — ZZFeatureMap design, Hilbert space geometry
- `03_Evaluation_Metrics_Baseline.ipynb` — Confusion matrices, ROC, metric calculations

Src-level notebooks (`src/*.ipynb`) are experimental: `c3_noise_robustness.ipynb` (Conb3), `pca.ipynb`, `preprocess.ipynb`, `selectkbest_nslkdd.ipynb`.

### Streamlit Configuration

`.streamlit/config.toml` sets dark cybersecurity theme (primary color `#00d4ff`, monospace font, port 8501).
