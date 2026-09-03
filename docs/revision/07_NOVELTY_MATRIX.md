# Novelty matrix + literature 2025–2026

*Quan, 2026-09-03. Trả lời R3-1, R3-5 (novelty) và R1 (thiếu literature 2025–2026).*

**File kèm**: `paper/paper1/novelty_matrix.tex` (bảng LaTeX dán thẳng) ·
`paper/paper1/figs_revision/captions.tex` (caption 4 hình).

---

## 0. 🔴 Việc quan trọng nhất tìm được: có một bài 2026 gần như trùng đề tài

Trong lúc tra 4 bài reviewer chỉ, tôi tìm ra một bài **không ai trong hội đồng nhắc tới** mà
lại là bài gần bài mình nhất từ trước tới nay:

> **Gillani, Baig, Shah, Ali, Siddiqui (13-08-2026).** *How Quantum Is the Advantage?
> A Fair, Calibration- and Noise-Aware Benchmark and Attribution Audit of Quantum Machine
> Learning for Network Intrusion Detection.* arXiv:2608.18155.

Trùng với ta ở gần như mọi trục:

| | Họ | Ta |
|---|---|---|
| Dataset | **NSL-KDD, UNSW-NB15**, CICIDS2017, NF-ToN-IoT-v2 | **NSL-KDD, UNSW-NB15** |
| Split | **official** KDDTrain+/KDDTest+, official UNSW CSV | **giống hệt** |
| Model | hybrid VQC + QSVM (IQP fidelity kernel, angle projected kernel) | QSVM ZZ/Z fidelity kernel |
| Baseline | RF, XGBoost (5 baseline) | RF, XGBoost (5 baseline cổ điển) |
| Nhiễu | NISQ noise sweep | ideal / finite-shot / noisy simulator |
| Thống kê | McNemar + paired t/Wilcoxon + bootstrap, **BH-FDR trên 108 so sánh** | Wilcoxon + **Holm trong từng family** |
| Số lần lặp | **3–5 seed** | **10 run** |

**Kết luận của họ**: khi cho model cổ điển dùng **cùng front-end** và mức regularisation
tương đương thì "quantum advantage" tổng thể **biến mất** — lợi thế quy về **tiền xử lý**
chứ không phải tính chất lượng tử (F1 −0.039, p=0.021; AUPRC −0.036, p=0.035).

Chỉ **2 lợi thế sống sót** sau hiệu chỉnh FDR, cả hai trên NSL-KDD:

- QSVM vs random-feature kernel: AUPRC +0.075 (q=0.011), ROC-AUC +0.134 (q=0.018)
- Hybrid VQC 4 qubit tại TPR@1%FPR: +0.050 (q=0.030)

### Ba hệ quả

**(a) Phải trích dẫn và phân biệt, không được lờ.** Nộp bản revision sau bài này 2 tháng mà
không nhắc là reviewer sẽ tự tìm ra. Đã đưa vào bảng novelty.

**(b) 🟢 Nó *xác nhận* phát hiện của chính ta, chứ không đánh đổ.** Ta đã đo được điều tương
tự một cách độc lập: ablation ZZ-vs-Z **đảo dấu** dưới `refit_per_N`, và phân rã A/B/C cô lập
được nguyên nhân là **SelectKBest+PCA refit** (trùng 90,5% feature, cosine của PC1 = 0.9966 — vẫn đủ để lật dấu). Tức là
hai nhóm độc lập cùng đi tới "lợi thế đến từ tiền xử lý". Ta còn **mạnh hơn ở chỗ cô lập được
cơ chế** bằng phân rã, trong khi họ chứng minh bằng control có cùng front-end. Nên viết là
*independent corroboration*, và nói rõ ta bổ sung phần cơ chế.

**(c) 🔴 Ảnh hưởng tới Paper 2 (calibration, đã nộp IJNM 04-08-2026).** Bài họ có
"calibration-aware metrics" cho đúng bài toán NIDS. Nộp trước họ 9 ngày nên **không mất quyền
ưu tiên**, nhưng nếu IJNM cho revise thì phải trích. Cần kiểm xem họ có báo ECE/Brier trên
lớp hiếm không — đó mới là chỗ Paper 2 khẳng định. Chưa đọc kỹ phần này.

---

## 1. Bốn bài reviewer chỉ — đã đọc, tóm tắt đúng nội dung

| Ký hiệu | Bài | Nội dung thật |
|---|---|---|
| R3 chỉ | **arXiv:2403.07059** — Bowles, Ahmed, Schuld (03-2024), *"Better than classical? The subtle art of benchmarking quantum machine learning models"* | 12 model QML phổ biến × 6 bài toán phân loại nhị phân → 160 dataset, gói mã nguồn mở trên PennyLane, **mô phỏng không nhiễu**. Là benchmark QML **tổng quát**, không phải IDS. |
| R3 chỉ | **arXiv:2409.04406** — Schnabel & Roth (09-2024, rev 04-2025), *"Quantum Kernel Methods under Scrutiny: A Benchmarking Study"* | FQK vs PQK, 5 họ dataset / 64 dataset, **hơn 20.000 model** có HPO, phân tích tương quan để tìm cơ chế. Benchmark **kernel tổng quát**, không phải IDS. |
| R1 chỉ | **Quantum Machine Intelligence 2026**, doi 10.1007/s42484-026-00379-4, *"Benchmarking quantum machine learning methods for intrusion detection on noisy quantum computers"* | Pegasos-QSVC, VQC, HQNN trên **ToN_IoT + NSL-KDD**, simulator IBM ideal và nhiễu. Tốt nhất: Pegasos-QSVC 94,60% acc / 94,13% F1. ⚠️ Springer chặn, mới đọc được abstract — **cần lấy bản đầy đủ** qua thư viện trường. |
| R4 chỉ | **Carducci, ICAD 2026**, doi 10.1109/ICAD69378.2026.11609075, *"When Does Quantum Computing Provide Advantage for Malware Detection? Structural Complexity and the Intermediate Complexity Window"* | Chỉ lấy được thư mục, **chưa đọc được nội dung**. Từ nhan đề: cùng đặt câu hỏi "khi nào" và đề xuất khái niệm *intermediate complexity window*. ⚠️ Cần bản đầy đủ. |

> **Chưa đọc được toàn văn 2 bài** (QMI 2026 và Carducci 2026). Trong bảng novelty các ô đó
> để **`n/r`** chứ không đoán. Trước khi nộp phải lấy bản đầy đủ — nhất là Carducci, vì R4 nói
> thẳng là "câu hỏi này đã được hỏi ở lĩnh vực khác", nên ta phải đối chiếu khái niệm
> *intermediate complexity window* của họ với *regime map* của ta.

---

## 2. Lập luận novelty — nói gì và KHÔNG nói gì

R3 viết: *"the results of the paper are already established in numerous previous work"*.
Cãi thẳng là thua, vì **họ đúng một nửa**. Lập luận nên đi theo ba bước:

### Bước 1 — Đồng ý với kết luận của họ, và chỉ ra ta cũng ra đúng như vậy

Bowles và Schnabel–Roth kết luận: feature map tổng quát hiếm khi thắng model cổ điển đã tune,
tính trung bình trên nhiều dataset. **Bản revision của ta ra đúng kết quả đó**: trong 110 so
sánh có kiểm định, **21 nghiêng về QSVM, 21 nghiêng về cổ điển, 68 không kết luận được**. Ta
không hề khẳng định ngược lại. Đưa số này ra trước là cách mạnh nhất — nó cho thấy ta không
cố bảo vệ một khẳng định lợi thế.

### Bước 2 — Chỉ ra trục mà không bài nào trong số đó chạm tới

**Không bài nào quét kích thước tập huấn luyện.** Gillani et al. có ablation **bề rộng mạch**
(4/6/8/12 qubit) nhưng **không** thay đổi `N`; Bowles và Schnabel–Roth cũng không. Đây đúng là
trục của C4:

- Crossover tại `N ≈ 2000–5000` trên NSL-KDD, **6/6 tổ hợp** {XGBoost, RF, SVM-RBF} × {đóng
  băng siêu tham số, tune lại mỗi N} → không phải tạo tác của việc tune
- Làm giàu lớp hiếm gấp 12× thì crossover **biến mất** → nói được *cái gì* điều khiển nó
- Crossover **không** chuyển giao sang UNSW → nói được *giới hạn* của nó

### Bước 3 — Hai đóng góp phương pháp còn lại

- **Luật chọn số chiều là một thủ tục chuyển giao được**: cùng luật, không sửa tham số nào,
  ra `n*=4` trên NSL-KDD và `n*=6` trên UNSW (10/10 subset độc lập). Không bài nào có.
- **Bản đồ chế độ**: 110 verdict theo prior, thành phần tấn công, dịch chuyển phân phối và
  kích thước mẫu — thay cho một con số xếp hạng tổng.

### KHÔNG được nói

- ❌ Không nói ta rộng hơn Gillani: họ 4 dataset, ta 2; họ 8 qubit, ta 4–6; họ FDR trên 108
  so sánh, ta Holm trong từng family. **Về bề rộng ta thua** — nói thẳng ra thì đáng tin hơn.
- ❌ Không nói "quantum advantage". Nói "regime-specific competitiveness".
- ❌ Không nói ta là bài đầu hỏi "khi nào" — Carducci đã hỏi cho malware.

---

## 3. Bản nháp đoạn trả lời

### R3-1 + R3-5 (novelty)

> We thank the reviewer for the two benchmarking studies, which we now discuss explicitly
> (Sec. II and Table `\ref{tab:novelty}`). We agree with their central finding, and our revised
> results reproduce it: across 110 controlled comparisons, 21 favour the quantum kernel, 21
> favour a classical baseline and 68 are inconclusive after Holm correction. We therefore make
> no claim of a general quantum advantage, and we have removed the language that suggested one.
>
> Our contribution is on an axis those studies do not examine. Bowles et al. and Schnabel and
> Roth vary model family and dataset; the closest concurrent QML-IDS benchmark, Gillani et al.
> (arXiv:2608.18155), varies circuit width. **None varies the training-set size.** We sweep
> `N` from 10² to 10⁴ under a fixed protocol and find an ordering reversal at
> `N ≈ 2000–5000` on NSL-KDD that persists when hyper-parameters are frozen rather than
> re-tuned (6/6 baseline–arm combinations), disappears when rare attacks are enriched
> 12× as in the submitted version, and does not transfer to UNSW-NB15. Reporting when a
> reversal fails to appear is as much of the contribution as reporting when it does.
>
> We also no longer present the dimension-selection rule as a result but as a procedure, and we
> test it as such: applied unchanged to UNSW-NB15 it returns `n* = 6` rather than 4, on
> 10/10 independent subsets.
>
> We do not claim breadth over Gillani et al.: they evaluate four datasets to our two, at eight
> qubits to our four and six, with FDR correction over a larger comparison family. Our claim is
> narrower and, we hope, complementary.

### R1 (literature 2025–2026)

> We have added the requested work (Quantum Machine Intelligence, 2026) and
> extended Table I with the 2024–2026 literature, including Bowles et al. (2024), Schnabel
> and Roth (2024), Carducci (2026) and the concurrent benchmark of Gillani et al. (2026).
> The last of these reaches, on partly overlapping datasets, the same conclusion we reach
> independently: apparent quantum gains are largely attributable to the classical
> dimensionality-reduction front-end. Our decomposition experiment isolates that mechanism
> directly — refitting SelectKBest and PCA at each `N` is sufficient to reverse the sign of the
> entanglement ablation, even when the refitted front-end retains 90.5% of the same
> features and its first principal component has cosine similarity 0.9966 with the frozen one — and we now present it as corroborating rather than competing evidence.

---

## 4. BibTeX

    @article{bowles2024,
      title   = {Better than classical? The subtle art of benchmarking quantum machine learning models},
      author  = {Bowles, Joseph and Ahmed, Shahnawaz and Schuld, Maria},
      journal = {arXiv preprint arXiv:2403.07059},
      year    = {2024}
    }
    @article{schnabel2024,
      title   = {Quantum Kernel Methods under Scrutiny: A Benchmarking Study},
      author  = {Schnabel, Jan and Roth, Marco},
      journal = {arXiv preprint arXiv:2409.04406},
      year    = {2024}
    }
    @article{qmi2026,
      title   = {Benchmarking quantum machine learning methods for intrusion detection on noisy quantum computers},
      journal = {Quantum Machine Intelligence},
      year    = {2026},
      doi     = {10.1007/s42484-026-00379-4},
      note    = {TODO: bo sung ten tac gia + so trang tu ban day du}
    }
    @article{gillani2026,
      title   = {How Quantum Is the Advantage? A Fair, Calibration- and Noise-Aware Benchmark
                 and Attribution Audit of Quantum Machine Learning for Network Intrusion Detection},
      author  = {Gillani, Syeda Anshrah and Baig, Mirza Samad Ahmed and Shah, Shahid Munir
                 and Ali, Asher and Siddiqui, Hamzah},
      journal = {arXiv preprint arXiv:2608.18155},
      year    = {2026}
    }
    @inproceedings{carducci2026,
      title     = {When Does Quantum Computing Provide Advantage for Malware Detection?
                   Structural Complexity and the Intermediate Complexity Window},
      author    = {Carducci, N. M.},
      booktitle = {2026 IEEE International Conference on AI and Data Analytics (ICAD)},
      pages     = {1--7},
      year      = {2026},
      doi       = {10.1109/ICAD69378.2026.11609075}
    }

---

## 5. Việc còn treo

| # | Việc | Ai |
|---|---|---|
| 1 | Lấy toàn văn QMI 2026 + Carducci ICAD 2026 qua thư viện trường; điền các ô `n/r` | Quan |
| 2 | Đọc kỹ phần calibration của Gillani et al. → đối chiếu với Paper 2 (IJNM) | Quan |
| 3 | Mở rộng Table I của bài bằng literature 2024–2026 | Quan / thầy |
| 4 | Rà lại toàn bài, bỏ hết chữ "quantum advantage" còn sót | Quan / thầy |
| 5 | Sửa reference cũ: [15] `116990F`→`116990B`, bỏ [26] Rahman, giữ ≤45 ref | thầy |
