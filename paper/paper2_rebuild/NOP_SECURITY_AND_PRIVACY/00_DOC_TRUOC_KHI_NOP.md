# Nộp Paper 2 — Security and Privacy (Wiley)

Mọi thứ cần để nộp đều nằm trong thư mục này.

Checklist này viết theo **quy tắc thật** của tạp chí (`paper/quytac.md`),
không phải phỏng đoán.

> ✅ **`manuscript.pdf` là bản mới nhất (23-09-2026), đã đọc tay từng trang để kiểm.**
> Đúng tên thầy Vân theo dạng thầy tự sửa, đủ 4 email, có ORCID, 7 từ khoá,
> có mục **Use of AI Tools**. `main_document.tex` và `latex_supplementary.zip`
> là đúng `main.tex` sinh ra PDF này, chỉ khác ở chỗ đã xoá ghi chú nội bộ
> tiếng Việt (xem bên dưới) — phần in ra không đổi một ký tự.

---

## Tải lên ở đâu — theo đúng màn hình *Upload Manuscript*

Màn hình thật **không** có nhãn "Main Document – LaTeX PDF" như tôi đoán
lúc đầu. Nó có **1 ô bắt buộc** và **6 ô tự chọn**. Chỉ điền **3 ô**:

| Ô trên màn hình | Đưa file nào |
|---|---|
| **Main Manuscript** *(bắt buộc, tối đa 1 file)* | `manuscript.pdf` — nếu hệ thống không nhận PDF thì đưa `latex_supplementary.zip` |
| **LaTeX Supplementary File** | `latex_supplementary.zip` |
| **Cover letter / Comments** *(tối đa 1 file)* | `cover_letter.docx` |

**Bỏ trống 4 ô còn lại:** *Figure*, *Table*, *Supporting Information*,
*Additional File* (cả hai loại). Hình và bảng đã nằm trong bài rồi — chính
ô Main Manuscript ghi *"may include embedded figures and tables"*.

### Vì sao thử `manuscript.pdf` trước

Ô Main Manuscript ghi loại file nhận là *"MS Word or LaTeX"* — **không liệt kê
PDF**. Nhưng hầu hết tạp chí Wiley vẫn nhận PDF ở lần nộp đầu. Thử mất vài
giây và không hề mất gì: **nếu nó chặn thì bạn biết ngay tại chỗ**, lúc đó
đưa `latex_supplementary.zip` vào ô đó thay (ô này ghi rõ được phép dùng
một archive gồm toàn bộ file LaTeX, hình, bảng) và bỏ trống ô LaTeX
Supplementary.

**Đặt PDF lên trước tốt hơn** vì phản biện sẽ đọc đúng bản dàn trang bạn đã
kiểm, thay vì bản do máy của họ tự compile ra.

### Hai thứ tôi đã gỡ khỏi gói zip

Gói cũ **1,17 MB**, gói mới **164 KB**. Gỡ hai thứ, cả hai đều là lỗi thật:

1. **README tiếng Việt ghi chú nội bộ.** Nó viết nguyên văn *"Còn phải làm
   trước khi nộp: viết prose ở các chỗ % TODO"*, *"giữ danh mục của bản đã
   nộp IJNM"*, *"bản này đổi trục chủ đạo so với bản đã nộp"*. Biên tập giải
   nén ra là đọc được. Gói mới có README tiếng Anh, chỉ nói cách compile.
2. **Comment tiếng Việt trong chính `main.tex`** — 73 dòng, trong đó có
   *"Khác bản đã nộp IJNM bốn điểm"* và ba chỗ `TODO(tac gia)`. Đã xoá **nội
   dung** comment nhưng **giữ dấu `%`** — vì một dấu `%` cuối dòng là lệnh
   nối dòng của TeX (bài có 5 chỗ); xoá cả dòng sẽ sinh ra dấu cách thừa.
   Script tự kiểm rằng phần **sẽ in ra** không đổi một ký tự nào.

   Đồng thời bỏ `biographies.tex` và 4 ảnh chân dung: `main.tex` đã comment
   `\input` chúng, Wiley không in tiểu sử kiểu IEEE, và ô Main Manuscript ghi
   *"should not include any supplementary materials"*.

Dựng lại gói bằng: `python scripts/build_goi_latex_p2.py`

**Bản trong repo giữ nguyên mọi ghi chú** — chỉ bản gửi đi mới bị làm sạch.

Tên file **tiếng Anh** có chủ ý: tên file hiện ra trước mắt biên tập khi họ
tải về. Thư mục và file checklist này thì tiếng Việt vì không bao giờ được
tải lên.

`cover_letter.txt` giữ lại để dán vào ô nhập tay nếu gặp; `cover_letter.tex`
là bản nguồn, không tải lên.

---

## Đường vào

Tạp chí dùng **Research Exchange**, không phải ScholarOne.

**https://onlinelibrary.wiley.com/page/journal/24756725/homepage/forauthors.html**
→ nút **"Start your submission"**

Theo dõi trạng thái: **https://submission.wiley.com** → *My Submissions*

> ⛔ **ĐỪNG bấm `start manuscript transfer`** trong email từ chối của IJNM.
> Nó chuyển kèm hồ sơ quyết định của IJNM mà **không** mang theo phản biện
> nào — vì bài bị loại thẳng, không có phản biện. Nếu đã lỡ mở bản nháp
> transfer thì vào xoá.

Hỗ trợ kỹ thuật: `submissionhelp@wiley.com` · Toà soạn: `SPYoffice@wiley.com`

---

## Đối chiếu bài với quy tắc

| Quy tắc | Yêu cầu | Bài | |
|---|---|---|---|
| Abstract | ≤ 250 từ | 203 | ✅ |
| Keywords | **bảy** | 7 | ✅ |
| Loại bài | Original Paper | Original Paper | ✅ |
| Định dạng | Free Format | IEEEtran giữ nguyên được | ✅ |
| Tài liệu tham khảo | *"any style, as long as consistent"* | IEEEtran số | ✅ |
| ORCID tác giả nộp | bắt buộc | `0009-0000-9420-1767` | ✅ |
| Data availability | bắt buộc, có link kho | Zenodo DOI | ✅ |
| Conflict of interest | bắt buộc | có | ✅ |
| Cover letter | **không bắt buộc** | có | ✅ |
| Phản biện | **single-anonymized** | — | tác giả **không** cần ẩn danh |
| Khai dùng AI | **bắt buộc, ngay trong bài** | mục *Use of AI Tools* + *Tooling* | ✅ |
| Email đồng tác giả | bắt buộc | đủ 4 | ✅ |

**Tiêu đề:** quy tắc ghi *"less than 40 characters"* — tiêu đề của bạn 104.
Đó là **lỗi mẫu**, không ai theo: một bài đã đăng trên chính tạp chí này
(`10.1002/spy2.496`, 2025) dài ~125 ký tự. Giữ nguyên.

**Tài liệu tham khảo:** nộp lần đầu thì kiểu nào cũng được miễn nhất quán.
Nhưng nếu được nhận, tạp chí dùng **AMA** (số Ả Rập viết **trên dòng**).
Lúc revision mới phải chuyển — chưa cần bây giờ.

---

## Các ô phải điền

**Title**
```
A Reliability and Calibration Benchmark of QSVM Against Strong Tabular
Learners on NSL-KDD and UNSW-NB15
```

**Article type** — `Original Paper`

**Authors** (đúng thứ tự)

| # | Tên | |
|---|---|---|
| 1 | Nguyen Nang Hung Van | |
| 2 | Quan Tran Anh Vo | **corresponding**, ORCID `0009-0000-9420-1767` |
| 3 | Quang Anh Nguyen | |
| 4 | Minh Tuan Pham | |

Đơn vị cả bốn: `University of Science and Technology - The University of Danang, Danang 550000, Vietnam`

Email bốn người (đúng thứ tự tác giả):
```
nguyenvan@dut.udn.vn
votrananhquan1111@gmail.com
anh1303052005@gmail.com
pmtuan@dut.udn.vn
```

> Quy tắc mục 4 đòi **email của mọi đồng tác giả**, không chỉ tác giả liên
> hệ — để toà soạn báo kết quả cho tất cả. Chuẩn bị sẵn 4 email.

**Keywords** (bảy)
```
Quantum machine learning; quantum kernel; calibration; reliability;
intrusion detection; NSL-KDD; UNSW-NB15
```

**Data Availability Statement**
```
Every number reported in this paper is computed from artifacts archived with
it. The stored per-run measurements, the scripts that generate every figure
and table, and the audit scripts that recompute each reported number from
those artifacts are openly available at
https://doi.org/10.5281/zenodo.22893683
The two corpora are public benchmarks: NSL-KDD and UNSW-NB15.
```

**Funding**
```
The University of Danang - University of Science and Technology,
Project T2026-02-10TN
```

**Conflict of Interest**
```
The authors declare no conflict of interest.
```

**Ethics**
```
Not applicable. This study used only public benchmark datasets of network
traffic records and involved no human participants, no animal subjects and
no personally identifiable information.
```

**Author Contributions (CRediT)**
```
Quan Tran Anh Vo: conceptualization; methodology; software; formal analysis;
validation; visualization; writing - original draft; funding acquisition.
Quang Anh Nguyen: software; investigation; data curation; formal analysis;
validation; visualization.
Nguyen Nang Hung Van: conceptualization; supervision; writing - review and
editing.
Minh Tuan Pham: supervision; resources; writing - review and editing.
```

---

## Hai câu hệ thống có thể hỏi

**"Bài này đã nộp tạp chí Wiley nào chưa?"**
→ Trả lời **thật**: có, IJNM, bị từ chối 05-09-2026, manuscript 7478947.
Không tự khai thì thôi, nhưng hỏi thẳng thì phải trả lời đúng.

**"Có bài liên quan nào đang được xét ở nơi khác không?"**
→ **Có** — Paper 1 ở IEEE TETC, `TETC-2026-05-0252`. Cover letter đã khai.

---

## Một chỗ lệch nhỏ, không chặn

Quy tắc ghi *"Authors should list all funding sources in the
**Acknowledgments** section"*, còn bài đang để **Funding** thành mục riêng.
Cả hai đều rõ ràng và toà soạn thường không bắt bẻ. Nếu muốn khớp tuyệt đối
thì đổi tiêu đề mục `Funding` thành `Acknowledgments` — nói tôi một tiếng.

## Đã kiểm

```
audit_p2_rebuild   299/299     mọi số trong bài tính lại được từ artifact
check_latex        sạch
Zenodo DOI         10.5281/zenodo.22893683   (kiểm qua API, metadata đúng)
Tài liệu           30 mục, 30 được trích, không mục rác, không trích treo
manuscript.pdf     12 trang, đọc tay trang 1 / 11 / 12
goi LaTeX          164 KB, khong con ghi chu noi bo, khong con file thua
cover_letter.docx  624 tu, dung bang cover_letter.txt
```

**Một việc duy nhất tôi không kiểm được:** giới hạn số trang của tạp chí.
Trang hướng dẫn tác giả của Wiley chặn truy cập tự động (lỗi 403). Bài
dài **12 trang** — bạn mở trang hướng dẫn xem có trần nào không trước khi bấm nộp.
