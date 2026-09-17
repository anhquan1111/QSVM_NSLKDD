# QSVM-IDS — Where is a quantum kernel actually worth its cost?

*[Tiếng Việt](README.vi.md)*

A controlled benchmark of **quantum kernel SVMs** (ZZ-FeatureMap) for network intrusion
detection under **NISQ** hardware constraints, on NSL-KDD and UNSW-NB15.

The question is not *"does quantum win?"* but ***"where does it win, and is that worth the
circuit budget?"*** — and the honest answer turned out to be: **mostly nowhere we can
detect, with one measurable exception.**

```
NSL-KDD (41 features) → one-hot (122D) → SelectKBest (K=20) → PCA (n*=4)
  → min–max [0, π] → ZZ-FeatureMap (4 qubits, r=2, full entanglement) → SVC (precomputed Gram)
```

---

## Headline result

Across **110 controlled comparisons** against six classical baselines (XGBoost, random
forest, SVM-RBF/poly2/linear, and an entanglement-free quantum control), paired within run
over ten runs with Holm correction:

| | Count |
|---|---|
| Favour the quantum kernel | **21** |
| Favour a classical baseline | **21** |
| Inconclusive | **68** |

There is **no general advantage**. What there *is* is structure worth reporting:

1. **An ordering that reverses with sample size.** Under the natural class prior the quantum
   kernel is second-worst at *N* = 100 and best at *N* = 10⁴; the paired difference against
   XGBoost, random forest and SVM-RBF changes sign between *N* = 2 000 and *N* = 5 000 in
   **6/6** baseline × tuning-arm combinations. Enriching rare attacks twelvefold removes the
   effect entirely — which is what the original protocol did.
2. **A selection rule that transfers.** A three-stage lexicographic rule (variance gate →
   kernel-target alignment gate → cheapest survivor by CNOT count) returns *n*\* = 4 on
   NSL-KDD and, with no threshold changed, *n*\* = 6 on UNSW-NB15, reproduced on **10/10**
   independent subsets.
3. **A measured boundary, with a mechanism.** Spending a larger feature budget forces a wider
   circuit, and widening destroys the kernel: at *K* = 80 (*n*\* = 8) **all 48** paired
   comparisons favour the classical model. The cause is visible in the Gram matrix — its
   off-diagonal dispersion decays about twice as fast for the ZZ map as for its
   entanglement-free control, matching the pairwise-versus-single-qubit phase-term counting,
   and it predicts macro-F₁ at *r* = +0.77. This happens under **exact, noiseless**
   simulation, so it is not a hardware-error effect.

---

## What is engineering-notable here

**The verification layer is the part worth reading.** Five audit scripts recompute every
published number from the raw artifacts and fail loudly on any mismatch:

```bash
python runners/audit_c4.py        # 100/100  every published statistic
python runners/audit_figures.py   #  36      every number plotted on a figure
python runners/audit_prose.py     # 134/134  every number written in the manuscript text
python runners/verify_lemma1.py   #  15/15   the kernel expansion, against the exact kernel
python runners/verify_noise10.py  #  40/40   the ten-run noise check, incl. Holm thresholds
python runners/check_latex.py     #          .tex structure, for machines without LaTeX
```

Design decision that matters: **`audit_c4.py` does not call the statistics functions in
`src/c4_pipeline.py`.** It reimplements them from `scipy` and compares. Using the code that
produced a number to check that number lets a shared bug through both times.

These audits **found four real bugs in our own revision code before publication**, one of
which had reported *n*\* = 5 instead of 4. They also caught five claims in the previously
submitted version that did not survive re-measurement — all five are documented and withdrawn
in the manuscript rather than quietly dropped.

**A closed-form kernel instead of gate-by-gate simulation.** Because the ZZ-FeatureMap is
diagonal in the computational basis after each Hadamard layer, the statevector has a closed
form and the whole Gram matrix follows from dense linear algebra. This runs **457×–763×
faster** than the Qiskit path and agrees with it to **1.3 × 10⁻¹⁵** — machine precision. That
speed-up is what made a sweep over two orders of magnitude in *N*, seven circuit widths and
two datasets tractable at all.

**Finite-shot error and backend-derived noise are applied as separate conditions**, never
folded into the main results, so sampling error can never be mistaken for the effect under
study.

---

## Verify it yourself in about a minute

```bash
git clone https://github.com/anhquan1111/QSVM_NSLKDD && cd QSVM_NSLKDD
uv sync                      # or: pip install -e .
python runners/audit_c4.py
```

No experiment re-run is needed — the audits read the released artifacts in `results/`.

> `audit_figures.py` reports **9 SKIP** on a fresh clone. That is not a failure: git does not
> preserve file modification times, so the "is this figure newer than its inputs?" provenance
> check loses its basis after cloning and reports SKIP rather than a false result. The 27
> checks that re-derive the plotted **numbers** still run in full. Run
> `python runners/make_paper1_figures.py` first if you want provenance covered too.

---

## Repository layout

```
src/c4_pipeline.py         Core: quantum kernel, representation, sampling protocol, statistics
src/reliability.py         Core for the companion paper (calibration)

runners/                   One script, one job
  ├── audit_*.py           Independent re-derivation of every published number
  ├── verify_lemma1.py     Numerical check of the kernel expansion
  ├── verify_noise10.py    Numerical check of the ten-run noise experiment
  ├── check_latex.py       .tex structure checker
  ├── run_c4.py            Training-set-size sweep (the main result)
  ├── run_c1_ksens.py      Dimension-selection rule across feature budgets
  ├── run_width_sweep.py   Circuit-width sweep
  ├── run_gram_concentration.py   Gram-matrix concentration measurement
  ├── run_hardware_kernel.py      Real-QPU execution path (dry-run verified)
  ├── make_paper1_figures.py      Generates the nine manuscript figures
  └── make_overleaf_zip.py        Packages the manuscript for Overleaf

configs/c4_protocol.json   Frozen protocol: seeds, N grid, nesting rule
data/    { nslkdd/, unsw/ }   raw + preprocessed
models/  { nslkdd/, unsw/ }   fitted transformers (joblib) + Gram matrices (npy)
results/ { nslkdd/, unsw/ }   JSON/CSV artifacts  ← the source of every number in the paper

paper/paper1/              Manuscript source (own README)
paper/paper2/              Companion paper
docs/                      Revision report, reviewer letter, supplementary-code index
```

### Where each result lives

| Result | File |
|---|---|
| 110-cell regime map | `results/nslkdd/regime_map_rows.csv` |
| Training-set-size sweep | `results/nslkdd/c4_revision/c4_pairwise_statistics_natural.csv` |
| K=80 / n=8 variant | `results/nslkdd/c4_revision/variant_K80n8/` |
| Dimension-selection rule | `results/nslkdd/c1_revision/c1_ksensitivity.json` |
| Gram-matrix concentration | `results/nslkdd/c1_revision/c1_gram_concentration.json` |
| Ten-run noise check | `results/nslkdd/c2_revision/c2_noise_validation_10run.csv` |
| UNSW-NB15 transfer | `results/unsw/c4_revision/` |

### Figures

Only the figures in **`paper/paper1/figs_revision/`** belong to the current version. Anything
under `results/*/c3_multirun/`, `results/*/c4_multirun/` or `data/*/processed_data/` was
produced by the **earlier** protocol — five seeds, asymmetric tuning, no tree ensembles — and
contradicts the manuscript. See `paper/paper1/figs_revision/MANIFEST.md` for per-figure
provenance.

> **On repository size.** Kernel-matrix caches (`results/*/{c3,c4}_revision/cache/`) are
> **not** tracked — 1.7 GB and regenerable. Notebooks recompute them on demand, and every
> audit above runs without them.

---

## Reproducing from scratch

```bash
uv sync
python runners/run_c4.py               # main result (a few hours)
python runners/make_paper1_figures.py
python runners/audit_c4.py             # confirm the numbers match
```

Environment: NumPy 2.4 · SciPy 1.17 · scikit-learn 1.8 · XGBoost 3.3 · Qiskit 2.3 with
qiskit-machine-learning 0.9 · Qiskit Aer 0.17.

---

## Papers

| | Focus | Status |
|---|---|---|
| **Paper 1** | Where is a quantum kernel worth its cost? | Major revision at **IEEE TETC**, resubmission due 13-10-2026 |
| **Paper 2** | Are QSVM alert probabilities trustworthy? | Submitted to **IJNM** (Wiley), 04-08-2026 |

Authors: Minh Tuan Pham, Phuc Hao Do, Nguyen Nang Hung Van, Quang Anh Nguyen, and
Quan Tran Anh Vo (corresponding author). Supported by The University of Danang — University
of Science and Technology, project T2026-02-10TN.

Detailed revision report and the point-by-point reviewer response:
[docs/BAO_CAO_REVISION.md](docs/BAO_CAO_REVISION.md) ·
[paper/paper1/response_letter.tex](paper/paper1/response_letter.tex)
