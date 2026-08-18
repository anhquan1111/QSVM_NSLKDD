# 📄 Paper 1 Revision — Kế hoạch 2 người (theo C1–C6)

> [!abstract] Mục tiêu & chiến lược
> Đưa bài đạt chuẩn nhận ở **TETC (Q1/Q2)**. Cốt lõi: **bỏ mọi phóng đại — làm chắc từng đóng góp bằng bằng chứng rigorous kiểu 2026 — định vị lại là "phương pháp regime-specific", KHÔNG phải "quantum advantage".**
>
> - 👤 **Người 1** → **C1, C2, C3** (nền toán + kernel)
> - 👤 **Người 2** → **C4, C5, C6** + thí nghiệm mới cross-cutting
> - ✍️ Viết `.tex` là việc của **THẦY** (gom ở cuối) — ở đây chỉ ghi **CODE / thí nghiệm cần làm**.

> [!warning] Ràng buộc chung
> - Giữ **≤ 12 trang** → đẩy grid/sweep/noise/UNSW ra **supplementary**.
> - References **≤ 45**; **không** đổi tác giả, **không** đổi self-citation.
> - Chạy bằng `uv run`. Output mỗi bước ghi vào `docs/paper1_revision_report.md`.

**Ký hiệu:** 🔴 nặng/bắt buộc · 🟡 vừa · 🟢 nhẹ

---

# 👤 NGƯỜI 1 — C1 · C2 · C3

## 🔴 C1 — Rebuild phần chọn số chiều
> [!danger] Vấn đề (Reviewer 4 đúng)
> `V(n)↑`, `Q(n)↑`, `F̃(n)↓` **đều đơn điệu** ⇒ "Pareto đa mục tiêu" **không lọc gì** — n=4 thực chất chỉ do ngưỡng `V ≥ 0.80`.
> **Theorem 1 viết sai chiều**: nói `F̃(4) > F̃(3)` nhưng Bảng III cho `0.471 < 0.628`.

📁 `notebooks/nslkdd/pca.ipynb` · `selectkbest_nslkdd.ipynb`

> [!todo] CODE cần làm
> - [ ] **Bỏ** hàm tổ hợp `F(n)` + Pareto giả + **Theorem 1**.
> - [ ] Thay bằng **đường cong chọn n thực nghiệm**: chạy pipeline đầy đủ với `n ∈ {2,3,4,5,6,8}`, đo **F1_macro · KTA · #SV** (multi-seed + CI), overlay **chi phí 2-qubit gate `Q(n)`**.
> - [ ] Chứng minh `n=4` là **elbow**: F1/KTA ==bão hòa== sau n=4 trong khi Q(n) tăng tuyến tính ⇒ đánh đổi **thật**.
> - [ ] **Verify K**: doc cũ ghi K=25 nhưng `config.K_FINAL=20` → chạy lại ablation, chốt số F1 thật.
> - [ ] *(tùy chọn → supplementary)* ablation **PCA vs KernelPCA vs no-reduction** ở 4D → cho thấy PCA đủ tốt ở low-data.

> [!example] Output
> 1 hình *"F1/KTA/Q vs n"* + bảng n-sweep → **thay Bảng III cũ**.

---

## 🔴 C2 — Expressibility + Kernel Concentration + NISQ Noise
> [!danger] Vì sao
> Rev3 chê novelty (ZZ chuẩn) → C2 phải **giải thích chắc vì sao ZZ hợp IDS**.
> Rev2 đòi nhắc **"exponential concentration"**. Rev1/Rev3 đòi **noise thật** (bài đang toàn sim lý tưởng).

📁 `c2_quantum_kernel_expressibility.ipynb` · `c2_5_fidelity_vs_statevector_kernel_fixed.ipynb`

> [!todo] CODE cần làm
> - [ ] **Kernel concentration (điểm 2026 quan trọng):** đo **phương sai phần tử off-diagonal của Gram matrix** theo n và N. Chứng minh 4-qubit ZZ ==KHÔNG bị concentration nặng== → đáp Rev2 **và biến "ít qubit" thành điểm mạnh**. *(ref: Thanasilp et al. 2024.)*
> - [ ] **NISQ noise thật:** chạy kernel qua **Aer noise model / IBM FakeBackend** (depolarizing + readout + thermal relaxation) — miễn phí, local. So **KTA/F1 ideal vs noisy**.
> - [ ] Giữ expressibility (KL / entanglement entropy), **nối logic** vào concentration.

> [!tip] Nếu noise phá quá nặng
> **Hạ tiêu đề** thành *"statevector benchmark"* + đưa noise vào phần limitation. ==Trung thực > phóng đại.==

> [!example] Output
> Hình concentration-vs-n + bảng ideal-vs-noisy (KTA, F1). Chi tiết noise → **supplementary**.

---

## 🔴 C3 — Geometry + QSVM C-Sensitivity (fix bất đối xứng)
> [!danger] Vấn đề (Rev1 / Rev4)
> SVM được tune C, **QSVM để `C=1.0` cố định** → không công bằng; có thể là lý do QSVM "degrade dưới σ=0.20".

📁 `c3_c_tuning_statevector.ipynb` · `c3_kernel_geometry_statevector_multirun.ipynb`

> [!todo] CODE cần làm
> - [ ] **Tune QSVM C trên CÙNG grid với SVM** (`C ∈ {0.1,0.3,0.5,1,3,5,10}`) → báo best-C cho cả hai, HOẶC chứng minh kết luận ==robust theo C== (QSVM thắng ở nhiều C).
> - [ ] Giữ **KTA · ablation ZZ vs Z · geometry**; đảm bảo số **khớp** bảng chính (chống mâu thuẫn Bảng III/IV).
> - [ ] Rà **headline** (F1 0.854 vs 0.838): xác nhận đúng + báo kèm **CI, với best-C** để không bị nói "marginal do chọn C".

> [!example] Output
> Bảng QSVM/SVM theo C + khẳng định robust. Grid chi tiết → **supplementary**.

---

# 👤 NGƯỜI 2 — C4 · C5 · C6 (+ cross-cutting)

## 🔴 C4 — Robustness: stats cho MỌI regime (chống cherry-pick)
> [!danger] Vấn đề (Reviewer 2 rất tinh)
> 3 regime QSVM **thắng** có full stats; 2 regime **thua** (temporal, perturbation) chỉ **định tính** ("wrapped phase") → mất cân bằng, dễ bị coi cherry-pick.

📁 `c4_robustness_distribution_shift_multirun_fixed.ipynb`

> [!todo] CODE cần làm
> - [ ] Tính **Cohen's d + bootstrap CI + McNemar** cho **cả regime thua**, y như regime thắng.
> - [ ] Tăng **seed 5 → 10+** (hoặc bootstrap) cho mọi regime.
> - [ ] Trình bày **"regime map" trung thực**: thắng / hòa / thua đều có số.

> [!example] Output
> Bảng regime đầy đủ (d, CI, p) cho cả 5 regime.

---

## 🔴 C5 — Calibration + số Rare-Attack
> [!danger] Vấn đề (Reviewer 4)
> Claim rare-attack N=500 *"+6.7 điểm, d=+0.68"* nhưng **không có bảng số** để kiểm chứng.

📁 `c5_confidence_calibration_multirun.ipynb`

> [!todo] CODE cần làm
> - [ ] Xuất **bảng số rare-attack (U2R∪R2L)**: F1/ECE/margin cho QSVM vs baseline, kèm **d + CI**.
> - [ ] Đảm bảo định nghĩa/giá trị **nhất quán** với C6 & bảng chính.

> [!warning] Ranh giới Paper 2
> Calibration sâu (ECE/Brier vs RF/XGBoost) ==để cho Paper 2==; Paper 1 chỉ nêu vừa đủ + **cite Paper 2**.

> [!example] Output
> Bảng rare-attack chuẩn (kiểm chứng được).

---

## 🔴 C6 — Learning curve: verify số + crossover
> [!danger] Vấn đề (Rev1 / Rev4)
> - Bảng VI (N=1000) ≠ Bảng IV.
> - QSVM thắng **mọi** N → hỏi có crossover không.
> - ==Cohen's d N=500 vênh==: bài ghi **+0.68** nhưng nội bộ **0.4043**.

📁 `c6_learning_curve_sample_complexity.ipynb`

> [!todo] CODE cần làm
> - [ ] **CHỐT lại Cohen's d N=500 thật** (0.68 vs 0.4043) → sửa số đúng.
> - [ ] **Đối chiếu Bảng VI vs IV** cùng N=1000 → giải thích/đồng bộ.
> - [ ] **Mở rộng N** (2000, 5000 nếu kernel kịp) → tìm crossover hoặc lập luận rõ. Chi tiết → supplementary.
> - [ ] Tăng seed các mốc N.

> [!example] Output
> Learning curve mở rộng + bảng số nhất quán.

---

## ⚡ Cross-cutting (Người 2 chủ trì)
> [!todo] X1 — Baseline non-SVM 🔴 *(điều kiện tiên quyết theo 3 reviewer)*
> - [ ] Thêm **RandomForest + XGBoost** (tái dùng `src/reliability.py`) vào so sánh **accuracy/F1 theo regime + learning curve**. Cân nhắc **TabNet / FT-Transformer / CatBoost** (1 cái đủ) nếu kịp.
> - [ ] Chỉ đưa **số tổng hợp** vào bài; chi tiết → supplementary.
> - ⚠️ Ranh giới: dùng cho **accuracy/regime**, KHÔNG bê calibration của Paper 2.

> [!todo] X2 — UNSW supplementary 🔴 *(lần này PHẢI nộp)*
> - [ ] Đóng gói `notebooks/unsw/` thành supplementary. Verdict: QSVM ==competitive, không dominant== → củng cố "regime/dataset-dependent".

> [!todo] X3 — Reproducibility 🟢
> - [ ] Đảm bảo repo chạy được `uv sync` + README; báo thầy thêm **link GitHub** vào bài.

---

# 🔗 Phối hợp (điểm chạm tối thiểu)
> [!info]
> - **Số headline & regime map:** Người 1 (C3 best-C) ↔ Người 2 (C4/C6) chốt **cùng một bộ số**.
> - **Refs mới:** Người 2 (noise/tuning/baseline) báo Người 1 để gộp audit ≤45.
> - **Độ dài:** cả hai canh ≤12 trang; mọi chi tiết → **supplementary**.

---

# 🥇 5 đòn bẩy đạt Q1 (nguyên tắc 2026)
> [!success]
> 1. **Trung thực > phóng đại:** bỏ "quantum advantage is real" → khung *"khi nào quantum có lợi"* (Rev4 khen).
> 2. **Rigor thống kê:** CI/bootstrap, nhiều seed, số cho MỌI regime.
> 3. **Bằng chứng đúng chỗ reviewer đòi:** non-SVM + noise thật + dataset 2 + C-sensitivity.
> 4. **Biến điểm yếu → điểm mạnh:** ít qubit ⇒ tránh concentration · low-data ⇒ PCA hợp hơn NN · regime thua ⇒ báo cáo trung thực.
> 5. **Novelty = phương pháp**, không phải kernel mới.

---

# 📋 Thứ tự ưu tiên (cả nhóm)
> [!note]
> 1. 🔴 **Liêm chính + số:** C1 (bỏ Theorem/Pareto) · C6 (verify Cohen's d) · rà refs bịa.
> 2. 🔴 **Bằng chứng mới:** X1 baseline · C2 noise · X2 UNSW.
> 3. 🔴 **Fix phương pháp:** C3 QSVM C-sensitivity · C4 stats mọi regime · C2 concentration.
> 4. 🟡 **Số & làm rõ:** C6 crossover / Bảng VI-IV · C5 bảng rare-attack.
> 5. Gom `docs/paper1_revision_report.md` → chuyển thầy.

---

# ✍️ PHẦN CHO THẦY (viết `.tex` — không phải việc code)
> [!quote]- Bấm để mở — nhóm cấp số/hình qua `paper1_revision_report.md`, thầy chèn & sửa văn bản
> - **Theory section:** Propositions là fact đã biết → đổi thành *"Background/Observation"*, bỏ khung "Proposition + proof". **Proposition 3** chỉ cite → dẫn ngắn hoặc hạ thành nhận xét.
> - **References ≤45:** bỏ **[26] (bịa)**, sửa **[15]** `116990F → 116990B`, thêm QMI-2026 + Carducci ICAD-2026 + arXiv:2403.07059 + 2409.04406 + ref bối cảnh F1 NSL-KDD; cắt ref non-self yếu; **highlight vàng + giải trình** mọi thay đổi (KHÔNG đụng self-cite).
> - **Novelty positioning:** đoạn định vị đóng góp = phương pháp regime-specific + n-selection có chi phí qubit + bộ ablation/calibration/stress-test; **phân biệt sắc** với 2 arXiv + QMI-2026.
> - **Hạ giọng claim:** "quantum advantage is real" → "giới hạn trong baseline & setup đã thử".
> - **Nhỏ:** thêm câu *"exponential concentration of kernel matrix"* (nối kết quả C2 của nhóm).
> - **Đóng gói nộp:** bản sạch + bản highlight vàng + rebuttal **point-by-point** + cover letter; giữ **≤12 trang** (né MOPC).
> - **Đổi affiliation (nếu có):** khai ở rebuttal + cover letter.
