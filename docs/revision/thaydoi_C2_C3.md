# Báo cáo thay đổi C2 / C3 — sửa reproducibility

> Gửi Quang Anh · 2026-09-01 · Người thực hiện: Quan
> Toàn bộ số cũ vẫn nằm trong git (commit `d397961`), có thể `git checkout` lại bất cứ lúc nào.

---

## TL;DR

| | |
|---|---|
| Sửa | 4 dòng code trong 2 notebook |
| Kết quả chính của C2 (ZZ vs Z) | **KHÔNG ĐỔI** — ΔF1, CI, p, d_z giống hệt |
| Verdict của C3 | **1/36 ô đổi**: prior 70% vs XGBoost, `classical-favorable` → `inconclusive` |
| Việc còn dở | Phần noise của C2 **không chạy được trên máy m** (MemoryError) — cần m chạy lại |

---

## 1. Đã sửa gì

| # | File | Chỗ sửa | Vì sao |
|---|---|---|---|
| 1 | `C2_revision.ipynb` cell 11 | XGBoost tuning: `n_jobs=-1` → `n_jobs=1` | `tree_method='hist'` gộp histogram theo thứ tự thread → kết quả phụ thuộc số core của máy |
| 2 | `C2_revision.ipynb` cell 17 | XGBoost trong `make_baseline_models`: `n_jobs=-1` → `n_jobs=1` | như trên |
| 3 | `C2_revision.ipynb` cell 31 | `transpile(..., optimization_level=1)` → thêm `seed_transpiler=42` | `optimization_level=1` dùng Sabre (ngẫu nhiên) → circuit khác nhau mỗi lần chạy |
| 4 | `C3_revision.ipynb` cell 9 | XGBoost trong `make_models`: `n_jobs=-1` → `n_jobs=1` | như #1 |
| 5 | `pyproject.toml` | thêm `qiskit-aer==0.17.2`, `qiskit-ibm-runtime==0.49.0` | đang thiếu → `uv sync` xong không chạy được phần noise |

RandomForest **giữ nguyên** `n_jobs=-1`: đã kiểm chứng nó tất định (khớp chính xác 10/10 run).

---

## 2. Bằng chứng cho việc sửa #1–#2

Cùng seed, cùng dữ liệu, cùng tham số, C2 run 1, máy 16 core:

| cấu hình | F1 |
|---|---:|
| `n_jobs=-1` (m dùng) | 0.836520 |
| `n_jobs=1` | 0.853307 |
| số m lưu trong `c2_per_run.csv` | 0.856627 |

Lặp lại trên **cùng** máy thì giống hệt → không phải lỗi seed, mà là phụ thuộc số thread.

---

## 3. C2 sau khi sửa

### 3.1 Kết quả chính KHÔNG đổi

| | cũ | mới |
|---|---|---|
| ΔF1 (ZZ − Z) | +0.011360, CI [−0.005408, 0.028128], p=0.2324, d_z=0.4846 | **giống hệt** |
| ΔKTA (ZZ − Z) | +0.137807, CI [0.126738, 0.148876], p=0.001953, d_z=8.906 | **giống hệt** |

### 3.2 Bảng baseline

| Model | mean cũ | mean mới | Δ |
|---|---:|---:|---:|
| SVM_Linear | 0.813655 | 0.813655 | 0 |
| SVM_Poly2 | 0.832326 | **0.832657** | +0.000331 |
| SVM_RBF | 0.836186 | 0.836186 | 0 |
| RandomForest | 0.844636 | 0.844636 | 0 |
| XGBoost | 0.851625 | **0.850310** | −0.001315 |

Thứ hạng không đổi: **XGB > QSVM-ZZ (0.846888) > RF > RBF > Z > Poly2 > Linear**.
CI của XGBoost hẹp lại: [0.8396, 0.8637] → [0.8412, 0.8595].

### 3.3 XGBoost từng run

| run | cũ | mới | Δ |
|---:|---:|---:|---:|
| 1 | 0.856627 | 0.853307 | −0.003320 |
| 2 | 0.856652 | 0.856627 | −0.000025 |
| 3 | 0.849958 | 0.843318 | −0.006641 |
| 4 | 0.846660 | 0.856665 | +0.010005 |
| 5 | 0.826659 | 0.833304 | +0.006645 |
| 6 | 0.846639 | 0.859975 | +0.013336 |
| 7 | 0.873283 | 0.863320 | −0.009963 |
| 8 | 0.839993 | 0.839993 | 0 |
| 9 | 0.836665 | 0.829983 | −0.006682 |
| 10 | 0.883114 | 0.866613 | −0.016501 |

Hyperparameter XGBoost được chọn **không đổi** (lr=0.1, depth=5, n=500, subsample=0.8), chỉ điểm CV nhích 0.9349 → 0.9374. Nên hợp đồng đóng băng mà C3/C4 kế thừa vẫn y nguyên.

### 3.4 `SVM_Poly2` run 3 — ô cũ không tái tạo được, giờ đã sạch

Trước: `c2_per_run.csv` ghi **0.819928**. Tôi tính lại độc lập ra **0.823237**, quét hết `C ∈ {0.1…10}` × {StandardScaler, MinMax} × {degree 2, 3} không cấu hình nào ra 0.819928. Sau khi chạy lại, ô này ra **0.823237** — khớp với tính toán độc lập.

Nghi nguyên nhân: cache cũ sinh ra dưới scikit-learn **1.7.2** (artifact joblib báo `InconsistentVersionWarning`) trong khi `pyproject.toml` ghim **1.8.0**. `config_signature` chỉ băm `C2_CONFIG` chứ không băm hyperparameter đã tune lẫn hash artifact C1 nên cache không tự invalid.

---

## 4. C3 sau khi sửa — chỗ quan trọng nhất

**36 ô so sánh, đúng 1 ô đổi verdict:**

| Regime | Baseline | mean_delta cũ → mới | holm_p cũ → mới | Verdict |
|---|---|---|---|---|
| prior_shift / attack_70pct | XGBoost | −0.0253 → −0.0229 | **0.0273 → 0.0977** | **classical-favorable → inconclusive** |

Toàn bộ 35 ô còn lại giữ nguyên verdict. Ô `perturbation / all_sigma_slope` vs XGBoost vẫn `classical-favorable` rất vững (holm_p = 0.0039, d_z = −2.6 → −2.8).

### Ý nghĩa

Đây là verdict **duy nhất** trong C3 nói *"XGBoost thắng QSVM-ZZ có ý nghĩa thống kê"*. Nó không sống sót khi XGBoost tất định.

Không phải `n_jobs=1` "đúng hơn" `n_jobs=-1`. Vấn đề là kết quả nằm sát ranh giới đến mức **một artifact về số thread quyết định verdict**. Dù chọn cấu hình nào, ô này phải được báo cáo là **không robust**.

Ảnh hưởng: Fig 10 (regime map) và luận điểm *"advantage phụ thuộc lớp comparator"* — vốn đang dựa chính vào ô này.

### Các con số khác của C3

- Model không phải XGBoost: **0 ô đổi verdict**.
- 8/220 ô per-run của QSVM lệch ~0.001 (đúng 1 mẫu trên 1000 bị lật). Nguyên nhân: tie ở biên libsvm — support vector nằm đúng trên margin bị lật do chênh lệch ~1e-15, cộng với việc artifact cũ pickle bằng sklearn 1.7.2 còn môi trường hiện tại là 1.8.0. Không ô nào đổi verdict.

---

## 5. ⚠️ Việc còn dở — phần noise của C2 KHÔNG chạy được trên máy tôi

Sau khi sửa, chạy lại C2 thì mục `realistic_noisy_simulator` **fail**:

```
reason     : AlgorithmError('Sampler job failed!')
root_cause : MemoryError('bad allocation')
ERROR: Failed to load circuits: bad allocation
```

Máy tôi: 16 GB RAM (lúc chạy còn trống ~5 GB).

Đã thử và **không** giải quyết được:
- `max_parallel_experiments=1` → vẫn fail sau 115s
- `max_memory_mb=2048` → vẫn fail sau 117s

Lý do hai cách trên vô dụng: lỗi xảy ra ở khâu **nạp circuit**, trước khi mô phỏng. `kta_sample_size=200` sinh 200×199/2 = **19,900 cặp circuit** nộp trong **một** job Aer.

Đo được ngưỡng:

| n | số cặp | kết quả |
|---:|---:|---|
| 25 | 300 | OK, 2.5s |
| 50 | 1,225 | OK, 12.5s |
| 100 | 4,950 | OK, 99s |
| **200** | **19,900** | **MemoryError** |

### Hệ quả

`c2_summary.json` giờ báo `status: FAIL`, `realistic_noise_validation: false`, và `c2_noise_validation.csv` có dòng `realistic_noisy_simulator = SKIPPED`. Ba điều kiện ideal/finite-shot vẫn chạy bình thường.

**Số noise cũ của m vẫn còn nguyên trong git** (commit `d397961`) — không mất gì.

### Cần m làm

Chọn một trong hai:

**(a)** M chạy lại C2 trên máy m (đã có `seed_transpiler=42`) để phần noise có số tất định. Lưu ý transpile của m trước đây không seed nên note ghi *depth 70 / 48 CX* còn artifact lại là *depth 59 / 44 CX* — sau khi seed thì cố định ở **depth 59 / 44 CX**.

**(b)** Cho phép tôi sửa `noise_validation()` thành **đánh giá theo khối** (chia 200×200 thành các khối 50×50, mỗi job ≤ 1,225 cặp). Tôi đang test hướng này. Ưu điểm: reviewer máy 16 GB cũng chạy được — đúng cái R4-2 đòi. Nhược điểm: chia khối làm đổi chuỗi shot-noise nên **số sẽ lệch nhẹ** so với bản của m, phải chạy lại và cập nhật note.

Ý tôi nghiêng về **(b)** vì nó biến thí nghiệm noise thành thứ ai cũng tái tạo được, nhưng đây là phần của m nên m quyết.

---

## 6. Tóm tắt cần m xác nhận

1. C1/C2/C3 đã frozen chưa — tôi có được phép sửa tiếp không?
2. Phần noise: chọn (a) m tự chạy, hay (b) tôi sửa thành chia khối?
3. Note C2 của m cần cập nhật: XGBoost mean 0.851625 → 0.850310, Poly2 0.832326 → 0.832657, transpile depth 70/48 CX → 59/44 CX.
4. Note C3 của m cần cập nhật: bỏ verdict *"XGB thắng ZZ ở prior 70%"*, đổi thành inconclusive.
