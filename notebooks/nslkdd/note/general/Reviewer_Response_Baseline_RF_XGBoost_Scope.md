# Response to Reviewer — Scope of the Classical Baseline Expansion

## Reviewer concern

The reviewer noted that the original benchmark relied primarily on SVM variants and therefore did not provide a sufficiently broad comparison against strong classical tabular learning methods. The reviewer specifically requested the inclusion of **XGBoost** and **Random Forest**, and additionally suggested **CatBoost** and potentially **deep tabular models** such as TabNet or FT-Transformer if resources permitted.

## Response

We thank the reviewer for this constructive suggestion. We agree that evaluating the proposed QSVM against strong non-SVM classical baselines is important for assessing its practical competitiveness.

In the revised benchmark, we therefore expanded the classical baseline suite to include **Random Forest (RF)** and **XGBoost (XGB)**. These models were incorporated into the same controlled experimental framework as the existing SVM baselines and quantum models. In particular, the revised experiments use the fixed C1-selected representation, dedicated tuning data, symmetric model selection procedures, fixed random seeds, and repeated 10-run evaluation. The same expanded baseline family is also used in the subsequent regime-specific and cross-dataset analyses.

The revised baseline family is therefore:

1. QSVM-ZZ
2. QSVM-Z
3. SVM-Linear
4. SVM-Poly2
5. SVM-RBF
6. Random Forest
7. XGBoost

This change directly addresses the central concern that the original comparison was overly SVM-centric. The revised results also provide a substantially stronger practical comparison: on the main C2 benchmark, XGBoost obtained the highest mean Macro-F1 (0.8503), while QSVM-ZZ achieved 0.8469 and Random Forest achieved 0.8446. Thus, the revised study does not assume or enforce a quantum advantage; instead, it evaluates QSVM-ZZ against strong classical alternatives and reports the outcome transparently.

## Rationale for the selected additional baselines

We chose **Random Forest and XGBoost** as representative strong classical ensemble baselines for the following reasons.

### 1. They directly address the reviewer’s primary baseline concern

The main concern was that SVM-only comparisons were insufficient for judging practical competitiveness. RF and XGBoost introduce two substantially different tree-based ensemble approaches and therefore provide a stronger comparator family than adding another kernel-SVM variant.

### 2. They provide complementary classical model classes

Random Forest represents a bagging-based tree ensemble, whereas XGBoost represents gradient-boosted decision trees. Evaluating both gives the benchmark coverage across two widely used ensemble paradigms rather than relying on a single classical family.

### 3. They are particularly relevant to the tabular nature of the datasets

NSL-KDD and UNSW-NB15 are structured tabular intrusion-detection datasets. Tree ensembles are therefore natural classical reference points for this experimental setting. Their inclusion also allows the study to test whether the proposed quantum kernel remains competitive when compared with non-kernel tabular learners.

### 4. They preserve the controlled scope of the study

The central objective of the revised paper is not to establish a leaderboard across all possible tabular architectures. Rather, the objective is to study **regime-dependent behavior of a NISQ-aware quantum kernel under controlled and reproducible comparisons**.

Expanding the baseline family indefinitely would introduce additional model families, tuning spaces, computational budgets, and implementation choices that are not central to this objective. We therefore prioritized representative strong classical ensembles while keeping the benchmark protocol consistent across datasets, sample sizes, and operating regimes.

## Why CatBoost and deep tabular models were not added

We appreciate the reviewer’s additional suggestion concerning CatBoost and deep tabular architectures such as TabNet or FT-Transformer. These models were considered as possible extensions, but we did not include them in the final benchmark.

This was a deliberate scope decision rather than an assessment that these models are unimportant.

First, **CatBoost would constitute another member of the boosted-tree family**, while XGBoost already provides a strong gradient-boosting representative in the revised benchmark. Adding CatBoost would increase the breadth of the baseline suite, but would not substantially change the primary comparison structure or introduce a fundamentally different experimental question.

Second, **TabNet and FT-Transformer introduce a separate deep tabular modeling family** with substantially different architecture, optimization, regularization, and hyperparameter considerations. Including these models rigorously would require an additional methodological layer to ensure that their training budgets and tuning procedures were comparable with the existing models. Such an extension would broaden the scope from controlled quantum-kernel benchmarking toward a much larger survey of tabular-learning architectures.

Third, the revised study already substantially increases experimental breadth through strong classical ensemble baselines, 10-run repeated evaluation, symmetric hyperparameter tuning, multiple training-set sizes, regime-specific stress tests, a second dataset (UNSW-NB15), and additional noise-aware quantum validation. The existing revision therefore already addresses the central weakness identified by the reviewer without turning the study into an exhaustive survey of tabular models. The current revision documentation explicitly distinguishes the **minimum baseline requirement** from the reviewer’s broader recommendation and avoids claiming coverage of all strong tabular baselines.

## Interpretation of the revised benchmark

Importantly, the expanded baseline study changes the interpretation of the paper in a more conservative and informative direction.

The revised experiments show that QSVM-ZZ is **competitive with strong classical baselines in some settings, but does not universally outperform them**. In the main C2 experiment, XGBoost achieved the highest mean Macro-F1, while QSVM-ZZ remained very close to both XGBoost and Random Forest. This is treated as a point-estimate comparison rather than as a collection of unsupported statistical superiority claims.

Accordingly, we have avoided claims such as “QSVM universally outperforms classical ML” or “quantum advantage” based solely on these comparisons. The revised manuscript instead frames the contribution as a **regime-specific empirical benchmark of NISQ-aware quantum kernel learning against representative strong classical baselines**.

## Scope statement

We therefore respectfully consider the revised baseline expansion to have addressed the primary reviewer concern by moving beyond an SVM-only benchmark and incorporating **Random Forest and XGBoost** as strong representative classical tabular baselines.

We acknowledge that CatBoost and deep tabular architectures could provide additional breadth. However, we consider their inclusion beyond the focused scope of the present study, and we have correspondingly avoided claiming that the benchmark exhaustively covers all strong tabular-learning methods.

## Suggested concise response for the rebuttal letter

> **Response:** We thank the reviewer for highlighting the need for stronger classical baselines. We substantially expanded the benchmark by adding Random Forest and XGBoost, while retaining the SVM family and matched quantum controls. These models were evaluated under the same controlled protocol, including dedicated hyperparameter tuning, fixed seeds, and 10-run repeated evaluation. This revision removes the original reliance on SVM-only comparisons and enables a more meaningful assessment of practical competitiveness. In the revised main benchmark, XGBoost achieved the highest mean Macro-F1 (0.8503), followed by QSVM-ZZ (0.8469) and Random Forest (0.8446), and we report this result without assuming a quantum advantage.
>
> We also considered the reviewer’s suggestion to include CatBoost and deep tabular models such as TabNet or FT-Transformer. We ultimately limited the expanded baseline suite to representative strong ensemble methods in order to preserve a controlled and reproducible experimental scope. CatBoost would provide another boosted-tree representative, while TabNet and FT-Transformer would introduce a substantially different deep-tabular modeling family with additional architecture and optimization choices. Since the main objective of this work is regime-specific evaluation of NISQ-aware quantum kernels rather than an exhaustive survey of all tabular learners, we prioritized representative classical ensemble baselines and clearly state this scope limitation in the revised manuscript.

---

# Ghi chú nội bộ — không gửi kèm rebuttal

*(Quan bổ sung 2026-09-03 khi đưa file vào repo)*

**Đã sửa hai chỗ so với bản Quang Anh gửi:**

1. **Gỡ dấu trích dẫn nội bộ.** Bản gốc còn 5 chuỗi dạng `citeturn23file4L516-L535`
   kèm ký tự private-use U+E200–E202 do công cụ soạn thảo chèn vào. Gửi nguyên như
   vậy thì reviewer sẽ thấy rác giữa câu.

2. 🔴 **XGBoost `0.8493` → `0.8503`.** Số `0.8493` là kết quả trên máy Quang Anh;
   artifact đang nằm trong repo (`results/nslkdd/c2_revision/c2_aggregate.csv`
   nhánh `revisionC4`) ghi **0.85031**. Rebuttal bắt buộc phải khớp file ta công bố
   kèm bài, nếu không reviewer đối chiếu là thấy ngay.

**Vì sao lệch — đã kiểm chứng, không phải bug:**

So `master` (máy Quang Anh) với `revisionC4` (máy Quan), cả 7 model:

| Model | Lệch `f1_macro_mean` |
|---|---|
| QSVM_ZZ, QSVM_Z | **0.000000** (trùng khít) |
| SVM_Linear, SVM_RBF, RandomForest | **0.000000** |
| SVM_Poly2 | +0.000331 |
| XGBoost | +0.001010 |

`kta_mean` của cả hai model quantum cũng trùng khít. Nghĩa là **mọi số quantum —
phần lõi của bài — tái tạo chính xác giữa hai máy**; chỉ đúng hai baseline cổ điển
lệch, và cả hai đều đã có trong nhật ký:

- **XGBoost** phụ thuộc số thread ngay cả khi `n_jobs=1` (`tree_method='hist'`) —
  Phát hiện #6 trong `docs/revision/02_PROGRESS.md`.
- **SVM_Poly2** lệch do một ô cache C2 (run 3) không tái tạo được — Phát hiện #7.

**Kết luận không đổi ở cả hai máy**: XGBoost cao nhất (0.8503 hoặc 0.8493), rồi
QSVM-ZZ (0.8469), rồi Random Forest (0.8446). Thứ tự y hệt.

**Việc cần làm khi viết bài**: mục reproducibility phải nói rõ XGBoost dao động
~±0.001 giữa các máy, và số công bố lấy từ artifact trong repo. Nói trước là cẩn
thận; để reviewer tự phát hiện thì thành thiếu nhất quán.
