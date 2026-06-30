# PLAN_PAPER2_RELIABILITY.md

# Reliability and Calibration Analysis of Quantum Kernel Intrusion Detection Systems

---

# 1. Motivation

Paper 1 trả lời:

> Khi nào QSVM đạt lợi thế hiệu năng?

Paper 2 trả lời:

> Các dự đoán của QSVM có đủ đáng tin cậy để triển khai thực tế hay không?

Trọng tâm chuyển từ:

* Accuracy
* Quantum advantage

sang:

* Reliability
* Calibration
* Confidence
* Deployment readiness

---

# 2. Research Gap

Các nghiên cứu Quantum IDS hiện tại chủ yếu báo cáo:

* Accuracy
* F1-score

Nhưng chưa nghiên cứu:

1. Calibration của Quantum Kernel.
2. Reliability trên lớp hiếm.
3. Reliability dưới distribution shift.
4. Khả năng hiệu chỉnh xác suất.

---

# 3. Research Questions

RQ1. Quantum Kernel có bị over-confident hay không?

RQ2. Các dự đoán trên nhóm tấn công hiếm có đáng tin cậy hay không?

RQ3. Độ tin cậy thay đổi như thế nào dưới distribution shift?

RQ4. Platt Scaling cải thiện calibration đến mức nào?

---

# 4. Main Contributions

## C1. Calibration Analysis

Nguồn:

C5 - c5_confidence_calibration_multirun.ipynb

Metrics:

* ECE
* Brier Score
* Reliability Diagram

---

## C2. Rare Attack Reliability

Nguồn:

C5

Metrics:

* Precision
* Recall
* PR Curve
* AUC-PR

Terminology:

* Rare attacks
* Minority attack group

---

## C3. Reliability under Prior Shift

Nguồn:

C4 - c4_robustness_distribution_shift_multirun_fixed.ipynb

Chỉ sử dụng:

* Balanced
* Attack-heavy
* DoS-only

Metrics:

* ECE
* Brier Score
* AUC-PR

---

## C4. Probability Calibration using Platt Scaling

Nguồn:

C5

Metrics:

* ECE
* Brier Score

Before calibration vs After calibration.

---

# 5. Additional Analyses

## A1. Low-data Reliability

Nguồn:

C6 - learning_curve_sample_complexity.ipynb

Không dùng:

* F1 learning curve

Chỉ dùng:

* ECE(N)
* Brier(N)
* AUC-PR(N)

Narrative:

Reliability under label scarcity.

---

## A2. Temporal Reliability

Nguồn:

C4

Không dùng:

Temporal robustness.

Chỉ dùng:

* ECE temporal
* Brier temporal

Narrative:

Calibration degradation under temporal shift.

---

# 6. Excluded Contents

## C3

* Kernel geometry
* KTA
* Entanglement ablation

## C4

* Gaussian perturbation

## C6

* Sample-complexity advantage

## C1

* Pareto optimization

---

# 7. Notebook → Paper Mapping

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

# 8. Baselines

Quantum:

* QSVM-ZZ

Classical:

* SVM-RBF
* Random Forest
* XGBoost

Deep Learning:

* MLP (optional)

---

# 9. Figures

Figure 1: Reliability Diagram

Figure 2: ECE comparison

Figure 3: Brier Score comparison

Figure 4: PR Curve of rare attacks

Figure 5: Calibration degradation under prior shift

Figure 6: Before vs After Platt Scaling

Figure 7: Low-data reliability curve

Figure 8: Temporal calibration degradation

---

# 10. Tables

Table I: Baselines

Table II: Calibration metrics

Table III: Rare attack performance

Table IV: Prior shift reliability

Table V: Platt scaling

---

# 11. Tasks for C5

[ ] Add Brier Score

[ ] Cohen's d for ECE

[ ] Cohen's d for Brier

[ ] Cohen's d for AUC-PR

[ ] Add Platt Scaling

[ ] Add Random Forest baseline

[ ] Add XGBoost baseline

[ ] Reduce role of margin analysis

---

# 12. Tasks for C4

Giữ:

* Balanced
* Attack-heavy
* DoS-only

Không dùng:

* Gaussian perturbation

Tasks:

[ ] Replace F1 with ECE

[ ] Add Brier Score

[ ] Add AUC-PR

[ ] Calibration degradation curve

[ ] Cohen's d for ECE

[ ] Add Random Forest baseline

[ ] Add XGBoost baseline

---

# 13. Tasks for C6

Không dùng learning curve F1.

Tasks:

[ ] Compute ECE(N)

[ ] Compute Brier(N)

[ ] Compute AUC-PR(N)

---

# 14. General Tasks

[ ] Same seeds as Paper 1

[ ] mean ± std

[ ] Same figure style

[ ] Same table style

---

# 15. Limitations

* Rare attack classes contain few samples.
* Single dataset (NSL-KDD).
* Simulation-based QSVM.
* Platt scaling limitations.

---

# 16. Draft Paper Structure

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
