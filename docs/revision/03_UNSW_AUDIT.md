# Giai đoạn 7 — Kiểm kê UNSW-NB15 và chốt phạm vi

> Ngày: 2026-09-02 · Đóng item: **R1-2**, **AE-4** (dataset thứ hai)
> Nguyên tắc: chỉ ghi số kiểm chứng được; cái gì chưa kiểm chứng thì ghi rõ.

---

# 1. Hiện trạng dữ liệu

## 1.1 Kích thước và phân bố

| | Train | Test |
|---|---:|---:|
| Số hàng | **175,341** | **82,332** |
| Số cột | 189 (186 feature + 3 nhãn) | 189 |
| Normal | 31.9% | **44.9%** |
| Rare (Worms + Shellcode + Backdoor + Analysis) | **2.86%** | **2.04%** |
| Số lớp | 10 | 10 |

Phân bố lớp đầy đủ (train): Normal 31.9% · Generic 22.8% · Exploits 19.0% · Fuzzers 10.4% ·
DoS 7.0% · Reconnaissance 6.0% · Analysis 1.14% · Backdoor 1.00% · Shellcode 0.65% ·
Worms 0.074%.

> **Có prior shift sẵn trong dataset**: tỉ lệ Normal đi từ 31.9% (train) lên 44.9% (test).
> Song song với NSL-KDD (53.5% → 43.1%) nhưng ngược chiều — điểm đáng khai thác.

## 1.2 ✅ Tiền xử lý SẠCH — không rò rỉ

Đã kiểm tra mã của cả ba notebook:

| Bước | Cách fit | Kết luận |
|---|---|---|
| `get_dummies` (proto, service, state) | riêng train/test | ✓ |
| `MinMaxScaler` | `fit_transform(train)` / `transform(test)` | ✓ |
| `SelectKBest(f_classif)` | `fit_transform(X_train, y_train)` | ✓ |
| `PCA(4)` | `fit_transform(X_train)` | ✓ |
| `MinMaxScaler(0, π)` | `fit(X_train_pca)` | ✓ |

Không có NaN, không có Inf, không có cột hằng số. Giá trị đã chuẩn hoá về [0, 1].

---

# 2. 🔴 Phát hiện 13 — UNSW-NB15 có trùng lặp dữ liệu ở mức rất cao

Đây là phát hiện quan trọng nhất của giai đoạn kiểm kê, và **phải được khai trong bài**.

| | Số hàng | Chữ ký duy nhất | Trùng lặp nội bộ |
|---|---:|---:|---:|
| Train (đã xử lý) | 175,341 | 92,357 | **47.3%** |
| Test (đã xử lý) | 82,332 | 48,353 | **41.3%** |

Và nghiêm trọng hơn:

| | Hàng test có bản sao **chính xác** trong train |
|---|---:|
| **UNSW-NB15** | **20,561 / 82,332 = 24.97%** |
| NSL-KDD (để so sánh) | 610 / 22,544 = 2.71% |

## 2.1 Đây là thuộc tính của dataset, không phải lỗi của nhóm

Kiểm tra trên **dữ liệu thô** (`data/unsw/raw/`, trước mọi tiền xử lý), chỉ dùng 34 feature gốc:

| | Trùng lặp nội bộ | Test có bản sao trong train |
|---|---:|---:|
| Raw train | 47.5% | — |
| Raw test | 41.4% | **20,851 / 82,332 = 25.33%** |

Con số raw (25.33%) khớp con số đã xử lý (24.97%) ⇒ **trùng lặp có sẵn trong UNSW-NB15**,
không do `get_dummies` hay làm tròn của MinMaxScaler sinh ra.

## 2.2 Hệ quả bắt buộc phải nêu

**Một phần tư tập test UNSW có thể được "thuộc lòng" từ tập train.** Mọi con số accuracy/F1
trên UNSW — của nhóm và của mọi công trình khác — đều được nâng lên bởi hiệu ứng này.

Điều này **không làm hỏng** so sánh giữa các model (tất cả cùng chịu), nhưng:

1. Phải ghi vào Limitations.
2. Nên báo cáo thêm một biến thể **de-duplicated test** (loại 20,561 hàng trùng) làm kiểm chứng
   phụ — đây sẽ là một điểm cộng lớn về mức độ cẩn thận, và chưa thấy công trình QSVM-IDS nào làm.

---

# 3. 🔴 Phát hiện 14 — Dữ liệu UNSW cũ làm giàu lớp hiếm gấp 7 lần, và không nhất quán

| Tập | n | Normal | **Rare (4 lớp)** |
|---|---:|---:|---:|
| Train đầy đủ | 175,341 | 31.9% | **2.86%** |
| `multi_run/train_run{1..5}` | **100** | 26.0% | **20.00%** |
| `UNSW_Train_Sample100` | 96 | 27.1% | 20.83% |
| `UNSW_Train_Sample500` | 496 | 26.4% | 20.16% |
| `UNSW_Train_Sample1000` | 997 | 29.0% | **12.04%** |

Hai vấn đề:

1. **Làm giàu gấp ~7 lần** (20% so với 2.86% tự nhiên) — cùng loại vấn đề đã phát hiện ở
   NSL-KDD (Phát hiện 4), nhưng mạnh hơn.
2. **Không nhất quán giữa các mốc N**: 20.8% ở N=100 nhưng 12.0% ở N=1000. Nghĩa là đường
   learning curve dựng từ các file này sẽ trộn lẫn "thêm dữ liệu" với "đổi thành phần lớp" —
   đúng lỗi đã sửa ở C4 NSL-KDD.

⇒ Bắt buộc dựng lại tập con theo **hai chế độ `matched` / `natural` lồng nhau** như C4 NSL-KDD.

---

# 4. Khoảng cách giữa UNSW hiện có và chuẩn mới

| Hạng mục | UNSW hiện tại (05/2026) | Chuẩn C2/C3/C4 mới | Phải làm lại? |
|---|---|---|:--:|
| N_train | **100** | 1,000 (+ sweep tới 10,000) | ✅ |
| Số run | 5 | **10** | ✅ |
| Số model | 4 (QSVM + 3 SVM) | **7** (thêm Z, RF, XGB) | ✅ |
| Tuning | `C=1.0` "neutral", không có tuning set | tuning set riêng, 1-SE, **7 model tại mỗi (N, run)** | ✅ |
| Chọn n | **áp đặt n=4** từ NSL-KDD (`n_pca_fixed: 4`) | luật 3 tầng của C1 chạy độc lập | ✅ |
| Chọn K | K=35 (elbow CV) nhưng C1-sweep lại chốt K=80 — **không nhất quán** | chốt lại một lần | ✅ |
| Test set | subsample 100–300 mẫu | **full 82,332** + subset cố định | ✅ |
| Thành phần lớp | làm giàu 7×, không nhất quán | 2 chế độ lồng nhau, khai báo rõ | ✅ |
| Thống kê | mean ± std, McNemar | paired Δ, CI, Wilcoxon, d_z, Holm | ✅ |
| Noise validation | không có | — | ❌ không cần (C2 đã làm trên NSL-KDD) |
| Temporal shift | không có | — | ❌ UNSW không có split thời gian |

**Kết luận: gần như phải chạy lại toàn bộ.** Phần tái sử dụng được:

- ✅ `UNSW_Train_Cleaned.parquet` / `UNSW_Test_Cleaned.parquet` — tiền xử lý sạch, dùng lại được
- ✅ Đường cong CV chọn K (`unsw_selectkbest_cv_results.csv`) — làm tham chiếu
- ❌ Mọi file `multi_run/`, `Sample*`, `results/unsw/*.json`, `models/unsw/qsvm_cache` — bỏ

---

# 5. Điểm cộng khoa học lớn nhất của UNSW: kiểm chứng C1 là **thủ tục**, không phải con số

Toàn bộ công việc UNSW cũ đặt `n_pca_fixed = 4`, tức **mượn thẳng con số của NSL-KDD**.

Nếu chạy luật 3 tầng của C1 độc lập trên UNSW:

```
V(n) ≥ 85%  →  KTA(n) ≥ 95%·KTA_max trong vùng feasible  →  min Q(n)  →  n*_UNSW
```

thì có hai khả năng, **cả hai đều tốt cho bài**:

- `n*_UNSW = 4` → thủ tục cho cùng kết quả trên hai dataset độc lập, củng cố C1.
- `n*_UNSW ≠ 4` → **chứng minh C1 là một thủ tục có thể chuyển giao**, không phải một hằng số
  gán tay. Đây chính là câu trả lời cho **R3-1** (chê novelty thấp): đóng góp nằm ở
  *phương pháp lựa chọn*, không ở *cấu hình được chọn*.

Đây là lý do U1 phải chạy trước, vì `n*` quyết định mọi thứ phía sau.

---

# 6. Phạm vi đã chốt

## Sẽ làm

| ID | Nội dung | Đóng item |
|---|---|---|
| **U1** | Chạy luật 3 tầng C1 trên UNSW độc lập → `n*`, `K*` | R3-1, R1-2 |
| **U2** | Tuning set riêng + tune đối xứng 7 model | R1-3, R4-5 |
| **U3** | **Sample-complexity sweep** — 2 chế độ, 10 run, 7 model, test đầy đủ 82,332 | **R1-7**, R1-2, AE-4 |
| **U4** | Rare-attack (Worms/Shellcode/Backdoor/Analysis), signed margin + F1/recall | R4-4 |
| **U5** | Kiểm chứng phụ trên **test đã khử trùng lặp** (bỏ 20,561 hàng) | mới — điểm cộng |
| **U6** | Prior-shift (nếu còn thời gian) | R1-2 |

**Câu hỏi khoa học trung tâm của U3**: *crossover tìm được trên NSL-KDD ở N≈2000–5000 có
chuyển giao sang UNSW không?* Đây là phép thử tổng quát hoá trực tiếp nhất cho phát hiện chính
của C4, và trả lời đúng cái AE-4 đòi.

## Sẽ KHÔNG làm — và lý do

| Bỏ | Lý do |
|---|---|
| Noise validation trên UNSW | C2 đã làm trên NSL-KDD; lặp lại chỉ tốn trang, không trả lời objection mới |
| Temporal shift | UNSW-NB15 không có split theo thời gian như KDDTest-21 |
| Calibration / ECE | thuộc Paper 2, tránh trùng lặp |
| CatBoost / deep tabular | đã chốt giữ 7 model cho đồng bộ C2/C3/C4 |

---

# 7. Ước tính chi phí

Statevector: 0.84 ms/mẫu. Test UNSW 82,332 mẫu → **69 s** mỗi (N, run, kernel, representation).

| Phần | Ước tính |
|---|---:|
| U3 chế độ `natural` (7 N × 10 run × 2 kernel) | ~2.7 h |
| U3 chế độ `matched` (5 N × 10 run × 2 kernel) | ~1.9 h |
| Statevector train + tuning + fit + U1/U2/U4/U5 | ~2 h |
| **Tổng** | **~7 h** (chạy nền được) |

Bộ nhớ: Gram test 82,332 × N. Với N=10,000 là 6.6 GB float64 → **bắt buộc dùng dự đoán theo lô**
(`quantum_predict_chunked` đã có sẵn trong `runners/run_c4.py`, lô 4,000 dòng ≈ 320 MB).

---

# 8. Việc cần làm trước khi chạy U3

1. **U1 trước** — `n*` quyết định toàn bộ phía sau.
2. Mở rộng `src/c4_pipeline.py` để nhận dataset UNSW (đường dẫn, nhãn 4 lớp rare khác, số
   feature khác). Không viết lại từ đầu — tham số hoá phần nạp dữ liệu.
3. Định nghĩa nhãn phân tầng cho UNSW. NSL-KDD dùng 4 lớp `{Normal, DoS, Probe, Rare}`.
   UNSW có 10 lớp; đề xuất gộp thành 5: `{Normal, Generic, Exploits, Other-frequent, Rare}`
   với `Rare = Worms ∪ Shellcode ∪ Backdoor ∪ Analysis` (2.86% train, 2.04% test).
4. Thêm `results/unsw/c4_revision/cache/` vào `.gitignore` (đã có sẵn từ Giai đoạn 0).
