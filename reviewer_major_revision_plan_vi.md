# Kế hoạch Major Revision – Reviewer Report của Manuscript QSVM-NIDS

## 0. Mục đích của tài liệu

Tài liệu này được xây dựng từ **decision letter + comments của Associate Editor và 4 reviewers** cho manuscript:

> **NISQ-Aware Quantum Kernel SVM for Network Intrusion Detection: A Regime-Specific Benchmark on NSL-KDD**

Mục tiêu không chỉ là dịch reviewer sang tiếng Việt, mà còn biến toàn bộ review thành một **revision roadmap có thể triển khai được**:

1. Reviewer thực sự đang phàn nàn điều gì?
2. Họ đang yêu cầu **sửa câu chữ**, **sửa lý thuyết**, hay **bổ sung experiment**?
3. Vấn đề nào là **bắt buộc phải giải quyết** để tránh bị reject ở vòng này?
4. Experiment/code/notebook nào cần sửa hoặc bổ sung?
5. Kết quả nào cần đưa vào manuscript, supplementary material và rebuttal?
6. Claim nào phải giảm mức độ mạnh?
7. Thứ tự thực hiện tối ưu là gì để không làm lại toàn bộ pipeline nhiều lần?

> **Đánh giá tổng thể:** Đây là một **Major Revision thật sự**, nhưng decision letter cho thấy Editor vẫn đánh giá manuscript có khả năng cứu được. Điểm rất quan trọng là EIC nói rõ TETC **không cho phép thêm một vòng major revision thứ hai**, nên lần sửa này cần xử lý toàn bộ các yêu cầu cốt lõi một cách có hệ thống.

---

# 1. Executive Summary – Reviewer thực sự muốn gì?

Nếu nén toàn bộ review xuống một câu:

> **Reviewer không phản đối hướng nghiên cứu “when is QSVM useful?”, nhưng họ chưa tin rằng evidence hiện tại đủ mạnh để kết luận rằng QSVM có practical/quantum advantage.**

Họ muốn paper chuyển từ:

> “QSVM tốt hơn classical trong một số regime”

thành cách claim thận trọng hơn:

> “Trong experimental setting được nghiên cứu, QSVM-ZZ cho thấy advantage so với các baseline được benchmark trong một số regime cụ thể; advantage này cần được đánh giá thêm trên dataset, baseline, hardware-noise model và kernel-tuning setting rộng hơn.”

Có **7 nhóm vấn đề lớn**:

| Nhóm | Mức độ | Reviewer |
|---|---|---|
| Classical baselines quá yếu / thiếu XGBoost, RF, TabNet, FT-Transformer… | **Critical** | R1, R2, AE |
| Chỉ NSL-KDD, cần dataset khác | **Critical** | R1, AE |
| NISQ-aware nhưng gần như chỉ chạy ideal simulator | **Critical** | R1, R3, AE |
| C1/Theorem 1 có vấn đề logic/số liệu | **Critical** | R4 |
| Hyperparameter tuning không đối xứng | **High** | R1, R4 |
| Novelty/related work chưa đủ mạnh | **High** | R1, R3, R4, AE |
| Statistical base còn mỏng + negative regimes chưa được xử lý đối xứng | **High** | R2 |

Ngoài ra có một nhóm **submission/reproducibility/reference hygiene**:

- supplementary chưa được cung cấp;
- code/repository chưa có link;
- Table VI vs Table IV cần giải thích;
- citation [15] có lỗi;
- citation [26] phải kiểm tra vì reviewer không tìm thấy;
- cần giữ ≤45 references;
- mọi thay đổi bibliography phải highlight vàng và giải thích;
- author list/affiliation phải kiểm soát cực chặt.

---

# 2. Decision Letter của Editor – dịch và hiểu đúng

## 2.1. EIC nói gì?

### Bản dịch

> “Quá trình review manuscript đã hoàn tất. Dựa trên peer review, manuscript cần major revision. Chúng tôi mời authors trả lời các comment của reviewers và sửa manuscript tương ứng.”

Associate Editor đề xuất major revision và EIC đồng ý.

EIC nhấn mạnh:

> **Tác giả cần address ALL requested modifications**, vì đây là các thay đổi nhằm nâng chất lượng bài. Đồng thời EIC nhắc rằng TETC **không cho phép một vòng major revision thứ hai**.

### Ý nghĩa thực tế

Đây là câu quan trọng nhất trong toàn bộ decision letter.

Không nên chọn kiểu:

> “Reviewer này chỉ góp ý phụ nên bỏ.”

Với lần revision này, chiến lược an toàn là:

> **Mọi comment đều phải có một response rõ ràng trong rebuttal.**

Ngay cả khi không làm đúng yêu cầu của reviewer, cần:

1. giải thích tại sao;
2. cung cấp evidence thay thế;
3. sửa claim cho phù hợp.

---

# 3. Yêu cầu nộp revision của TETC

Editor yêu cầu **3 sản phẩm**:

### 3.1. Clean copy

Bản manuscript cuối:

- không highlight;
- không annotation.

### 3.2. Annotated copy

Một bản:

- các text mới/sửa được highlight **yellow**.

### 3.3. Rebuttal letter

Phải có:

- summary of differences;
- detailed point-by-point response đến từng reviewer.

### 3.4. Deadline

Decision letter ghi deadline:

> **13-Oct-2026**

Vì EIC nói không có second round major revision, nên nên coi đây là:

> **revision deadline cứng để hoàn tất toàn bộ technical validation.**

---

# 4. Quy định page length

TETC:

> manuscript > 12 pages sẽ chịu Mandatory Overlength Page Charges.

Manuscript hiện tại có 11 trang theo file được cung cấp.

Điều này có một hệ quả rất quan trọng:

> Bổ sung experiment nhưng không được để paper phình quá mức nếu chưa cần thiết.

Chiến lược:

- core results → main paper;
- quá nhiều tables / ablations → supplementary;
- methodology mới quan trọng → main paper;
- implementation detail → supplementary/repository.

---

# 5. Quy định bibliography

TETC yêu cầu:

- ≤45 bibitems;
- chỉ giữ references relevant;
- self-citations phải được xử lý theo policy;
- additions/deletions phải highlight vàng;
- mọi thay đổi bibliography cần có lý do mạnh trong rebuttal.

Reviewer cũng phát hiện reference error.

Do đó revision phải có một bước riêng:

> **Reference audit toàn bộ bibliography.**

---

# 6. Associate Editor – thông điệp tổng quát

AE nói manuscript:

### Điểm mạnh

- timely;
- relevant;
- well-organized;
- easy-to-follow;
- majority reviewers vẫn thấy có đủ contribution.

### Nhưng có 6 vấn đề chính

#### AE-1. Claims quá generic so với evidence

Paper nói “advantage”, nhưng experiment chủ yếu so với SVM.

#### AE-2. Literature coverage chưa đủ

Một số recent work 2025–2026 chưa được đưa vào.

#### AE-3. Một số references có vấn đề

Có reference reviewer cho rằng không tồn tại/misattributed.

#### AE-4. Cần thêm dataset

Reviewer 1 muốn validation trên dataset khác.

#### AE-5. Cần non-SVM baseline

Reviewer 1, Reviewer 2 và AE đều nhấn mạnh.

#### AE-6. NISQ-ready claim chưa đủ evidence

Reviewer muốn:

- noisy simulation;
- realistic backend noise;
- hoặc giảm claim.

### AE kết luận

> Manuscript **có cơ hội tốt để được đưa vào shape tốt**, nhưng “with quite some effort”.

Đây là tín hiệu tích cực:

> **Paper chưa bị đánh giá là fundamentally broken.**

Nhưng cần một revision substantial.

---

# 7. REVIEWER 1 – dịch và phân tích từng comment

## R1.1 – Related work thiếu

### Reviewer nói

Paper bỏ sót:

> “Benchmarking quantum machine learning methods for intrusion detection on noisy quantum computers” (Quantum Machine Intelligence, 2026)

và yêu cầu:

- thảo luận rõ paper này;
- giải thích khác biệt;
- bổ sung recent works 2025–2026;
- cập nhật Table I.

### Reviewer thực sự muốn gì?

Reviewer đang nói:

> “Novelty claim của bạn chưa đáng tin nếu bạn chưa chứng minh mình khác gì với những benchmark mới nhất.”

### Action

**Bắt buộc:**

1. thêm work reviewer chỉ ra;
2. audit literature 2025–2026;
3. sửa Table I;
4. thêm cột/axis thể hiện:
   - hardware/noise;
   - ablation;
   - regime stress;
   - low-data;
   - classical baseline breadth;
   - dataset breadth;
   - real hardware vs simulator.

### Quan trọng

Không được chỉ thêm citation.

Phải viết:

> “Các work trước làm X; paper chúng tôi làm Y; khoảng trống còn lại là Z.”

---

# 8. R1.2 – NSL-KDD quá cũ, cần dataset khác

### Reviewer nói

NSL-KDD là benchmark aging.

Paper có nói supplementary làm UNSW-NB15 nhưng reviewer không được xem supplementary.

Reviewer yêu cầu:

> validation trên ít nhất một additional modern intrusion-detection dataset.

### Action – PRIORITY 1

Bắt buộc nên hoàn thành:

> **UNSW-NB15 đầy đủ và reproducible.**

Không nên chỉ copy một bảng kết quả.

Cần chạy tối thiểu:

- same preprocessing philosophy;
- same QSVM configuration selection protocol;
- same classical baselines;
- same C3 prior-shift test nếu có thể;
- same C4 low-data sweep nếu computationally feasible.

### Mức tối thiểu an toàn

Nếu thời gian có hạn:

**UNSW-NB15 + main stationary benchmark + prior shift + low-data**

là hợp lý hơn chạy một dataset thứ hai nhưng chỉ có một F1.

### Cần đặc biệt chú ý

Dataset mới phải dùng:

> **zero leakage pipeline**

và phải giải thích rõ:

- feature preprocessing;
- categorical handling;
- train/test split;
- class mapping;
- binary vs multiclass.

---

# 9. R1.3 – Hyperparameter selection không đối xứng

### Reviewer nói

QSVM:

`C = 1.0` cố định.

Classical SVM:

`C` được validation-select.

Reviewer hỏi:

> Nếu classical được tune còn quantum không được tune thì comparison có fair không?

### Đây là criticism hợp lý.

Paper hiện tại lập luận:

> cố định C=1 cho QSVM để tránh biased hyperparameter tuning.

Nhưng reviewer không thấy đủ.

### Action – PRIORITY 1

Chạy **QSVM C sensitivity**.

Ví dụ:

`C ∈ {0.01, 0.1, 1, 10, 100}`

hoặc một grid hợp lý.

Quan trọng:

- tune trên validation split;
- không dùng test để chọn;
- report:
  - F1,
  - KTA nếu cần,
  - selected C frequency,
  - mean ± std.

### Tốt hơn nữa

Có hai protocol:

#### Protocol A – Strict preset

QSVM C=1, như manuscript cũ.

#### Protocol B – Symmetric tuned

C cho **cả QSVM và classical SVM** được validation tune.

Sau đó main conclusion nên dựa trên Protocol B nếu nó không quá khác.

### Mục tiêu

Chứng minh:

> Advantage không phải artifact của việc QSVM “không được tune”.

---

# 10. R1.4 – Claims quá mạnh

Reviewer phản đối wording:

> “The quantum advantage is real and measurable in two regimes…”

vì paper chỉ benchmark SVM variants.

### Action – BẮT BUỘC

Sửa toàn bộ claim:

### Không nên viết

> quantum advantage

một cách generic.

### Nên viết

> “observed advantage over the evaluated classical baselines”

hoặc:

> “QSVM-ZZ shows a consistent empirical advantage over the benchmarked SVM configurations in…”

### Conclusion mới nên nói

> “Within the evaluated datasets, baselines, embedding, and simulation protocol…”

### Không nên claim

- universal quantum advantage;
- practical superiority over classical ML;
- production superiority;
- quantum computational speedup.

---

# 11. R1.5 – Cần non-SVM baselines

Reviewer đề xuất:

- XGBoost;
- CatBoost;
- TabNet;
- FT-Transformer.

### Associate Editor cũng nhấn mạnh.

### Đây là một trong những yêu cầu quan trọng nhất.

Vì câu:

> “when quantum is worth it”

ngụ ý competitor thực tế.

Industry không nhất thiết dùng SVM.

### Action – PRIORITY 1

Ít nhất phải có:

1. **XGBoost**
2. **Random Forest**

Khuyến nghị thêm:

3. **CatBoost**

Nếu tài nguyên đủ:

4. **TabNet hoặc FT-Transformer**

### Nếu không thể chạy tất cả

Không nên cố cho có.

Chiến lược hợp lý:

> XGBoost + Random Forest + một deep tabular baseline.

### Vì sao XGBoost cực kỳ quan trọng?

NSL-KDD là:

- tabular;
- mixed categorical/numerical;
- imbalanced.

XGBoost là comparator thực tế hơn.

---

# 12. R1.6 – NISQ feasibility chưa đủ

Reviewer nói:

> Finite-shot noise không mô phỏng realistic hardware noise.

Thiếu:

- gate errors;
- decoherence;
- readout errors.

### Action – PRIORITY 1

Bổ sung noisy simulation.

Có thể dùng:

- Qiskit Aer noise model;
- IBM FakeBackend/noise properties;
- realistic gate/readout noise.

### Tối thiểu

Chạy final 4-qubit depth-2 configuration qua:

- ideal statevector;
- finite-shot ideal;
- noisy simulator.

### Nên test

Ví dụ:

- 128 / 512 / 2048 shots;
- noisy backend;
- readout error;
- depolarizing error;
- thermal relaxation nếu feasible.

### Metrics

- Gram matrix Frobenius similarity;
- F1;
- accuracy;
- KTA;
- kernel MAE;
- degradation vs ideal.

### Nếu noisy model làm performance xấu?

**Không được giấu.**

Đây có thể trở thành một finding:

> “NISQ-aware selection is hardware-conscious, but model performance is sensitive to realistic noise.”

Điều này thậm chí làm regime-map narrative trung thực hơn.

---

# 13. R1.7 – Low-data regime có crossover không?

Reviewer nhận xét:

> QSVM dường như thắng ở mọi N.

Nếu vậy thì tại sao gọi là “low-data advantage”?

### Action

Không nhất thiết phải tạo crossover giả.

Có 2 trường hợp:

### Case A – Có crossover

Nếu chạy đến:

`N = 2k, 5k, 10k, 20k`

và classical bắt đầu thắng:

> đây là một kết quả rất tốt.

Khi đó regime map thực sự có boundary.

### Case B – Không có crossover trong range thực tế

Cũng hoàn toàn hợp lệ.

Khi đó viết:

> “Within the evaluated sample sizes, no crossover was observed.”

và đổi wording:

> “small-sample robustness/advantage”

thay vì:

> “low-data regime only”.

### Khuyến nghị

Nên mở rộng:

`N ∈ {100, 200, 500, 1000, 2000, 5000}`

nếu computational budget cho phép.

---

# 14. R1.8 – Table VI và Table IV không nhất quán

Reviewer nhìn thấy:

- Table IV:
  `Ntrain=1000, Ntest=300`
- Table VI:
  `N=1000`, test toàn bộ 22,544.

F1 khác nhau.

### Đây thực ra là khác experimental protocol.

Table IV:

> 1000 train → **300 test subset**

Table VI:

> 1000 train → **full KDDTest+ = 22,544**

Vì thế F1 không bắt buộc giống.

### Action

Phải viết rõ ngay caption/table discussion:

> “Table IV and Table VI use the same training budget at N=1000 but different evaluation sets; Table IV uses the fixed 300-sample multi-run test subsets, whereas Table VI evaluates on the complete 22,544-sample KDDTest+ split. Therefore their absolute F1 values are not directly comparable.”

Đây là một **clarification rất dễ sửa**.

---

# 15. R1.9 – Classical F1 có vẻ thấp

Reviewer thấy:

> classical F1 thấp hơn literature thường báo cáo.

### Nguyên nhân có thể liên quan:

- full 5-class / binary mapping;
- strict preprocessing;
- train/test semantics;
- rare attacks;
- zero leakage;
- full KDDTest+;
- different metrics;
- no tuned classical model under same exact protocol.

### Action

Thêm một subsection:

> **Benchmark protocol versus commonly reported NSL-KDD results**

Giải thích:

- task formulation;
- preprocessing;
- feature handling;
- labels;
- test split;
- macro-F1 definition.

Không nên cố làm F1 cao hơn chỉ vì reviewer nói thấp.

---

# 16. R1.10 – Supplementary không truy cập được

### Action

Bắt buộc:

- upload supplementary;
- đảm bảo manuscript link/path không lỗi;
- đưa UNSW-NB15 vào supplementary nếu vẫn giữ;
- bổ sung noise experiments;
- bổ sung hyperparameter sensitivity;
- thêm detailed statistics.

---

# 17. REVIEWER 2 – dịch và phân tích

## R2.1 – Classical baseline quá yếu

Reviewer nói:

> “Real competitor in industry is rarely an SVM.”

### Action

Trùng R1:

- XGBoost;
- Random Forest;
- CatBoost;
- có thể deep tabular.

### Đây là criticism về **practical relevance**, không chỉ performance.

---

# 18. R2.2 – Kernel methods cũng có exponential concentration

Paper viết:

> kernel avoids barren plateau.

Reviewer nói:

> đúng, nhưng quantum kernel có vấn đề conceptually tương tự:

> **exponential concentration of the kernel matrix**.

### Action – Theory revision

Thêm một paragraph vào Background:

> Variational circuits face barren plateaus, while quantum kernels can face concentration/collapse of pairwise similarities as embedding dimension grows.

Sau đó liên kết trực tiếp với:

- n penalty;
- 4-qubit choice;
- kernel geometry.

### Đây sẽ làm theoretical framing tốt hơn.

---

# 19. R2.3 – Five seeds là statistical base khá mỏng

Reviewer phản đối:

- N_train=1000;
- 5 seeds;
- effect size/CIs dựa trên 5 seeds.

### Vấn đề

`n=5` không phải bằng chứng statistical rất mạnh.

### Action – PRIORITY 2

Không nhất thiết phải bỏ 5 seeds vì computation đắt.

Có thể thêm:

- bootstrap CI trên per-instance predictions;
- paired bootstrap;
- repeated stratified resampling;
- confidence intervals theo training subsets.

### Tốt hơn:

thay vì nói:

> “large effect size proves robustness”

nói:

> “the multi-run estimate indicates a large empirical effect under the selected five-seed protocol.”

### Nếu có computational budget

Tăng:

`5 → 10 seeds`

cho core C2/C3/C4.

Không nhất thiết 10 seeds cho mọi experiment nặng.

---

# 20. R2.4 – Negative regimes không được statistical treatment đối xứng

Reviewer thấy:

- positive regimes có Cohen's d/CI;
- negative regimes chỉ giải thích qualitative.

### Action

Phải tạo **full regime table**:

| Regime | Metric | QSVM | Best Classical | Effect size | CI | p-value | Verdict |
|---|---|---:|---:|---:|---|---:|---|
| Prior shift | F1 | ... | ... | +d | CI | p | QSVM |
| Low data | margin/F1 | ... | ... | +d | CI | p | QSVM |
| Perturbation | F1 slope | ... | ... | -d | CI | p | Classical |
| Temporal shift | F1 | ... | ... | d | CI | p | Inconclusive |

### Đây sẽ củng cố Figure 10.

---

# 21. R2.5 – Reference [15] sai article number

Reviewer nói:

> 116990F → phải là 116990B.

### Action

Sửa.

Trong rebuttal:

> “Corrected the bibliographic metadata of Ref. [15].”

---

# 22. R2.6 – Reference [26] có vẻ fabricated/misattributed

Reviewer không tìm thấy:

> Rahman et al. – Quantum machine learning for cybersecurity...

### Action – BẮT BUỘC

Phải audit citation này.

Nếu không xác minh được:

> **Remove it.**

Sau đó thay bằng:

- một review thực sự tồn tại;
- hoặc không cần citation đó.

Không được “cố bảo vệ” một reference không xác minh được.

### Đây là vấn đề integrity rất nghiêm trọng.

---

# 23. REVIEWER 3 – reviewer khó tính nhất

Reviewer 3 phản đối publication.

Nhưng cần đọc kỹ lý do:

> không phải họ nói methodology hoàn toàn sai.

Họ phản đối chủ yếu vì:

1. novelty thấp;
2. gain nhỏ;
3. theory framing yếu;
4. simulation ≠ NISQ;
5. kết quả tương tự previous benchmarking work.

---

# 24. R3.1 – Technical novelty thấp

Reviewer nói:

> 4-qubit depth-2 ZZFeatureMap là một cấu hình QSVM rất phổ biến.

Paper không có:

- new quantum kernel;
- new feature map;
- new training method;
- real hardware implementation;
- theorem establishing new quantum advantage.

### Đây là challenge lớn nhất về novelty.

### Cách giải quyết

Không nên cố “phát minh” một quantum algorithm mới trong revision.

Hãy **định nghĩa novelty của paper chính xác hơn**.

Novelty nên được chuyển sang:

> **evaluation framework + regime analysis + controlled attribution + hardware-constrained embedding selection + stress testing.**

Cụ thể:

### Novelty claim

**Không phải:**
> new QSVM algorithm.

**Mà là:**
> a controlled, regime-aware benchmark framework for understanding when an existing NISQ-feasible quantum kernel is useful for NIDS.

### Cần bổ sung Table “Our work vs recent benchmarks”

Các cột:

- Dataset count
- QSVM configuration
- hardware-aware qubit selection
- entanglement ablation
- class-prior shift
- low-data sweep
- perturbation noise
- temporal shift
- non-SVM baselines
- noisy simulation
- reproducible code
- regime map.

Mục tiêu:

> chứng minh **novelty ở experimental methodology and evaluation question**.

---

# 25. R3.2 – Gain 0.854 vs 0.838 quá nhỏ

Đây là criticism rất quan trọng.

Reviewer hỏi:

> “+0.016 F1 đáng để nói quantum advantage sao?”

### Cách xử lý

Không cố chứng minh:

> +0.016 là huge.

Thay vào đó:

> Stationary benchmark gain là nhỏ.

Sau đó chuyển trọng tâm contribution sang:

- prior shift;
- low-data;
- entanglement attribution;
- robustness/failure boundaries.

Đây chính là lý do title có:

> **Regime-Specific Benchmark**

### Câu nên dùng

> “The stationary benchmark difference is modest; the main contribution is not a large aggregate F1 gain, but identifying the conditions under which the quantum kernel consistently outperforms the evaluated classical baselines.”

---

# 26. R3.3 – Theory section confusing

Reviewer nói:

> propositions are established facts and framing as formal propositions with proofs is inappropriate.

### Action – PRIORITY 1

Cân nhắc **giảm formalism**.

Không cần bỏ toàn bộ mathematics.

Đổi cấu trúc:

### Trước

Definition 1  
Definition 2  
Proposition 1  
Proposition 2  
Proposition 3  
Proposition 4  
Theorem 1

### Nên sửa thành

#### Background

- Quantum kernel definition
- ZZFeatureMap formulation
- local geometric intuition
- KTA interpretation

#### C1 Theoretical motivation

- hardware-cost model
- Pareto selection rationale

#### C2 Statistical test

- ΔKTA significance test

#### Appendix/Supplementary

- detailed proofs.

### Mục tiêu

Theory trở thành:

> **supporting rationale for experiments**

thay vì:

> một pseudo-theoretical contribution.

---

# 27. R3.4 – NISQ-aware nhưng ideal simulation

Đây là criticism lớn.

### Action

Bổ sung realistic noisy simulation.

Nhưng phải thay wording.

### Không nên viết

> “NISQ-ready.”

### Nên viết

> “NISQ-aware.”

hoặc:

> “NISQ-constrained.”

Nói rõ:

> “The framework is hardware-conscious but the present study does not constitute a real-device validation.”

---

# 28. R3.5 – Previous work đã làm tương tự

Reviewer dẫn:

- arXiv:2403.07059
- arXiv:2409.04406
- các benchmarking studies.

### Action

Phải có một **novelty matrix**.

Không được chỉ nói:

> “to the best of our knowledge…”

Hãy cho reviewer nhìn trực tiếp:

> previous study did X  
> another did Y  
> ours adds A+B+C+D.

---

# 29. REVIEWER 4 – Technical/theoretical critique

Reviewer 4 là người chỉ ra các lỗi cụ thể nhất.

## R4.1 – Theorem 1 có vẻ sai

Reviewer chỉ ra:

Paper viết:

> `F~(4) > F~(3)`

nhưng Table III:

- F~(4)=0.471
- F~(3)=0.628

Tức:

`0.471 < 0.628`

### Đây là CRITICAL.

Không được rebuttal bằng wording.

Phải **re-derive theorem**.

---

# 30. C1 phải được audit từ đầu

Reviewer cũng nghi ngờ:

> J(n) maximum dường như ở n=2 khi α=β=γ=1/3.

Table III:

| n | J |
|---:|---:|
| 2 | 0.551 |
| 3 | 0.457 |
| 4 | 0.397 |
| 5 | 0.349 |
| 6 | 0.303 |
| 7 | 0.249 |
| 10 | 0.059 |

Đúng:

> `n=2` có J lớn nhất trong cột equal-weights.

Nhưng n=2 không Pareto vì bị n=4 hoặc n khác dominate?

Cần kiểm tra lại **định nghĩa dominance**.

---

# 31. Điểm cực kỳ quan trọng về Pareto

Theo manuscript:

Pareto tối ưu trên:

`(V, Fe, -Q)`

Nhưng Table III cho thấy:

- V tăng theo n;
- Fe giảm theo n;
- Q tăng theo n.

Do đó cần xem carefully:

> một n nhỏ có thể trade-off Fe/Q.

Reviewer nghi ngờ Pareto filtering có thể không có nhiều tác dụng.

### Action – PRIORITY 1

Chạy lại C1 độc lập:

1. lấy raw values;
2. kiểm tra formula;
3. kiểm tra direction của từng objective;
4. kiểm tra Pareto dominance;
5. kiểm tra scalarization;
6. kiểm tra theorem;
7. test tất cả candidate n.

### Đặc biệt kiểm tra:

> `Fe = 1/DBI`

Nếu Fe giảm theo n thì trong theorem phải dùng đúng inequality.

---

# 32. Có khả năng Theorem 1 nên bỏ

Đây là một quyết định chiến lược.

Nếu proof không thật sự cần:

> **bỏ Theorem 1 khỏi main paper.**

Thay bằng:

> “Empirically, n=4 is selected as the smallest hardware-feasible Pareto point under the adopted cost model.”

Điều này an toàn hơn một theorem bị reviewer bắt lỗi.

### Tốt hơn một theorem sai là không có theorem.

Nếu vẫn giữ:

- re-derive;
- verify;
- unit-test numerical conditions;
- bổ sung proof appendix.

---

# 33. R4.2 – Reproducibility nhưng không có link code

Reviewer:

> paper says implementation released nhưng không đưa machinery/link.

### Action

Cần repository public hoặc ít nhất reviewer-accessible.

Repository nên chứa:

```text
README.md
environment.yml / requirements.txt
pyproject.toml
src/
configs/
notebooks/
scripts/
results/
figures/
supplementary/
```

### Bắt buộc pin:

- Python version;
- Qiskit;
- Qiskit ML;
- scikit-learn;
- numpy;
- scipy.

### Reproduction command

Ví dụ:

```bash
python run_c2.py --seed 0
python run_c3.py --seed 0
python run_c4.py --seed 0
```

Reviewer phải có khả năng:

> clone → install → run → reproduce Table IV/VI.

---

# 34. R4.3 – Proposition 3 khó hiểu

Reviewer:

> paper cite another work nhưng không prove/derive.

### Action

Có 2 lựa chọn:

### Option A – đơn giản hóa

Không gọi Proposition 3.

Viết:

> “Prior work establishes that higher kernel-target alignment can improve generalization bounds under appropriate assumptions…”

và cite paper.

### Option B – nếu muốn giữ

Đưa derivation/proof vào appendix.

### Khuyến nghị

**Option A**.

Vì Theoretical contribution không phải core novelty.

---

# 35. R4.4 – Không thấy rare-attack result của N=500

Reviewer không thể verify claim:

> +6.7 points / d=0.68.

### Action – BẮT BUỘC

Thêm table:

| N | Model | Rare subset | F1 | Margin mean | Margin std | Cohen's d |
|---:|---|---|---:|---:|---:|---:|

Và phải định nghĩa rõ:

- rare subset = R2L ∪ U2R?
- hay attack-only?
- hay all minority class?
- dùng absolute margin hay signed margin?
- d tính across samples hay across seeds?

### Đây là nơi cần đối chiếu lại C6 notebook.

Notebook hiện tại có một kết quả d khoảng **0.4043** ở một protocol, trong khi manuscript nói **0.68**.

=> **Không nên tiếp tục viết 0.68 cho đến khi protocol được xác minh.**

---

# 36. R4.5 – Quantum kernel chưa tune

Reviewer nói:

> classical implementation được tune, quantum không.

Và reviewer liên hệ điều này với perturbation result:

> có thể QSVM tưởng như brittle đơn giản vì cấu hình quantum không được tối ưu.

### Action – PRIORITY 1

Tạo **quantum kernel hyperparameter sensitivity**.

Ít nhất:

- `C`
- `reps r`
- entanglement:
  - full
  - linear nếu feasible
- qubit dimensions:
  - 2
  - 3
  - 4
  - 5
  - 6

Nhưng phải tránh biến paper thành exhaustive architecture search.

### Cách cân bằng

C1 chọn:

`n=4, r=2`

Sau đó sensitivity study:

> “How sensitive is the chosen configuration to reasonable hyperparameter changes?”

Không chọn test set bằng kết quả này.

---

# 37. Tổng hợp reviewer thành 5 “gates” trước resubmission

Tôi khuyến nghị coi revision như 5 gates.

## Gate 1 – Scientific validity

Phải sửa:

- Theorem 1;
- C1;
- C parameter fairness;
- C6 rare-attack result;
- Table IV vs VI explanation.

**Không qua gate này thì không submit.**

---

## Gate 2 – Empirical breadth

Phải thêm:

- non-SVM baselines;
- second dataset;
- noisy simulation.

**Không qua gate này sẽ tiếp tục bị hỏi practical relevance.**

---

## Gate 3 – Claim calibration

Sửa:

- quantum advantage;
- practical deployment;
- NISQ-ready;
- speedup.

**Mọi claim phải match evidence.**

---

## Gate 4 – Literature and novelty

Phải:

- recent literature;
- novelty matrix;
- verify references;
- remove questionable refs.

---

## Gate 5 – Reproducibility

Phải:

- code;
- supplementary;
- exact environment;
- exact seeds;
- reproducible figures.

---

# 38. Revision plan – ưu tiên theo thứ tự

## PHASE 0 — Freeze current baseline

Trước khi sửa code:

- archive manuscript hiện tại;
- archive all current notebooks;
- export current figures;
- export current tables;
- record package versions;
- record random seeds.

Tạo tag:

```text
revision_v0_original
```

---

# 39. PHASE 1 — Fix C1/theory FIRST

### Mục tiêu

Đảm bảo paper không còn mathematical inconsistency.

### Việc cần làm

1. Recompute Table III.
2. Reimplement Pareto selection independently.
3. Verify `V`.
4. Verify `Fe`.
5. Verify `Q`.
6. Verify dominance.
7. Verify `J`.
8. Re-derive Theorem 1.
9. Decide:
   - keep theorem;
   - sửa theorem;
   - hoặc bỏ theorem.

### Output

- `C1_verified.ipynb`
- corrected Table III
- corrected Fig. 5
- revised Section III-C.

---

# 40. PHASE 2 — Symmetric hyperparameter tuning

### Experiment A

QSVM C sensitivity:

`C ∈ {0.01, 0.1, 1, 10, 100}`

### Experiment B

SVM same grid.

### Protocol

- validation split;
- no test leakage;
- 5 seeds minimum.

### Output

- hyperparameter sensitivity figure;
- table of best C;
- main result with tuned configuration;
- supplementary full grid.

---

# 41. PHASE 3 — Strong classical baselines

## Minimum

- SVM-RBF
- SVM-Poly2
- SVM-Linear
- Random Forest
- XGBoost

## Recommended

- CatBoost

## Optional

- TabNet / FT-Transformer.

### Không nên

Thêm quá nhiều model nhưng không tune đúng.

### Mục tiêu

Câu hỏi cần trả lời:

> “QSVM-ZZ có còn useful khi gặp strong tabular baselines không?”

Không nhất thiết phải thắng tất cả.

Nếu XGBoost thắng:

> đó là kết quả khoa học hợp lệ.

---

# 42. PHASE 4 — Second dataset

## Khuyến nghị

**UNSW-NB15**.

### Protocol

- preprocessing separately;
- train-only fitting;
- same QSVM methodology;
- classical baselines;
- stationary F1;
- prior-shift;
- low-data.

### Không được reuse

- PCA basis từ NSL-KDD;
- scaler từ NSL-KDD;
- feature selection từ NSL-KDD.

Mỗi dataset phải có pipeline riêng.

---

# 43. PHASE 5 — Realistic noise simulation

### Baselines

1. Statevector ideal
2. Shot-noise ideal
3. Noisy simulator

### Noise models

Có thể thử:

- depolarizing;
- readout;
- thermal relaxation.

### Backend-style model

Một FakeBackend/Aer-noise model phù hợp là tốt nhất nếu stable.

### Metrics

- F1;
- KTA;
- Gram Frobenius similarity;
- MAE;
- nSV.

### Câu hỏi cuối:

> At what noise level does QSVM-ZZ stop being competitive?

Đây thậm chí có thể trở thành một **sub-regime map**.

---

# 44. PHASE 6 — Expand sample complexity

Hiện tại:

`N={100,200,500,1000}`

Nên cân nhắc:

`N={100,200,500,1000,2000,5000}`

Nếu computational budget cho phép.

### Mục tiêu

Tìm:

> crossover.

Nếu không có crossover:

> nói rõ rằng không quan sát được crossover trong tested range.

---

# 45. PHASE 7 — Strengthen negative regimes

Cần làm symmetric.

## Perturbation

Report:

- mean F1;
- std;
- slope;
- CI;
- Cohen's d nếu phù hợp.

## Temporal

Report:

- F1;
- per-model difference;
- CI;
- McNemar p;
- effect size;
- conclusion = “inconclusive” nếu p>0.05.

### Đừng gọi

> “QSVM fails”

nếu evidence chỉ là:

> performance drops more rapidly.

---

# 46. PHASE 8 — Revise theory

### Main paper nên giữ

- Quantum kernel definition.
- ZZFeatureMap intuition.
- hardware cost.
- Pareto rationale.
- KTA interpretation.

### Move/shorten

- long PSD proof;
- KTA bound proof;
- technical derivations.

### Đặc biệt

Bỏ cách trình bày khiến reader nghĩ:

> paper đang claim theoretical quantum advantage.

Theory nên hỗ trợ empirical methodology.

---

# 47. PHASE 9 — Rewrite narrative / title logic

Title hiện tại:

> **NISQ-Aware Quantum Kernel SVM for Network Intrusion Detection: A Regime-Specific Benchmark on NSL-KDD**

Có thể giữ vì khá phù hợp.

Nhưng language toàn paper cần thống nhất:

### Từ khóa

- regime-specific;
- empirical;
- benchmarked baselines;
- observed advantage;
- hardware-aware;
- NISQ-constrained;
- not universal.

---

# 48. Claim replacement table

| Claim cũ | Nên sửa thành |
|---|---|
| “The quantum advantage is real…” | “QSVM-ZZ shows an empirical advantage over the evaluated classical baselines…” |
| “when quantum kernel is worth the overhead” | “when QSVM-ZZ is competitive under the evaluated regime…” |
| “NISQ-feasible” | “NISQ-aware / hardware-constrained” |
| “robust under prior shift” | “shows a consistent advantage under the evaluated prior-shift protocol” |
| “low-data advantage” | “advantage within the evaluated low-data range” |
| “deployment-ready” | “suggestive for deployment-oriented evaluation” |
| “quantum advantage” | “observed QSVM-ZZ advantage” |

---

# 49. Phase 10 — Rebuild the regime map

Figure 10 hiện tại nên trở thành figure “signature”.

Nhưng revision version nên có:

- positive effects;
- negative effects;
- inconclusive effects;
- confidence intervals;
- baseline identity.

Ví dụ:

```text
              QSVM better        Classical better

Prior shift       +d
Low-data          +d
Noise                                   -d
Temporal                         ≈ 0 / inconclusive
Stationary         small +d
```

### Đây sẽ trực tiếp trả lời reviewer 2.

---

# 50. Phase 11 — Reproducibility package

Repository phải có:

```text
01_preprocessing/
02_c1_pareto/
03_c2_entanglement/
04_c3_prior_shift/
05_c4_sample_complexity/
06_noise/
07_baselines/
08_unsw_nb15/
09_statistics/
10_figures/
supplementary/
```

Mỗi experiment có:

- config;
- seed;
- input;
- output;
- command.

---

# 51. PHASE 12 — Supplementary material

Tôi khuyến nghị supplementary gồm:

## S1. Full hyperparameter tables

## S2. Full Pareto sweep

## S3. Full noisy simulation results

## S4. Additional baseline results

## S5. UNSW-NB15

## S6. Rare-attack analysis

## S7. Calibration

## S8. Statistical details

## S9. Proofs/derivations nếu giữ

---

# 52. Main paper page strategy

Vì TETC cảnh báo >12 pages:

### Main paper giữ

- problem;
- novelty;
- C1;
- C2;
- core C3;
- core C4;
- noisy simulation summary;
- strong baseline summary;
- second-dataset summary;
- regime map;
- limitations.

### Supplementary chuyển

- full grids;
- detailed tables;
- calibration;
- proofs;
- per-seed details;
- all ablations.

---

# 53. Rebuttal strategy – không nên “đấu” với reviewer

Một rebuttal tốt không phải:

> “Reviewer is wrong.”

Mà:

> “We agree with the concern and have added X.”

hoặc:

> “We agree that the original wording was too strong. We have therefore revised Section VI from A to B.”

### Đối với Reviewer 3

Không cần thuyết phục reviewer rằng:

> “0.016 is huge.”

Hãy nói:

> “We agree the stationary gain is modest. We have therefore reframed the contribution around regime-specific characterization rather than aggregate superiority.”

Đây là cách rất mạnh.

---

# 54. Cách trả lời criticism novelty

### Không nên

> “No previous work has done this.”

Vì reviewer đã chỉ ra nhiều work.

### Nên

> “We have revised the novelty statement and added a structured comparison with recent benchmarking studies. The revised manuscript positions the contribution as a controlled, hardware-aware regime evaluation rather than a new quantum algorithm.”

Sau đó Table mới chứng minh.

---

# 55. Cách trả lời criticism NISQ

### Không nên

> “4 qubits is enough for NISQ.”

### Nên

> “We agree that the original evidence did not justify a broad NISQ-feasibility claim. We therefore added realistic noisy simulations and revised the terminology from ‘NISQ-ready’ to ‘NISQ-aware/hardware-constrained’.”

---

# 56. Cách trả lời criticism classical baselines

### Nếu QSVM vẫn thắng

> “The advantage persists against XGBoost/Random Forest/… under the matched protocol.”

### Nếu QSVM thua

Cũng tốt:

> “The new strong baseline experiments show that the advantage is specific to SVM-style comparisons, so we have narrowed the practical claim accordingly.”

Điều quan trọng là:

> **Reviewer phải thấy bạn không cherry-pick.**

---

# 57. Cách trả lời Reviewer 4 về Theorem 1

Không nên cố bảo vệ theorem nếu math sai.

### Response kiểu tốt nhất

> “We thank the reviewer for identifying this inconsistency. We independently recomputed the Pareto objective and found that the inequality in the original theorem statement was incorrect. We have corrected the derivation and revised Table III/Fig. 5 accordingly.”

Nếu theorem không còn cần:

> “Because the theorem was not essential to the empirical contribution, we removed it and retained the Pareto selection as an empirically verified hardware-aware procedure.”

**Khuyến nghị cá nhân:** nếu theorem sau khi audit không thật sự mạnh, **bỏ theorem** là lựa chọn an toàn.

---

# 58. Cách xử lý Reviewer 4 về Proposition 3

Khuyến nghị:

> bỏ “Proposition 3” khỏi main paper.

Viết ngắn:

> “Prior KTA theory motivates using alignment as a kernel diagnostic; however, KTA is not used as a standalone accuracy surrogate.”

Điều này dễ hiểu hơn và tránh reviewer kéo paper vào tranh luận theory không cần thiết.

---

# 59. Cách xử lý Reviewer 4 về tuning

Cần nói rõ:

> “The original fixed-C protocol was intended to prevent post-hoc optimization on a small quantum training subset, but we agree that the asymmetric treatment could itself bias the comparison.”

Sau đó:

> thêm symmetric tuning experiment.

Đây là response rất thuyết phục.

---

# 60. Một điểm rất quan trọng: Đừng thêm experiment theo kiểu “patch”

Reviewer đang nhìn paper như một scientific argument.

Vì vậy mỗi experiment mới phải trả lời một objection:

| New experiment | Objection it answers |
|---|---|
| XGBoost/RF | Classical baseline too weak |
| UNSW-NB15 | Single old dataset |
| C sensitivity | Unfair tuning |
| Noisy simulator | Not really NISQ |
| Larger N | No crossover |
| Negative-regime statistics | Asymmetric evidence |
| Pareto re-check | Theorem/Pareto correctness |
| Rare subset table | Unsupported +6.7/d=.68 |
| Code release | Reproducibility |

Đây là cách tốt nhất để revision có logic.

---

# 61. Một “revision matrix” nên duy trì trong project

Tạo file:

```text
REVIEW_REVISION_MATRIX.xlsx
```

với các cột:

| ID | Reviewer | Comment | Severity | Action | Experiment | Code | Manuscript section | Supplement | Status |
|---|---|---|---|---|---|---|---|---|---|

Ví dụ:

| R4-1 | R4 | Theorem 1 inconsistent | CRITICAL | Re-derive/remove | C1 audit | c1_verified | III-C | S2 | TODO |
| R1-5 | R1 | Need XGBoost | CRITICAL | Add baseline | B1 | baseline_tabular | V-B | S4 | TODO |
| R1-2 | R1 | Need dataset | CRITICAL | Add UNSW | U1 | unsw | V-F | S5 | TODO |

Đây nên là “single source of truth” của revision.

---

# 62. Priority classification

## RED – phải xử lý

1. C1/Theorem correctness.
2. XGBoost/RF/strong baseline.
3. UNSW-NB15.
4. Noisy simulation.
5. Claim calibration.
6. Reference audit.
7. Supplementary availability.
8. Reproducibility/code.
9. Rare-attack N=500 discrepancy.
10. Hyperparameter fairness.

## ORANGE – rất nên làm

11. Larger sample-complexity range.
12. More seeds / bootstrap.
13. Symmetric negative-regime statistics.
14. Recent-literature matrix.
15. Theory simplification.

## GREEN – có thể cải thiện

16. Calibration C5.
17. Hybrid deployment discussion.
18. Extra plots.

---

# 63. Suggested revised paper architecture

## I. Introduction

- NIDS challenge.
- quantum kernel motivation.
- literature gap.
- recent benchmark gap.
- contribution = regime evaluation, not new kernel.

## II. Related Work

- quantum kernels;
- QSVM IDS;
- recent noisy benchmark;
- regime-specific QML;
- tabular baselines.

## III. Methodology

### A. Problem
### B. Pipeline
### C. Hardware-aware embedding
### D. Entanglement ablation
### E. Prior shift
### F. Sample complexity
### G. Noise model
### H. Hyperparameter protocol

## IV. Experimental Setup

- datasets;
- baselines;
- hardware/simulator;
- tuning;
- seeds;
- statistics.

## V. Results

### A. C1
### B. C2
### C. C3
### D. C4
### E. Strong baselines
### F. UNSW-NB15
### G. Noise

## VI. Regime Map

- positive;
- negative;
- inconclusive.

## VII. Limitations

- real hardware;
- dataset breadth;
- larger qubits;
- computational cost;
- remaining generalization.

## VIII. Conclusion

- no universal quantum superiority;
- observed regime-specific advantage;
- future real hardware.

---

# 64. Revised contribution statements – đề xuất

Thay contribution cũ bằng:

### C1
A hardware-constrained embedding-selection procedure that jointly considers information retention, class geometry, and two-qubit-gate cost.

### C2
A controlled ablation that quantifies the incremental contribution of ZZ entanglement under matched preprocessing and SVM conditions.

### C3
A regime-oriented robustness evaluation covering class-prior shift and temporal/feature perturbation, with both positive and null/negative outcomes reported.

### C4
A sample-complexity analysis that characterizes the operating range in which QSVM-ZZ is competitive under limited labels.

### C5 – revision-added
A broader empirical comparison against strong non-SVM tabular baselines and a second IDS dataset, establishing how far the observed regime-specific advantage generalizes.

Đây là cách novelty sẽ mạnh hơn rất nhiều.

---

# 65. Một vấn đề cần tránh: “paper becomes too broad”

Reviewer đang yêu cầu rất nhiều.

Nhưng nếu làm:

- 2 datasets;
- 10 classical models;
- 20 noise models;
- 10 qubit dimensions;
- 20 sample sizes;

paper sẽ mất focus.

### Scope nên giữ

**Core question:**

> When does a small, NISQ-aware ZZ quantum kernel provide useful empirical value for NIDS?

Mỗi experiment phải map vào câu hỏi này.

---

# 66. “Minimum viable revision” nếu thời gian rất gấp

Nếu phải ưu tiên cực mạnh, tôi chọn:

### Must do

1. **Fix/rewrite C1 theorem + Pareto.**
2. **XGBoost + Random Forest.**
3. **UNSW-NB15.**
4. **Noisy simulation.**
5. **QSVM C sensitivity + symmetric tuning.**
6. **Fix Table IV/VI explanation.**
7. **Verify/fix rare-attack +6.7/d=.68.**
8. **Reference audit.**
9. **Supplementary upload.**
10. **Code repository.**
11. **Tone down all “quantum advantage” claims.**
12. **Update related work 2025–2026.**

Nếu làm được 12 mục này một cách sạch sẽ, manuscript sẽ trả lời phần lớn criticism.

---

# 67. “Strong revision” nếu còn đủ thời gian

Thêm:

13. CatBoost.
14. TabNet/FT-Transformer.
15. N=2000/5000.
16. 10 seeds cho core experiments.
17. bootstrap CIs.
18. symmetric statistics cho negative regimes.
19. better noisy hardware models.
20. revised theory appendix.
21. calibration C5.
22. automated reproduction scripts.

---

# 68. Timeline đề xuất từ bây giờ đến deadline

Deadline:

> **13-Oct-2026**

### Tuần 1

- freeze baseline;
- audit C1;
- verify Theorem 1;
- audit references;
- audit manuscript/table discrepancies.

### Tuần 2

- XGBoost/RF;
- QSVM C sensitivity;
- symmetric tuning.

### Tuần 3

- UNSW-NB15.

### Tuần 4

- noisy simulation.

### Tuần 5

- extended sample complexity;
- negative-regime statistics;
- rare-attack analysis.

### Tuần 6

- rewrite manuscript;
- revise Introduction/Related Work;
- novelty matrix.

### Tuần 7

- supplementary;
- code repository;
- reproduction scripts.

### Tuần 8

- rebuttal;
- clean copy;
- yellow-highlighted copy;
- final consistency audit.

---

# 69. Final pre-submission audit

## Scientific correctness

- [ ] Table III recomputed.
- [ ] Pareto code independently verified.
- [ ] Theorem 1 corrected or removed.
- [ ] All formulas checked.
- [ ] C sensitivity complete.
- [ ] Rare-attack result verified.
- [ ] Table IV vs VI explained.
- [ ] No unsupported claim remains.

## Experimental

- [ ] XGBoost.
- [ ] Random Forest.
- [ ] At least one strong tabular baseline if feasible.
- [ ] UNSW-NB15.
- [ ] Noisy simulation.
- [ ] Existing C2/C3/C4 rerun if core pipeline changes.
- [ ] Negative regimes have statistics.
- [ ] Sample complexity interpretation updated.

## Literature

- [ ] 2025–2026 relevant literature.
- [ ] Reviewer-suggested papers evaluated.
- [ ] Reference [15] corrected.
- [ ] Reference [26] verified/removed.
- [ ] ≤45 references.
- [ ] All bibliography changes documented.

## Reproducibility

- [ ] Repository accessible.
- [ ] README.
- [ ] Environment pinned.
- [ ] Seeds.
- [ ] Configs.
- [ ] Scripts reproduce tables.
- [ ] Supplementary accessible.

## Submission

- [ ] Clean copy.
- [ ] Yellow-highlight copy.
- [ ] Point-by-point rebuttal.
- [ ] Cover letter.
- [ ] Author list unchanged.
- [ ] Affiliation changes reported if any.
- [ ] Funding/acknowledgement updated.
- [ ] Page count checked.
- [ ] Deadline: 13-Oct-2026.

---

# 70. Kết luận chiến lược

Đọc toàn bộ review, tôi không nghĩ paper nên được cứu bằng cách:

> “làm quantum model phức tạp hơn”.

Reviewer không yêu cầu một quantum algorithm mới.

Hướng sửa mạnh nhất là:

> **làm benchmark rộng hơn, fair hơn, hardware-realistic hơn, mathematically correct hơn và claim khiêm tốn hơn.**

Cụ thể:

```text
CURRENT PAPER

ZZFeatureMap
    ↓
4 qubits
    ↓
SVM baselines
    ↓
NSL-KDD
    ↓
regime map


REVISED PAPER

Hardware-aware ZZ kernel
          ↓
Validated C1 / Pareto
          ↓
Fair hyperparameter tuning
          ↓
SVM + strong tabular baselines
          ↓
NSL-KDD + UNSW-NB15
          ↓
Ideal + realistic noisy simulation
          ↓
Positive + negative + inconclusive regimes
          ↓
Reproducible regime map
```

Điểm cần bảo vệ mạnh nhất của paper sau revision nên là:

> **“We are not claiming a universal quantum advantage. We provide a controlled empirical framework for determining whether a small NISQ-oriented quantum kernel adds value under specific NIDS operating conditions.”**

Đây là framing phù hợp nhất với comment của cả AE, R1, R2, R3 và R4.

---

# 71. Thứ tự làm việc thực tế tôi khuyến nghị

### Bước 1
**Không sửa manuscript ngay.**

### Bước 2
Audit C1/Theorem 1 và toàn bộ discrepancy.

### Bước 3
Chốt một **revised experimental protocol** duy nhất.

### Bước 4
Chạy:
- strong baselines;
- C tuning;
- UNSW;
- noisy simulation.

### Bước 5
Sau khi có kết quả mới mới sửa:
- Introduction;
- Method;
- Results;
- Regime Map;
- Conclusion.

### Bước 6
Cuối cùng mới viết rebuttal.

Lý do:

> rebuttal tốt phải nói về **những gì đã thực sự thay đổi**, không phải hứa sẽ làm.

---

# 72. Một câu để nhớ toàn bộ revision

> **Reviewer không yêu cầu chúng ta chứng minh “quantum mạnh hơn”; họ yêu cầu chúng ta chứng minh rằng câu chuyện “quantum mạnh hơn trong một số regime” là fair, reproducible, mathematically correct, experimentally broad enough, hardware-realistic enough và không overclaimed.**
