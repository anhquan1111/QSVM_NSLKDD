# S0.1 — Audit truy vết 5 claim C4 của bản đã nộp

> Ngày chạy: 2026-09-01 · Nguồn đối chiếu: `paper/paper1/paper1.pdf` (Sec. V-D, Table VI, Fig 9, Fig 10, Sec. VI-B)
> Artifact: `results/nslkdd/c6_results.json`, `results/nslkdd/c5_results.json`, `results/nslkdd/c5_results_multirun.json`, `results/nslkdd/c4_multirun/*.csv`, `data/nslkdd/processed_data/c5_multirun_stat_per_run.csv`
> **Nguyên tắc: chỉ ghi số tái tạo được. Không tái tạo được thì ghi "không tái tạo được".**

---

## Bảng phán quyết

| # | Claim trong bản nộp | Số trong bài | Tái tạo được? | Phán quyết |
|---|---|---|---|---|
| K1 | Table VI: QSVM-ZZ 0.813/0.797/0.831/0.813 | ✔ | ✅ khớp tuyệt đối | **Đúng nhưng yếu** |
| K2 | *"leads by +6.7 points over SVM-RBF on the rare-attack subset"* | +6.7 | ❌ | **Sai — 3 lỗi chồng nhau** |
| K3 | *"Cohen's d of +0.68 on the per-sample decision margins"* | +0.68 | ❌ | **Không tái tạo được; nghi sai dấu** |
| K4 | perturbation slope −0.835 vs −0.013 | ✔ | ✅ khớp tuyệt đối | **Đúng nhưng thiếu CI/p** |
| K5 | Table VI (N=1000) vs Table IV (N=1000) | 0.813 vs 0.854 | ✅ | **Không mâu thuẫn — chỉ khác test set** |

---

## K1 — Table VI tái tạo được, nhưng nền tảng quá mỏng

Từ `c6_results.json`:

| N | QSVM | SVM-RBF | SVM-Poly | SVM-Linear | Δ vs RBF | Δ vs best | best |
|---:|---:|---:|---:|---:|---:|---:|---|
| 100 | 0.8132 | 0.7240 | 0.7008 | 0.7331 | +0.0893 | **+0.0801** | SVM-Linear |
| 200 | 0.7973 | 0.7431 | 0.7537 | 0.7583 | +0.0542 | **+0.0390** | SVM-Linear |
| 500 | 0.8311 | 0.7310 | 0.7262 | 0.7646 | +0.1001 | **+0.0665** | SVM-Linear |
| 1000 | 0.8128 | 0.7289 | 0.7434 | 0.7370 | +0.0839 | **+0.0694** | SVM-Poly |

→ khớp 100% với Table VI (0.813 / 0.797 / 0.831 / 0.813 và Δ = +0.080 / +0.039 / +0.066 / +0.069).

**Nhưng** `c6_results.json → config` cho thấy:
- `random_state: 42` — **1 seed duy nhất**, không có CI, không có test thống kê
- `c_qsvm: 1.0`, `c_svm: 0.1` — QSVM không được tune (đúng lỗi R1-3 / R4-5)
- chỉ 3 baseline SVM — **không có QSVM-Z, RF, XGBoost**

⇒ Con số đúng, nhưng **không đủ chuẩn** cho R2-3 (thống kê) và R1-5 (baseline). Phải chạy lại toàn bộ.

---

## K2 — *"+6.7 points over SVM-RBF on the rare-attack subset"*: sai ở ba chỗ cùng lúc

Câu trong bài (Sec. V-D):
> *"At N=500 QSVM-ZZ still leads by +6.7 points over SVM-RBF on the rare-attack subset, with a Cohen's d of +0.68 on the per-sample decision margins."*

| Lỗi | Chi tiết |
|---|---|
| **(a) Sai đối tượng so sánh** | `+6.7` = `0.0665` = Δ vs **SVM-Linear** (baseline mạnh nhất), chính là ô cuối cột N=500 của dòng "Δ vs best" trong Table VI. So với **SVM-RBF** thì khoảng cách là **+10.0 points**, không phải +6.7. |
| **(b) Sai tập dữ liệu** | `0.0665` được tính trên **toàn bộ 22,544 mẫu KDDTest+**, không phải trên rare subset. |
| **(c) Không có số hậu thuẫn** | **Không có bất kỳ artifact nào trong repo chứa F1 (hoặc recall) trên rare subset ở N=500.** `c6_results.json` chỉ có margin, không có metric phân loại theo rare subset. |

⇒ Câu này lấy con số của một phép so sánh (toàn tập, vs SVM-Linear) và gán cho một phép so sánh khác (rare subset, vs SVM-RBF). **Không thể bảo vệ trong rebuttal.** Phải tính rare-subset F1 thật rồi viết lại.

---

## K3 — *"Cohen's d of +0.68"*: không tái tạo được, và có dấu hiệu sai dấu

### Số thật của C6 tại N=500

`c6_results.json → statistical_tests.cohens_d_n500_rare_classes`:

```
n_rare_test_samples = 2952   (U2R ∪ R2L trong KDDTest+)
QSVM |margin| = 0.6538 ± 0.4674
RBF  |margin| = 0.5070 ± 0.2126
pooled std    = 0.3631
Cohen's d     = +0.4043      ← số thật của C6
```

### Truy tìm nguồn của `+0.68` — hai ứng viên, không cái nào khớp

| Ứng viên | Giá trị | Vấn đề |
|---|---:|---|
| (a) `c5_results.json → statistical_tests.cohens_d_margin_rare` | **−0.68048** | Cùng độ lớn nhưng **ngược dấu**. Và đến từ **thí nghiệm khác**: C5 calibration với `train_size=99, test_size=99, n_rare_test=**10**` — không phải N=500 với 2,952 mẫu rare. |
| (b) Glass's Δ trên chính dữ liệu C6 (dùng std của RBF làm control thay vì pooled std) | **+0.6905** | Ra ≈ 0.69, gần 0.68, nhưng đây **không phải Cohen's d** và bài không khai báo dùng Glass's Δ. |

### Bằng chứng nội bộ cho thấy dấu là vấn đề đã biết

Notebook `c5_confidence_calibration_multirun.ipynb` (cell 22) in ra nguyên văn:

```
if d_mean < 0:
    →  d < 0  ⇒  RBF margin LON HON QSVM trên lop hiem
    →  Narrative cu ('QSVM margin tighter') la SAI DAU → DA SUA.
```

Và C5 multi-run (5 runs) cho:

| run | 1 | 2 | 3 | 4 | 5 | **mean ± std** |
|---|---:|---:|---:|---:|---:|---:|
| `cohens_d_margin_rare` | −0.547 | +0.128 | +0.060 | −0.005 | −0.440 | **−0.161 ± 0.309** |

⇒ Trên nhiều run, hiệu ứng margin rare **về gần 0 và hơi nghiêng về RBF**, chứ không phải +0.68 ủng hộ QSVM.

### Phán quyết

> **`+0.68` không tái tạo được từ bất kỳ artifact nào của repo.** Số gần nhất về độ lớn là `−0.68048` từ một thí nghiệm khác (C5, 10 mẫu rare) và **mang dấu ngược lại**. Số đúng theo protocol mà bài mô tả (C6, N=500, 2,952 mẫu rare) là **+0.4043**.
>
> Đây là con số xuất hiện **hai lần** trong bản nộp (Sec. V-D và một thanh trong Fig 10). **Cả hai đều phải sửa.**

---

## 🔴 K3b — Lỗi phương pháp nghiêm trọng hơn cả con số: dùng |margin| thay vì signed margin

Cả C5 và C6 đều tính effect size trên **giá trị tuyệt đối** của decision function:

```python
qsvm_margins = np.abs(qsvm_500.decision_function(X_te_500[rare_mask]))   # c6, cell 11
rbf_margins  = np.abs(rbf_500.decision_function(X_te_500[rare_mask]))
```

**Vì sao đây là lỗi:** `|f(x)|` lớn chỉ có nghĩa là model **tự tin**, không có nghĩa là model **đúng**. Trên U2R/R2L — lớp mà cả hai model đều sai rất nhiều — một `|margin|` lớn hơn hoàn toàn có thể là **sai một cách tự tin hơn**. Do đó `d = +0.4043` **không phải bằng chứng** rằng QSVM tốt hơn trên rare attack.

Đại lượng đúng là **signed margin** `y · f(x)`: dương = nằm đúng phía biên, và độ lớn mới mang nghĩa "biên an toàn".

> [!danger] Đây là loại lỗi reviewer TETC sẽ bắt
> R4 đã nghi ngờ đúng chỗ khi nói *"I don't know if I see any number for the rare-attack subset, so it is not possible to verify the paper's claim"*. Nếu ta chỉ sửa `0.68 → 0.4043` mà giữ nguyên `|margin|`, reviewer đọc code sẽ phát hiện và tình hình còn tệ hơn.

**Hành động cho C4 (đã đưa vào protocol S0.2):**
1. **Primary**: signed margin `y·f(x)`, Cohen's d với pooled std, bootstrap CI.
2. **Secondary**: `|margin|` — chỉ để bắc cầu với con số cũ và nói rõ nó đo cái gì.
3. **Bắt buộc thêm**: `F1_rare` và `recall_rare` — để câu "leads by X points on the rare-attack subset" **thực sự có số đứng sau**.

---

## K4 — Slope perturbation: đúng, nhưng thiếu thống kê

`results/nslkdd/c4_multirun/degradation_slope_summary.csv`:

| Model | slope_mean | slope_std |
|---|---:|---:|
| QSVM (ZZ) | **−0.8354** | 0.1611 |
| SVM-RBF (mm) | **−0.0127** | 0.0527 |
| SVM-RBF (std) | −0.2291 | 0.0468 |
| SVM-Poly2 (mm) | +0.0433 | 0.0346 |
| SVM-Linear (mm) | −0.0234 | 0.0135 |

→ khớp chính xác con số −0.835 và −0.013 trong Sec. VI-B. **Số đúng.**
→ Nhưng chỉ có mean ± std, **không CI, không p-value** — đúng điều R2-4 phàn nàn. Đã được `C3_revision` thay thế bằng bản có CI/Wilcoxon/d_z/Holm. Không thuộc phạm vi C4.

---

## K5 — Table IV vs Table VI: không mâu thuẫn

| | Table IV (C2) | Table VI (C4) |
|---|---|---|
| N_train | 1000 | 1000 |
| **N_test** | **300** | **22,544 (full KDDTest+)** |
| Pipeline | fit trên train đầy đủ | **re-fit trên đúng 1000 dòng** |
| QSVM-ZZ F1 | **0.854** | **0.813** |

⇒ Hai giao thức đánh giá khác nhau, không phải lỗi. Nhưng bản nộp **không nói rõ ở caption**, nên R1 đọc thành mâu thuẫn. Cách xử lý ở S5.1: báo cáo **cả hai test set ở mọi N**, để chênh lệch tự hiện ra bằng số.

---

## Tổng kết S0.1

| Hạng mục | Kết luận |
|---|---|
| Số tái tạo được | K1 (Table VI), K4 (slope), K5 (chênh lệch test set) |
| Số **sai** phải thay | K2 (`+6.7 ... vs SVM-RBF ... rare subset`) |
| Số **không tái tạo được** phải thay | K3 (`d = +0.68`) — số thật là +0.4043 dưới |margin|, và −0.161 ± 0.309 trên nhiều run của C5 |
| Lỗi **phương pháp** phải sửa | K3b — dùng `|margin|` thay vì signed margin; thiếu hoàn toàn metric phân loại trên rare subset |

**Hệ quả cho rebuttal:** không thể trả lời R4-4 bằng cách "bổ sung bảng số cho claim cũ". Phải **thừa nhận claim cũ sai**, đưa ra số mới có bảng đầy đủ, và nói rõ đã đổi định nghĩa margin vì lý do phương pháp. Đây là cách duy nhất an toàn — reviewer TETC có thể đọc code trong repo public.
