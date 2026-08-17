# Paper 2 — Tổng quan (Độ tin cậy / Reliability & Calibration)

> Companion paper đi cùng Paper 1. **Đã nộp** lên IJNM (International Journal of Network
> Management, Wiley Q2) — Submission ID `e3282690-e2a0-4bb5-891f-df0cee201a41`,
> corresponding + submitting author = **Quan Tran Anh Vo**.

## 1. Paper 2 là gì
Cùng dataset **NSL-KDD** và mô hình **QSVM 4-qubit ZZFeatureMap** như Paper 1, nhưng khác trục:
- **Paper 1:** QSVM **đoán đúng** đến đâu (F1, accuracy)?
- **Paper 2:** khi QSVM báo "tấn công 90%" thì **con số 90% có đáng tin không** (calibration)?

Hai trục độc lập → hai bài bổ trợ, không trùng lặp.

## 2. Vì sao chọn hướng calibration
Trên dữ liệu bảng, XGBoost/RF thường **chính xác hơn** QSVM 4 chiều → khó thắng về accuracy.
Nhưng **calibration** là điểm QSVM có lợi thế và là **khoảng trống nghiên cứu** (gần như chưa
ai đánh giá calibration của quantum kernel cho IDS, cũng chưa ai so QSVM với mô hình cây).

## 3. Phương pháp
- Pipeline chung không rò rỉ (SelectKBest 20 → PCA 4D → MinMax `[0,π]`) → khác biệt chỉ do classifier.
- **4 mô hình:** QSVM-ZZ, SVM-RBF, Random Forest, XGBoost.
- Mọi model đều **Platt scaling** (fit train, áp test) trước khi đo.
- **5 lần chạy** độc lập (mean ± std) + **Cohen's d**.

## 4. Kết quả chính
**Nơi QSVM thắng rõ nhất — tấn công hiếm (U2R, R2L, <1%):**
| Mô hình | ECE↓ | Brier↓ | AUC-PR | F1 |
|---|---|---|---|---|
| **QSVM-ZZ** | **0.450** | **0.329** | 0.931 | 0.776 |
| SVM-RBF | 0.539 | 0.367 | 0.913 | 0.782 |
| Random Forest | 0.647 | 0.629 | 0.947 | 0.785 |
| XGBoost | 0.672 | 0.656 | 0.944 | 0.796 |

Cohen's d vs mô hình cây = **1.9–3.6** (hiệu ứng lớn). QSVM cũng đáng tin nhất ở **điểm cân bằng**
(ECE 0.099) và **low-data** (N≥200).

**Nơi QSVM KHÔNG dẫn đầu (báo cáo trung thực):** prior-shift mạnh (attack-heavy, DoS-only) và
temporal drift (KDDTest-21) → chỉ **cạnh tranh**; RF hiệu chỉnh tốt hơn.

**Hai phát hiện:** (1) xếp hạng tốt (AUC-PR) ≠ đáng tin — cây "quá tự tin", Brier gấp đôi QSVM;
(2) Platt scaling hợp mô hình margin (QSVM/SVM), làm xấu mô hình cây.

## 5. Kết luận
**"Regime-specific reliability":** QSVM không chính xác nhất, nhưng **đáng tin nhất ở đúng nơi
khó & nguy hiểm nhất** (tấn công hiếm, low-data). Song song với Paper 1 → hai bài củng cố nhau.

## 6. Quan hệ Paper 1 & liêm chính
Vì khác trục rõ ràng (hiệu năng vs độ tin cậy), tồn tại song song là **an toàn về liêm chính**,
không bị xem là nộp trùng — miễn **cite chéo + khai companion với editor**, và **không tái dùng
nguyên văn/hình** giữa 2 bài. Nếu Paper 1 (đang major revision) thêm RF/XGBoost thì chỉ dùng cho
accuracy, để calibration cho Paper 2.

## 7. Ghi chú phối hợp
Phần robustness (prior-shift + temporal) dùng kết quả của thành viên phụ trách contribution 4;
các phần còn lại (calibration, rare-attack, low-data, Platt) do nhóm thực hiện trên cùng khung.

*Code: `src/reliability.py` + `runners/run_reliability_*.py`; kết quả `results/nslkdd/p2_*.json`.*
