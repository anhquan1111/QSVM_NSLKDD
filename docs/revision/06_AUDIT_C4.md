# Soát bug C4 — báo cáo

*Quan, 2026-09-03. Trả lời yêu cầu của Quang Anh: "còn lại m có thể tự double check bug C4 lại".*

**Kết quả: 96/96 mục PASS.** Chạy lại bằng `python runners/audit_c4.py`.

Không tìm thấy bug nào trong C4. Tìm thấy **2 vấn đề khác** (một khoảng trống artifact, một
cái bẫy diễn giải) và **1 kết quả robustness mới** — chi tiết ở dưới.

---

## 0. Notebook C4 để ở đâu

Câu hỏi của Quang Anh. **C4 không có notebook** — cố ý, và đây là lý do:

C1/C2/C3 mỗi cái chạy một lần trên một cấu hình, notebook là hợp lý. C4 phải quét
**2 dataset × 2 chế độ lấy mẫu × 2 chế độ biểu diễn × 2 arm × 7 giá trị N × 10 run × 7 model**.
Nhét vào notebook thì không đặt được cache, không chạy lại được từng ô, và mỗi lần treo máy
là mất hết. Nên C4 tách thành module + CLI:

| Đường dẫn | Vai trò |
|---|---|
| `src/c4_pipeline.py` | Toàn bộ logic: lấy mẫu lồng nhau, biểu diễn, kernel, tuning, thống kê, gate |
| `runners/run_c4.py` | Chạy thí nghiệm — `--dataset --regime --repr-mode --arms --n-grid --run-ids` |
| `runners/analyze_c4.py` | Sinh learning curve, thống kê ghép cặp, rare-attack, crossover |
| `runners/pairwise_all_arms.py` | **MỚI** — bảng thống kê phủ hết arm/split |
| `runners/audit_c4.py` | **MỚI** — script soát này |
| `runners/make_paper1_figures.py` | Sinh 4 hình cho bản revision |
| `configs/c4_protocol.json` | Protocol đóng băng + `_changelog` |

Kết quả đọc được ở `notebooks/nslkdd/note/C4/*.md` (m đã xem và nói ổn rồi).

Nếu m vẫn muốn có notebook để review/đóng gói supplementary thì t làm một cái mỏng: nạp
artifact đã có, in bảng, vẽ hình, chạy audit — **không train lại**. Nói t một tiếng.

---

## 1. Soát cái gì, soát thế nào

Nguyên tắc: **không gọi lại hàm của `src/c4_pipeline.py` để tính thống kê.** Nếu dùng chính
code đã sinh ra số để kiểm tra số đó thì lỗi chung sẽ lọt. Nên toàn bộ phần thống kê được
viết lại từ đầu bằng `scipy`/`numpy` trong `runners/audit_c4.py`, rồi đối chiếu từng ô với
CSV đã commit.

### A. Thống kê ghép cặp — dựng lại từ per-run thô (6 bộ dữ liệu)

| Kiểm tra | Kết quả |
|---|---|
| Không có dòng `(điều kiện, run, model)` trùng | PASS |
| Mỗi cặp so sánh dùng **đúng cùng tập `run_id`** | PASS |
| Mọi dòng đã công bố đều dựng lại được từ per-run | PASS |
| `mean_delta`, `ci_low`, `ci_high` khớp | PASS — lệch ≤ 9.9e-17 |
| `raw_p` (Wilcoxon), `holm_p` khớp | PASS — lệch **0.0** |
| `effect_size_dz` khớp | PASS — lệch ≤ 1.8e-15 |
| `verdict` khớp | PASS |
| Mọi ô đủ 10 run, không NaN ở cột quyết định | PASS |

> Chỗ t nghi nhất là `pivot_table` mặc định `aggfunc='mean'`: nếu có dòng trùng thì nó **gộp
> im lặng** chứ không báo lỗi. Đã kiểm riêng — không có dòng trùng ở cả 6 bộ. Không phải bug,
> nhưng là mìn nếu sau này ai chạy thêm run mà quên xoá cache.

### B. Gate dữ liệu — chạy lại trên cả 10 run

| Gate | nslkdd/natural | nslkdd/matched | unsw/natural |
|---|---|---|---|
| Train không dính test (rò rỉ) | PASS | PASS | PASS |
| Chuỗi con lồng nhau đúng | PASS | PASS | PASS |
| Mọi N đều có lớp hiếm | PASS | PASS | PASS |

### C. Nhân lượng tử — đường tắt statevector vs Qiskit

Đường tắt dạng đóng nhanh hơn 457–763×; phải chứng minh nó ra **đúng** kết quả Qiskit:

| | 4 qubit | 6 qubit |
|---|---|---|
| ZZFeatureMap | 3.94e-15 | 1.06e-15 |
| ZFeatureMap | 2.66e-15 | 1.94e-15 |

Đúng tới sai số máy. (Sai số 1e-15 là mức tích luỹ float64, không phải xấp xỉ.)

### D. Các khẳng định chính — dựng lại từ per-run thô

| Khẳng định | Kết quả |
|---|---|
| Crossover vs XGBoost đổi dấu **đúng 1 lần** | PASS |
| Đổi dấu nằm trong `N = 2000→5000` | PASS |
| NSL-KDD: **không N nào** QSVM-ZZ thắng SVM-RBF có ý nghĩa | PASS |
| UNSW: QSVM-ZZ thắng SVM-RBF có ý nghĩa tại `N ∈ {2000, 5000, 10000}` | PASS |
| Bản đồ chế độ (khối C4) khớp file nguồn — 42 ô | PASS |

---

## 2. Hai vấn đề tìm thấy (không phải bug C4)

### 2.1 🟡 Khoảng trống artifact — ĐÃ SỬA

`runners/analyze_c4.py` nhận **một** cặp `(arm, test_split)` mỗi lần chạy và **ghi đè**
`c4_pairwise_statistics_{regime}.csv`. Nên file cuối cùng chỉ giữ tuỳ chọn chạy sau cùng:

| File | Phủ | Số dòng |
|---|---|---|
| `..._matched.csv` | 2 arm × 2 split | 120 |
| `..._natural.csv` (NSL) | chỉ `tuned_per_N` × `full_test` | 42 / 168 |
| `..._natural.csv` (UNSW) | chỉ `tuned_per_N` × `full_test` | 36 / 144 |

Dữ liệu per-run có đủ, chỉ thiếu bảng thống kê. Vấn đề là **nhánh `frozen_c2` chính là phép
thử robustness** — crossover có còn khi *không* tune lại siêu tham số tại từng N — mà câu hỏi
đó đang bỏ trống.

Đã thêm `runners/pairwise_all_arms.py` sinh `c4_pairwise_statistics_*_all_arms.csv` phủ hết.
**Không đụng vào file cũ** để không làm hỏng thứ đang dùng.

### 2.2 🔴 Bẫy diễn giải: arm `tuned_once` trên UNSW — ĐỪNG TRÍCH SỐ NÀY

Bảng mới lòi ra `mean_delta` QSVM-ZZ − SVM-RBF = **+0.2223** ở `N=100`, arm `tuned_once`.
Nhìn qua tưởng quantum thắng đậm. Kiểm tra thì không phải:

| `N=100`, UNSW | `tuned_once` | `tuned_per_N` |
|---|---|---|
| SVM-RBF macro-F1 | **0.3635** | 0.6289 |
| SVM-RBF recall_macro | **0.5041** (gần suy biến) | 0.6518 |
| QSVM-ZZ macro-F1 | 0.5858 | 0.5953 |

Siêu tham số tune một lần trên tập tuning lớn **lệch hẳn** khi đem xuống `N=100`: SVM-RBF mất
0.265 F1, còn QSVM-ZZ **chỉ mất 0.010**. Tức arm `tuned_once` phạt SVM-RBF nặng chứ không
phạt QSVM — nó **không phải phép so sánh công bằng ở N nhỏ**.

**Ảnh hưởng tới bài: không có.** Mọi hình và mọi khẳng định đều dùng arm `tuned_per_N`.
Nhưng phải ghi lại, vì đây đúng kiểu số mà người ta vô tình trích ra rồi reviewer bắt được.

---

## 3. Kết quả robustness MỚI — nên đưa vào bài

Có bảng phủ hết arm rồi thì trả lời được câu hỏi robustness. **Crossover xảy ra ở đúng cùng
một chỗ trong cả hai arm, và với cả ba baseline mạnh:**

`mean_delta` QSVM-ZZ − baseline, NSL-KDD `natural`, tập test đầy đủ:

| N | XGB `frozen_c2` | XGB `tuned_per_N` | RF `frozen_c2` | RF `tuned_per_N` | RBF `frozen_c2` | RBF `tuned_per_N` |
|---|---|---|---|---|---|---|
| 100 | −0.0393 | −0.0812 | −0.0242 | −0.0705 | −0.0145 | −0.0307 |
| 1000 | −0.0309 | −0.0289 | −0.0171 | −0.0196 | −0.0021 | −0.0028 |
| 2000 | −0.0134 | −0.0129 | −0.0013 | −0.0059 | −0.0055 | −0.0138 |
| **5000** | **+0.0114** | **+0.0100** | **+0.0103** | **+0.0082** | **+0.0008** | **+0.0026** |
| 10000 | +0.0169 | +0.0149 | +0.0144 | +0.0127 | +0.0092 | +0.0115 |

→ **6/6 đổi dấu tại `2000→5000`.**

Đây là câu trả lời mạnh cho phản biện hiển nhiên nhất: *"crossover chỉ là tạo tác của việc
tune lại siêu tham số ở mỗi N"*. Không phải — đóng băng siêu tham số ở giá trị C2 thì
crossover vẫn nằm nguyên chỗ cũ.

Hai chế độ còn lại vẫn nhất quán: NSL-KDD `matched` không đổi dấu ở cả hai arm; UNSW so với
ensemble cây không đổi dấu ở cả hai arm.

---

## 4. Việc còn treo

| # | Việc | Ai |
|---|---|---|
| 1 | Có muốn t làm notebook C4 mỏng để đóng gói supplementary không | Quang Anh quyết |
| 2 | Đưa kết quả robustness §3 vào bản thảo (một câu + bảng phụ lục) | Quan, lúc viết |
| 3 | Ghi caveat arm `tuned_once` vào mục hạn chế | Quan, lúc viết |
| 4 | Mục reproducibility phải nói XGBoost dao động ±0.001 giữa các máy | Quan, lúc viết |
