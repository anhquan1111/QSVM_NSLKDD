
Transactions on Emerging Topics in Computing <onbehalfof@manuscriptcentral.com>
01:03 Thứ 7, 15 thg 8
đến pmtuan, haodp, nguyenvan, anh1303052005, tôi, tetc

TETC-2026-05-0252, "NISQ-Aware Quantum Kernel SVM for Network Intrusion Detection: A Regime-Specific Benchmark on NSL-KDD"

14-Aug-2026

Dear Dr. Pham:

The review process of your manuscript  has been completed. Based on the peer review process for your submission, your manuscript requires a major revision. We invite you to respond to the reviewers' comments, included at the bottom of this letter, and revise your manuscript accordingly.

COMMENTS BY THE EIC:

I concur with the recommendation of the Associate Editor. I gently invite the Authors to address ALL requested modifications as they are aimed at improving the quality of the submission and at the same time remind that TETC policies do not allow a second round of major revisions. Please consult the comments by the Associate Editor and the Reviewers at the bottom of this email.

I take this opportunity to thank the Authors for their manuscript as well as the Associate Editor & Reviewers for their collaboration and time while handling and reviewing this submission.

UPLOAD FORMAT
Please make sure you submit your revision in the following format:
1) a clean-copy version of their revised manuscript without annotations nor highlighted-text.
2) an annotated version where the new/changed text with respect to the previous submission is highlighted in yellow.
3) in the rebuttal letter, a summary of differences and a detailed response to the reviews.

ARTICLE LENGTH
Per Computer Society policies, manuscripts longer than 12 pages in print, will be subject to Mandatory Overlength Page Charges (MOPC).

In case the original submission was less than 12 pages and the revised version, which should include the biographies of all authors (less than 150 words each), exceeds 12 pages, the authors are requested to add the following statement about MOPC in their cover letter:

"ALL submissions exceeding 12 pages at any time of the review process should explicitly report, in the related cover letter, a declaration that the authors are aware of the MOPC policies and, when due, will pay the related charges without requesting any future waiving. Please note that the MOPC policies and the amount of final charges do effectively apply to ALL submissions exceeding 12 pages after final layout of the accepted manuscript."

In case the initial submission was already exceeding 12 pages and the statement above was already included in the cover letter, it is not necessary to add it again to the cover letter related to the new revised version.

AUTHOR LIST
In addition and as a matter of transparency and clarity, per IEEE and Computer Society policies and procedures, the addition/exclusion of new/old people with respect to the group of coauthors which were listed in the initial submission, is not possible without prior written consent by the EiC and can lead to the manuscript desk rejection and the opening of an investigation of all coauthors for potential misconduct.

Furthermore, any change of affiliation of any co-author, since the original submission, must be explicitly reported in a special section to the EiC and AE of the rebuttal document, AND in the cover letter. Also kindly observe that, in case the paper is accepted, no further modifications will be possible to the accepted version. All acknowledgments, funding, updated biographies, etc, should be updated/included in the major/minor revised versions AND described in the cover letter.

REFERENCES AND BIBLIOGRAPHY

TETC has strict policies about the relevance of the references and the number and relevance of self-citations. Only references that are highly relevant to the submission should be included in the bibliography. Overall, the number of bibitems cannot exceed 45. In particular, in case one or more reviewers have recommended/proposed to add citations to some papers which you feel that are either not sufficiently relevant/recent or even not in the domain of your research, please (immediately) inform the Editor-in-Chief (eic.tetc@wpi.edu, tetc@computer.org). Please consider that any communication, will be handled promptly and with high confidentiality.

Any change (addition/deletion) of the bibliography with respect to the previous version, should be highlighted in background yellow in the revised paper. Any change must be explicitly supported by detailed strong reasons in a special section to the EiC and AE of the rebuttal letter. Under no circumstances are changes (adding or removing) of self-citations allowed.

TETC MANUSCRIPT GUIDELINES
Please also check that the revised version complies with ALL journal’s policies and procedures, otherwise the manuscript cannot/will-not be considered further by the journal.

https://www.computer.org/csdl/journal/ec/write-for-
us/15071?title=Author%20Information&periodical=IEEE%20Transactions%20on%20Emerging%20T
opics%20in%20Computing

https://www.computer.org/overlength-submission-policy/

REVISION UPLOAD GUIDELINES

1. To revise your manuscript, you may click here https://ieee.atyponrex.com/submission/submissionBoard/REX-PROD-2-519D6D46-53AC-4E77-8DD3-8B65F5B33A69-F66F357F-24CB-4A20-AEA9-FE1F4990BB4A-53401/current?idtype=external 

2. In addition to preparing the revised version of your manuscript, you must include a point-by-point response to each of the reviewers’ comments in the designated area. You may also include these responses in an attached file with your revised manuscript.

3. Please upload an unmarked version of your manuscript as the main file. You may also include a version with highlighted changes or annotated text as an additional file.

Please note, some reviewers may have recommended that you discuss additional literature when revising your manuscript. If you feel that the recommended literature does not contribute to the scholarly content of the article or is otherwise irrelevant, please note your concerns in your response to reviewer feedback.

Once you have submitted your files, you will receive a confirmation email and an updated manuscript ID. In order to facilitate the timely publication of manuscripts submitted to Transactions on Emerging Topics in Computing, please submit your revised manuscript by 13-Oct-2026 .

Your kind cooperation is greatly appreciated.

Sincerely yours,

Dr. Patrick Schaumont, EIC
Transactions on Emerging Topics in Computing
eic.tetc@wpi.edu
**************************************************************
AE Comments: 
Associate Editor
Comments to the Author:
The reviewers praise the paper’s timeliness and relevance, they consider it well-organized and easy-to-follow. There are deviating assessments about novelty, but the majority of reviewers see sufficient new contribution for considering the paper (the reviewer who does not see novelty provides pointers to papers considered too close). At the same time, the reviewers criticize too generic advantage claims versus evidence on a limited set of methods and by a small numerical improvement, insufficient coverage of literature (including a few non-existing references). Reviewer 1 requests validation on an additional dataset, and multiple reviewers request a comparison with non-SVM methods as a prerequisite for claiming practical advantage. Reviewer 4 has identified several issues or at least unclarities in the theory. Several reviewers criticize the claim on NISQ-ready not being supported by experiments or noisy simulations (one reviewer points to a website offering the latter). Overall, I see a good chance to get the submission into a good shape, albeit with quite some effort, and recommend a Major Revision.

Reviewer Comments
Reviewer: 1

Public Comments (these will be made available to the author)
This paper proposes a NISQ-aware Quantum Support Vector Machine (QSVM) framework for network intrusion detection and investigates the operating regimes in which a quantum kernel provides an advantage over classical SVM baselines. Rather than reporting only aggregate classification metrics, the authors perform additional analyses including entanglement ablation, dimensionality reduction guided by a Pareto search, class-prior shift, temporal shift, and sample-complexity evaluation. The topic is timely and relevant, as understanding when quantum machine learning provides benefits is arguably more important than simply reporting higher accuracy.
Overall, the manuscript is well organized, the proposed framework is easy to follow, and the experimental methodology goes beyond many existing QSVM studies. The inclusion of stress tests and ablation analyses represents a valuable contribution. However, several methodological issues should be addressed before the conclusions can be fully supported.
First, the related work is incomplete. The introduction states that previous QSVM-based NIDS studies mainly report aggregate accuracy without deeper analysis. However, an important recent work is missing: "Benchmarking quantum machine learning methods for intrusion detection on noisy quantum computers" (Quantum Machine Intelligence, 2026). This work should be discussed explicitly, together with a clear explanation of how the proposed framework differs from and advances beyond it. More generally, Table I should include more recent literature, as quantum machine learning is evolving rapidly and several relevant works published during 2025–2026 are not considered.
Second, the experimental evaluation relies almost exclusively on NSL-KDD, which is an aging benchmark with well-known limitations. The manuscript mentions supplementary experiments on UNSW-NB15, but no supplementary material was available during the review process. Since the conclusions concern the practical operating regimes of QSVMs, validation on at least one additional modern intrusion detection dataset is highly desirable.
The hyperparameter selection protocol is asymmetric. The QSVM regularization parameter is fixed to C = 1.0, whereas the classical SVM baselines use validation-selected values. The authors should justify this design choice more clearly and provide either a sensitivity analysis of the QSVM using different C values or evidence that the reported conclusions are robust with respect to the choice of C. Without such analysis, it is difficult to determine whether the reported performance differences are influenced by the selected regularization parameter.
The manuscript also overstates some of its conclusions. In particular, statements such as "The quantum advantage is real and measurable in two regimes…" are stronger than the presented evidence supports. The experiments compare the proposed QSVM against several SVM configurations, not against the full spectrum of modern classical machine learning methods. Therefore, the manuscript cannot claim a general quantum advantage. The conclusions should be reformulated to clarify that the observed advantage is limited to the evaluated baselines and experimental setup.
While SVMs are natural comparators for QSVMs, the manuscript also makes practical deployment claims. These would be considerably stronger if the evaluation included competitive tabular learning methods such as XGBoost, CatBoost, TabNet, or FT-Transformer. Alternatively, the practical claims should be softened accordingly.
Regarding the NISQ-feasibility claim, the additional experiments evaluate only finite-shot estimation error. Although this is useful, it does not capture realistic hardware noise such as gate errors, decoherence, or readout errors. Consequently, the current evidence is insufficient to support the NISQ-feasibility claims. The authors are encouraged to include experiments using realistic backend noise models, such as IBM FakeBackends or Aer noise models, or to appropriately qualify their claims.
I also have a few additional comments. The manuscript states that QSVMs are particularly beneficial in the low-data regime. However, the sample-complexity figure appears to show that the QSVM consistently outperforms the classical SVM across all evaluated training sizes. It would therefore be useful to identify whether there exists a crossover point beyond which the classical SVM becomes preferable, or clarify why such a point is not observed.
The results reported in Table VI for N = 1000 appear inconsistent with those reported in Table IV, and the observed differences should be explained. Moreover, the absolute F1 values obtained by the classical SVM baselines appear relatively low compared with values commonly reported on NSL-KDD. Including additional references would help contextualize these results.
Finally, I was unable to access the supplementary material referenced in the manuscript. This should be provided to reviewers, especially if it contains the additional experiments on UNSW-NB15.
Recommendation: Major Revision. The paper has the potential to make a valuable contribution, but additional experimental validation, a more complete discussion of related work, a stronger justification of the experimental methodology, and a more balanced interpretation of the results are necessary before it can be considered for publication.

Reviewer: 2

Public Comments (these will be made available to the author)
The classical baselines are limited to SVM variants; no deep tabular baselines (TabNet, Random Forest or Xgboost) are tested despite these being standard, often stronger,
comparators for this kind of data. The authors acknowledge this (Sec. VII-C) but it undercuts the paper's practical claims about "when quantum is worth it," since the real competitor in industry is rarely an SVM but one of the algorithms mentioned.

As an argument pro kernel methods it is stated "...so the barren-plateau pathology of variational methods [10] is avoided". While this is true, it should be mentioned that
the conceptually similar problem for kernel methods is named "exponential concentration of the kernel matrix".

Sample sizes throughout the ablation and prior-shift studies are rather small (N_train=1000, five seeds) relative to the full 125,973-row training set, and effect sizes/CIs are computed across only five seeds rather than proper resampling — the paper defends this choice (Sec. IV-D) but it's a thin statistical base for claims like "large effect size".
The temporal-shift result (non-significant McNemar test) and the perturbation-sensitivity result are honestly reported as null/negative findings, which is a genuine strength — but the "regime map" framing then risks overselling: three positive regimes are given full statistical treatment while the two negative regimes get comparatively brief qualitative explanation ("wrapped phase encoding" mechanism) without a matching effect-size/CI treatment.

Reference [15] (Payares & Martínez-Santos, SPIE 11699) is cited with article number "116990F," but the actual published article number is 116990B (DOI 10.1117/12.2593297) — a factual citation error.

Reference [26] (Rahman, Kayed, Aljahdali, Ali, "Quantum machine learning for cybersecurity: a comprehensive review," IEEE Access vol. 11, pp. 97550–97574, 2023) could not be located under this title or author combination in IEEE Access or elsewhere — this citation looks fabricated or badly misattributed and should be verified.




Reviewer: 3

Public Comments (these will be made available to the author)
The manuscript „NISQ-Aware Quantum Kernel SVM for Network Intrusion Detection: A Regime-Specific Benchmark on NSL-KDD” is a use case study of using quantum support vector machines (QSVM) to classify network intrusion. In particular, the authors focus on a depth-2 ZZ FeatureMap on 4-qubits applied to the NSL-KDD dataset. The authors find that on the problem setup studied in the paper, the QSVM outperforms its classical competitors.
The authors set up the problem in a clearly defined manner and generally approach the results with a reasonable methodological rigor (entanglement ablation, multi-seed runs, sanity checks, etc.). There are, however, several severe concerns which is why I cannot recommend the publication of the manuscript in IEEE Transactions on Emerging Topics in Computing.

1) The core model studied in the paper is a standard QSVM using the Qiskit-style ZZFeatureMap with full entanglement, here instantiated at only 4 qubits and depth 2 after PCA. This is one of the most common baseline configurations in quantum-kernel machine learning and has already been extensively explored on low-dimensional tabular benchmarks, including intrusion-detection datasets. As a result, the paper’s technical novelty is limited: it does not introduce a new quantum kernel, a new feature map, a new training method, a hardware implementation, or a theoretical result establishing a new regime of advantage.

2) The claim of outperforming the classical baseline rests on a marginal (F1 0.854 compared to 0.838) improvement which hardly justifies any advantage claims. In particular, any structural quantum advantage in this setting needs to be motivated is very unlikely to originate from generic FeatureMaps as the one studied in the manuscript (see e.g. their reference [20]).

3) The structure of the paper, in particular the theory section is confusing. The propositions are well established facts and their framing as propositions which are subsequently proofed is inappropriate.

4) Experimental limitations: all experiments are conducted on an extremely small number of qubits with a very limited data set size. Particularly the framing as NISQ-aware is curious because all experiments are purely done in (ideal) simulations.

Given the results of the paper are already established in numerus previous work (e.g. in other benchmarking studies such as arXiv:2403.07059 or arXiv:2409.04406), I do not recommend a publication of the manuscript in IEEE Transactions on Emerging Topics in Computing.


Reviewer: 4

Public Comments (these will be made available to the author)
The paper does very good work to shift the conversation from "is QSVM better than classical?" to "when is QSVM better than classical?" The paper maps well to rising concerns about being more targeted and more thoughtful about using quantum machine learning for certain problems, and their proposed "regime-specific benchmark" is a good step in the right direction to make that happen.

The question is already being asked in other areas, such as malware detection. For example:
N. M. Carducci, "When Does Quantum Computing Provide Advantage for Malware Detection? Structural Complexity and the Intermediate Complexity Window," 2026 IEEE International Conference on AI and Data Analytics (ICAD), Boston, MA, USA, 2026, pp. 1-7, doi: 10.1109/ICAD69378.2026.11609075.

I think Theorem 1 might be misstated. It says F~(4) > F~(3) but the opposite is shown in Table III, where F~(4) = 0.471 and F~(3) = 0.628. And I think Theorem 1 ends up failing on its claim that n* = 4 is the maximizer of J. Also in Table III, in the J(n) |α=β=γ=1/3 column, we see consistent decreases and n = 2 is the maximum, though it is simply marked not member of Pareto. When coupled with the fact that V(n) always increases and F~(n) and Q(n) always decreases, that may mean Pareto might not be doing any filtering at all, so it might not be a contribution after all.

The paper claims reproducibility but doesn't provide any of the machinery to do so; it simply asserts the implementation has been released. It would be necessary for the paper to include a link or some other way of obtaining the machinery.

I am not sure I follow Proposition 3; this paper cites another paper for it but doesn't prove or derive itself.

I don't know if I see any number for the rare-attack subset, so it is not possible to verify the paper's claim that "At N=500 QSVM-ZZ still leads by +6.7 points over SVM-RBF on the rare-attack subset, with a Cohen’s d of +0.68 on the per-sample decision margins."

The paper does not engage with tuning the quantum kernel, but it does tune the classical implementation. The paper says that this is to avoid bias, but there is literature on quantum tuning, and I think the paper would be better if it engaged with that literature and make a more refined decision on whether or not to tune the quantum kernel. Because not tuning is a design choice that the paper does not comment on, and that design choice might end up being part of the reason behind the paper's claim that under "heavy feature perturbation (σ=0.20) the quantum kernel degrades." 