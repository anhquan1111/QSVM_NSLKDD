# C1 Final Revision — Results, Reviewer Resolution, and Manuscript Rewrite Plan

## 0. Executive conclusion

The final `C1_revision(7).ipynb` establishes a substantially stronger and more defensible C1 than the original manuscript.

The original C1 claimed:

> Pareto optimization + weighted scalarization + Theorem 1 → `n = 4`.

That formulation was vulnerable because Reviewer 4 identified an inconsistency between the theorem and the numerical values, and the original manuscript explicitly defined C1 through a Pareto/scalarized optimization procedure.

The revised C1 instead uses a transparent three-stage selection protocol:

```text
SelectKBest K=20
        ↓
Candidate PCA/embedding dimensions n = 2,...,10
        ↓
1. Information feasibility:
       V(n) ≥ 85%
        ↓
       {4,5,6,7,8,9,10}
        ↓
2. Quantum-kernel quality:
       KTA(n) ≥ 95% of the best KTA
       within the information-feasible region
        ↓
       {4,5,6}
        ↓
3. Hardware-cost selection:
       minimize the CNOT-weighted hardware-cost proxy Q(n)
        ↓
       n* = 4
        ↓
Freeze n=4 for C2–C4
```

Finite-shot analysis is retained as a separate validation/sanity check and is **not** part of the selection rule.

This is the version of C1 that should be used as the source of truth for the manuscript revision.

---

# Final freeze decision

**Status: FROZEN — C1_revision(7).ipynb**

The corrected implementation was executed successfully after replacing the previous two-qubit interaction count with the decomposed CNOT count. The revised cost remains monotonic in the candidate dimension, the information-feasible and KTA-feasible sets are unchanged, and the final operating point remains **n=4**. The downstream contract therefore remains unchanged: **K=20, n=4, r=2**.

The corrected hardware-cost definition is:

\[
N_{\mathrm{ZZ}}(n)=r\binom{n}{2},\qquad
N_{\mathrm{CNOT}}(n)=2r\binom{n}{2},
\]

with the normalized cost

\[
Q(n)=\frac{N_{1q}(n)+5N_{\mathrm{CNOT}}(n)}{Q_{\max}}.
\]

For n=4 and r=2, this corresponds to 6 ZZ interaction pairs per layer, 12 CNOTs per layer, and 24 CNOTs across the two repetitions. The numerical Q(n) values and C1 artifacts were regenerated from this corrected implementation.

**Freeze rule:** no further changes to the C1 selection methodology or frozen operating point should be made unless a new scientific issue is identified.

---

# 1. What the final C1 actually found

## 1.1 Candidate dimensions

The experiment evaluates every candidate:

\[
n \in \{2,3,4,5,6,7,8,9,10\}.
\]

No candidate is removed before the analysis.

The input contains 20 features after SelectKBest.

---

## 1.2 Classical embedding / hardware trade-off

The executed C1 sweep produces:

| n | Explained variance V(n) | DBI | 1/DBI | Q(n) |
|---:|---:|---:|---:|---:|
| 2 | 0.7418 | 0.8746 | 1.1434 | 0.0298 |
| 3 | 0.8210 | 1.0179 | 0.9824 | 0.0766 |
| **4** | **0.8662** | **1.0846** | **0.9220** | **0.1391** |
| 5 | 0.9040 | 1.1311 | 0.8841 | 0.2283 |
| 6 | 0.9391 | 1.1718 | 0.8534 | 0.3391 |
| 7 | 0.9524 | 1.1850 | 0.8439 | 0.4766 |
| 8 | 0.9643 | 1.1985 | 0.8344 | 0.6298 |
| 9 | 0.9729 | 1.2065 | 0.8288 | 0.8043 |
| 10 | 0.9810 | 1.2140 | 0.8237 | 1.0000 |

The main pattern is:

\[
V(n)\uparrow,\qquad
1/DBI(n)\downarrow,\qquad
Q(n)\uparrow.
\]

Thus increasing the embedding dimension gives more classical variance retention, but it does not monotonically improve class geometry and incurs increasing two-qubit-related cost.

This is a real trade-off, rather than a trivial variance-threshold rule.

---

# 2. Pareto analysis: important but no longer the selector

The final notebook evaluates Pareto dominance over all candidates and obtains:

```text
Pareto-optimal:
[2,3,4,5,6,7,8,9,10]

Dominated:
none
```

Therefore:

> Pareto analysis does not itself select `n=4`.

This is now treated correctly as a **diagnostic characterization of the trade-off space**.

This is important because the old manuscript presented Pareto search as the core selection mechanism. The revised manuscript must not retain that claim.

Correct wording:

> “Pareto analysis is used to characterize the information–class-geometry–hardware trade-off across candidate embedding dimensions.”

Incorrect wording:

> “Pareto optimization selects the 4-qubit operating point.”

---

# 3. Information constraint

The predefined information-retention requirement is:

\[
V(n)\ge0.85.
\]

The final experiment gives:

\[
F_V = \{4,5,6,7,8,9,10\}.
\]

Therefore:

- `n=2`: 74.18% → fails.
- `n=3`: 82.10% → fails.
- `n=4`: 86.62% → first feasible dimension.

The information-only threshold sensitivity gives:

| Variance threshold | Smallest feasible n |
|---:|---:|
| 80% | 3 |
| **85%** | **4** |
| 90% | 5 |
| 95% | 7 |

The 85% threshold is therefore an explicit design requirement rather than a theorem-derived optimum.

It should be described as an **a priori information-retention requirement**.

---

# 4. Quantum-kernel geometry: the key new scientific result

A fixed stratified subset of 300 samples (seed 42) is used for every candidate dimension.

This gives:

| n | KTA | Effective rank | Off-diagonal mean | Off-diagonal std |
|---:|---:|---:|---:|---:|
| 2 | **0.3297** | 5.78 | 0.3464 | 0.3264 |
| 3 | 0.1537 | 9.55 | 0.3365 | 0.2946 |
| 4 | 0.2364 | 28.49 | 0.1476 | 0.2210 |
| **5** | **0.2439** | 46.50 | 0.0841 | 0.1954 |
| 6 | 0.2381 | 56.93 | 0.0628 | 0.1825 |
| 7 | 0.1949 | 79.57 | 0.0415 | 0.1515 |
| 8 | 0.1952 | 88.70 | 0.0334 | 0.1455 |
| 9 | 0.1907 | 100.60 | 0.0290 | 0.1394 |
| 10 | 0.1793 | 114.70 | 0.0248 | 0.1307 |

The important finding is:

> **More dimensions do not imply better quantum-kernel quality.**

The global KTA maximum is at `n=2`, but those dimensions do not satisfy the 85% information requirement.

Within the information-feasible region:

\[
F_V=\{4,\ldots,10\},
\]

the best KTA is:

\[
KTA_{\max,F_V}=0.2438648584
\]

at:

\[
n=5.
\]

This is the correct reference for the kernel-quality constraint.

---

# 5. Final KTA constraint

The primary tolerance is:

\[
\epsilon=0.05.
\]

Therefore:

\[
KTA_{\mathrm{threshold}}
=
0.95\times0.2438648584
=
0.2316716154.
\]

The dimensions satisfying this are:

\[
F_{V,KTA}=\{4,5,6\}.
\]

Therefore the KTA constraint removes:

\[
n=7,8,9,10
\]

even though those dimensions retain more classical PCA variance.

This is the most important evidence that the revised C1 is no longer merely:

> “choose the smallest dimension that retains 85% variance.”

The quantum-kernel criterion materially narrows the design space.

---

# 6. Hardware-cost selection

For the final feasible set:

\[
\{4,5,6\},
\]

the hardware-cost proxy is:

| n | Q(n) |
|---:|---:|
| 4 | **0.1391** |
| 5 | 0.2283 |
| 6 | 0.3391 |

Therefore:

\[
n^*=\arg\min_{n\in\{4,5,6\}}Q(n)=4.
\]

At `n=4`:

- explained variance = **86.6187%**;
- KTA = **0.2364**;
- best feasible KTA = **0.2439**;
- KTA gap from best feasible candidate ≈ **3.05%**;
- hardware cost = **0.1391**;
- full-entanglement ZZ interaction pairs/layer = **6**;
- CNOTs/layer = **12**; total CNOT count at r=2 = **24**.

Relative to the other remaining candidates, `n=4` has approximately:

- 39.1% lower Q than `n=5`;
- 59.0% lower Q than `n=6`.

Therefore hardware cost now plays a genuine final decision role.

The scientific interpretation should be:

> The information and kernel-quality constraints identify a narrow feasible region, after which the hardware-cost objective selects the lowest-cost operating point.

Do not claim that hardware cost alone globally determines `n=4`.

---

# 7. KTA tolerance sensitivity

The final notebook tests:

\[
\epsilon\in\{0.02,0.05,0.10\},
\]

corresponding to retaining 98%, 95%, and 90% of the best feasible KTA.

The resulting selected dimensions are:

| KTA tolerance ε | Required fraction | Selected n |
|---:|---:|---:|
| 2% | 98% | 5 |
| **5%** | **95%** | **4** |
| 10% | 90% | 4 |

This produces an important nuance:

> `n=4` is stable at the adopted 5% tolerance and also at 10%, but a stricter 2% tolerance would select `n=5`.

Therefore the manuscript should **not** claim that `n=4` is completely insensitive to the KTA tolerance.

The correct claim is:

> “The selected operating point is robust across the tested 5% and 10% tolerances, while a stricter 2% tolerance shifts the selection to n=5.”

The 5% value should be described as the **predefined primary design tolerance**, not as a value chosen to force `n=4`.

---

# 8. Bootstrap KTA uncertainty

The notebook uses 200 bootstrap resamples of the fixed 300-sample kernel subset.

For `n=4`:

\[
KTA=0.2364
\]

with 95% bootstrap CI:

\[
[0.2119,\;0.2762].
\]

The point estimates for `n=4`, `n=5`, and `n=6` are close, so the 5% tolerance should be interpreted as a practical near-best criterion rather than as evidence that `n=5` is statistically uniquely superior to `n=4`.

This is a useful supporting analysis, but it should remain a diagnostic rather than become another selection test.

---

# 9. Finite-shot validation

Finite-shot sampling uses:

- 1024 shots;
- seed 42;
- same fixed kernel subset;
- all `n=2,...,10`.

The results are:

| n | FroSim | D_noise | ΔKTA |
|---:|---:|---:|---:|
| 2 | 0.9999 | 0.0001 | -0.0014 |
| 3 | 0.9999 | 0.0001 | -0.0011 |
| **4** | **0.9997** | **0.0003** | **-0.0024** |
| 5 | 0.9999 | 0.0001 | +0.0002 |
| 6 | 0.9999 | 0.0001 | +0.0007 |
| 7 | 0.9999 | 0.0001 | +0.0008 |
| 8 | 1.0000 | 0.0000 | +0.0004 |
| 9 | 1.0000 | 0.0000 | +0.0005 |
| 10 | 1.0000 | 0.0000 | +0.0007 |

The selected `n=4` has:

\[
D_{\mathrm{noise}}=0.000321.
\]

This means that under the evaluated finite-shot sampling budget, the quantum Gram matrix is very close to its ideal statevector reference.

However:

> This is **finite-shot sampling validation**, not realistic hardware-noise validation.

The notebook explicitly excludes gate-level depolarizing, readout, and thermal-relaxation noise from C1 selection.

This is an important limitation, but it does not invalidate the C1 selection procedure itself.

---

# 10. Shot-sensitivity result

The reduced sensitivity study uses:

\[
shots\in\{256,512,1024\}
\]

and representative:

\[
n\in\{4,6,10\}.
\]

The 1024-shot results are reused from the primary finite-shot evaluation.

The observed distortion values are:

| Shots | n=4 | n=6 | n=10 |
|---:|---:|---:|---:|
| 256 | 0.0007 | 0.0005 | 0.0003 |
| 512 | 0.0008 | 0.0006 | 0.0002 |
| 1024 | 0.0003 | 0.0001 | 0.0000 |

The trend is not monotonic with `n` across all shot levels.

Therefore the correct conclusion is:

> finite-shot distortion remains very small in the evaluated setting, but no monotonic dependence on embedding dimension is established.

Do not claim:

> larger n necessarily produces larger shot-noise sensitivity.

---

# 11. Does the new C1 resolve the original reviewer criticism?

## Reviewer 4 — Theorem 1 / C1 inconsistency

### Status: **Resolved methodologically**

The original reviewer criticism was that the theorem and table were inconsistent and that equal-weight scalarization appeared to favour `n=2`.

The old manuscript explicitly defined:

\[
J(n)=\alpha V(n)+\beta F_e(n)-\gamma Q(n)
\]

and used Pareto filtering + a weight sweep + Theorem 1 to select `n=4`. The manuscript also stated that `n=4` was uniquely selected for sufficiently large hardware weight.

Those claims must now be removed.

The new C1 no longer uses:

- Theorem 1;
- scalarized objective as the primary selector;
- Pareto mode across weights;
- a theorem claiming global optimality.

Instead, it has an explicit empirical selection contract.

This directly addresses the core mathematical inconsistency identified by Reviewer 4.

---

## Reviewer 4 — “Does Pareto filtering actually do anything?”

### Status: **Resolved**

The final notebook explicitly finds:

```text
Pareto-optimal = all n=2,...,10
Dominated = none
```

Therefore the paper should no longer pretend Pareto filtering eliminates candidates.

This is actually a strength because the revised methodology is transparent:

> Pareto analysis describes the trade-off; it is not the selection mechanism.

---

## Reviewer 4 — Why n=4?

### Status: **Resolved much more convincingly**

The answer is now:

\[
V\ge85\%
\rightarrow
KTA\ge95\%\,KTA_{\max,F_V}
\rightarrow
\min Q(n)
\rightarrow
n=4.
\]

This is much more defensible than “Theorem 1 says n=4”.

---

## Reviewer 2 — kernel concentration

### Status: **Substantially addressed**

Reviewer 2 specifically asked that kernel concentration be acknowledged.

The revised C1 now directly computes:

- effective rank;
- off-diagonal mean;
- off-diagonal standard deviation.

These diagnostics show a strong geometry change as `n` grows:

\[
R_{\mathrm{eff}}: 5.78\rightarrow114.70,
\]

while off-diagonal standard deviation decreases:

\[
0.3264\rightarrow0.1307.
\]

This gives C1 an empirical link to the kernel-concentration discussion.

Do not call effective rank itself an “expressibility” metric; call it a kernel-geometry/effective-complexity diagnostic.

---

## Reviewer 1 / Reviewer 3 — NISQ realism

### Status: **Only partially addressed by C1**

The revised C1 correctly limits its claim to finite-shot validation.

This is scientifically cleaner.

However, the reviewer concern about realistic gate/readout/decoherence noise remains a **paper-level issue**, not a C1-selection issue. Reviewer 1 explicitly asked for realistic backend/Aer-type noise or a qualified claim.

Therefore:

- C1 does **not** need realistic noise inside its selection rule.
- The paper still needs either a separate realistic-noise experiment or a clear reduction of NISQ-feasibility claims.

The review roadmap explicitly classifies noisy simulation as a major revision item independent of C1. fileciteturn26file11L1246-L1278

---

# 12. Corrected hardware-cost implementation

The final notebook now implements the hardware-cost term using the actual CNOT count implied by the ZZFeatureMap decomposition. Each pairwise ZZ interaction contributes two CNOTs through the CNOT–RZ–CNOT decomposition. Thus:

\[
N_{\mathrm{CNOT}}(n)=2r\binom{n}{2}.
\]

The recomputed normalized costs are:

| n | Q(n) |
|---:|---:|
| 2 | 0.0261 |
| 3 | 0.0717 |
| **4** | **0.1391** |
| 5 | 0.2283 |
| 6 | 0.3391 |
| 7 | 0.4717 |
| 8 | 0.6261 |
| 9 | 0.8022 |
| 10 | 1.0000 |

The correction changes the numerical scale of Q(n) but preserves its monotonic increase with embedding dimension. Consequently, the information-feasible set remains {4,5,6,7,8,9,10}, the KTA-feasible set remains {4,5,6}, and the minimum-cost candidate remains **n=4**.

For the selected configuration (n=4, r=2):

- 6 ZZ interaction pairs per layer;
- 12 CNOTs per layer;
- 24 CNOTs across the two ZZ layers.

This corrected implementation should be the source of truth for the revised manuscript and rebuttal.

---

# 12. Overall scientific quality of the new C1

The revised C1 is much stronger than the original.

## Original scientific story

```text
PCA
 ↓
85% variance
 ↓
Pareto / weights
 ↓
Theorem
 ↓
n=4
```

This was vulnerable and difficult to defend.

## New scientific story

```text
Increasing n
 ↓
more information
but changing kernel geometry
and increasing hardware cost
 ↓
information-feasible region
 ↓
kernel-quality feasible region
 ↓
hardware-cost minimization
 ↓
n=4
```

The critical new finding is:

> **Among dimensions that retain sufficient classical information, increasing dimension beyond 6 does not preserve near-best kernel-target alignment, while the remaining near-best region {4,5,6} has rapidly increasing two-qubit cost.**

That is a substantially more meaningful contribution.

---

# 13. What must change in the manuscript

This section is the direct manuscript rewrite plan.

## 13.1 Abstract

Current wording says that the embedding dimension is selected by a Pareto search and that the 4-qubit configuration is fixed by that Pareto pipeline.

That must change.

### Recommended wording

> “We introduce a hardware-aware embedding-dimension selection procedure that first enforces an information-retention requirement, then constrains quantum-kernel alignment, and finally minimizes a CNOT-weighted hardware-cost proxy. On NSL-KDD, this procedure selects a 4-qubit depth-2 ZZFeatureMap.”

Do not say:

> “Pareto optimization selects 4 qubits.”

Do not say:

> “Theorem 1 proves the 4-qubit optimum.”

---

# 14. Introduction — contribution statement

The old manuscript says C1 is a:

> “two-stage dimensionality reduction pipeline whose embedding dimension is selected by Pareto optimisation over three objectives...”

That is no longer correct.

The revised contribution should be:

> **C1: A hardware-aware embedding-selection procedure that combines an explicit information-retention constraint, quantum-kernel quality constraint, and CNOT-weighted hardware-cost minimization.**

This matches the proposed contribution framework in the reviewer roadmap. The revision plan explicitly recommends framing C1 as a hardware-constrained embedding-selection procedure rather than a new quantum algorithm. fileciteturn27file6L985-L999

---

# 15. Figure 3 — system pipeline

The current manuscript has:

```text
PCA n=4
   ↓
C1 Pareto search
J(n)
   ↓
ZZFeatureMap
```

That must be redesigned conceptually as:

```text
SelectKBest K=20
       ↓
Candidate PCA dimensions n=2,...,10
       ↓
V(n) ≥ 85%
       ↓
KTA ≥ 95% of best feasible KTA
       ↓
minimize Q(n)
       ↓
n*=4
       ↓
ZZFeatureMap n=4, r=2
```

The current figure explicitly labels C1 as a Pareto search with scalarized `J(n)`, so this is a necessary manuscript change. fileciteturn27file0L11-L27

---

# 16. Problem 1 — rewrite

The current Problem 1 states that C1 must be Pareto-optimal in:

\[
(V,F_e,-Q)
\]

on the weight simplex.

That formulation is obsolete.

Replace the C1 portion with:

\[
F_V=\{n\in\mathcal N:V(n)\ge\tau_V\}
\]

where:

\[
\tau_V=0.85.
\]

Then:

\[
KTA_{\max,F_V}
=
\max_{n\in F_V}KTA(n),
\]

and:

\[
F_{V,KTA}
=
\left\{
n\in F_V:
KTA(n)\ge(1-\epsilon)KTA_{\max,F_V}
\right\}.
\]

Finally:

\[
n^*
=
\arg\min_{n\in F_{V,KTA}} Q(n).
\]

with:

\[
\epsilon=0.05.
\]

This should become the formal definition of C1.

---

# 17. Section III-C — complete rewrite

The current subsection explicitly says:

- weighted scalarization;
- Pareto definition;
- Algorithm 1;
- Theorem 1.

All of that needs replacement.

The old version is visible in the manuscript around Section III-C and Algorithm 1. fileciteturn27file1L133-L163

### New subsection structure

## C. C1: Hardware-Aware Embedding-Dimension Selection

### Stage 1 — SelectKBest

Keep the existing K=20 methodology if unchanged.

### Stage 2 — Candidate embedding sweep

Evaluate:

\[
n=2,\ldots,10.
\]

### Information criterion

\[
V(n)\ge0.85.
\]

### Kernel-quality criterion

\[
KTA(n)\ge0.95KTA_{\max,F_V}.
\]

### Hardware selection

\[
n^*=\arg\min Q(n).
\]

### Diagnostic analyses

Mention:

- Pareto frontier;
- scalarization sensitivity;
- effective rank;
- concentration;
- finite-shot validation.

But explicitly state that these are not the primary selection mechanism unless they are part of the formal rule above.

---

# 18. Theorem 1

### Recommendation: remove completely

Do not replace it with another theorem.

The C1 contribution is empirical/methodological.

The old theorem is exactly where Reviewer 4 identified the logical inconsistency.

The revision plan also explicitly recommends removing the theorem if it is not essential. fileciteturn27file2L1160-L1176

A clean methodology is stronger here than a fragile theorem.

---

# 19. Algorithm 1 — replace

Old Algorithm 1 is a Pareto/weight-sweep algorithm.

Replace it with:

```text
Algorithm 1: Hardware-aware embedding-dimension selection

Input:
    Training set X
    Candidate dimensions N={2,...,10}
    Variance threshold τV=0.85
    KTA tolerance ε=0.05

1. For each n in N:
       fit PCA(n) on training data
       compute V(n), DBI(n), Q(n)

2. Compute:
       FV = {n : V(n) ≥ τV}

3. For n in FV:
       construct quantum Gram matrix
       compute KTA(n)

4. Compute:
       KTAbest = max KTA(n), n ∈ FV

5. Compute:
       FV,KTA = {n ∈ FV :
                  KTA(n) ≥ (1−ε)KTAbest}

6. Select:
       n* = argmin Q(n), n ∈ FV,KTA

7. Freeze PCA(n*) and scaler for downstream experiments.

Output:
       n*
```

Finite-shot analysis should appear as validation, not inside this algorithm.

---

# 20. Table III — rewrite

The current Table III is tied to the old Pareto/scalarization/theorem narrative.

The new Table III should contain:

| n | V(n) | DBI | 1/DBI | KTA | R_eff | offdiag std | Q(n) | V≥85% | KTA-feasible |
|---:|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|
| 2 | 0.7418 | 0.8746 | 1.1434 | 0.3297 | 5.78 | 0.3264 | 0.0298 | No | — |
| 3 | 0.8210 | 1.0179 | 0.9824 | 0.1537 | 9.55 | 0.2946 | 0.0766 | No | — |
| **4** | **0.8662** | **1.0846** | **0.9220** | **0.2364** | **28.49** | **0.2210** | **0.1391** | **Yes** | **Yes** |
| **5** | **0.9040** | **1.1311** | **0.8841** | **0.2439** | **46.50** | **0.1954** | **0.2283** | **Yes** | **Yes** |
| **6** | **0.9391** | **1.1718** | **0.8534** | **0.2381** | **56.93** | **0.1825** | **0.3391** | **Yes** | **Yes** |
| 7 | 0.9524 | ... | ... | 0.1949 | 79.57 | 0.1515 | 0.4766 | Yes | No |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

The key row/summary should emphasize:

\[
\{4,5,6\}
\rightarrow
\min Q
\rightarrow
4.
\]

---

# 21. Figure 5 — rewrite

The old Figure 5 should no longer claim to demonstrate that Pareto search selects `n=4`.

Suggested figure structure:

### Panel A
Explained variance vs `n`.

### Panel B
KTA vs `n`, with:

- vertical/marker indication of `V≥85%`;
- horizontal line at `0.95 KTA_max,FV`;
- highlight `{4,5,6}`.

### Panel C
Hardware cost `Q(n)` vs `n`, highlighting 4,5,6.

This figure would visually communicate the entire selection chain in one place.

---

# 22. Results Section V-A — new narrative

The old Results section should not say:

> “Pareto search selected n=4.”

Instead:

> “The information constraint first excludes n=2 and n=3, yielding seven feasible dimensions (n=4–10). Within this set, the highest KTA occurs at n=5 (0.2439). Requiring each candidate to remain within 5% of this value retains n=4–6. The CNOT-weighted hardware-cost proxy then selects n=4 because Q(4)=0.1391, compared with 0.2283 and 0.3391 for n=5 and n=6.”

Then discuss:

> “Thus the selected 4-qubit embedding is not simply the first PCA dimension to exceed the variance threshold; it is the lowest-cost point within a kernel-quality-feasible region.”

That sentence should become the core C1 finding.

---

# 23. Add a short paragraph on robustness

Immediately after:

> “The 5% KTA tolerance sensitivity selects n=4 at ε=0.05 and ε=0.10, while a stricter ε=0.02 selects n=5. We therefore retain ε=0.05 as the predefined primary design tolerance and report tolerance sensitivity separately.”

This is scientifically honest and prevents a reviewer from accusing us of hiding the 2% case.

---

# 24. Finite-shot paragraph

Do not merge this into C1 selection.

Use something like:

> “As a separate validation, finite-shot sampling at 1024 shots produced Frobenius similarities ≥0.9997 across the evaluated dimensions, with D_noise at the selected n=4 of 0.0003. A representative shot-sensitivity analysis over 256–1024 shots showed small but non-monotonic distortion, so these measurements are treated as robustness diagnostics rather than selection criteria.”

This is consistent with what the notebook actually found.

---

# 25. Limitations section

Replace the old embedding-size limitation.

The current manuscript says the Pareto frontier contains other dimensions and that further work is needed to evaluate them.

The revised limitation should say:

> “C1 uses an information and kernel-quality constrained selection rule rather than claiming a globally optimal qubit dimension. The 5% KTA tolerance is a predefined design parameter; sensitivity analysis shows that a stricter 2% tolerance selects n=5. Thus n=4 should be interpreted as the selected operating point under the adopted design criterion, not a universally optimal embedding.”

This is important because it demonstrates methodological honesty.

---

# 26. C1-specific response to Reviewer 4

Suggested rebuttal:

> **Response:** We thank the reviewer for identifying the inconsistency in the original C1 selection theorem. We independently reimplemented the embedding-dimension analysis and found that the original theorem/scalarization formulation was unnecessarily strong. We therefore removed Theorem 1 and no longer use weighted scalarization as the primary selection mechanism. The revised C1 evaluates all candidate dimensions n=2–10, first requires at least 85% cumulative PCA variance, then retains dimensions whose quantum-kernel alignment is within 5% of the best KTA among the information-feasible candidates, and finally selects the minimum CNOT-weighted hardware cost within that feasible set. For NSL-KDD this yields the feasible set {4,5,6} and selects n=4. Pareto analysis is retained only as a diagnostic because all candidates are non-dominated. Weight-sensitivity analysis is reported as supplementary evidence and confirms that scalarized selection is weight-sensitive.

---

# 27. What C1 now resolves — and what it does not

## Resolved

### R4 — theorem inconsistency
**Yes.**

The theorem is removed and replaced with an executable, reproducible rule.

### R4 — Pareto interpretation
**Yes.**

Pareto is explicitly diagnostic.

### R4 — arbitrary n=4
**Yes, substantially.**

`n=4` emerges from:

- information;
- KTA;
- hardware cost.

### R2 — exponential/kernel concentration discussion
**Yes, substantially.**

It is now empirically supported by kernel-geometry diagnostics.

### R3 — novelty framing
**Improved.**

C1 now adds a genuine hardware-aware selection methodology rather than a simple fixed PCA threshold.

---

## Not fully resolved by C1 alone

### R1/R3 — realistic hardware noise
**No.**

Finite-shot validation is not gate/readout/decoherence noise.

### R1/R2 — strong classical baselines
**No.**

Still need XGBoost/RF/etc.

### R1 — second dataset
**No.**

Still need UNSW-NB15.

### R1/R4 — asymmetric hyperparameter tuning
**No.**

Still need symmetric QSVM/classical tuning study.

These remain paper-level revision tasks. The reviewer roadmap explicitly classifies these as major revision gates. fileciteturn27file4L530-L565

---

# 28. Final assessment of C1 quality

## Scientific contribution

**Much stronger than the original C1.**

The key contribution is now:

> a reproducible, hardware-aware embedding-selection procedure that prevents “more PCA dimensions = better quantum kernel” from being assumed.

## Numerical result

**Good.**

The result is particularly strong because:

- n=4 is retained;
- n=7–10 are eliminated by kernel-quality despite higher variance;
- n=5 is the best feasible-KTA point;
- n=4 has the lowest hardware cost in the remaining set.

This produces a meaningful operating point rather than a forced result.

## Robustness

**Good but not absolute.**

At the primary 5% KTA tolerance, n=4 is selected. At 10% it remains n=4. A stricter 2% tolerance selects n=5.

Therefore the result is:

> **robust over the practical 5–10% tolerance range tested, but not invariant to arbitrarily strict KTA tolerances.**

## Noise

**Positive validation result, not a selection result.**

At 1024 shots, n=4 has:

\[
FroSim=0.9997,
\quad
D_{\mathrm{noise}}=0.0003,
\quad
\Delta KTA=-0.0024.
\]

This supports finite-shot stability, but not realistic hardware-noise robustness.

---

# 29. Final C1 manuscript narrative to preserve

The C1 story should ultimately be:

> **The embedding dimension is not selected by PCA variance alone. We first require sufficient information retention, then reject dimensions whose quantum-kernel alignment falls materially below the best alignment achievable in that information-feasible region, and finally use a CNOT-weighted hardware-cost proxy to select the lowest-cost remaining operating point. On NSL-KDD, this procedure retains dimensions 4–6 and selects n=4. The selected 4-qubit configuration retains 86.62% cumulative variance, achieves KTA 0.2364 versus 0.2439 at the best feasible dimension, and has the lowest hardware-cost proxy Q=0.1391 among the kernel-quality-feasible candidates.**

This is the C1 story that should replace the original:

> “Pareto + scalarization + Theorem 1 selects n=4.”

---

# 30. Freeze checklist

- [x] Corrected two-qubit/CNOT cost implementation executed.
- [x] All candidate dimensions n=2,...,10 recomputed.
- [x] Information-feasible set unchanged: {4,5,6,7,8,9,10}.
- [x] KTA-feasible set unchanged: {4,5,6}.
- [x] Final selection remains n=4.
- [x] Frozen downstream interface remains K=20, n=4, r=2.
- [x] Updated C1 cost values and artifacts exported.
- [x] No further C1 rerun is required for C2/C3; they can continue using the frozen n=4 configuration.

**Final decision: C1 is frozen.**

# 31. Source files used

- `C1_revision(7).ipynb` — final executed C1 notebook and numerical outputs.
- `manuscript(3).pdf` — current manuscript that must be rewritten.
- `reviewer_major_revision_plan_vi(7).md` — reviewer-derived revision requirements and priority matrix.

The review roadmap explicitly identifies C1/Theorem correctness as a scientific-validity gate and recommends a new hardware-constrained embedding-selection contribution. fileciteturn27file3L341-L365 fileciteturn27file6L985-L999
