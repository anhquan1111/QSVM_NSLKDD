# Tổng kết đợt C4 + UNSW — gửi Quang Anh chốt

> Nhánh `revisionC4`, 2 commit. **Master không đụng vào.**
> M xem qua rồi cho ý kiến, chỗ nào không đồng ý thì nói, revert được hết.

---

# 1. T đã làm gì

| Phần | Nội dung | Số bản ghi |
|---|---|---:|
| **C4 NSL-KDD** | Viết lại hoàn toàn: 10 run, 7 model, tune đối xứng mỗi (N, run), 2 test set, 2 chế độ lấy mẫu, N tới 10.000 | 3.640 |
| **UNSW-NB15** | Làm lại từ đầu theo đúng chuẩn C2/C3/C4 | 1.680 |
| **C2** | Chạy lại với 2 fix reproducibility (phần t nói cần máy m — giờ làm được rồi) | — |
| Hạ tầng | `src/c4_pipeline.py`, `runners/run_c4.py`, `runners/analyze_c4.py`, `configs/c4_protocol.json` | — |
| Tài liệu | note C4, note UNSW, báo cáo bàn giao số, audit UNSW, nhật ký 22 phát hiện | — |

**Gate kiểm chứng trước khi tin bất cứ số nào**: pipeline của t phải tái tạo đúng số C2 của m
tại N=1000 → **khớp chính xác 7/7 model, 10/10 run**. Qua gate rồi mới chạy thí nghiệm mới.

---

# 2. Ba phát hiện làm đổi kết luận của bài

## 2.1 Claim rare-attack trong bản đã nộp là SAI

Câu *"At N=500 QSVM-ZZ leads by +6.7 points over SVM-RBF on the rare-attack subset, Cohen's d
of +0.68"* sai ba chỗ:

- `+6.7` thật ra là Δ so với **SVM-Linear** trên **toàn bộ 22.544 mẫu**, không phải vs RBF trên
  rare subset (vs RBF trên toàn tập là +10.0)
- **Không có file nào trong repo** chứa F1/recall trên rare subset ở N=500
- `d=+0.68` không tái tạo được — số thật của C6 là **+0.4043**; chỗ duy nhất có 0.68 là
  `c5_results.json` với dấu **ÂM** (−0.68048), từ thí nghiệm khác (train=99, 10 mẫu rare)

**Nặng hơn**: C5/C6 tính effect size trên `|margin|`. T đo signed margin trên rare subset —
**âm với mọi model** (−0.20 đến −0.98), tức mẫu rare trung bình nằm **sai phía biên**. Nên
`|margin|` lớn = **sai một cách tự tin hơn**, không phải tốt hơn.

Bằng chứng `|margin|` vô nghĩa: nó cho d = **+1.42** với RandomForest nhưng **−0.31** với
SVM-RBF — cùng model, hai kết luận ngược nhau, chỉ đổi đối chứng.

Số mới (N=500): F1 rare-subset của QSVM-ZZ = 0.577, hơn SVM-RBF **+0.024**, thua SVM-Linear
**−0.083**. Cohen's d trên signed margin gần như bằng 0 với mọi baseline (|d| ≤ 0.09).

## 2.2 CÓ crossover, nhưng NGƯỢC chiều claim cũ

Bài nói QSVM thắng ở vùng **ít** dữ liệu. Thực tế ngược lại:

| N | Δ (ZZ − XGB) | Holm p | Verdict |
|---:|---:|---:|---|
| 100 | −0.0812 | 0.0039 | classical |
| 1000 | −0.0289 | 0.0078 | classical |
| 2000 | −0.0129 | 0.2617 | inconclusive |
| **5000** | **+0.0100** | **0.0273** | **QSVM** |
| **10000** | **+0.0149** | **0.0078** | **QSVM** |

Cơ chế đo được: recall lớp hiếm của XGB/RF **đạt đỉnh ở N≈1000 rồi tụt** (0.28 → 0.20) vì hội
tụ về tiên nghiệm của train (chỉ 0.83% rare), còn của QSVM **tăng đơn điệu** (0.22 → 0.34).

Đây chính là cơ chế bài đã tự nêu ở Sec V-C (*"decision surface anchored to the geometry of the
embedded samples rather than to the empirical class frequency"*) — cơ chế **đúng**, chỉ là nằm
ở thí nghiệm khác và ở vùng **nhiều** dữ liệu.

## 2.3 Ablation ZZ vs Z phụ thuộc cơ sở biểu diễn

C2 cho ZZ > Z dưới representation đóng băng. Dưới giao thức **refit theo từng N** — chính là
giao thức bản nộp tự khai cho C4 (Sec III-F) — dấu **đảo ngược**.

Thí nghiệm phân rã, 10 run, cùng test 300, cùng C=3.0:

| Cấu hình | ZZ − Z | p |
|---|---:|---:|
| A. frozen selector+PCA+scaler (**= C2 của m**) | +0.0114 | 0.232 |
| B. frozen selector+PCA, **chỉ refit scaler** | **+0.0348** | 0.0039 |
| C. refit toàn bộ (**= C4**) | **−0.0190** | 0.0195 |

Thủ phạm không phải scaler mà là **fit lại SelectKBest + PCA trên N dòng**. Và bất ngờ: cơ sở
PCA fit lại gần như trùng khít (cosine PC1 = **0.9966**, trùng 90.5% feature) mà vẫn đủ lật dấu.

⇒ **Kết quả ΔKTA = +0.1378 của m vẫn đúng, nhưng CÓ ĐIỀU KIỆN**: chỉ giữ khi cơ sở PCA được
ước lượng từ toàn bộ 125.973 dòng train.

Và UNSW **tái lập độc lập** điều này: ZZ − Z âm ở N nhỏ, dương và significant từ N≥2000
(+0.045, p=0.002 ở N=10000) — mạnh gấp đôi NSL-KDD.

---

# 3. UNSW-NB15

## 3.1 Luật C1 chạy độc lập cho n\* = 6, không phải 4

`K*=35` (đúng tiêu chí elbow δ=0.01 của bài) → `V≥0.85` cho {4…10} → `KTA ≥ 0.95×0.1986`
(đạt tại n=6) cho **{6}** → `min Q` → **n\* = 6**. Vững **10/10 subset** ở ε=0.02 và 0.05.

Toàn bộ UNSW cũ đặt `n_pca_fixed = 4` — tức mượn thẳng con số của NSL-KDD.

> Đây là câu trả lời trực diện cho R3-1 (chê novelty): **C1 là thủ tục chuyển giao được, không
> phải hằng số gán tay.** Hai dataset độc lập qua cùng một luật cho hai cấu hình khác nhau.

## 3.2 Cái gì chuyển giao, cái gì không

| Phát hiện trên NSL-KDD | Chuyển sang UNSW? |
|---|---|
| Crossover vs tree ensembles | ❌ **Không** — classical thắng ở mọi N |
| Entanglement cần đủ dữ liệu | ✅ **Có**, mạnh gấp đôi |
| QSVM-ZZ thắng họ SVM ở N lớn | ✅ **Có** (từ N≥2000) |
| Rare-attack khó | ❌ **Không** — lớp hiếm UNSW dễ (recall 0.94–0.99 mọi model) |
| C1 là thủ tục | ✅ **Có** — nhưng cho n\*=6 |

## 3.3 UNSW-NB15 trùng lặp rất nặng — phải khai trong Limitations

| | Trùng lặp nội bộ | Test có bản sao trong train |
|---|---:|---:|
| UNSW-NB15 | train 47.3%, test 41.3% | **24.97%** |
| NSL-KDD | 0% | 2.71% |

Kiểm chứng trên **dữ liệu thô** (34 feature gốc): 25.33% → **thuộc tính của dataset**, không
phải lỗi tiền xử lý của m. Riêng lớp `Generic`: **40.000 hàng / 1.800 chữ ký duy nhất = 95.5%
trùng lặp**.

---

# 4. T có đụng vào C2 — đây là chính xác cái gì

## 4.1 Hai fix

| Fix | Lý do |
|---|---|
| `algorithm_globals.random_seed` vào đầu `noise_validation()` | `FidelityStatevectorKernel` **không có tham số seed nào**. Chạy 3 lần liên tiếp cùng máy cùng dữ liệu cho KTA 0.0437 / 0.0372 / 0.0299. Dòng `ideal_finite_shot` **chưa bao giờ tái tạo được**, kể cả trên máy m |
| `evaluate_in_blocks` cho phần noise | `kta_sample_size=200` sinh 19.900 cặp circuit trong **một** job Aer → máy 16 GB fail ở khâu **nạp circuit**. Chia khối 50×50: 200×200 trong 374s, RAM đỉnh 721 MB |

## 4.2 Kết quả sau khi chạy lại: `status: PASS`

**Kết quả lõi KHÔNG đổi một chữ số:**

| | m | t |
|---|---|---|
| ΔF1 (ZZ−Z) | +0.011360, CI [−0.005408, +0.028128], p=0.2324 | **giống hệt** |
| ΔKTA (ZZ−Z) | +0.137807, CI [+0.126738, +0.148876], p=0.001953 | **giống hệt** |

Bảng 10 run: **5/7 model trùng tuyệt đối 10/10**. Hai chỗ lệch:

| Model | m | t | Nguyên nhân |
|---|---:|---:|---|
| SVM_Poly2 | 0.832326 | 0.832657 | sklearn 1.7.2 (máy m) vs 1.8.0 (`pyproject` ghim) — **m chạy `uv sync` là hết** |
| XGBoost | 0.849301 | 0.850310 | phụ thuộc số thread của máy, không sửa được |

Noise: `ideal_finite_shot` đổi do fix seed; `realistic_noisy` đổi nhẹ do chia khối làm đổi chuỗi
shot-noise. Câu chuyện chính giữ nguyên: KTA của ZZ 0.1965 → 0.1490 dưới noise, `D_F` của ZZ
gấp **3.6 lần** của Z, khớp footprint 44 CX vs 0 CX.

---

# 5. Một chỗ trong C3 của m KHÔNG ROBUST — cần m biết

Ô `prior_shift / attack_70pct / XGBoost`:

| Bản | holm_p | Verdict |
|---|---:|---|
| Gốc (trước mọi sửa) | 0.0273 | classical-favorable |
| Máy m, `n_jobs=1` | **0.0391** | classical-favorable |
| Máy t, `n_jobs=1` | **0.0977** | **inconclusive** |

**Cùng code đã seed, hai máy, hai verdict ngược nhau.** 35/36 ô còn lại hai bên khớp hoàn toàn.

Đây là verdict **duy nhất** trong C3 nói "XGBoost thắng QSVM-ZZ có ý nghĩa thống kê". Dù ta in
số nào thì cũng phải báo cáo ô này là **borderline / không robust** trong bài.

Độ lệch XGBoost liên máy: ±0.01/run, **trung bình +0.0010** — nhỏ hơn một bậc so với độ rộng CI
của crossover (0.012–0.020), nên **không lật kết luận C4**.

---

# 6. Cần m chốt 5 điểm

1. **Hai fix trong C2** (`algorithm_globals`, `evaluate_in_blocks`) — m đồng ý giữ không? Nếu
   không thì revert được, số cũ vẫn nằm trong commit `abd6dad`.
2. **`uv sync`** về sklearn 1.8.0 trên máy m — để hết lệch `SVM_Poly2`.
3. **Note C2 và C3 của m cần cập nhật**: XGBoost mean 0.851625 → 0.850310; transpile cố định
   depth 59 / 44 CX; ô prior-70 XGB đổi thành borderline.
4. **Kết quả ΔKTA của C2 phải viết là CÓ ĐIỀU KIỆN** (mục 2.3) — m thấy cách diễn đạt đó ổn không?
5. **Fig 10 regime map**: t đã gom một bộ số chung `results/nslkdd/regime_map_rows.csv`
   (110 dòng, C2+C3+C4). Tổng kết: **21 ô QSVM / 21 ô classical / 68 ô inconclusive** — con số
   này tự nó đóng luôn cái AE/R1 chê overclaim. Ai vẽ hình?

---

# 7. Còn lại gì sau khi chốt

| # | Việc | Cần chạy không |
|---|---|---|
| 1 | Audit references: sửa [15] `116990F`→`116990B`, bỏ [26] Rahman, giữ ≤45 | không |
| 2 | Literature 2025–26 + QMI-2026 + Carducci + 2 arXiv của R3 | không |
| 3 | Novelty matrix | không |
| 4 | Hạ Proposition 1–4 thành Background, bỏ Proposition 3 | không |
| 5 | Vẽ lại Fig 5, Fig 9, Fig 10 + hình UNSW | có, nhẹ |
| 6 | Đóng gói supplementary + README repo public | không |
| 7 | Rebuttal point-by-point 33 item + bản highlight vàng | không |
| 8 | **Xin thầy file `.tex` nguồn của bản đã nộp** | 🚨 chặn khâu bản highlight |

---

# 8. Đọc thêm ở đâu

| Cần gì | File |
|---|---|
| Số để viết bài (từng bảng/hình: cũ → mới → câu chữ) | `docs/revision/04_BAN_GIAO_SO_LIEU.md` |
| Note C4 | `notebooks/nslkdd/note/C4/C4_results_reviewer_analysis_and_manuscript_revision.md` |
| Note UNSW | `notebooks/nslkdd/note/C4/UNSW_transfer_results_and_manuscript_revision.md` |
| Truy vết claim sai | `docs/revision/c4_claim_audit.md` |
| Audit UNSW | `docs/revision/03_UNSW_AUDIT.md` |
| Nhật ký đầy đủ 22 phát hiện | `docs/revision/02_PROGRESS.md` |
| Trạng thái 33 item reviewer | `docs/revision/00_STATUS_paper1.md` |
