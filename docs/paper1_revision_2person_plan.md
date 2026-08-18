# Paper 1 Revision — Kế hoạch 2 người (theo C1–C6, tập trung CODE)

> **Mục tiêu:** đưa bài đạt chuẩn nhận ở TETC (Q1/Q2). Chiến lược cốt lõi: **bỏ mọi phóng đại,
> làm chắc từng đóng góp bằng bằng chứng thực nghiệm rigorous kiểu 2026, định vị lại là
> "phương pháp regime-specific" chứ không phải "quantum advantage".**
>
> - **Người 1 = C1, C2, C3** (nền toán + kernel).
> - **Người 2 = C4, C5, C6** (robustness + calibration + sample-complexity) + thí nghiệm mới cross-cutting.
> - **Việc viết .tex → THẦY** (gom ở cuối). Ở đây chỉ ghi **CODE/thí nghiệm cần làm + output**.
> - Ràng buộc: **≤12 trang** (đẩy chi tiết ra **supplementary**), refs **≤45**, KHÔNG đổi tác giả/self-cite, dùng `uv run`.

**Mức độ:** 🔴 nặng/bắt buộc · 🟡 vừa · 🟢 nhẹ. **Trạng thái:** ☐ chưa · ☑ xong.

---

# 👤 NGƯỜI 1 — C1, C2, C3

## C1 — REBUILD phần chọn số chiều 🔴 (nặng nhất cả bài)
**Vấn đề (Rev4 đúng):** V(n)↑, Q(n)↑, F̃(n)↓ đều đơn điệu ⇒ "Pareto đa mục tiêu" **không lọc gì**; n=4 thực chất do ngưỡng V≥0.80. Theorem 1 viết **sai chiều** (F̃(4)>F̃(3) ngược Bảng III 0.471<0.628).
**Notebook:** `notebooks/nslkdd/pca.ipynb`, `selectkbest_nslkdd.ipynb`.
**CODE cần làm:**
1. ☐ **Bỏ hàm tổ hợp F(n) + Pareto giả + Theorem 1.**
2. ☐ Thay bằng **đường cong chọn n thực nghiệm**: chạy pipeline đầy đủ với **n ∈ {2,3,4,5,6,8}**, đo **F1_macro, KTA, #SV** trên test (multi-seed, có CI). Vẽ overlay với **chi phí 2-qubit gate Q(n)** của ZZ.
   → Chứng minh **n=4 là "elbow"**: F1/KTA **bão hòa** sau n=4 trong khi Q(n) tăng tuyến tính ⇒ đánh đổi THẬT, biện minh được.
3. ☐ **Verify K**: doc cũ ghi K=25 nhưng config `K_FINAL=20` → chạy lại ablation, chốt K đúng + số F1 ablation thật.
4. ☐ (nếu kịp, để supplementary) ablation **PCA vs KernelPCA vs no-reduction** ở 4D → cho thấy PCA tuyến tính **đủ tốt ở low-data** (phản biện "PCA cũ", đồng thời bảo vệ tại sao KHÔNG dùng NN-reducer: NN overfit ở N nhỏ + làm mờ quantum advantage).
**Output:** 1 hình "F1/KTA/Q vs n" + bảng số n-sweep → thay Bảng III cũ. Ghi vào `paper1_revision_report.md`.

## C2 — Expressibility + Kernel Concentration + NISQ NOISE 🔴
**Vì sao:** Rev3 chê novelty (ZZ chuẩn) → C2 là chỗ **giải thích vì sao ZZ hợp IDS**, phải làm chắc. Rev2 đòi nhắc **"exponential concentration"**. Rev1/Rev3 đòi **noise thật** (bài toàn sim lý tưởng).
**Notebook:** `c2_quantum_kernel_expressibility.ipynb`, `c2_5_fidelity_vs_statevector_kernel_fixed.ipynb`.
**CODE cần làm:**
1. ☐ **Kernel concentration analysis (điểm 2026 quan trọng):** đo **phương sai các phần tử off-diagonal của Gram matrix** theo n và theo N. Chứng minh ở **4 qubit ZZ KHÔNG bị concentration nặng** (kernel còn phân biệt được) → vừa đáp Rev2, vừa **biến điểm yếu "ít qubit" thành điểm mạnh** (ít qubit = tránh exponential concentration). *(Tham chiếu: Thanasilp et al. 2024, concentration in quantum kernels.)*
2. ☐ **NISQ noise thật:** chạy kernel qua **Aer noise model / IBM FakeBackend** (depolarizing + readout + thermal relaxation) — MIỄN PHÍ, local. So **KTA/F1 ideal vs noisy** (vài mức noise). → làm "NISQ-aware" **có bằng chứng**.
   - Nếu noise phá quá nặng → **hạ tiêu đề** thành "statevector benchmark" + thảo luận noise ở mức limitation. Trung thực > phóng đại.
3. ☐ Giữ expressibility (KL/entanglement entropy) nhưng **nối logic** vào concentration ở trên.
**Output:** hình concentration-vs-n + bảng ideal-vs-noisy (KTA, F1). Chi tiết noise → supplementary.

## C3 — Geometry + QSVM C-SENSITIVITY (fix bất đối xứng) 🔴
**Vấn đề (Rev1/Rev4):** SVM được tune C, **QSVM để C=1.0 cố định** → không công bằng, và có thể là lý do QSVM "degrade dưới σ=0.20".
**Notebook:** `c3_c_tuning_statevector.ipynb`, `c3_kernel_geometry_statevector_multirun.ipynb`.
**CODE cần làm:**
1. ☐ **Tune QSVM C trên CÙNG grid với SVM** (C∈{0.1,0.3,0.5,1,3,5,10}) → báo cáo kết quả **best-C cho cả hai**, hoặc chứng minh **kết luận robust theo C** (QSVM thắng ở nhiều C, không chỉ C=1.0). → xóa bất đối xứng.
2. ☐ Giữ **KTA, ablation ZZ vs Z, geometry**; đảm bảo số **khớp** với bảng chính (chống mâu thuẫn Bảng III/IV).
3. ☐ Rà lại **headline number** (F1 0.854 vs 0.838): xác nhận đúng, và **báo cáo kèm CI + với best-C** để không bị nói "marginal do chọn C".
**Output:** bảng QSVM/SVM theo C + khẳng định robust. Grid chi tiết → supplementary.

---

# 👤 NGƯỜI 2 — C4, C5, C6 (+ thí nghiệm mới cross-cutting)

## C4 — Robustness: STATS cho MỌI regime 🔴 (chống cherry-pick)
**Vấn đề (Rev2 rất tinh):** 3 regime QSVM thắng có full stats; 2 regime thua (temporal, perturbation) **chỉ định tính** ("wrapped phase") → mất cân bằng.
**Notebook:** `c4_robustness_distribution_shift_multirun_fixed.ipynb`.
**CODE cần làm:**
1. ☐ Tính **Cohen's d + bootstrap CI + McNemar** cho **CẢ regime thua** (temporal, perturbation) y như regime thắng. Báo cáo đối xứng.
2. ☐ Tăng **seed 5→10+** (hoặc bootstrap) cho mọi regime → nền thống kê dày hơn (đáp Rev2).
3. ☐ Trình bày thành **1 "regime map" trung thực**: nói rõ đâu thắng / hòa / thua, có số cho mọi ô.
**Output:** bảng regime đầy đủ (d, CI, p) cho 5 regime. Ghi report.

## C5 — Calibration + số RARE-ATTACK 🔴
**Vấn đề (Rev4):** claim rare-attack N=500 "+6.7 điểm, d=+0.68" **không có bảng số** để kiểm.
**Notebook:** `c5_confidence_calibration_multirun.ipynb`.
**CODE cần làm:**
1. ☐ Xuất **bảng số rare-attack (U2R∪R2L)** rõ ràng: F1/ECE/margin cho QSVM vs baseline, kèm d + CI. → để Rev4 kiểm chứng được.
2. ☐ Đảm bảo **định nghĩa/giá trị nhất quán** với C6 và bảng chính (tránh vênh số).
3. ☐ (ranh giới) calibration sâu (ECE/Brier vs RF/XGBoost) **để cho Paper 2**, ở Paper 1 chỉ nêu vừa đủ + cite Paper 2.
**Output:** bảng rare-attack chuẩn.

## C6 — Learning curve: VERIFY số + CROSSOVER 🔴
**Vấn đề (Rev1/Rev4):** (a) Bảng VI (N=1000) ≠ Bảng IV; (b) QSVM thắng **mọi** N → hỏi có crossover không; (c) **Cohen's d N=500 vênh** (bài +0.68 vs nội bộ 0.4043).
**Notebook:** `c6_learning_curve_sample_complexity.ipynb`.
**CODE cần làm:**
1. ☐ **CHỐT lại Cohen's d N=500 thật** (chạy lại, so 0.68 vs 0.4043) → sửa số đúng vào bài + report.
2. ☐ **Đối chiếu Bảng VI vs IV** cùng N=1000 → giải thích/đồng bộ (khác setup? khác seed?).
3. ☐ **Mở rộng N** (thêm 2000, 5000 nếu kernel kịp) → tìm **crossover** hoặc lập luận rõ vì sao QSVM vẫn dẫn (low-data advantage bão hòa ở đâu). Chi tiết → supplementary.
4. ☐ Tăng seed cho các mốc N.
**Output:** learning curve mở rộng + bảng số nhất quán.

## ⚡ CROSS-CUTTING (Người 2 chủ trì) 🔴
**X1. Baseline non-SVM (điều kiện tiên quyết theo 3 reviewer):**
- ☐ Thêm **RandomForest + XGBoost** (tái dùng `src/reliability.py`) vào **so sánh accuracy/F1 theo regime + learning curve**. Cân nhắc **TabNet/FT-Transformer/CatBoost** (1 cái là đủ) nếu kịp.
- Chỉ đưa **số tổng hợp** vào bài (bảng gọn); chi tiết → supplementary. → chống >12 trang.
- ⚠️ **Ranh giới Paper 2:** dùng non-SVM cho **accuracy/regime**, KHÔNG bê calibration.
**X2. UNSW supplementary (lần này PHẢI nộp):**
- ☐ Đóng gói `notebooks/unsw/` thành supplementary. Verdict: QSVM **competitive, không dominant** → củng cố "regime/dataset-dependent", không thổi phồng.
**X3. Reproducibility:**
- ☐ Đảm bảo repo chạy được bằng `uv sync` + README; báo thầy thêm **link GitHub** vào bài.

---

# 🔗 Phối hợp (điểm chạm tối thiểu)
- **Số headline & regime map:** Người 1 (C3 best-C) ↔ Người 2 (C4/C6) chốt **cùng một bộ số** để không mâu thuẫn bảng.
- **Refs mới:** Người 2 (noise/tuning/baseline) báo Người 1 ref cần thêm → gộp audit ≤45.
- **Độ dài:** cả hai canh tổng ≤12 trang; mọi grid/sweep/UNSW/noise chi tiết → **supplementary**.

# 🥇 Chiến lược đạt Q1 (nguyên tắc xuyên suốt 2026)
1. **Trung thực > phóng đại:** bỏ "quantum advantage is real"; khung lại là **"khi nào quantum có lợi"** (đúng hướng 2026, Rev4 khen).
2. **Rigor thống kê:** CI/bootstrap, nhiều seed, số cho MỌI regime (thắng lẫn thua).
3. **Bằng chứng đúng chỗ reviewer đòi:** non-SVM baseline + noise thật + dataset 2 + C-sensitivity.
4. **Biến điểm yếu thành điểm mạnh:** ít qubit ⇒ **tránh kernel concentration** (C2); low-data ⇒ **PCA hợp hơn NN**; regime thua ⇒ báo cáo trung thực = uy tín.
5. **Định vị novelty = phương pháp**, không phải kernel mới.

# 📋 Thứ tự ưu tiên (cả nhóm)
1. 🔴 **Liêm chính + số:** C1 (bỏ Theorem/Pareto) · C6 (verify Cohen's d) · rà refs bịa.
2. 🔴 **Bằng chứng mới:** X1 baseline · C2 noise · X2 UNSW.
3. 🔴 **Fix phương pháp:** C3 QSVM C-sensitivity · C4 stats mọi regime · C2 concentration.
4. 🟡 **Số & làm rõ:** C6 crossover/Bảng VI-IV · C5 bảng rare-attack.
5. Gom `docs/paper1_revision_report.md` → chuyển thầy.

---

# ✍️ PHẦN CHO THẦY (viết .tex — KHÔNG phải việc code)
> Nhóm cung cấp số/hình qua `docs/paper1_revision_report.md`; thầy chèn & sửa văn bản.
- **Theory section:** Propositions là fact đã biết → đổi thành "Background/Observation", bỏ khung "Proposition+proof". **Proposition 3** chỉ cite → dẫn ngắn hoặc hạ thành nhận xét.
- **References ≤45:** bỏ **[26] (bịa)**, sửa **[15]** 116990F→116990B, thêm QMI-2026 + Carducci ICAD-2026 + arXiv:2403.07059 + 2409.04406 + ref bối cảnh F1 NSL-KDD; cắt ref non-self yếu; **highlight vàng + giải trình** mọi thay đổi (KHÔNG đụng self-cite).
- **Novelty positioning:** đoạn định vị đóng góp = phương pháp regime-specific + n-selection có chi phí qubit + bộ ablation/calibration/stress-test; **phân biệt sắc** với 2 arXiv + QMI-2026.
- **Hạ giọng claim:** "quantum advantage is real" → "giới hạn trong baseline & setup đã thử"; nhấn regime-specific.
- **Nhỏ:** thêm câu "exponential concentration of kernel matrix" (nối với kết quả C2 của nhóm).
- **Đóng gói nộp:** bản sạch + bản highlight vàng + rebuttal **point-by-point** + cover letter. Giữ **≤12 trang** (né MOPC); nếu buộc vượt → khai MOPC.
- **Đổi affiliation (nếu có)** khai ở rebuttal + cover letter.
