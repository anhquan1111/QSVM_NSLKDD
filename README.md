# QSVM-IDS NISQ — Quantum Kernel SVM for Network Intrusion Detection

A scientific framework applying **Quantum Support Vector Machines (QSVM)** with the
**ZZ-FeatureMap** to network intrusion detection, under realistic **NISQ** hardware
constraints (4 qubits). The goal is not just benchmarking but explaining *when* and
*why* a quantum kernel helps — and *whether its predictions can be trusted* in
deployment.

```
NSL-KDD (41 feat) → One-Hot (122-d) → SelectKBest (20) → PCA (4-d)
                  → MinMax [0, π] → ZZ-FeatureMap (4 qubit, r=2, full) → SVM
```

## Two companion papers

| | Focus | Question | Location |
|---|---|---|---|
| **Paper 1** | Performance | *When does a NISQ QSVM beat classical SVMs?* | [`paper/paper1/`](paper/paper1/) (`main.tex`, `paper1.pdf` — submitted to IEEE) |
| **Paper 2** | Reliability | *Are QSVM's probabilistic alerts trustworthy vs. strong tabular learners?* | [`paper/paper2/`](paper/paper2/) (`main.tex` + `figs/`) |

**Paper 1 — regime-specific performance.** Hardware-aware Pareto pipeline (C1),
entanglement ablation via Kernel Target Alignment (C2/C3), distribution-shift stress
tests (C4), confidence calibration (C5), and a sample-complexity sweep (C6).

**Paper 2 — regime-specific reliability.** Calibration (ECE/Brier), rare-attack
reliability, prior-shift and temporal reliability, and Platt recalibration, against
**Random Forest** and **XGBoost** + SVM-RBF. QSVM is the **most calibrated** model on
rare attacks, on the balanced operating point, and in the low-data regime — while
trees rank well but are over-confident.

## Two datasets

| Dataset | Role | Notebooks |
|---|---|---|
| **NSL-KDD** | Primary benchmark (both papers) | [`notebooks/`](notebooks/) |
| **UNSW-NB15** | Cross-dataset generalization check | [`notebooks_unsw/`](notebooks_unsw/) |

## Repository layout

```
config.py              # Centralised paths & hyper-parameters
README.md              # This file
Tomtat.md              # Full Paper 2 summary (content + all results) — Vietnamese
requirements.txt       # Core dependencies

src/                   # Python modules
  preprocess.py        #   NSL-KDD preprocessing (OHE, zero-leakage)
  features.py          #   SelectKBest + Pareto PCA pipeline
  reliability.py       #   Paper 2: ECE/Brier/Platt, model factory  ← backbone of Paper 2

runners/               # Runnable scripts
  run_c1_pipeline.py            #   C1 dimensionality-reduction pipeline
  run_reliability_verify.py     #   Paper 2: rare-attack calibration (sanity check)
  run_reliability_recompute.py  #   Paper 2: prior-shift + low-data + Platt
  run_reliability_temporal.py   #   Paper 2: temporal (KDDTest-21)
  rebuild_p2_4model.py          #   Paper 2: regenerate all 4-model figures
  make_p2_schematic.py          #   Paper 2: pipeline schematic figure

notebooks/             # NSL-KDD experiments (see table below)
notebooks_unsw/        # UNSW-NB15 cross-dataset port (mirrors C1–C5)

paper/                 # All papers (IEEEtran LaTeX)
  paper1/              #   Paper 1 — main.tex + paper1.pdf
  paper2/              #   Paper 2 — main.tex + figs/

data/                  # data/processed_data (cleaned CSV, p2_*.json metrics),
                       # data/raw (auto-downloaded), data/unsw_nb15
models/  models_unsw/  # Trained models, kernel caches, result JSONs
reports/ reports_unsw/ # Publication figures (PNG)
results/c4_paper2/     # Paper 2 contribution-4 results (prior-shift, temporal)
outputs/               # Misc figure outputs (e.g. C2.5 shot-noise)
scripts/               # One-off utility / notebook-build scripts
docs/                  # Research documents + Overleaf guide
```

## NSL-KDD notebooks (`notebooks/`)

Run top-to-bottom for a fresh reproduction:

| Notebook | Contribution |
|---|---|
| `preprocess.ipynb` | One-hot encoding + zero-leakage validation |
| `selectkbest_nslkdd.ipynb` | **C1** — SelectKBest (K=20) optimisation + ablation |
| `pca.ipynb` | **C1** — Pareto-optimal PCA (n=4) |
| `c2_quantum_kernel_expressibility.ipynb` | **C2** — ZZ-FeatureMap expressibility |
| `c2_5_fidelity_vs_statevector_kernel_fixed.ipynb` | **C2.5** — shot-noise vs statevector sanity check |
| `c3_c_tuning_statevector.ipynb` | **C3** — regulariser (C) tuning |
| `c3_kernel_geometry_statevector_multirun.ipynb` | **C3** — kernel geometry, KTA, entanglement ablation |
| `c4_robustness_distribution_shift_multirun_fixed.ipynb` | **C4** — robustness (temporal / perturbation / prior shift) |
| `c5_confidence_calibration_multirun.ipynb` | **C5** — calibration + rare attacks (Paper 2 reuses its cache) |
| `c6_learning_curve_sample_complexity.ipynb` | **C6** — learning curve / sample complexity |
| `c4_paper2_reliability_complete_fixed.ipynb` | **Paper 2** — prior-shift + temporal reliability |

## UNSW-NB15 notebooks (`notebooks_unsw/`)

Cross-dataset port mirroring the NSL-KDD pipeline. The `*_C1` variants re-run C3/C4
with `C=1.0` (neutral) to remove a degeneracy artefact present at the tuned `C`; both
versions are kept for contrast.

`preprocess` → `selectkbest_unsw` → `pca_unsw` → `c_tuning_statevector` →
`c1_dimreduction_multirun` → `c2_quantum_kernel_expressibility` →
`c3_kernel_geometry_multirun_statevector(_C1)` →
`c4_robustness_multirun(_C1)` → `c5_confidence_calibration_multirun`.

> Finding: on UNSW-NB15 QSVM is **competitive but not dominant** (KTA RBF > QSVM,
> F1 tied) — the NSL-KDD advantage is regime/dataset dependent.

## Setup

```bash
python -m venv venv
source venv/Scripts/activate      # Windows Git Bash
pip install -r requirements.txt
```

## Reproducing Paper 2 (reliability)

```bash
python runners/run_reliability_verify.py      # rare-attack calibration (sanity: ECE_rare=0.4503)
python runners/run_reliability_recompute.py   # prior-shift + low-data + Platt
python runners/run_reliability_temporal.py    # temporal (KDDTest-21)
python runners/rebuild_p2_4model.py           # regenerate 4-model figures
```

Build the PDFs by uploading `paper/paper1/` or `paper/paper2/` to
[Overleaf](https://overleaf.com) (pdfLaTeX). A ready-to-upload archive is
provided at `paper/paper2/paper2.zip`.

## Key constraints

- **Zero-leakage**: all transformers `fit()` on train only, then `transform()` on test.
- **Hardware**: fixed at 4 features = 4 qubits for NISQ feasibility.
- **Validation**: multi-run (5 seeds), mean ± std, McNemar + Cohen's *d*.
- **Coding**: English identifiers (PEP 8), Vietnamese comments, `encoding='utf-8'`
  on every file I/O (see [`CLAUDE.md`](CLAUDE.md)).

## Dependencies

`numpy` · `pandas` · `scikit-learn` · `qiskit` 2.3 · `qiskit-machine-learning` 0.9 ·
`xgboost` · `scipy` · `matplotlib` · `seaborn` · `joblib`
