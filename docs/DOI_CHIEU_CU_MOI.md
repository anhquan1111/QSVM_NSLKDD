# Đối chiếu bản đã nộp ↔ bản revision

**TETC-2026-05-0252** · so sánh `paper/paper1/paper1.pdf` (đã nộp 05/2026, 11 trang) với
bản revision hiện tại (`paper/paper1/main_revision.tex`, 16 trang).

Mục đích: tách rõ **phần thêm mới** khỏi **phần cũ**, để quyết định nên giữ hay nên bỏ cái gì.

> **Bối cảnh về số trang.** TETC tính phí trang vượt từ trang thứ 13 và **không cho xin miễn**.
> Bản revision đang 16 trang, tức dôi 4 trang. Vì vậy cột "nên bỏ được không" ở dưới có ý
> nghĩa thực tế, không phải hỏi cho có.

---

## 1. Tổng quan cấu trúc

| | Bản đã nộp | Bản revision |
|---|---|---|
| Số trang | 11 | 16 |
| Hình | 10 | 9 |
| Bảng | 7 | 2 |
| Tài liệu tham khảo | 36 | 41 |
| Định lý / mệnh đề | 1 Theorem, 4 Proposition, 4 Definition, 1 Algorithm | 1 Lemma, 1 Definition, 1 Assumption, 1 Problem, 2 Remark |
| Phụ lục | không có | Phụ lục A (chứng minh Lemma 1) |

---

## 2. Từng mục: cũ → mới

| Mục | Bản đã nộp | Bản revision | Trạng thái |
|---|---|---|---|
| **I. Introduction** | Ba khoảng trống G1–G3, danh sách đóng góp | Viết lại; thêm tiểu mục **"Relation to the submitted version"** khai 5 khẳng định phải rút | ✍️ viết lại + **thêm mới** |
| **II-A. Quantum kernel** | Definition 1, Definition 2, Proposition 1, Proposition 2 | Gộp thành Eq (1)–(3); Prop 1 → fact (F1) | ✍️ viết lại, gọn hơn |
| **II-B. QML cho IDS** | Một đoạn ngắn + Table I (4 bài) | Viết lại, thêm survey 2026 và bài Cirillo et al. (R1 chỉ đích danh) | ✍️ viết lại |
| **II-C. Benchmark tổng quát** | *không có* | Bowles et al., Schnabel–Roth — hai bài R3 dẫn | ➕ **thêm mới** |
| **II-D. Cửa sổ lợi thế bị chặn** | *không có* | Carducci ICAD 2026 — bài R4 chỉ đích danh | ➕ **thêm mới** |
| **II-E. Định vị** | Table I: 4 bài, 3 cột | **Table I mới**: 5 bài, 13 dòng, đọc từ toàn văn | ✍️ dựng lại hẳn |
| **III-A. Feature map & cost** | Assumption 1, Eq (5) Q(n) | Eq (1)–(4) tường minh + Assumption 1 giữ nguyên ý | ✍️ viết lại rõ hơn |
| **III-B. Problem** | Problem 1 (tìm bộ ba K, n, r) | Problem 1 yếu hơn: **chấp nhận câu trả lời âm** | ✍️ viết lại |
| **III-C. Pipeline** | Fig 2, Fig 3, Table II (ký hiệu) | Mô tả bằng chữ; **bỏ cả 3** | ➖ **đã bỏ** |
| **III-E. Preliminaries** | Prop 1, 3, 4 kèm chứng minh | Hạ xuống fact (F1)(F2)(F3), chỉ trích dẫn | ✍️ hạ cấp (R3-3 yêu cầu) |
| **III-F. Lemma 1** | Proposition 2, chứng minh vắn tắt 3 dòng, **sai hệ số** | Lemma 1 phát biểu lại đúng cho r=1 + Remark 2 về r≥2 | 🔴 **sửa lỗi** |
| **III-G. Luật chọn số chiều** | Eq (6) J(n), Definition 4 (Pareto), Algorithm 1, **Theorem 1** | **Definition 1**: luật ba giai đoạn từ vựng, không trọng số | 🔴 **thay hẳn** (R4-2) |
| **III-H. Ablation** | Proposition 4 + kiểm định z hai mẫu | Giao thức ghép cặp trong từng run + Holm | ✍️ viết lại |
| **III-I. Erratum** | *không có* | Khai 4 lỗi của bản cũ, 2 do reviewer + 2 tự tìm | ➕ **thêm mới** |
| **IV. Experimental Setup** | 5 seed, QSVM cố định C=1.0 | 10 run, tune đối xứng, hai nhánh, hai tập test | ✍️ viết lại (R1-3, R2-3) |
| **V-A. C1** | Table III, Fig 4, Fig 5 (Pareto frontier) | Fig quét K + Fig luật ba giai đoạn (2 dataset) | ✍️ thay hình |
| **V-B. C2** | Table IV, Fig 6, Fig 7 | Giữ kết quả, thêm RF+XGBoost → **đổi thứ hạng** | ✍️ + baseline mới |
| **V-C. C3** | Table V, Fig 8 | Giữ, thêm RF/XGBoost → **đổi kết luận** | ✍️ + baseline mới |
| **V-D. C4** | Table VI, Fig 9 (N tới 1000) | N tới 10⁴, hai chế độ lấy mẫu, **crossover** | 🔴 **kết quả đảo chiều** |
| **V-E. Rare attacks** | *không có số nào* | Bảng F1 lớp hiếm cho cả 7 model | ➕ **thêm mới** (R4-5) |
| **V-F. Chuyển giao UNSW** | *chỉ nhắc trong Limitations* | Mục riêng + hình riêng | ➕ **thêm mới** (AE-3) |
| **V-G. Bề rộng mạch** | *không có* | K=80/n=8, 48/48 nghiêng cổ điển, cơ chế Gram | ➕ **thêm mới** (R3-4) |
| **V-E cũ. Shot noise** | Table VII riêng | Gộp vào V-B thành ba dòng | ➖ **đã gộp** |
| **VI. Regime map** | Fig 10 forest plot, 9 hàng | Fig 10 mới: **110 ô**, 3 tiểu mục | ✍️ mở rộng (R2-4) |
| **VI-C cũ. Decision rule** | Tiểu mục riêng | Gộp vào VI-C "Reading the map" | ➖ **đã gộp** |
| **VII. Limitations** | 4 tiểu mục, nhiều chỗ hứa "future work" | 4 tiểu mục, ba lời hứa cũ **giờ đã đo được** | ✍️ viết lại |
| **VIII. Conclusion** | Khẳng định lợi thế | Đóng khung lại thành ranh giới | ✍️ viết lại |
| **Phụ lục A** | *không có* | Chứng minh đầy đủ Lemma 1 | ➕ **thêm mới** |

---

## 3. Những gì ĐÃ BỎ khỏi bản cũ

Thầy xem có chỗ nào nên giữ lại không.

| Bỏ gì | Vì sao | Ai yêu cầu |
|---|---|---|
| **Theorem 1** | Chứng minh dùng tiền đề `F̃(4) > F̃(3)` trong khi Table III của chính bài ghi ngược lại. J cực đại tại n=2 chứ không phải n=4 | **R4 chỉ ra** |
| **Definition 4 (Pareto) + Algorithm 1 + Eq (6) J(n)** | Bước Pareto không lọc được ứng viên nào — V tăng, F̃ giảm, Q tăng đơn điệu nên mọi điểm đều Pareto-optimal | **R4 chỉ ra** |
| **Proposition 4 + kiểm định z** | Coi hai nhánh là độc lập trong khi chúng dùng chung tập train; và 5 tập con là quá ít cho xấp xỉ chuẩn | tự sửa |
| **Table II (bảng ký hiệu)** | Ký hiệu đã giải thích tại chỗ dùng | tiết kiệm trang |
| **Table III (dữ liệu Pareto)** | Bỏ theo Theorem 1; cột này còn **dán nhầm nhãn** (`1/DBI` nhưng số là thống kê ANOVA F) | tự khai |
| **Fig 5 (Pareto frontier)** | Thay bằng hình luật ba giai đoạn | R4-2 |
| **Fig 2, Fig 3 (sơ đồ đóng góp, pipeline)** | Không chứa dữ liệu; nội dung đã có trong chữ | tiết kiệm trang |
| **Fig 1 (sơ đồ mạch ZZ)** | R3 nói đây là cấu hình chuẩn phổ biến nhất — vẽ lại là thừa | tiết kiệm trang |
| **Table VII (shot noise)** | Gộp thành ba số trong V-B | tiết kiệm trang |

---

## 4. Những gì THÊM MỚI

Thầy xem có chỗ nào bỏ được để lấy lại trang không.

| Thêm gì | Trang ước tính | Vì sao thêm | Bỏ được không |
|---|---:|---|---|
| **V-D mở rộng: crossover** | ~1,2 | Kết quả chính của bản revision; trả lời trực tiếp R1-7 | ❌ không |
| **V-G: bề rộng mạch + cơ chế Gram** | ~1,0 | Câu trả lời mạnh nhất cho R3-4 và cho R3 nói chung | ❌ không |
| **V-F: chuyển giao UNSW** | ~0,8 | AE-3 và R1-2 đòi dataset thứ hai | ❌ không |
| **Table I định vị (5 bài)** | ~0,55 | R3-5 và AE-2 | ❌ không |
| **III-I: erratum 4 lỗi** | ~0,5 | Hai lỗi do R4 chỉ ra, bắt buộc phải trả lời | 🟡 rút gọn được ~0,2 (chi tiết đã có trong thư phản hồi) |
| **Phụ lục A: chứng minh Lemma 1** | ~0,4 | R3 chê "không có kết quả lý thuyết"; đây là thứ duy nhất mình có | 🟡 đẩy sang phụ lục trực tuyến được |
| **V-E: rare attacks** | ~0,35 | R4-5 hỏi thẳng, bản cũ không có số nào | ❌ không |
| **II-C + II-D: hai tiểu mục literature** | ~0,7 | R3-5 dẫn 2 bài, R4-1 dẫn 1 bài — đều đích danh | 🟡 gộp làm một được ~0,25 |
| **Table II: crossover qua hai nhánh** | ~0,25 | Chặn phản biện "chỉ do tune lại" | 🟡 chuyển thành 2 câu trong text |
| **Remark 1, Remark 2** | ~0,2 | Giải thích vì sao hạ cấp Proposition, và vì sao Lemma chỉ đúng r=1 | 🟡 rút gọn được |
| **"Relation to the submitted version" ở Intro** | ~0,25 | Khai 5 khẳng định phải rút ngay trang 1 | ❌ không — giấu xuống dưới là mất thiện chí |
| **6 tài liệu mới** | ~0,2 | Reviewer chỉ đích danh 4 bài; 2 bài còn lại tự tìm | ❌ không |

**Tổng nếu cắt hết những chỗ đánh 🟡: khoảng −1,0 trang.** Vẫn chưa đủ về 12 trang, phần còn
lại phải lấy từ việc gọn câu chữ chứ không bỏ nội dung.

---

## 5. Những gì GIỮ NGUYÊN

- **Tiêu đề** — không đổi
- **Danh sách tác giả và đơn vị** — không đổi (IEEE cấm đổi nếu không có văn bản đồng ý của EiC)
- **Assumption 1 (mô hình chi phí NISQ)** — giữ nguyên ý, viết lại cho rõ
- **Cấu hình mạch**: `K=20`, `n*=4`, `r=2`, full entanglement — không đổi
- **Kết quả C2 và C3 gốc** — số của QSVM không đổi một chữ số nào; chỉ thêm baseline mới vào
  cạnh chúng, và chính việc đó làm đổi thứ hạng

---

## 6. Ba chỗ đáng bàn nhất

**6.1 — Có nên giữ Phụ lục A không?** R3 chê bài "không có kết quả lý thuyết nào". Phụ lục A
là chứng minh thật duy nhất mình có, và chính lúc viết nó mới phát hiện Proposition 2 của bản
cũ sai hệ số. Bỏ đi thì tiết kiệm 0,4 trang nhưng mất luôn lập luận với R3.

**6.2 — Erratum nên dài hay ngắn?** Hiện 4 mục, ~0,5 trang. Thư phản hồi gửi ban biên tập đã
có bản đầy đủ. Trong bài có thể rút còn 4 câu. Rủi ro khi rút: reviewer đọc bài mà không đọc
thư thì không thấy mình tự khai.

**6.3 — Hai lỗi tự khai có nên khai không?** Table III dán nhầm nhãn và Proposition 2 sai hệ
số — **không reviewer nào bắt được**. Em đề nghị vẫn khai: nếu reviewer đối chiếu với dữ liệu
công khai mà tự tìm ra thì mất hết thiện chí, mà bài đang ở lần revision cuối cùng được phép.

---

## 7. Ghi chú về bản đánh dấu vàng

TETC bắt buộc nộp **ba file**: bản sạch, **bản đánh dấu phần thay đổi bằng nền vàng**, và thư
phản hồi. Bảng ở mục 2 cho thấy gần như mọi mục đều rơi vào "viết lại" hoặc "thêm mới" — nên
bản đánh dấu sẽ gần như vàng toàn bộ, tự nó không truyền đạt được gì.

Riêng phần **tài liệu tham khảo thì bắt buộc phải tô vàng từng mục thay đổi** và phải giải
trình trong một mục riêng của thư phản hồi. Phần đó gồm: 6 mục thêm, 1 mục gỡ (Rahman et al.,
không xác minh được là có thật — R2 phát hiện), 1 mục sửa số hiệu bài ([15] `116990F` →
`116990B`).
