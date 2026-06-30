# PLAN_PAPER2_RELIABILITY_V2.md

# Reliability and Calibration Analysis of Quantum Kernel Intrusion Detection Systems

---

# 1. Motivation

Paper 1 trả lời:

> Khi nào Quantum Kernel SVM đạt lợi thế hiệu năng?

Paper 2 trả lời:

> Các dự đoán của Quantum Kernel SVM có đủ đáng tin cậy để triển khai thực tế hay không?

Khác với Paper 1 tập trung vào:

* Accuracy;
* Quantum advantage;
* Kernel geometry;
* Sample complexity;
* Robustness.

Paper 2 tập trung vào:

* Reliability;
* Calibration;
* Confidence estimation;
* Deployment readiness.

---

# 2. Research Gap

Các nghiên cứu Quantum IDS hiện tại chủ yếu:

* báo cáo Accuracy;
* báo cáo F1-score;
* benchmark comparison.

Nhưng hầu như chưa nghiên cứu:

### G1. Calibration của Quantum Kernel.

### G2. Reliability trên các lớp tấn công hiếm.

### G3. Reliability dưới distribution shift.

### G4. Khả năng cải thiện reliability bằng probability calibration.

---

# 3. Research Questions

## RQ1

Quantum Kernel có bị over-confident hay không?

---

## RQ2

Các dự đoán trên nhóm tấn công hiếm có đáng tin cậy hay không?

---

## RQ3

Độ tin cậy của Quantum Kernel thay đổi như thế nào dưới distribution shift?

---

## RQ4

Platt Scaling cải thiện calibration đến mức nào?

---

# 4. Mapping giữa Paper 1 và Paper 2

| Paper 1                     | Paper 2                 |
| --------------------------- | ----------------------- |
| Accuracy                    | Reliability             |
| Quantum advantage           | Confidence analysis     |
| Robustness                  | Calibration degradation |
| Distribution shift          | Reliability under shift |
| Low-data advantage          | Low-data reliability    |
| Kernel geometry             | Không sử dụng           |
| KTA                         | Không sử dụng           |
| Entanglement ablation       | Không sử dụng           |
| Sample complexity advantage | Không sử dụng           |

---

# 5. Main Contributions

---

## C1. Calibration Analysis

### Vai trò

Contribution chính.

### Notebook nguồn

C5 - c5_confidence_calibration_multirun.ipynb

### Section tương ứng trong paper

Section IV - Calibration Analysis.

### Metrics

* ECE;
* Brier Score;
* Reliability Diagram.

### Figures sinh ra

* Figure 1;
* Figure 2;
* Figure 3.

### Tables sinh ra

* Table II.

### Narrative

Paper 1:

> accuracy.

Paper 2:

> confidence quality.

---

## C2. Rare Attack Reliability

### Vai trò

Contribution chính.

### Notebook nguồn

C5.

### Metrics

* Precision;
* Recall;
* PR Curve;
* AUC-PR.

### Figures

* Figure 4.

### Tables

* Table III.

### Terminology

Không dùng:

* U2R/R2L.

Dùng:

* Rare attacks;
* Minority attack group.

### Narrative

Paper 1:

> detection performance.

Paper 2:

> reliability on minority attacks.

---

## C3. Reliability under Prior Shift

### Vai trò

Contribution chính.

### Notebook nguồn

C4 - c4_robustness_distribution_shift_multirun_fixed.ipynb

### Chỉ sử dụng

* Balanced;
* Attack-heavy;
* DoS-only.

### Metrics

* ECE;
* Brier Score;
* AUC-PR.

### Figures

* Figure 5.

### Tables

* Table IV.

### Narrative

Paper 1:

> robustness.

Paper 2:

> calibration degradation.

---

## C4. Probability Calibration using Platt Scaling

### Vai trò

Contribution chính.

### Notebook nguồn

C5.

### Metrics

* ECE;
* Brier Score.

### Figures

* Figure 6.

### Tables

* Table V.

### Narrative

Paper 2 không chỉ đánh giá reliability mà còn nghiên cứu khả năng cải thiện reliability.

---

# 6. Additional Analyses

---

## A1. Low-data Reliability

### Notebook nguồn

C6 - learning_curve_sample_complexity.ipynb

### Không sử dụng

* Learning curve F1;
* Sample complexity advantage.

### Chỉ sử dụng

* ECE(N);
* Brier(N);
* AUC-PR(N).

### Vai trò

Discussion subsection.

### Narrative

Paper 1:

> Quantum advantage under low-data.

Paper 2:

> Reliability under label scarcity.

---

## A2. Temporal Reliability

### Notebook nguồn

C4.

### Không sử dụng

Temporal robustness.

### Chỉ sử dụng

* ECE temporal;
* Brier temporal.

### Vai trò

Discussion hoặc Appendix.

### Narrative

Calibration degradation under temporal shift.

---

# 7. Excluded Contents

## C1

* Pareto optimization;
* Qubit selection.

## C3

* Kernel geometry;
* KTA;
* Entanglement ablation.

## C4

* Gaussian perturbation.

## C6

* Learning curve advantage;
* Sample complexity advantage.

---

# 8. Notebook → Paper Mapping

| Notebook                 | Vai trò             |
| ------------------------ | ------------------- |
| C5 Calibration           | Contribution chính  |
| C5 Rare attacks          | Contribution chính  |
| C4 Prior shift           | Contribution chính  |
| C5 Platt scaling         | Contribution chính  |
| C6 Low-data reliability  | Additional analysis |
| C4 Temporal reliability  | Additional analysis |
| C4 Gaussian perturbation | Không dùng          |
| C3 Geometry/KTA          | Không dùng          |
| C6 Learning curve F1     | Không dùng          |

---

# 9. Priority Levels

## Priority A (Bắt buộc)

* Calibration;
* Rare attacks;
* Prior shift;
* Platt scaling.

---

## Priority B (Nên có)

* Random Forest;
* XGBoost;
* Brier Score;
* Cohen's d.

---

## Priority C (Nếu còn thời gian)

* Low-data reliability;
* Temporal reliability;
* MLP.

---

# 10. Baselines

## Quantum

* QSVM-ZZ.

## Classical

* SVM-RBF;
* Random Forest;
* XGBoost.

## Deep Learning

* MLP (optional).

---

# 11. Figures

Figure 1:

Reliability Diagram.

---

Figure 2:

ECE comparison.

---

Figure 3:

Brier Score comparison.

---

Figure 4:

PR Curve của Rare Attacks.

---

Figure 5:

Calibration degradation dưới Prior Shift.

X-axis:

Balanced → Attack-heavy → DoS-only.

Y-axis:

ECE.

Models:

* QSVM;
* RBF;
* RF;
* XGB.

---

Figure 6:

Before vs After Platt Scaling.

---

Figure 7:

Low-data reliability curve.

---

Figure 8:

Temporal calibration degradation.

---

# 12. Tables

Table I:

Baseline models.

---

Table II:

Calibration metrics.

* ECE;
* Brier Score;
* Macro-F1.

---

Table III:

Rare attack metrics.

* Precision;
* Recall;
* AUC-PR.

---

Table IV:

Reliability under Prior Shift.

---

Table V:

Before vs After Platt Scaling.

---

# 13. Tasks for C5

## File

c5_confidence_calibration_multirun.ipynb

---

## Đã hoàn thành

### Calibration Analysis (C1)

* [x] Multi-run (5 seeds);
* [x] Mean ± std;
* [x] Reliability Diagram;
* [x] ECE.

### Rare Attack Analysis (C2)

* [x] Rare attack analysis;
* [x] PR Curve;
* [x] AUC-PR;
* [x] Error analysis.

---

## Cần chỉnh sửa

### [C5-1]

Thêm Brier Score.

Phục vụ:

* C1;
* Table II;
* Figure 3.

---

### [C5-2]

Tính Cohen's d cho:

* ECE;
* Brier Score;
* AUC-PR.

---

### [C5-3]

Chuẩn hóa terminology.

Không dùng:

* U2R/R2L.

Dùng:

* Rare attacks;
* Minority attack group.

---

### [C5-4]

Giảm vai trò của margin analysis.

Giữ trong notebook.

Không đưa vào contribution chính.

---

### [C5-5]

Implement Platt Scaling.

Sinh ra:

* Figure 6;
* Table V.

Phục vụ:

Contribution C4.

---

### [C5-6]

Thêm Random Forest baseline.

---

### [C5-7]

Thêm XGBoost baseline.

---

## Có thể bổ sung

* MLP baseline.

---

# 14. Tasks for C4

## File

c4_robustness_distribution_shift_multirun_fixed.ipynb

---

## Giữ lại

### Prior Shift

* Balanced;
* Attack-heavy;
* DoS-only.

---

## Không sử dụng

* Gaussian perturbation.

---

## Cần chỉnh sửa

### [C4-1]

Đổi metric chính.

Từ:

* Macro-F1.

Sang:

* ECE;
* Brier Score;
* AUC-PR.

---

### [C4-2]

Tạo Calibration Degradation Curve.

---

### [C4-3]

Tính Cohen's d cho ECE.

---

### [C4-4]

Sinh Table IV.

---

### [C4-5]

Thêm Random Forest.

---

### [C4-6]

Thêm XGBoost.

---

## Có thể bổ sung

### Temporal Reliability

Metrics:

* ECE temporal;
* Brier temporal.

Vai trò:

Discussion hoặc Appendix.

---

# 15. Tasks for C6

## File

learning_curve_sample_complexity.ipynb

---

## Không sử dụng

Learning curve F1.

---

## Cần chỉnh sửa

### [C6-1]

ECE(N).

### [C6-2]

Brier(N).

### [C6-3]

AUC-PR(N).

---

## Vai trò

Additional Analysis.

Không phải contribution chính.

---

# 16. General Tasks

## Đồng bộ protocol với Paper 1

* seed = {0,1,2,3,4};
* mean ± std;
* Cohen's d.

---

## Đồng bộ Figure

* font;
* màu sắc;
* style.

---

## Đồng bộ Table

Format giống Paper 1.

---

## Chuẩn hóa terminology

Dùng:

* Rare attacks;
* Prior shift;
* Calibration degradation.

Không dùng:

* U2R/R2L;
* Robustness under shift.

---

# 17. Optional Contents

Có thể bỏ nếu gần deadline:

* MLP;
* Temporal reliability;
* Low-data reliability.

Không nên bỏ:

* Calibration;
* Rare attacks;
* Prior shift;
* Platt scaling.

---

# 18. Expected Claims

Không claim:

> Quantum outperforms all baselines.

Claim:

> Quantum kernels provide more reliable confidence estimates under several challenging scenarios.

---

# 19. Limitations

* Rare attacks có rất ít mẫu;
* NSL-KDD là dataset cũ;
* Chỉ sử dụng một dataset;
* QSVM chạy trên simulator;
* Không đánh giá trên hardware thực;
* Platt Scaling có giới hạn.

---

# 20. Draft Paper Structure

I. Introduction

II. Background

III. Experimental Setup

IV. Calibration Analysis

V. Rare Attack Reliability

VI. Reliability under Prior Shift

VII. Probability Calibration

VIII. Additional Analyses

IX. Discussion and Limitations

X. Conclusion
