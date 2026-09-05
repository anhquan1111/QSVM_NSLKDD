# QSVM-IDS NISQ — Quantum Kernel SVM cho phát hiện xâm nhập mạng

Khung thực nghiệm áp dụng **Quantum Support Vector Machine** với **ZZ-FeatureMap** cho phát
hiện xâm nhập mạng, dưới ràng buộc phần cứng **NISQ**. Câu hỏi của đề tài không phải *"quantum
có thắng không"* mà ***"thắng ở đâu, và có đáng cái giá của nó không"***.

```
NSL-KDD (41 đặc trưng) → One-Hot (122D) → SelectKBest (K=20) → PCA (n*=4)
   → MinMax [0, π] → ZZ-FeatureMap (4 qubit, r=2, full entanglement) → SVC (nhân đã tính sẵn)
```

---

## Bắt đầu từ đâu

| Muốn biết | Đọc file này |
|---|---|
| Bản revision đã làm gì, còn gì phải làm | **[docs/REVISION_REPORT.md](docs/REVISION_REPORT.md)** ← *bắt đầu ở đây* |
| Reviewer yêu cầu những gì | [docs/Review.md](docs/Review.md) — nguyên văn thư quyết định |
| Bản thảo đang viết tới đâu | [paper/paper1/main_revision.tex](paper/paper1/main_revision.tex) |
| Thư trả lời từng ý reviewer | [paper/paper1/response_letter.tex](paper/paper1/response_letter.tex) |
| Paper 2 (đã nộp IJNM) | [docs/PAPER2_overview.md](docs/PAPER2_overview.md) |

Bản PDF đã compile để trong `paper/paper1/overleaf/`.

---

## Kiểm chứng — chạy được ngay, không cần chạy lại thí nghiệm

Đây là phần đáng xem nhất của repo. Bốn bộ kiểm tự động **tính lại từ dữ liệu thô** và đối
chiếu với mọi con số đã viết trong bài:

```bash
python runners/audit_c4.py        # 100/100  mọi thống kê công bố
python runners/audit_figures.py   #  36 mục  mọi con số trên hình
python runners/audit_prose.py     # 115/115  mọi con số viết trong câu văn
python runners/verify_lemma1.py   #  15/15   khai triển bậc hai của nhân ZZ
python runners/check_latex.py     #          cấu trúc file .tex
```

Nguyên tắc thiết kế đáng lưu ý: **`audit_c4.py` không gọi lại hàm thống kê của
`src/c4_pipeline.py`** — nó viết lại từ đầu bằng `scipy` rồi so kết quả. Dùng chính code đã
sinh ra một con số để kiểm con số đó thì lỗi chung sẽ lọt qua cả hai lần.

Bốn bộ kiểm này đã **bắt được 4 lỗi thật trong chính code revision** trước khi công bố, trong
đó một lỗi làm `n*` ra 5 thay vì 4.

> `audit_figures.py` sẽ báo **9 mục SKIP** trên bản vừa clone về. Đó không phải lỗi: git không
> lưu thời điểm sửa file, nên sau khi clone thì phép kiểm "hình có mới hơn dữ liệu nguồn
> không" mất căn cứ và nó báo SKIP thay vì báo sai. 27 mục đối chiếu **số liệu** vẫn chạy đủ,
> và đó mới là phần xác nhận hình vẽ đúng số. Muốn kiểm cả xuất xứ thì chạy
> `python runners/make_paper1_figures.py` trước.

---

## Bản revision đã thay đổi những gì

Chạy lại toàn bộ dưới giao thức đã sửa — **10 run thay vì 5, tune đối xứng cho cả mô hình
lượng tử lẫn cổ điển, thêm Random Forest và XGBoost, báo cáo trên toàn bộ KDDTest⁺** — cho
thấy **năm khẳng định của bản đã nộp không đứng vững**:

| Bản đã nộp | Số đo được |
|---|---|
| Lợi thế ở chế độ ít dữ liệu | **Ngược lại** — cổ điển thắng ở N nhỏ |
| "+6.7 điểm rare-attack, d = +0.68" | **Không tái tạo được** |
| Theorem 1: n\* = 4 cực đại hoá J | **Sai** — J cực đại tại n = 2 |
| QSVM 0.854 > SVM-RBF 0.838 | **XGBoost 0.8503 > QSVM 0.8469** |
| "Quantum advantage is real" | **21 thắng / 21 thua / 68 hoà** trên 110 so sánh |

Ba kết quả mới thay vào chỗ đó:

1. **Thứ tự đảo chiều theo lượng dữ liệu** — QSVM gần chót ở N = 100, dẫn đầu ở N = 10⁴, đổi
   dấu trong khoảng N = 2000–5000, bền qua **6/6** tổ hợp baseline × cách tune.
2. **Luật chọn số chiều chuyển giao được** — cùng một luật, không sửa tham số: `n* = 4` trên
   NSL-KDD, `n* = 6` trên UNSW-NB15, lặp lại đúng trên 10/10 tập con.
3. **Ranh giới đo được kèm cơ chế** — mở rộng mạch lên 8 qubit thì **48/48 so sánh nghiêng về
   cổ điển**; độ trải ma trận Gram giảm nhanh gấp đôi cho nhân ZZ (đúng tỉ lệ cấu trúc mạch dự
   đoán) và **dự đoán được** macro-F1 (r = +0.77).

Chi tiết đầy đủ, kèm đối soát 33 ý của reviewer: **[docs/REVISION_REPORT.md](docs/REVISION_REPORT.md)**.

---

## Cấu trúc repo

```
src/c4_pipeline.py        Lõi: nhân lượng tử, biểu diễn, giao thức lấy mẫu, thống kê
src/reliability.py        Lõi Paper 2 (calibration)

runners/                  Script chạy được, mỗi cái một việc
  ├── audit_*.py          4 bộ kiểm độc lập  ← xem phần trên
  ├── verify_lemma1.py    Kiểm số cho Lemma 1
  ├── check_latex.py      Kiểm cấu trúc .tex khi máy không có LaTeX
  ├── run_c4.py           Quét kích thước tập huấn luyện (kết quả chính)
  ├── run_c1_ksens.py     Luật chọn số chiều theo K
  ├── run_ksweep.py       Quét ngân sách đặc trưng K
  ├── run_width_sweep.py  Quét bề rộng mạch
  ├── run_gram_concentration.py   Đo độ tập trung ma trận Gram
  ├── run_hardware_kernel.py      Chạy trên QPU thật (đã thử --dry-run)
  ├── make_paper1_figures.py      Sinh 9 hình của bài
  └── make_overleaf_zip.py        Đóng gói bản thảo để tải lên Overleaf

configs/c4_protocol.json  Giao thức đã đóng băng: seed, lưới N, quy tắc lồng nhau
config.py                 Đường dẫn trung tâm

notebooks/nslkdd/         C1..C4_revision.ipynb là bản đang dùng
notebooks/unsw/           Chuyển giao sang UNSW-NB15

data/     { nslkdd/, unsw/ }   dữ liệu thô + đã tiền xử lý
models/   { nslkdd/, unsw/ }   transformer đã fit (joblib) + ma trận Gram (npy)
results/  { nslkdd/, unsw/ }   artifact JSON/CSV  ← nguồn của mọi con số trong bài

paper/paper1/             Bản thảo revision + thư phản hồi + 9 hình
paper/paper2/             Paper 2, đã nộp IJNM
docs/                     Báo cáo revision, thư reviewer, tổng quan Paper 2
```

### Đọc kết quả ở đâu

Mọi con số trong bài đều truy được về `results/`:

| Kết quả | File |
|---|---|
| Bản đồ chế độ 110 ô | `results/nslkdd/regime_map_rows.csv` |
| Quét kích thước tập huấn luyện | `results/nslkdd/c4_revision/c4_pairwise_statistics_natural.csv` |
| Biến thể K=80 / n=8 | `results/nslkdd/c4_revision/variant_K80n8/` |
| Luật chọn số chiều | `results/nslkdd/c1_revision/c1_ksensitivity.json` |
| Độ tập trung Gram | `results/nslkdd/c1_revision/c1_gram_concentration.json` |
| Chuyển giao UNSW | `results/unsw/c4_revision/` |

---

## ⛔ Hình nào KHÔNG được dùng

Chỉ hình trong **`paper/paper1/figs_revision/`** là của bản revision.

Hình nằm trong `results/*/c3_multirun/`, `results/*/c4_multirun/`,
`data/*/processed_data/` đều là **của code cũ** — 5 seed, tune bất đối xứng, chưa có
RF/XGBoost — và **mâu thuẫn với bài**. Thư mục `reports/` chứa 96 hình loại này đã được **gỡ
khỏi repo** vì lý do đó; nếu cần tra cứu thì lấy trong lịch sử git.

Xem `paper/paper1/figs_revision/MANIFEST.md` để biết xuất xứ từng hình.

---

## Chạy lại

```bash
uv sync                              # hoặc: pip install -e .
python runners/run_c4.py             # kết quả chính (~vài giờ)
python runners/make_paper1_figures.py
python runners/audit_c4.py           # xác nhận kết quả khớp
```

Nhân lượng tử được tính bằng **statevector chính xác**, không lấy mẫu. Vì ZZ-FeatureMap chéo
hoá sau mỗi lớp Hadamard nên trạng thái có dạng đóng, không cần mô phỏng từng cổng — nhanh hơn
Qiskit vài trăm lần và đã đối chiếu khớp tới `1.3e-15`. Nhiễu và sai số lấy mẫu hữu hạn được
áp **riêng** như hai điều kiện khảo sát, không trộn vào kết quả chính.

Môi trường: NumPy 2.4 · SciPy 1.17 · scikit-learn 1.8 · XGBoost 3.3 · Qiskit 2.3.

---

## Hai bài báo

| | Trọng tâm | Trạng thái |
|---|---|---|
| **Paper 1** | *Quantum kernel đáng giá ở chế độ nào?* | Major revision @ IEEE TETC, hạn 13-10-2026 |
| **Paper 2** | *Xác suất cảnh báo của QSVM có đáng tin không?* | Đã nộp @ IJNM (Wiley Q2), 04-08-2026 |
