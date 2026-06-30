# Hướng dẫn đưa Paper 2 lên Overleaf (cho người chưa dùng LaTeX)

File cần upload: **`D:\QSVM_NSLKDD\paper2.zip`** (đã tạo sẵn, gồm `main.tex` + `figs/`).
Nếu cần tạo lại zip: nén thư mục `paper2/` (cả `main.tex` lẫn thư mục `figs/`).

## Bước 1 — Tạo tài khoản miễn phí
1. Vào https://www.overleaf.com
2. **Register** → đăng ký bằng email hoặc Google.

## Bước 2 — Upload project
1. **New Project** (góc trên trái) → **Upload Project**
2. **Select a .zip file** → chọn `D:\QSVM_NSLKDD\paper2.zip`
3. Overleaf tự giải nén và mở project.

## Bước 3 — Cấu hình biên dịch
1. Bấm **Menu** (góc trên trái).
2. **Compiler** = **pdfLaTeX**
3. **Main document** = **main.tex**
4. Đóng menu.

## Bước 4 — Biên dịch
1. Bấm **Recompile** (nút xanh, phía trên khung PDF bên phải).
2. Đợi ~10–30s → PDF hiện ra. (Warning vàng là bình thường; chỉ lo Error đỏ.)

## Bước 5 — Tải PDF
- Bấm biểu tượng **Download** phía trên khung PDF, hoặc Menu → **Download PDF**.

## Sửa nội dung
- Gõ trực tiếp vào khung soạn thảo bên trái rồi **Recompile**.
- Đổi tác giả/email: Ctrl+F tìm `\author`, sửa trong khối đó.

## Xử lý lỗi thường gặp
- **Ảnh "File not found"**: đảm bảo Main document = `main.tex` và có thư mục `figs/` với 8 file `.png`. Upload lại đúng `paper2.zip` nếu thiếu.
- **Lỗi package** (`IEEEtran`, `pifont`...): Overleaf có sẵn, hiếm khi lỗi.

## Ghi chú
- Máy local KHÔNG có pdflatex nên không build PDF tại máy được — phải dùng Overleaf (hoặc cài MiKTeX nếu muốn build offline).
- Paper 1 (`manuscript.pdf`) cũng compile bằng cách này (file gốc ghi "Compile on Overleaf").
