# Code bổ sung — bản revision Paper 1

**TETC-2026-05-0252** · repo: https://github.com/anhquan1111/QSVM_NSLKDD

Tổng: **17 file Python (~4.900 dòng)** và **4 notebook**, chia bốn nhóm.

---

## 1. Lõi

| File | Dòng | Nội dung |
|---|---:|---|
| `src/c4_pipeline.py` | 1.337 | Nhân lượng tử, biểu diễn dữ liệu, giao thức lấy mẫu, toàn bộ thống kê ghép cặp |

Nhân được tính bằng **statevector chính xác**, không lấy mẫu. ZZ-FeatureMap chéo hoá sau mỗi
lớp Hadamard nên trạng thái có dạng đóng — nhanh hơn Qiskit vài trăm lần, đã đối chiếu khớp
tới `1.3e-15`.

---

## 2. Sinh kết quả

| File | Dòng | Sinh ra kết quả nào |
|---|---:|---|
| `runners/run_c4.py` | 372 | Quét kích thước tập huấn luyện — **kết quả chính của bài** |
| `runners/run_c1_ksens.py` | 140 | Luật chọn số chiều theo ngân sách đặc trưng K |
| `runners/run_ksweep.py` | 193 | Quét K, giải thích vì sao chọn K = 20 |
| `runners/run_width_sweep.py` | 132 | Quét bề rộng mạch (4–10 qubit) |
| `runners/run_gram_concentration.py` | 127 | Đo độ tập trung ma trận Gram |
| `runners/pairwise_all_arms.py` | 68 | Thống kê ghép cặp qua cả hai nhánh tune |
| `runners/run_hardware_kernel.py` | 215 | Chạy trên QPU thật — đã thử `--dry-run`, **chưa chạy thật** |

---

## 3. Kiểm chứng — phần đáng xem nhất

| File | Dòng | Kiểm gì | Kết quả |
|---|---:|---|---|
| `runners/audit_c4.py` | 454 | Tính lại mọi thống kê công bố từ dữ liệu thô bằng scipy | 100/100 |
| `runners/audit_figures.py` | 325 | Xuất xứ hình + từng con số vẽ trên hình | 27/27 (+9 SKIP) |
| `runners/audit_prose.py` | 613 | Từng con số **viết trong câu văn** của bài và của thư phản hồi | 115/115 |
| `runners/verify_lemma1.py` | 178 | Khai triển bậc hai của nhân ZZ | 15/15 |
| `runners/check_latex.py` | 305 | Cấu trúc file `.tex` khi máy không có LaTeX | sạch |

```bash
python runners/audit_c4.py
python runners/audit_figures.py
python runners/audit_prose.py
python runners/verify_lemma1.py
```

Hai điểm về thiết kế:

- **`audit_c4.py` không gọi lại hàm thống kê của `c4_pipeline.py`** — nó viết lại từ đầu bằng
  scipy rồi đối chiếu. Dùng chính code đã sinh ra một con số để kiểm con số đó thì lỗi chung
  sẽ lọt qua cả hai lần.
- **`verify_lemma1.py`** là chỗ phát hiện Proposition 2 của bản đã nộp **sai hệ số** — lỗi
  không reviewer nào bắt.

Bốn bộ này đã bắt được **4 lỗi thật trong chính code revision** trước khi vào bài, trong đó
một lỗi làm `n*` ra 5 thay vì 4 (tức sai luôn cấu hình mạch).

> `audit_figures.py` báo **9 mục SKIP** trên bản vừa tải về. Không phải lỗi: git không lưu
> thời điểm sửa file, nên sau khi tải thì phép kiểm "hình có mới hơn dữ liệu nguồn không"
> mất căn cứ, và nó báo SKIP thay vì báo sai. 27 mục đối chiếu **số liệu** vẫn chạy đủ.

---

## 4. Vẽ hình và đóng gói

| File | Dòng | Nội dung |
|---|---:|---|
| `runners/make_paper1_figures.py` | 966 | Sinh 9 hình của bài |
| `runners/make_paper1_schematics.py` | 292 | Ba hình sơ đồ (đã bỏ khỏi bản thảo để lọt giới hạn trang) |
| `runners/make_overleaf_zip.py` | 151 | Đóng gói bản thảo để tải lên Overleaf |

---

## 5. Notebook

| File | Cell code | Nội dung |
|---|---:|---|
| `notebooks/nslkdd/C1_revision.ipynb` | 28 | Chọn số chiều |
| `notebooks/nslkdd/C2_revision.ipynb` | 19 | Ablation lớp entanglement |
| `notebooks/nslkdd/C3_revision.ipynb` | 14 | Dịch chuyển phân bố |
| `notebooks/nslkdd/C4_revision.ipynb` | 20 | Độ phức tạp mẫu + chuyển giao UNSW |

---

## 6. Cấu hình

| File | Nội dung |
|---|---|
| `configs/c4_protocol.json` | Giao thức đã đóng băng: seed, lưới N, quy tắc lồng nhau giữa các tập con |
| `config.py` | Đường dẫn trung tâm |

---

## Không cần xem — thuộc Paper 2

`src/reliability.py`, `runners/run_reliability_*.py` (4 file), `runners/rebuild_p2_4model.py`,
`runners/make_p2_schematic.py`. Đây là code của Paper 2 (calibration, đã nộp IJNM), không
liên quan tới revision Paper 1.

---

## Kết quả đọc ở đâu

Mọi con số trong bài đều truy được về `results/`:

| Kết quả | File |
|---|---|
| Bản đồ chế độ 110 ô | `results/nslkdd/regime_map_rows.csv` |
| Quét kích thước tập huấn luyện | `results/nslkdd/c4_revision/c4_pairwise_statistics_natural.csv` |
| Biến thể K = 80 / n = 8 | `results/nslkdd/c4_revision/variant_K80n8/` |
| Luật chọn số chiều | `results/nslkdd/c1_revision/c1_ksensitivity.json` |
| Độ tập trung Gram | `results/nslkdd/c1_revision/c1_gram_concentration.json` |
| Chuyển giao UNSW | `results/unsw/c4_revision/` |

---

## Nếu chỉ xem được một file

**`runners/audit_c4.py`** — nó trả lời câu *"số trong bài có đúng không"* một cách độc lập với
chính code đã sinh ra số đó.
