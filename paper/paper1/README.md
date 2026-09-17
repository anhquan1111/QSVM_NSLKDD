# Paper 1 — TETC-2026-05-0252

Bản R1 **đã nộp 17-09-2026**. Đang chờ review. TETC **không cho major revision lần hai**.

> **Mới vào hoặc lâu không đụng tới?** Đọc [DOC_TRUOC_KHI_LAM_TIEP.md](DOC_TRUOC_KHI_LAM_TIEP.md)
> trước — nó nói bản này khác bản đã nộp chỗ nào và vì sao.

---

## Bốn thư mục, đừng lẫn

| Thư mục | Là gì |
|---|---|
| **ngay đây** (`paper/paper1/`) | **Bản hoàn chỉnh** — bản đã nộp cộng hai thứ nộp không kịp |
| `v2_submitted/` | Bản **đã đi** 17-09-2026, đóng băng. **Đừng sửa** |
| `v1_submitted/` | Bản nộp lần đầu 05/2026, để đối chiếu |
| `v2_revision/` | Gói `.zip` để tải lên Overleaf (sinh lại được) |

Bản hoàn chỉnh khác bản đã nộp đúng **hai** chỗ: **ba hình đã sửa chồng lấn** (Fig. 6, 7, 8)
và **phép kiểm nhiễu 10 run** thay cho 1 run. Chi tiết trong `DOC_TRUOC_KHI_LAM_TIEP.md`.

---

## Ba file compile được

| File | Ra cái gì | Compiler |
|---|---|---|
| **`main_revision.tex`** | Bản thảo **sạch** | pdfLaTeX |
| **`main_annotated.tex`** | Bản **tô nền vàng** phần mới/đổi — TETC bắt buộc nộp kèm | **LuaLaTeX** |
| **`response_letter.tex`** | Thư phản hồi 33 ý reviewer | pdfLaTeX |

### Bản đánh dấu hoạt động thế nào

Hai lớp đánh dấu chồng lên nhau:

1. **Nền vàng** — môi trường `revbody` bọc thân mỗi tiểu mục mới hoặc viết lại. Chỉ bật khi
   `\annottrue`; bản sạch thì `revbody` không làm gì. Dùng `lua-ul`, nên **phải LuaLaTeX**.
2. **Nhãn màu** dưới tiêu đề, kèm mã ý reviewer:

| Nhãn | Nghĩa |
|---|---|
| **NEW** (xanh lá) | Mục hoàn toàn mới |
| **REWRITTEN** (xanh dương) | Có trong bản cũ nhưng viết lại |
| **CORRECTED** (đỏ) | Sửa một lỗi của bản đã nộp |
| **RETAINED** (xám) | Giữ nguyên ý bản cũ |

Cờ `\newif\ifannot` phải khai **trước** `\input{preamble}` — preamble đọc nó để quyết định
có nạp `lua-ul` hay không. Đổi thứ tự thì `revbody` thành rỗng và không tô gì.

Sửa nội dung một nhãn: tìm `\revnote{loại}{ghi chú}` dưới tiêu đề tiểu mục trong `sections/`.

**Hai bản dùng chung `preamble.tex` và `document.tex`** — sửa ở `sections/` là cả hai cùng
đổi, không bao giờ lệch nhau.

---

## Cấu trúc

```
main_revision.tex        Bản sạch        ─┐
main_annotated.tex       Bản tô vàng     ─┼─ ba file compile được
response_letter.tex      Thư phản hồi    ─┘

preamble.tex             Gói, macro, revbody, tham số đặt hình   (dùng chung)
document.tex             Tiêu đề, tác giả, abstract, thứ tự mục  (dùng chung)
bibliography.tex         38 tài liệu tham khảo, mục nào cũng được trích

sections/                Thân bài, tên file theo đúng số mục trong bài
  01_introduction  02_background  03_framework  03b_theory  04_setup
  05_results  06_regimemap  07_limitations  08_conclusion
  09_appendix      Phụ lục A — chứng minh Lemma 1
  10_biographies   Tiểu sử 5 tác giả

tables/
  novelty_matrix.tex             Bảng I   — định vị so với 5 nghiên cứu
  protocol_by_contribution.tex   Bảng II  — giao thức theo từng đóng góp
  crossover_arms.tex             Bảng III — crossover qua hai nhánh tune
  ref_arm.tex + ref_arm_macros   Bảng IV  — nhánh đối chứng 122 đặc trưng

figs_revision/           9 hình (.pdf/.png) + 9 file caption + MANIFEST.md
authors/                 5 ảnh tác giả cho phần tiểu sử
refs/                    PDF tài liệu tham khảo (không đẩy lên repo — bản quyền)
```

Mỗi mục một file thì sửa mục này không đụng mục khác, và **hình đặt được vào đúng chỗ nó
được nhắc tới**. Lần compile đầu tiên cả 9 hình đều khai báo ở cuối tài liệu nên LaTeX dồn
hết xuống cuối bài và chèn lẫn vào danh mục tài liệu — tách ra mới sửa được.

---

## Đóng gói để tải lên Overleaf

```bash
python runners/make_overleaf_zip.py
```

Ra **bốn** gói trong `v2_revision/`. Ba gói đầu, mỗi gói chứa **đúng một** tài liệu compile
được cộng toàn bộ phụ thuộc:

| Muốn xuất PDF nào | Gói nào | Compiler |
|---|---|---|
| Bản thảo sạch | `TETC-2026-05-0252_ban_sach.zip` | pdfLaTeX |
| Bản tô vàng | `TETC-2026-05-0252_ban_danh_dau.zip` | **LuaLaTeX** |
| Thư phản hồi | `TETC-2026-05-0252_thu_phan_hoi.zip` | pdfLaTeX |
| (gộp cả ba, để lưu trữ) | `TETC-2026-05-0252_revision.zip` | tuỳ file chọn |

Mỗi gói riêng chỉ có **một** file mang `\documentclass`, nên Overleaf tự nhận đúng Main
document — tải lên rồi bấm Recompile, không phải vào Settings chỉnh gì.

**New Project → Upload Project.** Đừng kéo zip thả vào project đang có: Overleaf giải nén vào
thư mục con, file main và `preamble.tex` nằm khác chỗ nhau, và báo
`File preamble.tex not found`.

Script tự kiểm ba điều trước khi báo OK: mỗi gói đúng một `\documentclass`, mọi `\input` trỏ
tới file **có trong gói**, và mọi `\includegraphics` cũng vậy.

---

## Kiểm

```bash
python runners/check_latex.py     # cấu trúc .tex, cả ba tài liệu
python runners/audit_c4.py        # 100/100  thống kê
python runners/audit_figures.py   #  36/36   hình
python runners/audit_prose.py     # 134/134  số viết trong câu văn
python runners/verify_lemma1.py   #  15/15   khai triển Lemma 1
python runners/verify_noise10.py  #  40/40   phép kiểm nhiễu 10 run
```

## Ràng buộc của TETC

- Nộp **ba file**: bản sạch · bản tô vàng · thư phản hồi
- Quá **12 trang** thì trả phí trang vượt, **không được xin miễn** — bản đã nộp **18 trang**
- Tài liệu tham khảo **tối đa 45 mục** — hiện **38**, mục nào cũng được trích
- **Không được thêm/bớt tác giả**, **không được thêm/bớt tự trích dẫn**

Toàn cảnh: `docs/BAO_CAO_REVISION.md` · Thư reviewer nguyên văn: `docs/Review.md`
