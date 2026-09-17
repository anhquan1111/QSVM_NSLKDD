# Đọc trước khi làm tiếp

*Viết 17-09-2026, sau khi bản R1 đã nộp. Nếu vài tháng nữa quay lại và không nhớ gì, đọc file
này trước tiên.*

---

## 1. Đang ở đâu

Bản R1 **đã nộp** cho IEEE TETC ngày **17-09-2026**. Không nộp lại được nữa — **đợi review**.

TETC **không cho major revision lần hai**, nên vòng tới chỉ có thể là: chấp nhận, minor
revision, hoặc từ chối.

| Thư mục | Là gì |
|---|---|
| `paper/paper1/` (ngay đây) | **Bản hoàn chỉnh** — bản đã nộp **cộng** hai thứ nộp không kịp |
| `paper/paper1/v2_submitted/` | Bản **đã đi**, đóng băng. Đừng sửa |
| `paper/paper1/v1_submitted/` | Bản nộp lần đầu 05/2026, để đối chiếu |
| `paper/paper1/v2_revision/` | Gói `.zip` để tải lên Overleaf. Sinh lại được, không giữ PDF |

---

## 2. Bản hoàn chỉnh khác bản đã nộp đúng **hai** chỗ

Cả hai đều làm xong **sau** khi thầy nộp. Nếu reviewer cho sửa, đây là hai thứ đưa vào ngay.

### (a) Ba hình bị chữ chồng lên nhau

Fig. 6, 7, 8 trong bản đã nộp có chữ đè lên nhau. Nguyên nhân: nhãn đặt ở lề phải trong khi
các đường kết thúc trong một dải rất hẹp, mà hàng legend dưới đáy **đã** gọi tên đủ bảy mô
hình rồi. Cộng thêm `RIGHT_MARGIN = 1.95` — lề chừa cho chính cụm nhãn đó — làm gần **nửa**
bề ngang panel thành đất trống.

Đã bỏ cụm nhãn, hạ lề xuống `1.06`, đường mảnh lại (×0,72), marker nhỏ lại (×0,68), dải tin
cậy nhạt đi (alpha 0,12 → 0,06). Xem `runners/make_paper1_figures.py`.

So sánh trực tiếp: hình trong `v2_submitted/source/figs_revision/` là **bản cũ**, hình trong
`figs_revision/` là **bản đã sửa**.

### (b) Phép kiểm nhiễu: 1 run → 10 run

Bản đã nộp trích `0.87 / 0.86 / 0.87` — đó là số của **riêng run 1**. Xếp hạng 10 run thì
run 1 **đứng đầu bảng** (0,8728 so với trung bình 0,8501). Trích một mình nó là trích chỗ
lệch.

Số đúng, trung bình 10 run:

| Điều kiện | QSVM-ZZ | QSVM-Z |
|---|---|---|
| Statevector chính xác | 0,8329 ± 0,0259 | 0,8309 ± 0,0236 |
| 512 shot | 0,8363 ± 0,0197 | 0,8323 ± 0,0237 |
| Nhiễu FakeManilaV2 | 0,8501 ± 0,0192 | 0,8307 ± 0,0230 |

**Kết luận định tính không đổi** — nhiễu vẫn không làm giảm F₁. Nhưng phải báo là
**inconclusive**: p nhỏ nhất là 0,027, không qua ngưỡng Holm đầu tiên ở bất kỳ family nào
(hẹp nhất family = 2, ngưỡng 0,025). Mục IV-C tự cam kết *"every verdict is the corrected
one"*, viết khác đi là tự đặt hai chuẩn.

`runners/verify_noise10.py` tính lại toàn bộ từ cache thô — 40/40.

---

## 3. Bài trích kho mã **không phải repo này**

Đây là chỗ dễ quên nhất.

```
\url{https://github.com/haodpsut/nisq-qsvm-nids-benchmark}, release tag tetc-r1
```

Đó là repo của thầy Phúc Hào Đỗ, **public**, tag `tetc-r1` có thật. Bản R1 trước đó trích
`anhquan1111/QSVM_NSLKDD` kèm commit hash — đã đổi.

Hệ quả:

- Reviewer chạy audit sẽ vào **repo kia**, không phải repo này.
- Repo kia có `runners/make_ref_arm_table.py` và `run_ref_arm_fullfeat.py` (sinh Bảng IV) —
  hai file đó **không có** trong repo này lúc đầu, đã kéo về.
- Repo kia **không có** `verify_noise10.py` (viết sau khi nộp).
- Vấn đề lịch sử git của repo này (file hợp đồng có CCCD, xem `scripts/viet_lai_lich_su.sh`)
  **không ảnh hưởng** tới bản phát hành của bài, vì bài không trích repo này nữa.

---

## 4. Bảng IV đã kiểm được — đừng lo lại

Từng có lúc tôi báo Bảng IV (nhánh đối chứng XGBoost/RF trên 122 đặc trưng) không có
artifact. **Sai** — thầy có chạy thật, file nằm ở repo kia. Đã kéo về
`results/nslkdd/c4_revision/ref_arm_fullfeat.csv` (10 run mỗi ô) và đối chiếu:

```
N      XGB 122-d  bài / artifact      RF 122-d  bài / artifact
100    0.7816 / 0.7816  KHỚP          0.7733 / 0.7733  KHỚP
200    0.7927 / 0.7927  KHỚP          0.7824 / 0.7824  KHỚP
500    0.8067 / 0.8067  KHỚP          0.7851 / 0.7851  KHỚP
1000   0.8048 / 0.8048  KHỚP          0.7861 / 0.7861  KHỚP
```

**Bẫy khi đọc file này:** nó có **hai** `featset` — `all122` và `k20`. Phải lọc
`featset == "all122"` mới ra số của Bảng IV. Trộn cả hai thì lệch, và trông như bài sai.
`audit_prose.py` giờ kiểm luôn phần này.

---

## 5. Thầy thêm gì so với bản mình viết

| Thêm gì | File |
|---|---|
| Bảng II — giao thức theo từng đóng góp | `tables/protocol_by_contribution.tex` |
| Bảng IV — nhánh đối chứng 122 đặc trưng | `tables/ref_arm.tex` + `ref_arm_macros.tex` |
| Tiểu sử + ảnh 5 tác giả | `sections/10_biographies.tex`, `authors/` |
| Đoạn ở III-C: mọi baseline dùng chung biểu diễn 4 chiều | `sections/03_framework.tex` |
| Đoạn ở IV-A: vì sao điểm tuyệt đối thấp hơn 0,99 hay gặp | `sections/04_setup.tex` |
| **Bản tô nền vàng** cho phần mới (TETC bắt buộc) | `preamble.tex`, môi trường `revbody` |

**Bản đánh dấu giờ compile bằng LuaLaTeX**, không phải pdfLaTeX — vì `lua-ul` mới tô được
nền vàng xuyên qua ngắt đoạn và công thức. Bản sạch vẫn pdfLaTeX. Nhãn cũng đổi sang tiếng
Anh: `NEW / REWRITTEN / CORRECTED / RETAINED`.

Thầy còn có thư mục `check/` (script `make_yellow_annotated.py`, `pair_ref_arm.py`) ở máy
thầy — **không có** trong repo nào. Cần thì xin.

---

## 6. Muốn dựng lại PDF

```bash
python runners/make_overleaf_zip.py
```

Ra bốn gói trong `v2_revision/`. Tải lên Overleaf bằng **New Project → Upload Project**
(đừng kéo thả vào project đang có — nó giải nén vào thư mục con rồi báo
`File preamble.tex not found`).

| Muốn xuất gì | Gói nào | Compiler |
|---|---|---|
| Bản sạch | `..._ban_sach.zip` | pdfLaTeX |
| Bản tô vàng | `..._ban_danh_dau.zip` | **LuaLaTeX** |
| Thư phản hồi | `..._thu_phan_hoi.zip` | pdfLaTeX |

## 7. Kiểm trước khi động vào bất cứ gì

```bash
python runners/check_latex.py     # cấu trúc .tex, cả ba tài liệu
python runners/audit_c4.py        # 100/100
python runners/audit_figures.py   #  36/36
python runners/audit_prose.py     # 134/134  mọi con số trong câu văn
python runners/verify_lemma1.py   #  15/15
python runners/verify_noise10.py  #  40/40
```

Con số trong bài và con số trong bộ kiểm **phải khớp nhau** — `audit_prose` có một phép tự
kiểm: số phép kiểm mà bài và thư trích dẫn phải bằng đúng tổng của chính nó. Sửa bài mà quên
sửa script thì nó báo ngay.

---

## 8. Còn treo

| # | Việc | Ghi chú |
|---|---|---|
| 1 | Chờ review vòng 2 | không nộp lại được cho tới lúc đó |
| 2 | `verify_noise10.py` chưa có ở repo mà bài trích | nếu reviewer chạy audit bên đó sẽ không thấy |
| 3 | Lịch sử git repo này còn file hợp đồng có CCCD | `scripts/viet_lai_lich_su.sh`, chưa chạy |
| 4 | 52 commit còn dòng `Co-Authored-By: Claude` | cùng script trên; từ 16-09 không thêm nữa |
| 5 | Ngày tháng `\thanks{Manuscript received ...}` | vẫn để `[Date]` |

Toàn cảnh bản revision: `docs/BAO_CAO_REVISION.md`.
Thư reviewer nguyên văn: `docs/Review.md`.
