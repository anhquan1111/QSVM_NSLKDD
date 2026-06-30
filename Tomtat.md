# TÓM TẮT PAPER 2 (cho bạn đọc nhanh)

> Paper 2 = paper **dự phòng** cho Paper 1. Trục: **độ tin cậy / calibration** của QSVM,
> so với **Deep Learning + Machine Learning** (không đấu accuracy vì QSVM thua mảng đó).
> File LaTeX hoàn chỉnh: `paper2/main.tex` (+ `paper2/figs/`). Zip sẵn: `paper2.zip`.

---

## 1. Đã làm đúng theo plan `paper2.md` chưa? → ~90%, có 1 điều chỉnh quan trọng

| Mục trong `paper2.md` | Tình trạng |
|---|---|
| C1 — Calibration (ECE, Brier, Reliability Diagram) | ✅ Xong |
| C2 — Rare-attack reliability (AUC-PR, PR) | ✅ Xong |
| C3 — Reliability under prior shift (Balanced/Attack-heavy/DoS) | ✅ Xong |
| C4 — Platt before/after | ✅ Xong |
| A1 — Low-data reliability (ECE/Brier/AUC-PR theo N) | ✅ Xong |
| **A2 — Temporal reliability** | ✅ **Đã làm** — ECE/Brier trên KDDTest-21 (5 model, 5 run); kết quả: mọi model degrade, QSVM cạnh tranh không dẫn đầu (đúng kỳ vọng) |
| Baselines: QSVM-ZZ, SVM-RBF, RandomForest, XGBoost, **MLP** | ✅ Đủ (MLP plan ghi "optional" — bọn mình đưa vào luôn) |
| "Reduce role of margin analysis" | ✅ **Bỏ hẳn** margin (vì kiểm chứng cho thấy claim margin cũ bị SAI/đảo dấu) |
| Tasks C5/C4/C6 (Brier, Cohen's d, Platt, RF/XGB, đổi F1→ECE) | ✅ Làm hết |

### ⚠️ Điều chỉnh quan trọng nhất so với kỳ vọng của plan
Plan ngầm giả định "QSVM đáng tin hơn DL/ML nói chung". **Số liệu thật (đã verify) KHÁC:**
QSVM chỉ **thắng calibration TRÊN TẤN CÔNG HIẾM (U2R/R2L)**; trên **toàn tập** (prior-shift,
low-data, temporal) nó chỉ **cạnh tranh**, và **MLP thường calibrate tốt hơn**. Vì vậy narrative
đã được chốt là **"regime-specific reliability"** (đáng tin nhất ở đúng nhóm hiếm/nguy hiểm),
**không over-claim**. Đây là điểm phải nói rõ với reviewer — và may là đã phát hiện TRƯỚC khi viết.

---

## 2. Chuẩn định dạng IEEE chưa? → RỒI

- Dùng `\documentclass[journal]{IEEEtran}` — **đúng template Paper 1** của thầy (cùng class, cùng macro, cùng kiểu bảng `booktabs`, cùng kiểu bibliography).
- **8 section, phản chiếu đúng bộ khung Paper 1:** Introduction → Background & Related Work → Reliability Framework → Experimental Setup → Results → **Regime Map** → **Limitations** → Conclusion.
- Có đủ thành phần học thuật như Paper 1: **2 Definition, 1 Proposition (Platt giữ ranking), 1 Assumption (NISQ 4-qubit), 1 Problem, 1 Algorithm**, bibliography 15 reference.
- Đã kiểm tra tự động: mọi môi trường cân bằng, mọi `\ref`/`\cite`/`\label` khớp, không thiếu hình.

## 3. Hình & bảng? → 9 hình + 8 bảng (tương đương Paper 1: 10 hình + 7 bảng)

**9 hình:** (1) sơ đồ pipeline, (2) ECE/Brier rare, (3) reliability diagram, (4) forest plot Cohen's d,
(5) AUC-PR vs Brier, (6) prior-shift, (7) low-data curves, (8) Platt before/after, (9) temporal (KDDTest-21).
**8 bảng:** coverage công trình trước, notation, rare-attack reliability, Cohen's d, prior-shift, low-data, temporal, Platt.

**Để ra PDF:** máy không có LaTeX nên phải build trên **Overleaf** (upload `paper2.zip` → Recompile).
Hướng dẫn từng bước: `docs/HUONG_DAN_OVERLEAF.md`.

---

## 4. Nội dung chính + khác gì Paper 1?

| | **Paper 1** (manuscript.pdf — của thầy) | **Paper 2** (mới) |
|---|---|---|
| Câu hỏi | *Khi nào QSVM thắng HIỆU NĂNG?* | *Dự đoán QSVM có ĐÁNG TIN để triển khai?* |
| Metric | F1-macro, KTA, accuracy | **ECE, Brier, AUC-PR (calibration)** |
| Đối thủ | Chỉ SVM cổ điển (RBF/Poly/Linear) | **+ MLP (deep), RandomForest, XGBoost** |
| Phạm vi | Cả framework C1–C4 (giảm chiều, ablation, robustness, sample complexity) | **Chỉ trục reliability** (khôi phục C5 calibration đã bị cắt khỏi Paper 1) |
| Kết luận | Lợi thế hiệu năng theo regime | Lợi thế độ tin cậy theo regime |

**Kết quả chính (số thật, 5 run NSL-KDD):**
1. **Rare attacks:** QSVM đáng tin NHẤT — ECE_rare = **0.4503**, Brier_rare = **0.3288** (thấp nhất),
   đánh bại cả DL lẫn tree. So với XGBoost/RF: effect cực lớn (Cohen's d = **1.9–3.6**). So với MLP:
   thắng cả calibration lẫn ranking.
2. **Toàn tập (prior-shift, low-data, temporal):** QSVM chỉ **cạnh tranh**, MLP thường tốt hơn → báo cáo trung thực. Riêng **temporal (KDDTest-21): mọi model degrade mạnh** (ECE vọt ~3×), QSVM hạng 2 sau MLP → đúng chỗ Paper 1 nói QSVM yếu.
3. **Platt scaling** giúp QSVM/SVM nhưng làm hại tree/MLP → đóng góp phương pháp.
4. **Điểm tinh tế:** RF/XGBoost rank tốt hơn (AUC-PR cao) nhưng **overconfident** (Brier gấp đôi QSVM)
   → "rank giỏi ≠ đáng tin". Đây là thông điệp bán hàng của paper.

**Liên hệ 2 paper:** khác trục rõ ràng (performance vs reliability) nên **an toàn**, không bị coi là
trùng lặp/salami khi nộp IEEE. Paper 2 có thể: (a) nộp riêng như companion, hoặc (b) dùng kết quả
DL/ML này để cứu Paper 1 nếu reviewer chê "thiếu so deep learning".

---

## 5. Việc còn lại
- [ ] Upload `paper2.zip` lên Overleaf → ra PDF (xem `docs/HUONG_DAN_OVERLEAF.md`).
- [ ] Điền tên tác giả/affiliation/email thật (đang để theo nhóm Paper 1).
- [ ] (Tùy chọn) Rà câu chữ abstract cho khớp văn phong manuscript.

> ✅ A2 (temporal) đã hoàn tất → paper giờ đủ cả 4 contribution chính (C1–C4) + 2 additional (A1, A2) đúng như plan `paper2.md`.
