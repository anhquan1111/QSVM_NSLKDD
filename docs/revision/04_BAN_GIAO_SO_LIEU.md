# Báo cáo bàn giao số liệu — Paper 1 Major Revision

> **Mục đích**: một tài liệu duy nhất để viết lại manuscript. Với **từng bảng, từng hình, từng
> claim** của bản đã nộp: số cũ là gì, số mới là gì, đóng item reviewer nào, và câu chữ đề xuất.
>
> Cập nhật: 2026-09-03 · Deadline: **13-Oct-2026** · Bản đã nộp: `paper/paper1/paper1.pdf`
>
> Tài liệu liên quan: [00_STATUS](00_STATUS_paper1.md) (bóc 33 item reviewer) ·
> [02_PROGRESS](02_PROGRESS.md) (nhật ký 22 phát hiện) ·
> [c4_claim_audit](c4_claim_audit.md) (truy vết claim sai)

---

# PHẦN A — Trạng thái 33 item reviewer

| Trạng thái | Số item | Ghi chú |
|---|---:|---|
| ✅ Đã đóng bằng bằng chứng | **21** | có số, có artifact, có câu chữ đề xuất |
| 🟡 Đóng một phần | **3** | cần viết thêm vào bài |
| ❌ Chưa làm | **9** | refs, literature, theory, đóng gói — việc viết, không cần chạy |

## Đã đóng

| Item | Bằng chứng | Ở đâu |
|---|---|---|
| **R4-1** Theorem 1 sai | Bỏ Theorem 1, thay bằng luật 3 tầng; Pareto chỉ là diagnostic (9/9 candidate non-dominated) | C1 note |
| **R1-3, R4-5** Tuning bất đối xứng | Tuning set riêng + 1-SE cho C2; C4 tune cả 7 model tại **mỗi (N, run)** | C2 note, §D-4 |
| **R1-5, R2-1, AE-5** Baseline yếu | RF + XGBoost ở **mọi** contribution và **mọi** regime | C2/C3/C4 |
| **R1-6, R3-4, AE-6** NISQ chỉ ideal | FakeManilaV2 + Aer, 3 điều kiện | C2 note |
| **R2-2** Kernel concentration | R_eff 5.78→114.7, off-diag std 0.326→0.131 | C1 note |
| **R2-3** Thống kê mỏng | 10 run + CI + Wilcoxon + d_z + Holm ở C2/C3/C4 | tất cả |
| **R2-4** Regime âm thiếu thống kê | Mọi ô của C3 đều có Δ/CI/p/d_z/verdict | C3 note |
| **R3-2** Gain quá nhỏ | Báo cáo ΔF1 non-significant một cách trung thực | C2 note |
| **R1-7** Có crossover không? | **Có, N≈2000–5000 trên NSL-KDD, ngược chiều claim cũ; KHÔNG có trên UNSW** | §B-6, §C |
| **R1-8** Table IV vs VI | Phân rã: −0.051 do test set, +0.011 do representation | §B-4 |
| **R1-9** F1 thấp bất thường | Cùng model/feature/train, chỉ đổi test set: 0.804 vs **0.999** | §B-7 |
| **R4-4** Rare-attack không kiểm chứng được | Claim cũ **sai**; bảng đầy đủ mọi N × 7 model | §B-5 |
| **R1-2, AE-4** Dataset thứ hai | UNSW-NB15 đầy đủ giao thức, 1.680 bản ghi | §C |
| **R3-1** Novelty thấp | C1 chạy độc lập trên UNSW cho **n\*=6 ≠ 4** → là thủ tục, không phải hằng số | §C-1 |
| **R1-4, AE-1** Overclaim | 110 ô regime map: **21 QSVM / 21 classical / 68 inconclusive** | §D-1 |

## Chưa làm — đều là việc viết

R1-1, AE-2 (literature 2025–26) · R3-5 (novelty matrix vs 2 arXiv) · R3-3, R4-3 (hạ Proposition) ·
R2-5, R2-6, AE-3 (audit references) · R1-10 (đóng gói supplementary) · R4-2 (repo public)

---

# PHẦN B — Thay đổi từng bảng, từng hình

## B-1. Table III (C1 — Pareto sweep) → **THAY HOÀN TOÀN**

**Cũ**: cột `J(n)|α=β=γ=1/3`, đánh dấu Pareto, dẫn tới Theorem 1.
**Sai ở đâu**: Theorem 1 phát biểu `F̃(4) > F̃(3)` nhưng bảng cho `0.471 < 0.628` (R4 bắt).

**Mới**: bảng của C1 revision với luật 3 tầng. `V(n) ≥ 0.85` → `KTA ≥ 0.95·KTA_max` → `min Q(n)`.
Kết quả **vẫn là n=4**, nhưng được biện minh khác hẳn.

| Số then chốt | Giá trị |
|---|---|
| Vùng feasible theo thông tin | {4,…,10} |
| Vùng feasible theo KTA | **{4, 5, 6}** |
| n\* | **4** (V=86.62%, KTA=0.2364, 24 CNOT) |
| Pareto | **cả 9 candidate đều non-dominated** → chỉ là diagnostic |
| Độ nhạy ε | ε=0.02 → n=5; ε=0.05 và 0.10 → n=4 |

⚠️ Phải ghi rõ ε=0.02 cho n=5 — đừng giấu.

**Nguồn**: `data/nslkdd/processed_data/c1_selection.json`

---

## B-2. Table IV (C2 — multi-run) → **CẬP NHẬT SỐ**

| Model | Cũ (5 seed, C=1.0) | Mới (10 run, C tuned) |
|---|---:|---:|
| **QSVM-ZZ** | 0.854 ± 0.016 | **0.846888** |
| QSVM-Z | 0.827 ± 0.015 | **0.835528** |
| SVM-RBF | 0.838 ± 0.013 | **0.836186** |
| SVM-Poly2 | 0.829 ± 0.034 | **0.832657** |
| SVM-Linear | 0.813 ± 0.016 | **0.813655** |
| **RandomForest** | — | **0.844636** |
| **XGBoost** | — | **0.850310** |

**Thứ hạng mới**: XGB > QSVM-ZZ > RF > RBF > Z > Poly2 > Linear.

Ablation: ΔF1 = **+0.011360**, CI [−0.005408, +0.028128], p=0.2324 → **không significant**.
ΔKTA = **+0.137807**, CI [0.126738, 0.148876], p=0.001953, d_z=8.91 → **rất mạnh**.

⚠️ Con số 0.854 trong Abstract phải đổi thành 0.847, và phải bỏ hàm ý "thắng mọi baseline".

**Nguồn**: `results/nslkdd/c2_revision/c2_per_run.csv`, `c2_paired_statistics.csv`

---

## B-3. Table V + Fig 8 (C3 — prior shift) → **VIẾT LẠI KẾT LUẬN**

**Cũ**: prior-shift là regime thắng, Cohen's d ∈ [+0.72, +1.26] so với 6 baseline SVM.

**Mới**: khi thêm RF/XGB thì **không còn là regime thắng rõ**.

| Điều kiện | Kết quả |
|---|---|
| Prior 30% | Chỉ thắng SVM-Linear; còn lại inconclusive |
| Prior 50% | Chỉ thắng QSVM-Z |
| Prior 70% | Thắng QSVM-Z; **XGBoost borderline thắng ZZ** |
| Attack-composition (DoS) | Thắng toàn bộ SVM/kernel; **hoà RF/XGB** |

⚠️ **Ô `prior_shift/attack_70pct/XGBoost` KHÔNG ROBUST** — hai máy chạy cùng code đã seed cho
hai verdict ngược nhau (holm_p 0.0391 vs 0.0977). Phải báo cáo là borderline.

**Nguồn**: `results/nslkdd/c3_revision/c3_pairwise_statistics.csv`

---

## B-4. Table VI + Fig 9 (C4 — sample complexity) → **THAY HOÀN TOÀN**

**Cũ** (1 seed, 3 baseline SVM): QSVM-ZZ 0.813/0.797/0.831/0.813, Δ vs best +0.080/+0.039/+0.066/+0.069.

**Mới** — hai chế độ lấy mẫu, 10 run, 7 model, test đầy đủ:

### Chế độ `natural` (tỉ lệ lớp tự nhiên) — **dùng làm bảng chính**

| N | QSVM-ZZ | QSVM-Z | SVM-RBF | RF | XGB |
|---:|---:|---:|---:|---:|---:|
| 100 | 0.6989 | 0.7613 | 0.7296 | 0.7695 | **0.7802** |
| 1000 | 0.7717 | 0.7666 | 0.7745 | 0.7913 | **0.8007** |
| 2000 | 0.7781 | 0.7615 | **0.7919** | 0.7839 | 0.7910 |
| 5000 | **0.7820** | 0.7596 | 0.7794 | 0.7737 | 0.7720 |
| 10000 | **0.7855** | 0.7787 | 0.7740 | 0.7728 | 0.7706 |

### Verdict QSVM-ZZ vs XGBoost (Holm)

| N | Δ | Holm p | Verdict |
|---:|---:|---:|---|
| 100 | −0.0812 | 0.0039 | classical |
| 1000 | −0.0289 | 0.0078 | classical |
| 2000 | −0.0129 | 0.2617 | inconclusive |
| **5000** | **+0.0100** | **0.0273** | **QSVM** |
| **10000** | **+0.0149** | **0.0078** | **QSVM** |

### Table IV vs Table VI — phân rã (đóng R1-8)

| | QSVM-ZZ |
|---|---:|
| Table IV (frozen repr + test 300) | 0.8469 |
| Table VI (refit repr + test 22.544) | 0.8072 |
| **Tổng chênh** | **−0.0397** |
| ↳ do **đổi test set** | **−0.0510** |
| ↳ do đổi representation | +0.0113 |

Ô đối chứng tái tạo chính xác 0.8469 của C2 → lưới đáng tin.

**Nguồn**: `results/nslkdd/c4_revision/c4_per_run_natural_refit_per_N.csv`,
`c4_pairwise_statistics_natural.csv`, `c4_table_iv_vs_vi.csv`

---

## B-5. Claim rare-attack → **SAI, PHẢI THAY**

**Cũ**: *"At N=500 QSVM-ZZ still leads by +6.7 points over SVM-RBF on the rare-attack subset,
with a Cohen's d of +0.68 on the per-sample decision margins."*

**Ba lỗi**:
1. `+6.7` = Δ so với **SVM-Linear** trên **toàn tập 22.544**, không phải vs RBF trên rare subset
   (vs RBF trên toàn tập là +10.0)
2. Không có file nào trong repo chứa F1/recall trên rare subset ở N=500
3. `d=+0.68` không tái tạo được. Số thật của C6 là **+0.4043**. Giá trị 0.68 duy nhất trong repo
   là `c5_results.json → −0.68048` — **ngược dấu**, từ thí nghiệm khác (train=99, 10 mẫu rare)

**Lỗi phương pháp nghiêm trọng hơn**: C5/C6 tính effect size trên `|margin|`. Signed margin trên
rare subset **âm với mọi model** (−0.20 đến −0.98) → `|margin|` lớn = **sai một cách tự tin hơn**.

### Số mới tại N=500, `matched`, test đầy đủ

| So với | d trên \|margin\| (cách cũ) | d trên **signed margin** | Δ F1_rare |
|---|---:|---:|---:|
| SVM-RBF | −0.3074 | +0.0831 | **+0.0235** |
| SVM-Linear | −0.2329 | −0.0771 | −0.0828 |
| XGBoost | **+1.1638** | +0.0297 | +0.1032 |
| RandomForest | **+1.4222** | −0.0175 | +0.0944 |

`|margin|` cho +1.42 với RF nhưng −0.31 với RBF — cùng model, hai kết luận ngược nhau.

**Câu thay thế**:

> At \(N=500\), QSVM-ZZ attains a rare-subset (U2R ∪ R2L, 2,952 samples) F1 of 0.577, which is
> +0.024 over SVM-RBF, +0.103 over XGBoost and +0.094 over Random Forest, but −0.083 below
> SVM-Linear. Cohen's \(d\) on **signed** decision margins is negligible against every baseline
> (\(|d| \le 0.09\)). The mean signed margin on the rare subset is negative for all evaluated
> models, so effect sizes computed on absolute margins are not interpretable.

**Nguồn**: `results/nslkdd/c4_revision/c4_rare_attack.csv`

---

## B-6. Fig 10 (Regime map) → **DỰNG LẠI TỪ BỘ SỐ CHUNG**

Dùng `results/nslkdd/regime_map_rows.csv` — **110 dòng**, gộp C2 + C3 + C4, cùng schema.

| Contribution | QSVM-favorable | classical-favorable | inconclusive |
|---|---:|---:|---:|
| C2 | 1 | 0 | 1 |
| C3 | 7 | 10 | 19 |
| C4 | 13 | 11 | 48 |
| **Tổng** | **21** | **21** | **68** |

**Con số này tự nó đóng AE-1 và R1-4.** Không còn cơ sở viết *"the quantum advantage is real"*.

Ô QSVM thắng mạnh nhất, dùng cho hình:

| Contribution | Regime | Baseline | Δ | p | d_z |
|---|---|---|---:|---:|---:|
| C2 | ΔKTA | QSVM_Z | +0.1378 | 0.0020 | 8.91 |
| C3 | attack_composition | SVM_Linear | +0.0650 | 0.0059 | 3.02 |
| C4 | N=10000 natural | **XGBoost** | +0.0149 | 0.0078 | 1.07 |
| C4 | N=10000 natural | **RandomForest** | +0.0127 | 0.0078 | 1.13 |

⚠️ **C4 là contribution DUY NHẤT có ô QSVM thắng một tree ensemble với ý nghĩa thống kê.**

---

## B-7. Mục mới: "Benchmark protocol versus literature" (đóng R1-9)

| Cấu hình | Model | Feature | macro-F1 | recall_rare |
|---|---|---:|---:|---:|
| **A** train đầy đủ → test **KDDTest+** | XGB | 122 | 0.8041 | 0.1037 |
| **B** train đầy đủ → test **random split KDDTrain+** | XGB | 122 | **0.9993** | — |
| **C** K=20+PCA-4 → test KDDTest+ | XGB | 4 | 0.7655 | 0.1799 |

1. **A vs B là toàn bộ lời giải thích**: cùng model, cùng feature, cùng train, chỉ đổi test set
   → **cách nhau ~20 điểm**. Con số 99% trong literature NSL-KDD đến từ chia ngẫu nhiên KDDTrain+.
2. Giảm 122 → 4 chiều chỉ mất **0.039** macro-F1, và **cải thiện** recall lớp hiếm (0.104 → 0.180).
3. Đáng đưa vào bài: QSVM-ZZ ở N=10.000 với **4 chiều** đạt 0.7855, **cao hơn RandomForest dùng
   toàn bộ 125.973 mẫu và 122 feature** (0.7765).

**Nguồn**: `results/nslkdd/c4_revision/c4_protocol_vs_literature.csv`

---

# PHẦN C — Mục UNSW-NB15 (thay hoàn toàn)

Chi tiết đầy đủ: [`note/C4/UNSW_transfer_results_and_manuscript_revision.md`](../../notebooks/nslkdd/note/C4/UNSW_transfer_results_and_manuscript_revision.md)

## C-1. Luật C1 chọn n\*=6 trên UNSW

`K*=35` (elbow δ=0.01) → `V≥0.85` cho {4…10} → `KTA≥0.95×0.1986` cho **{6}** → `min Q` → **n\*=6**.
Vững **10/10 subset** ở ε=0.02 và 0.05.

> **Đây là câu trả lời cho R3-1**: C1 là thủ tục chuyển giao được, không phải hằng số. Mọi kết
> quả UNSW cũ dùng n=4 là dưới tối ưu theo chính tiêu chí của nhóm.

## C-2. Crossover KHÔNG chuyển giao

| N | NSL-KDD Δ(ZZ−XGB) | UNSW Δ(ZZ−XGB) |
|---:|---:|---:|
| 1000 | −0.029 | −0.041 |
| 5000 | **+0.010** ✅ | −0.016 ❌ |
| 10000 | **+0.015** ✅ | −0.020 ❌ |

Không có ô QSVM thắng tree ensemble ở bất kỳ N nào. Arm `tuned_once` cho cùng kết luận.

## C-3. Ablation entanglement CÓ chuyển giao, mạnh gấp đôi

| N | ZZ − Z | p | Verdict |
|---:|---:|---:|---|
| 2000 | +0.0185 | 0.049 | QSVM |
| 5000 | +0.0424 | 0.002 | QSVM |
| 10000 | +0.0449 | 0.002 | QSVM |

Tái lập độc lập phát hiện "entanglement cần đủ dữ liệu để ước lượng cơ sở biểu diễn".

## C-4. Rare-attack KHÔNG chuyển giao

Mọi model recall **0.94–0.99**, signed margin **dương**. Lớp hiếm UNSW đều là attack và 68%
train là attack → dễ. Không được nói phát hiện rare-attack tổng quát hoá.

## C-5. Bắt buộc khai trong Limitations

- UNSW-NB15 trùng lặp **47% nội bộ**, **25% hàng test có bản sao trong train** (kiểm chứng trên
  dữ liệu thô: 25.33%). Lớp `Generic`: 40.000 hàng / 1.800 chữ ký = **95.5% trùng lặp**.
- n\*=6 nâng chi phí từ 24 lên **60 CNOT**.
- UNSW không có split thời gian → không có regime temporal.
- Không lặp noise validation trên UNSW.

---

# PHẦN D — Câu chữ và cấu trúc

## D-1. Bảng thay claim

| Claim cũ | Thay bằng |
|---|---|
| *"The quantum advantage is real and measurable in two regimes"* | *"Within the evaluated baselines and protocol, QSVM-ZZ shows a regime- and comparator-dependent empirical advantage"* |
| *"QSVM-ZZ dominates every classical baseline at every N"* | *"classical ensembles are significantly better below N≈2000; QSVM-ZZ becomes significantly better above N≈5000 on NSL-KDD, but not on UNSW-NB15"* |
| *"+6.7 points ... Cohen's d of +0.68"* | xem §B-5 |
| *"Under class-prior shift the quantum kernel attains the highest mean F1"* | *"...highest among the SVM-family baselines; XGBoost is borderline favourable in the attack-heavy condition"* |
| *"NISQ-feasible / NISQ-ready"* | *"NISQ-aware; backend-derived noisy simulation, not physical-device validation"* |
| Theorem 1, Def 4, Algorithm 1 | luật 3 tầng của C1; **bỏ Theorem 1** |
| Proposition 3 | một câu cite, bỏ khung "Proposition" |
| *"six classical SVM baselines"* | *"six SVM configurations and two strong tabular learners"* |
| *"n=4 is the NISQ-feasible choice"* | *"the rule yields n=4 on NSL-KDD and n=6 on UNSW-NB15"* |

## D-2. Hình cần làm lại

| Hình | Việc |
|---|---|
| **Fig 5** (C1) | Bỏ Pareto-as-selector. 3 panel: V(n) · KTA(n) với ngưỡng 0.95 · Q(n), highlight {4,5,6} |
| **Fig 9** (learning curve) | 2 panel log-x, 7 model + dải CI: (a) `natural` cho thấy crossover, (b) `matched` cho thấy làm giàu lớp hiếm xoá crossover. Đánh dấu vùng N∈[2000,5000] |
| **Fig 10** (regime map) | Dựng lại từ `regime_map_rows.csv`, có cả ô âm và inconclusive |
| **Mới** | Learning curve UNSW cạnh NSL-KDD — cho thấy crossover không chuyển giao |

## D-3. Bảng cần thêm

1. Rare-subset (F1, recall, signed margin, d, CI) ở mọi N — bảng R4 đòi mà không tìm thấy
2. Protocol vs literature (§B-7)
3. Table IV vs VI decomposition (§B-4)
4. C1 trên UNSW (§C-1)
5. Bảng "cái gì chuyển giao / cái gì không" (§C)

## D-4. Mục Methodology cần sửa

- **III-C (C1)**: bỏ Def 4 + Algorithm 1 + Theorem 1, thay bằng luật 3 tầng
- **III-F (C4)**: khai rõ 2 chế độ lấy mẫu và lý do; khai `train_run{i}` giàu lớp hiếm 12×
- **IV-B**: `C_QSVM=1.0` cố định → tune đối xứng 7 model tại mỗi (N, run)
- **Mới**: mục Reproducibility ghi các nguồn phi tất định đã phát hiện (xem §E)

---

# PHẦN E — Limitations bắt buộc bổ sung

1. **XGBoost phụ thuộc máy** ±0.01/run ngay cả với `n_jobs=1` và seed cố định. Hai máy chạy
   cùng code cho hai verdict ngược nhau ở ô `prior_shift/70%` (holm_p 0.0391 vs 0.0977). Dịch
   chuyển kỳ vọng +0.0010, nhỏ hơn một bậc so với độ rộng CI của crossover nên kết luận không đổi.
2. **NSL-KDD**: 610/22.544 hàng test (2.71%) có bản sao chính xác trong train.
3. **UNSW-NB15**: 25% hàng test có bản sao trong train; 47% trùng lặp nội bộ.
4. **`train_run{i}` giàu lớp hiếm 12×** so với tỉ lệ tự nhiên — nền của C2, C3 và Table IV.
5. `n=4` (NSL-KDD) và `n=6` (UNSW) kế thừa từ C1, không chọn lại ở mỗi N.
6. Chế độ `matched` dừng ở N=2000 vì 10 run chia sẻ 59% mẫu rare ở N=5000, 94% ở N=8000.
7. Toàn bộ là mô phỏng statevector; noise chỉ có ở C2 trên NSL-KDD.
8. `SVM_Poly2` không hội tụ ở C≥5 trên UNSW → đặt `max_iter=2.000.000`.

---

# PHẦN F — Chỉ mục file: số nằm ở đâu

| Cần gì | File |
|---|---|
| C1 selection NSL-KDD | `data/nslkdd/processed_data/c1_selection.json` |
| C1 selection UNSW | `results/unsw/c4_revision/u1_c1_selection_unsw.json` |
| C2 per-run, paired stats, noise | `results/nslkdd/c2_revision/` |
| C3 mọi regime, pairwise stats | `results/nslkdd/c3_revision/` |
| C4 NSL-KDD learning curve | `results/nslkdd/c4_revision/c4_per_run_{matched,natural}_refit_per_N.csv` |
| C4 NSL-KDD thống kê | `c4_pairwise_statistics_{matched,natural}.csv` |
| C4 rare-attack | `c4_rare_attack.csv`, `c4_rare_attack_natural.csv` |
| Table IV vs VI | `c4_table_iv_vs_vi.csv` |
| Protocol vs literature | `c4_protocol_vs_literature.csv` |
| C4 UNSW | `results/unsw/c4_revision/` |
| **Regime map (một bộ số duy nhất)** | `results/nslkdd/regime_map_rows.csv` |
| Note từng contribution | `notebooks/nslkdd/note/C{1,2,3,4}/` |
| Truy vết claim sai | `docs/revision/c4_claim_audit.md` |
| Nhật ký 22 phát hiện | `docs/revision/02_PROGRESS.md` |
| Audit UNSW | `docs/revision/03_UNSW_AUDIT.md` |

## Lệnh tái tạo

```bash
uv sync
uv run python runners/run_c4.py --dataset nslkdd --regime natural   # C4 NSL-KDD
uv run python runners/run_c4.py --dataset nslkdd --regime matched
uv run python runners/run_c4.py --dataset unsw   --regime natural   # C4 UNSW
uv run python runners/analyze_c4.py --dataset nslkdd --regime natural
uv run python runners/analyze_c4.py --dataset unsw   --regime natural
```

---

# PHẦN G — Việc còn lại

| # | Việc | Ai | Ghi chú |
|---|---|---|---|
| 1 | Audit references: sửa [15] `116990F`→`116990B`, bỏ [26] Rahman, giữ ≤45 | viết | 36 refs hiện tại, dư 9 slot |
| 2 | Literature 2025–26 + QMI-2026 + Carducci ICAD-2026 + 2 arXiv của R3 | viết | R1-1, AE-2, R3-5 |
| 3 | Novelty matrix so với các benchmark gần đây | viết | R3-1, R3-5 |
| 4 | Hạ Proposition 1–4 thành Background; bỏ Proposition 3 | viết | R3-3, R4-3 |
| 5 | Đóng gói supplementary S1–S9 | đóng gói | R1-10 |
| 6 | Repo public + README + lệnh tái tạo | đóng gói | R4-2 |
| 7 | Bản sạch + bản highlight vàng + rebuttal + cover letter | viết | ≤12 trang |
| 8 | **Xin file `.tex` nguồn của bản đã nộp** | 🚨 | không có thì không làm được bản highlight |
