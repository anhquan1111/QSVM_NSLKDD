# QSVM-IDS — Nhân lượng tử đáng giá ở chỗ nào?

*[English](README.md)*

Khung thực nghiệm có kiểm soát cho **Quantum Kernel SVM** (ZZ-FeatureMap) áp dụng vào phát
hiện xâm nhập mạng, dưới ràng buộc phần cứng **NISQ**, trên NSL-KDD và UNSW-NB15.

Câu hỏi không phải *"lượng tử có thắng không"* mà ***"thắng ở đâu, và có đáng cái giá mạch
không"*** — câu trả lời trung thực hoá ra là: **phần lớn là không đo được lợi thế nào, trừ
đúng một chỗ.**

```
NSL-KDD (41 đặc trưng) → one-hot (122D) → SelectKBest (K=20) → PCA (n*=4)
  → min–max [0, π] → ZZ-FeatureMap (4 qubit, r=2, full entanglement) → SVC (nhân tính sẵn)
```

---

## Kết quả chính

Trên **110 phép so sánh có kiểm soát** với sáu baseline cổ điển (XGBoost, random forest,
SVM-RBF/poly2/linear, và một mạch lượng tử không rối làm đối chứng), ghép cặp trong từng run
qua mười run, hiệu chỉnh Holm:

| | Số ô |
|---|---|
| Nghiêng về nhân lượng tử | **21** |
| Nghiêng về baseline cổ điển | **21** |
| Không kết luận được | **68** |

**Không có lợi thế tổng quát.** Nhưng có cấu trúc đáng báo cáo:

1. **Thứ hạng đảo chiều theo lượng dữ liệu.** Ở tỉ lệ lớp tự nhiên, nhân lượng tử gần chót ở
   *N* = 100 và dẫn đầu ở *N* = 10⁴; hiệu ghép cặp với XGBoost, random forest và SVM-RBF đổi
   dấu trong khoảng *N* = 2.000–5.000, đúng ở **6/6** tổ hợp baseline × nhánh tune. Làm giàu
   lớp hiếm gấp mười hai lần thì hiệu ứng **biến mất hoàn toàn** — mà đó chính là cách lấy
   mẫu của giao thức cũ.
2. **Luật chọn số chiều chuyển giao được.** Luật ba giai đoạn theo thứ tự từ vựng (cổng
   phương sai → cổng kernel-target alignment → chọn ứng viên rẻ nhất theo số CNOT) cho
   *n*\* = 4 trên NSL-KDD và, không sửa một ngưỡng nào, *n*\* = 6 trên UNSW-NB15, lặp lại
   đúng trên **10/10** tập con độc lập.
3. **Một ranh giới đo được, kèm cơ chế.** Tăng ngân sách đặc trưng thì buộc phải mở rộng
   mạch, và mở rộng thì phá hỏng nhân: ở *K* = 80 (*n*\* = 8), **cả 48** phép so sánh đều
   nghiêng về cổ điển. Nguyên nhân nhìn thấy trong ma trận Gram — độ trải ngoài đường chéo
   suy giảm nhanh gấp khoảng đôi ở nhân ZZ so với đối chứng không rối, đúng tỉ lệ mà phép đếm
   số hạng pha (cặp so với đơn qubit) dự đoán, và nó **dự đoán được** macro-F₁ ở *r* = +0,77.
   Chuyện này xảy ra dưới mô phỏng **chính xác, không nhiễu**, nên không phải hiệu ứng của
   lỗi phần cứng.

---

## Phần đáng xem về mặt kỹ thuật

**Lớp kiểm chứng mới là phần đáng đọc.** Năm bộ audit tính lại mọi con số đã công bố từ dữ
liệu thô, và báo lỗi thẳng nếu lệch:

```bash
python runners/audit_c4.py        # 100/100  mọi thống kê công bố
python runners/audit_figures.py   #  36      mọi con số vẽ trên hình
python runners/audit_prose.py     # 134/134  mọi con số viết trong câu văn bài báo
python runners/verify_lemma1.py   #  15/15   khai triển nhân, đối chiếu nhân chính xác
python runners/verify_noise10.py  #  40/40   phép kiểm nhiễu 10 run, kèm ngưỡng Holm
python runners/check_latex.py     #          cấu trúc .tex, cho máy không cài LaTeX
```

Quyết định thiết kế đáng nói: **`audit_c4.py` không gọi lại hàm thống kê trong
`src/c4_pipeline.py`.** Nó viết lại từ đầu bằng `scipy` rồi so. Dùng chính code đã sinh ra một
con số để kiểm con số đó thì một lỗi chung sẽ lọt qua cả hai lần.

Bộ kiểm này đã **bắt được bốn lỗi thật trong chính code revision** trước khi công bố, trong đó
một lỗi cho ra *n*\* = 5 thay vì 4. Nó cũng bắt được năm khẳng định của bản nộp trước không
đứng vững khi đo lại — cả năm đều được ghi rõ và rút lại trong bài, không lặng lẽ bỏ đi.

**Nhân dạng đóng thay vì mô phỏng từng cổng.** Vì ZZ-FeatureMap chéo hoá trong cơ sở tính toán
sau mỗi lớp Hadamard, trạng thái có dạng đóng và cả ma trận Gram tính được bằng đại số tuyến
tính dày đặc. Cách này nhanh hơn đường Qiskit **457–763 lần** và khớp tới **1,3 × 10⁻¹⁵** —
mức chính xác của số thực máy. Chính tốc độ đó mới làm cho việc quét hai bậc độ lớn của *N*,
bảy bề rộng mạch và hai bộ dữ liệu trở nên khả thi.

**Sai số lấy mẫu hữu hạn và nhiễu dựng từ máy thật được áp riêng như hai điều kiện khảo sát**,
không trộn vào kết quả chính, để sai số lấy mẫu không bao giờ bị nhầm thành hiệu ứng đang đo.

---

## Tự kiểm trong khoảng một phút

```bash
git clone https://github.com/anhquan1111/QSVM_NSLKDD && cd QSVM_NSLKDD
uv sync                      # hoặc: pip install -e .
python runners/audit_c4.py
```

Không cần chạy lại thí nghiệm — bộ kiểm đọc thẳng artifact đã công bố trong `results/`.

> `audit_figures.py` báo **9 mục SKIP** trên bản vừa clone. Đó không phải lỗi: git không lưu
> thời điểm sửa file, nên phép kiểm xuất xứ "hình có mới hơn dữ liệu nguồn không" mất căn cứ
> sau khi clone, và nó báo SKIP thay vì báo sai. 27 phép đối chiếu **số liệu** vẫn chạy đủ.
> Muốn kiểm cả xuất xứ thì chạy `python runners/make_paper1_figures.py` trước.

---

## Cấu trúc repo

```
src/c4_pipeline.py         Lõi: nhân lượng tử, biểu diễn, giao thức lấy mẫu, thống kê
src/reliability.py         Lõi của bài thứ hai (calibration)

runners/                   Mỗi script một việc
  ├── audit_*.py           Tính lại độc lập mọi con số đã công bố
  ├── verify_lemma1.py     Kiểm số cho khai triển nhân
  ├── verify_noise10.py    Kiểm số cho thí nghiệm nhiễu 10 run
  ├── check_latex.py       Kiểm cấu trúc .tex
  ├── run_c4.py            Quét kích thước tập huấn luyện (kết quả chính)
  ├── run_c1_ksens.py      Luật chọn số chiều theo ngân sách đặc trưng
  ├── run_width_sweep.py   Quét bề rộng mạch
  ├── run_gram_concentration.py   Đo độ tập trung ma trận Gram
  ├── run_hardware_kernel.py      Đường chạy trên QPU thật (đã thử --dry-run)
  ├── make_paper1_figures.py      Sinh chín hình của bài
  └── make_overleaf_zip.py        Đóng gói bản thảo để tải lên Overleaf

configs/c4_protocol.json   Giao thức đã đóng băng: seed, lưới N, quy tắc lồng nhau
data/    { nslkdd/, unsw/ }   dữ liệu thô + đã tiền xử lý
models/  { nslkdd/, unsw/ }   transformer đã fit (joblib) + ma trận Gram (npy)
results/ { nslkdd/, unsw/ }   artifact JSON/CSV  ← nguồn của mọi con số trong bài

paper/paper1/              Mã nguồn bản thảo (có README riêng)
paper/paper2/              Bài thứ hai
docs/                      Báo cáo revision, thư reviewer, danh mục code bổ sung
```

### Đọc kết quả ở đâu

| Kết quả | File |
|---|---|
| Bản đồ chế độ 110 ô | `results/nslkdd/regime_map_rows.csv` |
| Quét kích thước tập huấn luyện | `results/nslkdd/c4_revision/c4_pairwise_statistics_natural.csv` |
| Biến thể K=80 / n=8 | `results/nslkdd/c4_revision/variant_K80n8/` |
| Luật chọn số chiều | `results/nslkdd/c1_revision/c1_ksensitivity.json` |
| Độ tập trung Gram | `results/nslkdd/c1_revision/c1_gram_concentration.json` |
| Phép kiểm nhiễu 10 run | `results/nslkdd/c2_revision/c2_noise_validation_10run.csv` |
| Chuyển giao UNSW-NB15 | `results/unsw/c4_revision/` |

### Hình nào KHÔNG được dùng

Chỉ hình trong **`paper/paper1/figs_revision/`** là của bản hiện tại. Hình nằm trong
`results/*/c3_multirun/`, `results/*/c4_multirun/` hay `data/*/processed_data/` đều do giao
thức **cũ** sinh ra — 5 seed, tune bất đối xứng, chưa có RF/XGBoost — và **mâu thuẫn với
bài**. Xem `paper/paper1/figs_revision/MANIFEST.md` để biết xuất xứ từng hình.

> **Về dung lượng.** Cache ma trận nhân (`results/*/{c3,c4}_revision/cache/`) **không** nằm
> trong repo — 1,7 GB và sinh lại được. Notebook tự tính lại khi thiếu, và mọi bộ kiểm ở trên
> chạy bình thường mà không cần chúng.

---

## Chạy lại từ đầu

```bash
uv sync
python runners/run_c4.py               # kết quả chính (~vài giờ)
python runners/make_paper1_figures.py
python runners/audit_c4.py             # xác nhận số khớp
```

Môi trường: NumPy 2.4 · SciPy 1.17 · scikit-learn 1.8 · XGBoost 3.3 · Qiskit 2.3 với
qiskit-machine-learning 0.9 · Qiskit Aer 0.17.

---

## Hai bài báo

| | Trọng tâm | Trạng thái |
|---|---|---|
| **Bài 1** | Nhân lượng tử đáng giá ở chế độ nào? | Major revision tại **IEEE TETC**, hạn nộp lại 13-10-2026 |
| **Bài 2** | Xác suất cảnh báo của QSVM có đáng tin không? | Đã nộp **IJNM** (Wiley), 04-08-2026 |

Tác giả: Minh Tuan Pham, Phuc Hao Do, Nguyen Nang Hung Van, Quang Anh Nguyen, và
Quan Tran Anh Vo (tác giả liên hệ). Đề tài T2026-02-10TN, Trường Đại học Bách khoa —
Đại học Đà Nẵng.

Báo cáo revision đầy đủ và thư trả lời từng ý reviewer:
[docs/BAO_CAO_REVISION.md](docs/BAO_CAO_REVISION.md) ·
[paper/paper1/response_letter.tex](paper/paper1/response_letter.tex)
