# Bản đồ chèn — mảnh nào vào chỗ nào của bản đã nộp

*Quan, 2026-09-03. Dựng từ `paper1.pdf` (pdftotext), không suy đoán.*

---

## 0. `main.tex` KHÔNG phải bản đã nộp — bằng chứng

Anh hỏi đúng chỗ nên tôi đối chiếu hẳn ra:

| | `paper/paper1/main.tex` | `paper1.pdf` (đã nộp) |
|---|---|---|
| Tạp chí trong `\markboth` | **Cognitive Communications and Networking** | **Emerging Topics in Computing** |
| Tiêu đề | "…A **Six-Contribution** Analysis on NSL-KDD **and UNSW-NB15**" | "…A **Regime-Specific Benchmark** on NSL-KDD" |
| Đóng góp | C1–C**6** | C1–C**4** |
| Tác giả | `First~Author, Second~Author` (placeholder) | Minh Tuan Pham, Phuc Hao Do, Nguyen Nang Hung Van, Quang Anh Nguyen, Quan Tran Anh Vo |
| Lý thuyết | **không có** Assumption / Problem / Definition / Proposition / Theorem | có đủ Assumption 1, Problem 1, Definition 1–4, Proposition 1–4, **Theorem 1** |
| Công thức J | `J = ω₁V − ω₂Q` (2 hạng) | `J = αV + βF̃ − γQ` (3 hạng, α+β+γ=1) |
| Số ref | 37 | 36 |
| UNSW | nằm trong thân bài | không phải thí nghiệm chính (R1 mới yêu cầu bổ sung) |

Toàn bộ phần lý thuyết mà R3 và R4 chê **không tồn tại** trong `main.tex`. Nó là một draft
anh em, gửi cho tạp chí khác.

> **Phát hiện phụ**: cột số `0.9413 / 0.6275 / 0.4711 / …` trong `main.tex` gắn nhãn **"1−V"**,
> còn trong `paper1.pdf` gắn nhãn **"F̃ = 1/DBI"**. Cả hai nhãn đều sai — đó là thống kê Fisher
> (1 − 0.7418 = 0.258, không phải 0.941). Cùng một cột bị dán nhầm nhãn qua nhiều bản.

### Xin thầy đúng cái gì

Nói cụ thể để khỏi nhận nhầm file lần nữa:

> File `.tex` mà bản PDF nộp cho TETC (Submission ID **TETC-2026-05-0252**) được biên dịch ra.
> Nhận ra bằng ba dấu hiệu: (a) tiêu đề có cụm **"A Regime-Specific Benchmark on NSL-KDD"**;
> (b) có **Theorem 1 (Selection theorem)** và **Proposition 1–4**; (c) `\markboth` ghi
> **Emerging Topics in Computing**. Xin kèm cả thư mục hình và file `.bib` (hoặc
> `thebibliography`) đúng bản đó.

**Nếu thầy không còn file**: nói tôi biết, tôi dựng lại từ `paper1.pdf`. Có sẵn toàn văn qua
pdftotext và `main.tex` cho phần khung IEEEtran + khoảng 30/36 ref dùng chung. Mất khoảng
một buổi, nhưng phải dò lại từng công thức nên chỉ làm khi chắc là không xin được.

---

## 1. Cấu trúc bản đã nộp

8 mục, 7 bảng (I–VII), 10 hình.

| Mục | Nội dung | Chứa |
|---|---|---|
| I | Introduction | — |
| II-A | Quantum Kernel and ZZFeatureMap | Def 1, Def 2, **Prop 1**, Def 3, **Prop 2** |
| II-B | Why Kernel Geometry Matters | **Prop 3** |
| II-C | Network Intrusion Detection Baselines | — |
| II-D | QSVM for Intrusion Detection | **Table I** (coverage 3 gap) |
| III-A | Problem Formulation | Assumption 1, Problem 1, Eq (5) |
| III-B | System Pipeline and Notation | Table II, Fig 3 |
| III-C | C1: Hardware-Constrained Pareto Pipeline | **Def 4, Algorithm 1, Eq (6) J(n), Theorem 1** |
| III-D | C2: Centred Entanglement Ablation | Eq (7), Eq (8), **Prop 4** |
| III-E | C3: Class-Prior Shift Stress Test | — |
| III-F | C4: Sample-Complexity Sweep | — |
| IV-A | Software and hardware | — |
| IV-B | Hyper-parameter and seed protocol | 🔴 5 seed, tune bất đối xứng |
| IV-C | Reproducibility | 🔴 "released" nhưng không có link |
| IV-D | Statistical methodology | — |
| V-A | C1: Pareto Pipeline Selection | **Table III**, Fig 4, **Fig 5** |
| V-B | C2: Kernel Geometry and Entanglement Ablation | Table IV, Fig 6, Fig 7 |
| V-C | C3 | Table V, Fig 8 |
| V-D | C4: Low-Data Regime Advantage | Table VI, **Fig 9** |
| V-E | Shot-Noise Sanity Check | Table VII |
| VI | Regime Map: When to Use QSVM-ZZ | **Fig 10** |
| VII | Limitations and Threats to Validity | A. Hardware noise · B. Embedding size · C. Classical-baseline strength · **D. Dataset breadth** |
| VIII | Conclusion and Future Work | — |

---

## 2. Bản đồ chèn

### Thay thế trực tiếp

| Mảnh của tôi | Thay cho | Vì |
|---|---|---|
| `theory_revision.tex` §Background (F1)(F2)(F3) | **Prop 1** (II-A), **Prop 3** (II-B), **Prop 4** (III-D) | R3-3 |
| `theory_revision.tex` Lemma 1 | **Prop 2** (II-A), proof xuống Appendix A | R3-3 |
| `theory_revision.tex` §C1 three-stage | **toàn bộ III-C**: Def 4 + Algorithm 1 + Eq (6) + **Theorem 1** | R4 — Theorem 1 sai |
| `theory_revision.tex` §Identifying entanglement | phần z-test trong **III-D** | Prop 4 sai giao thức |
| `fig5_c1_dimension_selection.pdf` | **Fig 5** (Pareto frontier) trong V-A | Pareto không lọc gì |
| `fig9_learning_curve_nslkdd.pdf` | **Fig 9** trong V-D | thêm chế độ natural + crossover |
| `fig10_regime_map.pdf` | **Fig 10** trong VI | 110 so sánh thay cho bảng tổng |
| — | **Table III** phải dựng lại | mất cột J, và cột F̃ dán nhầm nhãn |

### Chèn mới

| Mảnh | Chèn vào | Vì |
|---|---|---|
| `novelty_matrix.tex` | **II-D**, cạnh Table I | R3-1, R3-5, R1 |
| `crossover_arms_table.tex` | **V-D** hoặc phụ lục | robustness của crossover qua 2 arm |
| `fig11_unsw_transfer.pdf` | **mục mới** cho UNSW-NB15 | R1 yêu cầu dataset thứ hai |
| `theory_revision.tex` §Corrections | cuối **III** hoặc **VII** | tự khai 3 lỗi |

### Sửa văn bản không cần hình/bảng

| Chỗ | Bản cũ | Bản revision |
|---|---|---|
| IV-B | 5 seed `{0,1,2,3,4}` | 10 run |
| IV-B | "C=1.0 xuyên suốt để tránh bias" nhưng lại tune C cho SVM cổ điển | tune **đối xứng** cả quantum lẫn cổ điển |
| IV-C | "implementation is released" mà không có link | link repo + hash commit (R4 bắt) |
| VII-D | Dataset breadth | cập nhật: đã có UNSW-NB15 |
| Toàn bài | mọi chỗ còn chữ "quantum advantage" | "regime-specific competitiveness" |

---

## 3. Lưu ý về đánh số khi ghép

- **Giữ nguyên C1–C4.** Reviewer trích theo số đó.
- Thêm mục UNSW sẽ **đẩy số mục VI/VII/VIII**. Nên đặt UNSW thành **V-F** (mục con của
  Results) thay vì mục cấp 1, để không xê dịch số mục — reviewer dò lại dễ hơn.
- Bỏ Theorem 1 + Def 4 làm **lùi số** Definition 4 → không còn, và Proposition 1–4 → không
  còn. Lemma 1 là môi trường mới. Phải rà lại mọi `\ref` sau khi ghép.
- Hình mới: Fig 5, 9, 10 giữ nguyên số; Fig 11 (UNSW) là số mới nối tiếp.
- Bảng mới: novelty matrix và crossover-arms cần số mới → Table VIII, IX (hoặc đưa xuống phụ lục).

---

## 4. Việc còn treo

| # | Việc | Ai |
|---|---|---|
| 1 | 🚨 Xin `.tex` nguồn theo đúng mô tả ở §0 | thầy |
| 2 | Nếu không xin được → tôi dựng lại từ PDF (~1 buổi) | Quan, chờ lệnh |
| 3 | Dựng lại Table III (bỏ cột J, sửa nhãn cột F̃) | Quan |
| 4 | Viết Appendix A (proof BCH của Lemma 1) | Quan |
| 5 | Link repo + commit hash cho mục IV-C | Quan |
