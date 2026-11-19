# Paper 1: kế hoạch nộp lại Quantum Machine Intelligence

Viết 19-11-2026. Tạp chí đã chốt: xem `docs/PAPER1_CHON_TAP_CHI.md`.

## Bốn giai đoạn

| GĐ | Việc | Cổng soát cuối giai đoạn |
|---|---|---|
| **1** | Sửa khoa học theo R3 + đối chiếu Cirillo 2026 (chi tiết bên dưới) | Bảng số mới khớp CSV; danh sách câu phải đổi |
| 2 | Viết lại gọn theo mẫu Springer Nature: bỏ mọi chỗ nhắc bản cũ và phản biện, tóm tắt 150–250 từ, tiêu đề có UNSW-NB15 | Bản PDF compile được; audit chữ sạch |
| 3 | Bộ nộp: PDF, nguồn LaTeX, cover letter, khai AI (mục Methods nếu dùng AI viết nội dung) | Thầy Vân duyệt |

GĐ 0 (chọn tạp chí) đã xong.

**Gốc để sửa:** `paper/paper1/` (bản hoàn chỉnh = bản R1 đã nộp + hình sửa chồng chữ + nhiễu 10 run).
`paper/paper1/v2_submitted/` đóng băng, không sửa. GĐ 1 chỉ sinh số liệu và danh sách câu cần đổi;
câu chữ áp vào bài ở GĐ 2 (viết lại một lần, không sửa hai lần).

## Giai đoạn 1: chi tiết

### 1.1 Độ nhạy khi bỏ dòng test trùng train (R3, việc nặng nhất)

**Đo trước (19-11):** dòng test có bộ đặc trưng thô y hệt một dòng train:

| Tập | Test | Trùng train | Tỉ lệ | Ghi chú |
|---|---|---|---|---|
| UNSW-NB15 | 82.332 | 20.851 | **25,3 %** | 16.452 là tấn công (36 % số tấn công trong test) |
| NSL-KDD | 22.544 | 664 | 2,95 % | có `snmpgetattack` trùng hệt dòng train |

**Cách làm:**
1. Viết `runners/run_dedup_sensitivity.py`: đọc siêu tham số đã chỉnh trong
   `results/*/c4_revision/cache/*.json` (không dò lại), huấn luyện lại 7 mô hình, cùng seed, mọi N
   và mọi run; dự đoán trên toàn tập test và **lưu dự đoán từng dòng** (lần trước không lưu).
2. Chấm trên hai tập: test đầy đủ và test đã bỏ dòng trùng. Đếm lại các ô của bản đồ regime
   (cùng Wilcoxon ghép cặp, cùng hiệu chỉnh), ra bảng "trước / sau" cho từng ô.
3. Thử nhỏ trước (1 N, 1 run), rồi chạy đủ qua `dieuhanh chay-nang` trong khung 0h–6h30.
   Lần chạy gốc tốn khoảng 2,3 giờ (UNSW) và 3,3 giờ (NSL-KDD), có cả phần dò siêu tham số;
   lần này không dò nên dự kiến ít hơn.

**Đạt khi:**
- Huấn luyện lại trên test đầy đủ ra **đúng** số cũ trong cache (mọi ô lệch ≤ 1e-4); lệch thì dừng, tìm
  nguyên nhân trước khi dùng số sau khi bỏ trùng.
- Có bảng: số ô đổi kết luận (nghiêng quantum / nghiêng cổ điển / không kết luận) sau khi bỏ trùng,
  tách theo tập và theo protocol.
- Số trong bài sinh từ CSV bằng script, không gõ tay.

### 1.2 Bỏ "exponential concentration", tương quan ≠ nhân quả (R3)

Chỗ cần đổi trong `paper/paper1/sections/`: `02_background.tex` (dòng ~31–36), `05_results.tex`
(~285–294), `07_limitations.tex` (~77–89), `08_conclusion.tex` (~42, 58).
Ta chỉ đo vài độ rộng mạch, nên chỉ được nói "Gram matrix tập trung hơn khi tăng độ rộng, và đi
cùng F1 thấp hơn" kèm r và khoảng tin cậy; không nói "lũy thừa", không dùng động từ nhân quả.

**Đạt khi:** thêm luật vào `runners/audit_prose.py`: không còn "exponential" gắn với số đo của ta;
không còn "destroys / causes / drives / explains" nối độ tập trung với F1.

### 1.3 Thay "parity" bằng "không khác biệt có ý nghĩa" (R3)

Chỗ cần đổi: tóm tắt, `01_introduction.tex` ~67, `05_results.tex` ~199, `06_regimemap.tex` ~52,
`08_conclusion.tex` ~24. Mỗi chỗ ghi Δ và khoảng tin cậy 95 %.

**Đạt khi:** audit không còn "parity / on par / tied" (trừ "parity functions" toán học ở phụ lục).

### 1.4 Mâu thuẫn rare-attack enrichment / crossover / 7 trên 10 run (R3)

Ứng viên đã thấy: `01_introduction.tex` ~67–69 và `05_results.tex` ~173–187 (nhánh tăng mẫu tấn
công hiếm "không quyết được" nhưng vẫn ra kết luận ở 4/30 ô); `06_regimemap.tex` ~61, 86 (ô C3 lấy
từ pool tăng mẫu); `05_results.tex` ~239 ("7/10 ở ε = 0,1").
**Cần nguyên văn ý R3** để biết chính xác họ thấy mâu thuẫn ở đâu (xem "Cần chủ nhân").

**Đạt khi:** mỗi khẳng định xuất hiện ở ≥ 2 chỗ trong bài dùng cùng một con số, lấy từ một CSV;
audit đối chiếu được.

### 1.5 Mô phỏng nhiễu chạy lặp (R3): đã làm, chỉ cần đưa vào

Đã chạy 10 run (commit `8f100a0`, kiểm độc lập `runners/verify_noise10.py` 40/40). Số mới: QSVM-ZZ
trung bình 0,8501 dưới nhiễu `FakeManilaV2` (bản R1 ghi 0,8728 là run cao nhất). Đã có trong
`paper/paper1/sections/05_results.tex`.

**Đạt khi:** chạy lại `verify_noise10.py` vẫn 40/40; bài nói rõ chỉ một mô hình nhiễu (một backend),
không suy rộng sang phần cứng thật.

### 1.6 Đối chiếu Cirillo, Esposito, Seo 2026 (mới, do chọn QMI)

Bài *Benchmarking quantum machine learning methods for intrusion detection on noisy quantum
computers*, QMI, DOI 10.1007/s42484-026-00379-4 (đăng mở). Đọc toàn văn, lập bảng: tập dữ liệu, mô
hình, số qubit, nhiễu / phần cứng thật, giao thức thống kê, kết luận.

**Đạt khi:** mỗi ô có trích dẫn trang hoặc mục của bài họ; nêu ≥ 3 điểm khác cụ thể; chỗ nào kết
quả giống họ thì trích họ, không nhận là mới.

## Giai đoạn 2: chi tiết (chủ nhân gật 19-11)

**Đầu vào:** `paper/paper1/` (chỉ đọc) + danh sách câu cần đổi trong `docs/PAPER1_GD1_KET_QUA.md`
(1.1–1.4, 1.6). **Đầu ra:** thư mục mới `paper/paper1_qmi/`, mẫu LaTeX Springer Nature (`sn-jnl.cls`, tải
từ trang hướng dẫn tác giả của Springer), hình dùng lại từ `paper/paper1/figs_revision/`.

**Các bước (mỗi bước một commit):**
1. Dựng khung: tải mẫu Springer, `main.tex` + `sections/`, đưa hình và danh mục tham khảo sang.
   **Xong 19-11:** mẫu `sn-jnl` 3.1 (12-2024), 7 mục + declarations + phụ lục (mỗi file ghi nguồn cũ, câu
   phải đổi, số từ mục tiêu), `runners/make_qmi_zip.py` đóng gói Overleaf (15 file), audit chữ ra 0.
   Chưa compile thử trên Overleaf. Danh mục tham khảo vẫn kiểu IEEE (`thebibliography`).
2. Viết lại từng mục theo thứ tự: kết quả → bản đồ regime → phương pháp → giới thiệu và liên quan (đối
   chiếu Cirillo 2026) → giới hạn → kết luận → tóm tắt (viết cuối, khi số đã chốt).
3. Mỗi mục xong thì chạy hai máy kiểm: `audit_wording_r3.py paper/paper1_qmi` (chữ) và kiểm số đối chiếu
   CSV; bảng số sinh bằng script, không gõ tay.
   Thêm soát giọng văn theo skill Humanizer (`~/projects/channel_3_asian_explained/.claude/skills/humanizer/SKILL.md`,
   26 dấu hiệu văn AI; chủ nhân 20-11): mỗi mục ghi các dấu hiệu đã sửa. Không có máy chấm điểm, Claude tự soát.
4. Đọc lại toàn bài một lượt như người phản biện mới (không biết bản cũ).

**Đạt khi:**
- `uv run python runners/audit_wording_r3.py paper/paper1_qmi` ra 0 (không "exponential" về số đo của
  ta, không câu nhân quả, không "parity", không "10/10" thiếu "7/10", không nhắc phản biện / bản cũ).
- Tóm tắt 150–250 từ, tiêu đề có UNSW-NB15; tóm tắt đưa khối 42 ô tự nhiên lên trước tổng 110 ô.
- Mọi con số trong bài có trong một CSV của repo; câu bỏ trùng (1.1) và số 664 / 610 đã thay đúng.
- Độ dài mục tiêu ≤ 9.000 từ thân bài (bản cũ ~13.100; AE TETC chê dài), phụ lục tách riêng.
- Compile được: tải gói `.zip` lên Overleaf (máy không có LaTeX; cài TeX tại máy phải hỏi trước).

**Khai báo AI (QMI):** dùng LLM viết nội dung thì phải khai ở mục Methods; chỉ sửa ngữ pháp, văn phong thì
không cần. AE của TETC đã chê "mùi AI".

**Cách viết (chốt 19-11, chủ nhân chọn (a)):** Claude soạn nháp từng mục; chủ nhân và thầy Vân sửa lại bằng
giọng mình, riêng tóm tắt, giới thiệu, kết luận viết lại hẳn; bài khai dùng LLM ở mục Methods. Đã cân nhắc
và bỏ (b) "chủ nhân tự viết, Claude chỉ soát" vì tốn thời gian chủ nhân hơn.

## Thứ tự và thời gian

1. 1.6 và lấy thư từ chối (rẻ, làm trước; 1.6 có thể ảnh hưởng cách định vị).
2. 1.1: viết script + thử nhỏ (ban ngày), chạy đủ (đêm, hàng đợi việc nặng).
3. 1.2–1.5: lập danh sách câu cần đổi + luật audit, song song với 1.1.
4. Cổng cuối GĐ 1: bảng trước/sau bỏ trùng + danh sách câu đổi, đưa chủ nhân xem.

## Cần chủ nhân

- **Thư từ chối 11-11-2026 nguyên văn** (nhất là ý R3): máy chỉ có bản tóm tắt trong bộ nhớ.
  Dán vào `docs/Review_R1_tu_choi.md` (giống `docs/Review.md` của vòng trước).
