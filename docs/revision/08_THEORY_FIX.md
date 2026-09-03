# Sửa phần lý thuyết — Theorem 1, Pareto, Proposition 1–4

*Quan, 2026-09-03. Trả lời R3-3 và các ý về lý thuyết của R4.*

**File kèm**: `paper/paper1/theory_revision.tex` (phần thay thế, dán thẳng vào bài).

---

## 0. Trả lời câu của anh: tôi **chưa** viết bài

Tôi mới làm các **mảnh ghép** để dán vào bài: hình, caption, bảng, novelty matrix, và giờ là
phần lý thuyết viết lại. Chưa động vào bản thảo, vì **chưa có file `.tex` nguồn của bản đã
nộp** — đây vẫn là blocker P0.1 từ đầu.

Nhắc lại cho rõ: `paper/paper1/main.tex` trong repo **không phải** bản đã nộp. Nó là một draft
khác — **6 đóng góp C1–C6**, không có Theorem 1, UNSW nằm trong thân bài, 37 ref. Bản đã nộp
(`paper1.pdf`) có **4 đóng góp C1–C4**, có Theorem 1, 36 ref. Hai bản khác nhau thật sự.

**Anh nói đúng là "họ không cho đổi đồ".** Cụ thể với major revision của IEEE:

- Giữ nguyên submission ID, giữ nguyên template IEEEtran journal
- **Giữ nguyên cách đánh số đóng góp C1–C4** — reviewer trích dẫn theo số đó, đổi là họ không
  dò lại được
- Phải nộp kèm **bản highlight vàng** chỗ nào đã sửa → **bắt buộc phải có `.tex` nguồn**,
  không dựng lại từ PDF được

Nên mọi thứ tôi làm đều ở dạng **mảnh dán vào**, giữ nguyên tên mục và số hiệu, không đổi cấu
trúc. Khi nào thầy gửi `.tex` thì ghép là xong.

---

## 1. Đọc kỹ bản đã nộp thì thấy **ba lỗi**, không phải một

R4 chỉ ra một cái. Đọc kỹ Table III thì lòi thêm hai cái nữa.

### 1.1 🔴 Theorem 1 **sai** — R4 đúng

Chứng minh trong bài viết nguyên văn: *"Substituting numerical values from Table III
(ΔV₃₄ = 0.045, ΔQ₃₄ = 0.068, and **F̃(4) > F̃(3)** for stratified NSL-KDD)"*.

Nhưng chính Table III của bài ghi:

| n | V(n) | F̃(n) | Q(n) | J(n) α=β=γ=1/3 |
|---|---|---|---|---|
| **2** | 0.742 | 0.941 | 0.030 | **0.551** ← lớn nhất |
| 3 | 0.821 | **0.628** | 0.077 | 0.457 |
| 4 | 0.866 | **0.471** | 0.145 | 0.397 |
| 5 | 0.904 | 0.378 | 0.234 | 0.349 |
| 6 | 0.939 | 0.315 | 0.345 | 0.303 |
| 7 | 0.952 | 0.272 | 0.477 | 0.249 |
| 10 | 0.981 | 0.196 | 1.000 | 0.059 |

`F̃(4) = 0.471 < F̃(3) = 0.628`. Tiền đề của chứng minh **ngược với dữ liệu của chính bài**.

Thay số đúng vào: `ΔJ₃₄ = 0.045α − 0.156β − 0.068γ`. Tại α=β=γ=1/3 thì `ΔJ₃₄ = −0.060 < 0`,
tức `J(3) > J(4)`. Cột J giảm đều từ n=2 xuống n=10, **n=2 mới là cực đại**. Theorem 1 khẳng
định n*=4 là cực đại duy nhất của J với mọi γ ≥ 0.30 — sai.

Tôi có kiểm lại độc lập từ output notebook C1: Fisher `n=2: 0.9413, n=3: 0.6275, n=4: 0.4711`
— khớp Table III tới 3 chữ số. Không phải lỗi in.

### 1.2 🔴 Bước Pareto **không lọc gì cả** — R4 cũng đúng

R4 viết: *"V(n) always increases and F̃(n) and Q(n) always decreases, that may mean Pareto
might not be doing any filtering at all"*.

Đúng. Với bộ ba `(V, F̃, −Q)`: V tăng đơn điệu, F̃ giảm đơn điệu, Q tăng đơn điệu. Không điểm
nào trội hơn điểm nào → **mọi candidate đều Pareto-optimal**. Chính notebook C1 của ta cũng
ghi: *"Tất cả candidate đều Pareto-optimal — Pareto ở đây CHỈ là diagnostic, KHÔNG được dùng
để chọn n"*. Nhưng bài đã nộp lại trình bày Pareto như một bước chọn (Definition 4 +
Algorithm 1 + Fig. 5).

### 1.3 🟡 Table III **ghi sai tên cột** — chưa reviewer nào bắt

Caption Table III ghi `F̃(n) = 1/DBI(n)`. Nhưng số trong cột (0.941, 0.628, 0.471…) là
**thống kê Fisher**, không phải nghịch đảo Davies–Bouldin. Nghịch đảo DBI thật là
`1.143, 0.982, 0.922` tại n=2,3,4 — hoàn toàn khác.

Không ai bắt, và không kết luận nào của bản revision phụ thuộc vào nó (đại lượng này bị bỏ
cùng với J). Nhưng **phải tự khai**, vì nếu reviewer đối chiếu supplementary là thấy.

---

## 2. Sửa thế nào

Không vá Theorem 1 mà **bỏ hẳn**, vì lỗi 1.2 cho thấy cả cấu trúc Pareto + J không làm việc
mà bài gán cho nó. Thay bằng **luật ba giai đoạn từ vựng** (lexicographic) — không có trọng
số, nên không phải biện minh cho bất kỳ đánh đổi nào.

| Bản đã nộp | Bản revision |
|---|---|
| Proposition 1 (PSD) + proof | → **(F1)** trong mục Background, có trích dẫn, bỏ proof |
| Proposition 2 (khai triển ZZ) + proof sketch | → **Lemma 1**, proof chuyển xuống Appendix A |
| Proposition 3 (KTA bound, after [23]) + proof | → **(F2)**, trích [23] nguyên trạng, bỏ proof |
| Proposition 4 (z-test KTA) + proof | → **(F3)** + đổi hẳn sang giao thức ghép cặp |
| Definition 4 (Pareto) | → **bỏ** |
| Algorithm 1 (Pareto search) | → **bỏ** |
| Eq. (6) `J(n) = αV + βF̃ − γQ` | → **bỏ** |
| **Theorem 1** | → **bỏ**, thay bằng Definition (three-stage selection) |
| Fig. 5 (Pareto frontier) | → hình mới 3 panel × 2 dataset |

**Vì sao giữ Proposition 2 (thành Lemma 1)**: nó **không** phải sự thật hiển nhiên — đó là
khai triển riêng của bài, và nó chính là lý do SVM-Poly2 được chọn làm đối thủ cổ điển sắc
nhất. R3 chê "well established facts framed as propositions" — Prop 2 không thuộc diện đó.

**Proposition 4 không chỉ hiển nhiên mà còn sai giao thức**: z-test hai mẫu coi hai nhánh là
độc lập, trong khi chúng **dùng chung subset huấn luyện** — vứt mất đúng cái ghép cặp làm cho
phép so sánh có ý nghĩa. Và m=5 quá ít cho xấp xỉ chuẩn. Bản revision dùng Wilcoxon ghép cặp
trên 10 run + Holm, chặt hơn hẳn.

### Ánh xạ trích dẫn — **không thêm ref mới**

Reviewer đang yêu cầu ≤45 ref và đã bắt được ref không tồn tại, nên phần viết lại chỉ dùng ref
đã có sẵn:

| Key trong `.tex` | Số trong bản đã nộp |
|---|---|
| `cortes1995` | [16] Cortes & Vapnik |
| `scholkopf2002` | [17] Schölkopf & Smola *(dùng cho định lý Schur — bản cũ nói "Schur product theorem" mà không trích ai)* |
| `havlicek2019` | [11] Havlíček et al. |
| `schuld2019` | [12] Schuld & Killoran |
| `thanasilp2024` | [22] Thanasilp et al. |
| `cortes2012` | [23] Cortes, Mohri, Rostamizadeh |
| `cristianini2001` | [28] Cristianini et al. |

---

## 3. Bản nháp đoạn trả lời

### R3-3 (propositions là sự thật hiển nhiên)

> We agree. Propositions 1, 3 and 4 restated results that are established
> elsewhere, and proving them added length without adding content. They are now stated as
> background facts (F1)–(F3) with citations and no proofs. Proposition 2 is retained, since it
> is a derivation specific to the comparison this paper makes rather than a known result, but
> it is now labelled a lemma and its proof moved to Appendix A.

### R4 (Theorem 1 sai + Pareto không lọc gì)

> The reviewer is correct on both counts, and we are grateful for the care taken.
>
> Theorem 1 was false. Its proof asserted F̃(4) > F̃(3), while Table III of the same submission
> reports F̃(4) = 0.471 < F̃(3) = 0.628. With the correct values the conclusion does not
> follow: at α = β = γ = 1/3 the objective is maximised at n = 2 (J = 0.551) and decreases
> monotonically to J = 0.059 at n = 10, so n = 4 is not a maximiser for any weight triple in
> the stated range.
>
> The reviewer is also right that the Pareto stage was not filtering. Because V(n) is
> increasing while F̃(n) is decreasing and Q(n) is increasing, no candidate dominates any
> other, so every candidate is Pareto-optimal and the stage removed nothing.
>
> We have therefore removed Theorem 1, the objective J and the Pareto construction rather than
> repairing them, and replaced them with a lexicographic three-stage rule that involves no
> weights (Definition 2). The rule keeps dimensions with V(n) ≥ 0.85, then those within 5% of
> the best kernel–target alignment among the survivors, then takes the cheapest. On NSL-KDD it
> returns n* = 4; applied unchanged to UNSW-NB15 it returns n* = 6 on 10/10 independent
> subsets. We now present C1 as a transferable procedure rather than as the constant n = 4.
>
> While making this correction we found a further error the reviewers did not raise: the
> caption of Table III defined F̃(n) = 1/DBI(n), but the tabulated values are the ANOVA F
> statistic. We record this in Sec. III-E for completeness; no conclusion in the revision
> depends on it, as the quantity has been dropped along with J.

### R4 (Proposition 3 không được dẫn xuất)

> Correct — the former Proposition 3 restated the bound of [23] without deriving it. It is now
> cited as background fact (F2) with no proof, and its role is stated explicitly: it is a
> diagnostic that explains why two kernels with the same empirical risk can differ in the
> bound, not a result this paper establishes.

---

## 4. Việc còn treo

| # | Việc | Ai |
|---|---|---|
| 1 | 🚨 **Xin file `.tex` nguồn của bản đã nộp** — không có thì không tạo được bản highlight vàng | thầy |
| 2 | Viết Appendix A (proof BCH của Lemma 1) — lấy từ proof sketch cũ, giãn ra | Quan |
| 3 | Compile thử (máy chưa có pdflatex) | Quan |
| 4 | Sửa mục III-B: bản cũ ghi "C=1.0 xuyên suốt để tránh bias" nhưng lại tune C cho SVM cổ điển — R4 bắt đúng chỗ này. Bản revision tune đối xứng cả hai. | Quan |
| 5 | Sửa mục III-B: bản cũ ghi 5 seed {0,1,2,3,4}; bản revision dùng 10 run | Quan |
