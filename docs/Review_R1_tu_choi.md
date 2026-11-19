TETC-2026-05-0252.R1, "NISQ-Aware Quantum Kernel SVM for Network Intrusion Detection: A Regime-Specific Benchmark on NSL-KDD"

11-Nov-2026

Dear Dr. Pham:

I regret to inform you that based on the reviewer feedback, we could not recommend publishing your paper in  Transactions on Emerging Topics in Computing.  The comments of the reviewers are included below.

COMMENTS BY THE EIC:

I have carefully looked at the full picture, including reading the paper, the comments of the reviewers and the Editor. I fully concur with the recommendation of the AE. I remark that TETC policies do not allow the resubmission of a previously rejected paper, (by TETC) or modified versions thereof.

Thank you for considering our publication. I hope this outcome does not discourage you from future submissions to our journal.

Sincerely,

Dr. Patrick Schaumont, EIC
Transactions on Emerging Topics in Computing
eic.tetc@wpi.edu
**************************************************************
AE Comments: 
Associate Editor
Comments to the Author:
The modifications are drastic, to the extent one has difficulties connecting the revision to the original submission; every figure and table is now replaced with a different result. Heavy use of AI stated in the “Acknowledgements” section is felt subjectively when reading the text, which is now 18 pages long and exceeds the page limits. Two out of three reviewers still have major reservations about the revised manuscript. It is at least unusual to refer to reviewers in the paper text; at the same time their influence on the changed manuscript content seems to be rather major, to the extent one could question whether the authorship is still completely with the original authors. Overall, the manuscript does not seem to meet the bar even after an extensive rewrite, and I recommend rejection.

Reviewer Comments
Reviewer: 1

Public Comments (these will be made available to the author)
The comments and concerns raised in the previous review have been adequately addressed. I recommend only a few minor revisions to further improve the clarity and presentation of the manuscript:
1. The title should better reflect the broader scope of the study, as the evaluation is not limited to NSL-KDD and also includes UNSW-NB15.
2. The abstract is excessively long and detailed. It should be substantially shortened, focusing on the problem, methodology, main findings, and key contribution, while moving detailed numerical results and protocol-specific details to the main text.
3. Section 2E should be revised to avoid explicitly referring to reviewers or the review process. These points could instead be presented directly as methodological motivation or design considerations.
4. A final proofreading pass is recommended to improve readability, particularly by shortening some dense sentences in the abstract.
Overall, the manuscript has been substantially improved, and I believe these minor revisions would further enhance its clarity and presentation.


Reviewer: 2

Public Comments (these will be made available to the author)
The revised manuscript is a more rigorous and more transparent paper than the original submission, and I thank the authors for the substantial effort invested. The result, however, is a heavily qualified and largely inconclusive benchmark of a standard configuration. Its remaining positive findings are either reproduced by a classical kernel or correspond to known phenomena. The lack of novelty was the principal reason for my original recommendation, and it remains unresolved. I therefore do not recommend publication in IEEE Transactions on Emerging Topics in Computing.

Reviewer: 3

Public Comments (these will be made available to the author)
The revision substantially improves the manuscript, but it also represents an unusually extensive repositioning—from a claimed quantum advantage to a regime-specific benchmark with largely negative or inconclusive findings—which requires careful validation of the revised contributions. Most of my original concerns have been addressed; however, I recommend major revision before publication for the following reasons:

Generalisation and data duplication: The acknowledged train–test duplication, particularly in UNSW-NB15, remains an unresolved threat to the central comparisons. Please provide a sensitivity analysis excluding test records duplicated in the training set, at least for the principal comparative and cross-dataset findings. Merely listing this issue as future work is insufficient.

Kernel concentration and causal Interpretation: The measured power-law trend over a limited range of circuit widths does not establish exponential concentration. Likewise, the correlation between kernel dispersion and classification performance does not establish causality. Please either provide stronger supporting analyses or consistently describe these observations as empirical findings compatible with kernel concentration. Claims that improved hardware cannot expand the useful regime should also be qualified.

Statistical Interpretation: A non-significant difference does not establish “parity” or equivalence. Please replace such wording with “no statistically significant difference was detected,” unless an appropriate equivalence or non-inferiority analysis is provided. Recommendations about when to use the quantum kernel should also reflect their sensitivity to the chosen multiplicity correction.

Internal Consistency: Please reconcile the contradictory statements about whether rare-attack enrichment removes the sample-size crossover. The design does not establish this conclusion. Similarly, claims of robustness across all tested selection thresholds must be reconciled with the reported recovery rate of only 7/10 runs for one threshold setting.

Noise validation:  The additional noise simulation is a useful preliminary check, but a single run does not support general claims that noise is immaterial or leaves the operating point unchanged. Please extend the repeated-run evaluation or restrict the conclusions explicitly to the single tested configuration.
These requests do not require hardware execution or an exhaustive expansion of the classical baselines. After these targeted revisions, publication as a carefully scoped empirical benchmark may be appropriate; acceptance in the current form would be premature.
