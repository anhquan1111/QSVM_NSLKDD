# UNSW-NB15 Cross-Dataset Transfer — Results and Manuscript Revision Plan

## 1. Scope

This document reports the **second-dataset study on UNSW-NB15** requested by Reviewer 1 and the
Associate Editor (**R1-2**, **AE-4**), and the extent to which the C4 findings on NSL-KDD
transfer to it.

Artifacts:

- `results/unsw/c4_revision/u1_c1_selection_unsw.json` — C1 selection rule applied to UNSW
- `results/unsw/c4_revision/u1_dimension_metrics.csv`, `u1_nstar_robustness.csv`
- `results/unsw/c4_revision/c4_per_run_unsw_natural_refit_per_N.csv` — **1,680 records**
- `results/unsw/c4_revision/c4_pairwise_statistics_natural.csv`
- `results/unsw/c4_revision/c4_rare_attack_natural.csv`, `c4_crossover_natural.csv`
- Data audit: `docs/revision/03_UNSW_AUDIT.md`

The submitted manuscript refers to a UNSW-NB15 study in supplementary material that reviewers
could not access, based on \(N_{\text{train}}=100\), five runs, four models, an untuned
\(C=1.0\), and a 100–300-sample test subset. **That study is superseded in full.** The revised
study uses the same protocol as the revised C4: 10 runs, 7 models, symmetric per-\((N,\text{run})\)
tuning, and the complete 82,332-sample test split.

---

# 2. Protocol

| | Submitted UNSW study | Revised |
|---|---|---|
| \(N_{\text{train}}\) | 100 | **100 → 10,000** (6 points) |
| Runs | 5 | **10** |
| Models | 4 | **7** (adds QSVM-Z, RF, XGBoost) |
| Hyperparameters | \(C=1.0\) fixed for all | **all 7 tuned at every \((N,\text{run})\)**, plus a `tuned_once` control arm |
| Embedding dimension | **\(n=4\) imported from NSL-KDD** | **\(n^{*}=6\), selected by running the C1 rule on UNSW** |
| Test set | 100–300-sample subset | **full 82,332** + fixed 300 |
| Class composition | rare-enriched to 20% (7× natural), inconsistent across N | **natural prior (2.86%), nested chain** |
| Statistics | mean ± std, McNemar | paired Δ, 95% CI, Wilcoxon, \(d_z\), Holm |

Total: 120 cells, 1,680 records, 2 h 11 min.

---

# 3. C1 transfers as a *procedure*, and selects a different operating point

This is the most important methodological result of the UNSW study and the direct answer to
**R3-1** (novelty).

## 3.1 Stage 0 — choosing K

Applying the manuscript's own elbow criterion (\(\delta = 0.01\) around the CV peak): the peak
proxy F1 is 0.8896 at \(K=100\), threshold 0.8796, so \(K^{*} = 35\).

## 3.2 Stages 1–3 — choosing n

| n | V(n) | 1/DBI | KTA | \(R_{\text{eff}}\) | offdiag std | Q(n) | CNOT |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0.7822 | 0.3959 | 0.1368 | 6.47 | 0.3148 | 0.0261 | 4 |
| 3 | 0.8366 | 0.4057 | 0.1470 | 11.38 | 0.2647 | 0.0717 | 12 |
| 4 | 0.8696 | 0.3948 | 0.1478 | 16.18 | 0.2516 | 0.1391 | 24 |
| 5 | 0.8892 | 0.3899 | 0.1689 | 21.28 | 0.2380 | 0.2283 | 40 |
| **6** | **0.9044** | 0.3840 | **0.1986** | 38.52 | 0.1905 | **0.3391** | **60** |
| 7 | 0.9188 | 0.3806 | 0.1625 | 53.54 | 0.1623 | 0.4717 | 84 |
| 8 | 0.9329 | 0.3758 | 0.1874 | 84.31 | 0.1455 | 0.6261 | 112 |
| 9 | 0.9444 | 0.3737 | 0.1808 | 95.99 | 0.1380 | 0.8022 | 144 |
| 10 | 0.9552 | 0.3711 | 0.1771 | 100.55 | 0.1346 | 1.0000 | 180 |

- \(V(n) \ge 0.85\) ⇒ \(F_V = \{4,\ldots,10\}\)
- \(\mathrm{KTA} \ge 0.95 \times 0.1986\) (attained at \(n=6\)) ⇒ \(F_{V,\mathrm{KTA}} = \{6\}\), a singleton
- \(\min Q(n)\) ⇒ \(\mathbf{n^{*} = 6}\)

## 3.3 Robustness of the selection

The rule was re-run on **ten independent KTA subsets** (seeds 42–51, \(N=300\), sampled exactly
as C1 does with `train_test_split` stratified on `attack_category`):

| \(\varepsilon\) | \(n^{*}=5\) | \(n^{*}=6\) |
|---:|---:|---:|
| 0.02 | 0 | **10/10** |
| 0.05 | 0 | **10/10** |
| 0.10 | 3 | 7 |

\(n=6\) has the highest KTA in the feasible region on **all ten** subsets (0.1903–0.2182). This
is *more* stable than the NSL-KDD selection, where \(\varepsilon = 0.02\) shifts \(n^{*}\) from
4 to 5.

## 3.4 Why this matters

All previous UNSW work in this project hard-coded `n_pca_fixed = 4`, i.e. imported NSL-KDD's
answer. Running the rule independently gives **6**.

> **C1 is a transferable procedure, not a hard-coded constant.** Two independent datasets pass
> through the same rule and receive two different operating points, each justified by its own
> data. The contribution lies in the *selection procedure*, not in the *configuration selected* —
> which is precisely what Reviewer 3 said was missing.

A corollary worth stating: every earlier UNSW result using \(n=4\) was **sub-optimal by the
project's own criterion**.

---

# 4. The crossover does **not** transfer

## 4.1 Learning curve (mean macro-F1, `tuned_per_N`, full 82,332-sample test)

| N | QSVM-ZZ | QSVM-Z | SVM-Lin | SVM-Poly2 | SVM-RBF | RF | XGB |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | 0.5953 | 0.6234 | 0.6255 | 0.5762 | 0.6289 | 0.6851 | **0.6855** |
| 500 | 0.6721 | 0.6545 | 0.6090 | 0.6371 | 0.6727 | **0.7134** | 0.7072 |
| 1000 | 0.6797 | 0.6775 | 0.6740 | 0.6681 | 0.6837 | **0.7255** | 0.7206 |
| 2000 | 0.6997 | 0.6812 | 0.5706 | 0.6507 | 0.6808 | **0.7342** | 0.7189 |
| 5000 | 0.7223 | 0.6800 | 0.5502 | 0.6819 | 0.6816 | **0.7547** | 0.7385 |
| 10000 | 0.7301 | 0.6852 | 0.5704 | 0.6675 | 0.6899 | **0.7612** | 0.7505 |

## 4.2 QSVM-ZZ against the tree ensembles (Holm-corrected)

| N | Δ vs XGB | Holm \(p\) | Verdict | Δ vs RF | Holm \(p\) | Verdict |
|---:|---:|---:|---|---:|---:|---|
| 100 | −0.0901 | 0.0039 | classical | −0.0898 | 0.0039 | classical |
| 500 | −0.0351 | 0.0039 | classical | −0.0413 | 0.0039 | classical |
| 1000 | −0.0410 | 0.0078 | classical | −0.0458 | 0.0078 | classical |
| 2000 | −0.0193 | 0.0840 | inconclusive | −0.0345 | 0.0078 | classical |
| 5000 | −0.0161 | 0.0195 | classical | −0.0323 | 0.0078 | classical |
| 10000 | −0.0204 | 0.0039 | classical | −0.0312 | 0.0039 | classical |

**No QSVM-favorable cell against either tree ensemble at any N.**

## 4.3 Side-by-side with NSL-KDD, identical protocol

| N | NSL-KDD Δ(ZZ − XGB) | UNSW Δ(ZZ − XGB) |
|---:|---:|---:|
| 1000 | −0.029 | −0.041 |
| 5000 | **+0.010** (QSVM-favorable) | −0.016 (classical) |
| 10000 | **+0.015** (QSVM-favorable) | −0.020 (classical) |

## 4.4 Not an artefact of per-N tuning

The `tuned_once` control arm (hyperparameters tuned once on a dedicated 2,000-sample tuning set,
then frozen — the analogue of C2's protocol) gives the same conclusion with a *wider* gap:

| N | 100 | 1000 | 5000 | 10000 |
|---|---:|---:|---:|---:|
| Δ(ZZ − XGB), `tuned_per_N` | −0.090 | −0.041 | −0.016 | −0.020 |
| Δ(ZZ − XGB), `tuned_once` | −0.101 | −0.044 | −0.043 | −0.041 |

> **The crossover is a dataset-dependent phenomenon, not a property of the quantum kernel.**

---

# 5. The entanglement result **does** transfer — and is stronger

| N | ZZ − Z | 95% CI | \(p\) | Verdict |
|---:|---:|---|---:|---|
| 100 | −0.0281 | [−0.0658, +0.0097] | 0.131 | inconclusive |
| 500 | +0.0177 | [−0.0063, +0.0417] | 0.193 | inconclusive |
| 1000 | +0.0021 | [−0.0196, +0.0239] | 0.846 | inconclusive |
| **2000** | **+0.0185** | [+0.0006, +0.0364] | **0.049** | **QSVM-favorable** |
| **5000** | **+0.0424** | [+0.0182, +0.0666] | **0.002** | **QSVM-favorable** |
| **10000** | **+0.0449** | [+0.0192, +0.0706] | **0.002** | **QSVM-favorable** |

This independently replicates the NSL-KDD finding that **the entanglement benefit is conditional
on the embedding basis being estimated from enough data**: negative or inconclusive at small N,
significantly positive from \(N \ge 2000\). On UNSW the effect at \(N=5000\) is **twice** the
NSL-KDD value (+0.042 vs +0.022).

QSVM-ZZ also beats the entire SVM family from \(N \ge 2000\). Against SVM-RBF: +0.019
(\(N=2000\), Holm \(p=0.037\)) → +0.041 (\(N=5000\), \(p=0.020\)) → +0.040 (\(N=10000\),
\(p=0.006\)).

---

# 6. The rare-attack analysis does **not** transfer — and must not be claimed

Recall on the rare subset (Worms ∪ Shellcode ∪ Backdoor ∪ Analysis, 1,682 test samples):

| N | QSVM-ZZ | QSVM-Z | SVM-RBF | RF | XGB |
|---:|---:|---:|---:|---:|---:|
| 1000 | 0.9598 | 0.9549 | 0.9485 | 0.9438 | 0.9460 |
| 10000 | 0.9828 | **0.9927** | 0.9687 | 0.9700 | 0.9782 |

Every model reaches 0.94–0.99, and the **signed margin on the rare subset is positive** for all
models (0.36–1.68) — the exact opposite of NSL-KDD, where it is negative for every model
(−0.20 to −0.98).

**Reason.** UNSW's four rare classes are all *attacks*, and the binary task is Normal vs Attack
with 68% of training data being attacks; predicting "attack" is almost always right. NSL-KDD's
U2R/R2L are attacks that *look like normal traffic*, which is what makes them hard.

> UNSW's rare subset does not exercise the same capability. Do not present it as evidence that
> the rare-attack finding generalises; state explicitly that the two rare classes differ in
> nature.

---

# 7. Data-integrity findings that must be declared

## 7.1 UNSW-NB15 contains heavy duplication

| | Rows | Unique signatures | Internal duplication |
|---|---:|---:|---:|
| Train | 175,341 | 92,357 | **47.3%** |
| Test | 82,332 | 48,353 | **41.3%** |

| | Test rows with an exact duplicate in train |
|---|---:|
| **UNSW-NB15** | **20,561 / 82,332 = 24.97%** |
| NSL-KDD | 610 / 22,544 = 2.71% |

Verified on the **raw** data (34 original features, before any preprocessing): 25.33% — matching
the processed figure, so this is a property of the dataset, not of our pipeline.

A single class accounts for most of it: **`Generic` has 40,000 rows but only 1,800 unique
signatures (95.5% duplication)**.

**Consequence to state in Limitations**: roughly a quarter of the UNSW test set is memorisable
from training. Every UNSW figure — ours and everyone else's — is inflated by this. It does not
invalidate model-to-model comparisons (all models are equally affected), but it must be declared.

## 7.2 The earlier UNSW subsets were rare-enriched and inconsistent

| Set | n | Rare fraction |
|---|---:|---:|
| Full train | 175,341 | **2.86%** |
| `multi_run/train_run{1..5}` | 100 | **20.00%** |
| `UNSW_Train_Sample1000` | 997 | **12.04%** |

Both a 7× enrichment and an inconsistency across N. The revised study uses the natural prior
with a strictly nested chain.

## 7.3 File ordering

`UNSW_Train_Cleaned.parquet` is **sorted by class** — the first 20,000 rows are all `Normal`.
Any positional slice produces a single-class sample. All sampling must be randomised and
stratified.

---

# 8. What transfers and what does not

| C4 finding on NSL-KDD | Transfers to UNSW? |
|---|---|
| Crossover vs tree ensembles at \(N\approx2000\text{–}5000\) | ❌ **No** — classical wins at every N |
| Entanglement benefit requires sufficient data | ✅ **Yes**, and twice as strong |
| QSVM-ZZ beats the SVM family at large N | ✅ **Yes** (from \(N\ge2000\)) |
| Rare-attack: negative signed margins, hard minority classes | ❌ **No** — UNSW's rare classes are easy |
| C1 is a transferable selection procedure | ✅ **Yes** — but selects \(n^{*}=6\), not 4 |

This is the shape a *regime-specific benchmark* should have: a clear boundary between what is
general (the role of entanglement, the transferability of the selection procedure) and what is
dataset-specific (the crossover, the difficulty of the minority classes).

---

# 9. Reviewer resolution

| Item | Status |
|---|---|
| **R1-2 / AE-4** — second modern IDS dataset | ✅ **Resolved** — full protocol parity with NSL-KDD, complete test split, 10 runs |
| **R1-10** — supplementary inaccessible | ✅ Artifacts are in the repository, not an unreachable supplement |
| **R3-1** — low novelty | ✅ **Strongly addressed** — C1 demonstrated to be a procedure that selects differently on a different dataset |
| **R1-4 / AE-1** — overclaiming | ✅ **Strongly supported** — our own second dataset refutes the crossover generalisation |
| **R1-3 / R4-5** — asymmetric tuning | ✅ 7 models tuned at every \((N,\text{run})\), plus a `tuned_once` control |
| **R2-3** — thin statistics | ✅ 10 runs, CI, Wilcoxon, \(d_z\), Holm |

---

# 10. Manuscript guidance

## 10.1 Replace the UNSW paragraph entirely

The submitted text says the UNSW study "ties SVM-LIN on absolute F1 but retains its advantage
under prior shift". That was based on \(N=100\), five runs, four models and an untuned \(C\).
It should be replaced by the results above.

## 10.2 Suggested wording

> We repeat the full C4 protocol on UNSW-NB15. Applying the C1 selection rule independently
> selects a six-qubit embedding (\(K^{*}=35\), \(n^{*}=6\)), stable across ten KTA resamples,
> rather than the four-qubit configuration selected on NSL-KDD — evidence that the procedure,
> not the configuration, is the transferable contribution. On UNSW-NB15 the sample-complexity
> crossover observed on NSL-KDD does **not** appear: gradient-boosted trees and random forests
> remain significantly better than QSVM-ZZ at every training size up to \(N=10{,}000\). The
> entanglement ablation, by contrast, replicates and strengthens: QSVM-ZZ exceeds the matched
> non-entangling control by \(+0.045\) macro-F1 at \(N=10{,}000\) (\(p=0.002\)), and exceeds every
> SVM baseline from \(N\ge2000\). We therefore report the crossover as a dataset-specific regime
> boundary rather than a property of the quantum kernel.

## 10.3 Do / do not

| Do not write | Write instead |
|---|---|
| "the regime-specific picture generalises" | "the entanglement result generalises; the crossover does not" |
| "QSVM-ZZ is competitive on UNSW" | "QSVM-ZZ beats the SVM family from \(N\ge2000\) but remains significantly below RF and XGBoost at every N" |
| "rare-attack findings hold on UNSW" | "UNSW's rare classes are not comparably hard (recall 0.94–0.99 for all models), so the rare-attack analysis does not transfer" |
| "\(n=4\) is the NISQ-feasible choice" | "the selection rule yields \(n=4\) on NSL-KDD and \(n=6\) on UNSW-NB15" |

## 10.4 Mandatory Limitations additions

1. UNSW-NB15 contains 47% internal duplication and 25% of test rows have an exact duplicate in
   training; all UNSW results are inflated by this.
2. \(n^{*}=6\) raises the two-qubit cost from 24 to 60 CNOTs — still NISQ-scale, but the
   hardware-cost comparison across datasets is not like-for-like.
3. UNSW-NB15 has no temporal split, so the temporal-shift regime of C3 has no analogue here.
4. Noise validation was not repeated on UNSW; the C2 backend-derived noise study on NSL-KDD is
   the only hardware-realism evidence.

---

# 11. Not done, and why

| Skipped | Reason |
|---|---|
| Noise validation on UNSW | C2 covers it on NSL-KDD; repeating costs pages without answering a new objection |
| Temporal shift | UNSW-NB15 has no time-ordered split analogous to KDDTest-21 |
| Calibration / ECE | Belongs to Paper 2; repeating would duplicate |
| CatBoost / deep tabular | The 7-model family is held fixed across C2/C3/C4 for comparability |
| `matched` (rare-enriched) regime | The scientific question for UNSW is whether the crossover transfers, which lives in the natural regime |
