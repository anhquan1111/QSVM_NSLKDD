# C2 Revision — Tổng hợp vấn đề Reviewer và mức độ giải quyết

## 1. Mục đích của tài liệu

Tài liệu này tổng hợp:

1. Các vấn đề reviewer/Associate Editor đặt ra có liên quan trực tiếp đến C2.
2. Những hạn chế của C2 trong manuscript trước revision.
3. Các thay đổi đã thực hiện trong `C2_revision`.
4. Bằng chứng từ protocol và kết quả chạy mới.
5. Những vấn đề reviewer nào đã được giải quyết hoàn toàn, giải quyết một phần, hoặc vẫn cần xử lý ở cấp manuscript/rebuttal.
6. Cách diễn giải kết quả C2 mới một cách khoa học và không overclaim.

Nguồn review chính là kế hoạch Major Revision tổng hợp từ decision letter và comments của AE/R1/R2/R3/R4.

---

# 2. Executive summary

C2 revision đã thay đổi C2 từ một experiment tương đối hẹp:

> QSVM-ZZ với `C=1` cố định, so sánh chủ yếu với các SVM baselines trên một số seeds hạn chế

thành một controlled ablation protocol có:

\[
\boxed{
\text{C1 frozen}
\rightarrow
\text{dedicated tuning}
\rightarrow
\text{matched ZZ/Z}
\rightarrow
\text{10 repeated runs}
\rightarrow
\text{strong baselines}
\rightarrow
\text{realistic noisy validation}
}
\]

Các thay đổi quan trọng nhất:

- Freeze operating point từ C1 tại \(n=4\), \(r=2\).
- Tạo tuning set riêng 2,000 mẫu, không overlap với 10 training runs.
- Tăng repeated training runs từ 5 lên 10.
- Tune \(C\) cho quantum branch thay vì giữ `C=1`.
- Ép:
  \[
  C_{ZZ}=C_Z=C_Q^*
  \]
  để controlled ablation thực sự matched.
- Bổ sung Random Forest và XGBoost.
- Classical SVM dùng StandardScaler; quantum branch dùng frozen C1 representation + angle scaling.
- Main statistical comparison dùng paired \(\Delta F1\) và \(\Delta KTA\), 95% CI, Wilcoxon signed-rank và paired effect size.
- Thêm realistic backend-derived noise validation bằng IBM FakeManilaV2 + Qiskit Aer.
- Noise validation bao gồm:
  - ideal statevector;
  - ideal finite-shot;
  - realistic noisy simulator;
  - KTA;
  - relative Frobenius distance;
  - Macro-F1.
- Noise validation không tham gia selection/tuning.
- Có audit về disjointness, frozen hyperparameters, 10 runs, noisy F1 và noise-induced kernel change.

C2 hiện đã giải quyết **phần lớn các criticism trực tiếp về fairness, baseline breadth, statistical base và NISQ realism**.

Tuy nhiên, C2 không thể tự nó giải quyết các vấn đề cấp toàn paper như:

- Theorem 1 / C1 mathematical correctness;
- second dataset UNSW-NB15;
- literature/novelty matrix;
- negative-regime statistics của C3;
- C4 sample-complexity interpretation;
- reference audit;
- supplementary/repository;
- final claim rewriting.

Các vấn đề này phải được xử lý ở C1/C3/C4/manuscript/rebuttal tương ứng.

---

# 3. Vấn đề của C2 trong manuscript trước revision

## 3.1. QSVM dùng `C=1` cố định trong khi classical SVM được tune

Đây là một trong những criticism trực tiếp nhất.

Protocol cũ có:

\[
C_{QSVM}=1
\]

trong khi classical SVM có hyperparameter selection.

Reviewer cho rằng điều này có thể tạo comparison không đối xứng: classical model được tối ưu còn quantum model không.

Reviewer yêu cầu symmetric hyperparameter tuning trên validation data, không dùng test để lựa chọn.

### C2 revision đã thay đổi gì?

Tạo dedicated tuning set:

\[
D_{tune}=2000
\]

và thực hiện 5-fold stratified CV.

Quantum \(C\) được chọn trên grid:

\[
C\in\{0.1,0.3,0.5,1,3,5,10\}
\]

với 1-SE rule.

Kết quả:

| \(C\) | CV Macro-F1 |
|---:|---:|
| 0.1 | 0.8938 |
| 0.3 | 0.9129 |
| 0.5 | 0.9190 |
| 1.0 | 0.9250 |
| **3.0** | **0.9409** |
| 5.0 | 0.9339 |
| 10.0 | 0.9329 |

Frozen quantum hyperparameter:

\[
\boxed{C_Q^*=3.0}
\]

và:

\[
\boxed{C_{ZZ}=C_Z=3.0}
\]

### Mức độ giải quyết

\[
\boxed{\text{RESOLVED}}
\]

C2 hiện đã trực tiếp trả lời criticism về asymmetric \(C\)-tuning.

### Ý nghĩa rebuttal

Có thể phản hồi:

> The original fixed-\(C\) protocol was asymmetric. We therefore introduced a dedicated tuning set and selected the quantum regularization parameter using the same validation-based protocol used for the classical SVM family. The selected quantum value was then shared between the ZZ and Z ablation arms, preventing separate tuning from confounding the entanglement comparison.

---

# 4. Controlled ZZ vs Z ablation

## 4.1. Vấn đề cũ

C2 cũ có thể cho thấy QSVM-ZZ tốt hơn QSVM-Z, nhưng attribution cho entanglement chưa đủ mạnh nếu các model không được kiểm soát chặt về:

- \(C\);
- representation;
- training protocol;
- test data.

## 4.2. Protocol mới

C1 freeze:

\[
n=4
\]

C2 freeze:

\[
r=2.
\]

Hai quantum arms:

\[
ZZFeatureMap
\]

vs.

\[
ZFeatureMap.
\]

Cùng:

- frozen SelectKBest;
- frozen PCA-4;
- cùng train/test protocol;
- cùng \(C_Q^*=3\);
- cùng KTA subset theo từng run.

Đặc biệt:

\[
\boxed{C_{ZZ}=C_Z}
\]

được assert trong notebook.

## 4.3. Kết quả 10 runs

### Macro-F1

\[
\bar F1_{ZZ}=0.846888
\]

\[
\bar F1_Z=0.835528
\]

nên:

\[
\boxed{\Delta F1=+0.011360}
\]

95% CI:

\[
[-0.005408,\;0.028128]
\]

Wilcoxon:

\[
p=0.232422
\]

paired effect size:

\[
d_z=0.484633.
\]

### KTA

\[
\bar KTA_{ZZ}=0.207486
\]

\[
\bar KTA_Z=0.069679
\]

nên:

\[
\boxed{\Delta KTA=+0.137807}
\]

95% CI:

\[
[0.126738,\;0.148876]
\]

Wilcoxon:

\[
p=0.001953
\]

paired effect size:

\[
d_z=8.906227.
\]

### Diễn giải

Kết quả cho thấy một separation rất rõ:

\[
\boxed{
ZZ\text{ cải thiện kernel geometry rất mạnh và ổn định}
}
\]

nhưng:

\[
\boxed{
\text{classification gain dương nhưng chưa có ý nghĩa thống kê ở }n=10
}
\]

Đây là điểm cần giữ nguyên trong manuscript, không nên biến thành claim rằng “entanglement significantly improves F1”.

## 4.4. Mức độ giải quyết

\[
\boxed{\text{RESOLVED}}
\]

về controlled attribution.

---

# 5. Statistical base: từ 5 runs lên 10 runs

## 5.1. Reviewer concern

Reviewer 2 cho rằng 5 seeds là statistical base khá mỏng cho:

- effect size;
- confidence interval;
- repeated-run conclusions.

Roadmap đề xuất tăng core experiments từ 5 → 10 nếu computational budget cho phép.

## 5.2. C2 revision

Đã tạo:

\[
\boxed{10\text{ training runs}}
\]

mỗi:

\[
N=1000
\]

với seeds:

\[
100,\ldots,109.
\]

Training datasets:

- được tạo trước;
- stratified;
- pairwise overlap thấp;
- giữ metadata;
- không overlap tuning set.

Tuning set:

\[
N=2000,\quad seed=200
\]

và:

\[
D_{tune}\cap D_i=\varnothing
\]

cho cả 10 runs.

## 5.3. Statistical analysis

C2 không chỉ báo mean:

- paired \(\Delta F1\);
- paired \(\Delta KTA\);
- 95% CI;
- Wilcoxon;
- paired \(d_z\).

## 5.4. Mức độ giải quyết

\[
\boxed{\text{RESOLVED}}
\]

cho criticism về mỏng statistical base trong C2.

### Lưu ý

Điều này không tự động giải quyết statistical issues ở C3/C4. Các experiment downstream cũng cần được đồng bộ theo revised run protocol khi appropriate.

---

# 6. Dedicated tuning set và separation của Tune / Train / Test

Đây là một thay đổi lớn về experimental rigor.

## Protocol mới

\[
D_{full}
\rightarrow
D_{tune}=2000
+
D_{pool}
\]

\[
D_{pool}
\rightarrow
D_1,\ldots,D_{10}
\]

và fixed test được tách riêng.

Kiểm tra:

\[
D_{tune}\cap D_i=\emptyset
\]

đã PASS cho tất cả 10 runs.

Notebook cũng assert:

- tuning set size = 2000;
- all runs = 1000;
- fixed test set;
- no test used for tuning;
- \(C_{ZZ}=C_Z\).

## Mức độ giải quyết

\[
\boxed{\text{RESOLVED}}
\]

về data separation cho C2.

### Caveat cần ghi rõ

C1 feature-selection/PCA artifacts đã được freeze upstream. Tuning set không overlap với classifier training runs, nhưng không phải là “completely independent” của C1 representation fitting. Vì vậy manuscript nên dùng wording:

> dedicated non-overlapping hyperparameter-tuning subset under the frozen C1 representation

thay vì claim statistical independence tuyệt đối ở mọi tầng.

---

# 7. Strong classical baselines

## 7.1. Vấn đề cũ

Reviewer R1/R2/AE đều chỉ ra rằng benchmark chỉ có các SVM variants chưa đủ để nói về practical competitiveness.

Reviewer đặc biệt yêu cầu:

- XGBoost;
- Random Forest;

và khuyến nghị thêm CatBoost/deep tabular nếu tài nguyên đủ.

## 7.2. C2 revision

Baseline contract hiện tại:

1. QSVM-ZZ
2. QSVM-Z
3. SVM-Linear
4. SVM-Poly2
5. SVM-RBF
6. Random Forest
7. XGBoost

Classical SVM:

\[
SelectKBest/PCA_{C1}
\rightarrow
StandardScaler
\]

Quantum:

\[
SelectKBest/PCA_{C1}
\rightarrow
MinMax[0,\pi]
\rightarrow
ZZ/Z.
\]

RF/XGB được tune trên dedicated tuning set.

## 7.3. Kết quả 10-run mean Macro-F1

| Model | Mean Macro-F1 |
|---|---:|
| XGBoost | **0.849301** |
| QSVM-ZZ | **0.846888** |
| Random Forest | 0.844636 |
| SVM-RBF | 0.836186 |
| QSVM-Z | 0.835528 |
| SVM-Poly2 | 0.832326 |
| SVM-Linear | 0.813655 |

### Interpretation

QSVM-ZZ has a higher 10-run mean Macro-F1 than QSVM-Z and all evaluated SVM baselines, is very close to Random Forest, and is slightly below XGBoost. These are point-estimate comparisons; they should not be read as separate statistical superiority claims for every baseline.

Do đó C2 không còn dựa vào weak SVM-only comparison.

## 7.4. Mức độ giải quyết

\[
\boxed{\text{RESOLVED}}
\]

đối với minimum reviewer requirement.

### Vẫn còn việc ở cấp whole paper

Reviewer khuyến nghị CatBoost và có thể deep tabular baseline. C2 hiện không có hai model đó.

Do đó:

\[
\boxed{\text{PARTIALLY RESOLVED at the maximum breadth level, but minimum requirement resolved}}
\]

Không nên claim rằng C2 đã benchmark “all strong tabular baselines”.

---

# 8. Practical relevance của C2 đã thay đổi

Reviewer 2 đặt câu hỏi rất mạnh:

> real industry competitor is rarely only SVM.

C2 mới cho thấy:

\[
XGBoost=0.8493
\]

là model mạnh nhất, còn:

\[
QSVM-ZZ=0.8469.
\]

Đây là một outcome khoa học hợp lệ.

C2 revision vì thế không cần “ép” QSVM thắng XGBoost.

Thay vào đó, C2 có thể claim:

> QSVM-ZZ remains competitive with strong tabular baselines under the evaluated training budget and clearly separates from the matched non-entangling quantum baseline in kernel geometry.

Đây phù hợp với reviewer roadmap: nếu XGBoost thắng thì đó vẫn là kết quả khoa học hợp lệ.

---

# 9. Realistic hardware-noise validation

## 9.1. Vấn đề cũ

Reviewer R1/R3/AE chỉ ra:

> finite-shot ≠ realistic NISQ noise.

Paper cũ thiếu:

- gate errors;
- decoherence;
- readout errors.

Reviewer yêu cầu tối thiểu:

1. ideal statevector;
2. finite-shot ideal;
3. noisy simulator.

## 9.2. C2 revision

**Updated classifier-level noise test size.** The latest C2 run uses `noise_f1_test_size=300`, matching the main fixed test size (`test_size=300`). The KTA/noise-geometry subset remains `kta_sample_size=200` to keep the noisy kernel computation tractable. This is a deliberate separation between kernel-geometry computational budget and classifier-level evaluation size.

Đã bổ sung backend-derived realistic simulation:

\[
\boxed{\text{IBM FakeManilaV2 + Qiskit Aer}}
\]

environment:

- Qiskit 2.3.0;
- Aer 0.17.2;
- Qiskit IBM Runtime 0.49.0.

Feature maps được transpile theo backend target trước noisy execution. Artifact hiện ghi rõ `optimization_level=1` và `seed_transpiler=42`, nên circuit transpiled có thể reproduce theo cùng backend/optimization/seed.

### ZZ

Transpiled:

- depth = 59;
- 44 CX;
- 36 RZ;
- 8 SX.

### Z

Transpiled:

- depth = 8;
- 24 RZ;
- 8 SX;
- không có CX.

Điều này cung cấp hardware-cost context trực tiếp cho noise sensitivity.

## 9.3. Các condition

### Ideal statevector

ZZ:

\[
KTA=0.196472,\quad F1=0.866453
\]

Z:

\[
KTA=0.073744,\quad F1=0.849798
\]

### Ideal finite-shot, 512 shots

ZZ:

\[
KTA=0.195862,\quad F1=0.879566
\]

Z:

\[
KTA=0.072387,\quad F1=0.853098
\]

### Realistic noisy, 512 shots

ZZ:

\[
KTA=0.149988
\]

\[
D_F=0.599128
\]

\[
F1=0.863149
\]

Z:

\[
KTA=0.071298
\]

\[
D_F=0.165778
\]

\[
F1=0.856397
\]

## 9.4. Scientific interpretation

Noise làm:

\[
ZZ:\quad KTA\ 0.1965\rightarrow0.1500
\]

trong khi:

\[
Z:\quad KTA\ 0.0737\rightarrow0.0713.
\]

Đồng thời:

\[
D_F^{ZZ}=0.5991
\]

lớn hơn nhiều:

\[
D_F^Z=0.1658.
\]

Điều này phù hợp với circuit footprint:

\[
44\ CX\quad\text{(ZZ)}
\]

so với:

\[
0\ CX\quad\text{(Z)}.
\]

Với `noise_f1_test_size=300`, classifier-level F1 được đánh giá trên cùng kích thước test cố định như main C2 protocol. Đây vẫn là **secondary validation trên một representative subset**, không phải 10-run statistical noise study; tuy nhiên test-size lớn hơn giúp giảm sampling variability so với cấu hình 100 mẫu trước đó.

## 9.5. Mức độ giải quyết

\[
\boxed{\text{RESOLVED}}
\]

đối với requirement realistic noisy simulation.

---

# 10. C2 đã thay đổi cách claim “NISQ”

Reviewer phản đối wording kiểu “NISQ-ready”.

C2 revision hiện có evidence phù hợp hơn:

- hardware-constrained \(n=4\);
- actual two-qubit gate footprint;
- backend-derived noise;
- ideal/shot/noisy comparison.

Tuy nhiên vẫn không được claim real-device deployment.

Wording nên là:

> NISQ-aware

hoặc:

> hardware-constrained

và nêu rõ:

> The study uses backend-derived noisy simulation and does not constitute validation on a physical quantum device.

## Mức độ giải quyết

\[
\boxed{\text{RESOLVED with claim calibration}}
\]

nhưng wording này phải được sửa xuyên suốt manuscript, không chỉ trong C2.

---

# 11. C2 đã giải quyết concern về “entropy/geometry contribution” tốt hơn bản cũ

Một trong những điểm quan trọng nhất của C2 mới là nó tách hai câu hỏi:

### Kernel geometry

\[
\Delta KTA=+0.137807
\]

với:

\[
95\%CI=[0.126738,0.148876]
\]

và:

\[
p=0.001953.
\]

### Classification

\[
\Delta F1=+0.011360
\]

nhưng:

\[
95\%CI=[-0.005408,0.028128]
\]

và:

\[
p=0.232422.
\]

Do đó C2 revision không còn ngầm đồng nhất:

> kernel alignment improvement = guaranteed classification improvement.

Đây là một cải thiện khoa học quan trọng.

---

# 12. Reviewer R3: “gain quá nhỏ”

Reviewer R3 đặc biệt phản đối kiểu argument:

> +0.016 F1 là quantum advantage.

C2 mới thực tế còn mạnh hơn về mặt framing vì:

- stationary F1 gain của ZZ so với Z chỉ khoảng 1.14 percentage points;
- không significant ở 10 runs;
- XGBoost vẫn đứng đầu trung bình.

### Điều này nên được xử lý như thế nào?

Không cố bảo vệ:

> “quantum superiority”.

Thay vào đó:

\[
\boxed{
\text{C2 contribution = controlled attribution of entanglement}
}
\]

với:

\[
\boxed{
\text{large, reproducible KTA improvement}
}
\]

và:

\[
\boxed{
\text{modest, statistically inconclusive F1 gain}
}
\]

Đây là framing phù hợp với reviewer R3 yêu cầu chuyển contribution sang regime characterization thay vì aggregate superiority.

## Mức độ giải quyết

\[
\boxed{\text{RESOLVED at C2 level}}
\]

Nhưng final claim rewriting trong manuscript vẫn phải thực hiện.

---

# 13. Reviewer R3: novelty thấp vì ZZFeatureMap là cấu hình phổ biến

C2 không tạo quantum algorithm mới, và điều đó **không phải mục tiêu của revision**.

C2 giúp dịch novelty từ:

> new quantum method

sang:

> controlled evaluation / attribution framework.

Cụ thể C2 hiện có:

- frozen hardware-aware operating point từ C1;
- dedicated tuning;
- matched ZZ/Z ablation;
- 10 repeated runs;
- strong tabular baselines;
- realistic backend-derived noise;
- kernel-level + classifier-level analysis.

Đây là evidence cho novelty ở **evaluation methodology**, không phải algorithmic novelty.

## Mức độ giải quyết

\[
\boxed{\text{PARTIALLY RESOLVED by C2}}
\]

Phần còn lại phải nằm ở:

- Related Work;
- novelty matrix;
- Introduction;
- contribution statement.

---

# 14. Reviewer R2: negative/null results phải được đối xử đối xứng

C2 hiện đã làm tốt hơn bằng cách báo:

\[
\Delta F1
\]

với CI và p-value, thay vì chỉ chọn run thuận lợi.

Kết quả:

> positive point estimate nhưng CI crosses zero.

Đây là ví dụ đúng của:

> positive but inconclusive.

Nó phù hợp với yêu cầu reviewer rằng paper phải sẵn sàng ghi nhận null/inconclusive outcome thay vì ép positive claim.

## Mức độ giải quyết

\[
\boxed{\text{RESOLVED for C2}}
\]

Nhưng C3 negative regimes vẫn phải có treatment đối xứng.

---

# 15. Reviewer R2: statistical base

C2 hiện đã:

- 10 runs;
- paired differences;
- CI;
- Wilcoxon;
- effect size.

Đây là một cải thiện lớn từ 5 runs.

Tuy nhiên:

- không có bootstrap CI;
- không phải mọi experiment downstream đều đã 10 runs.

Do đó:

\[
\boxed{\text{C2 criticism resolved strongly}}
\]

nhưng:

\[
\boxed{\text{whole-paper statistical criticism not yet fully resolved}}
\]

cho đến khi C3/C4 đồng bộ.

---

# 16. Những reviewer issue C2 KHÔNG giải quyết

## 16.1. Theorem 1 / C1 correctness

Không thuộc C2.

Reviewer R4 yêu cầu:

- rederive theorem;
- verify \(V\), \(F_e\), \(Q\);
- independently verify Pareto dominance;
- hoặc bỏ theorem.

Đây phải xử lý bằng C1 audit.

Reviewer còn chỉ ra một inconsistency kiểu:

\[
\tilde F(4) > \tilde F(3)
\]

trong khi table có:

\[
0.471 < 0.628.
\]

C2 không có tác động tới issue này.

---

## 16.2. Second dataset UNSW-NB15

Reviewer R1/AE yêu cầu additional modern dataset.

C2 hiện **chỉ dùng NSL-KDD**.

Cần notebook/pipeline riêng cho UNSW-NB15.

---

## 16.3. Negative regimes của C3

C2 chưa giải quyết:

- perturbation;
- temporal shift;
- symmetric effect size/CI;
- McNemar nếu appropriate.

C3 phải tiếp tục.

---

## 16.4. Sample-complexity crossover

C2 chỉ dùng fixed training size:

\[
N=1000.
\]

Không giải quyết concern:

> QSVM có thật sự là “low-data advantage” hay nó vẫn tốt ở N lớn?

Đây là C4.

---

## 16.5. Rare-attack N=500 discrepancy

C2 không giải quyết claim cũ:

- +6.7 points;
- \(d=0.68\).

Reviewer yêu cầu trace lại C6 protocol và định nghĩa rare subset.

Đây là C4/C6 issue.

---

## 16.6. Literature / novelty matrix

C2 bổ sung evidence, nhưng không thay thế:

- 2025–2026 literature update;
- comparison với recent noisy IDS benchmark;
- structured novelty matrix.

---

## 16.7. Reference audit

Phải xử lý:

- Ref [15];
- Ref [26];
- ≤45 references.

Không phải C2.

---

## 16.8. Supplementary / repository

C2 đã tạo artifacts reproducible, nhưng whole paper vẫn cần:

- public/reviewer-accessible repository;
- supplementary;
- environment;
- reproduction instructions.

---

# 17. Mapping trực tiếp reviewer → C2 revision

| Reviewer concern | C2 action | Evidence | Status |
|---|---|---|---|
| QSVM `C=1` fixed, unfair vs classical | Dedicated tuning set + CV | \(C_Q^*=3\) | ✅ Resolved |
| ZZ/Z ablation not fully matched | Shared frozen \(C_Q^*\) | \(C_{ZZ}=C_Z\) | ✅ Resolved |
| Only 5 seeds | 10 runs | seeds 100–109 | ✅ Resolved |
| Weak SVM-only baselines | RF + XGB added | 7 model families | ✅ Resolved |
| No realistic hardware noise | FakeManilaV2/Aer noisy validation | noisy KTA/F1/D_F | ✅ Resolved |
| Finite-shot only | Ideal + shot + realistic noisy | 3 conditions | ✅ Resolved |
| Entanglement attribution unclear | Paired \(\Delta KTA,\Delta F1\) | 10-run statistics | ✅ Resolved |
| Strong practical competitor missing | XGB/RF | XGB mean F1 highest | ✅ Resolved at minimum level |
| Gain may be small | Report modest/non-significant F1 gain honestly | \(\Delta F1=0.01136,p=0.232\) | ✅ Resolved by claim calibration |
| Null/negative outcome under C2 ignored | CI + Wilcoxon + effect size | F1 CI crosses zero | ✅ Resolved |
| NISQ-ready claim too strong | Hardware-derived noisy simulation + narrower wording | FakeManila validation | ✅ Resolved with manuscript rewrite |
| Theorem 1 wrong | — | Outside C2 | ⏳ C1 |
| Second dataset missing | — | Outside C2 | ⏳ UNSW |
| Negative regimes insufficiently statistical | — | Outside C2 | ⏳ C3 |
| Low-data crossover unresolved | — | Outside C2 | ⏳ C4 |
| Rare N=500 mismatch | — | Outside C2 | ⏳ C4 |
| Literature/novelty matrix | — | Outside C2 | ⏳ Related Work |
| Reference errors | — | Outside C2 | ⏳ Reference audit |
| Supplementary inaccessible | — | Outside C2 | ⏳ Submission |
| Repository missing | — | Outside C2 | ⏳ Reproducibility |

---

# 18. C2 trước vs C2 revision

## C2 cũ

\[
\boxed{
\text{QSVM-ZZ, C=1}
\rightarrow
\text{limited seeds}
\rightarrow
\text{SVM-heavy baseline}
\rightarrow
\text{ideal simulation}
}
\]

Các reviewer có thể đặt câu hỏi:

- quantum có thật sự được tune công bằng?
- có vượt strong tabular baselines không?
- result có phụ thuộc seed không?
- ZZ có thực sự là nguyên nhân?
- noise thực tế ảnh hưởng thế nào?

## C2 revision

\[
\boxed{
\text{C1 freeze}
\rightarrow
D_{tune}
\rightarrow
C^*
\rightarrow
ZZ/Z
\rightarrow
10 runs
\rightarrow
RF/XGB
\rightarrow
realistic noise
}
\]

Mỗi stage trả lời một objection cụ thể.

---

# 19. Scientific story mới của C2

C2 revision không nên được viết theo story:

> “ZZ gives higher F1.”

Điểm này chỉ nên được dùng như một mô tả point estimate; kết luận inferential chính là classification gain dương nhưng chưa có ý nghĩa thống kê.

Story mạnh hơn là:

### Step 1 — Fair configuration

C1 đã freeze:

\[
n=4.
\]

Dedicated tuning xác định:

\[
C_Q=3.
\]

### Step 2 — Isolate entanglement

Matched:

\[
ZZ\leftrightarrow Z.
\]

### Step 3 — Geometry

\[
\Delta KTA=+0.1378
\]

với:

\[
p=0.001953.
\]

→ rất mạnh và reproducible.

### Step 4 — Classification

\[
\Delta F1=+0.0114
\]

nhưng:

\[
p=0.232.
\]

→ positive point estimate nhưng statistically inconclusive.

### Step 5 — Practical benchmark

\[
XGB > ZZ > RF
\]

về 10-run mean Macro-F1, với XGBoost đứng đầu, QSVM-ZZ ở vị trí thứ hai và Random Forest rất gần phía sau. Đây là ranking theo point estimate; nó không tự hàm ý mọi cặp đều có superiority có ý nghĩa thống kê.

→ QSVM-ZZ là competitive, không phải universally superior.

### Step 6 — Hardware realism

ZZ có:

\[
44 CX,\ depth=59
\]

và noise làm:

\[
KTA:0.1965\rightarrow0.1500.
\]

→ entanglement benefit có hardware sensitivity.

Đây là một câu chuyện scientific **thực tế hơn và mạnh hơn** so với “QSVM thắng classical”.

---

# 20. Recommended manuscript wording sau C2

## Không nên

> “The ZZ entanglement significantly improves classification performance.”

## Nên

> “The matched ZZ ablation produced a large and statistically significant improvement in kernel-target alignment, while the corresponding Macro-F1 improvement was positive but not statistically significant across ten repeated training subsets.”

## Không nên

> “QSVM-ZZ achieves quantum advantage over classical models.”

## Nên

> “QSVM-ZZ remained competitive with the evaluated classical baselines, although XGBoost achieved the highest mean Macro-F1 in the revised benchmark.”

## Không nên

> “The method is NISQ-ready.”

## Nên

> “The selected configuration was further evaluated under a backend-derived noisy simulator, providing a hardware-constrained robustness check rather than physical-device validation.”

---

# 21. Trạng thái C2 cuối cùng

### Scientific protocol

\[
\boxed{\text{PASS}}
\]

### Hyperparameter fairness

\[
\boxed{\text{PASS}}
\]

### Controlled entanglement attribution

\[
\boxed{\text{PASS}}
\]

### Statistical base

\[
\boxed{\text{PASS — 10 runs}}
\]

### Strong baseline breadth

\[
\boxed{\text{PASS — minimum requested}}
\]

### Realistic NISQ validation

\[
\boxed{\text{PASS}}
\]

### Negative/null honesty

\[
\boxed{\text{PASS}}
\]

### Whole-paper revision

\[
\boxed{\text{NOT COMPLETE}}
\]

vì các issue C1/C3/C4/UNSW/literature/reproducibility vẫn còn.

---

# 22. Kết luận

C2 revision đã chuyển C2 từ một experiment dễ bị reviewer chỉ trích về **asymmetric tuning, weak baselines, limited statistical base và ideal-only simulation** thành một **controlled, reproducible, hardware-aware ablation**.

Điểm mạnh nhất của kết quả mới là:

\[
\boxed{
\Delta KTA=+0.1378,\quad
95\%CI=[0.1267,0.1489],\quad
p=0.00195
}
\]

cho thấy contribution của ZZ ở **kernel geometry** rất mạnh và nhất quán.

Trong khi:

\[
\boxed{
\Delta F1=+0.0114,\quad
95\%CI=[-0.0054,0.0281],\quad
p=0.232
}
\]

cho thấy classification gain **không nên bị overclaim**.

Còn realistic noise cho thấy:

\[
\boxed{
D_F^{ZZ}\approx0.5991
\gg
D_F^{Z}\approx0.1658
}
\]

phù hợp với footprint:

\[
44\ CX\text{ vs }0\ CX.
\]

Vì vậy C2 mới không còn cố “chứng minh quantum advantage”, mà cung cấp một attribution story rõ hơn:

> **ZZ entanglement materially changes and improves the kernel geometry under the matched protocol; the downstream classification benefit is positive but not statistically conclusive in the stationary 10-run benchmark, while the entangling circuit is substantially more sensitive to the evaluated backend-derived noise.**

Đó là cách framing phù hợp nhất với criticism của R1/R2/R3/R4 ở cấp C2.



---

# 23. Hướng sửa manuscript — các nội dung liên quan trực tiếp đến C2

Phần này chuyển các thay đổi thực nghiệm của `C2_revision` thành các chỉnh sửa cụ thể trong manuscript. Mục tiêu là không chỉ thêm số liệu, mà phải viết lại C2 như một controlled ablation study và làm rõ objection → experimental control → evidence → conclusion.

## 23.1. Viết lại mục tiêu của C2

C2 không nên được giới thiệu như “QSVM-ZZ outperforms QSVM-Z and classical SVMs”.

Câu hỏi chính nên là:

> **Does the ZZ entangling layer provide incremental value over a matched non-entangling quantum feature map at the hardware-constrained operating point selected in C1?**

C2 có hai mục tiêu:

1. Primary: isolate the incremental contribution of ZZ entanglement.
2. Secondary: assess whether the selected configurations remain behaviorally stable under realistic backend-derived execution noise.

Điều này nối trực tiếp C1 và C2:

- C1: Which operating point?
- C2: What does entanglement contribute at that point?

## 23.2. Viết lại Experimental Setup

Nên mô tả rõ:

### Frozen representation

C2 dùng frozen C1 representation:

\[
	ext{SelectKBest}_{C1}
ightarrow PCA(n=4)
\]

và không re-select \(n\) trong C2.

### Dedicated tuning

\[
|D_{tune}|=2000
\]

5-fold stratified CV, với:

\[
C\in\{0.1,0.3,0.5,1,3,5,10\}.
\]

1-SE rule chọn:

\[
C_Q^*=3.
\]

Sau đó:

\[
C_{ZZ}=C_Z=3.
\]

### Repeated evaluation

\[
10	ext{ training subsets},\quad N=1000/run
\]

với seeds 100–109.

### Statistics

Nêu rõ trước khi trình bày kết quả:

- paired \(\Delta F1\);
- paired \(\Delta KTA\);
- 95% CI;
- Wilcoxon signed-rank;
- paired standardized effect size.

## 23.3. Đoạn manuscript nên thêm về tuning set

Có thể dùng gần nguyên văn:

> “To avoid asymmetric hyperparameter optimization, classifier hyperparameters were selected on a dedicated stratified tuning subset of 2,000 training instances. This subset was constructed before the ten repeated training subsets and was enforced to be row-disjoint from every evaluation training run. The C1 representation remained frozen during C2.”

Không nên gọi tuning set là “completely independent” của toàn bộ C1 pipeline, vì C1 representation đã được freeze upstream.

# 24. Viết lại định nghĩa controlled ZZ-versus-Z ablation

Nên có một statement rõ:

> “The primary C2 comparison is a controlled ZZ-versus-Z ablation. Both feature maps use the same frozen C1 representation, circuit width \(n=4\), repetition depth \(r=2\), training subsets, evaluation set, and quantum SVM regularization \(C=3\). Hence, the principal difference between the two arms is the presence of the ZZ entangling layer.”

Đây là câu trực tiếp trả lời attribution criticism.

# 25. Results — Hyperparameter tuning

Có thể trình bày condensed table:

| C | CV Macro-F1 |
|---:|---:|
| 0.1 | 0.8938 |
| 0.3 | 0.9129 |
| 0.5 | 0.9190 |
| 1.0 | 0.9250 |
| **3.0** | **0.9409** |
| 5.0 | 0.9339 |
| 10.0 | 0.9329 |

Sau table:

> “The dedicated tuning protocol selected \(C=3\) for the quantum SVM family. This value was then held fixed for both the ZZ and Z ablation arms.”

Full CV curves có thể đưa vào supplementary.

# 26. Results — Main entanglement ablation

Đây phải là subsection quan trọng nhất của C2.

### Main table

| Model | Macro-F1 | KTA |
|---|---:|---:|
| QSVM-ZZ | 0.8469 | 0.2075 |
| QSVM-Z | 0.8355 | 0.0697 |

### Paired-effect table

| Effect | Estimate | 95% CI | Wilcoxon p | \(d_z\) |
|---|---:|---:|---:|---:|
| ZZ − Z, Macro-F1 | +0.0114 | [−0.0054, 0.0281] | 0.232 | 0.485 |
| ZZ − Z, KTA | +0.1378 | [0.1267, 0.1489] | 0.00195 | 8.91 |

Narrative nên tách hai tầng:

> “Across ten repeated training subsets, the ZZ feature map produced a substantially higher KTA than the matched Z map. The paired mean difference was +0.1378 (95% CI [0.1267, 0.1489], Wilcoxon \(p=0.00195\)), indicating a large and consistent improvement in kernel-target alignment.”

và:

> “The corresponding Macro-F1 difference was positive (+0.0114), but its 95% CI included zero and the paired Wilcoxon test was not significant (\(p=0.232\)). Thus, the experiment supports a strong contribution of entanglement to kernel geometry, but does not establish a statistically significant classification improvement under the stationary ten-run protocol.”

Không nên viết rằng “entanglement significantly improves F1”.

# 27. Figure C2 chính

Nên có paired plot theo 10 runs cho:

\[
F1_{ZZ,i}\leftrightarrow F1_{Z,i}
\]

và một figure tương tự cho KTA.

Không nên chỉ dùng bar chart mean ± CI vì paired variability là một phần quan trọng của evidence.

# 28. Results — Strong classical baselines

Nên viết:

> “To contextualize the entanglement ablation against stronger non-SVM alternatives, we additionally evaluated Random Forest and XGBoost under the same dedicated tuning protocol.”

Bảng mean Macro-F1:

| Model | Mean Macro-F1 |
|---|---:|
| XGBoost | 0.8493 |
| QSVM-ZZ | 0.8469 |
| Random Forest | 0.8446 |
| SVM-RBF | 0.8362 |
| QSVM-Z | 0.8355 |
| SVM-Poly2 | 0.8323 |
| SVM-Linear | 0.8137 |

Narrative:

> “QSVM-ZZ remained competitive with the evaluated classical baselines, although XGBoost achieved the highest mean Macro-F1 in the revised benchmark.”

Có thể thêm:

> “The revised benchmark therefore rules out the interpretation that the observed quantum result is solely a consequence of comparison against weak SVM-only baselines.”

Không nói “QSVM-ZZ beats classical ML”.

# 29. Results — Hardware-noise validation

Nên có một subsection compact:

> **Hardware-noise sensitivity of the selected quantum kernels**

### Conditions

1. ideal statevector;
2. ideal finite-shot, 512 shots;
3. realistic backend-derived noisy simulator.

### Metrics

- KTA;
- relative Frobenius distance;
- Macro-F1.

### Hardware evidence

| Feature map | Depth | CX count |
|---|---:|---:|
| ZZ | 59 | 44 |
| Z | 8 | 0 |

### Noise table

| Condition | Model | KTA | \(D_F\) | Macro-F1 |
|---|---|---:|---:|---:|
| Ideal | ZZ | 0.1965 | — | 0.8665 |
| Ideal | Z | 0.0737 | — | 0.8498 |
| Finite-shot | ZZ | 0.1959 | 0.1126 | 0.8796 |
| Finite-shot | Z | 0.0724 | 0.0306 | 0.8531 |
| Realistic noisy | ZZ | 0.1500 | 0.5991 | 0.8631 |
| Realistic noisy | Z | 0.0713 | 0.1658 | 0.8564 |

Narrative:

> “Under the evaluated FakeManilaV2-derived noise model, the entangling ZZ circuit exhibited substantially larger kernel distortion than the non-entangling Z circuit, consistent with its larger transpiled two-qubit-gate footprint. Despite this geometry-level degradation, classifier-level Macro-F1 remained comparatively stable on the fixed representative validation subset.”

Sau đó nói rõ:

> “This experiment is a hardware-constrained simulation study rather than a physical-device validation.”

# 30. Contribution statement của C2

Nên đổi thành:

> **A controlled entanglement ablation that quantifies the incremental contribution of ZZ entanglement under matched preprocessing, regularization, training subsets, and evaluation conditions.**

Không nên định nghĩa contribution là “a quantum SVM that achieves improved classification through entanglement”.

# 31. Abstract

Không viết:

> “ZZ significantly improves classification performance.”

Có thể viết:

> “A controlled ten-run ablation shows a large and statistically significant improvement in kernel-target alignment from ZZ entanglement, while the corresponding classification gain remains modest and statistically inconclusive.”

Nếu abstract cần ngắn hơn:

> “Entanglement substantially improves kernel alignment, while classification gains are modest and regime-dependent.”

# 32. Introduction

Nên chuyển motivation của C2 từ aggregate performance sang attribution:

> “A central unresolved question is whether the observed behavior of small quantum kernels is attributable to entanglement itself or to confounded preprocessing, hyperparameter, and evaluation choices.”

Sau đó:

> “We address this with a controlled ZZ-versus-Z ablation at a hardware-constrained operating point, using dedicated hyperparameter tuning, repeated training subsets, strong tabular baselines, and backend-derived noisy simulation.”

# 33. Discussion — giải thích KTA và F1

Nên thêm:

> “The dissociation between kernel alignment and classification improvement is informative. The strong positive KTA shift indicates that entanglement changes the kernel geometry in a direction more aligned with the labels, but this geometric change does not guarantee a statistically significant improvement in downstream Macro-F1 on the evaluated stationary test protocol.”

Và:

> “Kernel geometry and predictive performance should therefore be reported jointly rather than treating KTA as a standalone proxy for accuracy.”

# 34. Discussion — classical baseline

Nên viết:

> “The revised benchmark also shows that QSVM-ZZ is not universally superior to classical tabular learning. XGBoost achieves the highest mean Macro-F1, while QSVM-ZZ remains competitive and clearly separates from the matched non-entangling quantum baseline in kernel alignment.”

# 35. Discussion — hardware noise

Nên viết:

> “The backend-derived noise study reveals an important hardware trade-off: the entangling ZZ circuit incurs substantially greater kernel distortion than the non-entangling Z circuit, consistent with its larger two-qubit-gate footprint. The result supports the use of hardware-aware configuration selection, while also cautioning against interpreting an ideal-simulator entanglement gain as device-independent.”

Điều này tạo liên kết tự nhiên:

\[
C1:	ext{hardware cost}

ightarrow
C2:	ext{hardware sensitivity of entanglement}.
\]

# 36. Conclusion

Không nên kết:

> “ZZ entanglement improves IDS accuracy.”

Nên:

> “The revised controlled ablation provides strong evidence that ZZ entanglement materially changes kernel geometry under the selected hardware-constrained operating point. The corresponding stationary classification improvement is positive but not statistically conclusive, reinforcing the need to distinguish kernel-level effects from downstream predictive gains.”

Và:

> “The backend-derived noisy simulation further shows that the entangling circuit is substantially more sensitive to realistic execution noise.”

# 37. Supplementary

Để tránh page count phình:

### Main paper

- condensed C tuning result;
- main ZZ vs Z table;
- paired statistical table;
- baseline comparison;
- compact noise table;
- main figures.

### Supplementary

- full CV curve;
- all 10 per-run results;
- pairwise deltas;
- full KTA/Gram diagnostics;
- transpilation metadata;
- backend/noise configuration;
- full noise output;
- config/seed metadata.

# 38. Rebuttal mapping riêng cho C2

### R1/R4 — asymmetric tuning

> We agree. We added a dedicated 2,000-instance tuning subset and selected \(C_Q=3\) by 5-fold CV. The value is shared between ZZ and Z.

### R1/R2 — weak baseline

> We added Random Forest and XGBoost. XGBoost achieved the highest mean Macro-F1, while QSVM-ZZ remained competitive.

### R2 — five seeds

> We increased the repeated training subsets from five to ten and use paired confidence intervals and Wilcoxon tests.

### R1/R3/AE — realistic noise

> We added backend-derived noisy simulation using FakeManilaV2 and Qiskit Aer, comparing ideal, finite-shot, and realistic-noisy execution.

### R3 — modest gain

> We agree that the stationary classification gain is modest. We therefore no longer characterize C2 as evidence of universal quantum superiority; instead, we emphasize the large and statistically significant kernel-geometry contribution of entanglement and report the classification result as positive but inconclusive.

# 39. Claim replacement table

| Claim không nên dùng | Claim mới |
|---|---|
| “ZZ significantly improves classification” | “ZZ significantly improves kernel-target alignment; the classification gain is positive but statistically inconclusive.” |
| “QSVM-ZZ outperforms classical ML” | “QSVM-ZZ remains competitive with the evaluated classical baselines.” |
| “Quantum advantage is demonstrated” | “An empirical regime-specific advantage is observed under the evaluated protocol.” |
| “NISQ-ready” | “NISQ-aware / hardware-constrained.” |
| “Entanglement is beneficial” | “Entanglement materially improves kernel geometry under the matched operating point.” |
| “Noise does not affect the model” | “The noisy simulation shows substantial kernel distortion, especially for the deeper entangling circuit, while classifier-level degradation remains modest on the representative subset.” |

# 40. C2 manuscript architecture đề xuất

## III. Methodology

- Frozen C1 representation
- Controlled entanglement ablation
- Hyperparameter protocol
- Hardware-noise validation

## IV. Experimental Setup

- datasets
- baselines
- ten-run protocol
- tuning
- statistics

## V. Results

- C1 operating point
- C2 entanglement ablation
- strong baseline comparison
- hardware-noise validation

C3/C4 tiếp tục sau đó.

# 41. Final C2 manuscript narrative

Toàn bộ C2 nên đi theo flow:

\[
	ext{Fair tuning}

ightarrow
	ext{Matched ZZ vs Z}

ightarrow
\Delta KTA	ext{ large + significant}

ightarrow
\Delta F1	ext{ positive but inconclusive}

ightarrow
	ext{XGB strongest overall baseline}

ightarrow
	ext{ZZ more noise-sensitive due to larger 2Q footprint}.
\]

Đây là story cần giữ nhất quán giữa Results, Discussion, Conclusion và rebuttal.

# 42. C2 manuscript status

| Thành phần | Trạng thái |
|---|---|
| Experimental design | ✅ Complete |
| C tuning fairness | ✅ Complete |
| ZZ/Z attribution | ✅ Complete |
| 10-run statistics | ✅ Complete |
| RF/XGB baselines | ✅ Complete |
| Realistic noise | ✅ Complete |
| C2 interpretation | ✅ Complete |
| Main-paper tables | 🟡 Draft from frozen artifacts |
| Figures | 🟡 Need final manuscript styling |
| Results prose | 🟡 Need rewrite |
| Discussion prose | 🟡 Need rewrite |
| Conclusion wording | 🟡 Need rewrite |
| Rebuttal response | 🟡 Need draft |
| Literature/novelty matrix | ⏳ Whole-paper task |

## Kết luận

C2 revision hiện không chỉ là một notebook mới; nó cần được phản ánh trong manuscript như một **controlled entanglement attribution study**. Các con số chính phải được giữ đúng tinh thần:

\[
\Delta KTA=+0.1378,\quad p=0.00195
\]

nhưng:

\[
\Delta F1=+0.0114,\quad p=0.232.
\]

Do đó manuscript nên claim mạnh về **kernel-geometry contribution**, thận trọng về **classification gain**, và trung thực rằng **XGBoost vẫn là baseline mạnh nhất** trong benchmark revised. Phần realistic noise được trình bày như **hardware-constrained validation**, không phải physical-device validation.
