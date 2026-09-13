# Bản revision — đang làm

Hạn nộp lại: **13-10-2026**. TETC **không cho major revision lần hai**.

| File | Nội dung |
|---|---|
| `main_revision.pdf` | Bản thảo revision, **16 trang** |
| `response_letter.pdf` | Thư phản hồi từng ý reviewer, 13 trang |

Hai file này là bản compile. **Mã nguồn nằm ở thư mục cha**, không nằm trong đây:

```
paper/paper1/
├── main_revision.tex          ← file chính, mở cái này
├── sections/                  ← thân bài, 7 mục
├── theory_revision.tex        ← Lemma 1 + luật ba giai đoạn + erratum
├── limitations_revision.tex   ← mục VII
├── appendix_lemma.tex         ← Phụ lục A
├── novelty_matrix.tex         ← Bảng I
├── crossover_arms_table.tex   ← Bảng II
├── bibliography_revision.tex  ← 41 tài liệu
├── response_letter.tex        ← thư phản hồi (tài liệu độc lập)
└── figs_revision/             ← 9 hình + 9 file caption
```

## Compile lại

```bash
python runners/make_overleaf_zip.py      # -> v2_revision/TETC-2026-05-0252_revision.zip
```

Tải zip lên Overleaf, đổi **Main document** sang `main_revision.tex` (hoặc
`response_letter.tex` khi muốn xuất thư), compile **hai lần** bằng pdfLaTeX.

## Còn phải làm trước khi nộp

| # | Việc |
|---|---|
| 1 | Ngày tháng cho `\thanks{Manuscript received ...}` |
| 2 | Cập nhật commit hash cuối vào mục Reproducibility |
| 3 | Thêm tiểu sử 5 tác giả — **đã có sẵn** ở `../v1_submitted/paper1_with_bios.pdf` trang 11 |
| 4 | Bản đánh dấu vàng phần tài liệu tham khảo (TETC bắt buộc) |
| 5 | Cover letter + mục riêng gửi EiC/AE giải trình thay đổi bibliography |

## Ràng buộc của TETC

- Nộp **ba file**: bản sạch · bản đánh dấu vàng · thư phản hồi
- Quá **12 trang** thì trả phí trang vượt (MOPC) và **không được xin miễn** — bản hiện tại 16 trang
- Danh mục tài liệu **tối đa 45 mục** — hiện 41
- **Không được thêm/bớt tác giả** nếu không có văn bản đồng ý của EiC
- **Không được thêm/bớt tự trích dẫn**

Xem `docs/DOI_CHIEU_CU_MOI.md` để biết bản này khác bản đã nộp chỗ nào, và
`docs/REVISION_REPORT.md` để biết toàn cảnh.
