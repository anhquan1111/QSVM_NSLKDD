# Paper 1: bản nộp Quantum Machine Intelligence

Bản viết lại của `paper/paper1/` (bản TETC, giờ chỉ đọc) theo mẫu LaTeX của Springer Nature.
Kế hoạch và tiêu chí đạt: `docs/PAPER1_KE_HOACH_QMI.md`, mục "Giai đoạn 2". Số liệu và các câu
phải đổi: `docs/PAPER1_GD1_KET_QUA.md`.

## Dựng PDF

Máy không có LaTeX, nên compile trên Overleaf:

1. `uv run python runners/make_qmi_zip.py` → `paper/paper1_qmi/build/Paper1_QMI_overleaf.zip`
2. Overleaf → New Project → Upload Project → chọn file zip (phải là project mới) → Recompile (pdfLaTeX).

Script tự gom mọi file mà `main.tex` cần, tìm ở `paper/paper1_qmi/` trước rồi mới tới `paper/paper1/`.
Chín hình (`figs_revision/fig4`…`fig12`) là bản riêng của QMI (không tiêu đề lớn, không dòng chữ
đầu hình, nhãn theo chữ của bài), vẽ bằng `uv run python runners/make_paper1_figures.py --qmi` vào
`paper/paper1_qmi/figs_revision/`; chạy không có `--qmi` thì vẫn vẽ bản TETC vào `paper/paper1/`.
Bảng số `tables/ref_arm_macros.tex` vẫn lấy từ `paper/paper1/`, đặt cùng đường dẫn trong gói.
Các bảng khác trong `tables/` sinh bằng `uv run python runners/make_qmi_tables.py`, không sửa tay.

## Kiểm trước khi commit một mục

    uv run python runners/audit_wording_r3.py paper/paper1_qmi   # phải ra 0

## File

| File | Là gì |
|---|---|
| `main.tex` | tiêu đề, tác giả, tóm tắt, thứ tự các mục |
| `macros.tex` | macro dùng chung (`\ZZ`, `\QSVM`, `\QSVMZ` cho control QSVM-Z, định lý) |
| `sections/*.tex` | từng mục; đầu mỗi file ghi nguồn cũ, câu phải đổi, số từ mục tiêu |
| `bibliography.tex` | danh mục tham khảo (kiểu IEEE, chép từ bản cũ) |
| `sn-jnl.cls`, `sn-mathphys-num.bst` | mẫu Springer Nature bản 3.1 (12-2024), không sửa |
