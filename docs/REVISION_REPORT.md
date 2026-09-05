# Báo cáo bản revision — Paper 1, IEEE TETC

**Bản thảo:** TETC-2026-05-0252 — *NISQ-Aware Quantum Kernel SVM for Network Intrusion
Detection: A Regime-Specific Benchmark on NSL-KDD*
**Quyết định:** Major revision, 14-08-2026 · **Hạn nộp lại:** 13-10-2026
**Lưu ý chính sách:** TETC **không cho major revision lần hai**.

Tài liệu này gộp toàn bộ 16 file ghi chú làm việc trong quá trình revision thành một bản
duy nhất. Bản gốc từng file vẫn còn trong lịch sử git (`git log -- docs/revision/`).

---

## 1. Tóm tắt cho người đọc vội

Chạy lại toàn bộ thí nghiệm dưới giao thức đã sửa cho thấy **năm khẳng định của bản đã nộp
không đứng vững** và phải rút. Bù lại, bản mới có ba kết quả mà bản cũ không có, và toàn bộ
số liệu đều kiểm chứng lại được bằng script trong repo.

**Câu chuyện của bài đổi từ "chúng tôi có lợi thế lượng tử" sang "đây là ranh giới của lợi
thế đó".** Đó chính là thứ AE và ba trên bốn reviewer yêu cầu.

Con số trung tâm: trên **110 so sánh có kiểm soát** — **21 nghiêng về QSVM, 21 nghiêng về mô
hình cổ điển, 68 không kết luận được**.

---

## 2. Năm khẳng định phải rút

| Bản đã nộp | Số đo được sau khi làm lại |
|---|---|
| Lợi thế ở **chế độ ít dữ liệu** | **Ngược lại.** Cổ điển thắng ở N nhỏ; thứ tự đảo chiều trong khoảng N = 2000–5000 |
| "+6.7 điểm rare-attack, Cohen's d = +0.68" | **Không tái tạo được.** Code cũ không hề tính metric nào cho lớp hiếm |
| Theorem 1: n\* = 4 cực đại hoá J | **Sai.** J cực đại tại n = 2 (J = 0.551) — đúng như R4 chỉ ra |
| QSVM-ZZ 0.854 > SVM-RBF 0.838 | Thêm baseline mạnh: **XGBoost 0.8503 > QSVM-ZZ 0.8469** > RF 0.8446, khoảng tin cậy chồng nhau |
| "Quantum advantage is real and measurable" | 21 / 21 / 68 trên 110 so sánh |

Nguyên nhân gốc của khẳng định thứ nhất: **tập huấn luyện của bản cũ giàu lớp hiếm gấp ~12
lần tỉ lệ tự nhiên** (10% so với 0,83%) và điều đó chưa từng được ghi trong bài. Ở chế độ làm
giàu thì không có crossover; ở chế độ tự nhiên thì có.

---

## 3. Bốn lỗi trong phần lý thuyết

Hai lỗi do reviewer chỉ ra, hai lỗi tự tìm thấy. Cả bốn đều được **tự khai trong bài** (mục
erratum của Sec. III) chứ không sửa lặng lẽ.

**(i) Theorem 1 sai** — R4 chỉ ra. Chứng minh dùng tiền đề `F̃(4) > F̃(3)` trong khi Table III
của chính bài ghi `0.471 < 0.628`. Đã bỏ hẳn Theorem 1 và hàm mục tiêu J.

**(ii) Bước Pareto không lọc gì** — R4 chỉ ra. V(n) tăng đơn điệu, F̃(n) giảm, Q(n) tăng, nên
mọi ứng viên đều Pareto-optimal. Thay bằng **luật ba giai đoạn từ vựng**, không trọng số:
`V(n) ≥ 0.85` → `KTA ≥ 0.95·KTA_max` → `min Q(n)`.

**(iii) Proposition 2 sai hệ số** — *không reviewer nào bắt*, tự tìm khi chuyển chứng minh
xuống phụ lục. Bản cũ viết `K = 1 − r²ΣΔᵢ² − r²ΣΔφᵢⱼ² + O(‖·‖⁴)`. Sai hai chỗ: hệ số đúng là
**1 và 1/4** (không bằng nhau), và **tiền tố r² không đúng với bất kỳ r ≥ 2 nào**. Kiểm số:
ở r = 1 khớp chính xác 1.000 / 0.250 với R² = 1.000000; công thức cũ chỉ giảm sai số bậc 2
thay vì bậc 4. Điểm làm việc của bài là r = 2 — đúng chỗ công thức cũ hỏng nặng nhất.

**(iv) Table III dán nhầm nhãn cột** — *không reviewer nào bắt*. Caption ghi
`F̃(n) = 1/DBI(n)` nhưng số trong cột là thống kê ANOVA F.

---

## 4. Ba kết quả mới

**4.1 — Thứ tự đảo chiều theo lượng dữ liệu.** Dưới tỉ lệ lớp tự nhiên, QSVM-ZZ là mô hình
gần chót ở N = 100 (0.6989, so với XGBoost 0.7802) và **dẫn đầu ở N = 10⁴** (0.7855 so với
XGBoost 0.7706). Chênh lệch ghép cặp so với XGBoost đổi dấu giữa N = 2000 và 5000
(−0.0129 → +0.0100), có ý nghĩa sau hiệu chỉnh Holm tại N = 5000 (p = 0.027) và N = 10⁴
(p = 0.0078).

Ba điều kiện kèm theo, đều ghi trong bài:
- **Không phải tạo tác của việc tune lại**: đổi dấu ở **6/6 tổ hợp** {XGBoost, RF, SVM-RBF} ×
  {đóng băng siêu tham số, tune lại mỗi N}.
- **Không đồng đều giữa các baseline**: so với SVM-RBF thì chênh lệch có chuyển dương nhưng
  **không ô nào đạt ý nghĩa** — QSVM chưa từng thắng SVM-RBF một cách chứng minh được.
- **Là tính chất của tỉ lệ lớp tự nhiên**: làm giàu lớp hiếm lên 10% thì 26/30 ô không kết
  luận được và không còn crossover.

**4.2 — Luật chọn số chiều chuyển giao được.** Cùng một luật, không sửa một tham số nào:
`n* = 4` trên NSL-KDD, `n* = 6` trên UNSW-NB15 (V = 0.9044, KTA = 0.1986, 60 cổng hai qubit),
lặp lại đúng trên 10/10 tập con độc lập. C1 vì thế là một **thủ tục**, không phải hằng số
n = 4 mang theo từ một thí nghiệm.

**4.3 — Ranh giới đo được, kèm cơ chế.** Ngân sách đặc trưng lớn hơn buộc mạch rộng hơn:
K = 20 → n\* = 4 (24 CNOT), K = 80 → n\* = 8 (112 CNOT). Chạy lại toàn bộ ở K = 80 thì **48/48
so sánh nghiêng về cổ điển** và ablation entanglement đổi dấu.

Cơ chế đo được chứ không suy diễn: độ trải của phần ngoài đường chéo ma trận Gram giảm theo
`n^(−α)` với **α_ZZ / α_Z = 2.02** tại K = 20 — đúng tỉ lệ mà cấu trúc mạch dự đoán
(C(n,2) số hạng pha theo cặp so với n số hạng đơn). Và độ trải đó **dự đoán được macro-F1**:
r = +0.77 cho nhân ZZ, r = +0.32 cho nhân Z.

**Điểm mạnh nhất trong lập luận:** hiện tượng này đo được trong mô phỏng **hoàn toàn không
nhiễu**, nên không thể quy cho lỗi cổng lượng tử. Nghĩa là **cửa sổ hoạt động không nở ra khi
phần cứng tốt lên** — nó là giới hạn nội tại của nhân.

---

## 5. Đối soát 33 item reviewer

**Tổng: 30 xong có số liệu · 3 xong một phần và có nêu rõ còn thiếu gì.**

### Associate Editor (6/6)

| ID | Yêu cầu | Xử lý |
|---|---|---|
| AE-1 | Khẳng định lợi thế quá rộng | Rút; thay bằng bản đồ chế độ 21/21/68 |
| AE-2 | Thiếu tài liệu, có ref không tồn tại | Thêm 6 ref mới, sửa 1, gỡ 1; Table I dựng lại |
| AE-3 | R1 đòi dataset thứ hai | UNSW-NB15 làm đầy đủ cùng giao thức |
| AE-4 | Đòi baseline non-SVM | RF + XGBoost vào mọi thí nghiệm |
| AE-5 | R4 chỉ ra lỗi lý thuyết | Bỏ Theorem 1 + Pareto; thêm 2 lỗi tự khai |
| AE-6 | "NISQ-ready" không có thí nghiệm nhiễu | FakeManilaV2, depth 59, 44 cổng hai qubit |

### Reviewer 1 (8 xong + 2 một phần)

| ID | Yêu cầu | Xử lý |
|---|---|---|
| R1-1 | Thiếu bài QMI 2026 | Trích đầy đủ (Cirillo, Esposito, Seo) + bàn ở Sec II-B. **Một phần**: chưa đọc được toàn văn |
| R1-2 | Chỉ dựa NSL-KDD | UNSW-NB15 thành phần chính, không còn là phụ lục |
| R1-3 | Tuning bất đối xứng (QSVM cố định C=1.0) | Tune đối xứng mọi model; báo cáo hai nhánh |
| R1-4 | Khẳng định quá mức | Đã rút |
| R1-5 | Thêm XGBoost, CatBoost, TabNet, FT-Transformer | RF + XGBoost xong. **Một phần**: cố ý không thêm ba cái còn lại, có biện minh |
| R1-6 | NISQ chỉ có finite-shot | Thêm noise model từ calibration máy thật |
| R1-7 | Có crossover point không? | **Có** — đây thành kết quả chính của bài |
| R1-8 | Table VI lệch Table IV | Tách được hai nguồn: tập test (−0.051) và refit biểu diễn (+0.006) |
| R1-9 | F1 cổ điển thấp so với literature | Do giao thức: split chính thức 0.804 vs split ngẫu nhiên 0.999 |
| R1-10 | Supplementary không truy cập được | Thay bằng repo công khai + commit hash |

### Reviewer 2 (6/6)

| ID | Yêu cầu | Xử lý |
|---|---|---|
| R2-1 | Chỉ có baseline SVM | RF + XGBoost |
| R2-2 | Nhắc "exponential concentration" | Đưa vào (F3) và **đo hẳn** — thành mục V-G |
| R2-3 | N=1000, 5 seed là nền thống kê mỏng | 10 run, Wilcoxon ghép cặp + Holm, CI 95%; N thành biến quét |
| R2-4 | Regime map bán quá: chế độ âm chỉ định tính | Cả 110 ô đều có Δ / CI / p / d_z như nhau |
| R2-5 | Ref [15] `116990F` → `116990B` | Xác minh 3 nguồn rồi sửa |
| R2-6 | Ref [26] Rahman có vẻ bịa | Tìm hai lần không ra, đã gỡ và **thay bằng survey có thật** (Kaissar et al., Future Internet 18(5):234, 2026) |

### Reviewer 3 (4 xong + 1 một phần) — reviewer đề nghị từ chối

| ID | Yêu cầu | Xử lý |
|---|---|---|
| R3-1 | Novelty thấp, cấu hình ZZ 4-qubit là chuẩn | Không cãi. Đưa ba thứ khác: trục sample-complexity chưa ai làm, luật chuyển giao được, cơ chế đo được |
| R3-2 | Cải thiện 0.854 vs 0.838 quá nhỏ | Đã rút; số mới XGBoost dẫn đầu |
| R3-3 | Proposition là sự thật hiển nhiên | Hạ Prop 1/3/4 → background facts; Prop 2 → Lemma 1 |
| R3-4 | Toàn mô phỏng lý tưởng mà gọi NISQ-aware | Mở rộng tới 8 qubit + noise model; định nghĩa lại "NISQ-aware" là ngân sách mạch. **Một phần**: không chạy QPU thật |
| R3-5 | Kết quả đã có ở arXiv:2403.07059, 2409.04406 | Đọc toàn văn cả hai; không bài nào quét kích thước tập huấn luyện |

**Về cách trả lời R3** — ba nước, không cãi thẳng:
1. Thừa nhận đúng như họ nói là bài không có kernel / feature map / phương pháp / phần cứng /
   định lý mới.
2. Nêu sự thật rằng **hai bài họ dẫn làm bằng chứng "kết quả đã có sẵn" cũng không có những
   thứ đó** — cả hai đều là benchmark thuần tuý. Suy ra tiêu chí cho một bài benchmark không
   thể là novelty của công cụ.
3. Đổi khung từ "lợi thế" sang "ranh giới", và đưa quan hệ định lượng độ trải Gram → F1 làm
   thứ gần nhất với "một kết quả lý thuyết xác lập một chế độ".

### Reviewer 4 (5 xong + 1 một phần) — reviewer ủng hộ nhất

| ID | Yêu cầu | Xử lý |
|---|---|---|
| R4-1 | Bài Carducci ICAD 2026 | Trích + thêm hẳn một tiểu mục II-D. **Một phần**: IEEE chặn toàn văn |
| R4-2 | Theorem 1 sai + Pareto không lọc gì | Xác nhận đúng cả hai, bỏ hẳn |
| R4-3 | Nói reproducible mà không có gì | Link repo + commit hash + 4 bộ audit |
| R4-4 | Proposition 3 không tự dẫn xuất | → background fact (F2), bỏ chứng minh |
| R4-5 | Không có số nào cho lớp hiếm | Có đủ; và **SVM-RBF (0.585) mạnh nhất**, trên cả QSVM (0.507) |
| R4-6 | Không tune kernel lượng tử | Đã tune cùng thủ tục |

---

## 6. Cách kiểm chứng — chạy được trên máy bất kỳ

```bash
python runners/audit_c4.py        # 100/100  thống kê
python runners/audit_figures.py   #  36/36   hình
python runners/audit_prose.py     # 115/115  số trong câu văn
python runners/verify_lemma1.py   #  15/15   khai triển Lemma 1
python runners/check_latex.py     #          cấu trúc .tex
```

Nguyên tắc thiết kế: **`audit_c4.py` không dùng lại hàm thống kê của `c4_pipeline.py`** — nó
tính lại từ đầu bằng scipy rồi đối chiếu. Dùng chính code sinh ra số để kiểm số đó thì lỗi
chung sẽ lọt qua.

`audit_prose.py` đối chiếu từng con số **viết trong câu văn** của bài và của thư phản hồi
ngược về artifact. Đây là chỗ hai bộ audit kia không phủ, và là chỗ reviewer đọc đầu tiên.

**Bốn bộ audit này đã bắt được 4 lỗi thật trong chính code revision** trước khi công bố —
trong đó một lỗi làm `n*` ra 5 thay vì 4.

---

## 7. Hình

Bản thảo dùng **9 hình**, tất cả sinh từ dữ liệu revision:

```bash
python runners/make_paper1_figures.py
```

> ⛔ **Cảnh báo quan trọng.** Mọi hình trong `results/*/c3_multirun/`, `c4_multirun/`,
> `data/*/processed_data/` đều là **của code cũ** — 5 seed, tune bất đối xứng, chưa có
> RF/XGBoost. **Không được dùng.** Chỉ dùng `paper/paper1/figs_revision/`.
> Thư mục `reports/` chứa hình cũ đã được **gỡ khỏi repo** vì lý do này (còn trong lịch sử git).

Ba hình sơ đồ (mạch ZZ, bản đồ đóng góp, pipeline) đã bỏ khỏi bản thảo để lọt giới hạn trang —
chúng không chứa dữ liệu nào và nội dung đã có trong phần chữ. Script sinh chúng
(`make_paper1_schematics.py`) vẫn giữ.

---

## 8. Bài trùng đề tài — phải trích, không được lờ

**Gillani et al. (13-08-2026), arXiv:2608.18155** — trùng cả NSL-KDD và UNSW-NB15, trùng
split chính thức, trùng baseline RF/XGBoost, có noise sweep và hiệu chỉnh đa so sánh (BH-FDR
trên 108 so sánh). Kết luận của họ: cho model cổ điển dùng cùng front-end thì "quantum
advantage" biến mất.

Điều này **xác nhận** phát hiện độc lập của ta, nên viết theo hướng *independent
corroboration*. Nộp sau họ 2 tháng mà lờ đi là reviewer tự tìm ra.

⚠️ Bài đó cũng có calibration-aware metrics, tức **chạm vào Paper 2**. Ta nộp IJNM 04-08, họ
13-08 — trước 9 ngày nên không mất quyền ưu tiên, nhưng nếu IJNM cho revise thì phải trích.

---

## 9. Việc còn lại

| # | Việc | Ai |
|---|---|---|
| 1 | Compile lần cuối trên Overleaf, kiểm bố cục | Quan |
| 2 | Ngày tháng cho `\thanks{Manuscript received ...}` | Quan |
| 3 | Cập nhật commit hash cuối vào mục Reproducibility | Quan |
| 4 | Tiểu sử 5 tác giả (< 150 từ mỗi người) + ảnh | Cả nhóm |
| 5 | Bản đánh dấu vàng cho phần tài liệu tham khảo (TETC bắt buộc) | Quan |
| 6 | Cover letter + mục riêng gửi EiC/AE về thay đổi bibliography | Quan |
| 7 | Toàn văn QMI 2026 và Carducci 2026 để điền vài ô `n/r` trong Table I | thư viện trường |
| 8 | **Tuỳ chọn**: chạy nhân trên QPU IBM thật — script xong, chờ token | Quan |

### Ràng buộc của TETC cần nhớ

- Bản nộp lại gồm **ba file**: bản sạch, bản đánh dấu vàng, và thư phản hồi.
- Quá **12 trang** thì phải trả phí trang vượt (MOPC) và **không được xin miễn**.
- Danh mục tài liệu **tối đa 45 mục** — hiện 41.
- **Không được thêm/bớt tác giả** nếu không có văn bản đồng ý của EiC.
- **Không được thêm/bớt tự trích dẫn**. Mọi thay đổi bibliography phải giải trình trong một
  mục riêng của thư phản hồi.

---

## 10. Đánh giá rủi ro theo từng reviewer

| Reviewer | Lập trường cũ | Khả năng thuyết phục |
|---|---|---|
| **R4** | Ủng hộ mạnh nhất | 🟢 Cao. Cả 6 item được xử lý, và ta **tự khai thêm hai lỗi họ chưa bắt**. Reviewer kiểu này đánh giá cao sự thẳng thắn |
| **R1** | Major revision, thiện chí | 🟢 Cao. Câu hỏi crossover của họ được trả lời bằng một kết quả thật |
| **R2** | Phê bình kỹ thuật, không phản đối | 🟢 Cao. Cả 6 item xong |
| **R3** | **Đề nghị từ chối** | 🟡 Khó nhất. Họ chê ở tầng "không có gì mới về công cụ" mà ta vẫn không có. Chỉ đổi được cách định vị |

AE đã viết *"the majority of reviewers see sufficient new contribution"* nên AE không đứng về
phía R3.

**Điều quan trọng nhất khi trình bày:** đóng khung là *"chúng tôi đo lại nghiêm ngặt hơn và
tìm ra một bức tranh có cấu trúc"*, **không phải** *"chúng tôi rút lại các khẳng định"*. Cùng
một sự thật, hai cách kể, hai kết cục.
