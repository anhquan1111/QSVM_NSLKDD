# Paper 1 — Trạng thái Major Revision (bản đã nộp ↔ reviewer ↔ việc đã làm)

> [!abstract] Mục đích
> File này là **single source of truth** trả lời 3 câu hỏi:
> 1. Bản đã nộp cho TETC thực sự chứa gì (claim nào, bảng nào, số nào)?
> 2. Reviewer đòi chính xác những gì (bóc thành item có ID)?
> 3. Tính đến nay ai đã làm được gì, còn hở chỗ nào?
>
> Cập nhật lần cuối: 2026-09-01 · Deadline nộp: **13-Oct-2026** · **Không có vòng major revision thứ 2.**

---

# PHẦN 0 — Ba phát hiện cần chốt trước khi làm bất cứ việc gì

> [!danger] P0.1 — `paper/paper1/main.tex` KHÔNG PHẢI bản đã nộp
> - **Bản đã nộp = `paper/paper1/paper1.pdf`** (≡ `main_v2.pdf`, cùng nội dung): 11 trang, **4 đóng góp C1–C4**, có Theorem 1, Prop 1–4, **36 references**, UNSW nằm ở **supplementary**.
> - `main.tex` trong repo là một draft KHÁC: **6 đóng góp C1–C6**, không có Theorem 1, UNSW nằm trong **main body**, 37 refs.
> - Bằng chứng bản nộp: reviewer trích đúng `F̃(4)=0.471 / F̃(3)=0.628`, cột `J(n)|α=β=γ=1/3`, ref [15] Payares SPIE `116990F`, ref [26] Rahman IEEE Access — tất cả chỉ có trong `paper1.pdf`.
> - `paper/paper1/manuscript.pdf` là **bài khác hoàn toàn** (LEO satellite routing) — file để nhầm, nên xoá/di chuyển.
>
> **⇒ Hành động bắt buộc: xin thầy file `.tex` NGUỒN của bản đã nộp.** Không có nó thì không tạo được bản highlight vàng (yêu cầu bắt buộc của TETC).

> [!success] P0.2 — KHÔNG có vấn đề đánh số lại contribution
> Bản đã nộp dùng đúng **C1 = embedding, C2 = entanglement ablation, C3 = prior-shift stress, C4 = sample complexity**.
> Notebook `C1_revision / C2_revision / C3_revision` của bạn Quang Anh map **1-1** vào C1/C2/C3 của bản nộp.
> ⇒ **"C4" mà tôi được giao = C4 của bản nộp = sample-complexity sweep + rare-attack margin.** Không cần bảng mapping, không cần viết lại danh sách contribution.
> *(Ghi chú: nhận định "đánh số lệch" ở phiên thảo luận trước dựa trên `main.tex`, tức là dựa trên sai file. Đã đính chính.)*

> [!info] P0.3 — Protocol low-data của bản nộp là RE-FIT, không phải freeze
> `paper1.pdf` Sec. III-F ghi nguyên văn: *"we stratify-sample N rows from the training set, **refit the entire pipeline (including SelectKBest and PCA) on those N rows to enforce zero leakage**, train every model, and evaluate on the full 22,544-sample test split."*
> ⇒ Câu hỏi "freeze hay re-fit" cho C4 đã có đáp án: **re-fit theo từng N là primary** (giữ đúng bản nộp + trung thực với claim low-data). Biến thể frozen-C1 chỉ để supplementary.

---

# PHẦN 1 — Giải phẫu bản đã nộp (`paper1.pdf`)

## 1.1 Bố cục

| Mục | Nội dung |
|---|---|
| I. Introduction | 3 gap: **G1** hardware-blind embedding · **G2** unattributed quantum gains · **G3** operating-regime blindness |
| II. Background & Related Work | Def 1–3 (feature map, quantum kernel, ZZFeatureMap), **Prop 1** (PSD), **Prop 2** (local expansion của ZZ kernel), **Prop 3** (KTA generalisation bound, chỉ cite [23]), **Table I** (coverage 3 gap của 4 work trước) |
| III. Framework | **Assumption 1** (NISQ cost model, 2q error ≈ 5× 1q), **Problem 1**, **Fig 2/3** (pipeline), III-C = **C1** (Pareto + **Def 4** + **Algorithm 1** + **Theorem 1**), III-D = **C2** (ablation + **Prop 4** identifiability của ΔKTA), III-E = **C3**, III-F = **C4** |
| IV. Experimental Setup | IV-B: **QSVM giữ C=1.0 cố định**, classical SVM tune C trên validation fold; 5 seeds `{0,1,2,3,4}`; runtime ~42h |
| V. Results | V-A **C1** (Fig 4 K-sweep, **Table III**, Fig 5) · V-B **C2** (**Table IV**, Fig 6, Fig 7) · V-C **C3** (**Table V**, Fig 8) · V-D **C4** (**Table VI**, Fig 9) · V-E shot-noise (**Table VII**) |
| VI. Regime Map | **Fig 10** forest plot; VI-B "where QSVM does not help"; VI-C decision rule |
| VII. Limitations | hardware noise · embedding size · classical-baseline strength · dataset breadth |
| VIII. Conclusion | — |
| References | **36 refs** (ngân sách TETC = 45 → còn dư ~9 slot) |

## 1.2 Bảng số của bản nộp (dùng để đối chiếu khi sửa)

**Table III — C1 Pareto sweep**

| n | V(n) | F̃(n)=1/DBI | Q(n) | J(n) @α=β=γ=1/3 | Pareto |
|---:|---:|---:|---:|---:|:--:|
| 2 | 0.742 | 0.941 | 0.030 | **0.551** | ✗ |
| 3 | 0.821 | 0.628 | 0.077 | 0.457 | ✗ |
| **4** | 0.866 | **0.471** | 0.145 | 0.397 | ★✓ |
| 5 | 0.904 | 0.378 | 0.234 | 0.349 | ✓ |
| 6 | 0.939 | 0.315 | 0.345 | 0.303 | ✓ |
| 7 | 0.952 | 0.272 | 0.477 | 0.249 | ✓ |
| 10 | 0.981 | 0.196 | 1.000 | 0.059 | ✓ |

→ **Theorem 1 phát biểu `F̃(4) > F̃(3)` nhưng bảng cho `0.471 < 0.628`.** Đây là lỗi R4 bắt.
→ J lớn nhất ở n=2, và n=2/n=3 bị đánh dấu "không thuộc Pareto" trong khi V↑, F̃↓, Q↑ đều đơn điệu ⇒ Pareto không lọc được gì.

**Table IV — C2 multi-run** (N_train=1000, N_test=**300**, 5 seeds)

| Model | F1_macro | KTA | n_SV | C |
|---|---:|---:|---:|---:|
| **QSVM-ZZ** | **0.854 ± 0.016** | 0.205 | 277 | 1.0 |
| QSVM-Z | 0.827 ± 0.015 | 0.070 | 327 | 1.0 |
| SVM-RBF (Std) | 0.838 ± 0.013 | 0.247 | 267 | 10 |
| SVM-Poly2 (Std) | 0.829 ± 0.034 | 0.125 | 404 | 0.1 |
| SVM-RBF (MM) | 0.818 ± 0.009 | 0.247 | 366 | 0.1 |
| SVM-Poly2 / SVM-Lin (MM/Std) | 0.812–0.813 | 0.062–0.125 | 349–369 | 0.1 |

→ ΔKTA = +0.135; Prop 4 cho Z ≈ 10.2.

**Table V — C3 prior shift** (3 test mix × 5 seeds × 300 mẫu): QSVM 0.840 / 0.784 / 0.821, mean **0.815**; Cohen's d vs 6 baseline ∈ **[+0.72, +1.26]**.

**Table VI — C4 sample complexity** (test = **full 22,544**)

| Model | N=100 | N=200 | N=500 | N=1000 |
|---|---:|---:|---:|---:|
| **QSVM-ZZ** | **0.813** | **0.797** | **0.831** | **0.813** |
| SVM-RBF | 0.724 | 0.743 | 0.731 | 0.729 |
| SVM-Poly2 | 0.701 | 0.754 | 0.726 | 0.743 |
| SVM-Linear | 0.733 | 0.758 | 0.765 | 0.737 |
| Δ vs best | +0.080 | +0.039 | +0.066 | +0.069 |

**Table VII — shot noise**: S ∈ {128, 512, 2048, 8192}, 3 seeds; FroSim ≥ 0.996; |ΔF1| ≤ 0.01.

**Fig 10 — regime map**: 6 dòng prior-shift + 1 dòng "C4 low data N=500 margin" + 1 dòng "perturbation σ=0.20" + 1 dòng "temporal shift (McNemar)".

## 1.3 Claim của bản nộp thuộc phần C4 cần kiểm chứng lại

| # | Claim nguyên văn | Ở đâu | Trạng thái |
|---|---|---|---|
| K1 | *"QSVM-ZZ dominates every classical baseline at every N"* | V-D | ⚠️ chỉ 1 seed, chỉ 3 baseline SVM |
| K2 | *"At N=500 QSVM-ZZ still leads by **+6.7 points** over SVM-RBF **on the rare-attack subset**"* | V-D | ❌ nghi sai: +6.7 trùng khít dòng "Δ vs best" của Table VI (toàn tập, so SVM-Lin 0.765), KHÔNG phải rare subset; so với RBF trên toàn tập là +10.0 |
| K3 | *"with a **Cohen's d of +0.68** on the per-sample decision margins"* | V-D, Fig 10 | ❌ artifact nội bộ cho **0.4043** (`results/nslkdd/c6_results.json`) |
| K4 | *"perturbation σ=0.20: QSVM slope −0.835 vs SVM-RBF −0.013"* | VI-B | ⚠️ chỉ định tính; C3_revision đã thay bằng số có CI |
| K5 | Table VI (N=1000) vs Table IV (N=1000) lệch nhau | V-B/V-D | ✅ giải thích được: test 22,544 vs test 300 (chỉ cần viết rõ) |

---

# PHẦN 2 — Bóc reviewer thành item có ID (revision matrix)

| ID | Reviewer | Yêu cầu | Mức |
|---|---|---|---|
| **AE-1** | AE | Claim "advantage" quá generic so với evidence | Critical |
| **AE-2** | AE | Literature 2025–2026 chưa đủ | High |
| **AE-3** | AE | Có reference không tồn tại | Critical (liêm chính) |
| **AE-4** | AE | Cần dataset thứ 2 | Critical |
| **AE-5** | AE | Cần baseline non-SVM | Critical |
| **AE-6** | AE | NISQ-ready không có evidence | Critical |
| **R1-1** | R1 | Thiếu *"Benchmarking QML methods for IDS on noisy quantum computers"* (QMI 2026); cập nhật Table I | High |
| **R1-2** | R1 | Chỉ NSL-KDD; cần dataset IDS hiện đại | Critical |
| **R1-3** | R1 | QSVM C=1.0 cố định trong khi SVM được tune → bất đối xứng | High |
| **R1-4** | R1 | *"quantum advantage is real"* quá mạnh | Critical |
| **R1-5** | R1 | Thiếu XGBoost / CatBoost / TabNet / FT-Transformer | Critical |
| **R1-6** | R1 | Chỉ finite-shot; cần gate/decoherence/readout noise | Critical |
| **R1-7** | R1 | Low-data: QSVM thắng ở MỌI N → có crossover không? | High |
| **R1-8** | R1 | Table VI (N=1000) mâu thuẫn Table IV | Medium |
| **R1-9** | R1 | F1 classical thấp bất thường so với literature NSL-KDD | Medium |
| **R1-10** | R1 | Không truy cập được supplementary | Critical |
| **R2-1** | R2 | Baseline chỉ SVM, industry dùng RF/XGB/TabNet | Critical |
| **R2-2** | R2 | Phải nhắc *"exponential concentration of the kernel matrix"* | Medium |
| **R2-3** | R2 | 5 seeds + N=1000 là base thống kê mỏng | High |
| **R2-4** | R2 | Regime thắng có full stats, regime thua chỉ định tính | High |
| **R2-5** | R2 | Ref [15]: `116990F` → phải là `116990B` | Critical (liêm chính) |
| **R2-6** | R2 | Ref [26] Rahman không tìm thấy — nghi bịa | Critical (liêm chính) |
| **R3-1** | R3 | Novelty thấp: ZZ 4-qubit depth-2 là cấu hình chuẩn | High |
| **R3-2** | R3 | Gain 0.854 vs 0.838 quá nhỏ để nói advantage | High |
| **R3-3** | R3 | Proposition/Theorem là fact đã biết, đóng khung định lý không phù hợp | High |
| **R3-4** | R3 | Gọi NISQ-aware nhưng toàn ideal simulation | Critical |
| **R3-5** | R3 | Đã có benchmark tương tự: arXiv:2403.07059, arXiv:2409.04406 | High |
| **R4-1** | R4 | **Theorem 1 sai chiều**; nghi Pareto không lọc gì | Critical |
| **R4-2** | R4 | Nói reproducible nhưng không có link code | Critical |
| **R4-3** | R4 | Proposition 3 chỉ cite, không prove/derive | Medium |
| **R4-4** | R4 | Không có số cho rare-attack N=500 (+6.7 / d=0.68) | Critical |
| **R4-5** | R4 | Quantum kernel không được tune trong khi classical được; gợi ý cite Carducci ICAD-2026 | High |

---

# PHẦN 3 — Đã làm được gì (tính đến 2026-09-01)

## 3.1 Bạn Quang Anh — C1 (FROZEN)

📁 [C1_revision.ipynb](../../notebooks/nslkdd/C1_revision.ipynb) · note: [C1_final_results…md](../../notebooks/nslkdd/note/C1/C1_final_results_and_manuscript_revision_plan_final.md) · artifact: [c1_selection.json](../../data/nslkdd/processed_data/c1_selection.json)

- **Xoá bỏ** `J(n)` scalarization, Pareto-as-selector, và **Theorem 1**.
- Thay bằng luật 3 tầng, không có tham số ẩn:
  `V(n) ≥ 0.85` → `KTA(n) ≥ 0.95 · max KTA trong vùng feasible` → `min Q(n)` → **n\* = 4**
- Sửa công thức chi phí: `N_CNOT(n) = 2r·C(n,2)` (mỗi ZZ = CNOT–RZ–CNOT). n=4, r=2 → 12 CNOT/layer, **24 CNOT tổng**.
- Tự chứng minh điều R4 nghi ngờ: **cả 9 candidate đều Pareto-optimal, 0 bị dominate** ⇒ Pareto giờ chỉ là diagnostic.
- Thêm: bootstrap KTA CI (n=4: 0.2364, CI [0.2119, 0.2762]), ε-sensitivity (**ε=0.02 sẽ chọn n=5** — báo cáo trung thực), finite-shot tách khỏi selection.
- Phát hiện khoa học mới đáng giá: **n=7–10 bị loại vì KTA tụt, dù giữ nhiều variance hơn** ⇒ "nhiều chiều hơn ≠ kernel tốt hơn".

**Đóng:** R4-1 ✅ · R2-2 ✅ (số: R_eff 5.78→114.7, off-diag std 0.326→0.131) · R3-1 🟡

## 3.2 Bạn Quang Anh — C2 (mạnh nhất)

📁 [C2_revision.ipynb](../../notebooks/nslkdd/C2_revision.ipynb) · results: [c2_revision/](../../results/nslkdd/c2_revision/)

- **Tuning set riêng 2000 mẫu** (seed 200), 5-fold CV, quy tắc 1-SE → **C_Q\* = 3.0**, ép `C_ZZ = C_Z`. Kiểm tra `D_tune ∩ D_i = ∅` cho cả 10 run.
- **10 runs** (seed 100–109), N=1000, test 300.
- **7 model**: QSVM-ZZ, QSVM-Z, SVM-Lin, SVM-Poly2, SVM-RBF, **RandomForest**, **XGBoost**.
- **Noise thật**: IBM **FakeManilaV2** + Qiskit Aer, transpile theo backend (ZZ: depth 70, **48 CX**; Z: depth 8, **0 CX**), 3 điều kiện ideal / finite-shot / noisy.

| Đại lượng | Giá trị | CI 95% | p (Wilcoxon) | d_z |
|---|---:|---|---:|---:|
| ΔKTA (ZZ−Z) | **+0.1378** | [0.1267, 0.1489] | 0.00195 | 8.91 |
| ΔF1 (ZZ−Z) | +0.0114 | [−0.0054, 0.0281] | 0.232 | 0.48 |

Xếp hạng F1 (10-run mean): **XGB 0.8516 > QSVM-ZZ 0.8469 > RF 0.8446 > RBF 0.8362 > Z 0.8355 > Poly2 0.8323 > Lin 0.8137**
Noise: KTA_ZZ 0.1965 → 0.1500; `D_F` = 0.60 (ZZ) vs 0.17 (Z) — khớp footprint 48 CX vs 0 CX.

**Đóng:** R1-3 ✅ · R4-5 ✅ · R1-5/R2-1/AE-5 ✅ (mức tối thiểu) · R1-6/R3-4/AE-6 ✅ · R2-3 ✅ (cho C2) · R3-2 ✅ · AE-1 🟡

## 3.3 Bạn Quang Anh — C3 (regime map trung thực)

📁 [C3_revision.ipynb](../../notebooks/nslkdd/C3_revision.ipynb) · results: [c3_revision/](../../results/nslkdd/c3_revision/)

Kế thừa nguyên hợp đồng C2. 4 regime × 110 evaluation context × 770 bản ghi. Mỗi so sánh có Δ / CI / Wilcoxon / d_z / Holm / verdict; temporal có thêm 120 bản ghi McNemar.

| Regime | Kết luận |
|---|---|
| Temporal shift | **Thua** Z/Linear/Poly2 (d_z −1.0…−1.4); **hoà** RBF/RF/XGB |
| Feature perturbation | **Thua toàn bộ 6 baseline** (\|d_z\| 2.62–4.78) — regime âm rõ nhất |
| Prior 30% | Gần như inconclusive; chỉ thắng SVM-Linear |
| Prior 50% | Thắng Z; còn lại inconclusive |
| Prior 70% | Thắng Z (p=0.006) **nhưng XGBoost thắng ZZ** (p=0.027) |
| Attack-composition (DoS) | Thắng toàn bộ SVM/kernel baseline; **hoà** RF/XGB |

**Đóng:** R2-4 ✅ · R2-3 ✅ · R1-5/R2-1 ✅ · AE-1 ✅ (evidence)

> [!warning] Hệ quả narrative không thể tránh
> Bản nộp nói prior-shift là regime thắng với d ∈ [+0.72, +1.26] so với **6 baseline SVM**. Khi thêm RF/XGB, prior-shift **không còn là regime thắng rõ ràng** (XGB thắng ở prior 70%). Regime thắng chắc chắn còn lại là **attack-composition (DoS)** và **ZZ vs Z (attribution)**. Toàn bộ Sec. VI + Abstract + Conclusion phải viết lại theo đó.

## 3.4 Hợp đồng đóng băng mà C4 và UNSW phải kế thừa

```text
Representation : SelectKBest K=20 → PCA n=4 → MinMax[0, π]   (quantum)
                 SelectKBest K=20 → PCA n=4 → StandardScaler (classical SVM)
Feature map    : ZZFeatureMap, r=2, entanglement=full, FidelityStatevectorKernel
Hyperparameter : C_QSVM-ZZ = C_QSVM-Z = 3.0
                 SVM-Linear C=0.1 · SVM-Poly2 C=0.1 · SVM-RBF C=5.0
                 RF (n=200, depth=None, leaf=1) · XGB (n=500, depth=5, lr=0.1, subsample=0.8)
Runs           : 10 seeds {100..109}, tuning set 2000 (seed 200), disjoint
Thống kê       : paired Δ, CI 95%, Wilcoxon signed-rank, d_z, Holm trong họ so sánh
```

Nguồn: [c2_downstream_tuned_parameters.json](../../results/nslkdd/c2_revision/c2_downstream_tuned_parameters.json)

---

# PHẦN 4 — Bảng trạng thái toàn bộ 33 item

| ID | Trạng thái | Ai | Bằng chứng / việc còn lại |
|---|---|---|---|
| R4-1 | ✅ Xong | QA | C1: bỏ Theorem 1, Pareto chỉ là diagnostic |
| R2-2 | ✅ Xong (số) | QA | C1 kernel-geometry; **còn**: viết 1 đoạn vào Background |
| R1-3, R4-5 | ✅ Xong | QA | C2: tuning set + C_Q\*=3.0 |
| R1-5, R2-1, AE-5 | ✅ Mức tối thiểu | QA | RF + XGB ở C2 & C3; **chưa** CatBoost / TabNet / FT-Transformer |
| R1-6, R3-4, AE-6 | ✅ Xong | QA | C2: FakeManilaV2 + Aer, 3 điều kiện |
| R2-3 | ✅ Xong C2/C3 | QA | 10 runs; **còn**: C4 và UNSW phải đồng bộ |
| R2-4 | ✅ Xong | QA | C3: mọi regime có Δ/CI/p/d_z |
| R3-2 | ✅ Xong (framing) | QA | C2 báo ΔF1 non-significant trung thực |
| **R1-7** | ❌ Chưa | **Tôi** | Crossover: cần mở rộng N |
| **R1-8** | ❌ Chưa | **Tôi** | Table IV vs VI: đánh giá trên cả 2 test set |
| **R4-4** | ❌ Chưa | **Tôi** | Rare-attack N=500: bảng số + chốt d thật |
| **R1-2, AE-4** | ❌ Chưa | **Tôi** | UNSW-NB15 nâng lên chuẩn mới |
| **R1-9** | ❌ Chưa | **Tôi** | Subsection giải thích protocol vs literature |
| **R1-10** | ❌ Chưa | **Tôi** | Đóng gói supplementary |
| **R4-2** | ❌ Chưa | **Tôi** | Repo public + README + uv sync |
| R1-1, AE-2 | ❌ Chưa | QA / thầy | QMI-2026 + literature 2025–26 + Table I mới |
| R3-5 | ❌ Chưa | QA / thầy | Novelty matrix vs arXiv:2403.07059 & 2409.04406 |
| R3-1 | 🟡 Một phần | QA / thầy | Định vị lại novelty = evaluation framework |
| R3-3, R4-3 | ❌ Chưa | thầy | Hạ Prop 1–4 thành Background; bỏ Prop 3 |
| R1-4, AE-1 | ❌ Chưa | thầy | Sửa chữ toàn bài (bảng thay claim trong file plan) |
| R2-5, R2-6, AE-3 | ❌ Chưa | thầy | Sửa [15], bỏ [26], audit ≤45 refs, highlight vàng |
| — | ❌ Chưa | thầy | Bản sạch + bản highlight + rebuttal + cover letter + ≤12 trang |
| — | 🚨 **BLOCKER** | thầy | **Chưa có file `.tex` nguồn của bản đã nộp** |

## Tổng kết một dòng

> Bạn Quang Anh đã đóng **13/33 item**, gồm gần như toàn bộ nhóm "phương pháp bất đối xứng / thống kê mỏng / thiếu baseline mạnh / thiếu noise thật / Theorem sai".
> Phần còn lại chia ba: **(a) C4 + UNSW + reproducibility = việc của tôi (7 item)**, **(b) literature/novelty (4 item)**, **(c) văn bản/refs/đóng gói = thầy (9 item)**.
