# C3 Revision — Final Results, Reviewer Resolution, and Manuscript Revision Plan

## 1. Scope

This document is the **final C3 results analysis** based on the exported C3 CSV artifacts:

- `c3_regime_summary.csv`
- `c3_pairwise_statistics.csv`
- `c3_temporal_mcnemar.csv`
- `c3_temporal_per_run.csv`
- `c3_perturbation_per_run.csv`
- `c3_prior_shift_per_run.csv`
- `c3_attack_composition_per_run.csv`

The purpose is to establish the final scientific findings of C3, map them directly to reviewer concerns, and provide manuscript-ready guidance.

The reviewer roadmap identifies two central C3 concerns: the statistical base was thin, and positive regimes received stronger statistical treatment than negative/null regimes. The revised C3 was designed specifically to address these points. See the reviewer roadmap and comments. 

---

# 2. Final C3 protocol

## 2.1 Frozen model/training contract

C3 inherits the frozen C2 configuration:

\[
N_{\text{train}}=1000,\qquad 10\text{ runs}
\]

with:

\[
n=4,\qquad r=2,\qquad C_{ZZ}=C_Z=3.
\]

The classical configurations are loaded from the C2 downstream parameter artifact using `chosen_params`, not `best_mean_params`.

The seven evaluated models are:

1. QSVM-ZZ
2. QSVM-Z
3. SVM-Linear
4. SVM-Poly2
5. SVM-RBF
6. Random Forest
7. XGBoost

The C1 representation is frozen and only transformed in C3; SelectKBest/PCA/scaling are not re-fit in C3.

## 2.2 Evaluation regimes

### E1 — Temporal shift

- KDDTest+
- KDDTest-21
- \(N_{\text{eval}}=1000\)

### E2 — Feature perturbation

\[
\sigma\in\{0,0.01,0.05,0.10,0.20\}
\]

with 10 matched realizations and 1000 evaluation samples per realization.

### E3 — Pure class-prior shift

\[
P(Attack)\in\{0.30,0.50,0.70\}
\]

with 10 realizations per prior regime and 1000 samples per realization.

### E4 — Attack-composition stress

\[
50\%Normal+50\%DoS
\]

with 10 realizations and 1000 samples per realization.

## 2.3 Statistical protocol

For each regime/baseline comparison, C3 reports:

- mean paired difference;
- median paired difference;
- 95% CI;
- Wilcoxon signed-rank test;
- paired standardized effect size \(d_z\);
- positive-run fraction;
- Holm-adjusted p-value;
- final verdict.

Temporal shift additionally has per-run McNemar tests.

The statistical unit for the repeated-run inference is:

\[
n=10\text{ training runs}.
\]

The 1000 evaluation examples are the test-set size, not the number of independent repetitions.

---

# 3. Full-run completion

The exported results contain:

\[
110\text{ evaluation contexts}
\]

and:

\[
110\times7=770
\]

model-evaluation records.

The context breakdown is:

- 20 temporal records/contexts;
- 50 perturbation contexts;
- 30 prior-shift contexts;
- 10 attack-composition contexts.

Temporal McNemar contains:

\[
10\times2\times6=120
\]

baseline/run records.

The C3 notebook audit reported the full-run protocol as passed.

---

# 4. Main scientific finding

The central result is:

\[
\boxed{
\textbf{QSVM-ZZ competitiveness is strongly regime- and comparator-dependent.}
}
\]

C3 does **not** support a universal statement that QSVM-ZZ is robust or generally superior.

Instead, the revised experiment produces all three outcomes:

\[
\boxed{\text{QSVM-favorable}}
\]

\[
\boxed{\text{Classical-favorable}}
\]

\[
\boxed{\text{Inconclusive}}
\]

depending on both the stress regime and the baseline.

This is the core scientific value of the revised C3 and is much better aligned with the intended “regime-specific benchmark” framing than an aggregate quantum-advantage claim.

---

# 5. E1 — Temporal shift

The temporal robustness metric is based on degradation from KDDTest+ to KDDTest-21.

The paired effect is defined so that positive values favor QSVM-ZZ.

## 5.1 Results

| Comparator | Mean effect | 95% CI | \(d_z\) | Holm \(p\) | Verdict |
|---|---:|---|---:|---:|---|
| QSVM-Z | -0.0219 | [-0.0360, -0.0079] | -1.116 | 0.0137 | Classical-favorable |
| SVM-Linear | -0.0327 | [-0.0557, -0.0097] | -1.016 | 0.0273 | Classical-favorable |
| SVM-Poly2 | -0.0484 | [-0.0725, -0.0244] | -1.442 | 0.0117 | Classical-favorable |
| SVM-RBF | +0.0006 | [-0.0207, 0.0220] | 0.021 | 0.8457 | Inconclusive |
| Random Forest | -0.0048 | [-0.0263, 0.0166] | -0.162 | 0.7695 | Inconclusive |
| XGBoost | -0.0133 | [-0.0383, 0.0118] | -0.379 | 0.4648 | Inconclusive |

## 5.2 Finding

Temporal shift is a **mixed regime**, not a universal failure or success case.

QSVM-ZZ has significantly greater degradation than:

- QSVM-Z;
- SVM-Linear;
- SVM-Poly2.

However, comparisons against:

- SVM-RBF;
- Random Forest;
- XGBoost

are inconclusive.

Therefore the correct manuscript claim is:

> **Temporal robustness is comparator-dependent. QSVM-ZZ does not establish a broad robustness advantage under the temporal shift protocol; classical SVM variants show significantly smaller degradation, whereas comparisons against RBF, Random Forest, and XGBoost are inconclusive.**

Do **not** write:

> “QSVM fails under temporal shift.”

The evidence is not uniform across all baselines.

## 5.3 McNemar

The temporal CSV contains 120 per-run McNemar records. These should be reported as supporting prediction-level evidence rather than replacing the run-level paired analysis.

The manuscript should state that temporal conclusions were supported by both:

1. run-level F1 degradation inference; and
2. paired prediction-level McNemar tests.

Because McNemar p-values vary considerably across runs, the paper should avoid summarizing them by an arithmetic mean p-value.

---

# 6. E2 — Feature perturbation

The perturbation robustness metric is the slope of:

\[
F1(\sigma)=a+b\sigma.
\]

A less-negative slope is more robust. Therefore:

\[
\Delta b=b_{ZZ}-b_{baseline}
\]

is positive when ZZ has the more favorable degradation slope.

## 6.1 Results

| Comparator | Mean slope difference | 95% CI | \(d_z\) | Holm \(p\) | Verdict |
|---|---:|---|---:|---:|---|
| QSVM-Z | -0.8421 | [-1.0028, -0.6814] | -3.748 | 0.00195 | Classical-favorable |
| SVM-Linear | -1.1082 | [-1.2740, -0.9425] | -4.784 | 0.00586 | Classical-favorable |
| SVM-Poly2 | -1.0675 | [-1.2401, -0.8950] | -4.426 | 0.00586 | Classical-favorable |
| SVM-RBF | -0.9966 | [-1.1559, -0.8374] | -4.477 | 0.00586 | Classical-favorable |
| Random Forest | -0.8638 | [-1.0018, -0.7258] | -4.478 | 0.00391 | Classical-favorable |
| XGBoost | -0.6933 | [-0.8662, -0.5203] | -2.867 | 0.00391 | Classical-favorable |

## 6.2 Finding

This is the clearest negative regime in C3.

\[
\boxed{
\text{All six baselines show significantly more favorable perturbation slopes than QSVM-ZZ.}
}
\]

The effect is not a small isolated difference. Standardized paired effects are large in magnitude:

\[
|d_z|\approx2.87\text{ to }4.78.
\]

This is strong evidence for a **robustness boundary of the selected ZZ embedding**.

Manuscript wording should be:

> **Under additive feature perturbations, QSVM-ZZ exhibits a substantially steeper Macro-F1 degradation slope than every evaluated classical comparator.**

Do not turn this directly into a causal claim that “phase wrapping causes the degradation.” The wrapped-phase explanation should be presented as a mechanistic interpretation/hypothesis supported by the observed pattern, not as a theorem established by C3.

---

# 7. E3 — Pure class-prior shift

## 7.1 Attack = 30%

| Comparator | Mean ΔF1 | 95% CI | \(d_z\) | Holm \(p\) | Verdict |
|---|---:|---|---:|---:|---|
| QSVM-Z | +0.0148 | [-0.0002, 0.0298] | 0.707 | 0.0840 | Inconclusive |
| SVM-Linear | +0.0303 | [0.0120, 0.0486] | 1.182 | 0.0293 | QSVM-favorable |
| SVM-Poly2 | +0.0116 | [-0.0042, 0.0273] | 0.526 | 0.2109 | Inconclusive |
| SVM-RBF | +0.0147 | [-0.0040, 0.0334] | 0.562 | 0.2109 | Inconclusive |
| Random Forest | -0.0090 | [-0.0243, 0.0063] | -0.422 | 0.3867 | Inconclusive |
| XGBoost | -0.0128 | [-0.0316, 0.0059] | -0.489 | 0.3203 | Inconclusive |

### Finding

Evidence is mostly inconclusive. The only statistically supported QSVM-favorable comparison is SVM-Linear.

The manuscript should **not** label the 30%-attack condition a general QSVM advantage regime.

---

# 8. Attack = 50% — stationary reference

| Comparator | Mean ΔF1 | 95% CI | \(d_z\) | Holm \(p\) | Verdict |
|---|---:|---|---:|---:|---|
| QSVM-Z | +0.0237 | [0.0079, 0.0396] | 1.069 | 0.0137 | QSVM-favorable |
| SVM-Linear | +0.0222 | [0.0041, 0.0403] | 0.879 | 0.1113 | Inconclusive |
| SVM-Poly2 | +0.0232 | [0.0023, 0.0442] | 0.795 | 0.1113 | Inconclusive |
| SVM-RBF | +0.0068 | [-0.0120, 0.0257] | 0.259 | 0.3223 | Inconclusive |
| Random Forest | -0.0137 | [-0.0272, -0.0002] | -0.727 | 0.0977 | Inconclusive |
| XGBoost | -0.0153 | [-0.0310, 0.0004] | -0.696 | 0.1055 | Inconclusive |

### Finding

The only statistically supported advantage is against the matched non-entangling quantum control:

\[
ZZ>Z.
\]

There is **no statistically significant evidence of superiority over RF/XGB** after the adopted correction.

This is especially important because it connects C2 and C3: a positive ZZ-vs-Z ablation result is not equivalent to general classical superiority.

---

# 9. Attack = 70% — attack-heavy prior

| Comparator | Mean ΔF1 | 95% CI | \(d_z\) | Holm \(p\) | Verdict |
|---|---:|---|---:|---:|---|
| QSVM-Z | +0.0367 | [0.0170, 0.0565] | 1.329 | 0.00586 | QSVM-favorable |
| SVM-Linear | +0.0231 | [0.0008, 0.0454] | 0.740 | 0.1289 | Inconclusive |
| SVM-Poly2 | +0.0291 | [0.0032, 0.0549] | 0.804 | 0.1113 | Inconclusive |
| SVM-RBF | +0.0033 | [-0.0204, 0.0269] | 0.099 | 0.4922 | Inconclusive |
| Random Forest | -0.0161 | [-0.0377, 0.0055] | -0.534 | 0.1602 | Inconclusive |
| XGBoost | -0.0242 | [-0.0430, -0.0054] | -0.921 | 0.0391 | Classical-favorable |

## 9.1 The most useful prior-shift finding

The 70%-attack regime simultaneously shows:

\[
ZZ>Z
\]

with a statistically supported advantage, while:

\[
XGB>ZZ
\]

with a statistically supported advantage.

This is a particularly clear demonstration of **comparator dependence**: a QSVM-favorable result against the matched quantum control can coexist with a classical-favorable result against a strong tabular learner.

It therefore provides a direct empirical answer to the reviewer concern about practical non-SVM competitors.

---

# 10. E4 — Attack-composition stress

Condition:

\[
50\%Normal+50\%DoS.
\]

| Comparator | Mean ΔF1 | 95% CI | \(d_z\) | Holm \(p\) | Verdict |
|---|---:|---|---:|---:|---|
| QSVM-Z | +0.0534 | [0.0346, 0.0723] | 2.029 | 0.00195 | QSVM-favorable |
| SVM-Linear | +0.0650 | [0.0496, 0.0804] | 3.024 | 0.00586 | QSVM-favorable |
| SVM-Poly2 | +0.0489 | [0.0311, 0.0668] | 1.960 | 0.00586 | QSVM-favorable |
| SVM-RBF | +0.0381 | [0.0207, 0.0555] | 1.564 | 0.00586 | QSVM-favorable |
| Random Forest | +0.0014 | [-0.0156, 0.0185] | 0.061 | 1.0000 | Inconclusive |
| XGBoost | +0.0006 | [-0.0151, 0.0164] | 0.029 | 1.0000 | Inconclusive |

## Finding

This is a selective positive regime:

\[
ZZ
\]

significantly outperforms all SVM/kernel baselines, but:

\[
ZZ\approx RF\approx XGB
\]

is the appropriate interpretation.

Do not write:

> “QSVM outperforms all classical models under DoS composition.”

Instead:

> **Under the attack-composition stress, QSVM-ZZ shows statistically supported gains over the evaluated SVM/kernel baselines, while comparisons against RF and XGBoost are inconclusive.**

---

# 11. Final C3 regime map

| Regime | Scientific conclusion |
|---|---|
| Temporal shift | Classical-favorable vs Z/Linear/Poly2; inconclusive vs RBF/RF/XGB |
| Feature perturbation | Classical-favorable vs all baselines |
| Prior 30% attack | Mostly inconclusive; QSVM-favorable vs Linear |
| Prior 50% attack | QSVM-favorable vs Z; otherwise inconclusive |
| Prior 70% attack | QSVM-favorable vs Z; XGB-favorable vs ZZ |
| Attack composition | QSVM-favorable vs SVM/kernel baselines; inconclusive vs RF/XGB |

The overall conclusion is therefore:

\[
\boxed{
\textbf{No universal robustness advantage}
}
\]

but:

\[
\boxed{
\textbf{regime- and comparator-dependent empirical competitiveness}
}
\]

This is the key scientific finding to carry into the manuscript.

---

# 12. How C3 resolves reviewer concerns

## R2 — Statistical base too small

Original concern:

- 5 runs;
- \(N_{train}=1000\);
- CIs/effect sizes based on 5 seeds.

### Revision

C3 uses:

\[
10\text{ runs}
\]

and:

\[
N_{eval}=1000.
\]

### Status

\[
\boxed{\text{RESOLVED for C3}}
\]

---

## R2 — Positive and negative regimes treated asymmetrically

Reviewer requested effect, CI, p-value and verdict for every regime.

### Revision

Every C3 comparison now has:

\[
\Delta,\quad95\%CI,\quad p,\quad d_z,\quad verdict.
\]

Temporal also has McNemar.

### Status

\[
\boxed{\text{RESOLVED}}
\]

This is one of the strongest aspects of the revised C3.

---

## R1/R2/AE — Classical baselines too weak

The reviewers specifically wanted stronger non-SVM comparators, especially RF and XGBoost, because practical competitors are not limited to SVMs. 

### Revision

C3 includes RF and XGBoost in **every C3 regime**, not just stationary evaluation.

### Status

\[
\boxed{\text{RESOLVED at the C3 level}}
\]

Do not claim that this exhausts all strong tabular models; CatBoost and transformer-style tabular models remain outside the current benchmark.

---

## R1/R3 — NISQ realism

Noise is intentionally not duplicated in C3.

C2 separately contains:

- ideal statevector;
- finite-shot;
- realistic noisy simulation;
- KTA;
- Gram/kernel distortion;
- Macro-F1.

Thus:

\[
\boxed{
C2=\text{execution/hardware sensitivity}
}
\]

\[
\boxed{
C3=\text{distribution-shift robustness}
}
\]

This avoids conflating two different stress dimensions.

---

## R1/R3 — Overclaiming quantum advantage

C3 contains significant classical-favorable outcomes and many inconclusive outcomes.

Therefore the revised paper should replace universal language with:

> **QSVM-ZZ exhibits regime- and comparator-dependent empirical competitiveness under the evaluated NIDS protocol.**

### Status

\[
\boxed{\text{STRONGLY SUPPORTED}}
\]

---

## R3 — Novelty is not an algorithmic novelty claim

C3 does not create a new quantum kernel.

Its contribution is instead methodological/empirical:

\[
\boxed{
\text{controlled regime characterization}
}
\]

based on:

- frozen C1 representation;
- frozen C2 model/HP;
- full baseline family;
- temporal shift;
- feature perturbation;
- class-prior shift;
- attack-composition stress;
- symmetric statistics;
- reproducible 10-run protocol.

This supports the revised novelty framing, but whole-paper novelty still requires the Related Work/novelty matrix.

---

# 13. Manuscript revision — Methodology

Add a subsection:

## “C3: Distribution-Shift Robustness Protocol”

Suggested wording:

> C3 evaluates the frozen C2 model configurations under controlled departures from the stationary evaluation distribution. The ten training subsets, representation, preprocessing artifacts, and model hyperparameters are inherited unchanged from C2; only the evaluation distribution is modified.

Then specify:

\[
N_{train}=1000,\quad 10\text{ runs},\quad N_{eval}=1000.
\]

Explain:

1. temporal shift;
2. feature perturbation;
3. class-prior shift;
4. attack-composition stress.

Explicitly state that attack-composition stress is **not** a pure class-prior shift.

---

# 14. Manuscript revision — Statistical Methods

Recommended text:

> All C3 robustness comparisons were performed as paired analyses across the ten repeated training runs. For each regime and baseline, we report the mean paired difference, 95% confidence interval, Wilcoxon signed-rank test, and paired standardized effect size \(d_z\). Positive effects were defined uniformly as QSVM-ZZ-favorable. Holm correction was applied within predefined comparison families.

For temporal shift:

> Because temporal robustness uses the same evaluation instances for each competing model, per-run McNemar tests were additionally used as a prediction-level diagnostic.

Do not average McNemar p-values.

---

# 15. Manuscript revision — Results structure

## V.C. Distribution-Shift Robustness

### V.C.1 Temporal Shift

Main message:

> QSVM-ZZ does not show a uniform temporal robustness advantage. It is significantly less favorable than QSVM-Z, Linear and Poly2 under the degradation metric, while comparisons with RBF, RF and XGBoost remain inconclusive.

### V.C.2 Feature Perturbation

Main message:

> QSVM-ZZ exhibits a significantly steeper Macro-F1 degradation slope than every evaluated baseline.

### V.C.3 Class-Prior Shift

Main message:

> Prior-shift results are strongly comparator-dependent. ZZ shows statistically supported gains over the matched Z control under the 50% and 70% attack-prior conditions, while these gains do not translate into uniform superiority over strong tabular learners; in the attack-heavy 70% condition, XGBoost is significantly favorable against ZZ.

### V.C.4 Attack-Composition Stress

Main message:

> ZZ is significantly favorable against the SVM/kernel baselines, while comparisons against RF and XGBoost are inconclusive.

---

# 16. Main C3 table

Recommended compact main-paper table:

| Regime | Comparator | Effect | 95% CI | Holm \(p\) | \(d_z\) | Verdict |
|---|---|---:|---|---:|---:|---|
| Temporal | Z | -0.0219 | [-0.0360,-0.0079] | 0.0137 | -1.116 | Classical |
| Temporal | RBF | +0.0006 | [-0.0207,0.0220] | 0.8457 | 0.021 | Inconclusive |
| Temporal | XGB | -0.0133 | [-0.0383,0.0118] | 0.4648 | -0.379 | Inconclusive |
| Perturbation | RBF | -0.9966 | [-1.1559,-0.8374] | 0.00586 | -4.477 | Classical |
| Perturbation | XGB | -0.6933 | [-0.8662,-0.5203] | 0.00391 | -2.867 | Classical |
| Prior 70% | Z | +0.0367 | [0.0170,0.0565] | 0.00586 | 1.329 | QSVM |
| Prior 70% | XGB | -0.0242 | [-0.0430,-0.0054] | 0.0391 | -0.921 | Classical |
| DoS composition | RBF | +0.0381 | [0.0207,0.0555] | 0.00586 | 1.564 | QSVM |
| DoS composition | XGB | +0.0006 | [-0.0151,0.0164] | 1.0000 | 0.029 | Inconclusive |

Full pairwise table: supplementary.

---

# 17. Main Figure — revised regime map

Replace the old positive-only forest plot with:

> **Regime-specific relative performance of QSVM-ZZ against the full baseline family**

Display:

- effect estimate;
- 95% CI;
- zero line;
- baseline identity;
- QSVM-favorable / classical-favorable / inconclusive.

This is a stronger replacement for the old regime map because the earlier version relied on five seeds and emphasized positive effects, while C3 now provides symmetric ten-run evidence.

---

# 18. Discussion — relation to C2

A useful cross-contribution interpretation is:

\[
C2:
\quad
ZZ>Z
\]

in controlled quantum ablation/geometry.

C3 then asks whether that advantage persists when the evaluation distribution changes.

Recommended text:

> The controlled ZZ/Z improvement established in C2 should not be interpreted as a universal predictive advantage. C3 shows that the downstream benefit of the entangling geometry is conditional on the evaluation regime and on the classical comparator.

This is a strong bridge between C2 and C3.

---

# 19. Discussion — strong classical baselines

C3 should explicitly acknowledge:

> The revised benchmark places QSVM-ZZ against practical tree-based learners, rather than limiting the comparison to SVM variants.

And:

> The results do not support universal superiority over strong classical learners.

This is essential for the R1/R2 practical-competitiveness criticism.

---

# 20. Limitations

Add:

> The robustness analysis remains simulation-based and does not constitute physical-device validation for each distribution-shift regime.

> The evaluated strong tabular family includes Random Forest and XGBoost but does not exhaust modern tabular methods such as CatBoost or transformer-based tabular learners.

> The identified regime boundaries are empirical boundaries of the tested NSL-KDD protocol and should not be interpreted as universal properties of quantum kernels.

---

# 21. Conclusion wording

Do **not** conclude:

> “QSVM-ZZ provides robust quantum advantage.”

Recommended wording:

> **“The revised C3 analysis shows that the empirical competitiveness of QSVM-ZZ is strongly regime- and comparator-dependent. The model retains statistically supported gains over the matched non-entangling quantum control and several kernel-based classical baselines in selected regimes, while it exhibits clear degradation under feature perturbation and does not establish universal superiority over strong tabular learners.”**

This wording matches the actual evidence.

---

# 22. Reviewer-resolution matrix

| Issue | C3 status |
|---|---|
| Five seeds too few | ✅ Resolved |
| Negative regimes lacked inference | ✅ Resolved |
| Temporal McNemar | ✅ Resolved |
| Perturbation statistics | ✅ Resolved |
| Strong practical baselines | ✅ Resolved at C3 level |
| Full baseline across all regimes | ✅ Stronger than minimum |
| Frozen C2 hyperparameters | ✅ Resolved |
| Frozen C1 representation | ✅ Resolved |
| Prior vs attack-composition separation | ✅ Resolved |
| Reproducibility/audit | ✅ Resolved |
| Regime-specific framing | ✅ Strongly supported |
| Hardware noise | ✅ handled at C2 level, intentionally not duplicated |
| UNSW-NB15 | ❌ separate workstream |
| C1/Theorem 1 | ❌ separate workstream |
| Literature/novelty audit | ❌ separate workstream |
| Rare-attack discrepancy | ❌ separate workstream |

Do not state in rebuttal that C3 “resolves all reviewer concerns.” The accurate statement is that C3 resolves the concerns concerning **statistical robustness, negative-regime symmetry, temporal/perturbation evidence, and strong-baseline robustness evaluation**.

---

# 23. Final scientific story

C3 does **not** tell:

\[
\text{QSVM wins everywhere}.
\]

It tells:

\[
\boxed{
\text{QSVM-ZZ is useful in specific regimes, but not universally.}
}
\]

The four most important empirical statements are:

\[
\boxed{
\text{Temporal robustness: mixed / often classical-favorable}
}
\]

\[
\boxed{
\text{Feature perturbation: clearly classical-favorable}
}
\]

\[
\boxed{
\text{Prior shift: mixed and comparator-dependent}
}
\]

\[
\boxed{
\text{Attack composition: favorable vs SVM/kernel baselines, inconclusive vs RF/XGB}
}
\]

This supports a more defensible paper-level question:

> **When, against which baselines, and under which distributional conditions does a small NISQ-constrained ZZ quantum kernel remain empirically competitive for NIDS?**

That is substantially stronger than a generic “quantum advantage” claim.

---

# 24. Final recommendation

**C3 results should now be treated as frozen.** There is no scientific reason to rerun C3 merely to obtain a more favorable narrative.

The next work should be manuscript integration:

1. replace the old C3 methodology with the frozen protocol;
2. replace the old regime map;
3. report the full baseline comparison in supplementary material;
4. report the compact regime table in the main paper;
5. rewrite the C3 discussion around comparator-dependent robustness;
6. revise abstract/conclusion language to remove universal quantum-advantage wording.

Issues outside C3—UNSW-NB15, C1/Theorem/Pareto, literature/novelty matrix, rare-attack discrepancy, repository and supplementary—remain separate workstreams.
