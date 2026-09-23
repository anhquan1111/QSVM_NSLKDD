# Nộp Paper 2 — Security and Privacy (Wiley)

Mọi thứ cần để nộp đều nằm trong thư mục này.

Checklist này viết theo **quy tắc thật** của tạp chí (`paper/quytac.md`),
không phải phỏng đoán.

> ⚠️ **`manuscript.pdf` trong đây ĐÃ CŨ.** Sau lần build đó bài còn đổi:
> tên thầy Vân, đơn vị + email 4 tác giả, và mục **Use of AI Tools**. **Build lại trên Overleaf** rồi chạy
> `python scripts/build_bo_nop_paper2.py` để làm mới thư mục này.

---

## File trong đây

Tên file **tiếng Anh** có chủ ý: tên file hiện ra trước mắt biên tập khi họ
tải về. Thư mục và file này thì tiếng Việt vì không bao giờ được tải lên.

| File | Nhãn phải chọn khi upload |
|---|---|
| `manuscript.pdf` | **Main Document – LaTeX PDF** |
| `main_document.tex` | **Main Document – LaTeX .tex File** |
| `latex_supplementary.zip` | **LaTeX Supplementary File** |
| `cover_letter.txt` | dán thẳng vào ô Cover Letter |
| `cover_letter.tex` | nếu bắt nộp dạng PDF |

Ba nhãn đầu là **nguyên văn** tên nhãn trong hệ thống. Quy tắc mục 4 ghi rõ:
nộp LaTeX thì phải kèm **cả** file `.tex` **và** bản PDF, file phụ trợ gắn
nhãn *LaTeX Supplementary File*.

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
```
