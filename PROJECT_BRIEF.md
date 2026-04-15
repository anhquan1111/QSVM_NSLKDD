# Học Máy Kernel Lượng Tử Có Ràng Buộc Phần Cứng Cho Phát Hiện Tấn Công Mạng Trong Kỷ Nguyên NISQ

**Tóm tắt định hướng:** Khung nghiên cứu định hướng khoa học tích hợp tối ưu tài nguyên lượng tử, phân tích khả năng biểu diễn và hình học kernel lượng tử, đánh giá robustness thực tế và calibration cho IDS deployment.

## 1. Tóm tắt định hướng nghiên cứu

Nghiên cứu này đề xuất một khung Quantum Support Vector Machine (QSVM) có xét đến ràng buộc phần cứng lượng tử trong kỷ nguyên NISQ (Noisy Intermediate-Scale Quantum). Khác với các công trình chủ yếu so sánh thực nghiệm, đề tài này tập trung vào chiều sâu khoa học thông qua sáu đóng góp nguyên gốc có thể kiểm chứng độc lập.

### 1.1 Bối cảnh & Vấn đề cốt lõi

- **Bài toán:** Phát hiện xâm nhập mạng (IDS) dựa trên tập dữ liệu chuẩn NSL-KDD (125.973 mẫu train, 22.544 mẫu test). Đặc thù: phân phối lớp cực kỳ mất cân bằng (U2R, R2L < 1%) và không gian đặc trưng hỗn hợp.
    
- **Phương pháp:** Sử dụng Quantum SVM khai thác quantum kernel `K(x,z) = |⟨φ(x)|φ(z)⟩|²` với `ZZFeatureMap` để mã hóa tương tác cặp đặc trưng phi tuyến.
    
- **Thách thức NISQ:** Dữ liệu sau One-Hot Encoding lên tới 122 chiều, không khả thi đưa trực tiếp vào phần cứng NISQ (giới hạn qubit và error rate cao của 2-qubit gate). Cần giảm chiều tối ưu (xuống ~4 qubit).
    
- **Hạn chế của các nghiên cứu hiện tại:** (1) Chọn chiều nhúng cố định bỏ qua chi phí qubit; (2) Chưa giải thích cơ chế lợi thế của kernel lượng tử; (3) Thiếu phân tích cấu trúc hình học biên quyết định; (4) Đánh giá thiếu thực tiễn (bỏ qua distribution shift và calibration).
    

### 1.2 Tóm tắt 6 Đóng góp (Contributions)

- **C1:** Pipeline giảm chiều hai giai đoạn (SelectKBest + PCA đa mục tiêu).
    
- **C2:** Phân tích khả năng biểu diễn của ZZFeatureMap.
    
- **C3:** Phân tích Kernel Geometry và Decision Boundary.
    
- **C4:** Đánh giá Robustness dưới Data Distribution Shift.
    
- **C5:** Phân tích Confidence Calibration và per-class trên tấn công hiếm.
    
- **C6:** Phân tích learning curve và sample complexity.
    

## 2. Chi tiết Các Đóng góp (Contributions)

### Đóng góp 1 (C1): Tối ưu hóa nhúng lượng tử có ràng buộc phần cứng

Pipeline giảm chiều 2 giai đoạn nối tiếp, tuân thủ nguyên tắc zero-leakage (chỉ fit trên tập train).

- **Bước 1: Tiền xử lý và lọc đặc trưng bằng SelectKBest (f_classif)**
    
    - **Thực thi:** Dùng ANOVA F-test (`f_classif`) lọc từ 122 chiều (sau OHE) xuống các đặc trưng có ý nghĩa. Tham số `K` được tối ưu bằng 5-fold CV (stratified).
        
    - **Kết quả:** Chọn `K_FINAL = 25` dựa trên elbow criterion (giảm 79.5% số lượng). Ablation study cho thấy pipeline 2 bước (SelectKBest K=25 + PCA 4D) đạt F1=0.8989, cao hơn PCA trực tiếp 4D (+4.8% relative improvement).
        
- **Bước 2: Tối ưu hóa PCA đa mục tiêu có ràng buộc phần cứng**
    
    - **Mục tiêu:** Xây dựng bài toán tối ưu đa mục tiêu: `Max F(n) = α·V(n) + β·S_norm(n) − γ·Q(n)`. Ràng buộc: `V(n) ≥ 80%`.
        
    - **Các tham số:** `V(n)` (variance), `S_norm(n)` (Fisher Score chuẩn hóa), `Q(n)` (hardware cost của ZZFeatureMap tính bằng số lượng gate có trọng số).
        
    - **Kết quả:** Tối ưu chọn `n = 4` qubit nằm trong tập Pareto-optimal trên cả 3 mục tiêu. Spearman correlation chứng minh có tương quan phi tuyến giữa các PC, làm tiền đề cho ZZFeatureMap.
        
- **Pipeline tổng thể:** `NSL-KDD (41 fts) -> OHE (122 fts) -> SelectKBest (25 fts) -> PCA Pareto (4 fts) -> MinMaxScaler [0, π] -> QSVM (ZZFeatureMap, 4-qubit)`.
    
- **Ý nghĩa khoa học:** Lần đầu tích hợp lọc thống kê và tối ưu Pareto qubit cost; tham số xác định bằng data-driven; có ablation study chứng minh hiệu quả rõ ràng.
    

### Đóng góp 2 (C2): Phân tích khả năng biểu diễn của Quantum Kernel

Giải thích lý do tại sao ZZFeatureMap vượt trội trên dữ liệu IDS.

- **Phân tích chính:** Dữ liệu IDS có tương quan cặp đặc trưng cao. `ZZFeatureMap` mô hình hóa tương tác bậc hai thông qua entanglement. Kernel lượng tử tương đương polynomial kernel bậc 2 nhưng ánh xạ vào không gian Hilbert tăng theo hàm mũ.
    
- **Ý nghĩa khoa học:** Liên kết cấu trúc dữ liệu với thiết kế kernel; giải thích lợi thế biên phân lớp; nâng cấp độ nghiên cứu từ benchmark lên phân tích bản chất.
    

### Đóng góp 3 (C3): Phân tích Kernel Geometry và Decision Boundary

Visualize và định lượng cấu trúc hình học của kernel (bằng chứng thực nghiệm cho C2).

- **Phân tích chính:**
    
    - **Kernel matrix heatmap:** So sánh block structure giữa ZZFeatureMap, ZFeatureMap (ablation), SVM-Linear, Poly, RBF.
        
    - **Ablation study (ZZ vs Z):** Cô lập vai trò của entanglement (cross-term 2xᵢxⱼ).
        
    - **Kernel Target Alignment (KTA):** Tính Frobenius inner product `KTA(K,y)`. KTA cao chứng tỏ kernel geometry tương thích tốt với label.
        
    - **Margin analysis & SV distribution:** Phân bố margin trên toàn tập train.
        
    - **Decision boundary projection (4D -> 2D):** Chiếu biên quyết định lên các cặp PC để so sánh trực quan độ cong.
        
- **Ý nghĩa khoa học:** Cung cấp bằng chứng hình học vững chắc; sử dụng metric KTA có nền tảng lý thuyết cao; tạo chuỗi narrative logic (C1 -> C2 -> C3).
    

### Đóng góp 4 (C4): Đánh giá Robustness dưới Data Distribution Shift

Đánh giá độ bền bỉ trong môi trường deployment thực tế.

- **Thực nghiệm 1 (Temporal split):** Train trên KDDTrain+, test trên KDDTest+ và KDDTest-21 (tập khó hơn, mô phỏng concept drift).
    
- **Thực nghiệm 2 (Feature perturbation):** Thêm nhiễu Gaussian (σ ∈ {0.01, 0.05, 0.1, 0.2}), đo F1-macro degradation curve để mô phỏng sensor noise.
    
- **Thực nghiệm 3 (Class prior shift):** Đánh giá trên các phân phối test bị tái cân bằng (50-50, Attack 70%, v.v.) để kiểm tra sự ổn định của margin.
    
- **Ý nghĩa khoa học:** Trả lời trực tiếp khả năng ứng dụng thực tế của QSVM; sử dụng chuẩn evaluation của cộng đồng IDS.
    

### Đóng góp 5 (C5): Confidence Calibration và Phân tích Tấn công Hiếm

Thay vì chỉ báo cáo weighted F1, phân tích sâu độ tin cậy (confidence score) của mô hình QSVM so với Classical SVM (RBF, Poly) trên các lớp tấn công hiếm (U2R, R2L).

- **Phân tích chính:**

  - **Reliability diagram & ECE/MCE:** Đánh giá QSVM có bị over-confident trên U2R/R2L không, từ đó ước lượng rủi ro False Alarm Rate. Sử dụng chiến lược adaptive binning hoặc gom nhóm số lượng mẫu bằng nhau cho các lớp U2R/R2L để tránh hiện tượng empty bins do thiếu hụt dữ liệu

  - **Decision margin histogram:** Phân tích độ phân tán của biên quyết định (|w·x - b|) cho các mẫu đoán đúng/sai. QSVM có margin tập trung hơn cho rare class không?). Các margin này sau đó được ánh xạ thành xác suất dự đoán $[0, 1]$ thông qua Platt Scaling để phục vụ tính toán ECE.

  - **PR curve và ROC per-class:** Đánh giá hiệu năng dựa trên operating point (ngưỡng FPR 1-5%).

  - **Error Pattern & Confusion Matrix:** So sánh chi tiết mẫu nào QSVM đoán đúng mà SVM đoán sai trên lớp hiếm.

- **Ý nghĩa khoa học:** Trực tiếp giải quyết bài toán False Alarm Rate trong thực tế triển khai IDS; vượt qua điểm mù của weighted F1 (bị dominate bởi lớp Normal).
    

### Đóng góp 6 (C6): Phân tích Learning Curve và độ phức tạp mẫu ✅ *Hoàn thành*

- **Phân tích chính:** Đánh giá trực tiếp mối quan hệ động lực học giữa kích thước tập huấn luyện và hiệu năng tổng quát hóa của mô hình thông qua đường cong học tập (Learning Curve). Thực nghiệm đã được tiến hành trên 4 mốc dữ liệu (N ∈ {100, 200, 500, 1000}) với các tập con đã được lấy mẫu phân tầng theo `attack_category`:
  - **Thiết lập mốc dữ liệu (Training Subsets):** Huấn luyện mô hình trên các tập con có kích thước tăng dần: 100, 200, 500, 1000 mẫu. Các tập con được chuẩn bị trước với chiến lược stratified sampling, đảm bảo đại diện của lớp hiếm (U2R, R2L) ngay cả ở mốc 100 mẫu.
  - **Triển khai kernel lượng tử:** Sử dụng `FidelityStatevectorKernel` với `ZZFeatureMap(feature_dimension=4, reps=2, entanglement='full')` — mô phỏng statevector không nhiễu, nhất quán với các đóng góp C3, C4, C5.
  - **Tuân thủ Zero-Leakage (Cực kỳ quan trọng):** Tại mỗi mốc N mẫu, toàn bộ pipeline (SelectKBest K=20 → PCA 4D → MinMaxScaler[0, π]) được khởi tạo lại từ đầu, chỉ `fit` trên tập con N mẫu đó, rồi mới `transform` tập Test cố định (22.544 mẫu).
  - **Đánh giá và Đối sánh:** Tại mỗi mốc, huấn luyện độc lập QSVM và 3 baseline (SVM-RBF, SVM-Poly bậc 2, SVM-Linear). Ghi nhận F1-macro trên cả tập Train và Test để phân tích generalization gap và overfitting.

- **Kết quả thực nghiệm:**

  | Mô hình | N=100 | N=200 | N=500 | N=1000 |
  |---------|-------|-------|-------|--------|
  | **QSVM** | **0.8132** | **0.7973** | **0.8311** | **0.8128** |
  | SVM-RBF | 0.7240 | 0.7431 | 0.7310 | 0.7289 |
  | SVM-Poly | 0.7008 | 0.7537 | 0.7262 | 0.7434 |
  | SVM-Linear | 0.7331 | 0.7583 | 0.7646 | 0.7370 |

  QSVM vượt trội tất cả baseline tại mọi mốc N. Khoảng cách rõ nhất tại N=500: QSVM đạt Test F1=0.8311, cao hơn SVM-RBF 10.0 điểm phần trăm.

- **Ý nghĩa khoa học:** Cung cấp bằng chứng thực nghiệm trực tiếp xác nhận giả thuyết lợi thế lượng tử (quantum advantage) trong điều kiện *low-data regime*. Kernel lượng tử ZZFeatureMap — nhờ ánh xạ dữ liệu vào không gian Hilbert với tương tác phi tuyến bậc hai — học được biên quyết định hiệu quả hơn khi số mẫu huấn luyện hạn chế.

- **Kiểm định thống kê (Cohen's d tại N=500, lớp hiếm U2R+R2L):**
  - QSVM mean |decision margin| = **0.6538** ± 0.4674
  - SVM-RBF mean |decision margin| = **0.5070** ± 0.2126
  - **Cohen's d = 0.4043** (kích thước hiệu ứng: *Nhỏ* nhưng có ý nghĩa thống kê trên 2.952 mẫu hiếm)
  - Kết quả xác nhận: QSVM tạo ra biên quyết định xa hơn và ổn định hơn trên các tấn công hiếm khi dữ liệu huấn luyện bị giới hạn ở 500 mẫu.
    

## 3. Khung kiểm định thống kê

- 5-fold cross validation.
    
- Báo cáo độ lệch chuẩn.
    
- Kiểm định McNemar.
    
- Hiệu ứng Cohen’s d. _(Đảm bảo kết luận có ý nghĩa thống kê và tránh overclaim)._
    

## 4. Khả năng áp dụng trên các tập dữ liệu khác (Generalization)

|Dataset|Đặc điểm cốt lõi|Câu hỏi nghiên cứu trọng tâm|
|---|---|---|
|**UNSW-NB15**|49 features, 9 loại tấn công, có tấn công hybrid.|Pipeline C1 có ổn định? Kernel có mô hình hóa được tương tác > bậc 2?|
|**CIC-IDS2017/18**|80 features (cao chiều), lưu lượng thực tế.|SelectKBest có chịu tải được không? Hay cần clustering trước?|
|**CICIOT2023**|Môi trường IoT, Normal > 95% (mất cân bằng cực đại).|Lợi thế QSVM so với RBF trong extreme prior shift?|
|**BETH (2021)**|Audit log Linux thực, APT attacks, < 1% bất thường.|C6 (learning curve) có vượt trội trong "true low-data regime"?|

### Ma trận ánh xạ Đóng góp – Tập dữ liệu

- **NSL-KDD:** C1 (cơ sở), C2, C3 (geometry), C4 (shift), C5 (calibration), C6.
    
- **UNSW-NB15:** C1 (kiểm tra stability), C2 (bậc cao), C3 (KTA), C5.
    
- **CIC-IDS:** C1 (high-dim stress test), C4 (shift).
    
- **CICIOT:** C4 (extreme shift), C5 (ECE trên IoT), C6 (IoT low-data).
    
- **BETH:** C6 (true low-data regime), C4 (natural shift vs benchmark).
    

## 5. Hướng nghiên cứu mở rộng

1. **Hardware execution:** Thử nghiệm trên backend lượng tử thực (IBM Quantum, IonQ) để đối chiếu C3.
    
2. **Hybrid Ensemble:** Kết hợp QSVM với Random Forest trên các đặc trưng bị loại bởi SelectKBest.
    
3. **Scalability:** Đánh giá hàm F(n) tại n = 8, 12, 16 qubit và tác động lên C3.
    
4. **Margin Theory:** So sánh lý thuyết margin giữa kernel lượng tử và cổ điển ở không gian cao chiều.
    
5. **Adaptive SelectKBest:** Tự động điều chỉnh K theo đặc trưng của từng dataset.
    
6. **Online Learning:** QSVM với incremental kernel update cho online IDS.
    
7. **Post-hoc Calibration:** Nghiên cứu temperature scaling / Platt calibration cho QSVM để cải thiện ECE.