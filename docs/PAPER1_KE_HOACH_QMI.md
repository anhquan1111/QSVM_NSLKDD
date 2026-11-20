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
   **Kết quả xong 20-11** (`sections/04_results.tex`, ~2.300 từ; hình `figs/`, bảng `tables/` sinh bằng
   `runners/make_qmi_tables.py`). Thêm tiểu mục bỏ dòng test trùng train (`sec:res-dedup`, bảng
   `tab:dedup`: 4/108 ô đổi, không ô nào đổi chiều). Kiểm: `audit_c4.py` 100/100, `audit_figures.py` 36/36,
   số mới (nhiễu, tấn công hiếm, bỏ trùng, nhánh tăng mẫu) đối chiếu CSV bằng tay; audit chữ 0 (luật "phần
   cứng tốt hơn" thêm ngoại lệ cho câu đã rào "did not test / no conclusion").
   Sửa so với bản cũ: nhiễu ghi đúng giao thức (200 dòng train, C = 3, 44 CNOT sau transpile; giải thích vì
   sao 0,8329 ≠ 0,8469); Cirillo: tập chính là ToN_IoT (bản cũ ghi "cùng tập"), bỏ câu "suy giảm sau ~60
   cổng" và "họ quy cho lỗi cổng" vì chưa đối chiếu lại bài họ.
   Humanizer đã sửa: (1) Not X but Y ("K = 20 không phải tối ưu"); (2) câu kết lặp ý (4 chỗ: ablation, dịch
   chuyển, UNSW, độ rộng); (4) câu dẫn trống ("Four further analyses…"); (11) bị động ở mục nhiễu.
   Methods phải thêm: bảng `tab:protocol`, số 0,804, định nghĩa frozen / tuned (ghi trong `03_methods.tex`).
   **Bản đồ regime xong 20-11** (`sections/05_regime_map.tex`, ~860 từ; hình `figs/fig_regime_map.tex`
   caption mới; bảng `tab:multiplicity` sinh từ `regime_map_multiplicity.csv`). Khối 42 ô tự nhiên
   (11/9/22) đứng trước tổng 110 ô (21/21/68), nói rõ 68 ô từ pool tăng mẫu (10/12/46). Tiểu mục độ nhạy
   hiệu chỉnh (R3): BH cả khối 21/18/71, ba ô đổi đều từ "nghiêng cổ điển" sang "không kết luận" (RF
   N = 500, 1000 tự nhiên; XGBoost ở 70 % tấn công), không ô nghiêng QSVM nào đổi; Holm cả khối 0 ô vì
   p nhỏ nhất 0,00195. Mỗi khuyến nghị ghi rõ đứng được dưới cách hiệu chỉnh nào. Đối chiếu từng ô bằng
   p thô; SVM-RBF không ô nào nghiêng QSVM kể cả không hiệu chỉnh (p thô nhỏ nhất phía dương 0,13).
   Bỏ so với bản cũ: "parity"; "closed from above by the physics … better hardware"; câu "điều kiện hay
   gặp nhất trong tài liệu" (ô 50/50, không có nguồn); câu "ranh giới … sẽ đúng ngoài hai tập" (nói quá).
   Humanizer đã sửa: (1) Not X but Y ("not seeing more; it is resolving less"); (4) phóng đại ý nghĩa
   ("the honest summary", "correct and useless", "sharpest … least expected"); câu kết hoành tráng cuối mục.
   **Phương pháp xong 20-11** (`sections/03_methods.tex`, ~1.700 từ; bảng `tables/protocol.tex` gõ tay,
   mỗi dòng đối chiếu config/code, ghi nguồn đầu file). Mọi `\ref` trong bài đã có nhãn. Bỏ: Problem /
   Assumption, mục "Corrections to the Submitted Version", lịch sử Pareto/J(n); Lemma 1 sang phụ lục.
   **Sai trong bản cũ, đã sửa:** (1) bản cũ ghi nhãn "năm lớp", code dùng nhãn nhị phân (`label_binary`,
   `src/c4_pipeline.py`); F1 lớp hiếm = 2R/(1+R) vì mọi dòng hiếm đều là attack. (2) Bản cũ ghi nhánh tuned
   dò trên tập tune 2.000 dòng; thật ra dò bằng 5-fold CV trên chính N dòng train, tập 2.000 dòng chỉ cho nhánh
   frozen. (3) Bảng giao thức cũ ghi hình độ rộng "enriched, 1000, test 300" cho cả hình; panel (a) thật là quét
   N ở K = 80 (natural, test đầy đủ, N tới 20.000), panel (b) một tập con 300 dòng. (4) Config ghi kiểm kernel
   trên 200 mẫu; code kiểm 150 điểm ngẫu nhiên. Bỏ câu chưa kiểm: "các bài báo ~0,99 dùng chia ngẫu nhiên",
   "XGBoost lệch ±0,001 giữa các máy".
   Humanizer đã sửa: (4) phóng đại ("not decorative", "mandatory trade"); (1) Not X but Y ở đoạn pipeline;
   câu tự khen độ chặt ("strictly more conservative").
   Còn chờ: (a) script sinh `results/unsw/c4_revision/u1_c1_selection_unsw.json` không có trong repo (JSON ghi
   lấy mẫu kiểu C1 trên tập train, chưa kiểm bằng code); (b) tag phát hành điền khi nộp; (c) đoạn khai LLM
   chủ nhân và thầy xác nhận; (d) phụ lục phải viết Lemma 1 + chứng minh (Methods trỏ `app:proofs`).
   **Giới thiệu + Liên quan xong 20-11** (nháp để chủ nhân / thầy viết lại hẳn phần Giới thiệu;
   `01_introduction.tex` ~820 từ, `02_related.tex` ~950 từ, bảng `tables/positioning.tex` từ novelty matrix cũ).
   Đóng góp ghi là giao thức benchmark + bản đồ verdict, không nhận lợi thế lượng tử (R2). Cirillo: chỉ giữ điều
   có trong bảng 1.6; liệt kê thẳng những gì họ đã làm trước ta; 5 điểm khác. Bỏ mục Carducci (chỉ đọc được tóm
   tắt), bỏ "Relation to the submitted version", bỏ câu "We take the reviewers' point". Gillani: sửa lập luận cũ
   (bản cũ ngầm nói ta đã thử ở toàn bộ tập train; thật ra QSVM chưa chạy ở 125.973 dòng).
   Humanizer đã sửa: (1) Not X but Y ("headline is a map, not a number", "not its novelty of apparatus but…");
   (4) phóng đại ("widening destroys the kernel", "changes what the field believes"); câu kết hoành tráng.
   Còn chờ: gỡ `carducci2026` khỏi danh mục khi soát tham khảo; chưa đối chiếu lại toàn văn Bowles / Schnabel /
   Gillani (bảng định vị lấy nguyên từ bản TETC).
   **Giới hạn xong 20-11** (`sections/06_limitations.tex`, ~760 từ, 6 đoạn: mô phỏng không phải phần cứng,
   sức mạnh thống kê, cỡ tập train, dữ liệu, lựa chọn thiết kế cố định, baseline). Không lặp số của Kết quả,
   chỉ trỏ về mục; mọi số đã có ở Phương pháp / Kết quả / Bản đồ. Thêm so với bản cũ: 10 run không bác bỏ
   được ô nào dưới Holm cả khối, không có kiểm định tương đương; QSVM chưa chạy ở toàn bộ tập train; nhãn
   nhị phân (R2L/U2R chỉ chấm là attack); trùng gần đúng và trùng trong tập train không bỏ (code không có
   `drop_duplicates` trên dòng dữ liệu). Bỏ: "NISQ-aware", câu "code có sẵn đường chạy phần cứng" (chưa
   kiểm), 47,3 % trùng trong train UNSW (chưa đối chiếu lại). Sửa sai lý của nháp: câu "thứ hạng độ rộng
   theo chi phí có thể đổi trên thiết bị khác" (quy tắc chỉ dùng việc chi phí tăng theo n).
   Humanizer đã sửa: (2) câu lặp ý ("An inconclusive cell is therefore…"); bộ ba "persists, widens or
   closes"; không có câu kết hoành tráng.
   **Kết luận xong 20-11** (`sections/07_conclusion.tex`, ~385 từ; nháp để chủ nhân / thầy viết lại hẳn).
   Bốn đoạn: làm gì + đếm bản đồ (khối 42 ô trước, BH cả khối 21/18/71); ba phát hiện kiểm được ở dữ liệu
   khác (đảo chiều so với XGBoost, quy tắc độ rộng chuyển sang UNSW kèm 7/10, mạch 8 qubit thua 48/48 +
   "goes with"); giới hạn một câu; ba câu hỏi mở (phần cứng, projected kernel \cite{ref19}, vì sao đảo
   chiều chỉ ở NSL-KDD). Bỏ so với bản cũ: số BH 17/15/78 (hiệu chỉnh hai lần), "parity", "operating window
   closed from above", "useful width bounded well below where hardware limits bite", "NISQ-aware", câu nhắc
   rút 5 khẳng định / erratum, "released code contains the execution path".
   Humanizer đã sửa: (4) phóng đại ("the one we would most like others to test", "specific enough");
   không câu kết hoành tráng.
   **Tóm tắt xong 20-11** (`main.tex`, 246 từ, không trích dẫn, không công thức; nháp để chủ nhân / thầy
   viết lại hẳn). Khối 42 ô tự nhiên (11/9/22) trước tổng 110 ô (21/21/68). Đảo chiều ghi đúng phạm vi: so
   với XGBoost trên cùng embedding 4 thành phần, NSL-KDD, còn sau khi bỏ trùng, không có ở UNSW, không khác
   biệt có ý nghĩa với XGBoost đủ 122 đặc trưng. Không ghi "10/10" (máy kiểm đòi kèm 7/10; tóm tắt chỉ nói
   quy tắc chọn 6 qubit ở UNSW). Câu cuối: mọi kernel tính bằng mô phỏng cổ điển.
   **Phụ lục xong 20-11** (`sections/appendix.tex`, ~420 từ): Lemma 1 (khai triển bậc hai ở r = 1) + chứng
   minh đầy đủ + Remark r ≥ 2 + đoạn kiểm số. Chạy lại `runners/verify_lemma1.py`: 15/15 PASS, mã thoát 0.
   **Sửa số cũ:** R² của dạng hai số hạng ở r = 2 là 0,73–0,94 (bản cũ ghi 0,60–0,94); bậc sai số
   3,76–3,94 (bản cũ "3,9"); sai số tại ‖Δ‖ = 10⁻³ tối đa 5,2×10⁻¹¹. Chứng minh: phần dư bậc ba vào qua b²
   là bậc sáu (bản cũ ghi "bậc bốn sau khi bình phương", lỏng). Bỏ câu "SVM-Poly2 là đối thủ cổ điển sắc
   nhất … Kết quả xác nhận" (Phương pháp chỉ dùng Lemma để chọn baseline). Việc (d) ở mục Phương pháp đã xong.
   Tổng thân bài (mục 1–7, không tính chú thích hình, bảng) ~7.570 từ, dưới trần 9.000.
   **Soát danh mục tham khảo xong 20-11** (`bibliography.tex`, 35 mục = 35 khóa được trích). Gỡ 3 mục không
   ai trích: `carducci2026`, `ref8` (Preskill NISQ), `ref27` (web IBM). Sắp lại theo thứ tự trích đầu tiên
   (trước đó mục trích đầu tiên đứng thứ 23). Sửa lỗi chép từ PDF có từ bản TETC: đuôi rác "IEEE TRANSACTIONS
   ON EMERGING TOPICS IN COMPUTING 11" ở `ref10`; "K--bler" → Kübler; số trang có dấu cách ("21 954");
   mất gạch nối (quantumenhanced, quantumclassical ×2, kerneltarget, AlNemrat); 28 cặp ngoặc kép thẳng
   → ``…''. Còn chờ: `ref29` Qiskit chỉ ghi "Qiskit Contributors, 2024" (nên đổi sang bài Qiskit chính
   thức, cần chủ nhân gật); chưa mở lại toàn văn Bowles / Schnabel / Gillani; vẫn `thebibliography` kiểu
   IEEE, chưa sang `.bib` + `sn-mathphys-num`.
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

- Không có việc chờ (thư từ chối đã lưu ở `docs/Review_R1_tu_choi.md` ngày 20-11).
