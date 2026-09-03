# Những chỗ t đã chỉnh trong C2 / C3 + lý do

> M xem giúp, thấy chỗ nào không ổn thì nói, t revert được hết (chưa commit gì).
> **Khoan chạy lại C2 đã** — t đang chạy dở với mấy chỉnh này, m chạy bản cũ là hai đứa đè nhau.

---

## 1. `C2_revision.ipynb` cell 11 — XGBoost tuning: `n_jobs=-1` → `n_jobs=1`

**Lý do:** `tree_method='hist'` gộp histogram theo thứ tự thread, nên kết quả phụ thuộc **số core của máy chạy**, không chỉ phụ thuộc seed.

**Bằng chứng** — cùng seed, cùng data, cùng tham số, C2 run 1, máy t 16 core:

| cấu hình | F1 |
|---|---:|
| `n_jobs=-1` (bản của m) | 0.836520 |
| `n_jobs=1` | 0.853307 |
| số m lưu trong `c2_per_run.csv` | 0.856627 |

Chạy lại **cùng** máy thì giống hệt → không phải seed, mà là thread.

Cách t phát hiện: dựng lại pipeline độc lập rồi đối chiếu từng ô với `c2_per_run.csv`:

| Model | Khớp chính xác |
|---|---|
| QSVM_ZZ, QSVM_Z, SVM_Linear, SVM_RBF, RandomForest | **10/10 run, chênh 0.00e+00** |
| SVM_Poly2 | 9/10 (lệch mỗi run 3) |
| XGBoost | **0/10** |

6/7 model khớp tới chữ số cuối nên pipeline t đúng, riêng XGBoost lệch cả 10 run.

---

## 2. `C2_revision.ipynb` cell 17 — XGBoost trong `make_baseline_models`: `n_jobs=-1` → `n_jobs=1`

**Lý do:** như trên. Đây là chỗ chạy 10 run chính.

RandomForest t **giữ nguyên** `n_jobs=-1` — đã kiểm chứng nó tất định (khớp chính xác 10/10 run), không cần đụng.

---

## 3. `C3_revision.ipynb` cell 9 — XGBoost trong `make_models`: `n_jobs=-1` → `n_jobs=1`

**Lý do:** như trên.

**Đây là chỗ quan trọng nhất.** Chạy lại C3 với `n_jobs=1`, trong 36 ô so sánh có **đúng 1 ô đổi verdict**:

| Regime | Baseline | holm_p | Verdict |
|---|---|---|---|
| prior_shift / attack_70pct | XGBoost | **0.0273 → 0.0977** | classical-favorable → **inconclusive** |

Đây là verdict **duy nhất** trong C3 nói *"XGBoost thắng QSVM-ZZ có ý nghĩa thống kê"*. Nó không sống sót khi XGBoost tất định.

Ý t không phải `n_jobs=1` đúng hơn `n_jobs=-1`. Vấn đề là ô này nằm sát ranh giới đến mức **một artifact về số thread quyết định verdict** — nên dù chọn cấu hình nào, mình cũng phải báo cáo nó là không robust. Ảnh hưởng thẳng Fig 10 và luận điểm "advantage phụ thuộc lớp comparator".

35 ô còn lại giữ nguyên verdict.

---

## 4. `C2_revision.ipynb` cell 31 — `transpile(...)` thêm `seed_transpiler=42`

**Lý do:** đúng như m nói, chưa seed. `optimization_level=1` dùng Sabre (ngẫu nhiên) nên mỗi lần chạy ra circuit khác.

Đây cũng là lý do note ghi *depth 70 / 48 CX* còn `c2_noise_backend_transpile.json` lại là *depth 59 / 44 CX*. Sau khi seed thì cố định ở **depth 59 / 44 CX**.

---

## 5. `C2_revision.ipynb` cell 31 — thêm hàm `evaluate_in_blocks()` cho phần noise

**Lý do:** sau khi sửa, chạy lại C2 thì `realistic_noisy_simulator` **fail trên máy t**:

```
MemoryError('bad allocation')
ERROR: Failed to load circuits: bad allocation
```

`kta_sample_size=200` sinh 200×199/2 = **19.900 cặp circuit** nộp trong **một** job Aer. Lỗi nằm ở khâu **nạp circuit**, chưa tới mô phỏng — nên `max_parallel_experiments=1` và `max_memory_mb` đều vô dụng (t đã thử, vẫn fail sau ~115s).

Ngưỡng t đo được:

| n | số cặp | kết quả |
|---:|---:|---|
| 50 | 1.225 | OK 12.5s |
| 100 | 4.950 | OK 99s |
| **200** | **19.900** | **MemoryError** |

**Cách sửa:** chia Gram thành khối 50×50, mỗi job ≤ 2.500 cặp. Test riêng: 200×200 chạy **374s, RAM đỉnh 721 MB**, ma trận đối xứng và PSD sẵn. Chạy lại C2 thì `status` quay về **PASS**, `realistic_noise_validation: true`.

**Kết quả noise sau khi sửa — kết luận không đổi:**

| Điều kiện | Model | KTA cũ → mới | D_F cũ → mới |
|---|---|---:|---:|
| ideal_statevector | ZZ | 0.196472 → 0.196472 | 0 |
| ideal_statevector | Z | 0.073744 → 0.073744 | 0 |
| ideal_finite_shot | ZZ | 0.194360 → 0.194787 | 0.1229 → 0.1010 |
| ideal_finite_shot | Z | 0.073272 → 0.072569 | 0.0279 → 0.0305 |
| realistic_noisy | ZZ | 0.149988 → **0.149005** | 0.599128 → **0.599557** |
| realistic_noisy | Z | 0.071298 → **0.070874** | 0.165778 → **0.165548** |

Câu chuyện chính giữ nguyên gần như tuyệt đối: KTA của ZZ tụt 0.1965 → 0.1490 dưới noise, còn `D_F` của ZZ (0.5996) lớn gấp ~3.6 lần của Z (0.1655) — khớp footprint 44 CX vs 0 CX.

⚠️ **Đánh đổi phải ghi rõ:** chia khối làm đổi chuỗi shot-noise, nên **số noise sẽ lệch nhẹ** so với bản của m. Đổi lại, phần noise thành thứ máy 16 GB cũng chạy được — đúng cái R4-2 (reproducibility) đòi. M không đồng ý thì revert 3 dòng là xong.

---

## 6. `C2_revision.ipynb` cell 31 — thêm `algorithm_globals.random_seed` vào đầu `noise_validation()`

**Lý do:** phát hiện lúc so kết quả noise cũ/mới — điều kiện `ideal_finite_shot` cũng lệch, mà chỗ đó t không đụng gì. Hoá ra `FidelityStatevectorKernel` **không có tham số seed nào cả**:

```
['self', 'feature_map', 'statevector_type', 'cache_size', 'auto_clear_cache', 'shots', 'enforce_psd']
```

Với `shots` hữu hạn, mỗi lần gọi cho một Gram khác nhau **ngay trên cùng một máy**. T chạy thử 3 lần liên tiếp trên cùng dữ liệu:

| lần | KTA |
|---|---:|
| 1 | 0.043651 |
| 2 | 0.037223 |
| 3 | 0.029919 |

Lệch ±0.014, tức khoảng 30% giá trị. Trong khi `shots=None` (statevector) thì tất định tuyệt đối.

**Cách sửa:** chỉ `algorithm_globals.random_seed` mới khống chế được — đã kiểm chứng 3 lần chạy cho `K[0,1]` giống hệt tới 8 chữ số; `np.random.seed` thì **không** ăn.

Đây là chỗ dòng `ideal_finite_shot` trong bảng noise của mình trước giờ không tái tạo được, kể cả m chạy lại trên chính máy m.

*(Ghi chú: C1 không dính lỗi này vì C1 đi đường `FidelityQuantumKernel` + `StatevectorSampler(seed=...)`, có seed đàng hoàng. Chỉ C2 dùng `FidelityStatevectorKernel(shots=...)`.)*

---

## 7. `pyproject.toml` — thêm `qiskit-aer==0.17.2` + `qiskit-ibm-runtime==0.49.0`

**Lý do:** hai package này đang **thiếu** trong dependency. Reviewer `git clone` → `uv sync` → không chạy được phần noise của m. Mà đó đúng là thí nghiệm đóng R1-6 / R3-4 / AE-6, còn R4-2 thì phàn nàn thẳng về reproducibility. Trúng hai chỗ.

---

## Kết quả sau khi chạy lại

**C2 — kết quả chính ZZ vs Z không đổi một chữ số:**

| | |
|---|---|
| ΔF1 (ZZ−Z) | +0.011360, CI [−0.005408, 0.028128], p=0.2324, d_z=0.4846 |
| ΔKTA (ZZ−Z) | +0.137807, CI [0.126738, 0.148876], p=0.001953, d_z=8.906 |

**C2 — bảng baseline:**

| Model | cũ | mới |
|---|---:|---:|
| SVM_Poly2 | 0.832326 | **0.832657** |
| XGBoost | 0.851625 | **0.850310** |
| 5 model còn lại | — | **y nguyên** |

Thứ hạng không đổi: XGB > QSVM-ZZ (0.846888) > RF > RBF > Z > Poly2 > Linear.
Hyperparameter XGBoost chọn ra cũng **không đổi** (lr=0.1, depth=5, n=500, subsample=0.8) → hợp đồng đóng băng C3/C4 kế thừa vẫn nguyên.

**C3:** 1/36 ô đổi verdict (đã nói ở mục 3). Model không phải XGBoost: 0 ô đổi.

---

## Hai chỗ nhỏ t phát hiện thêm, chưa sửa

**a) `SVM_Poly2` run 3 trong cache C2 không tái tạo được.** `c2_per_run.csv` ghi 0.819928, t tính lại độc lập ra 0.823237. Quét hết `C ∈ {0.1…10}` × {StandardScaler, MinMax} × {degree 2,3} không cấu hình nào ra 0.819928. Sau khi chạy lại thì ô này ra 0.823237, khớp tính toán độc lập.

Nghi do cache cũ sinh dưới **scikit-learn 1.7.2** (artifact joblib báo `InconsistentVersionWarning`) trong khi `pyproject.toml` ghim **1.8.0**. `config_signature` chỉ băm `C2_CONFIG` chứ không băm hyperparameter đã tune lẫn hash artifact C1, nên cache không tự invalid khi tuning đổi.

**b) 8/220 ô per-run của QSVM trong C3 lệch ~0.001** (đúng 1 mẫu trên 1000 bị lật) — tie ở biên libsvm, support vector nằm đúng trên margin bị lật do chênh lệch ~1e-15, cộng với đổi sklearn 1.7.2 → 1.8.0. Không ô nào đổi verdict.

---

## Về ý "C2 khác là do đổi thành 300 sample"

Chỗ đó m nói đúng cho phần **noise** (`noise_f1_test_size` 100 → 300), nhưng nó không giải thích chênh lệch t tìm ra — vì t so trên **bảng chính 10 run, test 300, N=1000**, tức chính `c2_per_run.csv`. Và ở đó 6/7 model khớp tuyệt đối, chỉ mình XGBoost lệch.

---

## Cần m

1. **Khoan chạy lại C2.** Pull trước, hoặc để t chạy xong rồi m review.
2. M double-check C1/C2/C3 rồi thì t coi như frozen và build C4 lên đó nhé?
3. Note C2 cần sửa: XGBoost mean 0.851625 → 0.850310, Poly2 0.832326 → 0.832657, transpile cố định depth 59 / 44 CX.
4. Note C3 cần sửa: bỏ verdict "XGB thắng ZZ ở prior 70%", đổi thành inconclusive.

Bảng số đầy đủ từng run nằm ở `docs/revision/thaydoi_C2_C3.md` trong repo.
