# Paper 1 — Tổng quan (Hiệu năng / Regime-Specific Benchmark)

> Tài liệu giúp hiểu nhanh Paper 1 làm gì, kết quả, và **hiện đang cần cải thiện gì**.
> Kế hoạch sửa chi tiết: [paper1_revision_plan.md](paper1_revision_plan.md).

## 1. Paper 1 là gì
- **Tựa:** *NISQ-Aware Quantum Kernel SVM for Network Intrusion Detection: A Regime-Specific Benchmark on NSL-KDD*
- **Nơi nộp:** IEEE **TETC** (Transactions on Emerging Topics in Computing), mã `TETC-2026-05-0252`.
- **Câu hỏi:** *Khi nào* và *vì sao* quantum kernel (4-qubit ZZFeatureMap) thắng SVM cổ điển — không chỉ báo cáo accuracy tổng.
- **Tác giả (thứ tự đã nộp, KHÔNG được đổi):** Minh Tuan Pham → Phuc Hao Do → Nguyen Nang Hung Van → Quang Anh Nguyen → **Quan Tran Anh Vo** *(đứng cuối nhưng là **corresponding author**)*.

## 2. Sáu đóng góp (C1–C6)
| | Nội dung | Kết quả chính |
|---|---|---|
| **C1** | Giảm chiều 2 giai đoạn: SelectKBest + PCA tối ưu Pareto có tính chi phí qubit `Q(n)` | **K=20 + PCA 4D → F1=0.8989** (vs PCA 4D trực tiếp 0.8577). Chọn n=4 qubit trên Pareto front |
| **C2** | Khả năng biểu diễn ZZFeatureMap (vì sao thắng trên IDS) | Kernel LT ≈ polynomial bậc-2 nhưng ánh xạ Hilbert mũ; IDS có tương quan cặp đặc trưng cao |
| **C3** | Kernel geometry + decision boundary + ablation ZZ vs Z | KTA nâng từ 0.070 (no entanglement); heatmap block structure |
| **C4** | Robustness dưới distribution shift | Temporal (KDDTest-21), feature perturbation (σ), class-prior shift |
| **C5** | Confidence calibration + tấn công hiếm (U2R/R2L) | Reliability diagram, ECE, Platt scaling |
| **C6** | Learning curve / sample complexity | QSVM thắng mọi mốc N; rõ nhất N=500 (F1 0.8311 vs RBF 0.7310); Cohen's d=0.4043 (rare, N=500) |

- **Kết quả tổng (Pareto pipeline):** `F1_macro = 0.854 ± 0.016` (5 multi-run).
- **Khung thống kê:** 5-fold CV, mean ± std, McNemar, Cohen's d.

## 3. HIỆN TẠI — Major Revision (hạn 13-Oct-2026)
Reviewer khen timely, well-organized; nhưng **Major Revision** (không có vòng 2). Các điểm phải sửa:

**🚨 Liêm chính (làm trước):**
- Reference **bịa/sai** ([26] Rahman nghi bịa; [15] sai số bài 116990F→116990B; AE nói còn refs không tồn tại) → audit toàn bộ ≤45 refs.
- **Theorem 1 sai** (F̃(4)>F̃(3) ngược Bảng III 0.471<0.628); nghi Pareto (C1) không thực sự lọc.

**Nội dung:**
- Thêm baseline **non-SVM** (RF/XGBoost — tái dùng từ Paper 2, CHỈ cho accuracy/regime để tránh trùng Paper 2).
- Bổ sung **UNSW-NB15** làm dataset thứ 2 + supplementary (đã port sẵn).
- **Nhiễu NISQ thật** (Aer/FakeBackend — MIỄN PHÍ, chạy local) hoặc bỏ chữ "NISQ-aware".
- **Giảm overclaim** ("quantum advantage is real" → giới hạn trong baseline/setup; F1 0.854 vs 0.838 là biên).
- Sửa Theory (Propositions là fact đã biết, đừng đóng khung định lý).
- **C-sensitivity** QSVM (giải trình C=1.0 cố định vs SVM được tune).
- **Link code** (GitHub public — reproducibility).

**Ràng buộc:** không đổi tác giả/self-citation; highlight vàng thay đổi; >12 trang → phí MOPC; cần bio tác giả (<150 từ).

## 4. Quan hệ với Paper 2
Companion. Paper 1 = **hiệu năng/regime**, Paper 2 = **calibration/độ tin cậy**. Khi thêm RF/XGBoost vào Paper 1 (do reviewer đòi), **giữ ranh giới**: Paper 1 dùng cho accuracy, phần calibration để cho Paper 2 và **cite chéo + khai với EiC**. Xem [PAPER2_overview.md](PAPER2_overview.md).

## 5. Tài liệu liên quan trong `docs/`
- `paper1_revision_plan.md` — checklist sửa từng comment reviewer.
- `PAPER1_final_report.docx` — báo cáo gốc thầy dựa vào để viết Paper 1.
- `ARCHIVE_initial_plan_v4.docx` — kế hoạch nghiên cứu ban đầu (rất cũ, lưu trữ).
