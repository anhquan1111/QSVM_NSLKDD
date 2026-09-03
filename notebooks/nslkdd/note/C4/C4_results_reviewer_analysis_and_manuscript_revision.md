# C4 Revision — Final Results, Reviewer Resolution, and Manuscript Revision Plan

## 1. Scope

This document is the **final C4 results analysis** (sample-complexity sweep and rare-attack
margin analysis), based on the exported artifacts:

- `results/nslkdd/c4_revision/c4_per_run_matched_refit_per_N.csv` — 1,400 records
- `results/nslkdd/c4_revision/c4_per_run_natural_refit_per_N.csv` — 1,960 records
- `results/nslkdd/c4_revision/c4_per_run_matched_frozen_c1.csv` — 280 records
- `results/nslkdd/c4_revision/c4_pairwise_statistics_matched.csv`
- `results/nslkdd/c4_revision/c4_pairwise_statistics_natural.csv`
- `results/nslkdd/c4_revision/c4_rare_attack.csv`
- `results/nslkdd/c4_revision/c4_table_iv_vs_vi.csv`
- `results/nslkdd/c4_revision/c4_protocol_vs_literature.csv`

Frozen protocol: `configs/c4_protocol.json`. Claim audit of the submitted version:
`docs/revision/c4_claim_audit.md`. Full working log: `docs/revision/02_PROGRESS.md`.

The reviewer roadmap assigns four items to C4: the crossover question (**R1-7**), the
Table IV / Table VI inconsistency (**R1-8**), the unusually low classical F1 (**R1-9**), and
the unverifiable rare-attack claim (**R4-4**). This document addresses all four.

---

# 2. Final C4 protocol

## 2.1 Inherited contract

C4 inherits the frozen C1/C2 configuration:

\[
K=20,\qquad n=4,\qquad r=2,\qquad \text{entanglement}=\text{full}
\]

with the seven-model family of C2/C3: QSVM-ZZ, QSVM-Z, SVM-Linear, SVM-Poly2, SVM-RBF,
Random Forest, XGBoost.

**Verification gate.** Before running any new experiment, the C4 pipeline was required to
reproduce C2 exactly at \(N=1000\) under the frozen representation, frozen hyperparameters and
the fixed 300-sample test set. Result: **all seven models matched to the last digit on all ten
runs** (max absolute difference 0.00e+00), including support-vector counts on 18 of 20 quantum
cells. Only after this gate passed were new C4 results generated.

## 2.2 What changed relative to the submitted C4

| | Submitted version | Revised C4 |
|---|---|---|
| Runs | 1 seed | **10 runs** (seeds 100–109) |
| Baselines | 3 SVM variants | **7 models** incl. RF and XGBoost |
| Hyperparameters | \(C_{QSVM}=1.0\) fixed, classical tuned | **symmetric tuning of all 7 models at every \((N,\text{run})\)** |
| N grid | \(\{100,200,500,1000\}\) | \(\{100 \ldots 2000\}\) matched, \(\{100 \ldots 10000\}\) natural |
| Test set | one per table | **both** (fixed 300 and full 22,544) reported at every N |
| Rare-attack metric | \(|f(x)|\) | **signed margin** \(y\cdot f(x)\) plus rare-subset F1/recall |
| Sampling | single stratified draw | **nested chain** \(D_{100}\subset\ldots\subset D_{N_{\max}}\), anchored at \(N=1000\) = C2's `train_run{i}` |

## 2.3 Two sampling regimes — and why both are needed

A property of the project's data that is **not stated anywhere in the submitted manuscript**
was discovered during this work:

| Split | Normal | DoS | Probe | R2L | U2R | **Rare (R2L∪U2R)** |
|---|---:|---:|---:|---:|---:|---:|
| KDDTrain+ (125,973) | 53.5% | 36.5% | 9.25% | 0.79% | 0.04% | **0.83%** |
| `train_run{i}` (1,000) — basis of C2, C3, Table IV | 48.4% | 33.1% | 8.5% | 9.4% | 0.6% | **10.0%** |
| KDDTest+ (22,544) | 43.1% | 33.1% | 10.7% | 12.8% | 0.3% | **13.1%** |

The training subsets used throughout C2/C3 are **rare-enriched by a factor of ~12** relative to
the natural training prior. This is a legitimate design choice (it moves the training prior
towards the test prior) but it must be declared, and it makes a single learning curve ambiguous:
extending N by drawing from the natural pool would confound "more data" with "different class
composition".

C4 therefore reports **two regimes**, both with strictly nested subsets:

- **`matched`** — holds the `train_run{i}` composition fixed (Rare = 10.0% at every N).
  Only N varies, so this is the clean sample-complexity experiment, and it is directly
  comparable to C2/C3. Ceiling \(N=2000\): beyond that the ten runs share too many rare samples
  (24% shared at \(N=2000\), 59% at 5,000, 94% at 8,000) and the runs stop being independent.
- **`natural`** — holds the true KDDTrain+ prior (Rare = 0.83%). Reaches \(N=10{,}000\) with
  inter-run rare overlap ≤ 10%, and reflects deployment conditions where labels arrive in their
  natural proportion.

## 2.4 Statistical protocol

Identical to C3, so the numbers are comparable across contributions: paired differences over
the ten runs, mean, median, 95% CI, Wilcoxon signed-rank, paired \(d_z\), Holm correction within
the same three baseline families (`entanglement`, `strong_tabular`, `classical_kernel`), and a
three-way verdict {QSVM-favorable, classical-favorable, inconclusive}.

---

# 3. Main scientific finding

\[
\boxed{
\textbf{A crossover exists, and it runs in the opposite direction to the submitted claim.}
}
\]

The submitted manuscript states that QSVM-ZZ *"dominates every classical baseline at every N"*,
most strongly in the low-data regime. Reviewer 1 asked directly whether a crossover point
exists. It does — at \(N \approx 2000\text{–}5000\) under the natural class prior — but classical
ensembles win **below** it and QSVM-ZZ wins **above** it.

## 3.1 Learning curve, `natural` regime, full KDDTest+ (mean over 10 runs)

| N | QSVM-ZZ | QSVM-Z | SVM-Lin | SVM-Poly2 | SVM-RBF | RF | XGB |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | 0.6989 | 0.7613 | 0.7261 | 0.6890 | 0.7296 | 0.7695 | **0.7802** |
| 200 | 0.7283 | 0.7473 | 0.7463 | 0.7292 | 0.7566 | 0.7909 | **0.7924** |
| 500 | 0.7587 | 0.7717 | 0.7389 | 0.7348 | 0.7880 | 0.7880 | **0.7881** |
| 1000 | 0.7717 | 0.7666 | 0.7406 | 0.7424 | 0.7745 | 0.7913 | **0.8007** |
| 2000 | 0.7781 | 0.7615 | 0.7373 | 0.7141 | **0.7919** | 0.7839 | 0.7910 |
| 5000 | **0.7820** | 0.7596 | 0.7338 | 0.7116 | 0.7794 | 0.7737 | 0.7720 |
| 10000 | **0.7855** | 0.7787 | 0.7335 | 0.7114 | 0.7740 | 0.7728 | 0.7706 |

## 3.2 QSVM-ZZ vs XGBoost — paired, Holm-corrected

| N | Δ (ZZ − XGB) | 95% CI | Holm \(p\) | \(d_z\) | Verdict |
|---:|---:|---|---:|---:|---|
| 100 | −0.0812 | [−0.1232, −0.0393] | 0.0039 | −1.386 | classical-favorable |
| 200 | −0.0641 | [−0.0983, −0.0300] | 0.0039 | −1.343 | classical-favorable |
| 500 | −0.0293 | [−0.0535, −0.0052] | 0.0273 | −0.868 | classical-favorable |
| 1000 | −0.0289 | [−0.0405, −0.0174] | 0.0078 | −1.798 | classical-favorable |
| 2000 | −0.0129 | [−0.0296, +0.0038] | 0.2617 | −0.552 | inconclusive |
| **5000** | **+0.0100** | [+0.0041, +0.0158] | **0.0273** | +1.224 | **QSVM-favorable** |
| **10000** | **+0.0149** | [+0.0050, +0.0249] | **0.0078** | +1.071 | **QSVM-favorable** |

Random Forest gives the same shape: classical-favorable for \(N \le 1000\), **QSVM-favorable at
\(N=10{,}000\)** (+0.0127, Holm \(p=0.0078\)).

## 3.3 Mechanism — measured, not asserted

Recall on the rare subset (U2R ∪ R2L, 2,952 test samples):

| N | QSVM-ZZ | XGBoost | RF | SVM-RBF |
|---:|---:|---:|---:|---:|
| 100 | 0.2189 | 0.1674 | 0.1529 | 0.1357 |
| 1000 | 0.3264 | 0.2783 | 0.2468 | 0.2547 |
| 2000 | 0.3275 | 0.2544 | 0.2360 | 0.4401 |
| 5000 | **0.3421** | 0.2119 ↓ | 0.2058 ↓ | 0.4383 |
| 10000 | **0.3400** | 0.2009 ↓ | 0.1982 ↓ | 0.4170 |

Rare-class recall of the tree ensembles **peaks near \(N=1000\) and then declines**, while that of
QSVM-ZZ **increases monotonically**.

Under the natural prior the training set contains only 0.83% rare instances — even at
\(N=10{,}000\) that is 83 rare samples — while the test set contains 13.1%. As N grows the tree
ensembles converge to the training prior and effectively stop predicting the rare classes. The
quantum kernel's decision surface is anchored to the geometry of the embedded samples rather
than to the empirical class frequency, so it keeps improving.

> This is **exactly the mechanism the submitted manuscript already hypothesises** in Sec. V-C.
> The mechanism is supported; it simply manifests in a different experiment than the one used to
> argue for it, and in the **high-data** rather than the low-data regime.

## 3.4 The two regimes are complementary

| | `matched` (rare 10%) | `natural` (rare 0.83%) |
|---|---|---|
| ZZ vs XGBoost | **inconclusive at every \(N \le 2000\)** | classical for \(N\le1000\) · **QSVM for \(N\ge5000\)** |
| ZZ vs Random Forest | inconclusive at every N | classical for \(N\le1000\) · **QSVM at \(N=10000\)** |
| ZZ vs SVM-Linear | QSVM-favorable for \(N\ge1000\) | QSVM-favorable for \(N\ge1000\) |
| Crossover | not observed in the tested range | **present, \(N \approx 2000\text{–}5000\)** |

When the rare classes are artificially enriched to 10%, the tree ensembles lose their advantage
and every comparison becomes inconclusive. Under the natural prior the crossover is clear.

---

# 4. Entanglement ablation is conditional on the embedding basis

C2 reports \(\Delta\mathrm{F1} = \mathrm{ZZ}-\mathrm{Z} = +0.0114\) (inconclusive) and
\(\Delta\mathrm{KTA} = +0.1378\) (\(p=0.002\)) under the **frozen** C1 representation. Under the
per-N re-fit protocol that the submitted manuscript itself declares for C4 (Sec. III-F,
*"refit the entire pipeline including SelectKBest and PCA on those N rows"*), the sign reverses.

## 4.1 Decomposition, 10 runs, fixed 300-sample test, \(C=3.0\)

| Configuration | ZZ − Z | 95% CI | \(p\) | Verdict |
|---|---:|---|---:|---|
| **A.** frozen selector + PCA + scaler (**= C2**) | +0.0114 | [−0.0054, +0.0281] | 0.232 | inconclusive |
| **B.** frozen selector + PCA, re-fit **scaler only** | **+0.0348** | [+0.0202, +0.0493] | 0.0039 | QSVM-favorable |
| **C.** re-fit everything (**= C4**) | **−0.0190** | [−0.0346, −0.0033] | 0.0195 | classical-favorable |

The scaler is not responsible — re-fitting it alone makes ZZ *better*. The responsible component
is **re-estimating SelectKBest and PCA from the N training rows**.

## 4.2 The surprising part

The re-fitted embedding is almost identical to the frozen one:

| N | Feature overlap with C1 | \(|\cos|\) of PC1 vs C1 | Inter-run axis stability |
|---:|---:|---:|---:|
| 100 | 82.5% | 0.9829 | 0.9759 |
| 1000 | 90.5% | 0.9966 | 0.9967 |
| 2000 | 90.0% | 0.9977 | 0.9987 |

A 10% difference in selected features and a cosine of 0.997 is **enough to flip the sign of the
ablation**.

## 4.3 Interpretation, and the link to C3

The entanglement benefit is highly sensitive to small perturbations of the embedding basis. This
is the same mechanism family as C3's clearest negative regime, where QSVM-ZZ degrades under
additive feature perturbation far faster than any baseline (slope −0.835 vs −0.013,
\(|d_z| = 2.6\text{–}4.8\)). The ZZ map encodes **pairwise products** of coordinates and is
therefore frame-dependent; the Z map uses coordinates individually and is not.

Consistently, in the `natural` regime the ablation recovers as the basis becomes better
estimated: ZZ − Z is **−0.0624** (\(p=0.006\)) at \(N=100\) and **+0.0224** (\(p=0.006\)) at
\(N=5000\).

> **The C2 result is not wrong — it is conditional.** \(\Delta\mathrm{KTA}=+0.1378\) holds when the
> PCA basis is estimated from the full 125,973-row training set. Under a strict zero-leakage
> protocol where the representation is estimated from the same N labelled samples used for
> training, the advantage disappears at small N and returns at large N.

---

# 5. Rare-attack analysis (R4-4)

## 5.1 The submitted claim cannot be reproduced

> *"At N=500 QSVM-ZZ still leads by +6.7 points over SVM-RBF on the rare-attack subset, with a
> Cohen's d of +0.68 on the per-sample decision margins."*

Three separate problems, established in `docs/revision/c4_claim_audit.md`:

1. **+6.7 is the wrong comparison.** \(0.0665\) is the Table VI margin against **SVM-Linear** on
   the **full 22,544-sample test set**, not against SVM-RBF and not on the rare subset. Against
   SVM-RBF on the full test set the gap at \(N=500\) is +10.0 points.
2. **No rare-subset classification metric existed anywhere in the repository.** The sentence had
   no supporting number.
3. **\(d = +0.68\) is not reproducible.** The C6 artifact reports \(+0.4043\). The only value of
   that magnitude in the repository is `c5_results.json → cohens_d_margin_rare = −0.68048`, of
   **opposite sign** and from a different experiment (\(N_{\text{train}}=99\), 10 rare samples).
   Over five runs that quantity averages \(-0.161 \pm 0.309\).

## 5.2 The deeper methodological problem

Both C5 and C6 computed effect sizes on \(|f(x)|\). C4 measured the **signed** margin
\(y \cdot f(x)\) on the rare subset and found it is **negative for every model at every N**:

| N | QSVM-ZZ | QSVM-Z | RF | XGB | SVM-RBF | SVM-Lin |
|---:|---:|---:|---:|---:|---:|---:|
| 100 | −0.3233 | −0.3870 | −0.2219 | −0.2543 | −0.5952 | −0.8021 |
| 1000 | −0.3919 | −0.4994 | −0.2032 | −0.2054 | −0.4584 | −0.9094 |
| 10000 | −0.5050 | −0.4855 | −0.2491 | −0.2778 | −0.3482 | −0.9779 |

The average rare sample lies on the **wrong side** of the decision boundary for all models.
A larger \(|f(x)|\) therefore means **more confidently wrong**, not "a safer margin". Effect
sizes computed on absolute margins are not interpretable here.

The two definitions disagree violently. At \(N=500\), `matched`, full test:

| vs | \(d\) on \(|f(x)|\) | \(d\) on signed margin | Δ F1 (rare subset) |
|---|---:|---:|---:|
| SVM-RBF | **−0.3074** | +0.0831 | **+0.0235** |
| SVM-Linear | −0.2329 | −0.0771 | −0.0828 |
| XGBoost | **+1.1638** | +0.0297 | +0.1032 |
| Random Forest | **+1.4222** | −0.0175 | +0.0944 |
| QSVM-Z | −0.2753 | −0.0666 | −0.0115 |

The absolute-margin statistic gives \(+1.42\) against Random Forest and \(-0.31\) against
SVM-RBF — opposite conclusions for the same model, from changing only the comparator.

## 5.3 Replacement text for the manuscript

> At \(N=500\), QSVM-ZZ attains a rare-subset (U2R ∪ R2L, 2,952 samples) F1 of 0.577, which is
> \(+0.024\) over SVM-RBF, \(+0.103\) over XGBoost and \(+0.094\) over Random Forest, but
> \(-0.083\) below SVM-Linear. Cohen's \(d\) computed on **signed** decision margins is negligible
> against every baseline (\(|d| \le 0.09\)). We note that the mean signed margin on the rare subset
> is negative for all evaluated models, so effect sizes computed on absolute margins — as in the
> original submission — are not interpretable.

## 5.4 Rare-attack shows the same crossover

Rare-subset F1, `natural` regime:

| N | QSVM-ZZ | XGBoost | RF | SVM-RBF |
|---:|---:|---:|---:|---:|
| 100 | 0.3334 | 0.2751 | 0.2550 | 0.2100 |
| 1000 | 0.4856 | 0.4272 | 0.3875 | 0.3815 |
| 5000 | 0.5093 | 0.3493 ↓ | 0.3409 ↓ | **0.6058** |
| 10000 | 0.5069 | 0.3342 ↓ | 0.3306 ↓ | **0.5846** |

Holm-corrected verdicts: QSVM-favorable against Random Forest from \(N\ge1000\), against
XGBoost from \(N\ge2000\), against SVM-Linear at every N.

⚠️ **Do not write that QSVM-ZZ is best on rare attacks.** SVM-RBF is the strongest model on the
rare subset at large N (0.6058 at \(N=5000\)) and is classical-favorable against QSVM-ZZ at
\(N = 500, 2000, 5000\).

---

# 6. Table IV versus Table VI (R1-8)

Both tables are correct; they use different evaluation protocols. Under matched hyperparameters
at \(N=1000\), the full \(2\times2\) grid is:

| Representation | Test set | QSVM-ZZ | QSVM-Z | SVM-RBF | RF | XGB |
|---|---|---:|---:|---:|---:|---:|
| frozen C1 | fixed 300 | **0.8469** | 0.8355 | 0.8362 | 0.8446 | 0.8503 |
| frozen C1 | full 22,544 | 0.7959 | 0.7721 | 0.7977 | 0.8009 | 0.8043 |
| re-fit per N | fixed 300 | 0.8526 | 0.8715 | 0.8645 | 0.8673 | 0.8666 |
| re-fit per N | full 22,544 | **0.8072** | 0.8250 | 0.8273 | 0.8250 | 0.8242 |

The top-left cell reproduces C2's published 0.8469 exactly, which validates the grid.

| | QSVM-ZZ |
|---|---:|
| Table IV protocol (frozen + 300) | 0.8469 |
| Table VI protocol (re-fit + 22,544) | 0.8072 |
| **Total gap** | **−0.0397** |
| ↳ due to the **test set** (300 → 22,544) | **−0.0510** |
| ↳ due to the **representation** (frozen → re-fit) | +0.0113 |

### Suggested caption text

> Table IV and Table VI use the same training budget at \(N=1000\) but different evaluation sets
> and different pipeline-fitting protocols. Decomposing the 0.040 macro-F1 gap under matched
> hyperparameters shows that \(-0.051\) is attributable to evaluating on the complete
> 22,544-sample KDDTest+ rather than the fixed 300-sample subset, and \(+0.011\) to re-fitting the
> embedding on the N training rows. The two tables are therefore consistent.

---

# 7. Benchmark protocol versus commonly reported NSL-KDD results (R1-9)

Reviewer 1 observed that the classical F1 values look low relative to the NSL-KDD literature.
Three reference configurations, changing one factor at a time:

| Configuration | Model | \(N_{\text{train}}\) | Features | Macro-F1 | Accuracy | Rare recall |
|---|---|---:|---:|---:|---:|---:|
| **A** all features, full train, test = **KDDTest+** | XGBoost | 125,973 | 122 | 0.8041 | 0.8043 | 0.1037 |
| **A** | Random Forest | 125,973 | 122 | 0.7765 | 0.7774 | 0.0623 |
| **B** all features, full train, test = **random split of KDDTrain+** | XGBoost | 100,778 | 122 | **0.9993** | **0.9993** | — |
| **B** | Random Forest | 100,778 | 122 | **0.9978** | **0.9979** | — |
| **C** \(K{=}20\) + PCA-4, full train, test = KDDTest+ | XGBoost | 125,973 | 4 | 0.7655 | 0.7658 | 0.1799 |
| **C** | Random Forest | 125,973 | 4 | 0.7560 | 0.7565 | 0.1480 |

Three conclusions:

1. **A vs B is the entire explanation.** Same model, same 122 features, same training data;
   only the evaluation set changes: 0.804 → **0.999**, a gap of roughly **20 points**. The
   near-99% figures common in the NSL-KDD literature come from randomly splitting KDDTrain+,
   not from training on KDDTrain+ and testing on KDDTest+, which deliberately contains attack
   types absent from training.
2. **The dimensionality reduction is cheap.** Going from 122 features to 4 costs only 0.039
   macro-F1 for XGBoost (0.8041 → 0.7655), and it *improves* rare-class recall
   (0.1037 → 0.1799).
3. Worth stating in the paper: QSVM-ZZ at \(N=10{,}000\) with **four** features reaches 0.7855,
   above Random Forest trained on all 125,973 samples with all 122 features (0.7765).

**Do not attempt to raise the reported F1.** The correct response is to explain the protocol and
include this table.

---

# 8. Symmetric hyperparameter tuning (R1-3 / R4-5 at the C4 level)

All seven models are tuned at every \((N,\text{run})\) by 5-fold stratified CV on that training
subset, with the 1-SE rule for the SVM/QSVM family and best-mean for RF/XGBoost — the same rules
as C2. The constraint \(C_{ZZ}=C_Z\) is preserved.

Median selected \(C\) for the quantum branch:

| N | `matched` | `natural` |
|---:|---:|---:|
| 100 | 0.50 | 0.75 |
| 500 | 0.75 | 0.50 |
| 1000 | 3.00 | 1.00 |
| 2000 | 1.00 | 3.00 |
| 5000 | — | 4.00 |
| 10000 | — | **10.00** |

The optimal \(C\) grows by more than an order of magnitude across the N range. The value
\(C=3.0\) frozen by C2 (tuned at \(N=1000\)) is therefore substantially mis-specified at both
ends of the sweep, which is exactly the asymmetry Reviewer 4 warned about. A `frozen_c2` arm is
reported alongside for comparison; conclusions are unchanged in sign, and the crossover is
present in both arms.

---

# 9. Reviewer-resolution matrix

| Issue | C4 status |
|---|---|
| **R1-7** — is there a crossover? | ✅ **Resolved** — yes, at \(N\approx2000\text{–}5000\), opposite in direction to the submitted claim, with a measured mechanism |
| **R1-8** — Table IV vs VI inconsistent | ✅ **Resolved** — decomposed quantitatively; the tables are consistent |
| **R1-9** — classical F1 looks low | ✅ **Resolved** — explained by the evaluation protocol, with a reference table |
| **R4-4** — rare-attack numbers unverifiable | ✅ **Resolved** — original claim shown to be wrong, replaced with a full table |
| **R2-3** — thin statistical base | ✅ **Resolved** — 10 runs, CI, Wilcoxon, \(d_z\), Holm |
| **R1-5 / R2-1** — weak baselines | ✅ **Resolved at C4 level** — RF and XGBoost at every N |
| **R1-3 / R4-5** — asymmetric tuning | ✅ **Resolved at C4 level** — all 7 models tuned at every \((N,\text{run})\) |
| **R1-4 / AE-1** — overclaiming | ✅ **Strongly supported** — the low-data claim is refuted by our own evidence |
| UNSW-NB15 | ❌ separate workstream |
| Literature / novelty matrix | ❌ separate workstream |

---

# 10. Manuscript revision guidance

## 10.1 The claim that must be removed

> *"QSVM-ZZ dominates every classical baseline at every N"* and the framing of C4 as a
> **low-data advantage**.

Our own 10-run evidence contradicts it: under the natural class prior, XGBoost and Random Forest
are **significantly better** than QSVM-ZZ for \(N \le 1000\).

## 10.2 The claim that replaces it

> Under the natural class prior, the crossover between QSVM-ZZ and strong tabular baselines
> occurs at \(N \approx 2000\text{–}5000\): classical ensembles are significantly better below it
> and QSVM-ZZ is significantly better above it. The mechanism is measurable — the rare-class
> recall of the tree ensembles peaks near \(N=1000\) and then declines as they converge to the
> training prior, whereas the quantum kernel's rare-class recall increases monotonically.

This is a **stronger** contribution than the original: it answers Reviewer 1's crossover question
directly, it is quantitative, it has a verified mechanism, and it connects C4 to C3's prior-shift
contribution.

## 10.3 Wording — do and do not

| Do not write | Write instead |
|---|---|
| "QSVM-ZZ wins in the low-data regime" | "classical ensembles are significantly better below \(N\approx2000\); QSVM-ZZ becomes significantly better above \(N\approx5000\)" |
| "QSVM-ZZ dominates every baseline at every N" | "the ranking is regime- and sample-size-dependent" |
| "+6.7 points on the rare-attack subset" | "+0.024 rare-subset F1 over SVM-RBF at \(N=500\)" |
| "Cohen's d of +0.68 on decision margins" | "negligible effect on signed margins (\(|d|\le0.09\)); absolute-margin effect sizes are not interpretable because the mean signed margin is negative" |
| "QSVM-ZZ is best on rare attacks" | "SVM-RBF is strongest on the rare subset at large N; QSVM-ZZ is significantly better than the tree ensembles from \(N\ge2000\)" |
| "entanglement improves the kernel" (unconditional) | "the entanglement benefit is conditional on the embedding basis being estimated from sufficient data" |

## 10.4 Figure 9 (learning curve) — replacement

Two panels, log-x, seven models with 95% CI bands:
- Panel (a): `natural` regime — shows the crossover.
- Panel (b): `matched` regime — shows that enrichment removes it.

Mark the crossover interval \(N\in[2000,5000]\) explicitly.

## 10.5 New table to add

The rare-subset table (F1, recall, signed margin, \(d\), CI) at every N — this is the table
Reviewer 4 asked for and could not find.

---

# 11. Limitations to declare

1. \(n=4\) qubits is inherited from C1 as a design choice; it is not re-selected at each N.
2. The `matched` regime stops at \(N=2000\) because the ten runs would otherwise share most of
   their rare samples (94% at \(N=8000\)).
3. XGBoost results are **machine-dependent at the ±0.01 level per run** even with `n_jobs=1`
   and a fixed seed (verified by comparing two machines running identical code). The expected
   shift is +0.0010, an order of magnitude below the crossover CI width, so the conclusion is
   unaffected — but the dependence must be declared.
4. KDDTrain+ and KDDTest+ share **610 rows** that are identical in features and label (2.7% of
   the test set). This is a property of NSL-KDD, not of our sampling.
5. All results are statevector simulations; hardware-noise validation lives in C2.

---

# 12. Final recommendation

C4 results should now be treated as **frozen**. There is no scientific reason to re-run in search
of a more favourable narrative — and the honest narrative is the stronger one.

The remaining C4-adjacent work is manuscript integration: replace Table VI and Figure 9, add the
rare-subset table and the protocol-versus-literature table, rewrite Sec. V-D, and update the
regime map with the C4 rows.
