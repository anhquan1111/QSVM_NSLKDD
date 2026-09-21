# Paper 3 — EAI AICON 2026

Special Session: *Quantum-Inspired AI for Autonomous SAGINs and Non-Terrestrial Networks*
· Phú Quốc, 20–22/11/2026 · Springer LNICST · **short paper 6–11 trang**

> **Trạng thái:** khung bài + toàn bộ số liệu, hình, bảng đã dựng xong và kiểm 47/47.
> Phần còn lại là **viết prose** — các chỗ `% TODO` trong [main.tex](main.tex).

---

## Bài này nói gì

Quy trình chọn siêu tham số có thể **tự sinh ra một phát hiện không có thật**.

Đây là một ca có thật trong chính dữ liệu của nhóm: `argmax` trên lưới C theo F₁ chọn ra
`C=0.01`, QSVM sụp về đoán-tất-cả-tấn-công, và cái mô hình sụp đó lại **sinh ra một kết quả
"robustness"** trông rất đẹp — F₁ bất biến theo nhiễu, đúng nghĩa đen, vì dự đoán là hằng.

**Cơ chế** nằm gọn trong Hình 1(a): F₁ của bộ phân loại hằng trên fold lệch lớp là một
**ngưỡng sàn** = 0,8504. Cả bốn kernel đều chạm đúng sàn đó ở `C=0.01`. Linear và poly vượt
lên từ `C=0.1`, RBF từ `C=1.0` — còn quantum thì **không bao giờ vượt** (điểm tốt nhất không
suy biến của nó là 0,8497, *thấp hơn* sàn). Nên `argmax` không có cực đại không-suy-biến nào
để tìm, và trả về đúng chỗ sụp.

**Và cái bẫy không đặc thù cho kernel lượng tử** — đây là chỗ làm bài công bằng thay vì một
chiều. Bảng kiểm đếm cho thấy linear và poly cũng sụp (1/5 run), và ở giao thức revision thì
**SVM-RBF sụp 9/10 run** còn QSVM không dòng nào. Cái riêng của kernel lượng tử chỉ là nó sụp
ở **mọi** run, nên `argmax` bị khoá vào đó.

---

## Quan hệ với hai bài kia — đọc trước khi thêm bất cứ gì

Ba bài chia theo **trục**, không theo dataset. Paper 1 sở hữu cả NSL-KDD lẫn UNSW trên trục
accuracy, nên **không được** chia theo dataset.

| Trục | Thuộc về |
|---|---|
| Accuracy / regime — crossover, KTA, luật chọn n\*, transfer UNSW | **Paper 1** (đang review ở TETC, đóng băng) |
| Calibration / reliability — ECE, Brier, Platt | **Paper 2** |
| **Quy trình đánh giá — bẫy tune, bộ kiểm** | **bài này** |

**Tuyệt đối không đưa vào bài này:** crossover · KTA như luật chọn n\* · kết luận transfer
UNSW · bất kỳ số ECE/Brier nào · hình `fig11_unsw_transfer` (hình của Paper 1).

**Một điểm phải khai rõ trong bài:** hàng `revision-tuned_once` của Bảng 1 tính từ **chính
những lần chạy Paper 1 báo cáo** — nhưng là một đại lượng Paper 1 **không** báo cáo. Hợp lệ,
vì là phép đo khác; nhưng phải nói ra.

---

## Hai thế hệ dữ liệu — không được trộn

| | Thế hệ A (bằng chứng suy biến) | Thế hệ B (revision) |
|---|---|---|
| Pipeline | K=35 → PCA **4** → **4 qubit** | K=35 → PCA **6** → **6 qubit** |
| Quy mô | N_train = N_test = **100**, **5 seed** | N tới 10 000, **10 run**, test đầy đủ |
| Nguồn | `results/unsw/*.json` | `results/unsw/c4_revision/` |

Bài **phải nói thẳng** kết quả suy biến là 4 qubit / N=100 / 5 seed, và **chưa từng được tái
lập** ở giao thức 10-run/6-qubit. Mục Limitations đã viết sẵn đoạn này.

---

## Dựng lại

```bash
python runners/make_paper3_figures.py   # 2 hình
python runners/make_paper3_tables.py    # bảng + macro số
python runners/audit_paper3.py          # 47/47
python runners/check_latex.py paper/paper3_aicon/main.tex
python runners/make_paper_zip.py paper3   # gói để tải lên Overleaf
```

**Máy này không có LaTeX**, nên bài phải compile trên Overleaf:
**New Project → Upload Project** với `dist/AICON2026_paper3.zip`, rồi Recompile.
Đừng kéo zip thả vào project đang có — Overleaf giải nén vào thư mục con rồi báo thiếu file.

Compiler: **pdfLaTeX**. `llncs.cls` có sẵn trên Overleaf, không cần đóng gói kèm.
Gói tự kiểm ba điều: đúng một `\documentclass`, mọi `\input` và mọi `\includegraphics`
đều trỏ tới file **có trong gói**.

## Kỷ luật về số

**Prose không được viết số trực tiếp.** Mọi con số đi qua macro trong
[tables/numbers_macros.tex](tables/numbers_macros.tex), sinh từ artifact. `audit_paper3.py`
có một phép quét bắt số viết tay trong câu văn và sẽ báo lỗi.

Bài lập luận rằng số không được kiểm sẽ đánh lừa người đọc — nên chính nó phải chịu đúng tiêu
chuẩn đó. Ba lớp kiểm: macro khớp artifact · câu văn không có số viết tay · các bất biến của
lập luận vẫn đúng (ví dụ: điểm CV tốt nhất không suy biến của quantum **phải** thấp hơn sàn,
nếu không thì cả câu chuyện sụp).

---

## Còn phải làm

| | Việc |
|---|---|
| 1 | Viết prose — các chỗ `% TODO` trong `main.tex` |
| 2 | Tài liệu tham khảo (`thebibliography` đang rỗng) |
| 3 | Tải `llncs.cls` nếu build ở máy (Overleaf có sẵn) |
| 4 | **Mirror ẩn danh** `anonymous.4open.science` — Confy+ bắt buộc PDF ẩn danh, mà repo mang tên thật |
| 5 | **Khai xung đột lợi ích**: ba chair của session đều là đồng tác giả Paper 1 |
| 6 | Giữ `\anonymoustrue` cho tới khi bài được nhận |

**Một món đáng cân nhắc thêm:** hiện chỉ có **hai** điểm test (C=0.01 và C=1.0) cộng năm điểm
CV. Một đường cong C dày trên tập test chỉ cần `SVC.fit` trên Gram **đã cache** ở
`models/unsw/qsvm_cache/multirun/` — **vài giây, không tính lại kernel nào**. Nó biến hai điểm
thành một đường, tức biến giai thoại thành phép đo.
