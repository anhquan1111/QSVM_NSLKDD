# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**QSVM-IDS NISQ** — A scientific framework applying Quantum Support Vector Machines (QSVM) to network intrusion detection (NSL-KDD dataset) under real NISQ hardware constraints (4 qubits, high error rates). The goal is not just benchmarking but producing 6 verifiable scientific contributions (C1–C6) explaining *why* and *how* QSVM works for this task.

The pipeline: `NSL-KDD (41 features) → One-Hot Encoding (122D) → SelectKBest (20D) → PCA (4D) → MinMax[0,π] → QSVM (ZZFeatureMap, 4-qubit kernel)`

## Environment Setup

```bash
# Activate the virtual environment (already present at project root)
source venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Adds Jupyter, streamlit, gdown
```

## Running Notebooks

Notebooks are the primary executables. They must be run in this order for C1:

```bash
jupyter notebook notebooks/preprocess.ipynb           # OHE + zero-leakage validation
jupyter notebook notebooks/selectkbest_nslkdd.ipynb   # C1: SelectKBest K=20 optimization + ablation
jupyter notebook notebooks/pca.ipynb                  # C1: Pareto-optimal PCA n=4
jupyter notebook notebooks/c2_quantum_kernel_expressibility.ipynb  # C2: Kernel theory (ZZFeatureMap expressibility)
jupyter notebook notebooks/c3_kernel_geometry_v3.ipynb             # C3: Kernel geometry, KTA, decision boundaries
jupyter notebook notebooks/c4_robustness_distribution_shift.ipynb             # C4: Robustness under distribution shift
jupyter notebook notebooks/c5_confidence_calibration.ipynb                    # C5: Confidence calibration, adaptive binning & rare attacks
```

The `runners/` scripts (`run_c1_pipeline.py`, `run_c2_analysis.py`, `run_c3_geometry.py`) are empty stubs — not yet implemented.

## Architecture

### Six Scientific Contributions

| ID | Focus | Status |
|----|-------|--------|
| C1 | Two-stage dimensionality reduction (SelectKBest + Pareto PCA) with hardware cost | Complete |
| C2 | Quantum kernel expressibility — why ZZFeatureMap outperforms classical kernels | Complete |
| C3 | Kernel geometry + decision boundary analysis + ablation studies | Complete |
| C4 | Robustness under distribution shift (temporal, perturbation, class prior) | Complete |
| C5 | Confidence calibration + rare attack analysis (U2R, R2L < 1%) | Complete |
| C6 | Learning curves and sample complexity in low-data regime | Complete |

### Key Design Constraints

- **Zero-leakage contract**: All transformers (OHE, SelectKBest, PCA, MinMax) are `fit()` only on training data, then `transform()` on test. This is non-negotiable.
- **Hardware constraint**: Must stay at 4 features = 4 qubits for NISQ compatibility.
- **ZZFeatureMap config**: `reps=2`, `entanglement='full'`.
- **Validation**: 5-fold stratified cross-validation everywhere. Report mean ± std. Use McNemar test for classifier comparisons, Cohen's d for effect sizes.

### C1 Key Result

SelectKBest(K=20) + PCA(4D) → F1=0.8989 vs PCA(4D) alone → F1=0.8577. The K=20 → 4D path is validated empirically, not arbitrary.

### C5 Key Result (multi-run, 5 seeds — `c5_confidence_calibration_multirun.ipynb`)
QSVM duy trì ưu thế calibration trên rare attacks: **ECE_rare = 0.4503 ± 0.0725** (vs SVM-RBF ECE_rare = 0.5387 ± 0.1697, Linear = 0.5460 ± 0.0633) và đạt **AUC-PR rare cao nhất = 0.9306 ± 0.0136** (vs RBF 0.9168, Linear 0.8861). Phân loại tổng thể tương đương các baseline (**McNemar p̄ = 0.4911** — không bác bỏ H0). **Lưu ý quan trọng — sửa narrative cũ**: Cohen's d margin = **−0.1608 ± 0.3095** (dấu âm ⇒ margin của RBF *rộng hơn*, không phải QSVM tighter như báo cáo gốc trước multi-run). Kết luận đã được hiệu chỉnh: QSVM thắng ở **chất lượng xếp hạng (AUC-PR)** và **calibration (ECE)** trên rare attacks, *không* thắng ở độ rộng margin; Hybrid Ensemble vẫn được khuyến nghị nhờ complementarity về xếp hạng.

### C6 Key Result
QSVM outperformed classical baselines in the low-data regime (N=100 to 1000). At N=500, QSVM achieved a significantly higher mean decision margin (0.6538) compared to SVM-RBF (0.5070) on rare attacks (U2R/R2L). The calculated Cohen's d of 0.4043 confirms a statistically meaningful advantage in feature separation when training data is scarce.

### Pre-trained Artifacts

- `models/qsvm_model.pkl` — Trained QSVM (4-qubit ZZFeatureMap)
- `models/csvm_model.pkl` — Classical SVM baseline
- `models/feature_selector_k20.joblib` — SelectKBest transformer
- `models/pca_4components.joblib` — PCA transformer
- `models/scaler_minmax_pi.joblib` — MinMax scaler to [0, π]
- `models/qsvm_cache/` — Cached kernel matrices (expensive to recompute)
- `data/processed_data/` — C3 metrics (CSV) and visualizations (PNG)
- `data/processed_data/c5_results.json` — C5 metrics (ECE, McNemar, Cohen's d, AP)
- `reports/` — Output directory for high-quality visualizations (ROC Insets, Calibration Curves, Heatmaps)

### Source Files in `src/`

- `src/__init__.py` — Empty package marker
- `src/preprocess.py`, `src/features.py`, `src/metrics.py`, `src/quantum_core.py` — New modular source files (check current state before modifying)

## Dependencies

Core: `numpy==2.4.3`, `pandas==2.3.3`, `scikit-learn==1.8.0`, `qiskit==2.3.0`, `qiskit-machine-learning==0.9.0`, `scipy==1.17.1`, `matplotlib==3.10.8`, `seaborn==0.13.2`, `joblib==1.5.3`

## Important Context

- `PROJECT_BRIEF.md` contains the full research framework in Vietnamese — read it for contribution-level context before modifying any analysis logic.
- `docs/PROJECT_CONTEXT_QSVM_IDS.md` has detailed English-language project context.
- NSL-KDD raw data auto-downloads via `gdown` from Google Drive when notebooks run (no manual download needed if `gdown` is installed).
- Kernel matrix computation is very slow (hours on CPU); always check `models/qsvm_cache/` before recomputing.

## Language & Coding Guidelines

- **Code Logic:** All variable names, function names, and class names MUST be written in English following standard PEP 8 conventions.
- **Comments & Documentation:** ALL inline comments and docstrings within `.py` files MUST be written in Vietnamese.
- **Jupyter Notebooks:** If generating or modifying `.ipynb` files, ALL Markdown cells and text explanations MUST be written in Vietnamese.
- **File I/O Encoding:** ALL Python file operations (reading/writing `.json`, `.ipynb`, `.py`, etc.) MUST explicitly include `encoding='utf-8'` in the `open()` function. Windows defaults to `cp1252`, which causes `UnicodeDecodeError`/`UnicodeEncodeError` when processing Vietnamese characters in notebooks. Never use `open(file)` without specifying the utf-8 encoding.