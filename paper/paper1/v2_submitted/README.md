# Bản R1 — **đã nộp lại** cho IEEE TETC

Thầy nộp lại ngày **17-09-2026**. Đây là bản đã đi, giữ nguyên để đối chiếu — **đừng sửa gì
trong thư mục này**.

```
TETC-2026-05-0252-R1-manuscript-clean.pdf   bản đã nộp, 18 trang
source/                                      mã nguồn của đúng bản đó
   (TETC-...-source-tetc-r1.zip)             gói gốc — không đẩy lên repo, trùng với source/
```

Ảnh tác giả (`source/authors/*.jpg`) **không** nằm trong repo, theo tiền lệ của `paper/paper2/`.
Bản gốc ở `D:/Documents/Project/NCKH_Document/paper1_author_photos/` — copy lại vào
`source/authors/` trước khi compile.

---

## Bản nộp khác nguồn đang làm việc chỗ nào

Nguồn đang làm việc là `paper/paper1/` (thư mục cha). Ba khác biệt:

### Thầy thêm vào — nguồn của mình **chưa** có

| Thêm gì | File |
|---|---|
| Bảng II — giao thức theo từng đóng góp | `source/tables/protocol_by_contribution.tex` |
| Bảng IV — nhánh đối chứng 122 đặc trưng | `source/tables/ref_arm.tex` + `ref_arm_macros.tex` |
| Tiểu sử + ảnh 5 tác giả | `source/sections/10_biographies.tex`, `source/authors/` |
| Đoạn ở III-C: mọi baseline dùng chung biểu diễn 4 chiều | `source/sections/03_framework.tex` |
| Đoạn ở IV-A: vì sao điểm tuyệt đối thấp hơn 0.99 | `source/sections/04_setup.tex` |

### Mình có — bản nộp **chưa** kịp lấy

| | Trạng thái trong bản nộp |
|---|---|
| Ba hình đã sửa chồng lấn (Fig. 6, 7, 8) | vẫn là **hình cũ**, chữ đè lên nhau |
| Phép kiểm nhiễu 10 run | vẫn là **1 run** (`0.87 / 0.86 / 0.87`, ±0.02) |

### Chỗ chưa có cơ sở kiểm

`ref_arm.tex` ghi được sinh từ `runners/make_ref_arm_table.py` và
`results/nslkdd/c4_revision/ref_arm_fullfeat.csv`. **Cả script lẫn artifact đều không có
trong repo.** Bài mời reviewer chạy audit từ repo, nên Bảng IV hiện không kiểm lại được từ
bản phát hành.

---

Xem `docs/BAO_CAO_REVISION.md` để biết toàn cảnh, và `../v1_submitted/` cho bản nộp lần đầu
(05/2026).
