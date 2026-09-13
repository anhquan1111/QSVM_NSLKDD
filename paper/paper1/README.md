# Paper 1 — TETC-2026-05-0252

Hạn nộp lại: **13-10-2026**. TETC **không cho major revision lần hai**.

---

## Ba file compile được

Mỗi file dưới đây ra **một PDF riêng**. Trên Overleaf, đổi **Settings → Main document** sang
file muốn xuất rồi compile hai lần bằng pdfLaTeX.

| File | Ra cái gì | Dùng để làm gì |
|---|---|---|
| **`main_revision.tex`** | Bản thảo **sạch** | Nộp cho tạp chí |
| **`main_annotated.tex`** | Bản thảo **có đánh dấu thay đổi** | Thầy và đồng tác giả đối chiếu; TETC **bắt buộc** nộp kèm |
| **`response_letter.tex`** | Thư phản hồi 33 ý reviewer | Gửi ban biên tập |

### Bản đánh dấu hoạt động thế nào

Mỗi tiểu mục trong bản đánh dấu có một nhãn màu ngay dưới tiêu đề, nói mục đó thay đổi ra sao
so với bản đã nộp, kèm mã ý reviewer tương ứng:

| Nhãn | Nghĩa |
|---|---|
| **MỚI** (xanh lá) | Mục hoàn toàn mới, bản đã nộp không có |
| **VIẾT LẠI** (xanh dương) | Có trong bản cũ nhưng viết lại |
| **SỬA LỖI** (đỏ) | Sửa một lỗi của bản đã nộp |
| **GIỮ** (xám) | Giữ nguyên ý của bản cũ |

**Hai bản dùng chung `preamble.tex` và `document.tex`**, chỉ khác đúng một dòng
(`\annotfalse` / `\annottrue`). Nghĩa là sửa nội dung ở `sections/` thì **cả hai bản cùng đổi**
— không bao giờ có chuyện bản sạch và bản đánh dấu lệch nhau.

Muốn sửa nội dung một nhãn thì tìm lệnh `\revnote{loại}{ghi chú}` ngay dưới tiêu đề tiểu mục
trong file `sections/` tương ứng.

---

## Cấu trúc

```
main_revision.tex        Bản sạch       ─┐
main_annotated.tex       Bản đánh dấu   ─┼─ ba file compile được
response_letter.tex      Thư phản hồi   ─┘

preamble.tex             Gói, macro, tham số đặt hình   (bản sạch + bản đánh dấu dùng chung)
document.tex             Tiêu đề, tác giả, abstract, thứ tự các mục   (dùng chung)
bibliography.tex         41 tài liệu tham khảo

sections/                Thân bài, đặt tên theo đúng số mục trong bài
  01_introduction.tex        I.    Introduction
  02_background.tex          II.   Background and Related Work
  03_framework.tex           III.  Framework — nửa đầu (phương trình, pipeline)
  03b_theory.tex             III.  Framework — nửa sau (Lemma 1, luật C1, erratum)
  04_setup.tex               IV.   Experimental Setup
  05_results.tex             V.    Results
  06_regimemap.tex           VI.   Regime Map
  07_limitations.tex         VII.  Limitations
  08_conclusion.tex          VIII. Conclusion
  09_appendix.tex            Phụ lục A — chứng minh Lemma 1

tables/
  novelty_matrix.tex         Bảng I  — định vị so với 5 nghiên cứu
  crossover_arms.tex         Bảng II — crossover qua hai nhánh tune

figs_revision/           9 hình (.pdf/.png) + 9 file caption + MANIFEST.md
v1_submitted/            Bản đã nộp 05/2026, giữ để đối chiếu
v2_revision/             PDF đã compile + gói zip để tải lên Overleaf
refs/                    PDF tài liệu tham khảo (không đẩy lên repo — bản quyền)
```

### Vì sao tách nhiều file

Mỗi mục một file thì sửa mục này không đụng mục khác, và **hình đặt được vào đúng chỗ nó được
nhắc tới**. Lần compile đầu tiên cả 9 hình đều khai báo ở cuối tài liệu nên LaTeX dồn hết
xuống cuối bài và chèn lẫn vào danh mục tài liệu tham khảo — tách ra mới sửa được.

---

## Đóng gói để tải lên Overleaf

```bash
python runners/make_overleaf_zip.py
```

Ra **bốn** gói trong `v2_revision/`. Ba gói đầu, mỗi gói chứa **đúng một** tài liệu compile
được cộng toàn bộ phụ thuộc của nó:

| Muốn xuất PDF nào | Tải lên gói nào |
|---|---|
| Bản thảo sạch | `TETC-2026-05-0252_ban_sach.zip` |
| Bản có đánh dấu thay đổi | `TETC-2026-05-0252_ban_danh_dau.zip` |
| Thư phản hồi reviewer | `TETC-2026-05-0252_thu_phan_hoi.zip` |
| (gộp cả ba, để lưu trữ) | `TETC-2026-05-0252_revision.zip` |

Mỗi gói riêng chỉ có **một** file mang `\documentclass`, nên Overleaf tự nhận đúng
Main document — tải lên rồi bấm Recompile, không phải vào Settings chỉnh gì.

**New Project → Upload Project.** Đừng kéo file zip thả vào một project Overleaf đang có:
Overleaf giải nén vào một thư mục con, file main nằm một nơi còn `preamble.tex` nằm nơi khác,
và báo `File preamble.tex not found`.

Script tự kiểm ba điều trước khi báo OK: mỗi gói đúng một `\documentclass`, mọi `\input`
trong gói trỏ tới file **có trong gói**, và mọi `\includegraphics` cũng vậy.
Thư mục `v1_submitted/` không nằm trong gói nào.

---

## Kiểm trước khi nộp

```bash
python runners/check_latex.py     # cấu trúc .tex, khi máy không có LaTeX
python runners/audit_c4.py        # 100/100  thống kê
python runners/audit_figures.py   #  36 mục  hình
python runners/audit_prose.py     # 115/115  số viết trong câu văn
python runners/verify_lemma1.py   #  15/15   khai triển Lemma 1
```

## Còn phải làm

| # | Việc |
|---|---|
| 1 | Ngày tháng cho `\thanks{Manuscript received ...}` trong `document.tex` |
| 2 | Cập nhật commit hash cuối vào `sections/04_setup.tex` |
| 3 | Tiểu sử 5 tác giả — **đã có sẵn** ở `v1_submitted/paper1_with_bios.pdf` trang 11 |
| 4 | Tô vàng phần tài liệu tham khảo thay đổi (TETC bắt buộc) |
| 5 | Cover letter + mục riêng gửi EiC/AE giải trình thay đổi bibliography |

## Ràng buộc của TETC

- Nộp **ba file**: bản sạch · bản đánh dấu · thư phản hồi
- Quá **12 trang** thì trả phí trang vượt và **không được xin miễn** — bản hiện tại 16 trang
- Tài liệu tham khảo **tối đa 45 mục** — hiện 41
- **Không được thêm/bớt tác giả**, **không được thêm/bớt tự trích dẫn**

Xem `docs/DOI_CHIEU_CU_MOI.md` để biết bản này khác bản đã nộp chỗ nào, và
`docs/REVISION_REPORT.md` để biết toàn cảnh.
