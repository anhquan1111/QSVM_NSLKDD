# PROJECT CONTEXT: QSVM-IDS NISQ Research
> File này dùng để cung cấp context cho AI khi làm việc với dự án nghiên cứu QSVM.
> Cập nhật lần cuối: 2025 (sync với Khung_Nghien_Cuu_QSVM_IDS_NISQ_Final_v4.docx + kết quả C4 thực tế)

---

## 1. TỔNG QUAN DỰ ÁN

**Tên đề tài:** Khung Quantum Support Vector Machine (QSVM) có xét đến ràng buộc phần cứng lượng tử trong kỷ nguyên NISQ (Noisy Intermediate-Scale Quantum) cho bài toán Phát hiện Xâm nhập Mạng (IDS).

**Hướng tiếp cận cốt lõi:** Không đơn thuần so sánh thực nghiệm QSVM vs SVM. Tập trung vào chiều sâu khoa học với **6 đóng góp nguyên gốc** có thể kiểm chứng độc lập.

**Bài toán:** Phân lớp nhị phân (Normal vs Attack) trên dữ liệu lưu lượng mạng NSL-KDD.

**Bốn hạn chế hiện tại của các nghiên cứu QSVM-IDS mà đề tài giải quyết:**
1. Lựa chọn chiều nhúng lượng tử theo ngưỡng phương sai cố định, không xét chi phí qubit thực tế.
2. Chưa giải thích cơ chế nào của kernel lượng tử tạo ra lợi thế phân lớp.
3. Chưa phân tích cấu trúc hình học của kernel và biên quyết định trong không gian đặc trưng.
4. Đánh giá thiếu tính thực tiễn — bỏ qua distribution shift và calibration của confidence score, dẫn đến overclaim về khả năng triển khai thực tế.

---

## 2. TẬP DỮ LIỆU

**Dataset chính:** NSL-KDD (phiên bản cải tiến của KDD Cup 1999)
- Train: 125.973 mẫu
- Test: 22.544 mẫu
- 41 đặc trưng gốc + 3 categorical (protocol_type, service, flag)
- Sau One-Hot Encoding: 122 đặc trưng
- 4 nhóm tấn công: DoS, Probe, R2L, U2R + lớp Normal
- Đặc thù: **phân phối lớp cực kỳ mất cân bằng** — U2R và R2L chiếm dưới 1% tổng mẫu

**Ràng buộc phần cứng:**
- Chỉ dùng **4 qubit** (NISQ constraint)
- Bắt buộc giảm từ 122 → 4 chiều trước khi đưa vào QSVM
- CNOT gate (2-qubit) error rate ~0.5–1% trên IBM Quantum, cao gấp 5–10× so với 1-qubit gate (~0.1%)

---

## 3. KIẾN TRÚC QUANTUM MODEL

**Quantum Kernel:** K(x,z) = |⟨φ(x)|φ(z)⟩|²

**Feature Map:** ZZFeatureMap trong Qiskit
- Mã hóa tương tác cặp đặc trưng phi tuyến qua cổng pha ZZ
- U(x) = [H⊗P(2xᵢ)⊗ZZ-entangle]^reps
- Không gian Hilbert: 2⁴ = 16 chiều

**Config baseline:**
- ZZFeatureMap | reps=2 | entanglement=full | shots=1024 | C=1.0

**Scaling convention:** MinMaxScaler([0, π]) — rotation angle cho RY gate: |ψ⟩ = RY(xᵢ)|0⟩. Scale đến π để khai thác toàn bộ Bloch hemisphere, tránh wrap-around.

---

## 4. PIPELINE TIỀN XỬ LÝ

```
NSL-KDD raw (41 features)
  → One-Hot Encoding zero-leakage (122 features)
  → SelectKBest f_classif, K=25 (kết quả elbow criterion)  ← [đang dùng K=20 trong code hiện tại]
  → PCA Pareto n=4 (hardware-aware multi-objective)
  → MinMaxScaler([0, π])
  → QSVM (ZZFeatureMap, 4-qubit)
```

**Zero-leakage contract:** Mọi transformer (SelectKBest, PCA, MinMaxScaler) chỉ được `.fit()` trên tập train, `.transform()` độc lập trên tập test.

**Files đã implement:**
- `data_preprocessing.py` — pipeline đầy đủ, lưu artifacts ra `models/`
- `preprocess.ipynb` — notebook tiền xử lý
- `selectkbest_nslkdd__2_.ipynb` — SelectKBest tuning
- `pca.ipynb` — PCA đa mục tiêu Pareto

**Artifacts được lưu (joblib):**
- `models/feature_selector_k20.joblib`
- `models/pca_4components.joblib`
- `models/scaler_minmax_pi.joblib`

**Dữ liệu trung gian:**
- `data/processed/NSL_KDD_Train_Cleaned.csv`
- `data/processed/NSL_KDD_Test_Cleaned.csv`
- `data/processed/NSL_KDD_Train_Selected.csv`
- `data/processed/NSL_KDD_Train_Sample{n}.csv` (subsets cho C6)

**Label columns:** `label_binary`, `attack_category`, `label_multiclass`

---

## 5. SÁU ĐÓNG GÓP KHOA HỌC (CONTRIBUTIONS)

Tóm tắt narrative xuyên suốt: **C1 tối ưu nhúng → C2 giải thích lý thuyết kernel → C3 visualize và định lượng cấu trúc kernel → C4 đánh giá robustness thực tế → C5 calibration & rare attack → C6 learning curve**

---

### C1 — Pipeline giảm chiều hai giai đoạn (ĐÃ HOÀN THÀNH phần lớn)

**Tóm tắt:** Lần đầu tích hợp lọc đặc trưng thống kê (SelectKBest) và tối ưu Pareto có xét đến chi phí qubit vào một framework thống nhất.

**Bước 1 — SelectKBest (f_classif):**
- Lý do dùng f_classif thay vì Mutual Information: phù hợp hơn về mặt thống kê cho continuous float sau MinMaxScaler, nhanh hơn ~10× trên 125.973 mẫu.
- MI vẫn tính song song để phân tích rare attacks (U2R, R2L) vì binary MI có thể đánh giá thấp các đặc trưng quan trọng cho rare class.
- Tham số K tối ưu bằng 5-fold cross-validation trên 5.000 mẫu stratified theo attack_category.
- Proxy classifier: SVM linear (nhanh hơn QSVM ~1.000 lần).
- Elbow criterion (plateau threshold = 0.007): chọn K nhỏ nhất mà F1-macro chỉ kém tối đa 0.007 so với max.
- **Kết quả thực nghiệm:**
  - K = 4–15: F1-macro tăng chậm (0.860 → 0.899)
  - K = 15 → 20: nhảy vọt +0.054 F1 (serror_rate và flag bổ sung cho nhau)
  - K ≥ 20: diminishing returns (chỉ +0.006 khi thêm 80 đặc trưng)
  - **K_FINAL = 25** (giảm 122 → 25 features, 79.5% reduction). *(Lưu ý: code hiện tại đang dùng K=20; K=25 là kết quả phân tích C1 đầy đủ)*

**Bước 2 — PCA đa mục tiêu Pareto:**
- Hàm mục tiêu: F(n) = α·V(n) + β·S_norm(n) − γ·Q(n)
  - V(n): tỷ lệ phương sai giữ lại (ràng buộc cứng ≥ 80%)
  - S_norm(n): Fisher Score chuẩn hóa (độ phân tách lớp của các PC)
  - Q(n): chi phí phần cứng = (n·reps + 5·n(n−1)/2·reps) / Q_max (penalty ×5 cho 2-qubit gate, phản ánh CNOT error rate trên NISQ)
- Grid search trên Dirichlet simplex α+β+γ=1 (~435 điểm, resolution=30).
- Dùng Davies-Bouldin Index (DBI) thay vì Silhouette trong vòng lặp: DBI O(k·n) vs Silhouette O(n²), nhanh hơn ~100×. Silhouette chỉ tính 1 lần để validate n tối ưu; Pearson correlation DBI–Silhouette trên tập candidates được báo cáo để xác nhận DBI là proxy đáng tin cậy.
- **Kết quả:** n=4 được chọn: F(n)=0.1420, variance=86.62%, Fisher S=0.4711, DBI=1.0846, Q(n)=0.1517.
- Bootstrap 95% CI (200 iterations × 5.000 samples) xác nhận tính ổn định.
- n=4 nằm trong Pareto-optimal frontier trên 3 mục tiêu (không có n nào vừa có variance cao hơn, Fisher Score cao hơn, và hardware cost thấp hơn cùng lúc).

**Ablation study (5 cấu hình trên proxy SVM linear):**
- C1: SelectKBest K=25 + PCA 4D → F1 = 0.8989 (**best**)
- PCA 4D trực tiếp → F1 = 0.8577 (kém hơn 0.0411, −4.8% relative)

**Điểm mới so với các nghiên cứu trước:**
1. Lần đầu tích hợp lọc thống kê + tối ưu Pareto qubit cost trong một framework thống nhất có thể kiểm chứng độc lập.
2. K và n đều xác định bằng dữ liệu, không dùng ngưỡng cố định → tổng quát hóa tốt hơn khi áp dụng trên dataset khác (UNSW-NB15, CIC-IDS).
3. Ablation study 5-cấu hình cung cấp bằng chứng định lượng rõ ràng rằng SelectKBest trước PCA cải thiện chất lượng quantum feature encoding.

**Kết quả phân tích tương quan PC:** Pearson correlation giữa các cặp PC = 0 (expected, PCA orthogonal), nhưng Spearman phi tuyến vẫn tồn tại: PC1–PC3 (r = +0.40), PC2–PC3 (r = −0.44) → tiền đề trực tiếp cho C2.

---

### C2 — Phân tích khả năng biểu diễn của Quantum Kernel (ĐÃ CÓ KHUNG LÝ THUYẾT)

**Câu hỏi nghiên cứu:** Tại sao ZZFeatureMap vượt trội trên dữ liệu IDS?

**Lập luận lý thuyết:**
- Dữ liệu IDS có tương quan cặp đặc trưng cao (evidenced bởi Spearman correlation giữa PC sau PCA — phát hiện ở C1).
- ZZFeatureMap mã hóa tương tác 2xᵢxⱼ vào pha lượng tử thông qua entanglement gate ZZ.
- Kernel lượng tử tương đương polynomial kernel bậc 2 nhưng được ánh xạ vào không gian Hilbert kích thước tăng theo hàm mũ.
- Linear SVM bỏ sót phần phi tuyến mà ZZFeatureMap khai thác được thông qua entanglement.

**Ý nghĩa:** Nâng paper từ mức benchmark lên mức phân tích bản chất; liên hệ cấu trúc dữ liệu với thiết kế kernel lượng tử.

---

### C3 — Phân tích Kernel Geometry và Decision Boundary

**Câu hỏi nghiên cứu:** Cấu trúc hình học của kernel lượng tử có thực sự tạo ra sự phân tách khác biệt trên dữ liệu IDS so với classical kernel không, và vai trò thực sự của entanglement là gì?

**Vị trí trong narrative:** Đóng góp này là bước nối tiếp tự nhiên từ C2. Nếu C2 giải thích lý thuyết tại sao ZZFeatureMap có lợi thế biểu diễn, thì C3 visualize và định lượng trực tiếp cấu trúc hình học của kernel lượng tử trong không gian đặc trưng, cung cấp bằng chứng thực nghiệm cụ thể cho luận điểm đó.

**Sáu phân tích chính:**

* **Kernel matrix heatmap:** Visualize ma trận K(x,z) dưới dạng heatmap trên tập subsample stratified (≤ KM_SAMPLE_SIZE mẫu, cân bằng theo class). Các mẫu được sắp xếp theo nhãn class để so sánh block structure giữa năm kernel: ZZFeatureMap, ZFeatureMap, SVM-Linear, SVM-Polynomial, và SVM-RBF. Block sáng tập trung trên đường chéo là minh chứng hình học cho thấy kernel phân tách class tốt.
* **Ablation study ZFeatureMap:** Bổ sung so sánh trực tiếp giữa ZZFeatureMap (có entanglement, dùng 2-qubit ZZ gate) và ZFeatureMap (không có entanglement, chỉ dùng single-qubit rotation H và P(2xᵢ)). Đây là bằng chứng định lượng trực tiếp để chứng minh cross-term 2xᵢxⱼ (được mã hóa bởi ZZ gate) chính là nguồn gốc lợi thế hình học, giúp cô lập yếu tố entanglement khỏi chiều sâu mạch hay noise lượng tử.
* **Kernel target alignment (KTA):** Tính Frobenius inner product giữa kernel matrix K và ma trận nhãn yyᵀ theo công thức KTA(K,y) = ⟨K, yyᵀ⟩ᴺ / (‖K‖ᴺ · ‖yyᵀ‖ᴺ). KTA cao chứng tỏ kernel geometry tương thích tốt với label structure. So sánh KTA giữa ZZ và Z cung cấp bằng chứng định lượng tập trung nhất về vai trò của entanglement.
* **Support vector distribution và margin analysis:** Đánh giá số lượng SV, tỷ lệ SV/train theo class, và phân bố functional margin |decision_function(x)|. Phân tích này kiểm tra xem entanglement có tạo ra margin rộng hơn hay không khi so sánh QSVM ZZ với QSVM Z và ba SVM classical, đặc biệt là trên vùng Normal vs Attack.
* **Decision boundary projection (4D → 2D):** Chiếu biên quyết định về hai cặp PC (PC1–PC2 và PC3–PC4) với median imputation cho các chiều còn lại (lưới 60x60). Tạo ra tổng cộng 10 subplot (5 kernel × 2 cặp PC) kèm đánh dấu các support vector, cho phép so sánh trực quan độ cong và hình dạng biên quyết định.
* **Spearman correlation validation:** Tính đồng thời Pearson (≈ 0) và Spearman (≠ 0) trên PCA output. Điều này tái xác nhận tương quan phi tuyến (rank-order correlation) mà Linear SVM bỏ sót, đồng thời chứng minh ZZFeatureMap khai thác chính xác tương quan này thông qua ZZ gate — đóng vòng bằng chứng nhất quán từ C1 → C2 → C3.

**Ưu điểm thực thi & Kỹ thuật:**
* Tái sử dụng hoàn toàn pipeline và model từ C1–C2.
* Toàn bộ kết quả tính toán nặng (kernel matrices, KTA scores, decision boundary grids) được cache theo `CONFIG_TAG` riêng biệt cho ZZ và Z. Việc này vừa đảm bảo tính tái hiện (reproducibility) vừa tránh overhead khi chạy lại.

**Ý nghĩa khoa học:**
* Cung cấp bằng chứng hình học trực quan để chuyển luận điểm từ "kernel lượng tử có thể biểu diễn" sang "thực sự tạo ra cấu trúc phân tách khác biệt", với ablation study ZFeatureMap loại bỏ các yếu tố confounding.
* KTA là metric có nền tảng lý thuyết vững chắc (Cristianini et al., 2002), được sử dụng rộng rãi để chứng minh lợi thế trong các bài báo về quantum kernel.
* Tạo ra một narrative hoàn chỉnh: C1 phát hiện Spearman ≠ 0 → C2 dự đoán ZZ khai thác tương quan này → C3 định lượng bằng KTA và visualize bằng decision boundary → tạo tiền đề vững chắc cho các đánh giá thực tiễn C4–C6.

---

### C4 — Đánh giá Robustness dưới Data Distribution Shift (ĐÃ HOÀN THÀNH)

**Câu hỏi nghiên cứu:** QSVM có bền vững dưới các dạng distribution shift thực tế trong triển khai IDS không?

**Lý do chọn distribution shift thay vì quantum noise:** Trên circuit 4-qubit nông, quantum noise không đáng kể trong thực tế. Vấn đề lớn nhất trong triển khai IDS thực tế là *distribution shift* — thay đổi phân phối dữ liệu theo thời gian (concept drift), biến đổi đặc trưng mạng, thay đổi tỷ lệ giữa các loại traffic.

**Config thực thi:**
- QSVM: ZZFeatureMap | reps=2 | entanglement=full | C=3.0 | FidelityStatevectorKernel (noiseless)
- Train: 998 mẫu stratified (Normal=48.6%, DoS=33.1%, Probe=8.3%, R2L=5.0%, U2R=5.0%)
- Baselines: SVM-RBF (C=0.1), SVM-Poly2 (C=0.1), SVM-Linear (C=0.1)

---

**Thực nghiệm 1 — Temporal Split Evaluation (E1):**
- Train trên KDDTrain+, evaluate trên KDDTest+ (n=499) và KDDTest-21 thực (n=499 — hard set, loại bỏ mẫu dễ phân loại, distribution shift tự nhiên).
- KDDTest-21 có phân phối lệch mạnh: DoS=36.7%, R2L=24.3%, Probe=20.3%, Normal=18.2% — khác xa KDDTrain+.

| Classifier  | F1_Standard | F1_Hard | ΔF1    | Drop%  |
|-------------|-------------|---------|--------|--------|
| QSVM (ZZ)   | 0.8672      | 0.6494  | +0.2178 | 25.11% |
| SVM-RBF     | 0.8255      | 0.6228  | +0.2027 | 24.55% |
| SVM-Poly2   | 0.8087      | 0.6380  | +0.1707 | 21.11% |
| SVM-Linear  | 0.8192      | 0.6359  | +0.1833 | 22.38% |

**Kết luận E1:** QSVM có F1_standard cao nhất (0.8672) và F1_hard cao nhất (0.6494), nhưng ΔF1 lớn nhất (+0.2178 = 25.11% drop). QSVM **không robust hơn** các SVM classical về mức độ suy giảm tương đối khi gặp temporal shift. SVM-Poly2 có drop nhỏ nhất (21.11%). McNemar test: QSVM vs SVM-RBF (p=0.0708, ns), QSVM vs SVM-Poly2 (p=0.2728, ns), QSVM vs SVM-Linear (p=0.2101, ns) — không có sự khác biệt thống kê đáng kể trên hard test set.

---

**Thực nghiệm 2 — Feature Perturbation Robustness (E2):**
- Thêm nhiễu Gaussian N(0, σ²) vào feature space (sau pipeline C1) với σ ∈ {0.0, 0.01, 0.05, 0.1, 0.2}.
- Base test: 399 mẫu stratified từ KDDTest+.

| Classifier | F1@σ=0 | F1@σ=0.05 | F1@σ=0.2 | Slope (F1/σ) |
|------------|--------|-----------|----------|--------------|
| QSVM (ZZ)  | 0.8445 | 0.8294    | 0.6125   | **-1.1591**  |
| SVM-RBF    | 0.7994 | 0.7943    | 0.7868   | -0.0594      |
| SVM-Poly2  | 0.8070 | 0.8070    | 0.7920   | -0.0663      |
| SVM-Linear | 0.7995 | 0.8020    | 0.7945   | -0.0262      |

**Kết luận E2:** QSVM **kém robust nhất** với feature noise — degradation slope (-1.1591 F1/σ) cao hơn ~20× so với SVM-RBF (-0.0594). Trong vùng noise thực tế (σ ≤ 0.05): QSVM vẫn dẫn đầu (F1=0.8294) và degradation nhỏ (−1.8%). Nhưng tại σ=0.2 (noise cao), QSVM sụt giảm nghiêm trọng xuống F1=0.6125 trong khi SVM-RBF vẫn giữ 0.7868. McNemar significant tại σ=0.01 (p=0.016, **) và σ=0.20 (p≈0, **).

**Nguyên nhân:** Kernel lượng tử nhạy với perturbation trong angle-encoded feature space — nhiễu trong [0, π] làm thay đổi fidelity ⟨φ(x)|φ(z)⟩ mạnh hơn so với RBF kernel.

---

**Thực nghiệm 3 — Class Prior Shift (E3):**
- Train trên phân phối gốc (Normal~48.6%), evaluate trên 3 phân phối test:
  - (a) Balanced 50-50: n=272
  - (b) Attack-heavy 70%: n=299
  - (c) DoS-only binary: n=300

| Classifier | Balanced | Atk70% | DoS-only | Mean   | Std    |
|------------|----------|--------|----------|--------|--------|
| QSVM (ZZ)  | 0.8417   | 0.8430 | 0.8766   | **0.8537** | 0.0161 |
| SVM-RBF    | 0.8009   | 0.7771 | 0.7877   | 0.7886 | 0.0098 |
| SVM-Poly2  | 0.8013   | 0.8092 | 0.7591   | 0.7899 | 0.0220 |
| SVM-Linear | 0.8086   | 0.8068 | 0.7783   | 0.7979 | 0.0138 |

**Kết luận E3:** QSVM **vượt trội rõ rệt** — F1 cao nhất ở cả 3 phân phối và mean F1 cao nhất (0.8537). Std của QSVM (0.0161) ở mức trung bình — ổn định hơn SVM-Poly2 (0.0220) nhưng kém SVM-RBF (0.0098). Effect size lớn: Cohen's d QSVM vs SVM-RBF = +3.99 (large), QSVM vs SVM-Poly2 = +2.70 (large), QSVM vs SVM-Linear = +3.03 (large).

---

**Tổng hợp kết luận C4:**

| Experiment | Metric chính | QSVM so với SVM classical |
|------------|-------------|--------------------------|
| E1: Temporal split | F1_hard, ΔF1 | F1_hard cao nhất nhưng drop % lớn nhất; không significant theo McNemar |
| E2: Feature noise | Degradation slope | Yếu nhất (slope -1.16); robust trong practical range (σ≤0.05) nhưng sụt mạnh ở σ=0.2 |
| E3: Prior shift | Mean F1, std | Vượt trội rõ rệt (effect size large) — đây là điểm mạnh nhất của C4 |

**Điểm mạnh có thể claim:** QSVM generalize tốt nhất dưới **class prior shift** (E3) — phù hợp với luận điểm margin lượng tử ổn định hơn khi phân phối class thay đổi.

**Điểm cần thận trọng khi viết paper:** E2 cho thấy QSVM nhạy với Gaussian noise trong feature space — cần framing đúng: "robust trong practical noise range (σ≤0.05) nhưng không phù hợp với môi trường noise rất cao." E1 không cho thấy ưu thế robustness rõ ràng so với SVM-Poly2/Linear.

**Technical stack C4:**
- Qiskit 2.3.0, Qiskit ML 0.9.0, FidelityStatevectorKernel (noiseless)
- McNemar test (Edwards continuity correction), Cohen's d effect size
- Stratified sampling (stratified_sample_for_qsvm) đảm bảo U2R/R2L có đại diện tối thiểu
- Tất cả pipeline transformers reuse từ C1 (zero-leakage contract)
- Cache artifacts: `results_cache/c4/`, test samples tại `data/processed_data/NSL_KDD_Test_C4_*.csv`
- Output figures: `reports/c4_e1_temporal_split.png`, `c4_e2_perturbation_robustness.png`, `c4_e3_prior_shift.png`, `c4_robustness_summary.png`

---

### C5 — Confidence Calibration và Phân tích Chi tiết Tấn công Hiếm (DỰ TÍNH)

**Câu hỏi nghiên cứu:** Confidence score của QSVM có đáng tin cậy không, đặc biệt trên U2R và R2L?

**Lý do quan trọng:** Trong IDS thực tế, một hệ thống được *calibrated* tốt (confidence = accuracy thực tế) quan trọng hơn F1 đơn thuần vì false alarm rate ảnh hưởng trực tiếp đến operator workload. Weighted F1 bị dominate bởi class Normal (~53%) — cần vượt qua giới hạn này.

**Phân tích chính:**
- **Reliability diagram (calibration curve):** Plot predicted confidence vs actual accuracy theo từng bin — kiểm tra QSVM có over-confident hoặc under-confident trên U2R/R2L không so với SVM cổ điển.
- **Expected Calibration Error (ECE) và Maximum Calibration Error (MCE) per-class:** ECE = Σ|Bₓ|/n · |acc(Bₓ) − conf(Bₓ)|. Classifier có ECE nhỏ hơn trên rare class → ít false alarm hơn khi triển khai.
- **Decision margin histogram:** Phân bố |w·x − b| cho đúng vs sai prediction theo class — QSVM có margin tập trung hơn cho rare class không? Margin phân tán → classifier không chắc chắn → nhiều false alarm.
- **PR curve và ROC per-class:** Thực tiễn hơn F1 đơn điểm — cho phép chọn operating point theo ngưỡng false positive rate chấp nhận được (thường 1–5% trong IDS).
- **Per-class precision/recall/F1 và confusion matrix chi tiết:** Phân tích error pattern (QSVM sai ở mẫu nào, SVM sai ở mẫu nào?) cho U2R và R2L.

**Label cần thiết:** `label_multiclass` đã được giữ lại trong pipeline để phục vụ phân tích này.

**Ý nghĩa:** ECE và MCE là metrics có nền tảng lý thuyết vững chắc (Guo et al., 2017), chưa được khảo sát trong các paper QSVM-IDS hiện tại. Potential follow-up: temperature scaling và Platt calibration cho QSVM (hiện chưa có công trình nào áp dụng post-hoc calibration cho quantum classifier trong IDS).

> ⚠️ **DỰ TÍNH** — Còn đang cân nhắc scope và phương pháp phân tích cụ thể.

---

### C6 — Phân tích Learning Curve và Sample Complexity (DỰ TÍNH)

**Câu hỏi nghiên cứu:** Trong low-data regime, QSVM có lợi thế hơn SVM cổ điển không?

**Hướng tiếp cận dự kiến:**
- Đánh giá mối quan hệ giữa kích thước tập huấn luyện và hiệu năng.
- So sánh learning curve của QSVM vs SVM linear vs SVM RBF.
- Kiểm tra giả thuyết lợi thế lượng tử khi dữ liệu hạn chế.
- Subsets: `NSL_KDD_Train_Sample{n}.csv` đã được chuẩn bị trong pipeline.

**Ý nghĩa dự kiến:** Phân tích khả năng tổng quát hóa; tăng chiều sâu lý thuyết về quantum advantage. Đây là thử nghiệm trực tiếp nhất cho giả thuyết lợi thế lượng tử khi dữ liệu hạn chế.

> ⚠️ **DỰ TÍNH** — Còn đang cân nhắc.

---

## 6. KHUNG KIỂM ĐỊNH THỐNG KÊ

Áp dụng cho tất cả contributions để đảm bảo kết luận có ý nghĩa thống kê:
- 5-fold cross validation
- Báo cáo mean ± standard deviation
- Kiểm định McNemar (so sánh hai classifier)
- Cohen's d (effect size)
- Bootstrap 95% CI (200 iterations)

---

## 7. KHẢ NĂNG MỞ RỘNG SANG TẬP DỮ LIỆU KHÁC

Ma trận ánh xạ đóng góp — dataset:

| Dataset | C1 | C2 | C3 | C4 | C5 | C6 | Câu hỏi chính |
|---------|----|----|----|----|----|----|----------------|
| NSL-KDD | ✅ cơ sở | ✅ | ✅ kernel geometry | ✅ distribution shift | ✅ U2R/R2L calibration | ✅ | Baseline toàn bộ |
| UNSW-NB15 | stability test | bậc tương tác cao hơn | kernel alignment so sánh | — | loại tấn công mới | — | Pipeline có stable không khi input sạch hơn? |
| CIC-IDS2017 | high-dim stress (80 feat) | — | — | distribution shift (80 feat, temporal) | — | — | Có scale được lên 80 features không? |
| CICIOT2023 | — | — | — | extreme class prior shift | ECE trên IoT rare attacks | IoT low-data | QSVM có lợi thế khi imbalance cực đoan? |
| BETH | — | — | — | natural distribution shift | — | true low-data regime | Learning curve QSVM có dốc hơn SVM khi rất ít data? |

**Ghi chú từng dataset:**
- **UNSW-NB15:** 49 đặc trưng, 9 loại tấn công hiện đại (Fuzzers, Backdoors, Exploits, Shellcode, Worms...). Hybrid attacks đòi hỏi kernel mô hình hóa tương tác bậc cao hơn bậc 2 → cơ sở để so sánh ZZFeatureMap vs ZFeatureMap và đánh giá lại C2.
- **CIC-IDS2017:** 80 đặc trưng (CICFlowMeter), chiều đặc trưng cao nhất. Câu hỏi: cần bổ sung pre-clustering hoặc feature hashing trước SelectKBest không?
- **CICIOT2023:** Normal traffic >95%, imbalance cực đoan. Đặc trưng IoT thường có phân phối bimodal → cần phân tích temporal stability của SelectKBest.
- **BETH:** 8 triệu sự kiện audit log Linux, <1% nhãn tấn công thực, APT attacks. Dữ liệu thực từ môi trường sản xuất — kiểm tra tính ứng dụng thực tiễn toàn bộ framework.

---

## 8. HƯỚNG NGHIÊN CỨU MỞ RỘNG

1. Thử nghiệm trên backend lượng tử thực (IBM Quantum, IonQ) để đối chiếu kernel alignment (C3) và support vector distribution với kết quả simulator.
2. Mô hình lai classical-quantum ensemble: kết hợp QSVM với Random Forest trên đặc trưng bị loại bởi SelectKBest.
3. Phân tích khả năng mở rộng khi số qubit tăng: đánh giá hàm F(n) tại n = 8, 12, 16 qubit và tác động lên kernel alignment (C3).
4. So sánh lý thuyết margin giữa kernel cổ điển và kernel lượng tử trên các tập dữ liệu mục 7 — mở rộng C3 sang không gian đặc trưng cao chiều hơn.
5. Nghiên cứu adaptive SelectKBest: tự động điều chỉnh K theo đặc trưng phân phối của từng tập dữ liệu thay vì dùng cross-validation tĩnh.
6. Mở rộng C4 sang online learning setting: QSVM với incremental kernel update khi traffic pattern thay đổi liên tục.
7. Temperature scaling và Platt calibration cho QSVM để cải thiện ECE (C5) — hiện chưa có công trình nào áp dụng post-hoc calibration cho quantum classifier trong bài toán IDS.

---

## 9. CÔNG CỤ & THƯ VIỆN

- **Quantum:** Qiskit, qiskit-aer (AerSimulator + NoiseModel)
- **ML:** scikit-learn (SVC, SelectKBest, PCA, MinMaxScaler, cross_val_score)
- **Data:** pandas, numpy
- **Visualization:** matplotlib, seaborn
- **Persistence:** joblib
- **Metrics:** f1_score, accuracy_score, davies_bouldin_score, silhouette_score

---

## 10. CẤU TRÚC THƯ MỤC DỰ ÁN

```
project_root/
├── data/
│   ├── raw/
│   │   ├── KDDTrain+.txt
│   │   └── KDDTest+.txt
│   └── processed/
│       ├── NSL_KDD_Train_Cleaned.csv
│       ├── NSL_KDD_Test_Cleaned.csv
│       ├── NSL_KDD_Train_Selected.csv
│       └── NSL_KDD_Train_Sample{n}.csv
├── models/
│   ├── feature_selector_k20.joblib
│   ├── pca_4components.joblib
│   ├── scaler_minmax_pi.joblib
│   └── qsvm_{CONFIG_TAG}_{n}.joblib
├── notebooks/
│   ├── preprocess.ipynb
│   ├── selectkbest_nslkdd__2_.ipynb
│   ├── pca.ipynb
│   └── c3_kernel_geometry.ipynb        ← mới (thay thế c3_noise_robustness_v2.ipynb)
└── src/
    └── data_preprocessing.py
```
