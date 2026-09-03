# Đối soát toàn bộ reviewer — đã giải quyết tới đâu, kết quả có khả quan không

*Quan, 2026-09-03. Rà từng item trong `Review.md` với bằng chứng thật trong repo.*

---

## 0. Trả lời ngắn

**Về mặt thí nghiệm: xong gần hết.** 33 item → **24 xong có số**, **5 một phần**,
**4 còn là việc viết** (đã có đủ liệu, chỉ chưa gõ vào bài).

**Về mặt kết quả: khả quan cho việc được nhận, nhưng câu chuyện của bài bị lật.**

Đây là chỗ anh cần nghe rõ trước khi viết:

| Bản đã nộp khẳng định | Số thật sau khi làm lại |
|---|---|
| QSVM-ZZ thắng ở **chế độ ít dữ liệu** | **Ngược lại** — cổ điển thắng ở N nhỏ, QSVM thắng ở N lớn (crossover tại N≈2000–5000) |
| "+6.7 điểm trên tập con rare, d=+0.68" | **Không tái tạo được** — phải bỏ |
| Theorem 1: n*=4 cực đại hoá J | **Sai** — J cực đại tại n=2 |
| QSVM-ZZ 0.854 > SVM-RBF 0.838 | Thêm baseline mạnh: **XGBoost 0.8503 > QSVM-ZZ 0.8469** > RF 0.8446 |
| "quantum advantage is real and measurable" | **21 thắng / 21 thua / 68 hoà** trên 110 so sánh |

**Nói thẳng: bài không còn khẳng định được lợi thế lượng tử tổng quát.** Nhưng đó **chính là
thứ AE và R1/R4 yêu cầu** — họ chê đúng cái khẳng định quá rộng đó. Bài mới trung thực hơn,
và có ba thứ bài cũ không có: crossover đo được và bền qua hai arm, luật C1 chuyển giao được
sang dataset thứ hai, và bản đồ chế độ 110 so sánh có kiểm định.

---

## 1. Bảng đối soát 33 item

Ký hiệu: ✅ xong có số · 🟡 một phần · ✍️ đủ liệu, chỉ còn gõ vào bài · ❌ chưa

### Associate Editor (6)

| ID | Yêu cầu | TT | Bằng chứng |
|---|---|---|---|
| AE-1 | Khẳng định lợi thế quá rộng, cải thiện số nhỏ | ✅ | Bản đồ chế độ 21/21/68 · `regime_map_rows.csv` |
| AE-2 | Thiếu literature, có ref không tồn tại | ✍️ | `07_NOVELTY_MATRIX.md` — đã đọc 5 bài; ref [15]/[26] chưa sửa |
| AE-3 | R1 đòi dataset thứ hai | ✅ | UNSW-NB15 đầy đủ · `results/unsw/c4_revision/` |
| AE-4 | Đòi so với non-SVM | ✅ | RF + XGBoost trong mọi thí nghiệm |
| AE-5 | R4 chỉ ra lỗi lý thuyết | ✅ | `theory_revision.tex` — bỏ Theorem 1, hạ Prop 1–4 |
| AE-6 | "NISQ-ready" không có thí nghiệm nhiễu | ✅ | FakeManilaV2 + `NoiseModel.from_backend()` · `c2_noise_validation.csv` |

### Reviewer 1 (10)

| ID | Yêu cầu | TT | Bằng chứng |
|---|---|---|---|
| R1-1 | Thiếu bài QMI 2026; Table I cần literature 2025–26 | 🟡 | Đã đọc abstract; **Springer chặn toàn văn** — cần thư viện trường |
| R1-2 | Chỉ dựa NSL-KDD; supplementary UNSW không truy cập được | ✅ | UNSW-NB15 làm đủ, có trong repo |
| R1-3 | Tuning bất đối xứng (QSVM C=1.0 cố định, cổ điển thì tune) | ✅ | `tune_quantum_C()` — tune đối xứng; 2 arm `tuned_per_N` / `frozen_c2` |
| R1-4 | Khẳng định quá mức | ✅ | Đã bỏ; thay bằng regime map |
| R1-5 | Thêm XGBoost, CatBoost, TabNet, FT-Transformer | 🟡 | **RF + XGBoost xong**; CatBoost/TabNet **cố ý không thêm** — có văn bản biện minh |
| R1-6 | NISQ chỉ có finite-shot, cần noise model thật | ✅ | FakeManilaV2, depth 59, 44 CX, gate+readout+relaxation |
| R1-7 | Có crossover point không? | ✅ | **Có** — N≈2000–5000, bền 6/6 tổ hợp |
| R1-8 | Table VI (N=1000) lệch Table IV | ✅ | `c4_table_iv_vs_vi.csv` — tách được 2 nguồn |
| R1-9 | F1 cổ điển thấp so với literature | ✅ | `c4_protocol_vs_literature.csv` — 0.804 vs 0.999 do giao thức |
| R1-10 | Supplementary không truy cập được | ✍️ | Repo public; cần đóng gói + link + commit hash |

### Reviewer 2 (6)

| ID | Yêu cầu | TT | Bằng chứng |
|---|---|---|---|
| R2-1 | Chỉ có SVM, thiếu RF/XGBoost/TabNet | ✅ | RF + XGBoost xong |
| R2-2 | Nhắc "exponential concentration" là tương ứng của barren plateau | ✅ | `theory_revision.tex` (F3), trích [22] Thanasilp |
| R2-3 | N=1000, 5 seed là nền thống kê mỏng | ✅ | **10 run**, Wilcoxon ghép cặp + Holm, CI 95% |
| R2-4 | Regime map bán quá — 3 chế độ dương có stats, 2 chế độ âm chỉ định tính | ✅ | **21 ô classical-favorable có đủ Δ/CI/p/d_z** như ô dương |
| R2-5 | Ref [15] `116990F` → `116990B` | ❌ | Việc viết |
| R2-6 | Ref [26] Rahman có vẻ bịa | ❌ | Việc viết — phải kiểm rồi bỏ |

### Reviewer 3 (5) — reviewer khó nhất, đề nghị **từ chối**

| ID | Yêu cầu | TT | Bằng chứng |
|---|---|---|---|
| R3-1 | Novelty thấp: ZZ 4-qubit depth-2 là cấu hình chuẩn | 🟡 | Định vị lại = *evaluation framework*; C1 chuyển giao n*=4→6 |
| R3-2 | Cải thiện 0.854 vs 0.838 quá nhỏ để khẳng định lợi thế | ✅ | **Đã bỏ khẳng định**. Số mới: XGBoost 0.8503 > QSVM 0.8469 |
| R3-3 | Proposition là sự thật hiển nhiên | ✅ | Hạ Prop 1/3/4 → Background; Prop 2 → Lemma 1 |
| R3-4 | Toàn mô phỏng lý tưởng mà gọi "NISQ-aware" | ✅ | FakeManilaV2; UNSW dùng 6 qubit |
| R3-5 | Kết quả đã có ở arXiv:2403.07059, 2409.04406 | 🟡 | Novelty matrix: **không bài nào quét kích thước tập huấn luyện** |

### Reviewer 4 (6) — reviewer ủng hộ nhất

| ID | Yêu cầu | TT | Bằng chứng |
|---|---|---|---|
| R4-1 | Carducci ICAD 2026 | 🟡 | Có thư mục; **IEEE chặn toàn văn** |
| R4-2 | Theorem 1 sai + Pareto không lọc gì | ✅ | Xác nhận đúng cả hai, đã bỏ hẳn, tự khai trong bài |
| R4-3 | Nói reproducible nhưng không có link | ✍️ | Repo public; cần link + commit hash |
| R4-4 | Proposition 3 không tự dẫn xuất | ✅ | → (F2), trích [23] nguyên trạng, bỏ proof |
| R4-5 | Không có số nào cho tập con rare | ✅ | `c4_rare_attack.csv` + margin **có dấu** |
| R4-6 | Không tune kernel lượng tử | ✅ | `tune_quantum_C()` + 2 arm |

**Tổng: 24 ✅ · 5 🟡 · 2 ✍️ · 2 ❌**

---

## 2. Bốn thứ phải rút lại — đây là phần khó nói

Không có cách nào viết bài mà giữ được mấy khẳng định này:

1. 🔴 **"+6.7 điểm trên tập con rare, Cohen's d = +0.68"** (R4-5 hỏi thẳng). Không có metric
   rare nào tồn tại trong code cũ. Không tái tạo được. Số thật ở `c4_rare_attack.csv`.
2. 🔴 **Theorem 1** — sai, chứng minh dùng tiền đề ngược với Table III của chính bài.
3. 🔴 **"Lợi thế ở chế độ ít dữ liệu"** — đo lại thì **ngược chiều**. Cổ điển thắng ở N nhỏ.
4. 🔴 **"Quantum advantage is real and measurable in two regimes"** — 110 so sánh cho
   21/21/68.

Ngoài ra `train_run{i}` **giàu lớp hiếm gấp 12 lần** tỉ lệ tự nhiên (10% vs 0.83%) — chưa từng
ghi trong bài. Chính nó tạo ra ảo giác "lợi thế ít dữ liệu": ở chế độ làm giàu thì crossover
biến mất, ở chế độ tự nhiên thì crossover xuất hiện.

---

## 3. Ba thứ mới, đủ mạnh để bù

1. **Crossover đo được và bền.** N≈2000–5000, đổi dấu ở **6/6 tổ hợp**
   {XGBoost, RF, SVM-RBF} × {đóng băng siêu tham số, tune lại mỗi N}. Trả lời thẳng R1-7, và
   chặn trước phản biện "chỉ là tạo tác của việc tune lại".
2. **C1 là thủ tục chuyển giao được.** Cùng luật, không sửa tham số, `n*=4` (NSL-KDD) →
   `n*=6` (UNSW), lặp lại trên 10/10 subset. Đây là câu trả lời thực chất cho R3-1.
3. **Bản đồ chế độ 110 so sánh.** Chế độ âm được đối xử ngang chế độ dương — đúng thứ R2-4
   đòi.

Thêm: trên UNSW, QSVM-ZZ **thắng SVM-RBF có ý nghĩa** từ N≥2000 (+0.040, Holm p=0.006) và
ablation entanglement mạnh gấp đôi NSL-KDD (+0.045, p=0.002).

---

## 4. Rủi ro theo từng reviewer

| Reviewer | Lập trường cũ | Đánh giá khả năng thuyết phục |
|---|---|---|
| **R4** | Ủng hộ mạnh nhất | 🟢 **Cao.** Cả 6 item đều được xử lý, và ta **tự khai thêm** một lỗi họ chưa bắt (Table III dán nhầm nhãn). Reviewer kiểu này đánh giá cao sự thẳng thắn. |
| **R1** | Major revision, thiện chí | 🟢 **Cao.** 8/10 xong có số. Câu hỏi crossover của họ được trả lời bằng một kết quả thật. Còn kẹt QMI 2026 (Springer chặn) và CatBoost/TabNet (cố ý không làm, có biện minh). |
| **R2** | Phê bình kỹ thuật, không phản đối | 🟢 **Cao.** 4/6 xong; 2 cái còn lại chỉ là sửa reference. |
| **R3** | **Đề nghị từ chối** | 🟡 **Khó nhất.** Họ chê novelty ở tầng "không có kernel mới / feature map mới / kết quả lý thuyết mới" — mà ta **vẫn không có**. Ta chỉ đổi được cách định vị: đóng góp là *evaluation framework* + trục sample-complexity chưa ai làm. Có thể không đủ với họ. |

**Về R3, cần chuẩn bị tinh thần**: họ nói *"the results are already established in numerous
previous work"*. Ta không cãi được điều đó, và cách khôn nhất là **đồng ý** rồi chỉ ra ta ra
đúng kết quả như họ (21/21/68) nhưng trên một trục họ không xét. Nếu R3 vẫn giữ nguyên, quyết
định nằm ở AE — mà AE đã viết *"the majority of reviewers see sufficient new contribution"*,
tức AE không đứng về phía R3.

> ⚠️ **Một rủi ro mới**: bài Gillani et al. (arXiv:2608.18155, 13-08-2026) trùng đề tài, trùng
> cả hai dataset, và kết luận "lợi thế quy về tiền xử lý". Nếu R3 tìm ra bài này thì lập luận
> novelty của ta yếu đi. **Phải chủ động trích và phân biệt** — chi tiết ở `07_NOVELTY_MATRIX.md`.

---

## 5. Còn lại phải làm

### Chặn đường viết bài

| # | Việc | Ai |
|---|---|---|
| 1 | 🚨 `.tex` nguồn — **đã chốt là không còn**, nên tôi dựng lại từ `paper1.pdf` | Quan |
| 2 | Toàn văn QMI 2026 (Springer) + Carducci ICAD 2026 (IEEE) | Quan/thầy — thư viện trường |

### Việc viết (đủ liệu rồi)

| # | Việc | Item |
|---|---|---|
| 3 | Sửa ref [15] `116990F`→`116990B`; kiểm và bỏ ref [26] Rahman; giữ ≤45 ref | R2-5, R2-6 |
| 4 | Link repo + commit hash vào mục IV-C | R4-3, R1-10 |
| 5 | Mở rộng Table I bằng literature 2024–2026 | R1-1, AE-2 |
| 6 | Rà toàn bài bỏ chữ "quantum advantage" | R1-4, R3-2 |
| 7 | Dựng lại Table III (bỏ cột J, sửa nhãn cột F̃, thêm KTA) | R4-2 |
| 8 | Appendix A — proof BCH của Lemma 1 | R3-3 |
| 9 | Đóng gói supplementary | R1-10 |
| 10 | Rebuttal letter điểm-theo-điểm 33 item | tất cả |

### Nếu còn thời gian

| # | Việc | Lợi |
|---|---|---|
| 11 | U5: đánh giá UNSW trên tập test đã khử trùng lặp (25% dòng test trùng train) | chặn trước phản biện |
| 12 | Sweep C cho QSVM để trả lời R1-3 bằng đồ thị độ nhạy | mạnh hơn |
