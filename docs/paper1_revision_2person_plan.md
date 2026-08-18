# Paper 1 Revision — Kế hoạch 2 người (độc lập tối đa)

> Chia việc để 2 người làm song song, ít phụ thuộc nhau. Đầu ra mỗi người = **cập nhật
> file MD báo cáo** (`docs/paper1_revision_report.md`) — thầy dựa vào đó sửa .tex.
> Ràng buộc chung: **giữ ≤12 trang** (né MOPC), refs **≤45**, không đổi tác giả/self-cite.

## Chú thích mức độ
🔴 nặng/bắt buộc · 🟡 định vị/viết lại · 🟢 nhẹ/nhanh

---

## 👤 NGƯỜI 1 — Lý thuyết, C1–C3, References, Novelty
*(mạch: nền toán + đóng góp lõi + định vị)*

### A. C1 — REBUILD (nặng nhất của người 1) 🔴
- **Vấn đề:** V(n)↑, Q(n)↑, F̃(n)↓ đơn điệu ⇒ "Pareto đa mục tiêu" vô nghĩa; n=4 thực chất do ngưỡng V≥0.80. Theorem 1 viết sai chiều (F̃(4)>F̃(3) ngược Bảng III).
- **Làm:**
  1. Bỏ khung "Pareto-optimal"; đổi thành **quy tắc chọn có ràng buộc phần cứng** (variance floor + qubit-cost penalty).
  2. Biện minh n=4 bằng **downstream thật**: chạy **F1 & KTA theo n∈{2..8}** → chứng minh n=4 là **elbow** (bão hòa hiệu năng) trong khi Q(n) vẫn tăng. Đây mới là đánh đổi thật.
  3. **Bỏ/viết lại Theorem 1** thành *quan sát thực nghiệm* với số ĐÚNG.
  4. Kiểm lại ablation K=20 (số cũ ghi K=25 ở doc — verify K thật).
- **Notebook:** `notebooks/nslkdd/pca.ipynb`, `selectkbest_nslkdd.ipynb`.

### B. Theory section — restructure 🔴
- Propositions là **fact đã biết** → đổi thành "Background/Observation", **không** đóng khung "Proposition + proof".
- **Proposition 3:** hiện chỉ cite → hoặc dẫn ngắn, hoặc hạ thành nhận xét có cite.

### C. References audit ≤45 🔴
- Bỏ **[26] (bịa)**; sửa **[15]** 116990F→116990B.
- Thêm: QMI-2026 "Benchmarking QML for IDS on noisy quantum computers", Carducci ICAD-2026, arXiv:2403.07059, arXiv:2409.04406, + ref bối cảnh F1 NSL-KDD.
- Cắt ref non-self yếu để giữ ≤45 (KHÔNG đụng self-cite). **Highlight vàng + giải trình** mọi thay đổi.

### D. Novelty positioning 🟡 (vô hiệu phiếu reject Rev3)
- Viết đoạn định vị: đóng góp KHÔNG phải kernel mới, mà là (a) regime-specific, (b) Pareto/elbow có chi phí qubit, (c) bộ ablation+calibration+stress-test.
- **Phân biệt sắc** với arXiv:2403.07059 & 2409.04406 & QMI-2026 (2–3 câu mỗi bài).

### E. Nhỏ 🟢
- Thêm câu "exponential concentration of kernel matrix" cạnh barren-plateau (C2/C3).

---

## 👤 NGƯỜI 2 — Thí nghiệm mới, C4–C6, Claims, Reproducibility
*(mạch: bằng chứng mới + số liệu + hạ giọng)*

### F. Baseline non-SVM 🔴 (điều kiện tiên quyết theo reviewer)
- Thêm **RandomForest + XGBoost** (tái dùng `src/reliability.py`) vào so sánh **accuracy/F1 theo regime** (KHÔNG lấn calibration của Paper 2). Cân nhắc TabNet/FT-Transformer nếu kịp trang.
- Chỉ báo cáo gọn (bảng) để không vượt 12 trang.

### G. NISQ noise 🔴 (cứu tiền đề tiêu đề)
- Chạy **Aer noise model / IBM FakeBackend** (gate/readout/decoherence) — MIỄN PHÍ, local.
- Nếu kết quả không đủ mạnh → **hạ tiêu đề/claim** "NISQ-aware".
- **Notebook:** mở rộng `c2_5_fidelity_vs_statevector_kernel_fixed.ipynb` (đang chỉ shot-noise).

### H. UNSW supplementary 🔴 (lần này PHẢI nộp kèm)
- Đóng gói kết quả `notebooks/unsw/` thành supplementary. Verdict: QSVM **competitive, không dominant** → dùng cho luận điểm regime-dependent, không thổi phồng.

### I. C-sensitivity / quantum tuning 🔴
- Chạy QSVM với **nhiều C** (`c3_c_tuning_statevector.ipynb`) → chứng minh kết luận **robust theo C** (giải quyết bất đối xứng "QSVM C=1.0 vs SVM tuned").
- Engage 1–2 ref về quantum kernel tuning; nêu rõ là **design choice**.

### J. Thống kê & số liệu 🔴
- Tăng **seed 5→10** (hoặc bootstrap CI) cho claim effect-size.
- **Regime âm** (temporal, perturbation): thêm effect-size/CI **tương xứng** regime dương (chống cherry-pick).
- **⚠️ Verify Cohen's d rare N=500**: bài ghi +0.68, nội bộ cũ 0.4043 → chạy lại `c6_learning_curve` / `run_reliability_*`, chốt số ĐÚNG, thêm **bảng số rare-attack** (Rev4 đòi).
- Giải thích **Bảng VI (N=1000) vs Bảng IV**; nêu **crossover** low-data (hoặc vì sao không có).

### K. Claims 🔴 + Reproducibility 🟢
- **Hạ giọng:** "quantum advantage is real" → "giới hạn trong baseline & setup đã thử"; nhấn *regime-specific* thay vì trung bình.
- Thêm **link GitHub** (repo public) vào paper.

---

## Phối hợp giữa 2 người (điểm chạm tối thiểu)
- **Refs (C):** người 2 báo người 1 các ref mới cần thêm (từ noise/tuning) để gộp vào audit ≤45.
- **Claims cuối (D, K):** thống nhất câu định vị novelty + mức "hạ giọng" trước khi chốt.
- **Độ dài:** cả 2 canh tổng ≤12 trang — đẩy chi tiết phụ ra supplementary.

## Thứ tự ưu tiên (cả nhóm)
1. 🔴 Liêm chính: C (refs) + A (Theorem 1) — làm NGAY.
2. 🔴 Bằng chứng: F (baseline) + G (noise) + H (UNSW) + A (rebuild C1 downstream).
3. 🔴 Số liệu: J (verify/stats) + I (C-sensitivity).
4. 🟡 Viết lại: B (theory) + D (novelty) + K (claims).
5. Đóng gói: rebuttal point-by-point + bản highlight vàng + cover letter (MOPC nếu cần).
