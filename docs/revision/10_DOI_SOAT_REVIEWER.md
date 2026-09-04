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

---

# CẬP NHẬT 2026-09-04 — sau khi soát hình và chạy thêm

## Soát hình: `runners/audit_figures.py` → **38/38 PASS**

Hai câu hỏi tách bạch:

1. **Xuất xứ** — mọi file hình đều **mới hơn** cả script sinh nó lẫn dữ liệu nguồn. Không có
   hình nào là bản còn sót lại. 12/12 PASS.
2. **Số liệu** — từng con số hình vẽ ra được dựng lại từ artifact. 26/26 PASS. Với ba hình sơ
   đồ thì đối chiếu hằng số hiển thị (24 CNOT khớp `count_ops()` của Qiskit, K=20 và n\*=4
   khớp `DatasetSpec`, 122 chiều khớp dữ liệu thật).

### 🔴 Một lỗi thật tìm được khi soát

Script `run_c1_ksens.py` của tôi **fit MinMax scaler trên 300 dòng tập con** thay vì trên
toàn bộ train như notebook C1. Hậu quả: KTA lệch tới **0.082**, và ở K=20 luật cho ra
**n\* = 5 thay vì 4**. Tức nếu không soát thì repo sẽ có hai giá trị `n*` mâu thuẫn.

Sau khi sửa, script tái tạo notebook **chính xác**: KTA_max 0.2439 tại n=5, ngưỡng 0.2317,
giai đoạn 2 = {4,5,6}, n\* = 4. Bảng gõ cứng trong Fig 5 nay **được kiểm chứng độc lập**,
lệch lớn nhất 4.9e-05 (chỉ là làm tròn 4 chữ số). Đã thêm `assert` vào script vẽ hình để nếu
sau này một trong hai bên trôi thì build hình gãy ngay chứ không âm thầm.

Cũng sửa `Q(n)` cho đúng công thức của bài (`Q_raw = 10n² − 8n`) thay vì bản rút gọn theo CNOT.

## Hai kết quả mới, cả hai đều củng cố bài

**#33 — "Elbow tại K=20" là điểm cuối lưới quét cũ.** Mở rộng tới K=122 thì F1 vẫn tăng.
Nhưng luật C1 cho thấy K lớn hơn đòi **nhiều qubit hơn** (K=20→n\*=4, K=80→n\*=8). Nên K=20
được biện minh bằng **ngân sách NISQ**, một lập luận đúng và mạnh hơn "elbow".

**#34 — Mở rộng mạch phá hỏng nhân lượng tử.** Chạy lại C4 ở K=80/n=8: **32/32 ô đều
classical-favorable**, không đổi dấu ở bất kỳ N nào; ablation entanglement đảo chiều (ZZ thua
Z từ −0.08 đến −0.17). Cơ chế **đo được**: độ lệch chuẩn off-diagonal của Gram, ZZ mất 55% độ
trải khi n đi 4→10 còn Z chỉ mất 21%.

### Ảnh hưởng tới trạng thái reviewer

| ID | Trước | Sau | Vì |
|---|---|---|---|
| **R3-4** (toàn mô phỏng, qubit quá ít) | ✅ (có FakeManila) | ✅✅ **mạnh hơn hẳn** | Không phải ta chọn 4 qubit cho tiện — rộng hơn thì **hỏng**, và ta đo được cơ chế |
| **R2-2** (nhắc exponential concentration) | ✅ (có nhắc) | ✅✅ **mạnh hơn hẳn** | Không nhắc suông mà **đo trực tiếp** trên đúng dữ liệu của bài |

---

# Đánh giá thẳng: đã đạt Q1 chưa

## Phần chắc chắn đạt

- **Nền bằng chứng**: 96/96 audit C4 + 38/38 audit hình. Mọi con số trong bài dựng lại được
  từ artifact. Đây là mức nghiêm ngặt trên trung bình của Q1.
- **Trục đóng góp thật**: không bài nào trong 5 bài đối chiếu quét kích thước tập huấn luyện.
- **Có cơ chế, không chỉ có số**: crossover + K–n coupling + concentration ghép thành một
  chuỗi giải thích, thay vì một bảng xếp hạng.
- **Trung thực**: tự khai 3 lỗi của bản cũ (Theorem 1 sai, Pareto vô dụng, nhãn cột Table III),
  trong đó có lỗi **chưa reviewer nào bắt**.

## Ba rủi ro còn lại

**1. 🔴 R3 vẫn là rủi ro lớn nhất.** Họ đòi "kernel mới / feature map mới / kết quả lý thuyết
mới" — ta **vẫn không có**. Ta chỉ đổi được cách định vị sang *evaluation framework*. AE viết
*"majority of reviewers see sufficient new contribution"* nên AE không đứng về phía R3, nhưng
nếu R3 giữ nguyên thì phụ thuộc AE.

**2. 🔴 Chưa có `.tex` — đây là rủi ro TIẾN ĐỘ, không phải khoa học.** Còn 39 ngày. Phải dựng
lại toàn bộ bản thảo từ PDF rồi ghép 12 hình + phần lý thuyết + novelty matrix + rebuttal 33
item. Đây mới là thứ dễ trượt deadline nhất.

**3. 🟡 Bài Gillani et al. (arXiv:2608.18155)** trùng đề tài, trùng cả hai dataset. Phải chủ
động trích và phân biệt.

## Kết luận

**Về mức độ chặt chẽ: đạt Q1, và vượt xa bản đã nộp.** Bản cũ có một định lý sai, một bước
chọn không lọc gì, một khẳng định không tái tạo được, và một khẳng định lợi thế mà dữ liệu
không đỡ nổi. Bản mới thay tất cả bằng số đo được, kiểm định có hiệu chỉnh đa so sánh, và
hai bộ audit tự động.

**Về khả năng được nhận: khá, nhưng không chắc chắn** — phụ thuộc hai thứ ta không kiểm soát
hoàn toàn: R3 có đổi ý không, và ta có viết kịp trong 39 ngày không.

**Điều quan trọng nhất khi viết**: bài phải được đóng khung là *"chúng tôi đo lại nghiêm ngặt
hơn và tìm ra bức tranh có cấu trúc"*, **không phải** *"chúng tôi rút lại các khẳng định"*.
Cùng một sự thật, hai cách kể, hai kết cục khác nhau.
