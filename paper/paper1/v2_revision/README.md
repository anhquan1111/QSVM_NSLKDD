# Bản revision — đang làm

Hạn nộp lại: **13-10-2026**. TETC **không cho major revision lần hai**.

Thư mục này **không giữ PDF đã compile nữa** — chỉ giữ gói `.zip` để tải lên Overleaf
rồi tự xuất PDF. Lý do: PDF trong đây liên tục lạc hậu so với nguồn (đã có lần gửi thầy
bản compile trước khi sửa hình), còn zip thì luôn được sinh lại từ nguồn hiện tại.

Riêng `ban_thay_revise_2026-09-14.pdf` giữ lại: đó là bản thầy tự revise, để đối chiếu.

**Mã nguồn nằm ở thư mục cha**, không nằm trong đây:

```
paper/paper1/
├── main_revision.tex      ← bản sạch          ─┐
├── main_annotated.tex     ← bản đánh dấu      ─┼─ ba tài liệu compile được
├── response_letter.tex    ← thư phản hồi      ─┘
├── preamble.tex           ← gói, macro, tham số đặt hình   (dùng chung)
├── document.tex           ← tiêu đề, tác giả, abstract, thứ tự mục (dùng chung)
├── bibliography.tex       ← 38 tài liệu
├── sections/              ← thân bài, 01…09 theo đúng số mục trong bài
├── tables/                ← Bảng I và Bảng II
└── figs_revision/         ← 9 hình + 9 file caption
```

## Đóng gói lại để compile

```bash
python runners/make_overleaf_zip.py
```

Ra **bốn** gói trong thư mục này. Mỗi gói riêng chỉ chứa **một** tài liệu, nên Overleaf
tự nhận đúng Main document — không phải vào Settings chỉnh gì:

| Muốn xuất PDF nào | Tải lên gói nào |
|---|---|
| Bản thảo sạch | `TETC-2026-05-0252_ban_sach.zip` |
| Bản có đánh dấu thay đổi | `TETC-2026-05-0252_ban_danh_dau.zip` |
| Thư phản hồi reviewer | `TETC-2026-05-0252_thu_phan_hoi.zip` |
| (gộp cả ba, để lưu trữ) | `TETC-2026-05-0252_revision.zip` |

Overleaf → **New Project → Upload Project**. Đừng kéo zip thả vào project đang có:
Overleaf giải nén vào thư mục con, file main và `preamble.tex` nằm khác chỗ nhau,
và báo `File preamble.tex not found`.

Các file `.zip` **không** được đẩy lên repo (xem `.gitignore`) — chạy lệnh trên là có.

## Còn phải làm trước khi nộp

| # | Việc |
|---|---|
| 1 | Ngày tháng cho `\thanks{Manuscript received ...}` |
| 2 | Cập nhật commit hash cuối vào mục Reproducibility |
| 3 | Thêm tiểu sử 5 tác giả — **đã có sẵn** ở `../v1_submitted/paper1_with_bios.pdf` trang 11 |
| 4 | Bản đánh dấu vàng phần tài liệu tham khảo (TETC bắt buộc) |
| 5 | Cover letter gửi EiC/AE — *mục giải trình bibliography đã viết xong, nằm trong thư phản hồi* |

## Ràng buộc của TETC

- Nộp **ba file**: bản sạch · bản đánh dấu vàng · thư phản hồi
- Quá **12 trang** thì trả phí trang vượt (MOPC) và **không được xin miễn** — bản hiện tại 16 trang
- Danh mục tài liệu **tối đa 45 mục** — hiện 38
- **Không được thêm/bớt tác giả** nếu không có văn bản đồng ý của EiC
- **Không được thêm/bớt tự trích dẫn**

Xem `docs/BAO_CAO_REVISION.md` — mục 11 đối chiếu bản này với bản đã nộp, các mục còn
lại là toàn cảnh bản revision.
