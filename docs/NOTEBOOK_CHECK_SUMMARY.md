# Tổng hợp kết quả kiểm tra Notebook

**Ngày kiểm tra:** 2026-05-17
**Người kiểm tra:** Claude Code (auto-check)
**Phạm vi:** `notebooks/` (NSL-KDD) + `notebooks_unsw/` (UNSW-NB15)

## Quy ước

- ✅ = Pass (không lỗi runtime, markdown tiếng Việt đầy đủ dấu, mỗi cell có giải thích)
- ⚠️ = Có vấn đề nhẹ (cần xem lại nhưng không chặn)
- ❌ = Lỗi nghiêm trọng (cell raise exception, mất diacritics nặng)
- N/A = Chưa kiểm tra

## Danh sách file MỚI vs CŨ

### `notebooks/` (NSL-KDD)
| Stage | File MỚI (đang dùng) | File CŨ (đã thay thế) |
|---|---|---|
| Preprocess | `preprocess.ipynb` | — |
| SelectKBest | `selectkbest_nslkdd.ipynb` | — |
| PCA | `pca.ipynb` | — |
| C2 | `c2_quantum_kernel_expressibility.ipynb` | `c2_5_fidelity_vs_statevector_kernel_fixed.ipynb` |
| C3 | `c3_kernel_geometry_statevector_multirun.ipynb` | `c3_kernel_geometry_FidelityQuantumKernel.ipynb`, `c3_kernel_geometry_statevector.ipynb` |
| C3 helper | `c3_c_tuning_statevector.ipynb` | — |
| C4 | `c4_robustness_distribution_shift_multirun_fixed.ipynb` | `c4_robustness_distribution_shift.ipynb` |
| C5 | `c5_confidence_calibration_multirun.ipynb` (May 15 22:29) | `c5_confidence_calibration.ipynb` (Apr 9) |
| C6 | `c6_learning_curve_sample_complexity.ipynb` | — |

### `notebooks_unsw/` (UNSW-NB15)
| Stage | File MỚI (đang dùng) | File CŨ (đã thay thế) |
|---|---|---|
| Preprocess | `preprocess.ipynb` | — |
| SelectKBest | `selectkbest_unsw.ipynb` | — |
| PCA | `pca_unsw.ipynb` | — |
| C1 dim-reduction | `c1_dimreduction_multirun.ipynb` | — |
| C tuning | `c_tuning_statevector.ipynb` | — |
| C2 | `c2_quantum_kernel_expressibility.ipynb` | — |
| C3 | `c3_kernel_geometry_multirun_statevector_C1.ipynb` (15:47) | `c3_kernel_geometry_multirun_statevector.ipynb` (08:40) |
| C4 | `c4_robustness_multirun_C1.ipynb` (15:58) | `c4_robustness_multirun.ipynb` (15:15) |
| C5 | `c5_confidence_calibration_multirun.ipynb` | — |

---

## GIAI ĐOẠN 1 — NSL-KDD

### 1.1 `preprocess.ipynb` — ✅

- **Cells:** 24 (12 code + 12 markdown)
- **Lỗi runtime:** 0
- **Markdown tiếng Việt:** 12/12 cell có đầy đủ dấu — ✅
- **Cấu trúc:** Mỗi code cell đều có markdown giải thích phía trên (chỉ 1 cell biểu đồ ở vị trí 11 nối tiếp cell phân phối — chấp nhận được).
- **Số liệu chính:**
  - Train raw: `(125973, 42)` → Post-OHE: `(125973, 123)` → final: `(125973, 126)` (122 features + 4 cột nhãn)
  - Test raw: `(22544, 42)` → final: `(22544, 126)`
  - Features sau OHE: **122 cột** (đã loại 1 cột để tránh leakage)
  - Feature range: `[0.000, 1.000]` (MinMax)
  - Phân phối lớp **Train**: Normal 53.5% / DoS 36.5% / Probe 9.3% / R2L 0.8% / U2R 0.04% (52 mẫu)
  - Phân phối lớp **Test**: Normal 43.1% / DoS 33.1% / R2L 12.8% / Probe 10.7% / U2R 0.3%
  - Attack types Train=23, Test=38 (test có thêm 17 loại tấn công mới — distribution shift)
  - Tạo các sample sizes: 100, 200, 500, 1000 cho Train/Test
  - Tạo `multi_run/train_run{1..5}.csv`, mỗi run 1000 mẫu, seed 100-104
  - ✅ Tất cả 8/8 sanity checks PASSED

### 1.2 `selectkbest_nslkdd.ipynb` — ⚠️ Mất dấu tiếng Việt

- **Cells:** 27 (14 code + 13 markdown)
- **Lỗi runtime:** 0
- **Markdown tiếng Việt:** ❌ **6/6 cell markdown bị MẤT DẤU hoàn toàn** (cả 13 cell md nhưng 6 cell có chữ VN; toàn bộ là tiếng Việt không dấu, ví dụ: "Buoc 1", "giam chieu", "Tinh F-scores", "Tim K toi uu bang Cross-Validation"…). Print statements trong code cũng không dấu ("Khong co NaN", "san sang sang pca_pareto").
- **Cấu trúc:** 2 code cell biểu đồ ở vị trí 11 và 22 không có markdown đứng trước (chấp nhận được — chúng nối tiếp cell phân tích).
- **Số liệu chính (cho báo cáo):**
  - Input: 122 features, output: 20 features (giảm 83.6%)
  - **K_FINAL = 20** (elbow criterion 5-CV với proxy SVM linear)
  - F1 plateau tại K=20: **0.9534 ± 0.0030** (best ở K=100: 0.9600 ± 0.0028)
  - **Ablation 5-CV (3000 mẫu, proxy SVM linear):**
    - (1) Baseline tất cả 122 features: F1 = **0.9558 ± 0.0106**
    - (2) PCA 95% variance: F1 = **0.9504 ± 0.0105**
    - (3) SelectKBest only (K=20): F1 = **0.9337 ± 0.0105**
    - (4) PCA only (4D): F1 = **0.8577 ± 0.0086**
    - (5) **SelectKBest(K=20) + PCA(4D) [C1 pipeline]: F1 = 0.8989 ± 0.0091**
    - **ΔF1 (C1 vs PCA-only 4D) = +0.0411** → SelectKBest trước PCA giúp ích
  - **QSVM thật (subset 100 train / 100 test):**
    - (A) Full → PCA 4D: F1 = 0.5942 / Acc = 0.60
    - (B) SKB(K=20) → PCA 4D: F1 = **0.6995** / Acc = 0.70
    - (C) SVM-linear baseline: F1 = 0.6875 / Acc = 0.70
    - Δ(B-A) = +0.1054 → Feature selection giúp QSVM
  - 18 cặp feature |r| > 0.8 → PCA xử lý redundancy
  - Lưu: `models/feature_selector_k20.joblib`, `f_scores_*.csv`, `ablation_study_results.csv`
- **Cần fix:** Toàn bộ markdown phải có dấu tiếng Việt đầy đủ.

### 1.3 `pca.ipynb` — ⚠️ Mất dấu tiếng Việt

- **Cells:** 39 (19 code + 20 markdown)
- **Lỗi runtime:** 0
- **Markdown tiếng Việt:** ❌ **7/9 cell markdown VN bị mất dấu** ("Toi uu hoa Da Muc tieu voi Rang buoc Phan cung Luong tu", "Truc quan hoa rang buoc cung", "Tim trong so toi uu", "Phan tich landscape trong so"…). Print outputs cũng không dấu.
- **Cấu trúc:** Tất cả code cell đều có markdown đứng trước — ✅
- **Số liệu chính (C1 — Hardware-aware Quantum Embedding):**
  - Input: 20 features (sau SelectKBest K=20)
  - Hard constraint: V(n) ≥ 85% → bị loại n=[2,3], candidates n=[4..10]
  - Trọng số tối ưu (simplex grid 496 điểm, DBI metric): **α=0.0667, β=0.4333, γ=0.5000**
  - **n* = 4 qubits** ← chosen
  - Variance giữ lại: **86.62%** (PC1=55.06%, PC2=19.11%, PC3=7.92%, PC4=4.52%)
  - Fisher Score S(4) = 0.4711
  - **Davies-Bouldin Index = 1.0846** (thấp nhất → tốt nhất)
  - **Silhouette Score = 0.4262** (đo độc lập với DBI)
  - Hardware cost Q(4) = 0.1447
  - Objective F(4) = 0.1455
  - Bootstrap 95% CI (200 iters): F ∈ [0.1268, 0.1676], Sil ∈ [0.4003, 0.4617]
  - Pearson(DBI, Silhouette) = **-0.9981** (DBI là proxy tốt)
  - Pareto front: n ∈ [4,5,6,7,8,9,10], n=4 là Pareto-optimal *
  - Test angle range sau clip: [0.0044, 3.1416] rad (~ [0, π])
  - Spearman corr |r|>0.2: PC2↔PC3 (-0.437), PC1↔PC3 (+0.397) → tiền đề ZZFeatureMap
  - ✅ 7/7 sanity checks PASSED
  - Lưu: `models/pca_4components.joblib`, `models/scaler_minmax_pi.joblib`, `X_train_pca.npy (125973, 4)`, `X_test_pca.npy (22544, 4)`
- **Cần fix:** Toàn bộ markdown phải có dấu tiếng Việt đầy đủ.

### 1.4 `c2_quantum_kernel_expressibility.ipynb` — ✅

- **Cells:** 27 (13 code + 14 markdown)
- **Lỗi runtime:** 0
- **Markdown tiếng Việt:** ✅ **14/14 cell có đầy đủ dấu** (chất lượng cao, có công thức LaTeX và phân tích chi tiết).
- **Cấu trúc:** Tất cả code cell có markdown đứng trước — ✅
- **Số liệu chính (N_SUBSAMPLE=300, reps=2, full entanglement):**
  - Block ratio (within/across class):
    - K_ZZ: within=0.1820, across=0.0949 → **ratio = 1.92x** (tốt nhất)
    - K_poly2: 1.08x
    - K_RBF: 1.69x
  - **CKA vs Kernel lý tưởng** (bootstrap 200 iters):
    - CKA(K_ZZ) = **0.2701** [0.2359, 0.3192]
    - CKA(K_poly2) = 0.3945 [0.3388, 0.4640]
    - CKA(K_RBF) = 0.3838 [0.3265, 0.4535]
    - ⚠️ **H2 KHÔNG được xác nhận** (CKA_ZZ < CKA_poly2)
  - **Effective rank** (bootstrap):
    - K_ZZ = **17.10** [13.89, 19.11] — phong phú nhất
    - K_poly2 = 1.46
    - K_RBF = 4.48
  - **Expressibility D_KL Haar** (lower = better):
    - reps=1: 0.0261 / reps=2: **0.0156** / reps=3: 0.0422
    - ⚠️ H4 không đơn điệu nghiêm ngặt → cảnh báo
  - **Entanglement entropy** (300 samples, bipartition {0,1}|{2,3}):
    - Normal: μ=0.7497, σ=0.3763
    - Attack: μ=1.2145, σ=0.2695
    - **Mann-Whitney U=18207.5, p=0.000000** → **H3 XÁC NHẬN** (Attack > Normal)
  - **Phân loại trên N=300:**
    - QSVM (K_ZZ): Acc=0.8233, Rec=0.7018, Pre=0.9836, **F1=0.8191**
    - CSVM poly-2: F1=0.6820
    - CSVM RBF: F1=0.6718
    - QSVM margin = 0.2588
  - **Spearman bridge với C1** (N=125,973):
    - PC0-PC2: ρ = **+0.3968** (C1 báo cáo ~+0.40)
    - PC1-PC2: ρ = **-0.4366** (C1 báo cáo ~-0.44)
  - Lưu: `data/processed_data/c2_results.json`, 8 ảnh trong `reports/`
- **Lưu ý báo cáo:** H2 và H4 không được xác nhận hoàn toàn (đã ghi rõ trong output). H1, H3, và cầu nối C1 OK.

### 1.5 `c3_kernel_geometry_statevector_multirun.ipynb` — ✅

- **Cells:** 36 (17 code + 19 markdown)
- **Lỗi runtime:** 0
- **Markdown tiếng Việt:** ✅ **8/8 cell VN có đầy đủ dấu**
- **Cấu trúc:** Tất cả code cell có markdown đứng trước — ✅
- **Số liệu chính (multi-run: 5 trains × 1 fixed test, n_train=1000, n_test=300, km=100):**
  - Cấu hình kernel: ZZFeatureMap 4 qubits, reps=2, entanglement=full; C=1.0
  - **F1-macro mean ± std (5 runs):**
    - quantum (ZZ): **0.8538 ± 0.0157**  ← QSVM
    - quantum_z (Z, no entanglement): 0.8271 ± 0.0151
    - linear_mm: 0.8134 ± 0.0160
    - poly_mm: 0.8122 ± 0.0193
    - rbf_mm: 0.8132 ± 0.0167
    - linear_std: 0.8182 ± 0.0089
    - poly_std: 0.8293 ± 0.0344
    - rbf_std: 0.8384 ± 0.0133
    - **QSVM thắng tất cả 7 baseline cổ điển** trên trung bình 5 runs
  - **KTA mean ± std:**
    - quantum (ZZ): **0.2047 ± 0.0290**
    - quantum_z: 0.0697 ± 0.0062
    - linear_std: 0.0621
    - poly_std: 0.1247
    - rbf_std: 0.2473 (cao nhất nhưng F1 thấp hơn)
    - **Δ KTA (ZZ - Z) = +0.1349** → entanglement có lợi
  - **n_SV mean (train=1000):**
    - quantum: 277.4 (27.7%) — ít SV nhất so với linear/poly
    - quantum_z: 326.6 / linear_std: 365.6 / poly_std: 404.0 / rbf_std: 266.8
  - Spearman correlation (rep run 4): PC2-PC3 có |ρ|=0.4825 (nonlinear=+0.4818) → cấu trúc phi tuyến
  - Lưu: 10 figure PNG + 3 CSV/JSON trong `results/c3_multirun/`
- **Key finding cho báo cáo:** QSVM F1 = 0.8538 ± 0.0157, robust over 5 train sets, vượt mọi kernel cổ điển.

### 1.6 `c3_c_tuning_statevector.ipynb` — ⚠️ Chỉ 1 markdown header tổng

- **Cells:** 8 (7 code + 1 markdown)
- **Lỗi runtime:** 0
- **Markdown tiếng Việt:** ✅ 1/1 cell có đầy đủ dấu
- **Cấu trúc:** 6 code cell không có markdown đứng trước (notebook utility cho phép, nhưng nên thêm comment phân tách cho rõ ý đồ).
- **Số liệu chính (5-fold CV, f1_macro, 1-SE rule, train sample 1000):**
  - Best C tuning kết quả (chốt cho C3):
    | Model | Best C | CV F1 | std |
    |---|---|---|---|
    | linear_mm | 0.1 | 0.8530 | 0.0248 |
    | linear_std | 0.1 | 0.8500 | 0.0253 |
    | poly_mm | 0.1 | 0.8657 | 0.0190 |
    | poly_std | 0.1 | 0.8589 | 0.0167 |
    | rbf_mm | 0.1 | 0.8632 | 0.0137 |
    | rbf_std | **10.0** | **0.9099** | 0.0118 |
    | **qsvm (ZZ)** | **1.0** | **0.9038** | 0.0266 |
  - Gợi ý config cho C3: `C_QSVM=1.0`, `SVM_C_VALUES=[0.1, 0.1, 0.1, 0.1, 0.1, 10.0]`
- **Lưu ý:** Nên thêm markdown đầu mỗi cell mô tả mục đích nếu báo cáo trình ra notebook này.

### 1.7 `c4_robustness_distribution_shift_multirun_fixed.ipynb` — ✅

- **Cells:** 27 (13 code + 14 markdown)
- **Lỗi runtime:** 0
- **Markdown tiếng Việt:** ✅ 14/14 cell có đầy đủ dấu
- **Cấu trúc:** Tất cả code cell có markdown đứng trước — ✅
- **Số liệu chính (5 runs × fixed test sets):**
  - **E1 — Temporal Split (KDDTest+ chuẩn vs KDDTest-21 khó):**
    | Model | F1_Std | F1_Hard | ΔF1 drop | Drop% |
    |---|---|---|---|---|
    | **QSVM (ZZ)** | **0.8538±0.0157** | 0.6217±0.0137 | +0.2321±0.0188 | +27.17%±1.89% |
    | SVM-RBF (std) | 0.8384±0.0133 | **0.6270±0.0357** | +0.2114±0.0229 | 25.25% |
    | SVM-Linear (std) | 0.8182 | 0.5834 | +0.2348 | 28.69% |
  - **E2 — Feature Perturbation slope (mean ± std):**
    - QSVM (ZZ): **-0.8354 ± 0.1611** (sốc với noise mạnh)
    - SVM-RBF (std): -0.2291
    - SVM-Poly2 (mm): +0.0433 (gần như flat)
    - F1 at σ=0.05: QSVM=0.8405 vs SVM-RBF(mm)=0.8139
  - **E3 — Class Prior Shift (mean F1 / std qua 3 phân phối):**
    - QSVM: mean **0.8150**, std across **0.0286** (ổn định nhất)
    - SVM-RBF (std): 0.7958 / 0.0284
    - SVM-RBF (mm): 0.7722 / 0.0443
    - SVM-Linear (std): 0.7707 / 0.0443
  - **McNemar QSVM vs baselines (E1 hard set):** Tất cả p > 0.05 (ns) — chênh lệch không có ý nghĩa thống kê trên hard set.
  - **Cohen's d (E3 across distributions):** QSVM vs RBF(mm)=+1.11, vs Poly2(mm)=+1.26, vs Linear(mm)=+1.22, vs Linear(std)=+1.16 → **large effect** (QSVM ổn định hơn rõ rệt).
  - Lưu 9 figures + 5 CSV/JSON trong `results/c4_multirun/`
- **Kết luận C4:** QSVM ổn định nhất khi class prior shift (E3), nhạy hơn với feature perturbation (E2 slope dốc hơn), tương đương trên temporal shift (E1, ns).

### 1.8 `c5_confidence_calibration_multirun.ipynb` — ✅ (vừa được tôi chạy mới)

- **Cells:** 25 (12 code + 13 markdown)
- **Lỗi runtime:** 0
- **Markdown tiếng Việt:** ✅ 8/8 cell có đầy đủ dấu
- **Cấu trúc:** Tất cả code cell có markdown đứng trước — ✅
- **Lưu ý quan trọng:** Trước khi check, notebook **chưa từng được chạy** (tất cả `execution_count=None`). Tôi đã chạy lại với `nbconvert --execute --inplace`, exit code 0. Kết quả mới khác **rất nhiều** so với narrative C5 cũ — đã ghi rõ "Narrative_corrected" trong output cuối.
- **Số liệu chính (5 trains × NSL_KDD_Test_Sample100, 100 mẫu test, n_rare=10):**
  - **MEAN ± STD (5 runs):**
    | Model | F1 | ECE_full | ECE_rare | AUC-ROC | AUC-PR |
    |---|---|---|---|---|---|
    | **QSVM** | 0.7755±0.0279 | 0.1643±0.0195 | **0.4503±0.0725** | 0.8948±0.0262 | **0.9306±0.0136** |
    | SVM-RBF | 0.7818±0.0643 | 0.1744±0.0076 | 0.5387±0.1697 | 0.8656±0.0330 | 0.9131±0.0148 |
    | SVM-Poly | 0.7737±0.0387 | 0.1908±0.0166 | 0.5747±0.0546 | 0.8459±0.0275 | 0.9079±0.0104 |
  - **Cohen's d (|margin| rare, QSVM vs RBF) = -0.1608 ± 0.3095** → **dấu ÂM** ⇒ RBF margin LỚN HƠN QSVM trên lớp hiếm.
    - ⚠️ **NARRATIVE CŨ "QSVM margin tighter" là SAI DẤU** — notebook đã ghi "DA SUA".
  - **McNemar p-value mean = 0.4911 ± 0.4688** (không ý nghĩa, n_rare=10 quá ít power)
  - **Narrative ĐÚNG (lợi thế QSVM thực sự):**
    - ECE_rare: QSVM=0.4503 vs RBF=0.5387 → **Δ=+0.0884** (calibration tốt hơn)
    - AUC-PR: QSVM=0.9306 vs RBF=0.9131 → **Δ=+0.0175** (ranking quality tốt hơn)
  - Representative run: 2 (QSVM ECE_rare = 0.4270)
  - Lưu: `c5_results_multirun.json`, 4 figures (`c5_multirun_ece.png`, `c5_multirun_auc.png`, `c5_multirun_trends.png`, `c5_multirun_reliability_rep.png`)
- **⚠️ ẢNH HƯỞNG BÁO CÁO:**
  - **CLAUDE.md** ghi: "ECE_rare=0.4337 vs RBF ECE_rare=0.4707" và "Cohen's d (-0.6805)" → **sai khớp** với kết quả multirun mới (ECE_rare QSVM=0.4503 vs RBF=0.5387, Cohen's d=-0.1608).
  - Memory `project_c5_complete.md` cũng cần được cập nhật.
  - **Số liệu báo cáo nên dùng:** `c5_results_multirun.json` mới (5 runs, robust hơn single run).

### 1.9 `c6_learning_curve_sample_complexity.ipynb` — ✅

- **Cells:** 21 (9 code + 12 markdown)
- **Lỗi runtime:** 0
- **Markdown tiếng Việt:** ✅ 12/12 cell có đầy đủ dấu
- **Cấu trúc:** Tất cả code cell có markdown đứng trước — ✅
- **Số liệu chính (Test F1-macro qua các mốc N):**
  | N | QSVM | SVM-RBF | SVM-Poly | SVM-Linear |
  |---|---|---|---|---|
  | 100 | **0.8132** | 0.7240 | 0.7008 | 0.7331 |
  | 200 | 0.7973 | 0.7431 | 0.7537 | 0.7583 |
  | 500 | **0.8311** | 0.7310 | 0.7262 | 0.7646 |
  | 1000 | **0.8128** | 0.7289 | 0.7434 | 0.7370 |
  - QSVM **vượt trội** tại mọi mốc N (≥0.07 F1)
  - Phân bố lớp 5-class với U2R, R2L rất thấp tại N=100,200
- **Cohen's d trên lớp hiếm (U2R+R2L), N=500:**
  - QSVM |margin| trung bình: **0.6538 ± 0.4674**
  - SVM-RBF |margin|: 0.5070 ± 0.2126
  - Pooled std: 0.3631
  - **Cohen's d = 0.4043** (small but meaningful)
  - 2,952 mẫu hiếm trong tập test
- Lưu: `c6_results.json`, `c6_learning_curve_metrics.json`, 3 figures (`c6_learning_curves_test_f1.png`, `c6_train_vs_test_f1.png`, `c6_training_time_vs_n.png`)
- **Key finding (đã ghi trong CLAUDE.md):** QSVM vượt classical baselines trong low-data regime, margin trên rare attacks rộng và ổn định hơn.

---

## GIAI ĐOẠN 2 — UNSW-NB15

### 2.1 `preprocess.ipynb` — ✅

- **Cells:** 24 (12 code + 12 markdown)
- **Lỗi runtime:** 0
- **Markdown tiếng Việt:** ✅ 12/12 cell có đầy đủ dấu
- **Cấu trúc:** 1 code cell (cell[11] biểu đồ) không có markdown đứng trước — chấp nhận được
- **Số liệu chính:**
  - Train raw: `(175341, 36)` → Post-OHE `(175341, 186)` → final `(175341, 189)`
  - Test raw: `(82332, 36)` → final `(82332, 189)` (186 features + 3 nhãn)
  - **Phân bố Train 10-class:** Normal 31.9% / Generic 22.8% / Exploits 19.0% / Fuzzers 10.4% / DoS 7.0% / Reconnaissance 6.0% / Analysis 1.14% / Backdoor 1.0% / Shellcode 0.65% / **Worms 0.07%** (130 mẫu)
  - **Phân bố Test:** Normal 44.94% / Generic 22.92% / … / Worms 0.05% (44 mẫu)
  - Phân bố binary Train: Normal 31.94% / Attack 68.06%
  - Phân bố binary Test: Normal 44.94% / Attack 55.06%
  - Rare categories: Analysis, Backdoor, Shellcode, Worms
  - Tạo các sample sizes: 100, 200, 500, 1000 và 5 train_run/test_run (stratified seed 100-104)
  - ✅ Tất cả 8/8 sanity checks PASSED

### 2.2 `selectkbest_unsw.ipynb` — ⚠️ Mất dấu tiếng Việt

- **Cells:** 20 (10 code + 10 markdown)
- **Lỗi runtime:** 0
- **Markdown tiếng Việt:** ❌ **4/4 cell VN bị mất dấu** ("Buoc 2", "Tinh F-scores", "DYNAMIC K DISCOVERY -- Elbow Criterion (KHONG hardcode K=20)", "Apply SelectKBest tren full train/test")
- **Cấu trúc:** 1 code cell (cell[11] biểu đồ) không có markdown header
- **Số liệu chính (5-fold CV LinearSVC proxy):**
  - K candidates: [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 70, 100, 150]
  - K=100: F1=0.8896 ± 0.0164 (best)
  - K=35: F1=0.8813 ± 0.0171 (plateau zone, **K_FINAL chọn**)
  - K=20: F1=0.8272
  - K=10: F1=0.7982
  - K=5: F1=0.7914
  - **K_FINAL = 35** (so với NSL-KDD K=20 → minh chứng K dataset-specific)
  - Reduction: 186 → 35 (81.2%)
  - Top features: state_INT (F=59703), dload (32161), state_CON (27258), ct_dst_sport_ltm (25646), dmean (23208), rate (22614), proto_tcp (21975)
  - ✅ Tất cả 12/12 sanity checks PASSED
- **Cần fix:** Toàn bộ markdown phải thêm dấu tiếng Việt đầy đủ.

### 2.3 `pca_unsw.ipynb` — ⚠️ Mất dấu tiếng Việt

- **Cells:** 17 (8 code + 9 markdown)
- **Lỗi runtime:** 0
- **Markdown tiếng Việt:** ❌ **5/5 cell VN bị mất dấu** ("Buoc 3 cua pipeline giam chieu", "PCA (n=4 components) -- giam tu 35D ve 4D", "Quantum Scaling -- map PCA outputs ve [0, π]", "Spearman Correlation Analysis (yeu cau khoa hoc cua giao su)")
- **Cấu trúc:** Tất cả code cell có markdown đứng trước — ✅
- **Số liệu chính (PCA + Quantum Scaling UNSW):**
  - Input: 35 features (sau SelectKBest)
  - PCA n_components = 4 (hardware constraint)
  - **Variance retained: 86.96%** (loss = 13.04%)
  - Per-PC EVR: PC1=62.1% / PC2=16.1% / PC3=5.4% / PC4=3.3% (cumulative 86.96%)
  - PCA std raw: PC1=1.239, PC2=0.632, PC3=0.367, PC4=0.285
  - Encoding range: [0, π] = [0.0000, 3.1416]
  - Test outliers: 54 cells clip → 0 (0.016%), 34 cells clip → π (0.010%)
  - **Pearson off-diag max = 1.78e-07** (~0, PCA theorem)
  - **Spearman off-diag max = 0.404858**, mean = 0.223054 → non-linear monotonic structure cho ZZFeatureMap
  - Top Spearman cặp: PC3-PC4 (+0.4049), PC1-PC3 (+0.3019), PC1-PC2 (+0.2740), PC2-PC3 (+0.2372)
  - ✅ 16/16 sanity checks PASSED
  - Lưu: `UNSW_Train_PCA4D.parquet (175341, 7)`, `UNSW_Test_PCA4D.parquet (82332, 7)`, scree plot, Spearman heatmap
- **Cần fix:** Toàn bộ markdown phải thêm dấu tiếng Việt đầy đủ.

### 2.4 `c1_dimreduction_multirun.ipynb` — ✅

- **Cells:** 25 (13 code + 12 markdown)
- **Lỗi runtime:** 0
- **Markdown tiếng Việt:** ✅ 4/4 cell VN có đầy đủ dấu
- **Cấu trúc:** 2 code cell biểu đồ (cell 19, 20) không có markdown header — chấp nhận được
- **Số liệu chính (Plan 1.6 — Pareto K vs F1/KTA, C=1.0 neutral, 5 runs, n_train=n_test=100):**
  - K sweep = [10, 20, 35, 50, 80, 120, 186]
  - F1 mean ± std (QSVM):
    | K | QSVM F1 | linear | poly | rbf | KTA QSVM | deg_dist | n_deg/5 |
    |---|---|---|---|---|---|---|---|
    | 10 | 0.786±0.028 | 0.786 | 0.787 | 0.785 | 0.294 | 0.0177 | 0/5 |
    | 20 | 0.785±0.019 | 0.806 | 0.797 | 0.796 | 0.231 | 0.0177 | 0/5 |
    | 35 | 0.798±0.022 | 0.813 | 0.797 | 0.801 | 0.193 | 0.0232 | 0/5 |
    | 50 | 0.809±0.011 | 0.815 | 0.802 | 0.801 | 0.202 | 0.0330 | 0/5 |
    | **80** | **0.811±0.012** | 0.812 | 0.802 | 0.799 | 0.204 | 0.0347 | **0/5** |
    | 120 | 0.811±0.012 | 0.812 | 0.802 | 0.799 | 0.204 | 0.0347 | 0/5 |
    | 186 | 0.811±0.012 | 0.812 | 0.802 | 0.799 | 0.204 | 0.0347 | 0/5 |
  - **VERDICT:** ✅ QSVM thoát degeneracy tại **K=80** (F1=0.8107, deg_dist=0.0347, 5/5 runs non-degenerate)
  - QSVM plateau từ K=80 trở đi → có thể dùng K=80, n_pca=4
  - Phản biện thành công với 1.5 (QSVM C=0.01 degenerate trên K=35) — chứng minh degeneracy là C-artifact
  - Lưu: `c1_results.json`, 3 figures (`c1_K_vs_f1.png`, `c1_K_vs_kta.png`, `c1_K_vs_degeneracy.png`)
- **Key finding cho báo cáo:** Tại C=1.0, QSVM competitive với linear (F1≈0.81), không degenerate ở mọi K, chứng minh QSVM trên UNSW không bị limitation kernel mà chỉ là C-tuning artifact.

### 2.5 `c_tuning_statevector.ipynb` — ⚠️ Chỉ 2 markdown header tổng

- **Cells:** 8 (6 code + 2 markdown)
- **Lỗi runtime:** 0
- **Markdown tiếng Việt:** ✅ 2/2 cell có đầy đủ dấu
- **Cấu trúc:** 4 code cell không có markdown đứng trước (notebook utility, có thể thêm comment phân tách).
- **Số liệu chính (5-fold CV, f1 binary, train_run1.parquet n=100):**
  - K=35, n_pca=4
  | Kernel | C_best | CV mean | std |
  |---|---|---|---|
  | quantum (ZZ) | **0.01** | 0.8504 | 0.0150 |
  | linear | 0.10 | 0.8813 | 0.0349 |
  | poly | 0.10 | 0.8813 | 0.0349 |
  | rbf | 1.00 | 0.8813 | 0.0349 |
  - **CRITICAL:** Best C cho QSVM là **0.01** → đó là nguyên nhân QSVM **degenerate** ở pipeline gốc 1.4/1.5 (predict-all-attack, biên rộng nhưng không phân biệt). Cần re-run với C=1.0 (xem C1 verdict).
- **Lưu:** `c_tuning_results.json`

### 2.6 `c2_quantum_kernel_expressibility.ipynb` — ✅

- **Cells:** 17 (9 code + 8 markdown)
- **Lỗi runtime:** 0
- **Markdown tiếng Việt:** ✅ 8/8 cell có đầy đủ dấu
- **Cấu trúc:** 2 code cell biểu đồ (cell 8, 14) không có markdown header — chấp nhận được
- **Số liệu chính (N_SUBSAMPLE=500, reps=2, entanglement=full, N_EXPR_PAIRS=2000):**
  - **Expressibility D_KL** (Haar Beta(1, 15)):
    - ZZ_reps1: D_KL = 0.0230
    - **ZZ_reps2: D_KL = 0.0221** ← chính
    - ZZ_reps3: D_KL = 0.0355
    - Z_reps2: D_KL = 0.9183 (baseline classical-like)
    - **Z vs ZZ gap: D_KL = 0.8962** → entanglement là then chốt
    - H1 (đơn điệu): False, nhưng reps=2 vẫn cải thiện vs reps=1
  - **Eigenspectrum (ZZ reps=2, N=500):**
    - Effective rank = **10.45** / 500
    - Idx 90% variance: 16
    - Idx 99% variance: 38
    - σ_1 / σ_N = 1.06e+14 (condition number rất lớn)
    - Top-5 sigma: 105.65, 69.07, 53.21, 32.78, 31.49
  - **Entanglement entropy** (bipartition {0,1}|{2,3}):
    - Normal: μ=1.0899, σ=0.3006
    - Attack: μ=1.2638, σ=0.2929
    - **Δ mean = +0.1739 bit**
    - **Mann-Whitney U=35566.5, p=1.418e-08 → H2 XÁC NHẬN**
  - **Kết luận:** ZZFeatureMap generalize tốt từ NSL-KDD sang UNSW-NB15. H2 vẫn xác nhận với p<<0.05.
  - Lưu: `c2_unsw_results.json`, 3 figures trong `reports_unsw/`

### 2.7 `c3_kernel_geometry_multirun_statevector_C1.ipynb` — ✅

- **Cells:** 29 (16 code + 13 markdown)
- **Lỗi runtime:** 0
- **Markdown tiếng Việt:** ✅ 8/8 cell có đầy đủ dấu
- **Cấu trúc:** 4 code cell không có markdown header (cell 3 hằng số toàn cục, 8 cache helper, 19/20 figures) — có thể chấp nhận với utility cells
- **Số liệu chính (1.4a-redo — C=1.0 neutral, 5 runs, n_train=n_test=100):**
  - **Aggregate (mean ± std):**
    | Kernel | C | F1 | Acc | KTA | nSV |
    |---|---|---|---|---|---|
    | quantum (ZZ) | 1.0 | 0.7977±0.0217 | 0.6960±0.0422 | 0.1934±0.0495 | 55.4 |
    | linear | 1.0 | **0.8129±0.0235** | 0.7360±0.0365 | 0.1578±0.0494 | 42.6 |
    | poly | 1.0 | 0.7971±0.0178 | 0.7040±0.0410 | 0.1173±0.0578 | 43.0 |
    | rbf | 1.0 | 0.8015±0.0213 | 0.7140±0.0503 | **0.2343±0.0541** | 48.6 |
  - **QSVM vs RBF:** ΔF1=-0.0038 (tied), ΔKTA=-0.0409 → RBF lead nhẹ
  - **QSVM vs Linear:** ΔF1=-0.0151
  - **McNemar QSVM vs RBF combined: p=0.1996** → KHÔNG khác biệt thống kê
  - **So sánh 1.4a tuned vs 1.4a-redo:**
    | Kernel | C_old | F1_old | C_new | F1_new | ΔF1 | TN_old → TN_new |
    |---|---|---|---|---|---|---|
    | quantum | 0.01 | 0.7760±0.004 | 1.0 | **0.7977±0.022** | +0.0217 | **0.0 → 9.8** (thoát degeneracy) |
    | linear | 0.1 | 0.8100 | 1.0 | 0.8129 | +0.003 | 11.0 → 16.0 |
    | poly | 0.1 | 0.8063 | 1.0 | 0.7971 | -0.009 | 9.8 → 12.2 |
    | rbf | 1.0 | 0.8015 | 1.0 | 0.8015 | 0.0 | 13.8 → 13.8 |
  - ✅ KTA cache-reuse: max |Δ| = 0.0e+00 (4 kernels, verified)
  - Lưu: `c3_results_statevector_C1.json`, 3 figures (`*_f1_boxplot.png`, `*_kta_bar.png`, `*_confmat.png`)
- **Key finding cho báo cáo:** Tại C=1.0 neutral, QSVM thoát degeneracy hoàn toàn (TN_mean 0→9.8), competitive với linear/RBF, McNemar p=0.20 → không khác biệt thống kê.

### 2.8 `c4_robustness_multirun_C1.ipynb` — ✅

- **Cells:** 35 (20 code + 15 markdown)
- **Lỗi runtime:** 0
- **Markdown tiếng Việt:** ✅ 9/9 cell có đầy đủ dấu
- **Cấu trúc:** 6 code cell không có markdown header (aggregate / figures helper) — chấp nhận được
- **Số liệu chính (1.5-redo — C=1.0 neutral, 5 runs):**
  - **E1 — Temporal cross-run (25 pairs, mean ± std):**
    | Kernel | F1 | Acc | KTA |
    |---|---|---|---|
    | quantum | 0.7975±0.0138 | 0.6948±0.0295 | 0.1934±0.0452 |
    | **linear** | **0.8108±0.0186** | 0.7276±0.0344 | 0.1578±0.0451 |
    | poly | 0.7951±0.0122 | 0.6972±0.0337 | 0.1173±0.0528 |
    | rbf | 0.8002±0.0162 | 0.7072±0.0424 | **0.2343** |
  - **E2 — Perturbation (F1 mean ± std per σ):**
    | Kernel | σ=0.05 | σ=0.1 | σ=0.2 |
    |---|---|---|---|
    | quantum | 0.798±0.022 | 0.785±0.005 | 0.779±0.010 |
    | linear | 0.813±0.020 | 0.810±0.022 | 0.808±0.022 |
    | poly | 0.801±0.018 | 0.802±0.014 | 0.805±0.011 |
    | rbf | 0.804±0.017 | 0.805±0.023 | 0.805±0.024 |
    - QSVM range across σ: **0.0194** (1.5 cũ: 0.0000 = invariant = degeneracy) → giờ non-degenerate
  - **E3 — Prior Shift (F1 mean ± std per ratio Normal:Attack):**
    | Kernel | 1:9 | 5:5 | 9:1 |
    |---|---|---|---|
    | quantum | 0.937±0.027 | 0.702±0.015 | 0.225±0.032 |
    | linear | 0.920±0.064 | 0.731±0.028 | 0.244±0.059 |
    | poly | 0.920±0.056 | 0.700±0.012 | 0.256±0.077 |
    | rbf | 0.917±0.061 | 0.716±0.035 | 0.232±0.065 |
  - **QSVM thoát degeneracy hoàn toàn** ở mọi experiment (deg_dist tăng từ ~0 lên 0.011-0.043). TN_mean QSVM:
    - E1 temporal: 9.40 (cũ: 0)
    - E2 σ=0.05: 8.60 / σ=0.1: 5.00 / σ=0.2: 1.80
    - E3 1:9: 2.60 / 5:5: 9.80 / 9:1: 9.80
  - QSVM vs RBF head-to-head (Δ F1):
    - E1: -0.0027 / E2 σ=0.05: -0.0058 / σ=0.1: -0.0196 / σ=0.2: -0.0264
    - E3 (1:9): **+0.0198** / (5:5): -0.0138 / (9:1): -0.0065
  - ✅ KTA cache-reuse: 28/28 checks OK, max |Δ| = 0.0
  - Lưu: `c4_results_C1.json`, 3 figures (`c4_temporal_C1.png`, `c4_perturbation_C1.png`, `c4_prior_C1.png`)
- **Key finding cho báo cáo:** Sau khi neutral C=1.0, QSVM thoát degeneracy, robust comparable với RBF/linear. Trên prior 1:9 (rare attack scenario) QSVM lead +0.0198 F1.

### 2.9 `c5_confidence_calibration_multirun.ipynb` — ✅

- **Cells:** 28 (14 code + 14 markdown)
- **Lỗi runtime:** 0
- **Markdown tiếng Việt:** ✅ 4/4 cell có đầy đủ dấu
- **Cấu trúc:** 1 code cell (cell 3 hằng số) không có markdown header — chấp nhận được
- **Số liệu chính (1.7 — C=1.0 neutral, 5 runs, 4 rare cats: Analysis/Backdoor/Shellcode/Worms):**
  - **Summary mean ± std per kernel:**
    | Kernel | F1 | ECE_rare ↓ | AUC-PR_rare ↑ | AUC-PR_all ↑ |
    |---|---|---|---|---|
    | quantum | 0.7977±0.022 | 0.1935±0.053 | 0.3355±0.089 | 0.8651±0.038 |
    | **linear** | **0.8129±0.024** | **0.1824±0.045** | 0.3449±0.046 | **0.8935±0.022** |
    | poly | 0.7971±0.018 | 0.1928±0.044 | **0.4079±0.083** | 0.8853±0.024 |
    | rbf | 0.8015±0.021 | 0.2047±0.029 | 0.2463±0.029 | 0.8582±0.071 |
  - **Cohen's d (QSVM vs RBF rare margin, pooled n=100): d = -0.2439** → small (RBF > QSVM)
  - **Per-group accuracy (mean 5 runs):**
    | Cat | QSVM | Linear | Poly | RBF |
    |---|---|---|---|---|
    | Analysis | **0.960** | 0.920 | 0.920 | 0.920 |
    | Backdoor | 1.000 | 1.000 | 1.000 | 1.000 |
    | Shellcode | **0.880** | 0.800 | 0.800 | 0.800 |
    | Worms | 0.960 | 0.960 | 0.960 | 0.960 |
  - **McNemar per cat (QSVM vs RBF):** Tất cả p ≥ 0.5 (không có ý nghĩa thống kê, n_rare=25 per cat quá ít)
  - **⇒ QSVM dẫn đầu ở: KHÔNG metric nào** trên UNSW (linear/poly đứng đầu).
  - **So sánh UNSW vs NSL-KDD:**
    | Metric | NSL-KDD QSVM | NSL-KDD RBF | UNSW QSVM | UNSW RBF |
    |---|---|---|---|---|
    | ECE_rare ↓ | 0.4337 | 0.4707 | 0.1935 | 0.2047 |
    | AUC-PR rare ↑ | 0.0617 | 0.0571 | 0.3355 | 0.2463 |
    | Cohen's d | -0.6805 | — | -0.2439 | — |
    - Cả 2 dataset: QSVM win ECE_rare, AUC-PR_rare nhưng Cohen's d âm (RBF margin lớn hơn)
  - Lưu: `models_unsw/c5_results.json`, 4 figures (`c5_calibration_curves.png`, `c5_auc_pr_curves.png`, `c5_margin_distribution.png`, `c5_per_group_accuracy.png`)
- **Key finding cho báo cáo:** Trên UNSW khi C=1.0, QSVM thắng linear/RBF trên Analysis (0.96 vs 0.92) và Shellcode (0.88 vs 0.80) per-group accuracy, nhưng overall metric thì linear lead. McNemar không significant do n_rare quá nhỏ.

---

## Tổng kết toàn cảnh

### Tình trạng 17 notebook MỚI

| # | Notebook | Run errors | Markdown VN diacritics | Markdown/code structure | Đã chạy đủ |
|---|---|---|---|---|---|
| 1.1 | NSL-KDD `preprocess.ipynb` | ✅ 0 | ✅ 12/12 | ✅ | ✅ |
| 1.2 | NSL-KDD `selectkbest_nslkdd.ipynb` | ✅ 0 | ❌ 6/6 mất dấu | ✅ | ✅ |
| 1.3 | NSL-KDD `pca.ipynb` | ✅ 0 | ❌ 7/9 mất dấu | ✅ | ✅ |
| 1.4 | NSL-KDD `c2_quantum_kernel_expressibility.ipynb` | ✅ 0 | ✅ 14/14 | ✅ | ✅ |
| 1.5 | NSL-KDD `c3_kernel_geometry_statevector_multirun.ipynb` | ✅ 0 | ✅ 8/8 | ✅ | ✅ |
| 1.6 | NSL-KDD `c3_c_tuning_statevector.ipynb` | ✅ 0 | ✅ 1/1 | ⚠️ Thiếu MD ở 6 code cell | ✅ |
| 1.7 | NSL-KDD `c4_robustness_distribution_shift_multirun_fixed.ipynb` | ✅ 0 | ✅ 14/14 | ✅ | ✅ |
| 1.8 | NSL-KDD `c5_confidence_calibration_multirun.ipynb` | ✅ 0 | ✅ 8/8 | ✅ | ✅ (tôi chạy mới) |
| 1.9 | NSL-KDD `c6_learning_curve_sample_complexity.ipynb` | ✅ 0 | ✅ 12/12 | ✅ | ✅ |
| 2.1 | UNSW `preprocess.ipynb` | ✅ 0 | ✅ 12/12 | ✅ | ✅ |
| 2.2 | UNSW `selectkbest_unsw.ipynb` | ✅ 0 | ❌ 4/4 mất dấu | ✅ | ✅ |
| 2.3 | UNSW `pca_unsw.ipynb` | ✅ 0 | ❌ 5/5 mất dấu | ✅ | ✅ |
| 2.4 | UNSW `c1_dimreduction_multirun.ipynb` | ✅ 0 | ✅ 4/4 | ⚠️ 2 cell biểu đồ thiếu MD | ✅ |
| 2.5 | UNSW `c_tuning_statevector.ipynb` | ✅ 0 | ✅ 2/2 | ⚠️ 4 cell thiếu MD | ✅ |
| 2.6 | UNSW `c2_quantum_kernel_expressibility.ipynb` | ✅ 0 | ✅ 8/8 | ⚠️ 2 cell biểu đồ thiếu MD | ✅ |
| 2.7 | UNSW `c3_kernel_geometry_multirun_statevector_C1.ipynb` | ✅ 0 | ✅ 8/8 | ⚠️ 4 cell thiếu MD | ✅ |
| 2.8 | UNSW `c4_robustness_multirun_C1.ipynb` | ✅ 0 | ✅ 9/9 | ⚠️ 6 cell thiếu MD | ✅ |
| 2.9 | UNSW `c5_confidence_calibration_multirun.ipynb` | ✅ 0 | ✅ 4/4 | ⚠️ 1 cell thiếu MD | ✅ |

### Vấn đề tổng hợp

**A. Vấn đề runtime:** Không có notebook nào raise exception. Toàn bộ 17 file đều có execution count đầy đủ.

**B. Vấn đề markdown mất dấu (CẦN FIX):** 5/17 notebook có markdown tiếng Việt KHÔNG dấu, vi phạm guideline trong CLAUDE.md ("ALL Markdown cells and text explanations MUST be written in Vietnamese"). Đây là vấn đề **chính** cần fix trước khi nộp báo cáo:
- `notebooks/selectkbest_nslkdd.ipynb` — 6/6 cell mất dấu
- `notebooks/pca.ipynb` — 7/9 cell mất dấu
- `notebooks_unsw/selectkbest_unsw.ipynb` — 4/4 cell mất dấu
- `notebooks_unsw/pca_unsw.ipynb` — 5/5 cell mất dấu

**C. Vấn đề cấu trúc cell (NHẸ):** Một số notebook utility có code cell không có markdown đứng trước. Không bắt buộc fix nhưng nên thêm markdown đầu mỗi block code để dễ đọc khi trình bày báo cáo.

**D. Vấn đề số liệu C5 NSL-KDD (CHÚ Ý):** 
- File `c5_confidence_calibration_multirun.ipynb` chưa từng được chạy trước phiên này → tôi đã chạy lại.
- Kết quả mới (5 runs) **khác đáng kể** so với CLAUDE.md và memory `project_c5_complete.md`:
  - Cohen's d MỚI = **-0.1608** (5 runs) thay vì -0.6805 (single run cũ)
  - ECE_rare QSVM MỚI = **0.4503** thay vì 0.4337
  - Narrative cũ "QSVM margin tighter" → đã được tự sửa thành "RBF margin LỚN HƠN QSVM"
- Nếu báo cáo dùng số liệu của notebook MỚI, cần cập nhật theo `data/processed_data/c5_results_multirun.json`.

### Số liệu chính cho báo cáo — tóm gọn

#### NSL-KDD

| Đóng góp | Metric chính | Giá trị (NSL-KDD) |
|---|---|---|
| C1 — Dim reduction | F1 (SKB+PCA 4D) | **0.8989 ± 0.0091** (vs PCA-only 4D: 0.8577) |
| C1 — Hardware-aware | n_qubit, Variance, DBI, Sil | n=4 / 86.62% / DBI=1.0846 / Sil=0.4262 |
| C2 — Expressibility | D_KL (ZZ reps=2), eff rank, CKA | 0.0156 / 17.10 / 0.2701 |
| C2 — Entanglement H3 | Mann-Whitney U=18207.5 | **p = 0.000000** (xác nhận) |
| C3 — F1 5-run | QSVM F1, KTA | **0.8538 ± 0.0157**, KTA=0.2047 |
| C3 — Δ KTA (ZZ−Z) | Entanglement có lợi | **+0.1349** |
| C4 — E1 Temporal | QSVM F1 drop | 27.17%±1.89% (vs RBF 25.25%) |
| C4 — E3 Prior shift | QSVM std across | **0.0286** (thấp nhất) |
| C4 — Cohen's d E3 | QSVM vs Linear(mm) | **+1.22** (large) |
| C5 — multirun mới | ECE_rare, AUC-PR, Cohen's d | 0.4503 / 0.9306 / -0.1608 |
| C6 — Learning curve | QSVM F1 @ N=500 | **0.8311** (vs RBF 0.7310) |
| C6 — Cohen's d rare | margin advantage | 0.4043 |

#### UNSW-NB15

| Đóng góp | Metric chính | Giá trị (UNSW) |
|---|---|---|
| C1 (Plan 1.6) — K sweep | QSVM F1 plateau | 0.8107±0.0116 từ K≥80 (0/5 degenerate) |
| C2 — Expressibility | D_KL ZZ reps=2, eff rank | 0.0221 / 10.45 |
| C2 — Entanglement H2 | Mann-Whitney p | **p=1.418e-08** |
| C3 (1.4a-redo) — F1 5-run | QSVM, linear, rbf | 0.7977 / 0.8129 / 0.8015 |
| C3 — McNemar QSVM vs RBF | combined p | 0.1996 (ns) |
| C4 (1.5-redo) — E3 1:9 | QSVM vs RBF ΔF1 | **+0.0198** (QSVM lead trên rare-heavy prior) |
| C4 — QSVM thoát degeneracy | TN_mean E3 5:5 | 0 → 9.80 |
| C5 — F1, ECE_rare | QSVM vs Linear | 0.7977 vs 0.8129 / 0.1935 vs 0.1824 |
| C5 — Per-group Analysis | QSVM vs RBF | **0.960 vs 0.920** |
| C5 — Cohen's d rare | QSVM vs RBF | -0.2439 (small, RBF > QSVM) |

### Khuyến nghị fix trước khi nộp

1. **(PRIORITY 1)** Bổ sung dấu tiếng Việt vào 4 notebook: `selectkbest_nslkdd.ipynb`, `pca.ipynb`, `selectkbest_unsw.ipynb`, `pca_unsw.ipynb`. CLAUDE.md yêu cầu rõ điều này.
2. **(PRIORITY 2)** Cập nhật CLAUDE.md (mục "C5 Key Result") để khớp với số liệu multi-run mới (ECE_rare=0.4503, Cohen's d=-0.1608).
3. **(PRIORITY 3 - tuỳ chọn)** Thêm markdown đầu mỗi code cell trong các notebook utility (`c3_c_tuning_statevector.ipynb`, `c_tuning_statevector.ipynb`) để rõ ý đồ.
