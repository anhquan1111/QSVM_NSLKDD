# Bản đã nộp — tháng 5/2026

Đây là **bản gốc nộp IEEE TETC**, mã bài `TETC-2026-05-0252`, nhận quyết định major revision
ngày 14-08-2026. Giữ lại để đối chiếu, **không chỉnh sửa gì trong này**.

Bản đang làm nằm ở `../v2_revision/` và mã nguồn ở thư mục cha.

| File | Nội dung |
|---|---|
| `paper1.pdf` | 11 trang, tạo 27-05-2026 |
| `paper1_with_bios.pdf` | 11 trang + **tiểu sử 5 tác giả kèm ảnh**, tạo 29-05-2026 |
| `main_reconstructed.tex` | Mã nguồn LaTeX **dựng lại từ PDF** — file `.tex` gốc không còn |

## Hai file PDF khác nhau chỗ nào

Đối chiếu toàn văn: **giống nhau 96,6%**. Khác biệt thực chất về nội dung chỉ có một chỗ:

| | `paper1.pdf` | `paper1_with_bios.pdf` |
|---|---|---|
| Dòng ngày tháng trang 1 | `accepted August 26, 2025` | `accepted [Date]` |
| Tiểu sử tác giả | không có | **có, 5 người kèm ảnh** |

Phần còn lại là khác biệt kỹ thuật của PDF (thứ tự neo liên kết nội bộ), không phải chữ trong
bài. Trang 7–8 — nơi chứa Table III, Table IV và mọi con số reviewer trích dẫn — giống hệt
nhau.

> **Chưa xác định được bản nào thật sự đã nộp.** Ngày tạo bên trong file cho thấy
> `paper1_with_bios.pdf` mới hơn 2 ngày, và TETC yêu cầu bản nộp *nên* có tiểu sử tác giả —
> nhưng đó chỉ là suy đoán. Chỗ biết chắc là hệ thống nộp bài (link Atypon trong email quyết
> định) hoặc email xác nhận hồi tháng 5.
>
> Việc này **không ảnh hưởng tới bản revision**: mọi câu reviewer trích dẫn đều khớp với cả
> hai file.

## Tiểu sử tác giả — đã có sẵn, không phải viết lại

TETC yêu cầu bản revision có tiểu sử 5 tác giả (dưới 150 từ mỗi người). Chúng **đã có sẵn ở
trang 11 của `paper1_with_bios.pdf`**, kèm ảnh chân dung. Chỉ cần bê sang bản mới, không phải
viết lại từ đầu.

## Về `main_reconstructed.tex`

File `.tex` gốc của bản đã nộp **không còn**. File này là bản dựng lại từ chính PDF để đối
chiếu từng mục, **không phải nguồn thật của bản đã nộp** và không compile ra đúng bản đó.
