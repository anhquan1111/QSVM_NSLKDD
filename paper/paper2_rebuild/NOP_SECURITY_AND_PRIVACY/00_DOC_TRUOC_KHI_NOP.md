# Nộp Paper 2 — Security and Privacy (Wiley)

Mọi thứ cần để nộp đều nằm trong thư mục này. Không phải đi tìm đâu khác.

**Dựng ngày 22-09-2026.** Nếu sau này sửa bài thì phải chạy lại
`python scripts/build_bo_nop_paper2.py` để làm mới thư mục này, nếu không
sẽ nộp nhầm bản cũ.

---

## File trong đây

| File | Dùng để |
|---|---|
| `01_ban_thao.pdf` | Bản thảo — tải lên ô *Main Document* |
| `02_nguon_latex.zip` | Nguồn LaTeX — tải lên khi hệ thống hỏi source files |
| `03_cover_letter.txt` | **Dán thẳng** vào ô Cover Letter (dễ nhất) |
| `03_cover_letter.tex` | Nếu hệ thống bắt nộp cover letter dạng PDF thì compile file này |

---

## Đường vào

Vào thẳng trang tạp chí rồi tìm nút **Submit an Article**:

**https://onlinelibrary.wiley.com/journal/24756725**

Hướng dẫn tác giả (nên mở xem giới hạn độ dài trước):

**https://onlinelibrary.wiley.com/page/journal/24756725/homepage/forauthors.html**

> ⛔ **ĐỪNG bấm nút `start manuscript transfer`** trong email từ chối của IJNM.
> Nó chuyển kèm hồ sơ quyết định của IJNM sang tạp chí mới, mà **không** mang
> theo phản biện nào — vì bài bị loại thẳng, không có phản biện. Nộp mới cho
> điểm khởi đầu tốt hơn. Nếu đã lỡ mở một bản nháp transfer thì vào xoá đi.

---

## Các ô phải điền trong hệ thống

Chép nguyên, không cần sửa.

**Title**
```
A Reliability and Calibration Benchmark of QSVM Against Strong Tabular
Learners on NSL-KDD and UNSW-NB15
```

**Article type** — `Original Paper`

**Authors** (đúng thứ tự này)

| # | Tên | Vai trò |
|---|---|---|
| 1 | Nang Hung Van Nguyen | |
| 2 | Quan Tran Anh Vo | **corresponding author**, ORCID `0009-0000-9420-1767` |
| 3 | Quang Anh Nguyen | |
| 4 | Minh Tuan Pham | |

Đơn vị cả bốn: `University of Science and Technology – The University of Danang, Danang 550000, Vietnam`

**Keywords** (6)
```
Quantum machine learning; quantum kernel; calibration; intrusion detection;
NSL-KDD; UNSW-NB15
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
Nang Hung Van Nguyen: conceptualization; supervision; writing - review and
editing.
Minh Tuan Pham: supervision; resources; writing - review and editing.
```

---

## Hai câu hệ thống có thể hỏi

**"Bài này đã nộp tạp chí Wiley nào chưa?"**
→ Trả lời **thật**: có, IJNM, đã bị từ chối 05-09-2026 (manuscript 7478947).
Không tự khai thì thôi, nhưng hỏi thẳng thì phải trả lời đúng.

**"Có bài liên quan nào đang được xét ở nơi khác không?"**
→ **Có** — Paper 1 ở IEEE TETC, mã `TETC-2026-05-0252`. Cover letter đã khai
sẵn, chỉ cần nhắc lại.

---

## Chưa kiểm được

Tôi **không đọc được** trang author guidelines của tạp chí (Wiley chặn truy
cập tự động, lỗi 403). Nên hai điều sau bạn phải **tự mở xem**:

1. **Giới hạn độ dài** cho Original Paper — bài đang 12 trang IEEEtran hai cột
2. Xác nhận tạp chí nhận **free format** — trang transfer có ghi "Free format"
   nên gần như chắc chắn được, nhưng nên tự xác nhận

---

## Đã kiểm

```
audit_p2_rebuild   296/296     mọi số trong bài tính lại được từ artifact
check_latex        sạch
Zenodo DOI         10.5281/zenodo.22893683   (đã kiểm qua API, metadata đúng)
Tài liệu           30 mục, 30 được trích, không mục rác, không trích treo
```
