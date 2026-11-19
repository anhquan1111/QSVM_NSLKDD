# Paper 1: bản nộp Quantum Machine Intelligence

Bản viết lại của `paper/paper1/` (bản TETC, giờ chỉ đọc) theo mẫu LaTeX của Springer Nature.
Kế hoạch và tiêu chí đạt: `docs/PAPER1_KE_HOACH_QMI.md`, mục "Giai đoạn 2". Số liệu và các câu
phải đổi: `docs/PAPER1_GD1_KET_QUA.md`.

## Dựng PDF

Máy không có LaTeX, nên compile trên Overleaf:

1. `uv run python runners/make_qmi_zip.py` → `paper/paper1_qmi/build/Paper1_QMI_overleaf.zip`
2. Overleaf → New Project → Upload Project → chọn file zip (phải là project mới) → Recompile (pdfLaTeX).

Script tự gom mọi file mà `main.tex` cần. Hình (`figs_revision/`) và bảng số sinh bằng script
(`tables/ref_arm_macros.tex`) lấy từ `paper/paper1/`, đặt cùng đường dẫn trong gói, nên không chép
hai bản vào git.

## Kiểm trước khi commit một mục

    uv run python runners/audit_wording_r3.py paper/paper1_qmi   # phải ra 0

## File

| File | Là gì |
|---|---|
| `main.tex` | tiêu đề, tác giả, tóm tắt, thứ tự các mục |
| `macros.tex` | macro dùng chung (`\ZZ`, `\QSVM`, định lý) |
| `sections/*.tex` | từng mục; đầu mỗi file ghi nguồn cũ, câu phải đổi, số từ mục tiêu |
| `bibliography.tex` | danh mục tham khảo (kiểu IEEE, chép từ bản cũ) |
| `sn-jnl.cls`, `sn-mathphys-num.bst` | mẫu Springer Nature bản 3.1 (12-2024), không sửa |
