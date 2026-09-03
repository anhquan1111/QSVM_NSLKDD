# Nhật ký tiến độ — Revision Paper 1 (phần Quan)

> Mỗi giai đoạn xong thì ghi vào đây: **đã làm gì · số liệu thật · phát hiện · vấn đề · bước tiếp theo**.
> Nguyên tắc: **chỉ ghi số tái tạo được**. Cái gì không kiểm chứng được thì ghi rõ là không kiểm chứng được.
>
> Kế hoạch: [01_PLAN_C4_UNSW.md](01_PLAN_C4_UNSW.md) · Bối cảnh: [00_STATUS_paper1.md](00_STATUS_paper1.md)

| Giai đoạn | Trạng thái | Ngày |
|---|---|---|
| **0 — Chuẩn bị** | ✅ **XONG** | 2026-09-01 |
| **1 — Hạ tầng C4 + gate** | ✅ **XONG — gate G2 PASS** | 2026-09-01 |
| **1B — Sửa + chạy lại C2/C3** | ✅ **XONG — C2 status PASS** | 2026-09-02 |
| **2 — Learning curve `matched`** | ✅ **XONG — 1400 bản ghi** | 2026-09-02 |
| **3 — Crossover (`natural`)** | ✅ **XONG — TÌM ĐƯỢC CROSSOVER** | 2026-09-02 |
| **4 — Rare-attack margin** | ✅ **XONG — chốt được số thay claim sai** | 2026-09-02 |
| **5 — Table IV vs VI + literature** | ✅ **XONG** | 2026-09-02 |
| **6 — Note C4 + regime map** | ✅ **XONG** | 2026-09-02 |
| **7 — UNSW audit** | ✅ **XONG — chốt phạm vi** | 2026-09-02 |
| **8 — UNSW pipeline** | ✅ **XONG** | 2026-09-02 |
| **9 — UNSW thí nghiệm (U3)** | ✅ **XONG — 1680 bản ghi** | 2026-09-02 |
| 10 — Đóng gói + rebuttal | ⬜ | |

---

# ✅ GIAI ĐOẠN 0 — Chuẩn bị (2026-09-01)

## S0.1 — Truy vết 5 claim C4 của bản đã nộp

**Sản phẩm**: [c4_claim_audit.md](c4_claim_audit.md)

### Kết quả kiểm chứng

| Claim | Phán quyết |
|---|---|
| Table VI (0.813 / 0.797 / 0.831 / 0.813) | ✅ **tái tạo khớp 100%** từ `c6_results.json` |
| Slope perturbation −0.835 vs −0.013 | ✅ **tái tạo khớp 100%** từ `c4_multirun/degradation_slope_summary.csv` |
| Table IV vs VI lệch nhau | ✅ **không mâu thuẫn** — khác test set (300 vs 22,544) |
| *"+6.7 points over SVM-RBF on the rare-attack subset"* | ❌ **SAI** |
| *"Cohen's d of +0.68"* | ❌ **KHÔNG TÁI TẠO ĐƯỢC** |

### 🔴 Phát hiện 1 — Câu "+6.7 points" sai ở ba chỗ cùng lúc

Câu trong bài: *"At N=500 QSVM-ZZ still leads by +6.7 points over SVM-RBF on the rare-attack subset."*

- `+6.7` thực chất là `0.0665` = Δ so với **SVM-Linear**, không phải SVM-RBF (so với RBF là **+10.0** điểm).
- `0.0665` tính trên **toàn bộ 22,544 mẫu**, không phải trên rare subset.
- **Không có bất kỳ file nào trong repo chứa F1 hay recall trên rare subset ở N=500.** Câu này không có số đứng sau.

### 🔴 Phát hiện 2 — `d = +0.68` không tái tạo được, và có dấu hiệu sai dấu

- Số thật của C6 tại N=500 (2,952 mẫu rare): **d = +0.4043**.
- Nguồn duy nhất trong repo có độ lớn 0.68 là `c5_results.json → cohens_d_margin_rare = **−0.68048**` — **ngược dấu**, và đến từ thí nghiệm khác (C5 calibration, train=99, test=99, **chỉ 10 mẫu rare**).
- Chính notebook C5 in ra: `d < 0 ⇒ RBF margin LỚN HƠN QSVM… Narrative cũ 'QSVM margin tighter' là SAI DẤU → ĐÃ SỬA`.
- C5 chạy 5 run cho mean **d = −0.161 ± 0.309** → hiệu ứng gần như bằng 0, hơi nghiêng về RBF.
- Giá trị `+0.6905` xuất hiện nếu dùng **Glass's Δ** (chia cho std của RBF) thay vì Cohen's d pooled — có thể đây là nguồn thật của con số 0.68.

### 🔴 Phát hiện 3 (nghiêm trọng nhất) — dùng `|margin|` thay vì signed margin

Cả C5 và C6 đều tính effect size trên **giá trị tuyệt đối** của decision function:

```python
qsvm_margins = np.abs(qsvm_500.decision_function(X_te_500[rare_mask]))
```

`|f(x)|` lớn chỉ nghĩa là model **tự tin**, không nghĩa là model **đúng**. Trên U2R/R2L — lớp mà cả hai model đều sai nhiều — `|margin|` lớn hơn hoàn toàn có thể là **sai một cách tự tin hơn**. Do đó ngay cả `d = +0.4043` cũng **không phải bằng chứng** rằng QSVM tốt hơn trên rare attack.

> **Hệ quả**: không thể trả lời R4-4 bằng cách "bổ sung bảng số cho claim cũ". Phải thừa nhận claim cũ sai, đổi sang **signed margin `y·f(x)`** làm đại lượng chính, và bắt buộc bổ sung **F1/recall trên rare subset** để câu "leads by X points" có số thật đứng sau.

---

## S0.2 — Đóng băng protocol C4

**Sản phẩm**: [`configs/c4_protocol.json`](../../configs/c4_protocol.json)

Bốn quyết định Q1–Q4 đã được mã hoá, cộng thêm 2 điều chỉnh phát sinh khi kiểm tra dữ liệu thật:

### Điều chỉnh 1 — Phân tầng theo nhãn 4 lớp, không phải 5 lớp

Kiểm tra `train_run1.csv`: `Normal 484 · DoS 331 · R2L 94 · Probe 85 · **U2R 6**`.

Nếu phân tầng theo `attack_category` (5 lớp), tại N=100 số mẫu U2R = `floor(6/1000×100)` = **0** → bảng rare-attack sẽ rỗng. Bản đã nộp (Sec. IV-B) cũng dùng nhãn 4 lớp `{Normal, DoS, Probe, R2L∪U2R}` chính vì lý do này. Đã đổi theo, kèm assert *"mọi subset ở mọi N phải có ≥ 1 mẫu rare"*.

### Điều chỉnh 2 — Kiến trúc tính kernel: cache statevector thay vì cache Gram

Đây là thay đổi làm chi phí sụp đổ. Ước tính ban đầu của tôi (~7 giờ) sai vì dựa trên `FidelityStatevectorKernel.evaluate()`, hàm này mô phỏng lại statevector mỗi lần gọi.

Cách đúng: mô phỏng statevector Ψ **một lần** (O(N)), rồi `Gram = |Ψ_a† Ψ_b|²` chỉ là matmul với inner dim 16.

**Số đo thực tế trên máy này:**

| Phép tính | Thời gian |
|---|---:|
| Mô phỏng statevector | 0.84 ms/mẫu → **toàn bộ 22,544 mẫu test ≈ 19 giây** |
| Gram 2000×2000 (matmul) | 0.046 s |
| Gram 10000×10000 | 1.7 s |
| `SVC.fit` precomputed N=10000 | 1.6 s |
| Gram 22544×10000 (1.8 GB) | 4.6 s |
| `predict` N=10000 | 1.2 s |

**Kiểm chứng đúng đắn**: Gram từ statevector cache vs `FidelityStatevectorKernel.evaluate()` → `max|Δ| = 4.4e-15`. Giống hệt về số học, không phải xấp xỉ.

⇒ **Mở rộng dải N từ `{100…5000}` lên `{100, 200, 500, 1000, 2000, 5000, 10000}`** — xa gấp 10 lần so với N=1000 của bản đã nộp, làm câu trả lời cho R1-7 (crossover) mạnh hơn hẳn. `N=20000` để dạng stretch tuỳ chọn.

### Chốt lại protocol

| | Quyết định |
|---|---|
| **Q1** Representation | primary `refit_per_N` · secondary `frozen_c1` |
| **Q2** Hyperparameter | tune đối xứng **cả 7 model tại mỗi (N, run)**, 5-fold, 1-SE; thêm arm `frozen_c2_hyperparameters` để đối chiếu |
| **Q3** Test set | báo cáo **cả hai** (fixed 300 + full 22,544) ở mọi N |
| **Q4** Dải N | `{100, 200, 500, 1000, 2000, 5000, 10000}`, 10 run, seed 100–109 |
| Rare-attack | signed margin (primary) · \|margin\| (secondary, có ghi hạn chế) · **bắt buộc thêm F1/recall rare** |
| Nesting | `D_100 ⊂ D_200 ⊂ … ⊂ D_10000`, neo tại **N=1000 = đúng `train_run{i}.csv` của C2** |
| Thống kê | paired Δ, CI 95% (t + bootstrap 10k), Wilcoxon, d_z, Holm — cùng schema với `c3_pairwise_statistics.csv` |

6 audit gate G1–G6 đã ghi trong protocol.

---

## S0.3 — Dọn repo

| Việc | Kết quả |
|---|---|
| `.claude/`, `.jupyter_tmp/` vào `.gitignore` | ✅ **đã có sẵn** — bạn Quang Anh đã làm |
| Thêm `results/nslkdd/c4_revision/cache/` và `results/unsw/c4_revision/cache/` vào `.gitignore` | ✅ đã thêm |
| `paper/paper1/manuscript.pdf` là bài khác (LEO satellite routing) | ⚠️ **đề xuất xoá — chờ duyệt, chưa đụng vào** |

### ⚠️ Cảnh báo về dung lượng repo

`results/nslkdd/c3_revision/cache/kernels/` đang **commit các file `.npy` Gram matrix**, mỗi file ~7.6 MB, tổng cộng vài trăm MB. Tổng repo tracked hiện có 583 file trong `results/`.

Nếu C4 làm theo cách đó, cache Gram tại N=10000 sẽ là ~1.8 GB **mỗi (run, kernel)** → khoảng 36 GB. Đây là lý do thứ hai để dùng statevector cache: file Ψ chỉ ~1.3 MB.

**Đề xuất** (chờ duyệt): thêm `results/nslkdd/c3_revision/cache/kernels/` vào `.gitignore` và `git rm --cached` — cần hỏi bạn Quang Anh trước vì đó là artifact của bạn ấy.

---

---

# ✅ GIAI ĐOẠN 1 — Hạ tầng C4 + gate kiểm chứng (2026-09-01)

**Sản phẩm**: [`src/c4_pipeline.py`](../../src/c4_pipeline.py) (~750 dòng)

## S1.1 — Module dùng chung

Thành phần: nạp dữ liệu · lấy mẫu lồng nhau · 2 chế độ representation · statevector cache ·
factory 7 model khớp C2 · tune 1-SE/best-mean · metric (gồm rare subset + margin) ·
thống kê sao y C3 (`mean_ci95`, `holm_adjust`, `paired_effect_summary`) · 5 audit gate.

### Kiểm chứng kiến trúc kernel
```
ZZ: max|Gram_statevector − FidelityStatevectorKernel| = 4.22e-15  → PASS
Z : max|Gram_statevector − FidelityStatevectorKernel| = 4.44e-15  → PASS
```

### 🔴 Phát hiện 4 — Tập train của C2 giàu lớp hiếm gấp ~12 lần

| Tập | Normal | DoS | Probe | R2L | U2R | **Rare (R2L+U2R)** |
|---|---:|---:|---:|---:|---:|---:|
| KDDTrain+ (125,973) | 53.5% | 36.5% | 9.25% | 0.79% | 0.04% | **0.83%** |
| `train_run{i}` (1,000) | 48.4% | 33.1% | 8.5% | 9.4% | 0.6% | **10.0%** |
| KDDTest+ (22,544) | 43.1% | 33.1% | 10.7% | 12.8% | 0.3% | **13.1%** |

`train_run{i}` — bộ dữ liệu nền của **C2, C3 và Table IV của bản đã nộp** — không phải mẫu
theo tỉ lệ tự nhiên của tập train. Nó được làm giàu lớp hiếm để tiến gần phân bố của tập
test. Đây là một **protocol fact chưa từng được ghi trong bài**, và nó giải thích một phần
R1-9 (*"F1 của classical thấp bất thường so với literature"*).

Hệ quả cho C4: nếu mở rộng N bằng cách rút thêm theo tỉ lệ tự nhiên, tỉ lệ rare tụt từ 10%
(N=1000) xuống 1.2% (N=10000) — đường learning curve sẽ trộn lẫn *"thêm dữ liệu"* với
*"đổi thành phần lớp"*, và mất nghĩa sample-complexity.

**Giải pháp: hai chế độ lấy mẫu, cả hai đều lồng nhau, trả lời hai câu hỏi khác nhau.**

| | `matched` | `natural` |
|---|---|---|
| Thành phần | giữ nguyên của `train_run{i}` (Rare 10%) | tỉ lệ tự nhiên KDDTrain+ (Rare 0.83%) |
| Dải N | 100 → **2000** | 100 → **20000** |
| Neo | N=1000 = đúng `train_run{i}` | không neo |
| Vai trò | sample-complexity đúng nghĩa; so trực tiếp với C2/C3 | crossover (R1-7) + bối cảnh triển khai thật |

### Vì sao `matched` dừng ở N=2000 — đo overlap giữa 10 run

Pool chỉ có 847 mẫu rare ngoài tuning set, nên giữ Rare=10% ở N lớn buộc các run phải
dùng chung mẫu rare:

| N | % mẫu rare dùng chung giữa 2 run bất kỳ |
|---:|---:|
| 1000 | 11% |
| 2000 | **24%** |
| 5000 | 59% |
| 8000 | **94%** |

Từ N=5000 trở lên, 10 run gần như trùng nhau ở phần rare → CI hẹp giả tạo. Chế độ
`natural` giữ overlap rare ≤ 10% tới tận N=10000 nên đi xa được.

**Kiểm chứng**: gate G4 (lồng nhau) và G5 (có mẫu rare) PASS cho **cả hai chế độ, mọi run,
mọi cặp N liên tiếp**; G3 (rời tuning set) = 0 chồng lấn ở mọi N.

### 🔴 Phát hiện 5 — KDDTrain+ và KDDTest+ có 610 dòng trùng nhau hoàn toàn

610/22,544 dòng test (**2.7%**) có feature + nhãn trùng khít một dòng trong train. Việc khử
trùng lặp của NSL-KDD làm *trong* từng split chứ không *giữa* hai split. Đây là thuộc tính
của bộ dữ liệu, mọi công trình dùng NSL-KDD đều chịu — **không phải lỗi lấy mẫu**. Gate G3
đã đổi thành: rời tuyệt đối với tuning set, còn với test thì ghi nhận và công bố.

---

## S1.2 + S1.3 — 🚦 GATE G2: tái tạo C2 tại N=1000 → **PASS**

Chạy chế độ `frozen_c1` + hyperparameter đóng băng của C2 + test 300 + 10 run, đối chiếu
từng ô với `results/nslkdd/c2_revision/c2_per_run.csv` (17 giây):

| Model | Khớp chính xác | max\|chênh\| | mean mới | mean C2 |
|---|---:|---:|---:|---:|
| **QSVM_ZZ** | **10/10** | **0.00e+00** | 0.846888 | 0.846888 |
| **QSVM_Z** | **10/10** | **0.00e+00** | 0.835528 | 0.835528 |
| SVM_Linear | 10/10 | 0.00e+00 | 0.813655 | 0.813655 |
| SVM_RBF | 10/10 | 0.00e+00 | 0.836186 | 0.836186 |
| RandomForest | 10/10 | 0.00e+00 | 0.844636 | 0.844636 |
| SVM_Poly2 | 9/10 | 3.31e-03 | 0.832657 | 0.832326 |
| XGBoost | 0/10 | 2.01e-02 | 0.851617 | 0.851625 |

Số hỗ trợ `n_SV` của quantum cũng trùng 18/20 ô, 2 ô lệch đúng 1 vector (tie ở biên, do
chênh lệch ~1e-15 giữa hai cách tính Gram) — không ảnh hưởng F1.

> **Kết luận: kiến trúc statevector cache tương đương tuyệt đối với `QSVC` của C2.**
> Hai model quantum trùng tới chữ số cuối trên cả 10 run.

### 🔴 Phát hiện 6 — XGBoost của C2 không tái tạo được trên máy khác

Cùng seed, cùng dữ liệu, cùng tham số, run 1:

| Cấu hình | F1 |
|---|---:|
| `n_jobs=-1, hist` (C2 dùng) | 0.836520 |
| `n_jobs=1, hist` | 0.853307 |
| `n_jobs=1, exact` | 0.863332 |
| C2 gốc (máy bạn Quang Anh) | 0.856627 |

Lặp lại trên **cùng** máy thì giống hệt → không phải lỗi seed, mà là `tree_method='hist'`
gộp histogram theo thứ tự thread nên kết quả **phụ thuộc số core của máy**.

Mức ảnh hưởng, 10 run:

| | mean F1 | max lệch từng run |
|---|---:|---:|
| `n_jobs=-1` | 0.851617 | 0.0201 |
| `n_jobs=1` | 0.850310 | 0.0165 |
| C2 gốc | 0.851625 | — |

**Kết luận trung thực**: trung bình gần như không đổi (0.8503–0.8516) nên **kết luận khoa học
không thay đổi** — XGBoost vẫn là baseline mạnh nhất, QSVM-ZZ vẫn xếp thứ hai. Nhưng **từng
run lệch tới 0.02**, tức reviewer chạy lại trên máy khác sẽ ra bảng khác. Mà XGBoost chính là
model dùng để nói *"QSVM không thắng được XGBoost"* — luận điểm đó đang tựa trên số không
tái tạo được. Đây là vấn đề R4-2.

**Đã chốt**: C4 dùng `n_jobs=1`. Cần bạn Quang Anh chạy lại C2/C3 với `n_jobs=1` để cả bài
đồng bộ và tái tạo được.

### 🟡 Phát hiện 7 — Một ô trong cache C2 không tái tạo được

`SVM_Poly2` run 3: C2 lưu **0.819928**, tính lại được **0.823237**. Đã quét toàn bộ lưới
`C ∈ {0.1…10}` × {StandardScaler, MinMax} × {degree 2, 3} — **không cấu hình nào cho ra
0.819928**. Cache `run_3_results.json` và `c2_per_run.csv` khớp nhau (export đúng), nên đây
là một entry cũ còn sót: `config_signature` chỉ băm `C2_CONFIG` chứ không băm hyperparameter
đã tune lẫn hash artifact C1, nên không tự invalid.

Ảnh hưởng: 1/70 ô, mean Poly2 lệch +0.00033 — **không đáng kể về khoa học**, nhưng nên chạy
lại run 3 với `FORCE_RERUN=True` cho sạch.

---

---

## 🔴 Phát hiện 8 — Một verdict của C3 là artifact của XGBoost phi tất định

Trước khi yêu cầu ai chạy lại, tôi đo xem lỗi ở Phát hiện 6 có thực sự đổi kết luận không.
Tận dụng việc C3 đã lưu `eval_subsets/`, tôi huấn luyện lại **chỉ XGBoost** với hai cấu hình
rồi tính lại thống kê paired trên đúng dữ liệu đánh giá của C3.

### Bước 0 — C3 có tái tạo được không?

| So sánh | max lệch |
|---|---:|
| XGB `n_jobs=-1` (đúng cấu hình C3) trên máy này vs số C3 lưu | **0.0295** |
| XGB `n_jobs=1` trên máy này vs số C3 lưu | 0.0278 |

⇒ Số XGBoost của C3 **không tái tạo được trên máy khác kể cả khi dùng đúng cấu hình gốc.**

### Bước 1 — Verdict có đổi không?

| Regime / điều kiện | C3 gốc | `n_jobs=-1` máy này | `n_jobs=1` (tất định) |
|---|---|---|---|
| attack_composition | inconclusive | inconclusive | inconclusive |
| prior 30% | inconclusive | inconclusive | inconclusive |
| prior 50% | classical (p=0.0488) | classical (p=0.0488) | **inconclusive** (p=0.0840) |
| prior 70% | classical (p=0.0137) | classical (p=0.0195) | classical (p=0.0488) |

### Bước 2 — Sau hiệu chỉnh Holm (family `strong_tabular`, RF raw_p = 0.1602)

| Nguồn XGBoost | raw_p | **holm_p** | Verdict công bố |
|---|---:|---:|---|
| C3 gốc (máy Quang Anh) | 0.0137 | **0.0274** | classical-favorable |
| `n_jobs=-1`, máy này | 0.0195 | 0.0390 | classical-favorable |
| `n_jobs=1` (tất định) | 0.0488 | **0.0976** | **INCONCLUSIVE** |

> ### Kết luận
> **Verdict duy nhất trong C3 nói *"XGBoost thắng QSVM-ZZ có ý nghĩa thống kê"* (prior 70%,
> Holm p = 0.0273) KHÔNG sống sót khi XGBoost được đặt về chế độ tất định.**
>
> Đây không phải chuyện `n_jobs=1` "đúng hơn" `n_jobs=-1`. Vấn đề là kết quả nằm sát ranh giới
> ý nghĩa đến mức **một artifact về số thread quyết định verdict**. Dù chọn cấu hình nào, so
> sánh này phải được báo cáo là **không robust**.
>
> Ảnh hưởng trực tiếp tới Fig 10 (regime map) và tới câu chuyện *"advantage phụ thuộc lớp
> comparator"* — luận điểm mà C3 đang dựa vào chính ô này.

Verdict `perturbation / all_sigma_slope` (XGB classical-favorable, d_z = −2.615) thì **rất
vững**, không bị ảnh hưởng bởi nhiễu cỡ 0.02.

**⇒ Việc chạy lại là cần thiết về khoa học, không phải thủ tục.**

---

---

# ✅ GIAI ĐOẠN 1B — Sửa và chạy lại C2 / C3 (2026-09-01)

**Sản phẩm bàn giao**: [thaydoi_C2_C3.md](thaydoi_C2_C3.md) — báo cáo thay đổi để gửi Quang Anh.

## Đã sửa

| # | File | Sửa gì |
|---|---|---|
| 1 | `C2_revision.ipynb` cell 11 | XGBoost tuning `n_jobs=-1` → `1` |
| 2 | `C2_revision.ipynb` cell 17 | XGBoost trong `make_baseline_models` `n_jobs=-1` → `1` |
| 3 | `C2_revision.ipynb` cell 31 | `transpile(...)` thêm `seed_transpiler=42` |
| 4 | `C3_revision.ipynb` cell 9 | XGBoost trong `make_models` `n_jobs=-1` → `1` |
| 5 | `pyproject.toml` | thêm `qiskit-aer==0.17.2` + `qiskit-ibm-runtime==0.49.0` |
| 6 | `src/c4_pipeline.py` | `make_tree_estimator` XGBoost `n_jobs=1` (lỗi của tôi, đã sửa) |

RandomForest giữ `n_jobs=-1` — đã kiểm chứng tất định.

## Kết quả C2

**Kết quả chính (ZZ vs Z) không đổi một chữ số**: ΔF1 = +0.011360, CI [−0.005408, 0.028128],
p = 0.2324, d_z = 0.4846; ΔKTA = +0.137807, p = 0.001953.

| Model | mean cũ | mean mới | Δ |
|---|---:|---:|---:|
| SVM_Poly2 | 0.832326 | **0.832657** | +0.000331 |
| XGBoost | 0.851625 | **0.850310** | −0.001315 |
| 5 model còn lại | — | — | **0** |

Thứ hạng không đổi: XGB > QSVM-ZZ (0.846888) > RF > RBF > Z > Poly2 > Linear.
Hyperparameter XGBoost chọn ra **y nguyên** → hợp đồng đóng băng cho C3/C4 không đổi.

Ô `SVM_Poly2` run 3 (Phát hiện 7) sau khi chạy lại ra **0.823237**, khớp tính toán độc lập của tôi.
Nghi nguyên nhân: cache cũ sinh dưới **scikit-learn 1.7.2** (joblib báo `InconsistentVersionWarning`)
trong khi `pyproject.toml` ghim **1.8.0**.

## Kết quả C3 — đúng như dự đoán ở Phát hiện 8

**36 ô so sánh, đúng 1 ô đổi verdict:**

| Regime | Baseline | mean_delta | holm_p | Verdict |
|---|---|---|---|---|
| prior_shift / attack_70pct | XGBoost | −0.0253 → −0.0229 | **0.0273 → 0.0977** | **classical-favorable → inconclusive** |

- 35 ô còn lại: verdict không đổi.
- Model không phải XGBoost: **0 ô đổi verdict**; 8/220 ô per-run của QSVM lệch ~0.001
  (đúng 1 mẫu/1000 bị lật — tie ở biên libsvm + đổi sklearn 1.7.2→1.8.0).
- `perturbation` vs XGBoost vẫn `classical-favorable` rất vững (holm_p 0.0039, d_z −2.8).

## 🚦 Gate G2 chạy lại sau khi sửa: **7/7 model khớp chính xác 10/10 run, max lệch 0.00e+00**

## ⚠️ Còn dở — phần noise của C2 không chạy được trên máy này

```
reason     : AlgorithmError('Sampler job failed!')
root_cause : MemoryError('bad allocation')
ERROR: Failed to load circuits: bad allocation
```

Máy: 16 GB RAM (~5 GB trống). `kta_sample_size=200` sinh **19,900 cặp circuit** nộp trong **một**
job Aer. Lỗi xảy ra ở khâu **nạp circuit**, trước khi mô phỏng — nên các cách sau đều vô dụng:

| Thử | Kết quả |
|---|---|
| `max_parallel_experiments=1` | vẫn fail sau 115s |
| `max_memory_mb=2048` | vẫn fail sau 117s |

Ngưỡng đo được:

| n | số cặp | kết quả |
|---:|---:|---|
| 25 | 300 | OK 2.5s |
| 50 | 1,225 | OK 12.5s |
| 100 | 4,950 | OK 99s |
| **200** | **19,900** | **MemoryError** |

Hệ quả: `c2_summary.json` báo `status: FAIL`, `realistic_noise_validation: false`;
`c2_noise_validation.csv` có dòng `realistic_noisy_simulator = SKIPPED`. Ba điều kiện
ideal/finite-shot vẫn chạy bình thường.

**Số noise cũ vẫn nằm nguyên trong git (commit `d397961`) — không mất gì.**

Đang test hướng **đánh giá theo khối** (chia 200×200 thành khối 50×50, mỗi job ≤1,225 cặp).
Nếu chạy được thì reviewer máy 16 GB cũng tái tạo được — đúng cái R4-2 đòi. Đánh đổi: chia khối
làm đổi chuỗi shot-noise nên **số sẽ lệch nhẹ** so với bản của Quang Anh.

---

---

# ✅ GIAI ĐOẠN 2 — Learning curve chế độ `matched` (2026-09-02)

**Sản phẩm**: `results/nslkdd/c4_revision/c4_per_run_matched_refit_per_N.csv` — **1400 bản ghi**
(2 arm × 5 mốc N × 10 run × 7 model × 2 test set). Thời gian chạy: 77 phút.

## Kết quả — mean Macro-F1, arm `tuned_per_N`, test full KDDTest+ (22.544 mẫu)

| N | QSVM-ZZ | QSVM-Z | SVM-Lin | SVM-Poly2 | SVM-RBF | RF | XGB |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | 0.7904 | **0.8129** | 0.7705 | 0.7872 | 0.7940 | 0.8099 | 0.8044 |
| 200 | 0.7985 | **0.8114** | 0.7696 | 0.7673 | 0.7865 | 0.7953 | 0.8066 |
| 500 | 0.8011 | 0.8127 | 0.7808 | 0.7961 | 0.8023 | **0.8161** | 0.8138 |
| 1000 | 0.8060 | **0.8274** | 0.7711 | 0.7893 | 0.8237 | 0.8250 | 0.8245 |
| 2000 | 0.8154 | **0.8464** | 0.7822 | 0.8229 | 0.8412 | 0.8289 | 0.8297 |

**QSVM-ZZ xếp cuối hoặc gần cuối ở mọi mốc N** theo giá trị trung bình. Chênh so với baseline
mạnh nhất: −0.022 / −0.013 / −0.015 / −0.022 / −0.031.

Điều này **mâu thuẫn trực diện** với Table VI của bản đã nộp (QSVM 0.813 vs baseline tốt nhất
0.733 ở N=100). Bản nộp chỉ có **1 seed** và chỉ so với **3 SVM**.

### ⚠️ Nhưng sau hiệu chỉnh Holm thì phải nói thận trọng hơn nhiều

Giá trị trung bình gợi ý "XGBoost thắng ở mọi N", **nhưng thống kê paired không ủng hộ điều đó**.
Bảng verdict (arm `tuned_per_N`, test full, Holm trong từng family như C3):

| N | vs QSVM_Z | vs RF | vs XGB | vs SVM-Lin | vs SVM-Poly2 | vs SVM-RBF |
|---:|---|---|---|---|---|---|
| 100 | inconc | inconc | inconc | inconc | inconc | inconc |
| 200 | inconc | inconc | inconc | inconc | inconc | inconc |
| 500 | inconc | inconc | inconc | inconc | inconc | inconc |
| 1000 | inconc | inconc | inconc | **QSVM** | inconc | inconc |
| 2000 | **classical** | inconc | inconc | **QSVM** | inconc | **classical** |

**Kết luận đúng cho dải N ≤ 2000:**

- QSVM-ZZ vs **XGBoost** và **RandomForest**: **inconclusive ở MỌI mốc N**. Không được viết
  "XGBoost thắng" — chênh lệch trung bình có tồn tại nhưng không vượt ngưỡng sau Holm.
- QSVM-ZZ **thắng SVM-Linear** ở N ≥ 1000 (d_z 1.42 và 1.46).
- QSVM-ZZ **thua QSVM-Z và SVM-RBF** ở N = 2000.

Đây là bức tranh nhất quán với C2/C3: QSVM-ZZ **cạnh tranh được**, không vượt trội, và không
thua đứt — trừ đối chứng không entangle.

---

## 🔴🔴 Phát hiện 9 — Ablation entanglement ĐẢO DẤU dưới giao thức re-fit

Đây là phát hiện nghiêm trọng nhất từ đầu tới giờ.

C2 kết luận **ZZ tốt hơn Z** (ΔF1 = +0.0114). Nhưng dưới giao thức `refit_per_N` — chính là
giao thức mà **bản đã nộp tự khai cho C4** (Sec. III-F: *"refit the entire pipeline including
SelectKBest and PCA on those N rows to enforce zero leakage"*) — kết quả đảo ngược:

| arm | test | N | ZZ − Z | CI 95% | p | verdict |
|---|---|---:|---:|---|---:|---|
| tuned_per_N | fixed_300 | 200 | −0.0293 | [−0.0549, −0.0038] | 0.027 | **classical** |
| tuned_per_N | fixed_300 | 1000 | −0.0157 | [−0.0301, −0.0012] | 0.037 | **classical** |
| tuned_per_N | fixed_300 | 2000 | −0.0201 | [−0.0354, −0.0049] | 0.037 | **classical** |
| tuned_per_N | full | 2000 | −0.0310 | [−0.0453, −0.0168] | 0.002 | **classical** |
| frozen_c2 | full | 2000 | −0.0300 | [−0.0400, −0.0200] | 0.002 | **classical** |

Dấu âm ở **cả 20 tổ hợp** (2 arm × 2 test × 5 N), không có ngoại lệ.

### Tách nguyên nhân — thí nghiệm phân rã 3 cấu hình, 10 run, test 300, C=3.0

| Cấu hình | ZZ − Z | CI 95% | p | verdict |
|---|---:|---|---:|---|
| **A.** frozen selector + PCA + scaler (**= C2**) | +0.0114 | [−0.0054, +0.0281] | 0.232 | inconclusive |
| **B.** frozen selector + PCA, **chỉ refit scaler** | **+0.0348** | [+0.0202, +0.0493] | 0.0039 | **QSVM-favorable** |
| **C.** refit toàn bộ (**= C4**) | **−0.0190** | [−0.0346, −0.0033] | 0.0195 | **classical-favorable** |

⇒ Thủ phạm **không phải scaler** (B còn làm ZZ tốt hơn), mà là **fit lại SelectKBest + PCA
trên N dòng**.

### Cơ chế — và đây là chỗ bất ngờ

Cơ sở PCA fit lại gần như **trùng khít** với cơ sở của C1:

| N | Trùng feature với C1 | \|cos\| trục PC1 vs C1 | Ổn định trục giữa các run |
|---:|---:|---:|---:|
| 100 | 82.5% | 0.9829 | 0.9759 |
| 1000 | 90.5% | 0.9966 | 0.9967 |
| 2000 | 90.0% | 0.9977 | 0.9987 |

Chỉ lệch ~10% feature và cosine 0.997 — vậy mà **đủ để lật dấu ablation**.

> **Kết luận: lợi thế của ZZ cực kỳ nhạy với thay đổi nhỏ của cơ sở biểu diễn.**
>
> Điều này ăn khớp với chính phát hiện của C3: dưới nhiễu đặc trưng, QSVM-ZZ tụt dốc nhanh
> hơn mọi baseline (slope −0.835 vs −0.013; \|d_z\| 2.6–4.8). Cùng một cơ chế: ZZ mã hoá
> **tích cặp** toạ độ nên phụ thuộc hệ trục, còn Z chỉ dùng từng toạ độ riêng lẻ nên không.

### Ý nghĩa cho bài báo

Kết quả ΔKTA = +0.1378 (p = 0.002) của C2 **vẫn đúng** — nhưng nó **có điều kiện**: chỉ giữ
khi cơ sở PCA được ước lượng từ toàn bộ tập train 125.973 dòng. Khi ước lượng từ đúng N mẫu
có nhãn dùng để train (zero-leakage nghiêm ngặt), lợi thế biến mất và đảo chiều.

Đây chính xác là mối lo tôi nêu ở quyết định **Q1** ngay từ đầu. Giờ nó đã được định lượng.

**Đây không phải tin xấu cho bài** nếu viết đúng: nó biến một claim yếu (*"entanglement giúp,
+0.011 không significant"*) thành một **phát biểu regime có điều kiện và kiểm chứng được** —
đúng tinh thần "regime-specific benchmark" mà cả 4 reviewer đều muốn.

⚠️ **Cần kiểm chứng thêm**: ở N lớn cơ sở PCA được ước lượng tốt hơn, ZZ có phục hồi không?
Chế độ `natural` chạy tới N=10000 (Giai đoạn 3) sẽ trả lời.

---

---

# ✅ GIAI ĐOẠN 3 — Crossover, chế độ `natural` (2026-09-02)

**Sản phẩm**: `c4_per_run_natural_refit_per_N.csv` (**1960 bản ghi**),
`c4_pairwise_statistics_natural.csv`. N ∈ {100 … 10000}, 10 run, 7 model, 2 test set, 2 arm.

## 🟢🟢 Phát hiện 10 — CÓ crossover, và nó NGƯỢC chiều với claim của bản đã nộp

Bản nộp: *"QSVM-ZZ dominates every classical baseline at every N"*, mạnh nhất ở vùng ít dữ liệu.
R1 hỏi thẳng: *"có crossover point nào không?"*

**Câu trả lời: có — ở N ≈ 2000–5000 — nhưng theo chiều ngược lại.**

### QSVM-ZZ vs XGBoost (test full 22.544, Holm)

| N | Δ (ZZ − XGB) | CI 95% | holm_p | d_z | Verdict |
|---:|---:|---|---:|---:|---|
| 100 | −0.0812 | [−0.1232, −0.0393] | 0.0039 | −1.39 | **classical** |
| 200 | −0.0641 | [−0.0983, −0.0300] | 0.0039 | −1.34 | **classical** |
| 500 | −0.0293 | [−0.0535, −0.0052] | 0.0273 | −0.87 | **classical** |
| 1000 | −0.0289 | [−0.0405, −0.0174] | 0.0078 | −1.80 | **classical** |
| 2000 | −0.0129 | [−0.0296, +0.0038] | 0.2617 | −0.55 | inconclusive |
| **5000** | **+0.0100** | [+0.0041, +0.0158] | **0.0273** | +1.22 | **QSVM** |
| **10000** | **+0.0149** | [+0.0050, +0.0249] | **0.0078** | +1.07 | **QSVM** |

RandomForest cho đúng một hình dạng như vậy: classical-favorable ở N ≤ 1000, **QSVM-favorable
ở N = 10000** (+0.0127, holm_p = 0.0078).

### Ablation ZZ vs Z cũng lật theo N — khớp giả thuyết ở Phát hiện 9

| N | ZZ − Z | p | Verdict |
|---:|---:|---:|---|
| 100 | −0.0624 | 0.0059 | **classical** |
| 500 | −0.0129 | 0.2754 | inconclusive |
| 1000 | +0.0051 | 0.7695 | inconclusive |
| **5000** | **+0.0224** | **0.0059** | **QSVM** |
| 10000 | +0.0068 | 0.5566 | inconclusive |

⇒ Đúng như Phát hiện 9 dự đoán: **entanglement chỉ có lợi khi cơ sở biểu diễn được ước lượng
đủ tốt.** Ở N nhỏ, PCA ước lượng từ ít mẫu → ZZ thua cả đối chứng không entangle. Ở N lớn,
cơ sở ổn định → ZZ vượt lên.

## Cơ chế — đã kiểm chứng bằng số, không phải suy đoán

**Recall trên rare subset (U2R ∪ R2L, 2952 mẫu test):**

| N | QSVM-ZZ | XGBoost | RandomForest | SVM-RBF |
|---:|---:|---:|---:|---:|
| 100 | 0.2189 | 0.1674 | 0.1529 | 0.1357 |
| 1000 | 0.3264 | 0.2783 | 0.2468 | 0.2547 |
| 2000 | 0.3275 | 0.2544 | 0.2360 | 0.4401 |
| 5000 | **0.3421** | 0.2119 ↓ | 0.2058 ↓ | 0.4383 |
| 10000 | **0.3400** | 0.2009 ↓ | 0.1982 ↓ | 0.4170 |

**Recall rare của XGBoost và RandomForest ĐẠT ĐỈNH ở N ≈ 1000 rồi TỤT** (0.28 → 0.20), trong
khi của QSVM-ZZ **tăng đơn điệu** (0.22 → 0.34).

Lý do: ở chế độ `natural`, tập train chỉ có 0.83% rare — ngay cả N=10000 cũng chỉ có **83 mẫu
rare**, trong khi tập test có **13.1%** rare. Càng nhiều dữ liệu, cây tăng cường càng hội tụ về
tiên nghiệm của tập train ("lớp hiếm không đáng kể") và ngừng dự đoán chúng. Kernel lượng tử
thì neo vào **hình học của mẫu đã nhúng** chứ không neo vào tần suất lớp thực nghiệm, nên
tiếp tục cải thiện.

> Đây **chính xác là cơ chế mà bản đã nộp tự nêu** ở Sec. V-C: *"the quantum kernel's decision
> surface is anchored to the geometry of the embedded samples rather than to the empirical class
> frequency"*. Cơ chế đó **đúng** — chỉ là nó thể hiện ở một thí nghiệm khác với thí nghiệm mà
> bài dùng để chứng minh nó, và ở **vùng nhiều dữ liệu** chứ không phải ít dữ liệu.

## Đối chiếu hai chế độ lấy mẫu

| | `matched` (rare 10%) | `natural` (rare 0.83%) |
|---|---|---|
| ZZ vs XGBoost | **inconclusive ở mọi N ≤ 2000** | classical ở N ≤ 1000 · **QSVM ở N ≥ 5000** |
| ZZ vs RF | inconclusive ở mọi N | classical ở N ≤ 1000 · **QSVM ở N = 10000** |
| ZZ vs SVM-Linear | QSVM ở N ≥ 1000 | QSVM ở N ≥ 1000 |
| Crossover | không quan sát được trong dải đã thử | **có, tại N ≈ 2000–5000** |

Khi lớp hiếm được làm giàu nhân tạo lên 10% (đúng như `train_run{i}` của C2/C3), lợi thế của
tree ensemble biến mất và mọi thứ hoà. Khi giữ tiên nghiệm tự nhiên, crossover hiện ra rõ.

## Hệ quả cho bài báo

Claim *"low-data advantage"* của C4 **phải bỏ** — bằng chứng ngược lại. Thay bằng một phát biểu
mạnh hơn và trả lời trực diện R1-7:

> Under the natural class prior, the crossover between QSVM-ZZ and strong tabular baselines
> occurs at N ≈ 2000–5000: classical ensembles are significantly better below it, QSVM-ZZ
> significantly better above it. The mechanism is measurable — tree ensembles' rare-class recall
> peaks near N = 1000 and then declines as they converge to the training prior, whereas the
> quantum kernel's rare-class recall increases monotonically.

Đây là một đóng góp **mạnh hơn** claim cũ, vì nó có crossover định lượng được, có cơ chế kiểm
chứng được, và ăn khớp với đóng góp prior-shift của C3.

---

---

# ✅ GIAI ĐOẠN 4 — Rare-attack margin (2026-09-02)

**Sản phẩm**: `results/nslkdd/c4_revision/c4_rare_attack.csv` — 84 hàng, 2 regime × 7 mốc N ×
7 model, gồm `f1_rare`, `recall_rare`, `precision_rare`, signed margin, |margin|, Cohen's d
theo cả hai định nghĩa, CI, Wilcoxon, verdict.

## 🔴 Phát hiện 11 — Signed margin trên rare subset là ÂM với MỌI model, MỌI N

| N | QSVM-ZZ | QSVM-Z | RF | XGB | SVM-RBF | SVM-Lin |
|---:|---:|---:|---:|---:|---:|---:|
| 100 | −0.3233 | −0.3870 | −0.2219 | −0.2543 | −0.5952 | −0.8021 |
| 1000 | −0.3919 | −0.4994 | −0.2032 | −0.2054 | −0.4584 | −0.9094 |
| 10000 | −0.5050 | −0.4855 | −0.2491 | −0.2778 | −0.3482 | −0.9779 |

Mẫu rare trung bình **nằm SAI phía biên quyết định** với tất cả model.

⇒ Đây là bằng chứng dứt điểm cho Phát hiện 3: `|margin|` lớn hơn nghĩa là **sai một cách tự
tin hơn**, không phải "biên an toàn hơn". Toàn bộ phân tích margin cũ của C5/C6 do đó **không
diễn giải được**.

## Số thật thay cho claim `+6.7 / d = +0.68`

Tại **N=500**, chế độ `matched`, test full — đúng điểm mà bản nộp đưa claim:

| So với | d trên **\|margin\|** (cách cũ) | d trên **signed margin** (cách đúng) | Δ F1_rare |
|---|---:|---:|---:|
| SVM-RBF | **−0.3074** | +0.0831 | **+0.0235** |
| SVM-Linear | −0.2329 | −0.0771 | −0.0828 |
| XGBoost | **+1.1638** | +0.0297 | +0.1032 |
| RandomForest | **+1.4222** | −0.0175 | +0.0944 |
| QSVM-Z | −0.2753 | −0.0666 | −0.0115 |

Ba điều rút ra:

1. **`|margin|` cho kết quả vô nghĩa**: d = **+1.42** với RandomForest nhưng **−0.31** với
   SVM-RBF. Cùng một model, hai kết luận trái ngược, chỉ vì đổi đối chứng.
2. **Signed margin cho hiệu ứng gần như bằng 0** với mọi baseline (|d| ≤ 0.083).
3. **Con số F1 thật trên rare subset lần đầu tiên có**: so với SVM-RBF là **+0.0235
   (2.35 điểm)**, không phải 6.7 điểm. Và so với SVM-Linear thì QSVM-ZZ **thua 0.083**.

### Câu thay thế đề xuất cho bài

> At N = 500, QSVM-ZZ attains a rare-subset (U2R ∪ R2L, 2,952 samples) macro-F1 of 0.577,
> which is +0.024 over SVM-RBF, +0.103 over XGBoost and +0.094 over Random Forest, but −0.083
> below SVM-Linear. Cohen's d computed on **signed** decision margins is negligible against
> every baseline (|d| ≤ 0.09). We note that the mean signed margin on the rare subset is
> negative for all evaluated models, so effect sizes computed on absolute margins — as in the
> original submission — are not interpretable.

## Rare-attack cũng cho thấy crossover (regime `natural`)

F1 trên rare subset:

| N | QSVM-ZZ | XGBoost | RandomForest | SVM-RBF |
|---:|---:|---:|---:|---:|
| 100 | 0.3334 | 0.2751 | 0.2550 | 0.2100 |
| 1000 | 0.4856 | 0.4272 | 0.3875 | 0.3815 |
| 5000 | **0.5093** | 0.3493 ↓ | 0.3409 ↓ | **0.6058** |
| 10000 | **0.5069** | 0.3342 ↓ | 0.3306 ↓ | 0.5846 |

Verdict (Holm): QSVM-favorable vs **RandomForest** từ N≥1000, vs **XGBoost** từ N≥2000, vs
**SVM-Linear** ở mọi N.

⚠️ **Nhưng phải nói rõ**: `SVM-RBF` mới là model tốt nhất trên rare subset ở vùng N lớn
(0.6058 tại N=5000), và **classical-favorable vs QSVM-ZZ** tại N = 500, 2000, 5000. Không được
viết "QSVM tốt nhất trên rare attack".

---

---

# 📌 GIAI ĐOẠN 1C — Hoà bản của Quang Anh + fix seed (2026-09-02)

## Đã hoà git

Quang Anh push `0364c92 "Edit C2, C3 for reproducibility"` (merge `abd6dad`). Tôi **bỏ bản
C2/C3 của mình**, merge fast-forward, không conflict. Toàn bộ phần C4 giữ nguyên.

Bản của bạn ấy có `n_jobs=1` (C2 cell 11+17, C3 cell 9) và `seed_transpiler=42` (cell 30+31).
Transpile giờ **cả hai máy đều ra depth 59 / 44 CX** — `seed_transpiler` đã ăn.

## 🔴 Phát hiện 12 — `n_jobs=1` là CẦN nhưng CHƯA ĐỦ cho XGBoost

Đối chiếu hai máy, cả hai `n_jobs=1`, cùng seed, cùng dữ liệu, cùng tham số:

| Model | Trùng chính xác | max lệch |
|---|---:|---:|
| QSVM_ZZ, QSVM_Z, SVM_Linear, SVM_RBF, RandomForest | **10/10** | 0.00e+00 |
| SVM_Poly2 | 9/10 | 3.3e-03 (do sklearn 1.7.2 vs 1.8.0) |
| **XGBoost** | **1/10** | **1.0e-02** |

Nguồn phi tất định còn lại nằm **trong chính XGBoost** (nhiều khả năng là binning của
`tree_method='hist'` phụ thuộc CPU), không phải số thread.

### Bằng chứng dứt điểm về ô `prior_shift / attack_70pct / XGBoost`

| Bản | mean_delta | **holm_p** | Verdict |
|---|---:|---:|---|
| Gốc (trước mọi sửa) | −0.0253 | 0.0273 | classical-favorable |
| **Quang Anh** (n_jobs=1, máy bạn ấy) | −0.0242 | **0.0391** | **classical-favorable** |
| **Tôi** (n_jobs=1, máy này) | −0.0229 | **0.0977** | **inconclusive** |

**Cùng một code đã seed, hai máy, hai verdict ngược nhau** — 0.0391 nằm dưới ngưỡng 0.05,
0.0977 nằm trên. 35/36 ô còn lại hai bên khớp hoàn toàn.

⇒ Không còn là tranh luận cấu hình nào đúng. Ô này **phải được báo cáo là borderline / không
robust**, bất kể ta in số nào.

### Độ lệch này có đe doạ kết luận crossover của C4 không? — KHÔNG

| | |
|---|---|
| Lệch XGBoost liên máy, từng run | −0.0099 … +0.0100 |
| Lệch **trung bình** | **+0.0010** (std 0.0061) |
| Độ rộng CI của crossover tại N=5000 / 10000 | 0.0116 / 0.0200 |

Dịch chuyển kỳ vọng (0.0010) nhỏ hơn một bậc so với độ rộng CI ⇒ **kết luận crossover không
bị lật**. Nhưng phải khai trong Limitations rằng số XGBoost phụ thuộc máy ở mức ±0.01/run.

## Fix `algorithm_globals.random_seed` — đã áp code, CHƯA chạy được

Đã thử chạy lại C2 trên máy này. Fix **hoạt động đúng**: `ideal_finite_shot` (ZZ) đổi
`0.879566 → 0.859944`, tức đúng mức lệch ~0.02 đã dự đoán.

**Nhưng lần chạy đó bị lùi**, vì hai lý do:

1. `realistic_noisy_simulator` **OOM lại** (`status: FAIL`, mất luôn dòng đó)
2. Notebook **tính lại cả 10 run** và đè số XGBoost của Quang Anh bằng số máy tôi

⇒ Đã `git checkout HEAD` khôi phục toàn bộ `results/c2_revision` và notebook về bản của bạn ấy,
rồi áp lại **chỉ 2 dòng fix** (không chạy). Diff cuối: **2 dòng thêm, 1 dòng đổi**.

Trong code đã ghi comment: *các dòng `ideal_finite_shot` trong artifact hiện tại được sinh
TRƯỚC fix này; lần chạy C2 tiếp theo sẽ làm chúng đổi nhẹ (~0.02 F1), không đụng điều kiện nào
khác.*

> ### ⚠️ Bài học quy trình
> **Không chạy `nbconvert --execute --inplace` trên notebook của người khác.** Nó tính lại toàn
> bộ và đè kết quả, kể cả phần mình không định đụng. Từ giờ với C2/C3: **chỉ sửa code, không
> chạy**, trừ khi thống nhất trước.

## Việc còn treo cho Quang Anh (nhỏ, không đổi kết luận nào)

1. `uv sync` để về `scikit-learn==1.8.0` như `pyproject.toml` đã ghim → hết lệch `SVM_Poly2` run 3.
2. Pull fix `algorithm_globals` rồi chạy C2 **một lần**. Chỉ 2 dòng `ideal_finite_shot` đổi.
   Máy tôi 16 GB không chạy nổi `realistic_noisy_simulator` (19.900 cặp circuit trong một job Aer).

---

---

# ✅ GIAI ĐOẠN 5 — Table IV vs VI + protocol vs literature (2026-09-02)

## S5.1 — Đóng R1-8: phân rã khoảng cách bằng số, không giải thích bằng lời

Chạy thêm chế độ `frozen_c1` tại N=1000 để có đủ lưới 2×2 {representation} × {test set},
hyperparameter đóng băng của C2. **Sản phẩm**: `c4_table_iv_vs_vi.csv`.

| representation | test set | QSVM-ZZ | QSVM-Z | SVM-RBF | RF | XGB |
|---|---|---:|---:|---:|---:|---:|
| frozen_c1 | fixed 300 | **0.8469** | 0.8355 | 0.8362 | 0.8446 | 0.8503 |
| frozen_c1 | full 22.544 | 0.7959 | 0.7721 | 0.7977 | 0.8009 | 0.8043 |
| refit_per_N | fixed 300 | 0.8526 | 0.8715 | 0.8645 | 0.8673 | 0.8666 |
| refit_per_N | full 22.544 | **0.8072** | 0.8250 | 0.8273 | 0.8250 | 0.8242 |

Ô trên-trái **tái tạo chính xác giá trị của C2 (0.8469)** → lưới này đáng tin.

### Phân rã

| | QSVM-ZZ |
|---|---:|
| Table IV của bài (C2: frozen + test 300) | **0.8469** |
| Table VI của bài (C4: refit + test 22.544) | **0.8072** |
| **Tổng khoảng cách** | **−0.0397** |
| ↳ do **đổi test set** (300 → 22.544) | **−0.0510** |
| ↳ do **đổi representation** (frozen → refit) | +0.0113 |

⇒ Chênh lệch giữa Table IV và Table VI **hoàn toàn do test set**, không phải mâu thuẫn.
Việc đổi representation thậm chí còn làm F1 tuyệt đối của QSVM-ZZ **nhích lên** — dù như
Phát hiện 9 đã chỉ, nó làm ZZ **tụt so với Z**.

Câu cho bài: *Table IV and Table VI use the same training budget at N = 1000 but different
evaluation sets and different pipeline-fitting protocols. Decomposing the 0.040 macro-F1 gap
under matched hyperparameters shows that −0.051 comes from evaluating on the full 22,544-sample
KDDTest+ instead of the fixed 300-sample subset, and +0.011 from re-fitting the embedding on
the N training rows. The two tables are therefore consistent.*

---

## S5.2 — Đóng R1-9: vì sao F1 thấp hơn literature? Trả lời bằng thí nghiệm

**Sản phẩm**: `c4_protocol_vs_literature.csv`. Ba cấu hình tham chiếu, cùng model, chỉ đổi
một yếu tố mỗi lần:

| Cấu hình | Model | n_train | n_feat | macro-F1 | accuracy | recall_rare |
|---|---|---:|---:|---:|---:|---:|
| **A** 122 feat, train đầy đủ, test = **KDDTest+** | XGB | 125.973 | 122 | 0.8041 | 0.8043 | 0.1037 |
| **A** | RF | 125.973 | 122 | 0.7765 | 0.7774 | 0.0623 |
| **B** 122 feat, train đầy đủ, test = **random split của KDDTrain+** | XGB | 100.778 | 122 | **0.9993** | **0.9993** | — |
| **B** | RF | 100.778 | 122 | **0.9978** | **0.9979** | — |
| **C** K=20+PCA-4, train đầy đủ, test = KDDTest+ | XGB | 125.973 | 4 | 0.7655 | 0.7658 | 0.1799 |
| **C** | RF | 125.973 | 4 | 0.7560 | 0.7565 | 0.1480 |

### Ba kết luận định lượng

1. **A vs B — đây là toàn bộ lời giải thích.** Cùng model, cùng 122 feature, cùng tập train,
   **chỉ đổi tập test**: 0.804 → **0.999**. Khoảng cách **~20 điểm**. Các con số 99% thường
   thấy trong literature NSL-KDD là kết quả của việc **chia ngẫu nhiên KDDTrain+**, không phải
   train trên KDDTrain+ rồi test trên KDDTest+. KDDTest+ cố ý chứa attack chưa từng xuất hiện.

2. **A vs C — giảm chiều của bài tốn rất ít.** Đi từ 122 feature xuống 4 chỉ mất **0.039**
   macro-F1 với XGBoost (0.8041 → 0.7655). Và đáng chú ý, PCA-4 **cải thiện recall lớp hiếm**
   (0.1037 → 0.1799) — giảm chiều làm model bớt overfit vào lớp đa số.

3. **Một điểm đáng đưa vào bài**: QSVM-ZZ ở N=10.000, chỉ **4 chiều** (regime `natural`) đạt
   **0.7855**, **cao hơn RandomForest dùng toàn bộ 125.973 mẫu và cả 122 feature (0.7765)**.

⇒ Kết luận cho R1-9: F1 của bài không thấp vì pipeline yếu, mà vì bài dùng **giao thức đánh
giá khó hơn** so với phần lớn literature. Không được "làm cho F1 cao lên" — phải giải thích
đúng, kèm bảng này.

---

---

# ✅ GIAI ĐOẠN 6 — Note C4 + bộ số chung cho regime map (2026-09-02)

## S6.1 — Note C4

**Sản phẩm**: [`notebooks/nslkdd/note/C4/C4_results_reviewer_analysis_and_manuscript_revision.md`](../../notebooks/nslkdd/note/C4/C4_results_reviewer_analysis_and_manuscript_revision.md)

Viết theo đúng format note C1/C3 FINAL của Quang Anh, 12 mục: scope · protocol · phát hiện
chính · ablation phụ thuộc cơ sở · rare-attack · Table IV vs VI · protocol vs literature ·
tuning đối xứng · ma trận đóng reviewer · hướng sửa manuscript (kèm bảng "nên/không nên viết") ·
limitations · khuyến nghị.

Đóng được **8 item reviewer** ở cấp C4: R1-7, R1-8, R1-9, R4-4, R2-3, R1-5/R2-1, R1-3/R4-5,
R1-4/AE-1.

## S6.2 — `results/nslkdd/regime_map_rows.csv` — một bộ số duy nhất cho cả bài

Gộp artifact của Quang Anh (C2, C3) với artifact C4 của tôi thành **110 dòng**, cùng schema:
`contribution, regime, condition, metric, baseline, estimate, ci_low, ci_high, p_value,
effect_size, verdict, source`.

| Contribution | QSVM-favorable | classical-favorable | inconclusive |
|---|---:|---:|---:|
| C2 | 1 | 0 | 1 |
| C3 | 7 | 10 | 19 |
| C4 | 13 | 11 | 48 |
| **Tổng** | **21** | **21** | **68** |

Con số này tự nó là câu trả lời cho AE-1 và R1-4: **21 ô ủng hộ quantum, 21 ô ủng hộ classical,
68 ô không kết luận được**. Không có cơ sở nào để nói "quantum advantage is real".

### Các ô QSVM-favorable mạnh nhất (dùng cho Fig 10 mới)

| Contribution | Regime | Baseline | Δ | p | d_z |
|---|---|---|---:|---:|---:|
| C2 | stationary (ΔKTA) | QSVM_Z | +0.1378 | 0.0020 | 8.91 |
| C3 | attack_composition | SVM_Linear | +0.0650 | 0.0059 | 3.02 |
| C3 | attack_composition | QSVM_Z | +0.0534 | 0.0020 | 2.03 |
| C3 | prior_shift 70% | QSVM_Z | +0.0367 | 0.0059 | 1.33 |
| **C4** | **N=10000 (natural)** | **XGBoost** | **+0.0149** | **0.0078** | **1.07** |
| **C4** | **N=10000 (natural)** | **RandomForest** | **+0.0127** | **0.0078** | **1.13** |
| **C4** | **N=5000 (natural)** | **XGBoost** | **+0.0100** | **0.0273** | **1.22** |

Đáng chú ý: **C4 là contribution duy nhất có ô QSVM thắng một tree ensemble với ý nghĩa thống
kê**. C2/C3 chỉ thắng được đối chứng không entangle và họ SVM.

---

---

# ✅ GIAI ĐOẠN 7 — Kiểm kê UNSW-NB15 (2026-09-02)

**Sản phẩm**: [03_UNSW_AUDIT.md](03_UNSW_AUDIT.md) — kiểm kê đầy đủ + bảng khoảng cách + phạm vi đã chốt.

## Tiền xử lý UNSW: SẠCH

Kiểm tra mã cả 3 notebook: `MinMaxScaler`, `SelectKBest`, `PCA`, angle-scaler **đều fit trên
train only**. Không NaN, không Inf, không cột hằng số. Không có rò rỉ.

## 🔴 Phát hiện 13 — UNSW-NB15 trùng lặp dữ liệu ở mức rất cao

| | Số hàng | Chữ ký duy nhất | Trùng lặp nội bộ |
|---|---:|---:|---:|
| Train | 175,341 | 92,357 | **47.3%** |
| Test | 82,332 | 48,353 | **41.3%** |

| | Hàng test có bản sao **chính xác** trong train |
|---|---:|
| **UNSW-NB15** | **20,561 / 82,332 = 24.97%** |
| NSL-KDD | 610 / 22,544 = 2.71% |

**Kiểm chứng trên dữ liệu THÔ** (34 feature gốc, trước mọi xử lý): 25.33% — khớp con số đã xử
lý (24.97%) ⇒ **thuộc tính của dataset**, không phải lỗi tiền xử lý của nhóm.

⇒ Một phần tư tập test UNSW có thể "thuộc lòng" từ train. Mọi con số trên UNSW — của nhóm và
của mọi công trình khác — đều được nâng bởi hiệu ứng này. Phải khai trong Limitations, và nên
báo cáo thêm biến thể **test đã khử trùng lặp** làm kiểm chứng phụ (U5) — chưa thấy công trình
QSVM-IDS nào làm.

## 🔴 Phát hiện 14 — Dữ liệu UNSW cũ làm giàu lớp hiếm 7×, và không nhất quán

| Tập | n | Rare (Worms+Shellcode+Backdoor+Analysis) |
|---|---:|---:|
| Train đầy đủ | 175,341 | **2.86%** |
| `multi_run/train_run{1..5}` | **100** | **20.00%** |
| `UNSW_Train_Sample500` | 496 | 20.16% |
| `UNSW_Train_Sample1000` | 997 | **12.04%** |

Vừa làm giàu 7×, vừa **không nhất quán giữa các mốc N** (20.8% ở N=100 → 12.0% ở N=1000) —
đúng lỗi đã sửa ở C4 NSL-KDD. Phải dựng lại tập con theo 2 chế độ lồng nhau.

## Khoảng cách so với chuẩn mới — gần như phải chạy lại toàn bộ

| Hạng mục | UNSW cũ | Chuẩn mới |
|---|---|---|
| N_train / số run | **100** / 5 | 1,000 (sweep tới 10,000) / **10** |
| Số model | 4 | **7** |
| Tuning | `C=1.0` cố định | tuning set + 1-SE, 7 model mỗi (N, run) |
| Chọn n | **áp đặt n=4** từ NSL-KDD | luật 3 tầng C1 chạy độc lập |
| Test | subsample 100–300 | **full 82,332** |

Tái sử dụng được: `UNSW_{Train,Test}_Cleaned.parquet` và đường cong CV chọn K. Bỏ: toàn bộ
`multi_run/`, `Sample*`, `results/unsw/*.json`, `models/unsw/qsvm_cache`.

## Điểm cộng khoa học lớn nhất: kiểm chứng C1 là **thủ tục**, không phải con số

UNSW cũ đặt `n_pca_fixed = 4` — mượn thẳng con số của NSL-KDD. Chạy luật 3 tầng C1 độc lập trên
UNSW cho hai khả năng, **cả hai đều tốt**:

- `n* = 4` → thủ tục cho cùng kết quả trên 2 dataset độc lập, củng cố C1
- `n* ≠ 4` → **chứng minh C1 là thủ tục chuyển giao được**, đóng góp nằm ở *phương pháp lựa
  chọn* chứ không ở *cấu hình được chọn* — đây là câu trả lời trực diện cho **R3-1**

## Phạm vi đã chốt

**Làm**: U1 luật C1 trên UNSW · U2 tuning đối xứng · **U3 sample-complexity 2 chế độ** ·
U4 rare-attack · U5 test khử trùng lặp · U6 prior-shift (nếu kịp).

**Không làm**: noise (C2 đã có) · temporal shift (UNSW không có split thời gian) ·
calibration (thuộc Paper 2) · CatBoost.

**Câu hỏi trung tâm của U3**: crossover tìm được trên NSL-KDD ở N≈2000–5000 có **chuyển giao**
sang UNSW không? Đây là phép thử tổng quát hoá trực tiếp nhất cho phát hiện chính của C4.

Ước tính chi phí: **~7 giờ** (test UNSW 82,332 mẫu → 69 s statevector mỗi cell). Bắt buộc dùng
dự đoán theo lô vì Gram test ở N=10,000 là 6.6 GB.

---

---

# 🔄 GIAI ĐOẠN 8 — UNSW pipeline

## ✅ U1 — Luật C1 chạy độc lập trên UNSW

**Sản phẩm**: `results/unsw/c4_revision/u1_c1_selection_unsw.json`,
`u1_dimension_metrics.csv`, `u1_nstar_robustness.csv`.

### 🟢 Phát hiện 15 — `n*_UNSW = 6`, KHÁC `n*_NSL-KDD = 4`

**Tầng 0 — chọn K.** Dùng đúng tiêu chí elbow của bài (δ = 0.01 quanh đỉnh CV):
đỉnh F1 = 0.8896 tại K=100, ngưỡng 0.8796 → **K\* = 35**. Khớp với K mà nhóm đã dùng.

**Bảng C1 cho UNSW** (K=35, subset KTA 300 mẫu, seed 42):

| n | V(n) | 1/DBI | KTA | R_eff | offdiag std | Q(n) | CNOT |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0.7822 | 0.3959 | 0.1368 | 6.47 | 0.3148 | 0.0261 | 4 |
| 3 | 0.8366 | 0.4057 | 0.1470 | 11.38 | 0.2647 | 0.0717 | 12 |
| 4 | 0.8696 | 0.3948 | 0.1478 | 16.18 | 0.2516 | 0.1391 | 24 |
| 5 | 0.8892 | 0.3899 | 0.1689 | 21.28 | 0.2380 | 0.2283 | 40 |
| **6** | **0.9044** | 0.3840 | **0.1986** | 38.52 | 0.1905 | **0.3391** | **60** |
| 7 | 0.9188 | 0.3806 | 0.1625 | 53.54 | 0.1623 | 0.4717 | 84 |
| 8 | 0.9329 | 0.3758 | 0.1874 | 84.31 | 0.1455 | 0.6261 | 112 |
| 9 | 0.9444 | 0.3737 | 0.1808 | 95.99 | 0.1380 | 0.8022 | 144 |
| 10 | 0.9552 | 0.3711 | 0.1771 | 100.55 | 0.1346 | 1.0000 | 180 |

**Áp luật 3 tầng:**

| Tầng | Kết quả |
|---|---|
| 1. `V(n) ≥ 0.85` | F_V = {4, 5, 6, 7, 8, 9, 10} |
| 2. `KTA ≥ 0.95 × 0.198587` (đạt tại n=6) → ngưỡng 0.188658 | F_V,KTA = **{6}** — chỉ một ứng viên |
| 3. `min Q(n)` | **n\* = 6** |

### Kiểm chứng độ vững — 10 subset KTA độc lập

Lặp lại toàn bộ luật với 10 subset khác nhau (seed 42–51), dùng **đúng cách lấy mẫu của C1**
(`train_test_split`, stratify theo `attack_category`, N=300):

| ε | n\*=5 | n\*=6 |
|---:|---:|---:|
| 0.02 | 0 | **10/10** |
| 0.05 | 0 | **10/10** |
| 0.10 | 3 | 7 |

`n=6` có KTA cao nhất trong vùng feasible ở **cả 10 subset** (0.1903–0.2182). Vững hơn hẳn
kết quả trên NSL-KDD, nơi ε=0.02 làm n\* nhảy từ 4 sang 5.

### Ý nghĩa — đây là câu trả lời trực diện cho R3-1

Toàn bộ công việc UNSW trước đây đặt `n_pca_fixed = 4`, tức **mượn thẳng con số của NSL-KDD**.
Luật C1 chạy độc lập cho **n\* = 6**.

> **C1 là một thủ tục có thể chuyển giao, không phải một hằng số gán tay.** Hai dataset độc lập
> đi qua cùng một luật cho hai cấu hình khác nhau, mỗi cấu hình được biện minh bằng dữ liệu của
> chính nó. Đóng góp nằm ở *phương pháp lựa chọn*, không ở *con số được chọn* — đúng điều
> Reviewer 3 nói là thiếu.

Hệ quả phụ: mọi kết quả UNSW cũ dùng n=4 là **dưới tối ưu theo chính tiêu chí của nhóm**.

### ⚠️ Phát hiện 16 — File UNSW được sắp xếp theo lớp

`UNSW_Train_Cleaned.parquet` **sắp theo lớp**: 20.000 hàng đầu đều là `Normal`. Bất kỳ thao tác
nào cắt theo chỉ số tuần tự (`X[:20000]`) đều cho tập chỉ có một lớp. Đã ghi cảnh báo vào
artifact; mọi lấy mẫu phải ngẫu nhiên có phân tầng.

### U2 — Mở rộng pipeline cho hai dataset

Thêm `DatasetSpec` vào `src/c4_pipeline.py`: tham số hoá đường dẫn, nhãn phân tầng, lớp hiếm,
số qubit, K. UNSW dùng n=6, K=35, rare = {Worms, Shellcode, Backdoor, Analysis}, 5 nhóm phân
tầng {Normal, Generic, Exploits, Frequent, Rare}.

**Kiểm chứng không hồi quy NSL-KDD sau mỗi lần refactor** — đây là điều kiện bắt buộc vì kết
quả C4 NSL-KDD đã dùng để viết note.

### Bốn lỗi phát hiện trong lúc chuẩn bị

| # | Lỗi | Cách phát hiện | Sửa |
|---|---|---|---|
| 1 | Gate G3 tính tỉ lệ nền theo **chữ ký** thay vì theo **hàng** | G3 fail giả trên UNSW (1.5% vs 28.5% thật) | tính theo hàng |
| 2 | Lấy mẫu loại trừ theo chữ ký → **chặn trần N ở ~8.000** và âm thầm khử trùng lặp tập train | Pool hết `Generic` ở N=20000 | đổi sang loại trừ theo **chỉ số hàng** |
| 3 | Statevector cache riêng theo `arm` → tính hai lần | arm 2 chạy lại từ đầu | tách khoá cache khỏi `arm`; arm 2 giờ tốn ~1s |
| 4 | Arm `frozen_c2` chạy cho UNSW bằng hyperparameter **của NSL-KDD** | hai arm cho kết quả giống hệt | chặn cứng; UNSW dùng `tuned_once` |

Lỗi #2 dẫn tới **Phát hiện 17**: lớp `Generic` của UNSW có **40.000 hàng nhưng chỉ 1.800 chữ ký
duy nhất** (trùng lặp **95,5%**). Một mình lớp này gây ra phần lớn trùng lặp của UNSW. Hệ quả
phụ: tuning set 2.000 mẫu có tới ~49.000 bản sao trong train, nên pool mất 28% số hàng.

## 🟢 Phát hiện 18 — Tính statevector dạng đóng, nhanh hơn 457–763 lần

Sau mỗi lớp Hadamard, phần còn lại của Z/ZZFeatureMap là **đường chéo** trong cơ sở tính toán:

```
pha_ZZ(z) = Σᵢ 2·xᵢ·zᵢ + Σᵢ<ⱼ 2(π−xᵢ)(π−xⱼ)·(zᵢ ⊕ zⱼ)
|ψ⟩ = (D(x) · H^⊗n)^reps |0⟩
```

Số hạng cặp chỉ áp khi `zᵢ ⊕ zⱼ = 1` vì ZZFeatureMap hiện thực tương tác bằng CNOT–RZ–CNOT.
Nên toàn bộ mẫu tính được cùng lúc bằng numpy thay vì gọi `Statevector` từng mẫu.

| | Qiskit | Dạng đóng | Tăng tốc |
|---|---:|---:|---:|
| n=4 | 0.805 ms/mẫu | 0.0011 ms/mẫu | **763×** |
| n=6 | 1.777 ms/mẫu | 0.0039 ms/mẫu | **457×** |

Toàn bộ 82.332 mẫu test UNSW: **170 s → 0,6 s**.

**Kiểm chứng**: max|Δ| so với `FidelityStatevectorKernel` là 1.8e-15 – 3.9e-15 cho cả 4 cấu
hình (n=4/6 × ZZ/Z). Hàm `verify_kernel_equivalence` chạy tự động ở mỗi lần khởi động.

**Kiểm chứng hồi quy trên kết quả NSL-KDD đã có**: **68/70 ô trùng khớp tuyệt đối**. 2 ô lệch
đúng **1 dự đoán trên 22.544 mẫu** (4.44e-05 lý thuyết vs 4.51e-05 quan sát) — tie ở biên
libsvm bị lật bởi chênh lệch 1e-15, cùng hiện tượng đã ghi nhận ở C2 (n_SV ±1).

## 🔴 Phát hiện 19 — Cache statevector suýt làm OOM cả job

Khi theo dõi lần chạy đầu, RAM tụt dần 3.9 → 2.7 GB. Nguyên nhân: `StatevectorCache` giữ **mọi**
mảng trong RAM, không giải phóng.

| | |
|---|---|
| 1 mảng statevector test UNSW đầy đủ | 82.332 × 2⁶ complex128 = **84 MB** |
| Mỗi cell giữ (2 kernel × 2 split) | ~0,17 GB |
| 60 cell nếu không giải phóng | **~10 GB → chắc chắn OOM** |

Job sẽ chết ở khoảng N=5000 sau vài giờ. Đã dừng và sửa trước khi mất công.

**Sửa hai chỗ:**

1. RAM: cache đổi sang **LRU giữ 6 mục gần nhất** — đủ để 2 arm trong cùng cell dùng chung.
   Kiểm chứng: sau 24 lần gọi giữ **259 MB** thay vì 1,0 GB.
2. Đĩa: sau khi có hàm dạng đóng, tính lại 82.332 mẫu chỉ mất 0,6 s trong khi cache đĩa đã ngốn
   **2,3 GB chỉ sau 15 cell** (sẽ là ~9 GB). Giờ chỉ mảng ≤ 20.000 hàng mới ghi đĩa.

> **Bài học**: cache là con dao hai lưỡi. Khi chi phí tính toán giảm 500 lần, cache từ chỗ có
> lợi trở thành gánh nặng. Phải đo lại lợi ích của cache sau mỗi lần tối ưu.

## Công cụ phân tích

`runners/analyze_c4.py` — learning curve, thống kê paired (CI/Wilcoxon/d_z/Holm cùng công thức
C3), rare-attack, và **tự động dò crossover**. Đã kiểm chứng trên NSL-KDD: tái tạo đúng mọi phát
hiện và dò ra crossover vs XGBoost (classical tới N=1000 → QSVM từ N=5000), vs RandomForest
(tới N=1000 → từ N=10000).

## Đang chạy

1 tiến trình, RAM 1,14 GB, còn trống 3,3 GB. N ∈ {100, 500, 1000, 2000, 5000, 10000},
10 run, 7 model, 2 arm, test đầy đủ 82.332.

Kết quả đầu tiên: N=100 → QSVM-ZZ **0.5953** vs XGBoost **0.6855** (classical dẫn rõ ở vùng ít
dữ liệu, đúng hình dạng của NSL-KDD regime `natural`).

---

# ✅ GIAI ĐOẠN 9 — Thí nghiệm UNSW (U3) (2026-09-02)

**Sản phẩm**: `results/unsw/c4_revision/` — `c4_per_run_unsw_natural_refit_per_N.csv`
(**1680 bản ghi**), `c4_pairwise_statistics_natural.csv`, `c4_rare_attack_natural.csv`,
`c4_crossover_natural.csv`. 120/120 cell, 2 giờ 11 phút.

Cấu hình: n=6 (từ U1), K=35, regime `natural`, N ∈ {100…10000}, 10 run, 7 model, 2 arm,
test đầy đủ **82.332 mẫu**.

## 🔴 Phát hiện 20 — Crossover KHÔNG chuyển giao sang UNSW

| N | QSVM-ZZ | QSVM-Z | SVM-RBF | RandomForest | XGBoost |
|---:|---:|---:|---:|---:|---:|
| 100 | 0.5953 | 0.6234 | 0.6289 | **0.6851** | 0.6855 |
| 500 | 0.6721 | 0.6545 | 0.6727 | **0.7134** | 0.7072 |
| 1000 | 0.6797 | 0.6775 | 0.6837 | **0.7255** | 0.7206 |
| 2000 | 0.6997 | 0.6812 | 0.6808 | **0.7342** | 0.7189 |
| 5000 | 0.7223 | 0.6800 | 0.6816 | **0.7547** | 0.7385 |
| 10000 | 0.7301 | 0.6852 | 0.6899 | **0.7612** | 0.7505 |

**QSVM-ZZ vs XGBoost / RandomForest: classical-favorable ở gần như MỌI N** (XGB chỉ
inconclusive tại N=2000). Không có ô QSVM-favorable nào so với tree ensemble ở bất kỳ N nào.

| N | ZZ − XGB | holm_p | ZZ − RF | holm_p |
|---:|---:|---:|---:|---:|
| 1000 | −0.0410 | 0.0078 | −0.0458 | 0.0078 |
| 5000 | −0.0161 | 0.0195 | −0.0323 | 0.0078 |
| 10000 | −0.0204 | 0.0039 | −0.0312 | 0.0039 |

### Đối chiếu trực tiếp hai dataset, cùng giao thức

| N | NSL-KDD (ZZ − XGB) | UNSW (ZZ − XGB) |
|---:|---:|---:|
| 1000 | −0.029 | −0.041 |
| 5000 | **+0.010** ✅ QSVM | −0.016 ❌ |
| 10000 | **+0.015** ✅ QSVM | −0.020 ❌ |

⇒ **Crossover là hiện tượng phụ thuộc dataset, không phải tính chất của quantum kernel.**

Kiểm chứng không phải artifact của việc tune lại mỗi N — arm `tuned_once` cho cùng kết luận,
thậm chí khoảng cách còn rộng hơn:

| N | 100 | 1000 | 5000 | 10000 |
|---|---:|---:|---:|---:|
| ZZ−XGB, `tuned_per_N` | −0.090 | −0.041 | −0.016 | −0.020 |
| ZZ−XGB, `tuned_once` | −0.101 | −0.044 | −0.043 | −0.041 |

## 🟢 Phát hiện 21 — Nhưng ablation entanglement thì CHUYỂN GIAO, và mạnh hơn

| N | ZZ − Z | CI 95% | p | Verdict |
|---:|---:|---|---:|---|
| 100 | −0.0281 | [−0.0658, +0.0097] | 0.131 | inconclusive |
| 500 | +0.0177 | [−0.0063, +0.0417] | 0.193 | inconclusive |
| 1000 | +0.0021 | [−0.0196, +0.0239] | 0.846 | inconclusive |
| **2000** | **+0.0185** | [+0.0006, +0.0364] | **0.049** | **QSVM-favorable** |
| **5000** | **+0.0424** | [+0.0182, +0.0666] | **0.002** | **QSVM-favorable** |
| **10000** | **+0.0449** | [+0.0192, +0.0706] | **0.002** | **QSVM-favorable** |

Đây là **tái lập độc lập** của Phát hiện 9/10 trên NSL-KDD: lợi thế của entanglement **cần đủ
dữ liệu để ước lượng cơ sở biểu diễn**. Ở N nhỏ nó âm hoặc không kết luận được; từ N≥2000 nó
dương và có ý nghĩa thống kê.

Và trên UNSW hiệu ứng **mạnh gấp đôi** NSL-KDD tại N=5000 (+0.042 vs +0.022).

QSVM-ZZ cũng thắng **toàn bộ họ SVM** (Linear, Poly2, RBF) từ N≥2000, ví dụ vs SVM-RBF:
+0.019 (N=2000, p=0.037) → +0.041 (N=5000, p=0.020) → +0.040 (N=10000, p=0.006).

## ⚠️ Phát hiện 22 — Lớp hiếm của UNSW KHÔNG khó, nên phần rare-attack không chuyển giao

Recall trên rare subset (Worms ∪ Shellcode ∪ Backdoor ∪ Analysis, 1.682 mẫu test):

| N | QSVM-ZZ | QSVM-Z | SVM-RBF | RF | XGB |
|---:|---:|---:|---:|---:|---:|
| 1000 | 0.9598 | 0.9549 | 0.9485 | 0.9438 | 0.9460 |
| 10000 | 0.9828 | **0.9927** | 0.9687 | 0.9700 | 0.9782 |

**Mọi model đều đạt recall 0.94–0.99.** Và signed margin trên rare là **DƯƠNG** với mọi model
(0.36–1.68), trái ngược hoàn toàn với NSL-KDD (âm, −0.20 đến −0.98).

Nguyên nhân: 4 lớp hiếm của UNSW đều là **tấn công**, và bài toán nhị phân là Normal vs Attack
với 68% train là attack. Model dự đoán "attack" là trúng ngay. Còn U2R/R2L của NSL-KDD là tấn
công **trông giống lưu lượng bình thường** — đó mới là cái khó.

⇒ Rare subset của UNSW **không kiểm tra cùng năng lực** như rare subset của NSL-KDD. Không được
dùng nó để nói "phát hiện rare-attack chuyển giao"; phải ghi rõ hai lớp hiếm khác bản chất.

## Tổng kết: cái gì chuyển giao, cái gì không

| Phát hiện của C4 trên NSL-KDD | Chuyển giao sang UNSW? |
|---|---|
| Crossover vs tree ensembles ở N≈2000–5000 | ❌ **Không** — classical thắng ở mọi N |
| Entanglement cần đủ dữ liệu mới có lợi | ✅ **Có**, và mạnh gấp đôi |
| QSVM-ZZ thắng họ SVM ở N lớn | ✅ **Có** (từ N≥2000) |
| Rare-attack: signed margin âm, lớp hiếm khó | ❌ **Không** — lớp hiếm UNSW dễ |
| C1 là thủ tục chuyển giao được | ✅ **Có** — nhưng cho n\*=6 thay vì 4 |

Đây là kết quả **tốt cho bài**: nó cho một ranh giới rõ ràng giữa cái phổ quát (vai trò của
entanglement, tính chuyển giao của thủ tục C1) và cái phụ thuộc dataset (crossover, độ khó
của lớp hiếm) — đúng thứ mà một "regime-specific benchmark" cần chứng minh.

---

## Tổng kết Giai đoạn 0 + 1

Đã đóng băng protocol, dựng xong hạ tầng, và **gate quan trọng nhất đã PASS**: code C4 tái tạo
số của C2 chính xác tới chữ số cuối trên cả hai model quantum.

Trên đường đi phát hiện **7 vấn đề**, trong đó 3 cái là lỗi thật của bản đã nộp hoặc của
protocol dùng chung:

| # | Phát hiện | Mức |
|---|---|---|
| 1 | `"+6.7 points vs SVM-RBF trên rare subset"` sai ba chỗ; không có số rare nào tồn tại | 🔴 |
| 2 | `d = +0.68` không tái tạo được; số thật +0.4043; nguồn 0.68 gần nhất mang **dấu âm** | 🔴 |
| 3 | C5/C6 dùng `\|margin\|` — đo độ tự tin chứ không đo đúng/sai | 🔴 |
| 4 | `train_run{i}` giàu lớp hiếm **gấp 12 lần** tỉ lệ tự nhiên — chưa từng ghi trong bài | 🔴 |
| 5 | KDDTrain+ và KDDTest+ trùng 610 dòng (thuộc tính dataset, phải công bố) | 🟡 |
| 6 | XGBoost của C2 phụ thuộc số thread → không tái tạo được trên máy khác | 🔴 |
| 7 | Một ô cache của C2 (`SVM_Poly2` run 3) không tái tạo được | 🟡 |

## Việc còn treo

| # | Việc | Trạng thái |
|---|---|---|
| 1 | Xoá `paper/paper1/manuscript.pdf` | chờ, đã chốt sẽ xoá |
| 2 | Gỡ 1.7 GB cache `.npy` khỏi git | chờ bạn Quang Anh |
| 3 | CatBoost | **đã chốt: không thêm** |
| 4 | `qiskit-aer` + `qiskit-ibm-runtime` thiếu trong `pyproject.toml` | chờ Quang Anh xác nhận version |
| 5 | File `.tex` nguồn bản đã nộp | Quan tự lo |
| 6 | **MỚI** — Quang Anh chạy lại C2/C3 với XGBoost `n_jobs=1` | cần hỏi |
| 7 | **MỚI** — Quang Anh chạy lại C2 run 3 với `FORCE_RERUN=True` | cần hỏi |

**Bước tiếp theo**: Giai đoạn 2 — learning curve lõi, cả hai chế độ lấy mẫu, 10 run, 7 model,
2 test set, tune đối xứng tại mỗi (N, run).

---

# ✅ GIAI ĐOẠN 10 — Vẽ lại bộ hình cho bản revision (2026-09-03)

**Script**: `runners/make_paper1_figures.py` (một lệnh sinh cả 4 hình)
**Output**: `paper/paper1/figs_revision/*.pdf` + `*.png` (400 dpi, `pdf.fonttype=42` để
IEEE nhúng font được, khổ 7.16 in = đúng chiều rộng 2 cột)

## Bốn hình

| Hình | Nội dung | Nguồn số |
|---|---|---|
| **Fig 5** | Luật chọn số chiều 3 giai đoạn, 2 hàng (NSL-KDD / UNSW) × 3 panel: `V(n)`, KTA, `Q(n)` | `C1_revision.ipynb` block C/D/E + `u1_dimension_metrics.csv`, `u1_c1_selection_unsw.json` |
| **Fig 9** | Learning curve NSL-KDD, 2×2: (a)(b) F1 tuyệt đối `natural` / `matched`, (c)(d) Δ ghép cặp kèm CI 95% | `c4_per_run_{natural,matched}_refit_per_N.csv`, `c4_pairwise_statistics_*.csv` |
| **Fig 10** | Bản đồ chế độ — lưới điều kiện × baseline, 3 mức verdict | `regime_map_rows.csv` (110 dòng) |
| **Fig 11** | Chuyển giao sang UNSW-NB15: learning curve + Δ ghép cặp | `c4_per_run_unsw_natural_refit_per_N.csv`, `c4_pairwise_statistics_natural.csv` (UNSW) |

## Quyết định thiết kế đáng ghi

1. **Bỏ Pareto khỏi Fig 5.** Bản cũ vẽ Pareto như thể nó chọn `n`; thật ra cả 9 candidate đều
   Pareto-optimal (chính notebook C1 đã ghi "Pareto CHỈ là diagnostic"). Hình mới vẽ đúng
   ba giai đoạn của luật: vùng xám = bị loại bởi `V < T`, vòng tròn rỗng = qua giai đoạn 1-2,
   chấm đặc = `n*` chọn ở giai đoạn 3.

2. **Fig 5 ghép hai bộ dữ liệu vào một hình.** Đây là câu trả lời trực tiếp cho R3-1: cùng một
   thủ tục, không sửa tham số, ra `n*=4` trên NSL-KDD và `n*=6` trên UNSW. Một hình nói được
   điều mà hai hình rời không nói được.

3. **Fig 10 là lưới chấm, không phải forest plot.** 110 dòng effect size xếp dọc thì không ai
   đọc nổi; nhưng dữ liệu vốn có cấu trúc lưới (điều kiện × baseline) nên vẽ đúng dạng lưới.
   Verdict là phân cực 3 mức nên dùng 2 màu + xám trung tính ở giữa, kèm **hình dấu riêng**
   (▲ / ● / ▼) — danh tính không bao giờ chỉ dựa vào màu.

4. **Bốn panel của Fig 9 dùng chung một trục x** `[100, 10000]`. Nhóm `matched` cạn ở
   `N=2000`; nếu để mỗi panel một thang đo thì hai cột không đọc chồng lên nhau được.
   Phần không có dữ liệu tô xám và ghi rõ lý do thay vì để trục trống.

5. **Panel Δ dùng thanh sai số, không dùng dải.** Bốn dải CI chồng nhau thành mảng màu
   không đọc được; thanh sai số có lệch nhẹ theo x thì tách bạch.

6. 🔴 **Đã sửa một chỗ suýt thành cherry-picking.** Bản vẽ đầu để panel Δ chỉ so với
   QSVM-Z / XGBoost / RandomForest. Nhưng tại `N=10000` trên NSL-KDD, **SVM-RBF (0.7740) mới
   là baseline cổ điển mạnh nhất**, mạnh hơn XGBoost (0.7706) — bỏ nó đi thành ra chỉ so với
   đối thủ dễ hơn. Đã thêm SVM-RBF vào cả Fig 9 và Fig 11.

   Thêm vào rồi mới lộ ra **hai điều quan trọng**:

   | | NSL-KDD | UNSW-NB15 |
   |---|---|---|
   | ZZ − SVM_RBF tại `N=10000` | +0.0115, holm_p = **0.131** → inconclusive | +0.0401, holm_p = **0.0059** → QSVM-favorable |
   | ZZ − SVM_RBF, mọi `N` | **không có N nào có ý nghĩa** | có ý nghĩa từ `N≥2000` |

   - Trên NSL-KDD, QSVM-ZZ **chưa từng** thắng SVM-RBF có ý nghĩa ở bất kỳ `N` nào.
     Đây là caveat phải giữ trong bài, không được để hình che đi.
   - Trên UNSW thì ngược lại: QSVM-ZZ **thắng SVM-RBF có ý nghĩa** (+0.040, p=0.006).

7. **Đổi tiêu đề Fig 11 cho đúng phạm vi.** Ban đầu đặt là "The crossover does not transfer to
   UNSW-NB15" — đúng với ensemble cây nhưng sai với họ kernel. Đổi thành *"On UNSW-NB15 the
   quantum kernel beats classical kernels, not tree ensembles"*: hẹp hơn, nhưng đúng và
   thực ra mạnh hơn cho bài.

## Kiểm tra màu

Chạy `scripts/validate_palette.js` (skill dataviz) trước khi chốt bảng màu:

```
4 slot nhấn (#2a78d6, #eb6834, #1baf7a, #4a3aa7) — chế độ sáng, all-pairs
  [PASS] dải sáng · [PASS] sàn chroma
  [PASS] tách CVD        worst ΔE 9.2 (deutan), tritan 9.6   (ngưỡng 8)
  [PASS] sàn thị lực thường  worst ΔE 16.3                   (ngưỡng 15)
```

Ba đường SVM cổ điển hạ xuống ba mức xám khác nhau, mỗi đường một kiểu nét + một marker
riêng. Bảng in đen trắng vẫn phân biệt được: đây là yêu cầu bắt buộc vì TETC in giấy.

## Việc còn treo của hình

| # | Việc | Ghi chú |
|---|---|---|
| 1 | Viết caption LaTeX cho 4 hình | làm cùng lúc viết bài |
| 2 | Fig 5 hàng UNSW chưa có bootstrap CI cho KTA | NSL-KDD có (B=200); UNSW chưa chạy. Legend đã ghi rõ "NSL-KDD only" nên không nói sai, nhưng chạy nốt thì cân đối hơn (~15 phút) |
| 3 | Số hình cuối cùng (5 / 9 / 10 / 11) | phụ thuộc bố cục bài sau khi gộp, sẽ chốt khi có `.tex` |
