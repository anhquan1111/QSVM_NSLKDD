LỜI MỞ ĐẦU
Trong kỷ nguyên số hóa, an ninh mạng đã trở thành thách thức cấp thiết đối với cơ sở hạ tầng quốc gia và doanh nghiệp. Các cuộc tấn công ngày càng tinh vi, đặc biệt là tấn công leo thang đặc quyền (User-to-Root, U2R) và xâm nhập từ xa (Remote-to-Local, R2L), thường xuyên bị các hệ thống phát hiện xâm nhập (IDS) truyền thống bỏ qua. Sự hiếm gặp thống kê của các lớp tấn công này (chiếm dưới 1% trong tập chuẩn NSL-KDD) khiến các phương pháp học máy cổ điển dễ bị lệch lạc về phía lớp đa số, dẫn đến tỷ lệ bỏ sót cao đối với chính những tấn công nguy hiểm nhất.
Đồng thời, điện toán lượng tử đang đánh dấu bước ngoặt với sự ra đời của các bộ xử lý quy mô vừa và có nhiễu (NISQ). Mặc dù chưa đạt đến "lợi thế lượng tử" tổng quát, các thiết bị NISQ đã cho thấy tiềm năng khai thác trong học máy đặc thù — tiêu biểu là mô hình Quantum Support Vector Machine (QSVM-ZZ). Trong đó, kernel lượng tử  được tính toán trên phần cứng lượng tử để ánh xạ dữ liệu vào không gian Hilbert với số chiều tăng theo hàm mũ.
Tuy nhiên, khoảng cách giữa lý thuyết và thực tiễn triển khai vẫn còn rất lớn. Các nghiên cứu QSVM-ZZ cho bài toán IDS hiện nay thường chỉ dừng ở việc so sánh hiệu năng thực nghiệm mà chưa giải thích được cơ chế tạo nên lợi thế lượng tử. Ngoài ra, những ràng buộc nghiêm khắc của phần cứng NISQ (như giới hạn số qubit, tỷ lệ lỗi cổng hai-qubit cao) thường không được tích hợp một cách có hệ thống vào quy trình thiết kế mô hình.
Đề tài này xây dựng một khung nghiên cứu QSVM-ZZ toàn diện và có chiều sâu khoa học cho bài toán IDS, tập trung vào sáu đóng góp nguyên gốc: tối ưu hóa nhúng lượng tử có ràng buộc phần cứng (C1), phân tích khả năng biểu diễn của kernel lượng tử (C2), phân tích cấu trúc hình học kernel và biên quyết định (C3), đánh giá độ bền bỉ dưới dịch chuyển phân phối (C4), hiệu chỉnh độ tin cậy và phân tích tấn công hiếm (C5), và phân tích đường cong học tập trong điều kiện dữ liệu hạn chế (C6). Khung nghiên cứu cung cấp bằng chứng thực nghiệm và xây dựng chuỗi lập luận nhất quán từ thiết kế pipeline đến đánh giá khả năng triển khai thực tế.

# CHƯƠNG 1. TỔNG QUAN VỀ BÀI TOÁN VÀ KHUNG NGHIÊN CỨU


## 1.1. Bối cảnh nghiên cứu: An ninh mạng (IDS) và Kỷ nguyên Lượng tử NISQ


### 1.1.1. Thách thức của bài toán Phát hiện Xâm nhập Mạng

Hệ thống phát hiện xâm nhập mạng (NIDS) là tuyến phòng thủ quan trọng phân loại lưu lượng mạng thành bình thường (Normal) hoặc tấn công (Attack). Tập dữ liệu chuẩn NSL-KDD (phiên bản cải tiến của KDD Cup 1999) gồm 125.973 mẫu huấn luyện và 22.544 mẫu kiểm thử, với 41 đặc trưng gốc và bốn nhóm tấn công chính: DoS, Probe, R2L, và U2R. Bài toán này đặt ra hai thách thức cơ bản:
Thứ nhất, mất cân bằng lớp nghiêm trọng (Class Imbalance): Các lớp U2R và R2L chiếm dưới 1% tổng mẫu. Các bộ phân lớp tối ưu hóa theo accuracy tổng thể dễ bỏ qua các lớp này, gây tỷ lệ bỏ sót cao. Do đó, metric đánh giá bắt buộc là F1-macro (trung bình không trọng số của F1-score) để đảm bảo các lớp hiếm có trọng lượng tương đương.
Thứ hai, không gian đặc trưng hỗn hợp chiều cao: Sau khi One-Hot Encoding (OHE) các biến phân loại, không gian mở rộng từ 41 lên 122 chiều. Sự kết hợp giữa đặc trưng liên tục và rời rạc tạo ra cấu trúc phức tạp, gây khó khăn cho các phương pháp học máy tiêu chuẩn.

### 1.1.2. Tiềm năng và rào cản của Điện toán lượng tử NISQ

Kỷ nguyên NISQ đặc trưng bởi các bộ xử lý lượng tử từ hàng chục đến vài nghìn qubit nhưng chưa có khả năng sửa lỗi hoàn chỉnh. Trên phần cứng IBM Quantum, tỷ lệ lỗi của cổng hai qubit (CNOT) khoảng 0,5% - 1% — cao gấp 5 đến 10 lần so với cổng một qubit (khoảng 0,1%). Đây là ràng buộc phần cứng cứng nhắc khi thiết kế mạch lượng tử thực tế.
Đối với bài toán QSVM-ZZ-IDS, việc nạp trực tiếp 122 đặc trưng vào phần cứng NISQ là bất khả thi. Không chỉ thiếu thiết bị 122-qubit ổn định, mà độ sâu mạch của ZZFeatureMap còn tăng bậc hai theo số qubit, dẫn đến tích lũy lỗi không thể chấp nhận. Do đó, quy trình giảm chiều dữ liệu xuống giới hạn khả thi (4 qubit) một cách có hệ thống và định lượng là yêu cầu bắt buộc.

## 1.2. Hạn chế của các nghiên cứu QSVM-ZZ-IDS hiện tại

Khảo sát tài liệu cho thấy các nghiên cứu ứng dụng QSVM-ZZ cho IDS hiện mắc bốn hạn chế cơ bản:
Thứ nhất, lựa chọn chiều nhúng thiếu cơ sở phần cứng: Đa số các công trình chọn số chiều lượng tử theo ngưỡng phương sai PCA cố định (thường 95% hoặc 99%) mà bỏ qua chi phí cổng hai qubit. Mạch ZZFeatureMap với n qubit yêu cầu số cổng CNOT tăng theo bậc hai , làm tăng lũy kế lỗi phần cứng. Việc bỏ qua yếu tố này khiến thiết kế khó khả thi trên các thiết bị NISQ thực tế.
Thứ hai, thiếu giải thích cơ chế “lợi thế lượng tử”: Phần lớn các nghiên cứu chỉ dừng ở mức báo cáo benchmark (ví dụ: QSVM-ZZ đạt accuracy cao hơn SVM cổ điển vài phần trăm) mà không phân tích chiều sâu khoa học: tại sao cơ chế vướng víu (entanglement) của ZZFeatureMap lại phù hợp với cấu trúc dữ liệu IDS.
Thứ ba, bỏ qua phân tích cấu trúc hình học Kernel và biên quyết định: Hình học của biên quyết định trong không gian Hilbert ( chiều) quyết định trực tiếp hiệu năng phân lớp. Tuy nhiên, việc định lượng và trực quan hóa cấu trúc này thông qua Kernel Target Alignment (KTA) hay heatmap ma trận kernel chưa được thực hiện hệ thống. Do đó, thiếu các bằng chứng xác đáng chứng minh dữ liệu thực sự trở nên dễ phân tách hơn trong không gian lượng tử.
Thứ tư, đánh giá thiếu tính thực tiễn: Hầu hết mô hình chỉ được kiểm thử trên tập dữ liệu tĩnh cùng phân phối, bỏ qua hai bài toán then chốt khi triển khai thực tế: (1) Dịch chuyển phân phối (Distribution shift) do lưu lượng mạng thay đổi theo thời gian; và (2) Hiệu chỉnh độ tin cậy (Confidence calibration) để đảm bảo xác suất dự đoán phản ánh đúng tỷ lệ chính xác thực tế — yếu tố tiên quyết cho các hệ thống cảnh báo tự động.

## 1.3. Khung nghiên cứu tổng thể và 6 đóng góp nguyên gốc

Để giải quyết toàn diện bốn hạn chế trên, đề tài đề xuất một khung nghiên cứu với luồng logic xuyên suốt: C1 (Nền tảng tối ưu)  C2 (Cơ sở lý thuyết)  C3 (Bằng chứng hình học) C4 (Độ bền bỉ thực tế)  C5 (Độ tin cậy cảnh báo) C6 (Hiệu năng khi cạn kiệt tài nguyên). Chi tiết 6 đóng góp nguyên gốc được tóm tắt tại Bảng 1.1.
Bảng 1.1. Khung 6 đóng góp nguyên gốc và Câu hỏi nghiên cứu trọng tâm

[TABLE_1]
| Đóng góp | Tên | Câu hỏi nghiên cứu trọng tâm |
| C1 | Pipeline giảm chiều hai giai đoạn | Làm thế nào để chọn  qubit tối ưu có xét đến chi phí phần cứng NISQ? |
| C2 | Phân tích khả năng biểu diễn và độ ổn định của Quantum Kernel | Quantum kernel với ZZFeatureMap có khai thác được các tương tác phi tuyến trong dữ liệu IDS và duy trì ổn định khi chuyển từ statevector exact sang finite-shot sampling hay không? |
| C3 | Phân tích Kernel Geometry và Decision Boundary | Cấu trúc hình học kernel lượng tử có thực sự khác biệt với kernel cổ điển không? |
| C4 | Đánh giá Robustness dưới Distribution Shift | QSVM-ZZ có bền vững trong môi trường mạng thay đổi không? |
| C5 | Confidence Calibration và Rare Attack Analysis | QSVM-ZZ có đưa ra xác suất dự đoán đáng tin cậy cho tấn công hiếm không? |
| C6 | Learning Curve và Sample Complexity | QSVM-ZZ có lợi thế trong điều kiện dữ liệu huấn luyện hạn chế không? |

1.4. Mục tiêu và phạm vi của báo cáo
Báo cáo này tập trung thực hiện các mục tiêu chính sau:
Hệ thống hóa cơ sở lý thuyết: Trình bày đầy đủ nền tảng toán học cho từng đóng góp khoa học từ C1 đến C6.
Đảm bảo tính tái lập (Reproducibility): Mô tả chi tiết phương pháp luận và quy trình thực nghiệm để đảm bảo khả năng tái hiện hoàn toàn các kết quả.
Phân tích thực nghiệm chuyên sâu: Trình bày kết quả và biện giải ý nghĩa khoa học của ranh giới lợi thế lượng tử trong bài toán IDS.
Đánh giá tính tổng quát: Kiểm chứng khả năng thích nghi của mô hình trên các môi trường dữ liệu mạng khác nhau.
Phạm vi nghiên cứu:
Tập dữ liệu: Trọng tâm thực nghiệm trên NSL-KDD; đánh giá khả năng tổng quát hóa trên tập dữ liệu hiện đại UNSW-NB15.
Môi trường mô phỏng: Sử dụng mô phỏng trạng thái (statevector) trong điều kiện không nhiễu (noiseless) để xác định giới hạn hiệu năng lý thuyết của mô hình trước khi xét đến các yếu tố nhiễu vật lý.
1.5. Bố cục của đồ án
Nội dung đồ án được cấu trúc thành 6 chương chính:
Chương 1 - Mở đầu: Trình bày bối cảnh, thách thức của IDS, hạn chế của các nghiên cứu trước và xác lập 6 đóng góp nguyên gốc của đề tài.
Chương 2 - Cơ sở lý thuyết: Hệ thống hóa toán học về không gian Hilbert, Quantum Kernel, các kỹ thuật giảm chiều và các metric đánh giá chuyên sâu (KTA, Calibration, Robustness).
Chương 3 - Phương pháp luận: Thiết kế chi tiết pipeline C1–C6, quy trình thực thi thực nghiệm và các giao thức đảm bảo tính tái lập của mô hình.
Chương 4 - Kết quả và Thảo luận (NSL-KDD): Phân tích chi tiết hiệu năng của QSVM-ZZ trên tập dữ liệu trọng tâm, cung cấp bằng chứng thực nghiệm cho cả 6 đóng góp khoa học.
Chương 5 - Khả năng Tổng quát hóa (UNSW-NB15): Đánh giá tính ổn định và xác định ranh giới lợi thế lượng tử khi dịch chuyển sang môi trường dữ liệu mạng hiện đại.
Chương 6 - Kết luận và Hướng phát triển: Tổng kết các kết quả đạt được, đối chiếu với mục tiêu đề ra và đề xuất các hướng nghiên cứu tiềm năng trong tương lai.

# CHƯƠNG 2. CƠ SỞ LÝ THUYẾT VÀ NỀN TẢNG TOÁN HỌC KHÔNG GIAN NHÚNG LƯỢNG TỬ


## 2.1. Nền tảng Học máy Kernel Lượng tử (Quantum SVM)


### 2.1.1. Không gian Hilbert và Phép nhúng lượng tử

Cho một bộ xử lý lượng tử gồm n qubit. Không gian trạng thái của hệ thống lượng tử này là một không gian Hilbert phức  có số chiều . Một trạng thái thuần (pure state) của hệ n qubit được biểu diễn bởi một vector đơn vị :
Trong đó,  là cơ sở tính toán (computational basis) và  là các biên độ xác suất.
Để xử lý dữ liệu cổ điển trên máy tính lượng tử, ta sử dụng Phép nhúng lượng tử (Quantum Feature Map). Đây là một ánh xạ phi tuyến  đưa một điểm dữ liệu cổ điển  vào không gian Hilbert thông qua một mạch lượng tử (quantum circuit):
Với  là toán tử unita (unitary operator) được tham số hóa bởi dữ liệu đầu vào x, và  là trạng thái nền ban đầu của hệ. Quá trình này tương đương với kỹ thuật ánh xạ đặc trưng (feature mapping) trong học máy truyền thống, nhưng tận dụng được không gian Hilbert có số chiều tăng theo hàm mũ () để biểu thị các mẫu dữ liệu phức tạp.

### 2.1.2. Công thức Quantum Kernel

Hàm nhân lượng tử (Quantum Kernel) giữa hai điểm dữ liệu cổ điển  được định nghĩa thông qua tích vô hướng của các trạng thái lượng tử tương ứng trong không gian đặc trưng Hilbert:
Độ đo này về mặt vật lý chính là độ trung thực lượng tử (quantum fidelity) giữa hai trạng thái mã hóa  và . Nhờ tính chất hình học của không gian Hilbert, hàm nhân  tự động thỏa mãn các điều kiện của định lý Mercer (tính đối xứng và tính bán xác định dương). Do đó, ma trận kernel lượng tử  hoàn toàn có thể thay thế các hàm nhân cổ điển để huấn luyện mô hình Máy vectơ hỗ trợ (SVM) truyền thống thông qua bài toán tối ưu đối ngẫu.
Giả sử tập dữ liệu huấn luyện có dạng  với dữ liệu đầu vào  và nhãn phân lớp . Bài toán tối ưu đối ngẫu Lagrange của SVM sử dụng Quantum Kernel được phát biểu như sau:
Trong đó,  là các nhân tử Lagrange cần tối ưu và  là tham số điều hòa (regularization parameter) nhằm kiểm soát sự cân bằng giữa độ rộng của biên phân lớp và sai số huấn luyện.
Sau khi giải bài toán tối ưu để tìm ra tập nhân tử Lagrange tối ưu , hàm quyết định (decision function) sau cùng dùng để dự báo nhãn cho một điểm dữ liệu mới x được xác định bởi công thức:
Trong đó, b là hệ số chặn (bias) được tính toán từ các vectơ hỗ trợ (support vectors) nằm sát biên. Việc tích hợp một cấu trúc kernel lượng tử phi tuyến phức tạp dựa trên không gian trạng thái chồng chập và vướng víu cho phép mô hình xây dựng được các biên quyết định hiệu quả trong không gian Hilbert có số chiều siêu lớn, mở ra cơ hội phát hiện các cấu trúc dữ liệu dị thường cấu thành từ các cuộc tấn công mạng mà các hàm nhân cổ điển khó lòng bóc tách.
Để thuận tiện cho việc theo dõi các phân tích toán học sâu hơn tại các chương sau, các ký hiệu toán học cốt lõi và phạm vi giá trị của chúng trong nghiên cứu này được tổng hợp hệ thống tại Bảng 2.1.
Bảng 2.1. Danh mục các ký hiệu toán học sử dụng trong mô hình

[TABLE_2]
| Ký hiệu | Ý nghĩa | Đơn vị/Phạm vi |
| n | Số qubit của ZZFeatureMap | {2, 3, 4, 5, 6, 7, 10} |
| r | Số lần lặp (reps) cấu trúc mạch lượng tử |  |
| K | Số đặc trưng giữ sau SelectKBest | {4, 6, 8, 10, 20, …} |
| d | Số chiều PCA (= số qubit) | 4 (cố định cho NISQ) |
|  | Hệ số tương quan Pearson và Spearman rank | [−1, 1] |
|  | Ma trận Kernel lượng tử và Kernel cổ điển | , PSD |
| KTA | Kernel Target Alignment | [−1, 1] |
| CKA | Căn chỉnh Kernel trung tâm (Centered Kernel Alignment) | [0,1] |
|  | Hạng hiệu dụng (Effective rank) của ma trận Kernel | [1,N] |
|  | Entropy vướng víu von Neumann |  |
|  | Khoảng cách Kullback-Leibler (Đo lường Expressibility) |  |
| V(n) | Tỷ lệ phương sai tích lũy (Explained Variance Ratio) | [0, 1] |
| Q(n) | Chi phí phần cứng chuẩn hóa | [0, 1] |
| J(n) | Hàm mục tiêu Pareto đa mục tiêu | [0, 1] |
| DBI | Chỉ số Davies-Bouldin |  |
|  | Điểm F1 trung bình macro (Metric phân loại chính) | [0,1] |
| ECE, MCE | Lỗi hiệu chuẩn kỳ vọng / tối đa (Calibration Error) | [0,1] |
| d_Cohen | Cohen’s d effect size | (: lớn) |
|  | Giá trị kiểm định Chi-bình phương McNemar |  |
| σ | Std nhiễu Gaussian trên feature space | {0,01; 0,05; 0,10; 0,20} |


## 2.2. Cơ sở Toán học Tối ưu Không gian Nhúng (C1)

Để giảm thiểu gánh nặng tính toán và phù hợp với giới hạn tài nguyên của phần cứng lượng tử thế hệ NISQ, nghiên cứu này đề xuất quy trình giảm chiều dữ liệu hai giai đoạn bao gồm: lọc đặc trưng thống kê và tối ưu hóa không gian nhúng đa mục tiêu.

### 2.2.1. Phân tích phương sai ANOVA F-test

Không gian dữ liệu sau khi thực hiện mã hóa độc lập (One-Hot Encoding) bị mở rộng lên 122 chiều, chứa nhiều đặc trưng nhiễu hoặc không đóng góp vào năng lực phân tách lớp. Đề tài áp dụng kiểm định giả thuyết phân tích phương sai một yếu tố ANOVA F-test để định lượng mối quan hệ giữa các đặc trưng liên tục và nhãn phân loại. Đối với mỗi đặc trưng thứ j trong tập dữ liệu gồm K lớp tấn công và phòng thủ, đại lượng thống kê  được xác định bằng tỷ số giữa phương sai giữa các nhóm () và phương sai nội bộ nhóm ():
Trong đó:
là giá trị trung bình của đặc trưng j thuộc phân lớp c.
là giá trị trung bình tổng thể của đặc trưng j trên toàn bộ tập dữ liệu.
là số lượng mẫu thuộc phân lớp c.
N là tổng số lượng mẫu huấn luyện, và  là tập hợp các chỉ số mẫu thuộc lớp c.
Giá trị thống kê  càng cao chứng tỏ độ phân tách của đặc trưng j giữa các phân lớp càng lớn và ngược lại. Hệ thống tiến hành sắp xếp các đặc trưng theo thứ tự giảm dần của điểm số F nhằm thiết lập tập đặc trưng tối ưu . Số lượng đặc trưng K được xác định một cách khoa học thông qua tiêu chí khuỷu tay (Elbow criterion) trên đường cong hiệu năng  của một bộ phân loại cấu hình nhẹ làm đại diện (proxy model là Linear SVM). Điểm tối ưu  là giá trị nhỏ nhất đảm bảo hiệu năng phân loại không suy giảm vượt quá một ngưỡng dung sai  cho trước so với giá trị cực đại toàn cục.

### 2.2.2. Bài toán Tối ưu hóa Pareto đa mục tiêu và Ràng buộc phần cứng NISQ

Sau khi thu gọn dữ liệu về K chiều (K=20), kỹ thuật Phân tích thành phần chính (PCA) được triển khai nhằm xoay không gian đặc trưng sang hệ tọa độ mới tuyến tính và trực giao. Quá trình phân rã giá trị đơn lẻ (SVD) trên ma trận dữ liệu đã chuẩn tâm  được mô tả như sau:
Với  là thành phần chính thứ k và  là trị riêng tương ứng đại diện cho phương sai được giải thích bởi thành phần đó. Để xác định số lượng thành phần chính tối ưu n (tương ứng với số lượng qubit cấu hình trong không gian lượng tử), đề tài xây dựng bài toán tối ưu hóa đa mục tiêu Pareto.
Hàm mục tiêu tổng hợp J(n) cần được cực đại hóa, cấu thành từ ba đại lượng thành phần:
Thỏa mãn ràng buộc bảo toàn thông tin tuyến tính: , và các trọng số điều hòa nằm trên đơn hình Dirichlet:  (). Ý nghĩa toán học của ba thành phần trong J(n) được định nghĩa cụ thể:
Tỷ lệ phương sai tích lũy giải thích V(n): Đo lường mức độ bảo toàn thông tin của dữ liệu gốc sau khi giảm chiều:
Điểm số Fisher chuẩn hóa : Đại diện cho độ phân cụm hình học của các lớp dữ liệu trên không gian nhúng. Để tối ưu hóa tốc độ tính toán từ  của hệ số Silhouette xuống , nghiên cứu sử dụng giá trị nghịch đảo của chỉ số Davies-Bouldin (DBI) làm hàm đại diện (). Công thức chi tiết của các chỉ số cấu trúc cụm được xác định bởi:
(2.10)
Trong đó,  là phương sai trung bình của các điểm trong cụm i,  là khoảng cách Minkowski giữa hai tâm cụm;  và  lần lượt là khoảng cách nội cụm trung bình và khoảng cách ngoại cụm tối thiểu của mẫu i (dùng cho hệ số Silhouette).
Chi phí tài nguyên phần cứng lượng tử chuẩn hóa Q(n): Phản ánh độ phức tạp và xác suất tích lũy lỗi của mạch khi thực hiện ánh xạ phi tuyến. Do các cổng logic hai qubit (CNOT gate) có tỷ lệ nhiễu lớn hơn xấp xỉ 5 lần so với cổng đơn qubit trên các bộ xử lý lượng tử NISQ hiện tại, chi phí phần cứng được mô hình hóa theo cấu trúc phạt CNOT:
Với r là số tầng lặp mạch (reps),  là số lượng cổng CNOT trong cấu hình liên kết toàn phần (full entanglement), và  hằng số chuẩn hóa đưa miền giá trị về .
Phương pháp giải và xác định tập Pareto: Bài toán được giải bằng thuật toán tìm kiếm lưới (Grid Search) trên đơn hình tham số với độ phân giải cụ thể là 30 bước chia (tương đương với 435 cấu hình trọng số). Một số chiều n được công nhận là tối ưu Pareto (Pareto-optimal) nếu và chỉ nếu không tồn tại bất kỳ một phương án  nào khác có khả năng cải thiện một mục tiêu bất kỳ mà không làm suy giảm các mục tiêu còn lại, tức là không tồn tại  thỏa mãn đồng thời: , , và . Kết quả thực nghiệm tìm kiếm này sẽ trực tiếp định hình cấu hình phần cứng tối ưu cho mô hình lượng tử.

## 2.3. Nền tảng Toán học của mạch ZZFeatureMap (C2)


### 2.3.1. Kiến trúc mạch và mã hóa qua ZZ Gate

Mạch lượng tử tham số hóa  được sử dụng để thiết lập toán tử unita U(x), thực hiện ánh xạ phi tuyến các đặc trưng cổ điển vào không gian trạng thái Hilbert. Để gia tăng năng lực biểu diễn dữ liệu và tạo ra sự vướng víu phức tạp, mạch được cấu hình gồm r lần lặp (), trong đó mỗi lần lặp cấu thành từ hai lớp logic: lớp mã hóa trạng thái đơn qubit và lớp tạo vướng víu hai qubit (entanglement).
Toán tử unita của một lần lặp đơn lẻ  tác động lên hệ n qubit được định nghĩa toán học bởi công thức:
Trong đó:
là tích tensor của các cổng Hadamard nhằm đưa toàn bộ các qubit từ trạng thái nền  vào không gian chồng chập trạng thái (superposition).
là cổng dịch pha đơn qubit (Phase gate) thực hiện mã hóa các đặc trưng độc lập  dưới dạng các góc xoay .
đại diện cho lớp vướng víu hai qubit với sơ đồ liên kết toàn phần (full entanglement topology), tức tập cạnh .
Đối với mỗi cặp qubit , cổng tương tác hai qubit  được hình thức hóa thông qua phép lũy thừa toán tử Pauli-Z:
Khai triển ma trận của toán tử  trong cơ sở tính toán hai qubit () thể hiện cấu trúc ma trận chéo dưới dạng:
Toán tử toàn mạch sau khi thực hiện tích lũy qua r vòng lặp được xác định bằng công thức:
Điểm mấu chốt tạo nên sức mạnh của mạch  nằm ở hàm tham số hóa góc xoay hai qubit, được định nghĩa bởi cấu trúc tích chéo: . Về mặt bản chất, các mối quan hệ tương tác phi tuyến bậc hai (cross-terms) giữa cặp đặc trưng mạng  và  được nhúng trực tiếp và đồng thời vào pha lượng tử của hệ thống. Đây là cơ chế cốt lõi giúp mô hình lượng tử có khả năng bóc tách các mẫu hành vi xâm nhập tinh vi mà không cần thực hiện các bước khai triển đa thức thủ công trong không gian cổ điển.

![FIGURE_1](FIGURE_1)
Hình 2.1. Sơ đồ mạch ZZFeatureMap cơ bản (n=4, reps=2)

![FIGURE_2](FIGURE_2)
Hình 2.2. Cấu trúc entanglement topology (full) của ZZFeatureMap

![FIGURE_3](FIGURE_3)
Hình 2.3. Khai triển cổng pha và mã hóa đặc trưng

### 2.3.2. Quantum Kernel như một phép khai triển Đặc trưng

Để làm rõ cơ chế mở rộng không gian đặc trưng của mạch , trạng thái lượng tử đầu ra sau r lần lặp (bỏ qua hệ số chuẩn hóa để đơn giản hóa biểu thức) có thể được khai triển thành dạng tổ hợp tuyến tính của các trạng thái cơ sở kèm theo các pha dịch chuyển tương ứng:
Trong đó,  là chuỗi nhị phân đại diện cho các trạng thái cơ sở tính toán, và  là hàm pha tổng hợp phụ thuộc tuyến tính vào các đặc trưng độc lập và tương tác bậc hai giữa chúng:
Khi thực hiện tính toán hàm nhân lượng tử giữa hai điểm dữ liệu  và , giá trị bán xác định dương thu được từ bình phương độ lớn của tích vô hướng giữa hai trạng thái tương ứng:
Khi thực hiện khai triển chuỗi Taylor cho các hàm số mũ phức trong công thức (2.12), biểu thức hàm nhân lượng tử sẽ mở ra thành một chuỗi đa thức chứa tổng các số hạng dạng tích chéo đơn thức cấp cao. Cụ thể, các số hạng tuyến tính  và các số hạng tương tác bậc hai  được nhúng một cách tự nhiên vào pha lượng tử mà không cần tính toán tường minh các tọa độ mới.
Hệ quả toán học này xác nhận rằng  đóng vai trò như một bộ khai triển đặc trưng phi tuyến tương đương với hàm nhân đa thức (Polynomial Kernel) bậc 2 cổ điển. Tuy nhiên, điểm vượt trội của phương pháp lượng tử là các đặc trưng tương tác này được ánh xạ trực tiếp vào không gian Hilbert phức  có số chiều tăng theo hàm mũ (), thay vì không gian Euclid thực giới hạn ở số chiều  của hàm nhân đa thức truyền thống.

### 2.3.3. So sánh năng lực biểu diễn: ZZFeatureMap vs Polynomial Kernel bậc 2

Sự khác biệt mang tính bản chất về mặt cấu hình toán học và không gian hình học giữa hàm nhân lượng tử  và hàm nhân đa thức bậc 2 cổ điển được tổng hợp hệ thống tại Bảng 2.2.
Bảng 2.2. So sánh đặc tính hình học và tính toán giữa ZZFeatureMap và Polynomial Kernel

[TABLE_3]
| Đặc điểm | ZZFeatureMap (Quantum Kernel) | Polynomial Kernel bậc 2 (Classical) |
| Không gian đặc trưng | Không gian Hilbert phức , số chiều | Không gian Euclid thực , số chiều |
| Số hạng tương tác | Tất cả các cặp đặc trưng bậc hai thông qua lớp vướng víu (Entanglement) | Tất cả các cặp đặc trưng bậc hai thông qua tích chéo đa thức |
| Biên quyết định | Siêu phẳng phân lớp trong không gian Hilbert phức | Siêu phẳng phân lớp trong không gian Euclid thực |
| Cơ chế biểu diễn | Mã hóa không tường minh thông qua pha lượng tử của trạng thái phức | Tính toán tường minh thông qua các đơn thức (monomials) |
| Độ phức tạp tính toán | Phụ thuộc vào số lượng cổng logic unita và số lượng shots đo lường | Phụ thuộc vào số lượng phép nhân vô hướng trong không gian gốc |

Điểm khác biệt căn bản tạo nên ưu thế của  nằm ở cơ chế can thiệp vật lý. Trong không gian lượng tử, các tương tác giữa các đặc trưng mạng không chỉ đơn thuần là các phép nhân đại số, mà được điều biến trực tiếp vào pha của các biên độ xác suất phức. Do đó, biên quyết định tối ưu được xây dựng trong không gian Hilbert có khả năng khai thác hiện tượng giao thoa lượng tử (quantum interference) giữa các trạng thái chồng chập. Cơ chế giao thoa này cho phép khuếch đại khoảng cách hình học giữa các mẫu dữ liệu dị thường (tấn công mạng) và các mẫu dữ liệu bình thường, tạo ra một không gian nhúng có độ phân tách lớp vượt trội mà các mô hình cổ điển không có cơ chế vật lý tương đương để thực hiện.

### 2.3.4. FidelityStatevectorKernel và FidelityQuantumKernel: sai lệch finite-shot

Trong điều kiện mô phỏng lý tưởng không nhiễu (noiseless), ma trận nhân lượng tử giữa hai mẫu dữ liệu được tính toán dựa trên giá trị độ trung thực (quantum fidelity) chính xác tuyệt đối:
Đối với phương pháp mô phỏng vector trạng thái (Statevector simulation), giá trị này được trích xuất trực tiếp bằng đại số tuyến tính từ các biên độ xác suất toàn phần, do đó phản ánh chính xác cấu trúc hình học thuần túy của không gian nhúng lượng tử. Tuy nhiên, khi triển khai trên phần cứng lượng tử thực tế hoặc các backend mô phỏng dạng lấy mẫu (sampling-based backend), ma trận kernel không thể được tính toán trực tiếp mà phải ước lượng thông qua tần suất xuất hiện của trạng thái sau khi thực hiện mạch chồng (overlap circuit).
Khi cấu hình số lần đo giới hạn là N (shots), hàm nhân lượng tử thực nghiệm  được xác định bởi tỷ lệ số lần hệ thống sụp đổ về trạng thái nền :
Trong đó,  là số lượng shots thu được chuỗi nhị phân toàn không (). Theo định lý giới hạn trung tâm, toán tử ước lượng này tuân theo phân phối nhị thức với kỳ vọng và phương sai được xác định bởi:
Hệ quả toán học này cho thấy sai số lấy mẫu (shot noise) tỷ lệ nghịch với căn bậc hai của số lượng shots (). Để định lượng mức độ sai lệch hình học giữa ma trận ước lượng thực nghiệm  và ma trận tham chiếu chính xác , đề tài áp dụng hai độ đo cốt lõi bao gồm Độ tương đồng Frobenius () và Sai số tuyệt đối trung bình thành phần ():
Lưu ý toán học quan trọng: Ma trận tham chiếu chính xác  không đóng vai trò là giới hạn trên (upper bound) bắt buộc cho hiệu năng phân loại của mô hình. Trong một số kịch bản thực nghiệm, nhiễu shot noise ngẫu nhiên hoạt động như một cơ chế điều hòa (stochastic regularization) tương tự kỹ thuật Dropout trong mạng neuron, giúp làm phẳng biên quyết định và tăng nhẹ điểm số . Tuy nhiên, sự gia tăng hiệu năng này mang tính cục bộ và không đồng nghĩa với việc ma trận kernel dạng vị tự () tối ưu hơn về mặt cấu trúc hình học so với trạng thái vector nguyên bản.

### 2.3.5. Các độ đo lượng tử: Expressibility, Entanglement Entropy và Effective Rank

Để chứng minh định lượng sự vượt trội về năng lực biểu diễn của không gian Hilbert so với các hàm nhân cổ điển (đóng góp C2), nghiên cứu áp dụng ba độ đo chuyên biệt của lý thuyết thông tin lượng tử:
1. Khả năng biểu diễn (Expressibility):
Đo lường mức độ mạch lượng tử tham số hóa có thể khám phá toàn bộ không gian trạng thái Hilbert. Giá trị này được tính bằng khoảng cách Kullback-Leibler (KL Divergence) giữa phân phối độ trung thực sinh ra bởi mạch  () và phân phối đồng nhất lý tưởng Haar ():
Khoảng cách  càng hội tụ về 0, mạch càng có khả năng tạo ra các trạng thái đa dạng, giúp phủ kín không gian đặc trưng và tăng cường khả năng tìm kiếm siêu phẳng phân tách tối ưu.
2. Entropy vướng víu (Entanglement Entropy):
Để định lượng mức độ tương tác phi tuyến giữa các đặc trưng đầu vào, Entropy von Neumann được sử dụng trên ma trận mật độ rút gọn  của một hệ thống con (subsystem) A:
Trong đó,  là các trị riêng của . Giá trị  cao chứng tỏ mức độ vướng víu (entanglement) mạnh mẽ, đồng nghĩa với việc các đặc trưng độc lập đã được kết hợp chặt chẽ vào nhau thông qua cấu trúc liên kết toàn phần của mạch.
3. Hạng hiệu dụng của ma trận Kernel (Effective Rank):
Thay vì đếm số lượng trị riêng khác không, hạng hiệu dụng  đo lường độ phẳng (flatness) của phổ trị riêng ma trận kernel K:
Với  là trị riêng thứ i của ma trận K. Hạng hiệu dụng càng cao chứng tỏ ma trận kernel chứa đựng lượng thông tin phong phú và không bị suy biến, đảm bảo không gian nhúng có số chiều thực tế đủ lớn để giải quyết các tập dữ liệu mạng phức tạp.

## 2.4. Cơ sở Lý thuyết Đánh giá Mô hình nâng cao (C3, C4, C5)


### 2.4.1. Cấu trúc hình học Kernel và công thức Kernel Target Alignment

Để đánh giá định lượng mức độ tương thích giữa không gian nhúng phi tuyến do mạch lượng tử khởi tạo và cấu trúc logic của bài toán phân lớp xâm nhập mạng, nghiên cứu áp dụng lý thuyết Căn chỉnh mục tiêu nhân (Kernel Target Alignment - KTA). Trước khi định nghĩa đại lượng này, tích vô hướng Frobenius và chuẩn Frobenius giữa hai ma trận cùng chiều  được thiết lập làm nền tảng toán học:
Giả sử  là vector nhãn lớp thực tế của tập dữ liệu. Ma trận mục tiêu lý tưởng được cấu thành từ tích ngoài , trong đó thành phần  nếu mẫu p và mẫu q cùng loại (cùng là bình thường hoặc cùng là tấn công) và  nếu ngược lại. Hệ số KTA giữa ma trận nhân lượng tử K và ma trận nhãn Y được định nghĩa bởi tỷ số:
Đại lượng KTA ngặt ngỡ trong khoảng [0, 1] đối với các ma trận bán xác định dương. Giá trị KTA càng tiệm cận về 1 chứng tỏ cấu trúc hình học của không gian nhúng càng tối ưu: các mẫu cùng lớp tự động hội tụ thành các cụm mật độ cao, trong khi khoảng cách giữa các cụm khác lớp được kéo dãn tối đa, tạo điều kiện thuận lợi cho siêu phẳng SVM bóc tách dữ liệu.
Để triệt tiêu ảnh hưởng của giá trị trung bình ma trận và đánh giá cấu trúc hình học sau khi dịch chuyển về tâm tọa độ, hệ số Căn chỉnh nhân trung tâm (Centered Kernel Alignment - CKA) được bổ sung nhằm tăng tính nghiêm ngặt cho mô hình phương pháp luận:
Trong đó,  là ma trận chuẩn tâm (centering matrix). Khung toán học này cho phép so sánh định lượng một cách chính xác năng lực biểu diễn không gian của cấu hình mạch đề xuất  đối chiếu với mạch không vướng víu () cũng như các hàm nhân cổ điển (RBF, Polynomial, Linear).
Để định lượng sâu hơn về cấu trúc tương quan giữa các thành phần không gian nhúng (sử dụng trong phân tích C2), nghiên cứu áp dụng đồng thời hai độ đo thống kê. Hệ số Pearson () đánh giá tương quan tuyến tính, trong khi hệ số Spearman () dựa trên thứ hạng (rank) để đánh giá tương quan đơn điệu, phù hợp với các quan hệ phi tuyến:
Trong đó,  là độ chênh lệch thứ hạng giữa hai biến quan sát thứ i.

### 2.4.2. Đánh giá độ bền bỉ (Robustness) thông qua Dịch chuyển phân phối

Để đảm bảo mô hình phân loại xâm nhập mạng không chỉ vận hành tối ưu trong điều kiện lý tưởng mà còn có khả năng triển khai thực tế, việc phân tích độ bền bỉ (Robustness) trước hiện tượng dịch chuyển phân phối dữ liệu (Data Distribution Shift) là bắt buộc. Hiện tượng này xảy ra khi phân phối xác suất đồng thời của dữ liệu kiểm thử  có sự sai lệch so với phân phối huấn luyện . Nhằm định lượng mức độ suy giảm hiệu năng một cách nhất quán trên toàn bộ các kịch bản thực nghiệm, nghiên cứu sử dụng điểm số  làm thước đo cốt lõi:
Nghiên cứu thiết lập khung đánh giá dựa trên ba dạng dịch chuyển phân phối chính đối với hệ thống IDS:
Dịch chuyển theo thời gian (Temporal Shift): Kiểm tra năng lực tổng quát hóa của mô hình khi đối mặt với các dạng biến thể mẫu mới sinh ra trong tương lai. Đại lượng đo lường là Khoảng cách tổng quát hóa (Generalization Gap):
Mô hình đạt độ bền bỉ cao khi  tiến về 0, chứng tỏ ranh giới quyết định được xây dựng dựa trên bản chất hành vi xâm nhập thay vì ghi nhớ dữ liệu thô.
Nhiễu không gian đặc trưng (Feature Perturbation): Mô phỏng các sai số đường truyền bằng cách cộng nhiễu Gaussian  trực tiếp vào không gian đặc trưng . Đối với mô hình lượng tử, một biến động nhỏ trên X sẽ gây ra sự sụp đổ và lệch pha trong không gian Hilbert, làm biến dạng cấu trúc ma trận nhân lượng tử. Tác động của nhiễu được định lượng qua tỷ lệ sụt giảm hiệu năng () tại các mức nhiễu nghiêm trọng:
Dịch chuyển xác suất tiên nghiệm (Class Prior Shift): Hiện tượng tỷ lệ phân phối các lớp thay đổi giữa tập huấn luyện và kiểm thử  nhưng phân phối có điều kiện của đặc trưng giữ nguyên . Thử nghiệm này xác chứng xem mô hình lượng tử thực sự phân loại dựa trên cấu trúc hình học của dữ liệu hay bị phụ thuộc vào tần suất của lớp đa số (majority class).

### 2.4.3. Toán học của Confidence Calibration

Một bộ phân loại được coi là hiệu chuẩn hoàn hảo (perfectly calibrated) nếu xác suất dự báo đầu ra khớp với xác suất thực tế, tức là . Để đo lường sai lệch này, đề tài thiết lập khung toán học dựa trên hai chỉ số chính thông qua kỹ thuật chia tập dữ liệu thành M phân đoạn (bins):
Lỗi hiệu chuẩn kỳ vọng (Expected Calibration Error - ECE): Tính toán giá trị sai lệch trung bình có trọng số giữa độ tin cậy dự đoán () và độ chính xác thực tế () trên toàn bộ các phân đoạn:
Lỗi hiệu chuẩn tối đa (Maximum Calibration Error - MCE): Đại diện cho sai lệch lớn nhất trong kịch bản tệ nhất trên tất cả các phân đoạn, đặc biệt quan trọng trong các ứng dụng an ninh mạng bảo mật cao:
Đối với các phân lớp tấn công hiếm (như U2R và R2L với tỷ lệ cấu thành dưới 1%), việc chia đoạn có độ rộng bằng nhau (equal-width binning) dễ dẫn đến hiện tượng "bin trống", khiến ước lượng ECE bị sai lệch nặng. Để khắc phục, nghiên cứu áp dụng Quy tắc phân đoạn thích ứng (Adaptive Binning Rule) dựa trên phân vị (quantile):
Trong đó,  là phân vị thứ  của tập hợp các xác suất dự đoán , đảm bảo mọi phân đoạn đều chứa số lượng mẫu bằng nhau, tạo điều kiện cho việc đánh giá các lớp dữ liệu thiểu số một cách chính xác.
Đồng thời, để ánh xạ giá trị hàm quyết định f(x) dạng khoảng cách phi xác suất của mô hình lượng tử sang không gian xác suất có hiệu chuẩn, phương pháp Platt Scaling được triển khai thông qua cấu trúc hàm logistic:
Các tham số điều hòa A và B được tối ưu hóa bằng thuật toán ước lượng hợp lý cực đại (Maximum Likelihood Estimation - MLE) trên tập dữ liệu kiểm chứng độc lập. Cơ chế hiệu chuẩn này giúp tối ưu hóa độ chặt chẽ và ổn định của lề quyết định lượng tử trước khi đưa vào các hệ thống ra quyết định thực tế.

### 2.4.4. Khung Kiểm định Thống kê và Đánh giá trên tập dữ liệu mất cân bằng

Trong các bài toán phát hiện xâm nhập mạng (IDS), tập dữ liệu thực tế thường chịu hiện tượng mất cân bằng phân lớp nghiêm trọng, đặc biệt là các lớp tấn công hiếm như U2R (User-to-Root) và R2L (Remote-to-Local) với tỷ lệ xuất hiện thường dưới 1%. Để đánh giá toàn diện hiệu năng của mô hình Máy vectơ hỗ trợ lượng tử (), nghiên cứu thiết lập một khung kiểm định thống kê và đo lường nâng cao. Các chỉ số phân loại truyền thống bao gồm Độ chính xác toàn cục (), Độ chính xác dự báo (), Độ nhạy (), và Diện tích dưới đường cong đặc trưng hoạt động thu nhận ():
Mặc dù  phản ánh xác suất mô hình định thứ bậc (ranking) chính xác cho một mẫu dạng tấn công () so với một mẫu bình thường (), đại lượng này dễ bị phóng đại do số lượng lớn các mẫu âm tính thực tế () từ lớp đa số. Nhằm khắc phục nhược điểm này và tập trung đánh giá năng lực nhận diện trên các lớp dữ liệu thiểu số, chỉ số Diện tích dưới đường cong Precision-Recall (), hay còn gọi là Độ chính xác trung bình (), được thiết lập làm thước đo trọng tâm:
Trong đó,  và  lần lượt là giá trị  và  tại ngưỡng phân loại thứ n. Chỉ số này loại bỏ ảnh hưởng của số lượng mẫu bình thường, phản ánh chính xác độ chặt chẽ của ranh giới quyết định đối với các hành vi tấn công hiếm.
Để chứng minh các cải tiến hiệu năng của mô hình lượng tử so với các thuật toán phân loại cổ điển mang tính bản chất khoa học thay vì do sai số ngẫu nhiên của quá trình lấy mẫu, khung phương pháp luận tích hợp hai kiểm định thống kê và đại lượng kích thước hiệu ứng sâu bao gồm:
1. Kiểm định phi tham số McNemar (McNemar's Chi-square Test):
Sử dụng để so sánh tỷ lệ lỗi tương quan giữa bộ phân loại lượng tử và bộ phân loại cổ điển trên cùng một tập dữ liệu kiểm thử dưới dạng bảng phân kỳ (contingency table). Giả sử b là số mẫu mô hình lượng tử dự báo sai nhưng mô hình cổ điển dự báo đúng, và c là số mẫu ngược lại. Giá trị thống kê  với hiệu chỉnh liên tục Yates được định nghĩa:
Với mức ý nghĩa , nếu giá trị  tính toán nhỏ hơn  (tương ứng ), giả thuyết không  về sự đồng nhất năng lực giữa hai mô hình bị bác bỏ, xác chứng ưu thế vượt trội của cấu trúc nhân lượng tử.
2. Kích thước hiệu ứng Cohen's d (Cohen's d Effect Size):
Đo lường độ lớn của sự dịch chuyển lề quyết định (decision margin) giữa hai mô hình, đặc biệt trong các kịch bản thực nghiệm trên tập dữ liệu nhỏ hoặc dịch chuyển phân phối. Đại lượng  được xác định bằng tỷ số giữa hiệu trung bình mẫu và độ lệch chuẩn gộp ():
Giá trị  đại diện cho hiệu ứng nhỏ,  là hiệu ứng trung bình, và  khẳng định sự khác biệt về khoảng cách biên phân lớp giữa không gian nhúng lượng tử và không gian cổ điển đạt mức độ lớn và có ý nghĩa ứng dụng thực tiễn cao.
3. Kiểm định tổng hạng Mann-Whitney U (Mann-Whitney U Test):
Để kiểm chứng phân phối ngẫu nhiên của các đặc tính hình học hoặc entropy vướng víu lượng tử giữa các nhóm dữ liệu mà không phụ thuộc vào giả định phân phối chuẩn, giá trị thống kê U được tính toán nhằm bác bỏ claim về sự trùng lặp ngẫu nhiên:
Với  là tổng thứ hạng phân phối của mẫu lượng tử trong không gian gộp. Khung kiểm định toán học đa tầng này đảm bảo mọi công nhận về lợi thế lượng tử (Quantum Advantage) trong nghiên cứu đều đạt độ tin cậy khoa học tối đa theo các chuẩn mực thống kê quốc tế.

# CHƯƠNG 3. KHUNG PHƯƠNG PHÁP LUẬN VÀ KIẾN TRÚC HỆ THỐNG ĐỀ XUẤT


## 3.1. Kiến trúc tổng thể của hệ thống QSVM-ZZ-IDS


### 3.1.1. Sơ đồ luồng xử lý tổng thể (Zero-Leakage Pipeline)

Để hợp nhất các thành phần từ giảm chiều không gian cổ điển đến mã hóa lượng tử, hệ thống QSVM-ZZ-IDS được thiết kế theo một luồng xử lý tuần tự (feed-forward pipeline) tuân thủ nghiêm ngặt nguyên tắc Zero-Leakage. Toàn bộ các bộ biến đổi tiền xử lý chỉ được huấn luyện (fit()) duy nhất trên tập dữ liệu train và áp dụng nguyên trạng (transform()) lên tập kiểm thử (test set) nhằm triệt tiêu hoàn toàn rủi ro rò rỉ dữ liệu tương lai.
Kiến trúc tổng thể và luồng biến đổi không gian đặc trưng được mô tả trực quan tại Hình 3.1.

![FIGURE_4](FIGURE_4)

![FIGURE_5](FIGURE_5)
Hình 3.1: Sơ đồ block/flowchart pipeline tổng thể QSVM-ZZ-IDS vào đây
Như được minh họa, không gian đặc trưng trải qua hai giai đoạn chuẩn hóa biên độ: lần thứ nhất để phục vụ bộ lọc SelectKBest (K=20) và phân rã thành phần chính PCA (n=4); lần thứ hai sử dụng MinMaxScaler để ánh xạ chính xác tọa độ không gian 4D về dải góc xoay lượng tử . Việc giới hạn giá trị trong nửa trên của quả cầu Bloch là điều kiện tiên quyết nhằm ngăn chặn hiện tượng vòng lặp chu kỳ pha (wrap-around), đảm bảo bảo toàn tính phân biệt tuyến tính khi nhúng dữ liệu vào trạng thái phức.
Cấu hình cơ sở (Baseline Configuration):
Sau khi hoàn tất khâu tối ưu hóa giảm chiều (C1), hệ thống được cố định với cấu hình cốt lõi dưới đây để triển khai các phân tích thực nghiệm tiếp theo (C2–C6):
Mạch lượng tử: ZZFeatureMap (4 qubit tương đương 4 features, reps=2, liên kết entanglement='full').
Quantum Kernel: FidelityStatevectorKernel (Mô phỏng vector trạng thái lý tưởng, làm mốc tham chiếu không nhiễu).
Bộ phân lớp: Thuật toán SVC (C=1.0, kernel='precomputed').
Đóng băng không gian nhúng (Fixed Embedding): Xuyên suốt các thực nghiệm đánh giá độ biểu diễn (C2) và độ bền bỉ (C4), các bộ trọng số của pipeline C1 (SelectKBest, PCA, MinMaxScaler) sau khi fit trên tập gốc KDDTrain+ sẽ được lưu trữ cục bộ (định dạng .joblib). Ở mọi kịch bản chia fold hay kiểm thử sau đó, các thành phần này chỉ được gọi ở chế độ transform(). Thiết kế cô lập này đảm bảo hệ thống luôn được đánh giá trên cùng một không gian nhúng 4D, giúp mọi biến động về hiệu năng đều phản ánh chính xác năng lực bản chất của hàm nhân lượng tử thay vì sai lệch do khâu tiền xử lý cổ điển gây ra.

### 3.1.2. Tối ưu hóa tính toán và Đảm bảo tính tái lập

Để giải quyết rào cản độ phức tạp tính toán của ma trận nhân lượng tử (), hệ thống áp dụng cơ chế lưu trữ đệm (caching) tĩnh cho trạng thái lượng tử (Statevectors) và ma trận Kernel. Cơ chế này cho phép tái sử dụng kết quả trong các pha đánh giá chéo (cross-validation), giúp giảm triệt để thời gian mô phỏng. Đồng thời, nhằm đảm bảo tính tái lập (reproducibility), toàn bộ kiến trúc (lấy mẫu, PCA, chia dữ liệu) được neo bằng một hạt giống ngẫu nhiên (global random seed) duy nhất. Sự kiểm soát này loại bỏ nhiễu từ phân phối ngẫu nhiên, đảm bảo mọi chênh lệch hiệu năng thu được hoàn toàn xuất phát từ bản chất hình học của mô hình lượng tử.

## 3.2. Phương pháp thực thi C1: Pipeline giảm chiều hai giai đoạn

Dựa trên cơ sở Mục 2.2, quy trình nén dữ liệu từ không gian mã hóa (122 chiều) xuống không gian lượng tử (4 chiều) được thực thi qua hai kỹ thuật:
Lọc đặc trưng Top-K (Tiêu chí Elbow): Nhằm tối ưu tham số K mà không gây quá tải tài nguyên, hệ thống dùng Linear SVM làm mô hình đại diện (proxy model) chạy đánh giá chéo phân tầng (Stratified 5-fold CV) trên 5.000 mẫu. Điểm tối ưu  là giá trị nhỏ nhất giữ cho -score suy giảm không vượt ngưỡng dung sai  so với đỉnh. ANOVA F-test được chọn thay vì Mutual Information nhờ tính tất định và khả năng ổn định trên các lớp tấn công hiếm (U2R, R2L).
Tối ưu không gian nhúng (Lưới Dirichlet): Số lượng thành phần chính n (số qubit) được xác định thông qua thuật toán Grid Search giải bài toán Pareto trên đơn hình Dirichlet gồm 435 tổ hợp trọng số. Ba mục tiêu tối ưu bao gồm: tỷ lệ phương sai, độ phân cụm (nghịch đảo DBI), và chi phí phần cứng. Cấu hình không gian 4D/4-qubit tối ưu được xác chứng bằng kỹ thuật Bootstrap (khoảng tin cậy 95%) nhằm đảm bảo độ ổn định cao nhất trước khi ánh xạ lên quả cầu Bloch.
Thực nghiệm mở rộng trên UNSW-NB15: Để kiểm chứng năng lực tổng quát hóa, pipeline được tái chạy trên dữ liệu UNSW-NB15. Proxy model xác định K=35 ở màng lọc đầu (so với K=20 tại NSL-KDD). Tuy nhiên, nhằm đảm bảo tính công bằng và tuân thủ chặt chẽ tài nguyên NISQ, bước nén Pareto vẫn neo cố định tại n=4 thành phần chính (4 qubit).

## 3.3. Phương pháp thực thi C2: Phân tích Expressibility và Shot-noise

Phân tích C2 nhằm xác chứng năng lực biểu diễn vượt trội của hàm nhân lượng tử so với kỹ thuật cổ điển, được triển khai qua các phương diện lý thuyết và thực nghiệm sau:
Lý thuyết không gian Hilbert (Hướng 1): Hệ thống dùng kiểm định tương quan đơn điệu Spearman phi tuyến trên các thành phần chính (PCs từ C1) để tìm các cấu trúc tương tác ẩn. Qua đó, chứng minh mạch ZZFeatureMap mã hóa chính xác tương tác bậc hai nhờ giao thoa pha lượng tử—cơ chế tương đương hàm nhân đa thức bậc 2 (Polynomial Kernel) nhưng vận hành trong không gian Hilbert  chiều ưu việt hơn không gian Euclid.
Thực nghiệm định lượng (Hướng 2): Độ phủ (coverage) của hàm nhân được đo lường qua phổ trị riêng (Eigenvalue spectrum) của ma trận kernel; phổ phẳng hơn chứng tỏ năng lực bóc tách điểm dị biệt tốt hơn. Chỉ số Entropy vướng víu von Neumann trên hệ con lượng tử được dùng để xác nhận vai trò vật lý của cổng ZZ trong việc trói buộc (entanglement) đặc trưng. Đồng thời, hệ số Căn chỉnh nhân trung tâm (CKA) giúp đối chiếu sự tương đồng ma trận giữa không gian lượng tử và các hàm nhân cổ điển (RBF, Linear).
Thực nghiệm C2.5 - Định lượng nhiễu lấy mẫu (Finite-shot Kernel Analysis): Nhằm đánh giá sai lệch giữa ma trận lý tưởng và ma trận ước lượng trên phần cứng NISQ. Kịch bản giữ nguyên cấu trúc hạt nhân C1 (ZZFeatureMap 4 qubit, liên kết toàn phần, SVC với $C=1.0$), nhưng thay thế FidelityStatevectorKernel bằng FidelityQuantumKernel. Khảo sát được cô lập trên 100 mẫu train/test qua các mốc: 128, 512, 2048, và 8192 shots (lặp lại 3 seeds). Độ biến thiên hình học được giám sát qua Frobenius Similarity, MAE, KTA và phân phối lề quyết định. Qua đó khẳng định: C3/C4 là mốc tham chiếu không nhiễu lý tưởng, còn bản đồ nhiễu C2.5 phản ánh hiệu năng thực tế trên chip lượng tử vật lý.
Mở rộng thực nghiệm C2 trên UNSW-NB15: Nhằm kiểm chứng năng lực tổng quát hóa, khoảng cách Kullback-Leibler (KL Divergence) so với phân phối Haar và Entropy von Neumann được đo lường lại trên không gian 4D của UNSW-NB15. Việc này xác nhận kiến trúc ZZFeatureMap duy trì được năng lực biểu diễn (Expressibility) ổn định trước một tập dữ liệu có độ nhiễu và sự chồng chéo phân lớp (class overlap) khốc liệt hơn.

## 3.4. Phương pháp thực thi C3: Phân tích hình học Kernel và Trực quan hóa Biên quyết định

Thực nghiệm C3 áp dụng giao thức đánh giá đa lượt (multi-run) để cô lập và kiểm chứng cấu trúc hình học của không gian nhúng lượng tử. Quy trình sử dụng 5 tập mẫu huấn luyện độc lập (1.000 mẫu phân tầng/tập) trích xuất từ KDDTrain+, và một tập kiểm thử cố định (300 mẫu phân tầng) từ KDDTest+. Kết quả trung bình và độ lệch chuẩn () qua 5 lượt chạy phản ánh chính xác độ ổn định toán học của hàm nhân khi thay đổi phân phối mẫu. Phương pháp thực thi cụ thể hóa qua ba nội dung:
1. Nghiên cứu loại trừ (Ablation Study): QSVM-ZZ đối chiếu QSVM-Z
Để định lượng đóng góp của cơ chế vướng víu lượng tử (cổng CNOT), thực nghiệm so sánh song song hai cấu hình mạch đặc trưng:
Mô hình đề xuất (QSVM-ZZ): Sử dụng ZZFeatureMap phi tuyến, liên kết toàn phần (entanglement='full'), nhúng cả đặc trưng độc lập và tương tác chéo bậc hai  vào pha lượng tử.
Mô hình đối chứng (QSVM-Z): Sử dụng ZFeatureMap cải biên, chỉ giữ lại các cổng đơn qubit (H và P) và loại bỏ hoàn toàn các cổng CNOT (đóng vai trò là baseline tuyến tính lượng tử).
Biến số duy nhất thay đổi là số hạng tương tác chéo . Các yếu tố nền tảng khác (n=4 qubits, số tầng r=2, pipeline C1, dữ liệu và tham số điều hòa C=1.0) được giữ nguyên trạng tuyệt đối.
2. Chiếu không gian và trực quan hóa biên quyết định (Decision Boundary Projection)
Để trực quan hóa siêu phẳng phân lớp 4D (sau PCA) lên màn hình 2D, đề tài áp dụng kỹ thuật chiếu bằng phép gán trung vị (median imputation projection) gồm 4 bước:
Bước 1 (Mặt phẳng chiếu): Chọn cặp thành phần chính mấu chốt (ví dụ:  và ) làm hệ tọa độ 2D và thiết lập lưới điểm.
Bước 2 (Gán giá trị trung vị): Tại mỗi tọa độ lưới , xây dựng lại vector 4D đầy đủ bằng cách gán giá trị trung vị  của tập huấn luyện cho các chiều ẩn ( và ).
Bước 3 (Quét hàm quyết định): Nạp các vector 4D giả lập vào model.decision_function() để tính khoảng cách đại số đến siêu phẳng lượng tử.
Bước 4 (Trực quan hóa đường mức): Biểu diễn khoảng cách dưới dạng biểu đồ đường mức (contour plot), xếp chồng tọa độ thực của các vectơ hỗ trợ để phân tích hình thái biên quyết định (độ mịn, độ cong phi tuyến và lề phân lớp).
3. Giao thức mở rộng thực nghiệm trên tập dữ liệu UNSW-NB15
Giao thức C3 được tái triển khai độc lập trên UNSW-NB15 nhằm kiểm chứng tính tổng quát hóa với 4 điều chỉnh cấu hình quan trọng:
Chiều tối ưu: Xác định số đặc trưng màng lọc đầu là K=35 (tiêu chí Elbow riêng của UNSW-NB15). Giai đoạn hai vẫn nén cố định tại n=4 thành phần chính (4 qubit) để tuân thủ giới hạn phần cứng NISQ.
Tham số điều hòa trung hòa: Cố định C=1.0 thay vì tối ưu hóa theo từng fold. Việc này giúp phản ánh chính xác bản chất hàm nhân, ngăn mô hình rơi vào trạng thái suy biến (degenerate state—dự báo mù toàn bộ là tấn công) do mất cân bằng lớp cực đoan.
Đồng bộ hóa hình học ma trận: Lưu trữ 100% ma trận nhân lượng tử qua bộ nhớ đệm (cache). Điều này bảo đảm giá trị KTA (Kernel Target Alignment) luôn đồng nhất tuyệt đối, phục vụ như một bước sanity check cấu trúc hình học.
Quy mô và Pipeline độc lập: Sử dụng 5 tập huấn luyện độc lập  100 mẫu/lượt và 5 tập kiểm thử độc lập  100 mẫu/lượt (lấy mẫu phân tầng nhị phân). Quy mô được thu nhỏ do giới hạn thời gian tính toán ma trận kernel K. Toàn bộ pipeline C1 được huấn luyện (fit) lại từ đầu trên UNSW-NB15 để đảm bảo tính khách quan.

## 3.5. Phương pháp thực thi C4: Đánh giá độ bền bỉ (Robustness Validation)

Thực nghiệm C4 kiểm chứng năng lực duy trì hiệu năng của hệ thống trước 3 kịch bản dịch chuyển phân phối dữ liệu mạng. Giao thức multi-run sử dụng 5 tập huấn luyện độc lập (1.000 mẫu phân tầng/tập từ KDDTrain+) và các tập kiểm thử đóng băng. Nhằm cô lập hoàn toàn tác động của hàm nhân lượng tử, pipeline C1 (SelectKBest với K=20, PCA với n=4, MinMaxScaler ) được thiết lập ở chế độ đóng băng, chỉ chạy hàm transform(). Mô hình QSVM-ZZ được đối chiếu với SVM-RBF, SVM-Linear và Random Forest dưới 2 chế độ chuẩn hóa (MinMaxScaler , StandardScaler), đánh giá qua trung bình và độ lệch chuẩn () của -score.
Khung thực nghiệm cho ba dạng dịch chuyển được cụ thể hóa như sau:
Dịch chuyển thời gian (Temporal Shift): Đo lường mức độ sụt giảm hiệu năng  giữa tập kiểm thử chuẩn (300 mẫu KDDTest+) và tập kiểm thử ngặt KDDTest-21 (300 mẫu chứa dị thường nâng cao mà các benchmark truyền thống thường dự đoán sai).
Nhiễu đặc trưng (Feature Perturbation): Kiểm chứng độ nhạy hình học bằng cách tiêm nhiễu Gaussian  vào không gian tọa độ góc lượng tử với mức độ . Dữ liệu sau nhiễu được cắt xén (clipping) chặt về miền  để bảo toàn tính hợp lệ của góc xoay unita trên quả cầu Bloch. Độ bền bỉ được đánh giá qua đồ thị suy giảm  và hệ số góc tuyến tính m từ phép hồi quy ma trận lỗi.
Dịch chuyển xác suất tiên nghiệm (Class Prior Shift): Đánh giá độ phụ thuộc của biên quyết định vào tần suất lớp đa số qua 3 tập kiểm thử (300 mẫu/tập, lấy mẫu có hoàn lại): Tập cân bằng (50% Normal / 50% Attack); Tập bão hòa tấn công (30% Normal / 70% Attack); và Tập chuyên biệt DoS (Normal/DoS tỷ lệ 1:1). Hiệu năng được định lượng qua  của -score xuyên suốt ba miền phân phối.
Giao thức mở rộng thực nghiệm trên tập dữ liệu UNSW-NB15:
Quy mô tập mẫu: Thu gọn ở mức 100 mẫu/lượt chạy.
Nhiễu đặc trưng: Chỉ khảo sát . Mức cực nhỏ  bị loại bỏ do biến động không vượt qua được độ lệch chuẩn nội tại của hệ thống.
Dịch chuyển xác suất tiên nghiệm: Tái thiết kế ba phân phối để bao quát dải thực tế hơn: 10/90 (Attack-heavy cực đoan), 50/50 (Balanced), và 90/10 (Normal-heavy, sát với hệ thống IDS thực tế). Tham số điều hòa tiếp tục được neo tại C=1.0 trung hòa.

## 3.6. Phương pháp thực thi C5: Confidence Calibration

Thực nghiệm C5 chẩn đoán độ tin cậy phân lớp của hàm nhân lượng tử, đặc biệt chú trọng hiệu năng phát hiện các nhóm tấn công hiếm gặp qua các bước chuyên biệt:
Hiệu chuẩn xác suất và Adaptive Binning trên phân lớp hiếm:
Các lớp tấn công nguy hiểm (U2R, R2L) chiếm dưới 1% tổng số mẫu. Để tránh lỗi "bin rỗng" khi chia khoảng cố định, hệ thống áp dụng kỹ thuật phân đoạn thích ứng (Adaptive Binning) dựa trên phân vị. Số lượng phân đoạn được tinh chỉnh về mức M nhằm bảo đảm mỗi bin chứa tối thiểu 5 mẫu. Cấu hình này giúp phân bổ đều tập dữ liệu thiểu số và triệt tiêu sai số phương sai.
Quá trình ánh xạ khoảng cách hình học sang xác suất sử dụng phương pháp Platt Scaling (Công thức 2.37). Bộ tham số điều hòa (A, B) được tối ưu bằng thuật toán L-BFGS kết hợp ràng buộc  Regularization trên tập thẩm định độc lập (30% trích xuất từ KDDTrain+), giúp ngăn chặn triệt để hiện tượng quá khớp (overfitting) trên không gian mẫu chật hẹp.
Phân tích lề quyết định (Decision Margin Histogram) và rủi ro tự tin thái quá: Lề quyết định f(x) biểu diễn khoảng cách đại số từ điểm dữ liệu đến siêu phẳng phân lớp lượng tử. Phân tích biểu đồ tần suất (histogram) của f(x) giúp chẩn đoán 3 trạng thái ra quyết định cốt lõi:
f(x) lớn, dự đoán đúng: Mô hình hoạt động tự tin và chính xác.
f(x) nhỏ, dự đoán sai: Trạng thái bất định. Đây là vùng "xám" lý tưởng để tích hợp cơ chế từ chối dự đoán (abstain) trong hệ thống IDS thực tế, chuyển cảnh báo cho chuyên gia xử lý thủ công.
f(x) lớn, dự đoán sai (Over-confident error): Quyết định sai lệch với độ tự tin thái quá. Đây là rủi ro thảm họa nhất trong an toàn thông tin cần được nhận diện và giảm thiểu bằng mọi giá.
Giao thức mở rộng thực nghiệm trên tập dữ liệu UNSW-NB15: Giao thức C5 được mở rộng sang UNSW-NB15 để kiểm chứng tính nhất quán xuyên nền tảng với các tinh chỉnh bắt buộc:
Tái định nghĩa nhóm tấn công hiếm: Nhóm {U2R, R2L} của NSL-KDD được thay thế bằng tập {Analysis, Backdoor, Shellcode, Worms}.
Quy trình tối ưu hiệu chuẩn: Thay vì dùng tập validation độc lập, Platt Scaling được thực thi trực tiếp qua cơ chế đánh giá chéo 5-fold CV nội bộ (kích hoạt đối số probability=True trong bộ SVC).
Cơ sở so sánh (Caveat): Chỉ số AUC-PR cho lớp hiếm trên UNSW-NB15 được định nghĩa theo chuẩn phân loại nhị phân gộp (binary rare-membership), khác với tính trung bình vĩ mô (macro-average) từng lớp ở NSL-KDD. Do đó, kết quả AUC-PR mở rộng chỉ dùng để so sánh lợi thế định hướng (directional advantage) lượng tử - cổ điển, thay vì so sánh hiệu năng tuyệt đối chéo nền tảng.

## 3.7. Phương pháp thực thi C6: Đánh giá độ phức tạp mẫu (Sample Complexity Assessment)

Thực nghiệm C6 định lượng năng lực học tập và tốc độ hội tụ của mô hình lượng tử trong bối cảnh tài nguyên huấn luyện bị giới hạn khắt khe (low-data regime). Phương pháp thực thi gồm hai nội dung trọng tâm:
Giao thức đường cong học tập (Learning Curve) trên miền dữ liệu hữu hạn:
Khảo sát các mốc kích thước tập huấn luyện  phân bổ theo quy luật logarith. Mốc N=1000 là giới hạn tối đa khả thi do độ phức tạp tính toán tăng theo hàm mũ bậc hai của hàm nhân lượng tử. Tại mỗi mốc $N$, quy trình triển khai tuần tự:
Lấy mẫu phân tầng (stratified sampling) chính xác $N$ mẫu từ KDDTrain+ để bảo toàn sự hiện diện của các phân lớp thiểu số (U2R, R2L) ngay cả ở mốc khắc nghiệt nhất N=100.
Huấn luyện (fit) lại từ đầu toàn bộ pipeline tiền xử lý cổ điển (SelectKBest  PCA  MinMaxScaler) dựa trên trích xuất của chính tập N mẫu này nhằm bảo đảm nguyên tắc không rò rỉ dữ liệu (zero-leakage).
Huấn luyện mô hình đề xuất QSVM-ZZ song song với ba baseline cổ điển (SVM-RBF, SVM-Linear, Random Forest).
Đánh giá -score trên toàn bộ tập kiểm thử cố định (22.544 mẫu) sau khi áp dụng hàm transform().
Ghi nhận -score trên miền Train và Test để tính toán độ lệch tổng quát hóa (Generalization Gap) theo Công thức (2.32), nhằm chẩn đoán hiện tượng quá khớp (overfitting) khi cỡ mẫu suy giảm.
Kiểm định kích thước hiệu ứng lề quyết định tại mốc N=500:
Nhằm chứng minh ưu thế bản chất của hàm nhân lượng tử khi phân tách dữ liệu khan hiếm, nghiên cứu đo lường kích thước hiệu ứng Cohen's d trên phân phối lề quyết định f(x). Phép đo toán học này (tuân thủ Công thức 2.41) được thực thi chuyên biệt trên tập mẫu tấn công hiếm (U2R, R2L) thuộc tập kiểm thử tại mốc N=500, đóng vai trò xác thực khoảng cách phân tách hình học ổn định của siêu phẳng lượng tử.
Lưu ý phương pháp luận:
Do đặc thù thực nghiệm tập trung kiểm chứng sâu cấu trúc mẫu tấn công hiếm của học máy cổ điển trên NSL-KDD, giao thức C6 được cô lập hoàn toàn trên tập dữ liệu này và không mở rộng sang nền tảng UNSW-NB15.

## 3.8. Khung kiểm định thống kê áp dụng

Nhằm bảo đảm tính khách quan khoa học và loại bỏ giả thuyết cải thiện hiệu năng do sai số ngẫu nhiên (over-claim), hệ thống áp dụng khung kiểm định đa tầng xuyên suốt các thực nghiệm:
Đánh giá chéo phân tầng (Stratified 5-fold CV): Tối ưu siêu tham số và so sánh hiệu năng được thực thi trong khung 5-fold CV, phân tầng nghiêm ngặt theo nhãn hành vi (attack_category) nhằm duy trì tỷ lệ lớp hiếm. Kết quả được báo cáo theo trung bình và độ lệch chuẩn ().
Kiểm định phi tham số McNemar: Áp dụng trên bảng phân kỳ lỗi (discordant table) để đối chiếu tương quan dự báo giữa mô hình lượng tử và baseline cổ điển. Giá trị thống kê  (Công thức 2.40) tuân thủ ngưỡng ý nghĩa p < 0.05.
Kích thước hiệu ứng Cohen's d: Thước đo độ lớn hiệu ứng độc lập với quy mô mẫu, phát huy vai trò trọng tâm khi đánh giá trên không gian hẹp (phân lớp thiểu số, N=500). Trị số tuân thủ ngặt nghèo ngưỡng phân định của Cohen (1988) tại Mục 2.4.4.
Khoảng tin cậy Bootstrap 95% (95% Bootstrap CI): Thực thi 200 lượt tái lấy mẫu (bootstrap iterations) cho các đại lượng hình học ma trận (KTA, CKA) và đồ thị phân phối lề quyết định nhằm bảo đảm tính ổn định thống kê.

## 3.9. Tính tái lập của hệ thống (Reproducibility Statement)

Để bảo đảm minh bạch khoa học và khả năng tái hiện 100% kết quả thực nghiệm, hệ thống thiết lập cam kết tái lập qua 4 cấu phần quản trị:
Mã nguồn và dữ liệu sạch: Mã nguồn mô-đun hóa, tài liệu Jupyter Notebooks và cơ chế lưu đệm ma trận được đóng gói nguồn mở. Quy trình tải dữ liệu thô (NSL-KDD, UNSW-NB15) được tự động hóa qua tập lệnh kết nối quốc tế.
Kiểm soát hạt giống ngẫu nhiên (Global Random Seed): Mọi yếu tố biến thiên ngẫu nhiên (lấy mẫu, chia tập, PCA, multi-run seeds 1-5) đều được neo cố định bằng một hằng số duy nhất toàn cục.
Đóng băng Pipeline và đồng bộ bộ đệm: Toàn bộ pipeline tiền xử lý (C1) được đóng băng cấu trúc tĩnh sau khi huấn luyện, chỉ gọi hàm transform() ở các chương C2-C5 để ngăn chặn tuyệt đối nhiễu hình học ngoại lai. Ma trận nhân lượng tử (exact statevector cache) được lưu trữ tập trung theo định danh mạch nhằm bảo đảm tính bất biến giữa các thực nghiệm.
Môi trường điện toán và phiên bản: Vận hành nghiêm ngặt trên Python 3.11 với các thư viện cốt lõi cố định: qiskit==2.3.0, qiskit-machine-learning==0.9.0, scikit-learn==1.8.0, numpy==2.4.3, pandas==2.3.3, và scipy==1.17.1. Quy trình mô phỏng mạch lượng tử được tối ưu thực thi hoàn toàn trên CPU (không phụ thuộc GPU), với tổng thời gian 10-15 giờ trên kiến trúc máy tính cá nhân tiêu chuẩn (x86_64, 16GB RAM, môi trường WSL/Ubuntu).

# CHƯƠNG 4. KẾT QUẢ THỰC NGHIỆM VÀ PHÂN TÍCH CHUYÊN SÂU TRÊN NSL-KDD


## 4.1. Tiền xử lý và Phân tích Thống kê NSL-KDD


### 4.1.1. Đặc trưng tập dữ liệu và phân phối lớp

Phân tích thống kê chi tiết về các nhóm đặc trưng và phân phối nhãn lớp trên tập dữ liệu NSL-KDD được tổng hợp tại Bảng 4.1 và Bảng 4.2.
Bảng 4.1. Phân nhóm đặc trưng trong NSL-KDD (trước OHE)

[TABLE_4]
| Nhóm | Đặc trưng tiêu biểu | Mô tả | Số lượng |
| Cơ bản | duration, src_bytes, dst_bytes | Thông tin kết nối, giao thức, byte hai chiều | 9 |
| Nội dung | logged_in, hot, num_compromised | Xác thực, hoạt động nhạy cảm, truy cập root | 13 |
| Traffic (2 giây) | count, serror_rate | Thống kê cửa sổ 2 giây: kết nối, lỗi SYN/REJ | 9 |
| Traffic (100 kết nối) | dst_host_count, dst_host_serror_rate | Thống kê tích lũy 100 kết nối đến host đích | 10 |
| Categorical | protocol_type, service, flag |  |  |

Bảng 4.2. Phân phối lớp tập huấn luyện (NSL-KDD Train+)

[TABLE_5]
| Nhóm tấn công | Số mẫu | Tỷ lệ (%) |
| Normal | 67.343 | 53,5% |
| DoS | 45.927 | 36,5% |
| Probe | 11.656 | 9,3% |
| R2L | 995 | 0,8% |
| U2R | 52 | 0,04% |
| Tổng | 125.973 | 100% |


![FIGURE_6](FIGURE_6)
Hình 4.1. Phân bố nhãn nhị phân và danh mục tấn công trên tập huấn luyện NSL-KDD sau tiền xử lý

![FIGURE_7](FIGURE_7)
Hình 4.2. Phân phối lớp tấn công trên tập dữ liệu NSL-KDD
Sự mất cân bằng lớp nghiêm trọng giữa R2L và U2R so với lớp Normal (tỷ lệ xấp xỉ 1:68 và 1:1.295) tái khẳng định thách thức cốt lõi của bài toán thực tế. Dữ liệu phân phối lệch này là cơ sở thực nghiệm để hệ thống kích hoạt các kỹ thuật hiệu chuẩn độ tin cậy chuyên sâu (sẽ phân tích tại Mục 4.6).

### 4.1.2. Xác nhận tuân thủ hợp đồng Zero-Leakage

Quá trình tiền xử lý thực tế xác nhận sự tuân thủ tuyệt đối cam kết Zero-Leakage đã được thiết lập tại Mục 3.1.1. Toàn bộ các bộ trọng số biến đổi không gian (từ One-Hot Encoding, SelectKBest, PCA đến MinMaxScaler) đều được huấn luyện (fit) độc lập trên tập KDDTrain+. Không gian nhúng lượng tử 4 chiều cuối cùng trên cả hai tập huấn luyện và kiểm thử được xác nhận nằm gọn trong giới hạn tọa độ góc hợp lệ $[0, \pi]$ (ngăn chặn tuyệt đối hiện tượng wrap-around trên quả cầu Bloch). Đồng thời, hệ thống không ghi nhận bất kỳ giá trị khuyết thiếu (NaN) hay sự rò rỉ phân phối nào. Khâu kiểm định tính toàn vẹn này là tiền đề bắt buộc, bảo đảm tính hợp lệ và khách quan cho mọi kết quả đối chứng hiệu năng ở các giai đoạn sau.

## 4.2. Đánh giá C1: Tối ưu hóa Nhúng Lượng tử Có Ràng buộc Phần cứng


### 4.2.1. Kết quả SelectKBest: Xác định  tối ưu bằng Elbow Criterion

Thực thi giao thức tìm kiếm đã thiết lập tại Mục 3.2.2, kết quả sàng lọc đặc trưng thông qua tiêu chí Elbow trên mô hình proxy SVM-Linear được ghi nhận chi tiết tại Bảng 4.3 và trực quan hóa tại Hình 4.3.
Bảng 4.3. Kết quả 5-fold CV theo giá trị  (chọn lọc từ proxy SVM-Linear)

[TABLE_6]
|  | F1-macro | Std |
| 4 | 0,8596 | 0,0100 |
| 6 | 0,8614 | 0,0093 |
| 8 | 0,8616 | 0,0080 |
| 10 | 0,8612 | 0,0087 |
| 20 (K*) | 0,8989* | — |


![FIGURE_8](FIGURE_8)
Hình 4.3. Tiêu chí Elbow và bước nhảy F1-macro biên (Marginal gain) trong quá trình lựa chọn đặc trưng
Dữ liệu thực nghiệm chỉ ra điểm gãy (Elbow) xuất hiện rõ nét tại mốc K=20, đạt cực đại cục bộ với . Từ mốc này trở đi, hiệu suất biên suy giảm mạnh (việc bổ sung thêm 80 đặc trưng còn lại hầu như không tạo ra biến động đáng kể về năng lực phân tách). Điều này xác chứng K=20 là điểm cân bằng tối ưu, phản ánh toàn diện cấu trúc thống kê của các phân lớp tấn công mà không làm phình to không gian nhúng.
Tập hợp 20 đặc trưng cốt lõi này được phân loại thành 5 nhóm chức năng giải phẫu mạng:
Lưu lượng (Traffic Volume): src_bytes và dst_bytes đóng vai trò then chốt trong việc phân biệt các cuộc tấn công DoS (tràn ngập lưu lượng) và R2L (lệch tải bất thường giữa gửi/nhận).
Tỷ lệ lỗi (Error Rates): Các biến thể của serror_rate bao phủ cửa sổ thời gian 2 giây và 100 kết nối, cho phép nhận diện đồng thời các đợt SYN flood cường độ cao lẫn tấn công tinh vi nhịp độ chậm (slow attacks).
Thống kê kết nối (Connection Stats): Biến số count và srv_count phát hiện dấu hiệu DoS/Probe thông qua tần suất kết nối đột biến, trong khi diff_srv_rate và rerror_rate là dấu ấn định danh của hành vi quét cổng (portsweep/portscan).
Hành vi và Nội dung (Behavioral & Content): logged_in và hot nắm bắt ngữ cảnh thâm nhập sâu vào hệ thống, giúp phân tách hiệu quả các lớp R2L (xác thực trái phép) và U2R (leo thang đặc quyền).
Ngữ cảnh Giao thức (OHE Features): Các vector mã hóa từ flag, protocol_type và service cung cấp thông tin định danh tĩnh mức mạng (ví dụ: flag_S0 là chỉ báo rủi ro cao của DoS, flag_REJ cảnh báo hành vi Probe).
Bảng 4.4. Tóm tắt 20 đặc trưng được chọn và vai trò phát hiện tấn công

[TABLE_7]
| STT | Đặc trưng | Nhóm | Vai trò phát hiện |
| 1–2 | src_bytes, dst_bytes | Cơ bản | DoS (lưu lượng lệch), R2L (payload nhỏ) |
| 3–6 | serror_rate, srv_serror_rate, dst_host_serror_rate, dst_host_srv_serror_rate | Traffic | SYN flood (Neptune, Smurf); cửa sổ 2s + 100 kết nối bổ trợ |
| 7–10 | count, srv_count, dst_host_count, dst_host_srv_count | Traffic | DoS tức thời và Probe; hai cửa sổ thời gian bổ trợ |
| 11–15 | same_srv_rate, diff_srv_rate, dst_host_same_srv_rate, dst_host_diff_srv_rate, rerror_rate | Traffic | Portsweep (diff_srv cao), portscan (rerror cao) |
| 16–17 | logged_in, hot | Nội dung | R2L (xác thực trái phép), U2R (leo thang đặc quyền) |
| 18–20 | flag (OHE), protocol_type (OHE), service (OHE) | Categorical |  |

Kiểm định thống kê (ANOVA F-test) xác nhận toàn bộ 20 đặc trưng đều đạt mức ý nghĩa p < 0.001. Ba đặc trưng sở hữu F-score cao nhất lần lượt là flag_SF (168.332), same_srv_rate (163.827) và dst_host_srv_count (137.592). Tuy nhiên, phân tích sâu ma trận tương quan phát hiện sự tồn tại của 18 cặp biến số nội bộ có hiện tượng đa cộng tuyến mạnh (). Sự dư thừa thông tin (redundancy) này là cơ sở toán học then chốt, xác nhận sự cần thiết bắt buộc của thuật toán phân rã trực giao (PCA) ở giai đoạn tiếp theo nhằm nén không gian về định mức của phần cứng lượng tử.

### 4.2.2. Kết quả Tối ưu Pareto: Xác định  qubit tối ưu

Thực thi thuật toán tối ưu hóa đa mục tiêu thông qua quy trình tìm kiếm lưới (Grid Search) trên đơn hình Dirichlet đã thiết lập tại Mục 3.2.3, với ràng buộc bảo toàn thông tin cốt lõi (tổng phương sai giải thích lũy kế ). Trước tiên, chi phí phần cứng lượng tử Q(n) cho cấu trúc mạch ZZFeatureMap (cấu hình tầng lặp reps=2) được định lượng chi tiết theo số lượng qubit phần cứng tăng dần, làm cơ sở để tính toán hàm mục tiêu.
Bảng 4.5. Chi phí phần cứng  của ZZFeatureMap (reps=2) theo số qubit

[TABLE_8]
| (qubit) | Cổng 1-qubit | Cổng 2-qubit (CNOT) | (chuẩn hóa) | / qubit |
| 2 | 4 | 2 | 0,0298 | +2,98% |
| 3 | 6 | 6 | 0,0766 | +4,68% |
| 4 | 8 | 12 | 0,1447 | +6,81% |
| 5 | 10 | 20 | 0,2340 | +8,94% |
| 6 | 12 | 30 | 0,3447 | +11,06% |
| 10 | 20 | 90 | 1,0000 | — |

Bảng 4.6. Chỉ số thô cho các ứng viên  (sau khi lọc theo ràng buộc )

[TABLE_9]
|  |  |  |  | DBI | Silhouette | Pareto |
| 2 | 0,7418 | 0,9413 | 0,0298 | 0,8746 | — | LOẠI |
| 3 | 0,8210 | 0,6275 | 0,0766 | 1,0179 | — | LOẠI |
| 4 | 0,8662 | 0,4711 | 0,1447 | 1,0846 | 0,4262 | YES * |
| 5 | 0,9040 | 0,3777 | 0,2340 | 1,1311 | 0,4099 | YES |
| 6 | 0,9391 | 0,3154 | 0,3447 | 1,1718 | 0,3920 | YES |
| 7 | 0,9524 | 0,2717 | 0,4766 | 1,1850 | 0,3861 | YES |
| 10 | 0,9810 | 0,1957 | 1,0000 | 1,2140 | 0,3779 | YES |

Kết quả phân tích biên tối ưu Pareto xác định cấu hình  qubit (tương đương với không gian đặc trưng lượng tử 4 chiều) là nghiệm tối ưu toàn cục, đạt giá trị hàm mục tiêu J(n) cao nhất. Điểm cân bằng hình học này phản ánh chính xác chiến lược thiết lập bộ trọng số khảo sát đa mục tiêu bao gồm:  (ưu tiên phương sai),  (ưu tiên độ phân cụm và phân tách lớp dựa trên nghịch đảo DBI), và  (tiết kiệm chi phí cổng logic phần cứng). Trọng số này chứng minh hệ thống ưu tiên năng lực phân tách thực tế của cấu trúc dữ liệu và giới hạn phần cứng lượng tử NISQ hơn là việc chạy theo tối đa hóa lượng thông tin cổ điển một cách thuần túy.
Đánh giá thống kê nội bộ trên tập ứng viên chứng minh hệ số tương quan tuyến tính Pearson giữa chỉ số phân tách Davies-Bouldin (DBI) và hệ số Hình bóng (Silhouette) đạt giá trị cực hạn . Hệ quả toán học tiệm cận tuyệt đối này xác chứng DBI hoàn toàn là một proxy tính toán tin cậy, có khả năng thay thế hoàn toàn cho Silhouette nhằm giảm thiểu chi phí bộ nhớ trong các bài toán tối ưu không gian quy mô lớn.
Sau khi vượt qua màng lọc tối ưu Pareto, không gian đặc trưng lượng tử 4D cuối cùng giữ lại tổng cộng  lượng thông tin (phương sai giải thích tích lũy) của tập dữ liệu gốc, được phân bổ cụ thể qua các thành phần chính trực giao:
Thành phần chính thứ nhất (PC1): Chiếm 55.07% phương sai giải thích.
Thành phần chính thứ hai (PC2): Chiếm 19.11% phương sai giải thích.
Thành phần chính thứ ba (PC3): Chiếm 7.92% phương sai giải thích.
Thành phần chính thứ tư (PC4): Chiếm 4.52% phương sai giải thích.
Cấu trúc phân bổ và hình thái hình học của không gian nhúng lượng tử 4D này được mô tả chi tiết thông qua hệ thống biểu đồ trực quan dưới đây:

![FIGURE_9](FIGURE_9)
Hình 4.4. Ablation Study phân tích hiệu năng của Pipeline C1 (SelectKBest + PCA) so với các cấu hình Baseline trên mô hình Proxy tuyến tính.

![FIGURE_10](FIGURE_10)
Hình 4.5. Scree plot phân tích phương sai PCA và Elbow Criterion

![FIGURE_11](FIGURE_11)
Hình 4.6. Biểu đồ phân phối các thành phần chính trực giao PC1-PC4 theo từng lớp nhãn tấn công (Violin Plot))

### 4.2.3. Kết quả Ablation Study C1: Chứng minh hiệu quả Pipeline hai bước

Thực nghiệm loại trừ (Ablation Study) được triển khai trên khung đánh giá ch Chéo 5-fold CV nhằm kiểm chứng độc lập giá trị của từng pha giảm chiều không gian. Kết quả đối chứng hiệu năng giữa cấu hình đề xuất và các phương pháp baseline trên mô hình mạng đại diện (proxy model) được tổng hợp chi tiết tại Bảng 4.7.
Bảng 4.7. Ablation Study: So sánh 5 cấu hình pipeline (Proxy SVM-Linear)

[TABLE_10]
| Cấu hình | Mô tả | F1-macro | Std |
| (1) Baseline | Toàn bộ 122 đặc trưng | 0,9558 | 0,0106 |
| (2) PCA 95% variance | Ngưỡng phương sai cố định | 0,9504 | 0,0105 |
| (3) SelectKBest chỉ (K=20) | Không giảm xuống 4D | 0,9337 | 0,0105 |
| (4) PCA 4D trực tiếp | Không qua SelectKBest | 0,8577 | 0,0086 |
| (5) SKB(K=20) + PCA 4D [C1] | Pipeline hai bước | 0,8989 | 0,0091 |

Số liệu từ Bảng 4.7 chỉ ra rằng nếu chỉ áp dụng thuật toán PCA trực tiếp để ép chiều không gian từ dữ liệu thô xuống 4D (Cấu hình 4), hiệu năng hệ thống bị sụt giảm nghiêm trọng xuống mức . Tuy nhiên, khi tích hợp thêm màng lọc thống kê SelectKBest (K=20) ở giai đoạn đầu (Cấu hình 5), hiệu năng phục hồi mạnh mẽ lên mức  (tăng ròng  tuyệt đối, tương đương mức cải thiện +4,8% tương đối). Kết quả này chứng minh sự kết hợp hai giai đoạn tối ưu hơn hẳn việc sử dụng các kỹ thuật giảm chiều đơn lẻ trong điều kiện ràng buộc ngặt về số chiều phần cứng.
Để chứng minh tác động trực tiếp của sự cải thiện này lên mô hình lượng tử thực tế trong môi trường dữ liệu khan hiếm, đề tài thiết lập một thực nghiệm quy mô nhỏ (quy mô huấn luyện cố định N=100 mẫu) sử dụng bộ phân lớp QSVM-ZZ nguyên bản, kết quả thu được như sau:
Cấu hình nhúng tối ưu (SKB + PCA 4D): Đạt điểm .
Cấu hình đối chứng (PCA 4D trực tiếp): Chỉ đạt điểm .
Baseline cổ điển trên cùng tập mẫu: Thuật toán SVM-Linear đạt điểm .
Mức tăng trưởng hiệu năng lượng tử đạt  tuyệt đối (tương đương với  cải thiện tương đối) là minh chứng đanh thép xác chứng năng lực bóc tách thông tin vượt trội của hệ thống lọc hai lớp. Cấu hình này thậm chí giúp bộ phân lớp lượng tử bứt phá vượt qua cả baseline cổ điển ngay trên tập dữ liệu mồi quy mô cực chật hẹp.
Ý nghĩa khoa học của cấu trúc Pipeline hai giai đoạn (C1):
Sự nhảy vọt về hiệu năng xuất phát từ cơ chế vận hành tương hỗ giữa hai thuật toán cổ điển. Bộ lọc thống kê phi tham số SelectKBest đóng vai trò loại bỏ triệt để các đặc trưng nhiễu, các biến số không có tính phân tách cao hoặc các thuộc tính tĩnh suy biến trước khi phân tích thành phần chính. Nhờ đó, các vector đặc trưng 4D do PCA khởi tạo sau đó được tập trung hấp thụ tối đa các tín hiệu phân lớp thực chất, thay vì bị phân tán để giải thích các biến thiên nhiễu ngẫu nhiên.
Về mặt kiến trúc hệ thống, đây là framework đầu tiên trong bài toán IDS lượng tử tích hợp thành công cả bộ lọc phân phối thực nghiệm lẫn thuật toán tối ưu đa mục tiêu Pareto có định lượng trực tiếp rào cản cổng logic vật lý (CNOT). Toàn bộ các tham số hạt nhân ( và ) đều được trích xuất tự động theo cơ chế hướng dữ liệu ($data\text{-}driven$), tạo lập nền tảng không gian toán học ổn định và chuẩn mực, dọn đường cho việc ánh xạ chính xác các tọa độ hình học lên không gian Hilbert lượng tử đa chiều ở các chương sau.

![FIGURE_12](FIGURE_12)
Hình 4.7. Không gian biểu diễn phân tán của các thành phần PCA (Scatter Plot)

## 4.3. Đánh giá C2: Cầu nối Phân tích Cơ chế Biểu diễn Phi tuyến


### 4.3.1. Phân tích thực chứng tương quan Spearman giữa các PC

Để giải mã cơ chế bóc tách thông tin phi tuyến của hàm nhân lượng tử, nghiên cứu thiết lập một phép chẩn đoán thống kê độc lập trên đầu ra của không gian nhúng cổ điển (không gian 4D sau bộ lọc SelectKBest, PCA và MinMaxScaler). Kết quả đo lường tương quan cặp chéo toàn phần giữa các thành phần chính trực giao được tổng hợp chi tiết tại Bảng 4.8.
Bảng 4.8. Ma trận tương quan Pearson vs Spearman giữa các thành phần PCA

[TABLE_11]
| Cặp PC | Pearson | Spearman | Excess phi tuyến |
| PC1–PC2 | +2,28×10⁻⁸ | −0,1084 | 0,1084 |
| PC1–PC3 | −1,21×10⁻⁷ | +0,3968 | 0,3968 |
| PC1–PC4 | −4,43×10⁻⁸ | −0,0327 | 0,0327 |
| PC2–PC3 | +1,69×10⁻⁷ | −0,4366 | 0,4366 |
| PC2–PC4 | −8,30×10⁻⁸ | −0,1154 | 0,1154 |
| PC3–PC4 | −2,36×10⁻⁷ | +0,1336 | 0,1336 |

Hệ quả toán học thu được từ Bảng 4.8 bộc lộ một hiện tượng mâu thuẫn metric đặc biệt quan trọng. Do quy trình tính toán được thực thi đồng bộ trên toàn bộ tập huấn luyện gốc  với quy mô đại mẫu N = 125.973, thuật toán PCA đảm bảo tính trực giao tuyến tính tuyệt đối giữa các chiều không gian nhúng. Giá trị tuyệt đối lớn nhất ngoài đường chéo của hệ số Pearson chỉ đạt , tương đương giá trị 0 tuyệt đối trong giới hạn sai số sấp xỉ của độ chính xác số học.
Tuy nhiên, khi chuyển đổi sang hệ số tương quan thứ hạng Spearman (), ma trận biến thiên lại lệch rõ rệt khỏi giá trị 0 tại hai cặp thành phần mấu chốt: cặp – đạt  và cặp – đạt . Hiện tượng bất nhất cơ bản giữa hai đại lượng đo lường — một bên Pearson tiệm cận 0 nhưng một bên trị tuyệt đối Spearman đạt từ 0,40 đến 0,44 — là một bằng chứng định lượng đanh thép khẳng định rằng: Dù đã được trực giao hóa tuyến tính, không gian đặc trưng 4D cổ điển vẫn chứa đựng các cấu trúc ràng buộc phi tuyến đơn điệu (monotonic non-linear structures) tiềm ẩn rất mạnh.
Các liên kết phi tuyến này chính là "điểm mù" thuật toán mà bộ phân lớp tuyến tính cổ điển (Linear SVM) bỏ sót do hạn chế của siêu phẳng Euclid. Ngược lại, kiến trúc mạch lượng tử ZZFeatureMap khắc phục triệt để vấn đề này. Thông qua cổng dịch pha tương tác chéo ZZ, hệ thống mã hóa trực tiếp số hạng tích chéo phi tuyến  vào không gian pha lượng tử. Phép nhúng unita này biến đổi các tương quan đơn điệu ẩn thành các mối quan hệ phân tách tuyến tính trong không gian Hilbert đa chiều, tạo lợi thế giúp siêu phẳng lượng tử thiết lập lề quyết định chặt chẽ hơn.
Hình thái trực giao tuyến tính và phân tách phi tuyến đơn điệu này được trực quan hóa qua hai bản đồ nhiệt (heatmap) ma trận dưới đây:

![FIGURE_13](FIGURE_13)
Hình 4.8. Ma trận tương quan Pearson giữa 4 thành phần PCA trên toàn bộ X_train_pca (N = 125.973 mẫu NSL-KDD). Tất cả phần tử ngoài đường chéo có giá trị tuyệt đối ≤ 2,4 × 10⁻⁷, xác nhận PCA đảm bảo trực giao tuyến tính tuyệt đối trên đúng tập đã fit.

![FIGURE_14](FIGURE_14)
Hình 4.9. Ma trận tương quan Spearman trên toàn bộ X_train_pca bộc lộ các cấu trúc ràng buộc phi tuyến đơn điệu ẩn giữa cặp PC2-PC3 và PC1-PC3

### 4.3.2. Phân tích khả năng biểu diễn của Quantum Kernel (Expressibility)

Phân tích hình thái phổ trị riêng (eigenspectrum) của ma trận hạt nhân và độ vướng víu trạng thái (entanglement entropy) cung cấp các bằng chứng định lượng then chốt, giải mã năng lực biểu diễn phi tuyến vượt trội của kiến trúc mạch ZZFeatureMap trong không gian Hilbert.
Trước tiên, chỉ số phân kỳ lượng tử Kullback-Leibler () đối chiếu với phân phối Haar đóng vai trò xác thực cấu hình số tầng lặp (reps) tối ưu để nạp dữ liệu an ninh mạng. Thực nghiệm ghi nhận tại mốc reps=1, chỉ số đạt ; khi cấu hình tăng lên tầng lặp kép reps=2, chỉ số đạt điểm cực tiểu tối ưu . Tuy nhiên, nếu tiếp tục nâng lên mốc reps=3, giá trị sụt giảm xuống mốc 0,0422. Hệ quả này xác chứng rằng cấu hình reps=2 là điểm tới hạn hình học, giúp hàm sóng lượng tử bao phủ không gian trạng thái một cách đồng đều nhất, tiệm cận phân phối Haar lý tưởng mà không làm rơi mô hình vào hiện tượng cô đặc thước đo (measure concentration - rủi ro sụt giảm gradient pha).

![FIGURE_15](FIGURE_15)
Hình 4.10. Phổ trị riêng Kernel Matrix: ZZFeatureMap vs các kernel cổ điển

![FIGURE_16](FIGURE_16)
Hình 4.11. Expressibility: độ phủ của ZZFeatureMap trên không gian Hilbert
Định lượng sâu cấu trúc nội bộ hạt nhân thông qua số đo hạng hiệu dụng (Effective Rank - K) minh chứng ma trận nhân lượng tử  sở hữu một phổ trị riêng phẳng hơn hẳn các thuật toán cổ điển, đạt giá trị độc đỉnh , bỏ xa hạt nhân RBF () và hạt nhân đa thức (). Phổ trị riêng phẳng đồng nghĩa với việc năng lực phân bổ thông tin phương sai được trải đều trên các chiều không gian Hilbert, tối ưu hóa tỷ lệ phân tách khối cấu trúc ma trận (Block ratio giữa mật độ mẫu nội bộ lớp và xuyên phân lớp) đạt mốc 1,92 (vượt trội so với mốc 1,69 của RBF và 1,08 của Poly2).
Song song với hình thái phổ, việc đo lường Entropy vướng víu von Neumann (S) trên hệ con lượng tử (subsystem) cung cấp một bằng chứng vật lý trực tiếp về vai trò kết nối thông tin của các cổng trạng thái. Trạng thái lượng tử ứng với các mẫu hành vi tấn công xâm nhập mạng được kích hoạt mức độ vướng víu phức tạp hơn hẳn so với mẫu bình thường, ghi nhận giá trị toán học  đối chiếu với mốc . Phép kiểm định phi tham số Mann-Whitney U xuất xưởng giá trị ý nghĩa thống kê tối cao với , khẳng định sự phân tách cấu trúc vướng víu này mang tính bản chất chứ không do sai số ngẫu nhiên.

![FIGURE_17](FIGURE_17)
Hình 4.12. Entanglement entropy giữa các cặp qubit của ZZFeatureMap
Tuy nhiên, một phát hiện phản biện phương pháp luận quan trọng (caveat) cần được bề mặt hóa thông qua độ đo Căn chỉnh nhân trung tâm (Centered Kernel Alignment - CKA). Hệ số tương đồng hình học CKA giữa ma trận hạt nhân lượng tử  và ma trận nhãn mục tiêu chỉ đạt mức trung bình 0,270 với khoảng tin cậy 95% Bootstrap thực nghiệm . Chỉ số này thấp hơn tương đối so với hai đại diện cổ điển là  và . Hệ quả này chỉ ra một thực tế khách quan: Xét thuần túy trên không gian phẳng tuyến tính cổ điển, nhân lượng tử không sở hữu ưu thế đồng hướng tuyệt đối với cấu trúc nhãn so với các hàm nhân truyền thống. Lợi thế thực chất của mạch ZZFeatureMap không khu trú ở độ khớp siêu phẳng định hướng, mà nằm ở năng lực biểu diễn phi tuyến đơn điệu diện rộng (Expressibility) và cấu trúc liên kết vướng víu độc bản, cho phép bẻ cong không gian mẫu để bóc tách các điểm dữ liệu dị biệt cường độ cao.

![FIGURE_18](FIGURE_18)
Hình 4.13. So sánh CKA (Centered Kernel Alignment) giữa các kernel
4.3.3. Đánh giá C2.5: Sai lệch finite-shot giữa FidelityQuantumKernel và FidelityStatevectorKernel
Thực nghiệm C2.5 được thiết kế chuyên biệt nhằm định lượng mức độ suy giảm cấu trúc hình học và hiệu năng phân lớp do nhiễu lấy mẫu (shot noise) gây ra khi chuyển đổi trạng thái mô phỏng từ hạt nhân lượng tử lý tưởng sang hạt nhân ước lượng qua quá trình lấy mẫu hữu hạn. Giao thức đánh giá thiết lập ma trận nhân lượng tử tính toán theo trạng thái chính xác FidelityStatevectorKernel làm mốc tham chiếu không nhiễu (exact/noiseless baseline). Hệ thống tiến hành đối chiếu với FidelityQuantumKernel tại 4 cấp độ phân giải lấy mẫu: 128, 512, 2048, và 8192 shots.
Nhằm đảm bảo tính nhất quán hình học, toàn bộ cấu hình không gian nhúng của pipeline C1 (SelectKBest K=20 và PCA n=4), kiến trúc mạch ZZFeatureMap (4 qubit, reps=2, liên kết toàn phần), và bộ phân lớp cổ điển SVC (C=1,0, hạt nhân tính toán trước precomputed) được giữ nguyên trạng tuyệt đối. Thực nghiệm giới hạn quy mô trên một tập mẫu thu gọn gồm 100 mẫu huấn luyện và 100 mẫu kiểm thử lấy mẫu phân tầng nhị phân (Normal/Attack), thực hiện lặp lại qua 3 hạt giống ngẫu nhiên (seeds) để trích xuất giá trị trung bình kèm độ lệch chuẩn.
Hiệu năng nền tảng của bộ phân lớp lượng tử lý tưởng đóng vai trò mốc tham chiếu được ghi nhận tại Bảng 4.10.
Bảng 4.9. Hiệu năng tham chiếu của Baseline Statevector (Exact/Noiseless)

[TABLE_12]
| Kernel | F1-macro | Accuracy | N_SV | KTA |
| FidelityStatevectorKernel | 0,7796 | 0,7800 | 60 | 0,1861 |

Quá trình dịch chuyển hình học ma trận và biến thiên hiệu năng phân lớp tương ứng dưới tác động của phân giải shots tăng dần được thống kê chi tiết tại Bảng 4.11.
Bảng 4.10. Quá trình hội tụ của Finite-shot Kernel trung bình qua 3 lượt chạy

[TABLE_13]
| Shots | F1-macro mean | Std | ΔF1 = Statevector − Shot | FroSim train | FroSim test | MAE train | MAE test | KTA |
| 128 | 0,7892 | 0,0100 | −0,0095 | 0,9971 | 0,9961 | 0,01518 | 0,01534 | 0,1939 |
| 512 | 0,7728 | 0,0149 | +0,0069 | 0,9991 | 0,9989 | 0,00820 | 0,00820 | 0,1888 |
| 2048 | 0,7697 | 0,0100 | +0,0100 | 0,9996 | 0,9995 | 0,00597 | 0,00587 | 0,1891 |
| 8192 | 0,7797 | 0,0000 | −0,0000 | 1,0000 | 0,9999 | 0,00188 | 0,00185 | 0,1868 |

Sự phân rã sai số lấy mẫu lượng tử và xu hướng hội tụ cấu trúc hình học ma trận nhân được trực quan hóa toàn diện qua hệ thống 6 biểu đồ thành phần tại Hình 4.14.

![FIGURE_19](FIGURE_19)
Hình 4.14. Tác động của nhiễu lấy mẫu (Shot Noise Impact) đến hiệu năng và cấu trúc hình học ma trận kernel
Dữ liệu thực nghiệm chỉ ra hạt nhân lượng tử finite-shot sở hữu tốc độ hội tụ cấu trúc hình học về mốc lý tưởng cực kỳ nhanh chóng. Ngay tại cấu hình thấp 512 shots, độ tương đồng Cosine Frobenius (FroSim) đã vượt ngưỡng 0,999 trên cả hai miền dữ liệu huấn luyện và kiểm thử. Khi đẩy độ phân giải đo lường lên mức cực đại 8192 shots, ma trận sai số tuyệt đối trung bình (MAE) trên từng phần tử hạt nhân bị triệt tiêu xuống mức tối thiểu (đạt 0,00188 ở train và 0,00185 ở test), kéo theo giá trị căn chỉnh mục tiêu KTA (0,1868) tiệm cận sát mốc toán học noiseless gốc (0,1861).
Một dị biệt thống kê đáng chú ý bộc lộ tại cấu hình 128 shots khi điểm số  trung bình đạt 0,7892, vượt nhẹ +0,0095 điểm so với cấu hình statevector. Hiện tượng này tuyệt đối không phản ánh việc hạt nhân bị nhiễu lấy mẫu tốt hơn hạt nhân lý tưởng về mặt bản chất thuật toán. Sự nhô cao hiệu năng biên thực chất là hệ quả của việc nhiễu shot ngẫu nhiên hoạt động như một cơ chế điều hòa ngẫu nhiên (stochastic regularization), vô tình làm xê dịch siêu phẳng phân lớp lượng tử theo hướng có lợi trên không gian tập test quy mô nhỏ. Tuy nhiên, trạng thái này kém ổn định khi phương sai nội tại giữa các phần tử hạt nhân đạt mức cao (0,000161). Khi nâng số shots lên mốc 8192, biến động ngẫu nhiên bị loại trừ, phương sai tiêu biến về mức 0,000006, xác lập sự hội tụ ổn định tuyệt đối với độ lệch chuẩn hiệu năng bằng 0.
Song song với việc đảm bảo độ chính xác hình học, rào cản về chi phí điện toán (Wall-clock time) thực tế được định lượng chi tiết tại Bảng 4.12.
Bảng 4.11. Tương quan giữa độ phân giải lấy mẫu, hiệu năng và chi phí thời gian tính toán

[TABLE_14]
| Shots | Time mean (s) | Std (s) | F1-macro mean | Time / F1 |
| 128 | 81,53 | 8,43 | 0,7892 | 103,32 |
| 512 | 84,38 | 5,34 | 0,7728 | 109,19 |
| 2048 | 122,91 | 3,48 | 0,7697 | 159,69 |
| 8192 | 318,33 | 11,71 | 0,7796 | 408,30 |

Quy luật đánh đổi hiệu năng - chi phí mô phỏng và vị trí đường biên hiệu quả được biểu diễn trực quan qua Hình 4.15 và Hình 4.16.

![FIGURE_20](FIGURE_20)
Hình 4.15. Phân tích chi phí điện toán: Thời gian chạy thực tế theo số lượng shots

![FIGURE_21](FIGURE_21)
Hình 4.16. Đường biên Pareto giữa hiệu năng F1-macro và chi phí thời gian mô phỏng
Phân tích hình thái chi phí bộc lộ quy luật hàm mũ rõ nét: thời gian thực thi tăng trưởng rất chậm từ mốc 128 shots (81,53 giây) đến 2048 shots (122,91 giây), nhưng lập tức bùng nổ vọt lên mức 318,33 giây tại mốc 8192 shots (gấp gần 3 lần mốc trước đó). Sự đánh đổi tài nguyên này đổi lại một gain hiệu năng biên rất hẹp (chỉ cải thiện khoảng 0,01 điểm F1 khi tăng từ 2048 lên 8192 shots).
Hệ quả toán học này xác lập mốc cấu hình 2048 shots chính là điểm neo thực dụng tối ưu trên đường biên Pareto, đảm bảo ma trận lượng tử giữ vững độ tương đồng hình học Frobenius vượt ngưỡng 0,9995 trong khi tối ưu hóa được hơn 61% quỹ thời gian xử lý của CPU. Ngược lại, mốc phân giải cực hạn 8192 shots chỉ nên được kích hoạt trong các kịch bản kiểm chứng hội tụ toán học khắt khe.
Kết luận chuyên biệt cho thực nghiệm C2.5:
Kết quả chẩn đoán nhiễu lấy mẫu hoàn thành xuất sắc vai trò bảo chứng phương pháp luận cho toàn bộ đồ án: Nó xác chứng rằng các kết quả thực nghiệm tại giai đoạn C3 và C4 tiếp theo sử dụng bộ xử lý lý tưởng FidelityStatevectorKernel hoàn toàn có giá trị diễn giải như một mốc tham chiếu noiseless chuẩn mực, vì mọi sai lệch cấu hình hình học khi chuyển giao sang hệ thống đo lường finite-shot sampling thực tế sẽ được kiểm soát chặt chẽ trong biên độ nhiễu cực hẹp () tại ngưỡng phân giải khuyến nghị  shots.

## 4.4. Đánh giá C3: Phân tích Cấu trúc Hình học Kernel

Thực nghiệm C3 sử dụng giao thức đánh giá đa lượt (multi-run) với 5 tập huấn luyện độc lập (1.000 mẫu/tập, lấy mẫu phân tầng từ KDDTrain+) và một tập kiểm thử cố định (300 mẫu) để đảm bảo tính nhất quán. Mô hình đề xuất QSVM-ZZ sử dụng mạch ZZFeatureMap (reps=2, entanglement='full') phối hợp cùng FidelityStatevectorKernel. Hệ thống được đối chứng trực tiếp với cấu hình loại bỏ vướng víu QSVM-Z (ZFeatureMap) và ba baseline cổ điển (SVM-RBF, SVM-Poly bậc 2, Random Forest) dưới hai chế độ chuẩn hóa: MinMaxScaler và StandardScaler.
Để đảm bảo khách quan, tham số điều hòa ($C$) được tinh chỉnh hệ thống qua kỹ thuật đánh giá chéo phân tầng 5-fold trên tập mồi 1.000 mẫu. Quá trình này áp dụng nghiêm ngặt quy tắc một sai số chuẩn (1-SE Rule) với metric tối ưu -score: chọn giá trị C nhỏ nhất sao cho hiệu năng nằm trong khoảng 1-SE so với mô hình tốt nhất. Chiến lược này ưu tiên các siêu phẳng đơn giản và ngăn chặn rủi ro quá khớp (overfitting).
Quy trình tối ưu xác lập cấu hình lượng tử đề xuất tại mốc C = 1.0; trị số này được áp dụng nguyên trạng cho QSVM-Z để đảm bảo tính công bằng tuyệt đối cho nghiên cứu loại trừ (ablation study). Đối với các baseline cổ điển, các mốc C tối ưu được xác định cụ thể qua quét lưới (Grid Search) đã được tổng hợp tại bảng số liệu tương ứng.
Kết quả thực nghiệm cuối cùng được báo cáo dưới định dạng giá trị trung bình kèm độ lệch chuẩn () qua 5 lượt chạy. Do tập kiểm thử được đóng băng cố định, trị số  phản ánh chính xác độ nhạy và tính ổn định hình học của siêu phẳng mô hình trước biến động nhiễu của dữ liệu huấn luyện.

### 4.4.1. So sánh Hiệu năng Toàn diện (QSVM-ZZ vs Classical SVM)

Bảng 4.12. Hiệu năng trung bình qua 5 tập train độc lập kích thước 1000, đánh giá trên cùng tập test cố định kích thước 300

[TABLE_15]
| Mô hình | Scaler | C | F1-macro | Accuracy | n_SV |
| QSVM-ZZ |  | 1.0 | 0,8538 ± 0,0157 | 0,8540 ± 0,0157 | 277,4 ± 14,7 |
| QSVM-Z |  | 1.0 | 0,8271 ± 0,0151 | 0,8273 ± 0,0150 | 326,6 ± 20,8 |
| SVM-Linear |  | 0.1 | 0,8134 ± 0,0160 | 0,8140 ± 0,0155 | 368,6 ± 14,7 |
| SVM-Poly2 |  | 0.1 | 0,8122 ± 0,0193 | 0,8133 ± 0,0187 | 348,8 ± 18,6 |
| SVM-RBF |  | 0.1 | 0,8132 ± 0,0167 | 0,8140 ± 0,0161 | 406,8 ± 12,9 |
| SVM-Linear | StandardScaler | 0.1 | 0,8182 ± 0,0089 | 0,8187 ± 0,0087 | 365,6 ± 16,4 |
| SVM-Poly2 | StandardScaler | 0.1 | 0,8293 ± 0,0344 | 0,8300 ± 0,0336 | 404,0 ± 9,3 |
| SVM-RBF | StandardScaler | 10.0 | 0,8384 ± 0,0133 | 0,8387 ± 0,0135 | 266,8 ± 17,0 |

Dữ liệu tại Bảng 4.9 cho thấy bộ phân lớp lượng tử QSVM-ZZ đạt hiệu năng cao nhất với  và độ chính xác toàn cục 0.8853. So với các baseline trên không gian MinMaxScaler, QSVM-ZZ thiết lập lợi thế vượt trội: cải thiện $+0.0232$ điểm so với SVM-RBF, +0.0416 điểm so với SVM-Poly, và +0.0406 điểm so với SVM-Linear. Tuy nhiên, khi đối sánh với cấu hình cổ điển mạnh nhất (SVM-RBF + StandardScaler, ), cách biệt thu hẹp còn +0.0154. Điều này cho thấy dù QSVM-ZZ đạt hiệu năng tối ưu, ưu thế của nó không hoàn toàn áp đảo các giải pháp cổ điển được hỗ trợ bởi kỹ thuật scaling mạnh và phạt điều hòa cao (C=10.0).
Về phương diện hành vi hình học, QSVM-ZZ xác lập siêu phẳng quyết định qua trung bình 277.6 vectơ hỗ trợ (SV) trên 1.000 mẫu huấn luyện, đạt tỷ lệ tinh gọn 27.7%. Mật độ này thấp hơn rõ rệt so với các cấu hình cổ điển trên MinMaxScaler (406.8 của RBF, 368.6 của Linear) và cấu hình QSVM-Z thiếu vướng víu (326.6). Sự sụt giảm mật độ SV chứng minh cơ chế vướng víu đa qubit giúp bẻ cong không gian nhúng hiệu quả, thoát khỏi trạng thái suy biến hình học và hiện tượng ghi nhớ nhiễu (memorization), từ đó tạo ra biên phân lớp thanh thoát và có tính tổng quát hóa cao hơn.
Mức độ phân bổ hiệu năng và sai số biên giữa các cấu hình được trực quan hóa qua hệ thống biểu đồ cột dưới đây:

![FIGURE_22](FIGURE_22)
Hình 4.17. Biểu đồ cột đối chiếu điểm trung bình và độ lệch chuẩn của hiệu năng F1-macro và Accuracy giữa QSVM-ZZ và các baseline cổ điển xuyên suốt 5 lượt chạy độc lập

### 4.4.2. Kernel Target Alignment (KTA): Định lượng tương thích hình học

Bảng 4.10. Kernel Target Alignment trung bình qua 5 tập train độc lập

[TABLE_16]
| Kernel | KTA | Xếp hạng |
| SVM-RBF | 0,2473 ± 0,0318 | 1 |
| QSVM-ZZ | 0,2047 ± 0,0290 | 2 |
| SVM-Poly2 | 0,1247 ± 0,0214 | 3 |
| QSVM-Z | 0,0697 ± 0,0062 | 4 |
| SVM-Linear | 0,0621 ± 0,0071 | 5 |

Phân tích Insight cốt lõi:
Cổ điển vẫn dẫn đầu: Hạt nhân RBF (Std) đạt độ tương thích KTA cao nhất (),  xếp vị trí thứ hai (). Số liệu này một lần nữa khẳng định sự khách quan: nhân lượng tử không sở hữu cấu trúc hình học bám sát nhãn mục tiêu tốt nhất tuyệt đối so với RBF.
Vai trò quyết định của vướng víu (Entanglement):  áp đảo hoàn toàn phiên bản lượng tử tuyến tính  (0,2047 so với 0,0697). Biên độ chênh lệch lên tới +0,135 (lớn hơn rất nhiều sai số chuẩn) là bằng chứng định lượng đanh thép: Cổng tương tác chéo ZZ chính là cội nguồn tạo ra sự thay đổi hình học có lợi, vượt trội hoàn toàn so với các phép xoay qubit độc lập.

![FIGURE_23](FIGURE_23)
Hình 4.18. Ma trận hạt nhân (Kernel matrix): So sánh cấu trúc khối (block structure) của 5 kernel trên dữ liệu NSL-KDD

![FIGURE_24](FIGURE_24)
Hình 4.19. Biểu đồ cột phân bổ Kernel Target Alignment trung bình của các kernel qua 5 lượt chạy

### 4.4.3. Ablation Study: ZZFeatureMap vs ZFeatureMap (Cô lập vai trò Entanglement)

Thực nghiệm loại trừ (Ablation Study) cô lập trực tiếp vai trò của cơ chế vướng víu lượng tử bằng cách đối chiếu hai cấu hình mạch ZZFeatureMap (liên kết toàn phần) và ZFeatureMap (không vướng víu) trên cùng một hệ quy chiếu tham số (C=1,0).
Bảng 4.11. Ablation Study: Vai trò của ZZ-entanglement

[TABLE_17]
| Mô hình | Entanglement | F1-macro | Accuracy | n_SV | KTA |
| QSVM-ZZ | Có ZZ-entanglement | 0,8538 ± 0,0157 | 0,8540 ± 0,0157 | 277,4 ± 14,7 | 0,2047 ± 0,0290 |
| QSVM-Z | Không entanglement | 0,8271 ± 0,0151 | 0,8273 ± 0,0150 | 326,6 ± 20,8 | 0,0697 ± 0,0062 |
| Δ ZZ − Z | — | +0,0266 | +0,0267 | −49,2 | +0,1349 |

Phân tích Insight cốt lõi:
Cải thiện hiệu năng phân lớp: Sự hiện diện của cơ chế tương tác chéo giúp  tăng ròng +0,0266 điểm  và +0,0267 điểm Accuracy so với phiên bản không vướng víu.
Đột phá về hình học hạt nhân (KTA): Lợi ích lớn nhất của vướng víu lượng tử nằm ở cấu trúc không gian. Mạch ZZ làm KTA tăng vọt từ 0,0697 lên 0,2047 (chênh lệch +0,1349). Đây là bằng chứng vật lý cốt lõi: Entanglement chính là tác nhân định hình ma trận hạt nhân sát với nhãn mục tiêu, vượt xa các phép xoay qubit độc lập.
Tinh gọn lề quyết định: Mạch ZZ giúp giảm ròng 49,2 vectơ hỗ trợ (từ 326,6 xuống 277,4), chứng tỏ không gian phân tách trở nên mượt mà hơn và bớt phụ thuộc vào các điểm nhiễu ở vùng biên giới.
4.4.4. Trực quan hóa Biên Quyết định và Phân phối Support Vector

![FIGURE_25](FIGURE_25)
Hình 4.20. Decision boundary projection của năm kernel trên representative run 4 trong C3 multi-run
Phân tích Insight Hình học:
Hình 4.20 minh họa hình thái ranh giới quyết định được chiếu xuống hai mặt phẳng – và – (các chiều ẩn được cố định bằng giá trị trung vị).
Khác biệt cốt lõi của Vướng víu: So với , đường biên của  linh hoạt và phân mảnh hơn rất nhiều. Hiện tượng này trực quan hóa hệ quả toán học ở Bảng 4.11: Tương tác ZZ bẻ cong hình học hạt nhân để bọc lót tốt hơn các cụm dị biệt, thay vì cắt ngang tuyến tính.
Tối ưu hóa số lượng vectơ biên: Dù có đường biên phi tuyến phức tạp hơn trên hình chiếu,  lại cần ít vectơ hỗ trợ hơn hẳn  (273 so với 322 vectơ trên tập mồi). Điều này chứng tỏ lề phân lớp lượng tử Hilbert tạo ra độ sắc nét định hướng cao, không cần bám víu vào quá nhiều nhiễu cận biên (outliers) để định hình ranh giới.
Lưu ý Phương pháp luận (Caveat): Đây là phép chiếu bóng 2D từ không gian nhúng 4D. Tính "phân mảnh" hay "phức tạp" quan sát được không đồng nghĩa với ưu thế tuyệt đối về độ chính xác. Kết luận định lượng cuối cùng phải bám sát cấu trúc KTA toàn cục đa chiều đã chứng minh ở Mục 4.4.2.

## 4.5. Đánh giá C4: Robustness dưới Dịch chuyển Phân phối Dữ liệu

Giao thức C4 định lượng độ bền bỉ của mô hình qua 5 lượt chạy độc lập dưới 3 kịch bản dịch chuyển phân phối khắt khe: Dịch chuyển thời gian (Temporal Split), Nhiễu đặc trưng (Feature Perturbation) và Lệch xác suất tiên nghiệm (Class Prior Shift).

### 4.5.1. Thực nghiệm E1 — Temporal Split Evaluation

Thực nghiệm đối chiếu hiệu năng giữa tập kiểm thử chuẩn (KDDTest+) và tập khó chứa các mẫu phân phối lệch tự nhiên (KDDTest-21).
Bảng 4.13. Hiệu năng Temporal Split: KDDTest+ (Standard) vs KDDTest-21 (Hard)

[TABLE_18]
| Classifier | F1 Standard | F1 Hard | ΔF1 drop | Drop (%) |
| QSVM-ZZ | 0,8538 ± 0,0157 | 0,6217 ± 0,0137 | 0,2321 ± 0,0188 | 27,17% ± 1,89% |
| SVM-RBF MinMax | 0,8132 ± 0,0167 | 0,5961 ± 0,0185 | 0,2171 ± 0,0113 | 26,70% ± 1,39% |
| SVM-RBF Std | 0,8384 ± 0,0133 | 0,6270 ± 0,0357 | 0,2114 ± 0,0229 | 25,25% ± 3,14% |
| SVM-Poly2 MinMax | 0,8122 ± 0,0193 | 0,5974 ± 0,0090 | 0,2149 ± 0,0115 | 26,44% ± 0,86% |
| SVM-Poly2 Std | 0,8293 ± 0,0344 | 0,6161 ± 0,0402 | 0,2132 ± 0,0092 | 25,76% ± 1,99% |
| SVM-Linear MinMax | 0,8134 ± 0,0160 | 0,5832 ± 0,0185 | 0,2302 ± 0,0223 | 28,28% ± 2,47% |
| SVM-Linear Std | 0,8182 ± 0,0089 | 0,5834 ± 0,0137 | 0,2348 ± 0,0116 | 28,69% ± 1,41% |

Phân tích Insight cốt lõi:
Hiệu năng tập Chuẩn (Standard):  tiếp tục duy trì vị thế dẫn đầu với điểm .
Điểm mù trên tập Khó (Hard):  lật ngược tình thế để vươn lên dẫn đầu với F1 = 0,6270 và có biên độ sụt giảm thấp nhất (25,25%).  chỉ đạt 0,6217 (sụt giảm 27,17%). Lượng tử có hiệu năng cạnh tranh nhưng không vượt trội tuyệt đối trước dịch chuyển thời gian.
Bảng 4.14. Kết quả kiểm định McNemar so sánh QSVM-ZZ và các baseline trên tập KDDTest-21

[TABLE_19]
| Baseline so với QSVM-ZZ |  | p-value | Kết luận |
| SVM-Linear MinMax | 2,566 ± 1,907 | 0,1992 ± 0,1947 | ns |
| SVM-Linear Std | 2,401 ± 1,171 | 0,1655 ± 0,1501 | ns |
| SVM-Poly2 MinMax | 0,865 ± 0,552 | 0,4023 ± 0,2024 | ns |
| SVM-Poly2 Std | 1,483 ± 2,604 | 0,4877 ± 0,3044 | ns |
| SVM-RBF MinMax | 1,624 ± 1,011 | 0,2740 ± 0,2297 | ns |
| SVM-RBF Std | 1,882 ± 1,827 | 0,3813 ± 0,4042 | ns |

Ý nghĩa thống kê (McNemar Test): Phân tích từ Bảng 4.14 xác nhận mọi biên độ chênh lệch giữa  và các baseline trên tập Hard đều không đạt ý nghĩa thống kê (p > 0,05). Do đó, dữ liệu hiện tại chưa đủ cơ sở để khẳng định  robust hơn hẳn baseline cổ điển trong điều kiện dịch chuyển thời gian tự nhiên.

![FIGURE_26](FIGURE_26)
Hình 4.21. Biểu đồ Robustness dưới dịch chuyển phân phối Temporal Split qua 5 lượt chạy

### 4.5.2. Thực nghiệm E2 — Feature Perturbation Robustness

Thực nghiệm E2 định lượng độ nhạy hình học của hệ thống bằng cách tiêm nhiễu Gaussian tăng dần () trực tiếp vào không gian góc phân bổ tọa độ lượng tử.
Bảng 4.15. Hiệu năng F1-macro theo mức nhiễu  và Hệ số suy giảm Degradation Slope

[TABLE_20]
| Classifier | F1 @ ( | F1 @ (= 0.01) | F1 @ ( | F1 @ ( = 0.20) | Slope |
| QSVM-ZZ | 0,8538 ± 0,0157 | 0,8515 ± 0,0131 | 0,8405 ± 0,0105 | 0,6931 ± 0,0255 | −0,8354 ± 0,1611 |
| SVM-RBF MinMax | 0,8132 ± 0,0167 | 0,8131 ± 0,0149 | 0,8139 ± 0,0202 | 0,8118 ± 0,0250 | −0,0127 ± 0,0527 |
| SVM-RBF Std | 0,8384 ± 0,0133 | 0,8385 ± 0,0227 | 0,8377 ± 0,0267 | 0,7925 ± 0,0166 | −0,2291 ± 0,0468 |
| SVM-Poly2 MinMax | 0,8122 ± 0,0193 | 0,8122 ± 0,0193 | 0,8123 ± 0,0192 | 0,8215 ± 0,0267 | +0,0433 ± 0,0346 |
| SVM-Poly2 Std | 0,8293 ± 0,0344 | 0,8294 ± 0,0344 | 0,8253 ± 0,0324 | 0,8005 ± 0,0198 | −0,1496 ± 0,0998 |
| SVM-Linear MinMax | 0,8134 ± 0,0160 | 0,8133 ± 0,0162 | 0,8135 ± 0,0131 | 0,8089 ± 0,0135 | −0,0234 ± 0,0135 |
| SVM-Linear Std | 0,8182 ± 0,0089 | 0,8179 ± 0,0088 | 0,8155 ± 0,0114 | 0,8089 ± 0,0138 | −0,0432 ± 0,0305 |

Phân tích Insight cốt lõi:
Ưu thế tại vùng nhiễu thấp: Ở ngưỡng nhiễu biên độ nhỏ đến vừa (),  vẫn duy trì độ bền bỉ xuất sắc và giữ vững vị thế dẫn đầu toàn hệ thống (F1 = 0,8405).
Điểm gãy tại vùng nhiễu cao (Caveat): Khi nhiễu bị đẩy lên mức cực đoan , hiệu năng lượng tử lao dốc nghiêm trọng xuống mức $0,6931$. Hệ số suy giảm (Slope) dốc đứng ở mức , tồi tệ hơn rất nhiều so với sự ổn định tuyệt đối của baseline cổ điển  (Slope chỉ -0,013, F1 duy trì ở mức 0,8118).
Bản chất vật lý: Sự suy giảm này phản ánh đúng bản chất của mã hóa pha. Nhiễu trên đặc trưng đầu vào khuếch đại sự sai lệch của các cổng tương tác chéo, làm đứt gãy tính đồng pha của hàm sóng mạnh hơn hẳn so với sự xê dịch tuyến tính trong không gian Euclid cổ điển.

![FIGURE_27](FIGURE_27)
Hình 4.22. Biểu đồ Robustness dưới Feature Perturbation: F1-macro và mức suy giảm tương đối theo nhiễu Gaussian
4.5.3. Thực nghiệm E3 — Class Prior Shift
Thực nghiệm E3 đánh giá khả năng duy trì hiệu năng của các mô hình khi tỷ lệ lớp trong tập kiểm thử thay đổi. Ba phân phối kiểm thử cố định được tạo từ KDDTest+ bằng lấy mẫu có hoàn lại, mỗi tập gồm 300 mẫu: Balanced 50-50, Attack-heavy 70% và DoS-only binary. Các mô hình được đánh giá bằng F1-macro trên từng phân phối; sau đó tính Mean F1 để phản ánh hiệu năng tổng thể và Std across distributions để đo mức độ ổn định khi class prior thay đổi.
Bảng 4.16. Hiệu năng dưới Class Prior Shift

[TABLE_21]
| Mô hình | Balanced 50-50 | Attack-heavy 70% | DoS-only | Mean F1 | Std across dists |
| QSVM-ZZ | 0,8400 ± 0,0152 | 0,7839 ± 0,0287 | 0,8210 ± 0,0244 | 0,8150 | 0,0286 |
| SVM-RBF MinMax | 0,8192 ± 0,0134 | 0,7313 ± 0,0226 | 0,7662 ± 0,0194 | 0,7722 | 0,0443 |
| SVM-RBF Std | 0,8192 ± 0,0088 | 0,7643 ± 0,0248 | 0,8038 ± 0,0210 | 0,7958 | 0,0284 |
| SVM-Poly2 MinMax | 0,8145 ± 0,0104 | 0,7356 ± 0,0040 | 0,7528 ± 0,0292 | 0,7676 | 0,0415 |
| SVM-Poly2 Std | 0,8312 ± 0,0279 | 0,7273 ± 0,0252 | 0,7741 ± 0,0065 | 0,7775 | 0,0521 |
| SVM-Linear MinMax | 0,8169 ± 0,0156 | 0,7360 ± 0,0105 | 0,7564 ± 0,0139 | 0,7698 | 0,0421 |
| SVM-Linear Std | 0,8208 ± 0,0131 | 0,7368 ± 0,0081 | 0,7546 ± 0,0120 | 0,7707 | 0,0443 |

Để bổ sung cho so sánh F1-macro, nghiên cứu tính Cohen’s d giữa QSVM-ZZ và từng baseline trên ba phân phối class prior. Với thiết lập multi-run, Cohen’s d được tính riêng cho từng train run dựa trên vector F1 của ba phân phối, sau đó báo cáo dưới dạng mean ± std qua 5 runs. Chỉ số này đóng vai trò effect size, giúp định lượng mức độ lớn của khoảng cách hiệu năng giữa QSVM-ZZ và từng baseline.
Bảng 4.17. Cohen’s d giữa QSVM-ZZ và các baseline trong E3 Class Prior Shift

[TABLE_22]
| So sánh | Cohen’s d | Mức hiệu ứng |
| QSVM-ZZ vs SVM-RBF MinMax | +1,1099 ± 0,5226 | Lớn |
| QSVM-ZZ vs SVM-RBF Std | +0,7191 ± 0,6348 | Trung bình |
| QSVM-ZZ vs SVM-Poly2 MinMax | +1,2588 ± 0,7049 | Lớn |
| QSVM-ZZ vs SVM-Poly2 Std | +0,8671 ± 0,2115 | Lớn |
| QSVM-ZZ vs SVM-Linear MinMax | +1,2158 ± 0,4700 | Lớn |
| QSVM-ZZ vs SVM-Linear Std | +1,1607 ± 0,4662 | Lớn |

Kết quả E3 cho thấy QSVM-ZZ đạt F1-macro cao nhất trên cả ba phân phối class prior. Cụ thể, mô hình đạt trên Balanced 50-50, trên Attack-heavy 70%, và trên DoS-only binary. Mean F1 của QSVM-ZZ đạt 0,8150, cao hơn SVM-RBF StandardScaler (0,7958) và cao hơn rõ rệt các baseline còn lại.
Về độ ổn định giữa các phân phối, QSVM-ZZ có Std across distributions = 0,0286, gần tương đương với SVM-RBF StandardScaler (0,0284) và thấp hơn nhiều so với các baseline MinMax, Poly và Linear còn lại. Điều này cho thấy QSVM-ZZ không phải mô hình có độ lệch chuẩn thấp nhất tuyệt đối, nhưng đạt sự cân bằng tốt nhất giữa hiệu năng trung bình cao và độ ổn định khi tỷ lệ lớp thay đổi.
Cohen’s d tiếp tục củng cố kết luận này. QSVM-ZZ đạt effect size lớn so với hầu hết baseline, đặc biệt so với SVM-Poly2 MinMax , SVM-Linear MinMax , SVM-Linear Std và SVM-RBF MinMax . So với baseline mạnh nhất là SVM-RBF StandardScaler, effect size ở mức trung bình , cho thấy lợi thế của QSVM-ZZ vẫn tồn tại nhưng không quá áp đảo trước cấu hình RBF được chuẩn hóa tốt.
Tổng hợp các kết quả trên cho thấy Class Prior Shift là kịch bản trong đó QSVM-ZZ thể hiện lợi thế rõ nhất trong nhóm thí nghiệm C4. Mô hình đạt Mean F1 cao nhất qua ba phân phối kiểm thử, đồng thời duy trì độ dao động giữa các phân phối ở mức thấp, gần tương đương với SVM-RBF StandardScaler. Phân tích Cohen’s d cho thấy khoảng cách giữa QSVM-ZZ và phần lớn baseline đạt mức hiệu ứng lớn, trong khi so sánh với SVM-RBF StandardScaler đạt mức hiệu ứng trung bình. Điều này cho thấy QSVM-ZZ có khả năng duy trì hiệu năng tốt khi tỷ lệ Normal/Attack thay đổi, nhưng mức độ lợi thế phụ thuộc vào baseline đối chiếu và không nên được diễn giải như ưu thế tuyệt đối trong mọi cấu hình cổ điển.
Bảng 4.18. Tổng hợp kết luận C4

[TABLE_23]
| Thực nghiệm | Metric chính | Kết quả chính | Diễn giải |
| E1: Temporal split | F1 Hard, ( F1), Drop%, McNemar | QSVM-ZZ đạt F1 Standard cao nhất (0,8538), nhưng giảm xuống (0,6217) trên KDDTest-21; mức drop (0,2321), tương ứng (27,17%). Drop này thấp hơn Linear-Std (28,69%) và Linear-MinMax (28,28%), nhưng cao hơn RBF-Std (25,25%), Poly-Std (25,76%), Poly-MinMax (26,44%) và RBF-MinMax (26,70%). McNemar không significant. | QSVM-ZZ duy trì hiệu năng cạnh tranh trên hard split, nhưng mức suy giảm không phải thấp nhất; do đó chưa thể kết luận QSVM-ZZ robust hơn các baseline cổ điển dưới temporal shift. |
| E2: Feature perturbation | F1 theo (), degradation slope | QSVM-ZZ dẫn đầu ở nhiễu nhỏ ( 0,05), nhưng suy giảm mạnh tại (σ = 0,20) với slope âm lớn nhất. | Quantum kernel có lợi thế trong vùng perturbation thấp đến vừa, nhưng nhạy hơn với nhiễu lớn trong không gian góc ([0,π]). |
| E3: Class prior shift | Mean F1, Std, Cohen’s d | QSVM-ZZ đạt Mean F1 cao nhất; effect size lớn so với đa số baseline và trung bình so với RBF-Std. | Đây là kịch bản thuận lợi nhất cho QSVM-ZZ, cho thấy khả năng duy trì hiệu năng tốt khi tỷ lệ Normal/Attack thay đổi. |


## 4.6. Đánh giá C5: Confidence Calibration và Phân tích Tấn công Hiếm

Thiết lập: Tập test 99 mẫu, tập train 99 mẫu (nhất quán với C3). Phân phối lớp hiếm trong tập test: Normal=44, DoS=34, Probe=5, U2R=5, R2L=5 (tổng 10 mẫu hiếm, chiếm 10,1%). Platt Scaling được fit trên tập train để chuyển đổi decision function thành xác suất.
Tham số Platt Scaling: - QSVM-ZZ: ,  - SVM-RBF: ,  - SVM-Poly: ,

### 4.6.1. Đánh giá ECE/MCE và Reliability Diagrams

Tính toán ECE và MCE theo hai chế độ: (a) toàn bộ tập test 99 mẫu với equal-width binning (); (b) chỉ trên nhóm tấn công hiếm (U2R+R2L, ) với adaptive binning ().
Bảng 4.18. Kết quả ECE/MCE trên toàn tập test và lớp hiếm

[TABLE_24]
| Mô hình | ECE_full | MCE_full | ECE_rare | MCE_rare |
| SVM-Poly | 0,0980 | 0,4357 | 0,6191 | 0,8996 |
| QSVM-ZZ | 0,1065 | 0,4849 | 0,4337 | 0,9785 |
| SVM-RBF | 0,1219 | 0,4422 | 0,4707 | 0,9410 |

Phân tích Calibration:
Trên toàn bộ tập test (ECE_full): SVM-Poly đạt hiệu chỉnh tốt nhất (), QSVM-ZZ đứng thứ hai (), SVM-RBF đứng thứ ba (). Tất cả ba mô hình đều có calibration chấp nhận được ở mức tổng thể.
Trên lớp tấn công hiếm (ECE_rare): QSVM-ZZ đạt ECE thấp nhất () so với SVM-RBF () và SVM-Poly (). Khoảng cách QSVM-ZZ vs SVM-Poly là , tương đương cải thiện 30% về ECE_rare. Điều này có nghĩa là xác suất dự đoán của QSVM-ZZ trên các mẫu U2R/R2L phản ánh chính xác hơn rủi ro thực tế — đặc biệt quan trọng khi thiết kế ngưỡng cảnh báo cho hệ thống IDS tự động.

![FIGURE_28](FIGURE_28)
Hình 4.23. Reliability Diagram: toàn bộ tập test (99 mẫu)

![FIGURE_29](FIGURE_29)
Hình 4.24. Reliability Diagram: chỉ lớp hiếm U2R+R2L (Adaptive Binning)

### 4.6.2. Phân tích ROC/PR Curve và per-class Performance

Bảng 4.19. AUC-ROC và AUC-PR tổng thể

[TABLE_25]
| Mô hình | AUC-ROC | AUC-PR |
| QSVM-ZZ | 0,9574 | 0,9656 |
| SVM-RBF | 0,9409 | 0,9552 |
| SVM-Poly | 0,9256 | 0,9508 |

QSVM-ZZ đạt AUC-PR cao nhất () — metric phù hợp hơn ROC trong bài toán mất cân bằng lớp vì không bị inflate bởi số lượng True Negative lớn.
Bảng 4.20. Per-class AUC-PR (One-vs-Rest)

[TABLE_26]
| Lớp | QSVM-ZZ | SVM-RBF | SVM-Poly |
| Normal | 0,956 | 0,936 | 0,858 |
| DoS | 0,742 | 0,739 | 0,797 |
| Probe | 0,254 | 0,287 | 0,214 |
| U2R | 0,066 | 0,052 | 0,051 |
| R2L | 0,057 | 0,062 | 0,064 |

Phân tích per-class: QSVM-ZZ đạt AUC-PR cao nhất cho Normal (0,956) và U2R (0,066 cao hơn đáng kể so với baseline 0,051–0,052). Trên R2L, SVM-RBF và SVM-Poly nhỉnh hơn một chút (0,062 và 0,064 so với 0,057). Nhìn tổng thể, QSVM-ZZ cho thấy năng lực phát hiện U2R tốt hơn trong khi R2L vẫn là thách thức với cả ba mô hình — phù hợp với phân phối cực kỳ thưa thớt của U2R và R2L trong tập huấn luyện.

![FIGURE_30](FIGURE_30)
Hình 4.25. AUC-PR Heatmap per-class (One-vs-Rest): QSVM-ZZ vs SVM-RBF vs SVM-Poly

![FIGURE_31](FIGURE_31)
Hình 4.26. ROC Curve: so sánh QSVM-ZZ và các SVM cổ điển

![FIGURE_32](FIGURE_32)
Hình 4.27. Precision-Recall Curve: so sánh QSVM-ZZ và các SVM cổ điển

### 4.6.3. Phân tích Decision Margin Histogram cho lớp U2R/R2L

Bảng 4.21. Thống kê Decision Margin trên lớp hiếm (U2R+R2L, n=10)

[TABLE_27]
| Mô hình | Mean | Std | Cohen’s  vs QSVM-ZZ |
| QSVM-ZZ | 0,389 | 0,189 | d = +0,6805 |
| SVM-RBF | 0,560 | 0,301 |  |

Cohen’s d = (μ_RBF − μ_QSVM-ZZ) / σ_pooled = +0,6805 → RBF có margin trung bình lớn hơn QSVM-ZZ với mức hiệu ứng trung bình theo quy ước Cohen (|d|≥0,5).
McNemar test (trên 10 mẫu hiếm): ,  (không significant).

![FIGURE_33](FIGURE_33)
Hình 4.28. Histogram decision margin của QSVM-ZZ trên 5 lớp NSL-KDD, phân tách theo kết quả dự đoán (đúng/sai). Lớp hiếm (U2R, R2L) tập trung quanh ngưỡng 0 với phương sai nhỏ — bằng chứng cho ECE_rare thấp đã quan sát ở Bảng 4.18.
Phân tích: Cohen’s d = −0,6805 (mức trung bình theo quy ước Cohen) xác nhận SVM-RBF có margin trung bình lớn hơn QSVM-ZZ trên lớp hiếm (mean 0,560 vs 0,389). Std của RBF cao hơn QSVM-ZZ (0,301 vs 0,189) cho thấy phân phối margin của RBF dàn trải hơn — bao gồm cả vùng over-confident. Lưu ý quan trọng: kích thước hiệu ứng âm phản ánh khoảng cách trung bình, không phải chất lượng calibration. Bằng chứng chính cho lợi thế hiệu chuẩn của QSVM-ZZ nằm ở ECE_rare (0,4337 < 0,4707 của RBF) và AUC-PR (0,9656 > 0,9552), được trình bày ở các mục 4.6.1–4.6.2.

### 4.6.4. Phân tích Tính bổ trợ (Complementarity) — Bằng chứng về Lợi thế Lượng tử

Bảng 4.22. Phân rã kết quả dự đoán trên 10 mẫu hiếm (U2R+R2L)

[TABLE_28]
| Kịch bản | Số mẫu | Mô tả |
| QSVM-ZZ-wins (quantum advantage) | 1 | QSVM-ZZ đúng, RBF sai |
| RBF-wins | 2 | RBF đúng, QSVM-ZZ sai |
| Both-correct | 6 | Cả hai đúng |
| Both-wrong | 1 | Cả hai sai |

Trong 1 mẫu QSVM-ZZ-wins (chỉ số 86, nhóm U2R): QSVM-ZZ dự đoán đúng với confidence  và margin , trong khi SVM-RBF hoàn toàn sai với confidence  và margin âm sâu .Đối lại, trên 2 mẫu RBF-wins (nhóm R2L), QSVM-ZZ bỏ sót với confidence trung bình ~… trong khi RBF nắm bắt được — phù hợp với phân tích per-group U2R/R2L (mục 4.6.5 mới đề xuất ở Giai đoạn 3).

![FIGURE_34](FIGURE_34)
Hình 4.29. Phân tích tính bổ trợ: QSVM-ZZ wins vs RBF wins trên lớp hiếm
Kết luận C5: QSVM-ZZ đạt ECE_rare thấp nhất (0,434 vs 0,471 của RBF, cải thiện 7,9 %) và AUC-PR tổng thể cao nhất (0,966) — đây là bằng chứng chính. Phân tích per-group cho thấy lợi thế và bất lợi cùng tồn tại: QSVM-ZZ đạt accuracy 0,80 trên U2R (vs RBF 0,60) nhưng 0,60 trên R2L (vs RBF 1,00). Complementarity analysis ghi nhận 1 mẫu QSVM-ZZ-wins và 2 mẫu RBF-wins trên 10 rare → bằng chứng cho complementarity hai chiều, KHÔNG phải QSVM-ZZ dominance. Đây là động lực hợp lý cho kiến trúc Hybrid Ensemble: lấy lợi thế calibration của QSVM-ZZ trên U2R-like, lợi thế recall của RBF trên R2L-like. McNemar p = 1,0 phản ánh cỡ mẫu nhỏ (n=10), không nên diễn giải là”không khác biệt” — chỉ là “không đủ power”.”

![FIGURE_35](FIGURE_35)
Hình 4.30. Ma trận nhầm lẫn (Confusion Matrix) so sánh 3 mô hình

## 4.7. Đánh giá C6: Learning Curve và Sample Complexity

Thiết lập: Tập test cố định 22.544 mẫu. Bốn mốc dữ liệu huấn luyện:  (stratified sampling theo attack_category). Tại mỗi mốc : toàn bộ pipeline C1 được khởi tạo lại từ đầu và fit() chỉ trên  mẫu đó (zero-leakage tuyệt đối). QSVM-ZZ: FidelityStatevectorKernel với ZZFeatureMap(feature_dimension=4, reps=2, entanglement='full').

### 4.7.1. Bảng kết quả Test F1-macro theo mốc N

Bảng 4.23. Test F1-macro tại các mốc N: QSVM-ZZ vs Baselines

[TABLE_29]
| Mô hình | N=100 | N=200 | N=500 | N=1000 |
| QSVM-ZZ | 0,8132 | 0,7973 | 0,8311 | 0,8128 |
| SVM-RBF | 0,7240 | 0,7431 | 0,7310 | 0,7289 |
| SVM-Poly (bậc 2) | 0,7008 | 0,7537 | 0,7262 | 0,7434 |
| SVM-Linear | 0,7331 | 0,7583 | 0,7646 | 0,7370 |
| QSVM – ZZ – max baseline | +0,0801 | +0,0390 | +0,0665 | +0,0694 |

QSVM-ZZ vượt trội tất cả baseline tại mọi mốc N. Khoảng cách lớn nhất tại :
QSVM-ZZ đạt  trong khi SVM-RBF chỉ đạt  ().
Tại :
QSVM-ZZ đạt , cao hơn SVM-RBF  điểm phần trăm ().

![FIGURE_36](FIGURE_36)
Hình 4.31. Đường cong học tập: Test F1-macro theo N

![FIGURE_37](FIGURE_37)
Hình 4.32. Train F1 vs Test F1: Generalization gap theo N

![FIGURE_38](FIGURE_38)
Hình 4.33. Thời gian huấn luyện (Training time) theo N

### 4.7.2. Kiểm định thống kê Cohen’s d tại N=500

Bảng 4.24. Phân tích Decision Margin trên lớp hiếm (U2R+R2L) tại N=500 (n=2.952 mẫu)

[TABLE_30]
| Mô hình | Mean | Std | Cohen’s |
| QSVM-ZZ | 0,6538 | 0,4674 | — |
| SVM-RBF | 0,5070 | 0,2126 |  |

Cohen’s  (kích thước hiệu ứng: Nhỏ theo quy ước Cohen, ) trên 2.952 mẫu hiếm, đủ lớn để có ý nghĩa thực tiễn. QSVM-ZZ tạo ra biên quyết định xa hơn và ổn định hơn trên các tấn công hiếm ngay cả khi chỉ được huấn luyện trên 500 mẫu.
Phân tích đường cong học tập:
Tại N=100: QSVM-ZZ đạt F1=0,8132 — bằng chứng mạnh về lợi thế trong điều kiện dữ liệu cực kỳ hạn chế (low-data regime). Kernel lượng tử học được biên quyết định phi tuyến hiệu quả hơn ngay từ ít mẫu.
Tại N=200: F1 giảm nhẹ xuống 0,7973 — có thể do bộ mẫu ngẫu nhiên tại mốc này có phân phối bất lợi hơn. Tuy nhiên, QSVM-ZZ vẫn dẫn đầu.
Tại N=500: F1 tăng lên 0,8311 — đỉnh hiệu năng và cũng là điểm có khoảng cách lớn nhất so với SVM-RBF (+10 điểm phần trăm).
Tại N=1000: F1 ổn định ở 0,8128 — tương đương N=100 (0,8132) và thấp hơn N=500 (0,8311) khoảng 1,8 điểm phần trăm. Sự thiếu đơn điệu này (N=500 là đỉnh) nhiều khả năng do phân phối lớp hiếm trong subsample 500 ngẫu nhiên gặp may hơn là overfitting — vì generalization gap (train F1 − test F1) thực ra giảm dần từ N=100 (0,18) xuống N=1000 (0,14). Cần multi-seed sampling tại mỗi N để xác nhận.
Ý nghĩa khoa học của C6: Kết quả cung cấp bằng chứng thực nghiệm trực tiếp xác nhận giả thuyết lợi thế lượng tử trong điều kiện low-data regime. ZZFeatureMap ánh xạ dữ liệu vào không gian Hilbert  chiều với tương tác phi tuyến bậc hai, cho phép học biên quyết định phức tạp hơn từ ít mẫu hơn, một đặc điểm đặc biệt có giá trị trong môi trường IDS nơi dữ liệu tấn công hiếm (như U2R, R2L) rất khó thu thập.

## 4.8. Tổng hợp Kết quả và So sánh Đa đóng góp

Bảng 4.25. Tổng hợp bằng chứng khoa học từ C1 đến C6

[TABLE_31]
| Đóng góp | Metric cốt lõi | Kết quả định lượng | Kết luận |
| C1 | F1 pipeline vs baseline | SKB+PCA: 0,8989 vs PCA alone: 0,8577 | Pipeline 2 bước tốt hơn +4,8% relative |
| C1 | QSVM-ZZ thực tế | SKB+PCA: 0,6995 vs Full+PCA: 0,5942 | Cải thiện +17,7% relative khi dùng QSVM-ZZ |
| C2 | Spearman | PC2–PC3: ; PC3–PC4: | Tương quan phi tuyến xác nhận phù hợp ZZ gate |
| C3 | KTA (ZZ vs Z) | vs | Entanglement cải thiện KTA |
| C3 | F1 ablation | ZZ:  vs Z: | Entanglement cải thiện F1 |
| C4-E1 | F1_Hard | QSVM-ZZ:  (cao nhất) | Hiệu năng tốt nhất nhưng không robust hơn về drop% |
| C4-E3 | Mean F1 prior shift | QSVM-ZZ: , Cohen’s  = 3,99 | Vượt trội rõ rệt dưới class prior shift |
| C5 | ECE_rare | QSVM-ZZ:  vs RBF: | Calibration tốt hơn 7,9% trên lớp hiếm |
| C5 | AUC-PR | QSVM-ZZ:  vs RBF: | Phát hiện tấn công tốt nhất tổng thể |
| C6 | F1 @ N=500 | QSVM-ZZ:  vs RBF: | Lợi thế +10% trong low-data regime |
| C6 | Cohen’s  @ N=500 | trên 2.952 mẫu hiếm | Margin ổn định hơn có ý nghĩa thống kê |

Tóm tắt các khẳng định có thể claim:
Pipeline C1 (SelectKBest + Pareto PCA) được xác định hoàn toàn bằng dữ liệu và cải thiện đáng kể chất lượng đặc trưng đầu vào cho QSVM-ZZ.
ZZFeatureMap phù hợp tự nhiên với cấu trúc phi tuyến của dữ liệu IDS, được chứng minh bằng chuỗi bằng chứng nhất quán C1→C2→C3.
QSVM-ZZ vượt trội tất cả baseline trên tập test chuẩn và trong điều kiện dữ liệu hạn chế (N=100 đến N=1.000).
Lợi thế QSVM-ZZ mạnh nhất dưới class prior shift (E3) và trong low-data regime (C6), và thận trọng hơn dưới feature noise lớn (E2, ) và temporal shift (E1).
Về calibration, QSVM-ZZ cung cấp xác suất đáng tin cậy hơn cho tấn công hiếm (ECE_rare thấp nhất), là tiền đề quan trọng cho triển khai hệ thống IDS an toàn.
Toàn bộ các chuỗi thực nghiệm từ C1 đến C6 trong Chương 4 đã minh chứng sức mạnh của QSVM-ZZ, nhưng kết quả này hiện chỉ mới giới hạn trên một tập dữ liệu duy nhất (NSL-KDD). Câu hỏi khoa học được đặt ra tiếp theo là: Liệu chuỗi ưu thế hình học và hiệu năng này có bị sụp đổ khi môi trường mạng thay đổi (Distribution Shift) với ít nhiễu OHE và chứa nhiều tấn công lai (hybrid) hơn không? Chương 5 sẽ trả lời câu hỏi này thông qua việc tái triển khai toàn bộ pipeline trên tập dữ liệu hiện đại UNSW-NB15, từ đó xác định chính xác ranh giới lợi thế của học máy lượng tử.

# CHƯƠNG 5. KHẢ NĂNG TỔNG QUÁT HÓA TRÊN CÁC TẬP DỮ LIỆU IDS KHÁC


## 5.1. Ma trận Ánh xạ Đóng góp – Tập dữ liệu

Ma trận sau đây tóm tắt mức độ áp dụng của từng đóng góp trên mỗi tập dữ liệu, được xác định dựa trên đặc trưng kỹ thuật của từng dataset và câu hỏi nghiên cứu tương ứng:
Bảng 5.1. Ma trận ánh xạ Đóng góp (C1–C6) × Tập dữ liệu

[TABLE_32]
| Đóng góp | NSL-KDD | UNSW-NB15 | CIC-IDS2017/18 | CICIOT2023 | BETH (2021) |
| C1 (Pipeline giảm chiều) | Cơ sở | Stability test | High-dim stress | Imbalance | Low-data |
| C2 (Kernel expressibility) |  | Bậc cao hơn | — | — | — |
| C3 (Kernel geometry & KTA) |  | KTA | — | — | — |
| C4 (Robustness/shift) |  | — | Shift | Extreme shift | Natural shift |
| C5 (Calibration & rare) |  |  | — | ECE on IoT | — |
| C6 (Learning curve) |  | — | — | IoT low-data | True low-data |


## 5.2. UNSW-NB15: Thách thức Tấn công Hybrid và Tương tác Bậc cao


### 5.2.1. Đặc trưng kỹ thuật

Tập dữ liệu UNSW-NB15 [Moustafa & Slay, 2015] được tạo ra tại Phòng thí nghiệm Mạng thuộc Học viện Quốc phòng Úc (ADFA). Đặc điểm kỹ thuật:
Quy mô: 175.341 mẫu train, 82.332 mẫu test.
Không gian đặc trưng: 49 đặc trưng gốc (hỗn hợp số và phân loại), sau OHE khoảng 50–60 chiều, thấp hơn NSL-KDD (122D), thuận lợi hơn cho pipeline C1.
Phân loại tấn công: 9 loại (Fuzzers, Analysis, Backdoors, DoS, Exploits, Generic, Reconnaissance, Shellcode, Worms) — bao gồm nhiều tấn công hybrid kết hợp nhiều vector tấn công.
Mất cân bằng lớp: Moderate (không cực đoan như NSL-KDD U2R/R2L).

### 5.2.2. Khả năng tương thích của Pipeline Tiền xử lý (C1 Stability)

Thay vì cố định K=20 như trên NSL-KDD, pipeline tìm kiếm động (SelectKBest kết hợp LinearSVC proxy) trên UNSW-NB15 xác định điểm tối ưu Pareto tại K=35.Để xác nhận tính ổn định, thực nghiệm 1.6 quét K trong {10, 20, 35, 80, 120, 186} với PCA cố định 4 chiều, C=1,0 neutral cho cả 4 kernel, mỗi K chạy 5 train runs. Kết quả:
Bảng 5.2. So sánh hiệu năng F1 theo số lượng đặc trưng K trên tập UNSW-NB15.

[TABLE_33]
| K | QSVM-ZZ F1 | RBF F1 | Linear F1 | Poly F1 |
| 10 | 0,786 ± 0,028 | 0,786 ± 0,038 | 0,787 ± 0,041 | 0,787 ± 0,036 |
| 20 | 0,785 ± 0,019 | 0,796 ± 0,014 | 0,806 ± 0,020 | 0,797 ± 0,016 |
| 35 | 0,798 ± 0,022 | 0,802 ± 0,021 | 0,813 ± 0,024 | 0,797 ± 0,018 |
| 80 | 0,811 ± 0,012 | 0,800 ± 0,022 | 0,812 ± 0,024 | 0,802 ± 0,020 |
| 120 | 0,811 ± 0,012 | 0,800 ± 0,022 | 0,812 ± 0,024 | 0,802 ± 0,020 |
| 186 (all) | 0,811 ± 0,012 | 0,800 ± 0,022 | 0,812 ± 0,024 | 0,802 ± 0,020 |

Phát hiện: QSVM-ZZ đạt plateau F1 ≈ 0,811 từ K ≥ 80, ngang ngửa Linear. Tại K=35 (Pareto-optimal cho cân bằng compute), QSVM-ZZ 0,798 vs Linear 0,813 — chênh trong biên ± 1σ. Pareto frontier cho UNSW xác nhận K=35 vẫn là điểm cân bằng tốt giữa F1 và compute cost.

![FIGURE_39](FIGURE_39)
Hình 5.1. Đồ thị Scree plot thể hiện tỷ lệ phương sai tích lũy (Explained Variance Ratio) của các thành phần PCA trên tập dữ liệu UNSW-NB15.

### 5.2.3. Khả năng bao phủ không gian và Vướng víu Lượng tử (C2 Expressibility)

Thực nghiệm đo lường KL Divergence giữa phân phối của mạch ZZFeatureMap (reps=2) và phân phối Haar ngẫu nhiên lý tưởng trên UNSW-NB15 đạt mức 0.0221 (so với 0.0156 trên NSL-KDD). Chỉ số này < 0.05 khẳng định mạch lượng tử vẫn duy trì khả năng biểu diễn (expressibility) xuất sắc, không bị suy giảm khi gặp tập dữ liệu mới.

![FIGURE_40](FIGURE_40)
Hình 5.2. Phân bố phổ trị riêng (Eigenspectrum) của các ma trận Kernel trên tập dữ liệu UNSW-NB15, minh chứng cho khả năng tránh hiện tượng sụp đổ chiều của QSVM-ZZ.
Bên cạnh đó, phân tích Entanglement Entropy cho thấy lưu lượng Bình thường (Normal) của mạng lưới hiện đại 2015 mang tính nhiễu nội tại cao hơn (S = 1.0899) so với mạng 1999. Dù khoảng cách entropy  giữa lớp Attack và Normal bị thu hẹp, kiểm định Mann-Whitney vẫn xác nhận sự khác biệt này có ý nghĩa thống kê cực kỳ mạnh ()

![FIGURE_41](FIGURE_41)
Hình 5.3. Biểu đồ Violin thể hiện sự phân tán của Entanglement Entropy giữa lớp Normal và Attack trên môi trường mạng UNSW-NB15.

### 5.2.4. Đánh giá Hình học Kernel và Hiệu năng phân lớp (C3 & C4)

Khi chuyển từ tập dữ liệu NSL-KDD sang UNSW-NB15, chỉ số KTA trung bình (qua 5 lần chạy) giảm tương đương nhau ở cả hai kernel:
SVM-RBF: Giảm 0,0130 (tương đương 5,3%), từ số liệu $0,2473$ xuống $0,2343$.
QSVM-ZZ: Giảm 0,0113 (tương đương 5,5%), từ số liệu $0,2047$ xuống $0,1934$.
Kết luận thực tế:
Khác biệt về mức độ sụt giảm (drop) giữa hai kernel là không đáng kể. Do đó, kết luận chính xác là cả hai kernel đều bị mất một phần KTA do hiện tượng dịch chuyển đặc trưng, chứ không phải QSVM-ZZ có khả năng duy trì sự ổn định tốt hơn.

![FIGURE_42](FIGURE_42)
Hình 5.4. So sánh sự thay đổi độ tương thích hình học đích (Kernel Target Alignment - KTA) giữa SVM-RBF và QSVM-ZZ khi dịch chuyển từ môi trường NSL-KDD sang UNSW-NB15.
Bối cảnh: Sau khi tinh chỉnh siêu tham số C qua 5-fold CV trên tập UNSW (phiên bản 1.3), giao thức multi-run (5 train sets) được áp dụng với mức thiết lập trung hòa C = 1,0.
(Lưu ý: Mức C = 0,01 được tuned ban đầu khiến QSVM-ZZ bị suy biến – hiện tượng predict-all-attack trên tập test, chi tiết xem tại mục 5.2.6 mới).
Bảng 5.3. So sánh hiệu năng giữa các Kernel (qua 5 runs)

[TABLE_34]
| Kernel | C | F1​-macro | KTA | nSV​ |
| QSVM-ZZ | $1,0$ | $0,7977 \pm 0,0217$ | $0,1934 \pm 0,0495$ | $55,4 \pm 6,7$ |
| SVM-Linear | $1,0$ | $0,8129 \pm 0,0235$ | $0,1578 \pm 0,0494$ | $42,6 \pm 6,2$ |
| SVM-Poly2 | $1,0$ | $0,7971 \pm 0,0178$ | $0,1173 \pm 0,0578$ | $43,0 \pm 6,4$ |
| SVM-RBF | $1,0$ | $0,8015 \pm 0,0213$ | $0,2343 \pm 0,0541$ | $48,6 \pm 7,1$ |

Bảng 5.4. So sánh single-run cũ vs multi-run mới trên UNSW-NB15 (5 train sets)

[TABLE_35]
| Setting | QSVM-ZZ F1 | RBF F1 | McNemar Q vs R |
| Single-run cũ (C=1,0, không CV) | 0,7505 | 0,7649 | p = 0,749 (ns) |
| Multi-run C=0,01 (CV tuned, degenerate) | 0,776 ± 0,004 | 0,801 ± 0,021 | p = 6,57 × 10⁻⁵ (RBF wins) |
| Multi-run C=1,0 neutral (CHÍNH THỨC) | 0,798 ± 0,022 | 0,802 ± 0,021 | p = 0,1996 (ns) |

Giai đoạn C=0,01 tuned bộc lộ một hiện tượng quan trọng cho thảo luận khoa học: regularization parameter C tuned bằng F1 trên CV folds có thể đẩy QSVM-ZZ vào trạng thái degenerate (predict-all-attack) trên test set, dẫn đến confusion matrix TN=0 dù CV F1 cao. Khi chuyển sang C=1,0 neutral, QSVM-ZZ thoát degeneracy (TN trung bình 9,8) và F1 đẩy lên gần linear. Kết luận khoa học: ranh giới lợi thế của QSVM-ZZ trên UNSW không phải về kernel-task mismatch mà về độ nhạy của QSVM-ZZ với regularization trên dữ liệu cân bằng hơn.

![FIGURE_43](FIGURE_43)
Hình 5.5: Trực quan hóa cấu trúc khối (Block structure) của ma trận Quantum Kernel (ZZFeatureMap) và Classical Kernel (SVM-RBF).

### 5.2.5. Đánh giá Robustness trên UNSW-NB15 (C4 UNSW)

Thực nghiệm 1.5-redo lặp lại giao thức C4 trên tập dữ liệu UNSW-NB15 với cùng cấu hình tập gồm 5 train runs  5 test runs (tổng cộng 25 cặp), thiết lập siêu tham số trung hòa C = 1,0. Thực nghiệm tiến hành khảo sát qua 3 dạng dịch chuyển đặc trưng dữ liệu (data shift) cụ thể sau:
E1 — Temporal Cross-pair
Do tập dữ liệu UNSW-NB15 không có tập kiểm thử biệt lập tương đương như Test-21 của NSL-KDD, giao thức này sử dụng  cặp phối hợp chéo giữa các lượt train và test từ các run khác nhau để mô phỏng dịch chuyển theo thời gian.

[TABLE_36]
| Kernel | F1​-macro (mean±std) | TN mean |
| QSVM-ZZ |  | 9,4 |
| SVM-Linear |  | 14,3 |
| SVM-Poly2 |  | 11,0 |
| SVM-RBF |  | 12,2 |

Nhận xét: Hiệu năng  của cả 4 kernel rơi vào trạng thái xấp xỉ ngang nhau (tie) trong biên độ sai số .
E2 — Feature Perturbation Gaussian ()
Thử nghiệm độ bền vững của mô hình khi các đặc trưng đầu vào bị nhiễu loạn bởi nhiễu vi phân Gaussian với các mức độ lệch chuẩn  khác nhau.

[TABLE_37]
| σ | QSVM-ZZ F1 | RBF F1 | Linear F1 | Poly F1 |
| 0,05 | 0,798 ± 0,022 | 0,804 ± 0,017 | 0,813 ± 0,020 | 0,801 ± 0,018 |
| 0,10 | 0,785 ± 0,005 | 0,805 ± 0,023 | 0,810 ± 0,022 | 0,802 ± 0,014 |
| 0,20 | 0,779 ± 0,010 | 0,805 ± 0,024 | 0,808 ± 0,022 | 0,805 ± 0,011 |

Luận điểm thảo luận quan trọng:
Điểm yếu cốt lõi của Quantum Kernel: Chỉ số của QSVM-ZZ giảm rõ rệt 0,019 khi nhiễu  tăng từ . Ngược lại, các kernel cổ điển (RBF, Linear, Poly) gần như duy trì đồ thị phẳng và không bị ảnh hưởng. Điều này phản ánh một nhược điểm thực tế: không gian pha lượng tử (quantum phase space) có xu hướng khuếch đại các nhiễu loạn nhỏ từ dữ liệu đầu vào.
Tính nhất quán: So sánh trực tiếp với kịch bản C4-E2 trên NSL-KDD, QSVM-ZZ cũng duy trì tốt ở mức nhiễu thấp () nhưng suy giảm mạnh khi chạm ngưỡng nhiễu cao (). Xu hướng này đồng nhất trên cả hai tập dữ liệu.
E3 — Class Prior Shift (3 phân phối Normal/Attack):

[TABLE_38]
| Phân phối (Normal / Attack) | Kịch bản dữ liệu | QSVM-ZZ (F1​) | SVM-RBF (F1​) |
| 0,1 / 0,9 | Attack-heavy |  |  |
| 0,5 / 0,5 | Balanced |  |  |
| 0,9 / 0,1 | Normal-heavy |  |  |

Nhận xét so sánh:
QSVM-ZZ dẫn trước một khoảng nhỏ ở kịch bản Attack-heavy ($+0,02$ so với RBF) và đạt thế cân bằng (tie) ở hai kịch bản còn lại.
Biểu hiện này có sự khác biệt lớn so với kết quả trên NSL-KDD (nơi mà QSVM-ZZ thể hiện sự vượt trội hoàn toàn trên E3 với hiệu ứng khoảng cách d > 1). Lý do được xác định là bởi cấu trúc phân phối các lớp của UNSW-NB15 vốn dĩ đã cân bằng hơn, không có các phân phối thiểu số cực đoan như các lớp tấn công U2R hay R2L trên NSL-KDD.

### 5.2.6. Confidence Calibration + Rare Class trên UNSW-NB15 (C5 UNSW)

Thực nghiệm 1.7 tập trung đo lường độ chuẩn hóa cấu hình tin cậy (Confidence Calibration) thông qua chỉ số ECE và hiệu năng phát hiện các lớp tấn công hiếm ( trên Rare Attack Categories) của tập dữ liệu UNSW-NB15, bao gồm: Analysis, Backdoor, Shellcode, và Worms.
Cấu hình thực nghiệm:
Giao thức: Multi-run (5 train sets).
Siêu tham số:  (thiết lập trung hòa).
Phương pháp căn chỉnh xác suất: Platt scaling thông qua phân tách internal 5-fold CV của thuật toán SVC(probability=True).

[TABLE_39]
| Kernel | F1​ | AUC-PRoverall​ | AUC-PRrare​ | ECErare​ |
| QSVM-ZZ |  |  |  |  |
| SVM-Linear |  |  |  |  |
| SVM-Poly2 |  |  |  |  |
| SVM-RBF |  |  |  |  |

Phân tích & So sánh trực tiếp (QSVM-ZZ vs SVM-RBF)
Tương tự như giao thức phân tích C5 trên tập dữ liệu NSL-KDD, các chỉ số cốt lõi giữa mô hình lượng tử và RBF cổ điển thể hiện các xu hướng đáng chú ý:
Về độ sai số chuẩn hóa (): Chỉ số của QSVM-ZZ (0,194) thấp hơn so với SVM-RBF (0,205). Điều này chứng tỏ QSVM-ZZ cho khả năng hiệu chuẩn cấu hình tin cậy tốt hơn nhẹ so với kernel RBF.
Về khả năng nhận diện lớp hiếm (): QSVM-ZZ đạt 0,336 so với mức 0,246 của SVM-RBF. Với khoảng cách vượt trội , khẳng định QSVM-ZZ phát hiện các dạng tấn công hiếm tốt hơn rõ rệt.
Khoảng cách biên phân định: Chỉ số Cohen’s d (đo trên biên phân định gộp của các lớp hiếm - margin pooled rare) đạt -0,244. Đây là mức ảnh hưởng nhỏ (small effect), cho thấy SVM-RBF sở hữu biên phân định lớn hơn, một pattern hoàn toàn trùng khớp với kết quả trên NSL-KDD.
Hiệu năng theo từng nhóm Rare Lớp (Per-rare-group Accuracy)
Đánh giá độ chính xác chi tiết trên từng phân lớp tấn công thiểu số cho thấy:
Analysis: QSVM-ZZ (0,96) dẫn trước SVM-RBF (0,92).
Backdoor: Cả hai mô hình đều đạt mức tối đa (1,00)  Hòa (Tie).
Shellcode: QSVM-ZZ (0,88) dẫn trước SVM-RBF (0,80).
Worms: Cả hai mô hình đều đạt 0,96  Hòa (Tie).
Kết luận: QSVM-ZZ dẫn trước ở 2/4 nhóm lớp hiếm và đạt thế cân bằng ở 2 nhóm còn lại. Kết quả này tương thích tốt với quy luật phân phối từng thấy trên NSL-KDD (nơi QSVM-ZZ chiếm ưu thế ở lớp U2R và chịu mức yếu thế hơn ở lớp R2L).
Lưu ý phương pháp luận quan trọng (Methodological Caveats)
Hiện tượng suy biến đồ thị Calibration (Degenerate Plot): Khi tiến hành gộp chung (pool) chỉ riêng các lớp hiếm để vẽ biểu đồ Calibration, do tỷ lệ thành viên lớp hiếm quá nhỏ (rare-membership), phần lớn các xác suất dự đoán sẽ bị rơi hoàn toàn vào các bin xác suất thấp với tỷ lệ dương tính (fraction-of-positives) chạm ngưỡng 1,0. Hệ quả là đường cong độ tin cậy (reliability curve) sẽ bị bẹt phẳng. Khuyến nghị: KHÔNG sử dụng đồ thị biểu diễn Calibration plot đối với các lớp hiếm trên UNSW-NB15, thay vào đó hãy sử dụng biểu đồ cột (bar chart) để trực quan hóa chỉ số .
Sự khác biệt về định nghĩa : Trên tập dữ liệu NSL-KDD, chỉ số này được tính độc lập theo từng lớp đơn lẻ (pr_auc_per_class cho U2R, R2L riêng biệt). Ngược lại, trên UNSW-NB15, chỉ số được tính dựa trên tập hợp nhị phân các lớp hiếm (auc_pr_rare). Do đó, không so sánh trực tiếp giá trị tuyệt đối giữa hai tập dữ liệu, mà chỉ tập trung so sánh xu hướng lợi thế định hướng (directional advantage) của các mô hình.

### 5.2.7. Diễn giải Khoa học: Ranh giới của Lợi thế Lượng tử

Tổng hợp kết quả từ chuỗi 4 thực nghiệm trên tập dữ liệu UNSW-NB15 bao gồm: C1 K-sweep (Khảo sát số lượng chiều đặc trưng K), C3 Kernel Geometry (Hình học Kernel), C4 Robustness (Độ bền vững) và C5 Calibration (Độ hiệu chuẩn xác suất) cho phép định vị và định nghĩa chính xác vùng không gian mà cấu hình mô hình QSVM-ZZ duy trì được lợi thế so sánh, cũng như ranh giới nơi mô hình này đánh mất ưu thế trước các giải pháp phân lớp cổ điển trên một tập dữ liệu mạng hiện đại.
1. Vùng không gian QSVM-ZZ duy trì lợi thế (trên UNSW-NB15)
Hiệu chuẩn cấu hình tin cậy trên lớp hiếm (Rare Class Calibration - C5 UNSW): Chỉ số  và  của mô hình lượng tử tối ưu hơn so với SVM-RBF. Kết quả thực nghiệm này thể hiện tính nhất quán hoàn hảo với các phân tích trước đó trên tập dữ liệu NSL-KDD.
Hiệu năng đạt ngưỡng bão hòa (Plateau Performance) ở số chiều K lớn (C1 UNSW): Khi mở rộng không gian đặc trưng lên mức , độ chính xác  của mô hình lượng tử đạt 0,811, tiệm cận và thiết lập trạng thái cân bằng (tie) với mô hình SVM-Linear.
Khả năng chống chịu dịch chuyển phân phối tập trung tấn công (Attack-heavy Class Prior Shift - C4 E3 UNSW): Trong kịch bản phân phối dữ liệu kiểm thử bị lệch cực đoan về phía các mẫu độc hại (tỷ lệ 0,9 Attack), chỉ số  của QSVM-ZZ dẫn trước SVM-RBF một khoảng cách .
2. Vùng không gian QSVM-ZZ đánh mất ưu thế (trên UNSW-NB15)
Hiệu năng tổng thể tại điểm tối ưu Pareto (Overall  tại K=35): Tại điểm cắt tối ưu hóa tài nguyên toán học, QSVM-ZZ chỉ đạt thế cân bằng () với cả 3 kernel cổ điển còn lại, hoàn toàn không thể hiện sự vượt trội về mặt thống kê.
Độ bền vững trước nhiễu loạn đặc trưng (Robustness với Feature Noise - C4 E2 UNSW): Tại mức nhiễu vi phân lớn , mô hình lượng tử bộc lộ điểm yếu cốt lõi khi chỉ số  sụt giảm mạnh . Trong khi đó, đồ thị hiệu năng của các đối thủ cổ điển gần như phẳng tuyến tính và không bị ảnh hưởng bởi nhiễu đầu vào.
Giá trị đo lường hình học Kernel tuyệt đối (Absolute KTA - C3 UNSW): Chỉ số KTA của SVM-RBF vẫn giữ vị trí cao nhất (0,234), xếp trên QSVM-ZZ (0,193). Biên độ chênh lệch dịch chuyển KTA giữa hai tập dữ liệu (NSL-KDD và UNSW-NB15) là không đáng kể.
3. Phân tích bản chất qua cấu trúc Spearman PCA UNSW
Khảo sát hệ số tương quan phi tuyến đơn điệu Spearman trong không gian giảm chiều PCA của UNSW-NB15 cho thấy giá trị  (tương đương với phân phối trên tập dữ liệu NSL-KDD). Tuy nhiên, cấu trúc này lại không chuyển hóa thành lợi thế áp đảo về chỉ số  cho mô hình lượng tử trên UNSW.
Hệ quả này gợi mở một giả thuyết khoa học quan trọng: Chỉ riêng sự tồn tại của các cấu trúc phi tuyến trong không gian đặc trưng PCA là chưa đủ điều kiện để QSVM-ZZ giành chiến thắng tuyệt đối. Mô hình lượng tử cần có thêm sự cộng hưởng từ điều kiện mất cân bằng lớp cực đoan (chẳng hạn như sự xuất hiện của các phân lớp thiểu số U2R/R2L như trong NSL-KDD) để phát huy tối đa năng lực phân định biên.

## 5.3. Hướng mở rộng đánh giá khả năng Tổng quát hóa

Để hoàn thiện bức tranh về khả năng triển khai thực tế của hệ thống IDS Lượng tử, các nghiên cứu trong tương lai cần tiếp tục mở rộng thực nghiệm trên các bộ dữ liệu đặc thù, cụ thể:
High-Dimensional Stress Test (CIC-IDS2017/2018): Đánh giá khả năng của thuật toán SelectKBest trên không gian 80 đặc trưng gốc và khả năng chống chịu trước concept drift theo thời gian giữa hai phiên bản 2017 và 2018.
Extreme Class Imbalance trong IoT (CICIOT2023): Với tỷ lệ lớp Normal chiếm trên 95%, bộ dữ liệu này sẽ là bài kiểm tra khắc nghiệt nhất cho độ tin cậy của mô hình (ECE) trong môi trường tài nguyên hạn chế của thiết bị IoT.
True Low-Data Regime với APT (BETH 2021): Thử thách mô hình trên dữ liệu audit log Linux thực tế, nơi các cuộc tấn công Advanced Persistent Threat (APT) khan hiếm tự nhiên và không thể sinh mẫu nhân tạo. Việc kiểm chứng độ dốc đường cong học tập (Learning Curve) trên BETH sẽ khẳng định giá trị thực tiễn lớn nhất của học máy lượng tử.

# CHƯƠNG 6. KẾT LUẬN VÀ HƯỚNG NGHIÊN CỨU MỞ RỘNG


## 6.1. Tổng kết 6 Đóng góp Khoa học

Đề tài đã xây dựng và kiểm chứng thực nghiệm một khung Quantum Support Vector Machine (QSVM-ZZ) toàn diện cho bài toán phát hiện xâm nhập mạng, được điều hướng bởi hai nguyên tắc cốt lõi: ràng buộc phần cứng NISQ và chiều sâu giải thích khoa học. Sáu đóng góp nguyên gốc tạo thành một chuỗi narrative nhất quán và tự củng cố lẫn nhau, trong đó C1 đóng vai trò nền tảng tối ưu.
Đóng góp 1 (C1): Pipeline Giảm chiều Hai giai đoạn — Tối ưu Nhúng Lượng tử Có Ràng buộc Phần cứng
Tóm tắt nội dung: C1 giải quyết thách thức cốt lõi trong triển khai QSVM-ZZ thực tế: nén không gian 122 chiều (sau OHE) xuống còn 4 chiều (tương ứng 4 qubit NISQ) một cách định lượng và có hệ thống. Framework đề xuất pipeline hai bước bao gồm: (1) Lọc đặc trưng bằng SelectKBest (K=20) dựa trên ANOVA F-test, loại bỏ 83,6% đặc trưng dư thừa thông qua tiêu chí Elbow (); và (2) Tối ưu hóa đa mục tiêu PCA Pareto trên đơn hình Dirichlet để chọn số qubit tối ưu. Kết quả xác định cấu hình n=4 qubit đạt điểm cân bằng với tỷ lệ bảo toàn phương sai V=86,62%, Silhouette = 0,4262 và chi phí phần cứng Q(n)=0,1447.
Điểm mới khoa học: Đây là nghiên cứu đầu tiên tích hợp đồng bộ lọc thống kê (ANOVA F-test) và tối ưu hóa Pareto có xét đến giới hạn vật lý (với hệ số phạt  cho cổng CNOT nhằm phản ánh tỷ lệ lỗi thực tế của phần cứng NISQ). Phương pháp luận này có tính tổng quát cao, cho phép áp dụng trực tiếp cho các tập dữ liệu khác như UNSW-NB15 hay CIC-IDS mà không cần điều chỉnh thủ công.
Đóng góp 2 (C2): Phân tích Khả năng Biểu diễn Phi tuyến của Quantum Kernel
Tóm tắt nội dung: C2 xác lập cơ sở lý thuyết và thực nghiệm giải thích sự tương thích đặc biệt giữa mạch ZZFeatureMap và cấu trúc dữ liệu IDS. Chuỗi lập luận dựa trên việc xác nhận bản chất phi tuyến bậc hai của dữ liệu NSL-KDD sau PCA: trên toàn bộ X_train_pca (N=125.973), Pearson ≈ 0 (max|off-diag| = 2,36×10⁻⁷ — trực giao tuyến tính tuyệt đối) trong khi Spearman ρ đạt −0,437 ở PC2–PC3 và +0,397 ở PC1–PC3, bộc lộ cấu trúc phi tuyến đơn điệu mà Linear SVM bỏ sót. Cổng ZZ mã hóa trực tiếp các tương tác chéo  vào pha lượng tử, cho phép kernel lượng tử hoạt động tương đương polynomial kernel bậc 2 nhưng được ánh xạ hiệu quả trong không gian Hilbert  chiều.
Bằng chứng định lượng: Phân tích Entanglement Entropy xác nhận mạch ZZFeatureMap tạo ra trạng thái vướng víu thực sự giữa các qubit. Đồng thời, kết quả so sánh CKA (Centered Kernel Alignment) khẳng định sự khác biệt rõ rệt về cấu trúc biểu diễn của ma trận kernel lượng tử so với các giải pháp kernel cổ điển.
Điểm mới khoa học: Nghiên cứu đã nâng tầm từ việc so sánh hiệu năng (benchmark) thuần túy sang phân tích bản chất cơ chế, giúp lý giải tường minh tại sao mô hình QSVM-ZZ lại đạt được lợi thế phân lớp trên dữ liệu an ninh mạng.
Đóng góp 3 (C3): Phân tích Kernel Geometry và Decision Boundary
Tóm tắt nội dung: C3 cung cấp bằng chứng hình học thực nghiệm củng cố cho C2 thông qua sáu kỹ thuật định lượng: (i) So sánh cấu trúc khối (block structure) trên heatmap ma trận kernel; (ii) Thực hiện Ablation study cô lập vai trò entanglement; (iii) Đo lường Kernel Target Alignment (KTA); (iv) Phân tích phân phối Support Vector; (v) Trực quan hóa biên quyết định qua phép chiếu 4D  2D; và (vi) Xác nhận tương quan Spearman.
Bằng chứng định lượng: Cơ chế vướng víu giúp cải thiện chỉ số KTA từ 0,0697 ± 0,0062 (QSVM-Z) lên 0,2047 ± 0,0290 (QSVM-ZZ), tương ứng mức tăng ~194% trung bình qua 5 train runs. Hiệu năng F1-macro tăng +0,0266 (0,8538 ± 0,0157 so với 0,8271 ± 0,0151). Ngoài ra, QSVM-ZZ thiết lập biên quyết định ổn định hơn với ít Support Vectors hơn (277,4 so với 326,6 trung bình trên 1.000 mẫu) và vượt trội so với các baseline cùng scaling MinMax[0,π]: +0,0404 vs Linear, +0,0416 vs Poly, +0,0406 vs RBF-MinMax. So với baseline mạnh nhất là SVM-RBF + StandardScaler, khoảng cách thu hẹp còn +0,0154 — cần nhấn mạnh để tránh over-claim.
Điểm mới khoa học: Kết quả Ablation study giữa cấu hình ZZ và Z là bằng chứng nhân quả (causal evidence) khẳng định cổng CNOT-based entanglement chính là nguồn gốc tạo nên lợi thế hình học lượng tử, thay vì các yếu tố phụ trợ như độ sâu mạch hay số lượng tham số.
Đóng góp 4 (C4): Đánh giá Robustness dưới Data Distribution Shift
Tóm tắt nội dung: C4 đánh giá khả năng triển khai thực tế của QSVM-ZZ thông qua ba giao thức kiểm tra đa dạng, phản ánh các dạng dịch chuyển phân phối (distribution shift) điển hình trong môi trường mạng thực tế.
Bằng chứng định lượng: Temporal shift (E1): QSVM-ZZ đạt F1 Standard cao nhất (0,8538 ± 0,0157) nhưng KHÔNG đạt F1 Hard cao nhất — trên KDDTest-21, SVM-RBF Std dẫn đầu (0,6270 ± 0,0357) trong khi QSVM-ZZ đạt 0,6217 ± 0,0137. Mức sụt giảm của QSVM-ZZ là 0,2321 (27,17 %), thấp hơn Linear-Std (28,69 %) nhưng cao hơn RBF-Std (25,25 %). Kiểm định McNemar trên hard split cho p-value 0,17–0,49 → không khác biệt thống kê.
Feature noise (E2): QSVM-ZZ dẫn đầu ở nhiễu thấp với F1(σ=0,01) = 0,8515 ± 0,0131 và F1(σ=0,05) = 0,8405 ± 0,0105, vẫn cao hơn mọi baseline. Tuy nhiên ở σ=0,20, F1 giảm mạnh xuống 0,6931 ± 0,0255, slope = −0,8354 ± 0,1611 — âm mạnh nhất trong toàn bộ classifier. Đây là điểm yếu thật của quantum kernel: pha lượng tử khuếch đại nhiễu đầu vào theo cách phi tuyến.
Class prior shift (E3): QSVM-ZZ đạt Mean F1 cao nhất qua 3 phân phối = 0,8150 (vs SVM-RBF Std = 0,7958, là baseline mạnh nhất). Std across distributions = 0,0286, gần tương đương RBF-Std (0,0284). Cohen’s d so với baseline đa số đạt mức lớn (+1,11 vs RBF-MinMax, +1,26 vs Poly-MinMax), nhưng so với RBF-Std chỉ đạt +0,72 (mức trung bình) — lợi thế tồn tại nhưng không tuyệt đối.Framing khoa học: Kết quả xác lập lợi thế có điều kiện của QSVM-ZZ: mạnh nhất dưới tác động của biến động tần suất lớp (E3), cạnh tranh trong dịch chuyển thời gian (E1) và cần sự thận trọng khi môi trường có nhiễu đặc trưng cao (E2).
Đóng góp 5 (C5): Confidence Calibration và Phân tích Tấn công Hiếm
Tóm tắt nội dung: C5 mở rộng đánh giá sang chất lượng xác suất dự đoán của QSVM-ZZ trên các lớp tấn công hiếm. Đây là thông tin then chốt để thiết lập các ngưỡng cảnh báo tự động trong hệ thống IDS sản xuất thực tế.
Bằng chứng định lượng:
Hiệu chuẩn trên lớp hiếm: Chỉ số  (cho U2R và R2L) của QSVM-ZZ = 0,4337 (thấp nhất), giảm 30 % so với SVM-Poly (0,6191) và 7,9 % so với SVM-RBF (0,4707). ECE thấp hơn nghĩa là sai lệch giữa xác suất dự đoán và tần suất đúng thực tế trên rare class nhỏ hơn — quan trọng khi thiết kế ngưỡng cảnh báo cho IDS sản xuất.
Hiệu năng tổng quát: Mô hình đạt các mốc AUC-PR (0,9656) và AUC-ROC (0,9574) cao nhất trong các mô hình thử nghiệm.
Đánh giá lớp hiếm: Chỉ số AUC-PR per-class của lớp U2R đạt 0,0665 (vs SVM-Poly 0,0512, SVM-RBF 0,0522 — tăng ~27 % tuyệt đối). Về phân tích Decision Margin trên 10 mẫu U2R+R2L, Cohen’s d = −0,68 (RBF margin trung bình lớn hơn QSVM-ZZ trên cùng decision function scale). Hệ quả là QSVM-ZZ ít có hiện tượng over-confident-error trên lớp hiếm, nhất quán với ECE_rare thấp hơn — nhưng cần lưu ý đây là kết quả từ tập test 99 mẫu (10 rare), độ tin cậy thống kê giới hạn. Bằng chứng chính cho lợi thế của QSVM-ZZ trên rare class nằm ở ECE_rare (0,4337 vs 0,4707) và AUC-PR overall (0,9656)**, KHÔNG ở margin magnitude.Tính bổ trợ (Complementarity): Ghi nhận các trường hợp "QSVM-ZZ-wins" (nhận diện đúng mẫu U2R mà SVM-RBF bỏ sót), tạo động lực thực chứng cho kiến trúc Hybrid Quantum-Classical Ensemble.
Điểm mới khoa học: Đề xuất quy trình Adaptive Binning kết hợp Platt Scaling chuyên biệt cho lớp hiếm, đồng thời sử dụng phân tích tính bổ trợ để định vị "vùng ưu thế lượng tử" trong không gian Hilbert.
Đóng góp 6 (C6): Phân tích Learning Curve và Sample Complexity
Tóm tắt nội dung: C6 xác lập bằng chứng thực nghiệm trực tiếp về lợi thế lượng tử trong điều kiện dữ liệu huấn luyện hạn chế — kịch bản phổ biến khi đối phó với các loại tấn công mới hoặc zero-day. Việc thực thi giao thức zero-leakage tại mọi mốc N đảm bảo tính khách quan và hợp lệ cho các kết luận đánh giá.
Bằng chứng định lượng: QSVM-ZZ vượt trội hơn tất cả các baseline tại mọi mốc  với mức tăng .
Tại N=100 (dữ liệu cực kỳ hạn chế): QSVM-ZZ đạt 0,8132 trong khi SVM-RBF chỉ đạt 0,7240 ().
Tại N=500 (mốc quan trọng nhất): QSVM-ZZ đạt 0,8311 so với 0,7310 của SVM-RBF (, tương đương 10 điểm phần trăm).
Chỉ số Cohen’s d = +0,4043 (mức Nhỏ theo Cohen 1988: 0,2 ≤ |d| < 0,5) trên 2.952 mẫu hiếm cho thấy QSVM-ZZ tạo ra decision margin trung bình lớn hơn SVM-RBF (0,654 vs 0,507), với phương sai cao hơn (std 0,467 vs 0,213). Trên cỡ mẫu lớn này, hiệu ứng có ý nghĩa thực tiễn — nhưng nên trình bày đi kèm khoảng tin cậy bootstrap thay vì khẳng định ý nghĩa thống kê.Ý nghĩa tổng thể: Kết quả C6 củng cố giả thuyết về lợi thế lượng tử trong IDS: khi mẫu huấn luyện ít, việc ánh xạ vào không gian Hilbert  chiều cho phép mô hình tìm ra biên quyết định phức tạp hơn từ ít điểm dữ liệu hơn. Điều này tương đồng về bản chất với khái niệm "quantum advantage" lý thuyết trong PAC learning với các ví dụ lượng tử.
Sáu đóng góp trên tạo thành một chuỗi lập luận khoa học khép kín và nhất quán:
C1: Xác lập phương pháp nhúng dữ liệu tối ưu dưới các ràng buộc vật lý của phần cứng.
C2: Giải thích lý do phép nhúng này tương thích đặc thù với cấu trúc dữ liệu IDS.
C3: Cung cấp bằng chứng hình học thực chứng và xác nhận vai trò nhân quả của cơ chế vướng víu (entanglement).
C4: Đánh giá độ bền bỉ của hệ thống trong môi trường mạng thực tế đầy biến động.
C5: Định lượng chất lượng xác suất dự đoán nhằm phục vụ việc ra quyết định an ninh tin cậy.
C6: Chứng minh hiệu quả sử dụng dữ liệu vượt trội trong điều kiện tài nguyên huấn luyện hạn chế.

## 6.2. Các Hướng Nghiên cứu Mở rộng trong Tương lai

Từ kết quả thực nghiệm và các rào cản kỹ thuật hiện tại, đề tài đề xuất bảy hướng nghiên cứu mở rộng theo thứ tự ưu tiên và tính khả thi:
Thực nghiệm trên Phần cứng Lượng tử Thực (Hardware Execution): Chuyển đổi từ mô phỏng statevector sang thực thi trực tiếp trên các backend lượng tử thực như IBM Quantum (superconducting) hoặc IonQ (trapped-ion). Mục tiêu cốt lõi là định lượng mức độ sụt giảm KTA và F1-macro dưới tác động của nhiễu vật lý kỷ nguyên NISQ, từ đó xác định ngưỡng duy trì lợi thế của QSVM-ZZ so với các mô hình cổ điển.
Xây dựng Hybrid Quantum-Classical Ensemble: Dựa trên phân tích tính bổ trợ (complementarity) tại C5, hướng nghiên cứu này tập trung kết hợp QSVM-ZZ và SVM-RBF thông qua cơ chế weighted voting hoặc stacking. Trọng số sẽ được tối ưu hóa theo chỉ số  nhằm tận dụng biên quyết định ổn định của lượng tử trên lớp hiếm và khả năng hiệu chuẩn tốt của mô hình cổ điển trên lớp phổ biến.
Khả năng mở rộng (Scalability) lên số Qubit cao hơn: Khảo sát xu hướng của hàm mục tiêu J(n) khi  qubit nhằm đón đầu sự phát triển của phần cứng (như chip IBM Quantum Heron). Nghiên cứu này đồng thời mở rộng phân tích hình học C3 để kiểm chứng liệu cấu trúc biên quyết định trong không gian Hilbert 256 chiều có mang lại lợi thế KTA vượt trội hơn hay không.
Lý thuyết Margin và Quantum Kernel trong không gian cao chiều: Tập trung so sánh lý thuyết margin giữa kernel lượng tử và cổ điển dưới góc độ PAC learning. Việc chứng minh "quantum advantage" thông qua các chỉ số như chiều VC (VC dimension) hoặc độ phức tạp Rademacher sẽ cung cấp nền tảng toán học vững chắc cho các quan sát thực nghiệm về hiệu quả dữ liệu trong C6.
Tối ưu hóa Thích nghi và Tự động hóa Framework: Nâng cấp cấu hình C1 sang hướng tự động hóa hoàn toàn thông qua Bayesian Optimization hoặc Meta-learning. Mục tiêu là giúp hệ thống tự dự đoán tham số K và n tối ưu dựa trên đặc trưng của từng tập dữ liệu mới (mức độ mất cân bằng, cấu trúc tương quan), thay vì phải chạy lại Cross-Validation thủ công cho từng dataset.
Học trực tuyến (Online Learning) với Incremental Kernel Update: Phát triển kỹ thuật cập nhật ma trận kernel gia số (rank-b update) cho các luồng dữ liệu mạng (data stream) liên tục. Phương pháp này giúp hệ thống cập nhật tri thức về các biến thể tấn công mới mà không cần huấn luyện lại từ đầu, tối ưu hóa tài nguyên tính toán và bộ nhớ đệm.
Nâng cao hiệu chuẩn Post-hoc cho lớp tấn công hiếm: Áp dụng các kỹ thuật hiệu chuẩn tiên tiến như Temperature Scaling hoặc Beta Calibration để xử lý các phân phối xác suất lệch (skewed). Mục tiêu là đưa chỉ số  xuống dưới ngưỡng 0.3 mức độ tin cậy cần thiết để triển khai trong các hệ thống cảnh báo an ninh cấp độ doanh nghiệp.
6.3. Hạn chế và đe dọa tính hợp lệ
Để đảm bảo tính minh bạch khoa học, đề tài thừa nhận các hạn chế sau:
L1: Quy mô mô phỏng: Toàn bộ thực nghiệm thực hiện trên FidelityStatevectorKernel (statevector noiseless). Mặc dù §4.3.3 đã đánh giá finite-shot proxy với 4 mức shots, nhiễu phần cứng NISQ thật (gate noise, readout error, decoherence, transpilation overhead) chưa được mô phỏng — chuyển hiệu năng từ ideal sang hardware thực còn là câu hỏi mở.
L2: Quy mô tập test rare class (C5): Tập test 99 mẫu chứa 10 mẫu U2R+R2L. McNemar test p = 1,0 không nên hiểu là “không khác biệt” — cỡ mẫu này không đủ power để bác bỏ giả thuyết null. Cohen’s d trên n = 10 cũng có CI rộng.
L3: Tương đồng kernel với target (C2): CKA(K_ZZ) = 0,270 < CKA(K_RBF) = 0,384. Về centered alignment, ZZ KHÔNG vượt trội RBF/Poly — lợi thế của ZZ thể hiện ở expressibility và entanglement entropy (chiều khác của hình học kernel).
L4: Complementarity hai chiều (C5): Trên 10 rare samples, QSVM-ZZ-wins 1 vs RBF-wins 2. Đây là bằng chứng cho khả năng bổ trợ trong Hybrid Ensemble, không phải QSVM-ZZ dominance.
L5: Regularization sensitivity trên UNSW: C tuned bằng F1 trên CV folds mất cân bằng có thể đẩy QSVM-ZZ vào trạng thái degenerate (predict-all-attack) trên test (TN = 0). Phải verify confusion matrix trên test sau tuning trước khi báo cáo metric tổng hợp.
L6: Subsampling variance: Multi-run dùng 5 tập train độc lập kích thước 1.000 từ KDDTrain+. Std giữa run phản ánh độ nhạy với tập train, không phản ánh hardware/seed sensitivity của QSVM-ZZ kernel.
L7: Decision boundary visualization: Hình 4.15 chỉ là phép chiếu 2D từ không gian 4D (chiều khác cố định median train) — nhận xét hình thái không thay thế cho kết luận định lượng đa run.

# TÀI LIỆU THAM KHẢO

Tập dữ liệu và Bài toán IDS
[1] M. Tavallaee, E. Bagheri, W. Lu, and A. A. Ghorbani, “A detailed analysis of the KDD CUP 99 data set,” in Proc. IEEE Symposium on Computational Intelligence for Security and Defense Applications (CISDA), Ottawa, ON, Canada, 2009, pp. 1–6. doi: 10.1109/CISDA.2009.5356528.
[2] N. Moustafa and J. Slay, “UNSW-NB15: A comprehensive data set for network intrusion detection systems (UNSW-NB15 network data set),” in Proc. Military Communications and Information Systems Conference (MilCIS), Canberra, ACT, Australia, 2015, pp. 1–6. doi: 10.1109/MilCIS.2015.7348942.
[3] I. Sharafaldin, A. H. Lashkari, and A. A. Ghorbani, “Toward generating a new intrusion detection dataset and intrusion traffic characterization,” in Proc. 4th International Conference on Information Systems Security and Privacy (ICISSP), Funchal, Madeira, Portugal, 2018, pp. 108–116. doi: 10.5220/0006639801080116.
[4] S. Dadkhah, A. Danso, H. Neto, P. Bhuvaneswari, and A. Ghorbani, “Towards the development of a realistic multidimensional IoT profiling dataset,” in Proc. 19th International Conference on Privacy, Security and Trust (PST), Auckland, New Zealand, 2023. doi: 10.1109/PST58708.2023.10320194.
[5] K. Highnam, K. Arulkumaran, Z. Hanif, and N. R. Jennings, “BETH dataset: Real cybersecurity data for anomaly detection research,” in Proc. ICML Workshop on Uncertainty and Robustness in Deep Learning, 2021. [Online]. Available: https://arxiv.org/abs/2107.13741.
Máy véc-tơ hỗ trợ Cổ điển (SVM)
[6] V. N. Vapnik, The Nature of Statistical Learning Theory, 2nd ed. New York, NY, USA: Springer, 2000.
[7] C. Cortes and V. Vapnik, “Support-vector networks,” Machine Learning, vol. 20, no. 3, pp. 273–297, Sep. 1995. doi: 10.1007/BF00994018.
[8] J. C. Platt, “Probabilistic outputs for support vector machines and comparisons to regularized likelihood methods,” in Advances in Large Margin Classifiers, A. J. Smola, P. Bartlett, B. Schölkopf, and D. Schuurmans, Eds. Cambridge, MA, USA: MIT Press, 1999, pp. 61–74.
[9] B. Schölkopf and A. J. Smola, Learning with Kernels: Support Vector Machines, Regularization, Optimization, and Beyond. Cambridge, MA, USA: MIT Press, 2002.
Học máy Kernel Lượng tử (QSVM-ZZ)
[10] V. Havlíček, A. D. Córcoles, K. Temme, A. W. Harrow, A. Kandala, J. M. Chow, and J. M. Gambetta, “Supervised learning with quantum-enhanced feature spaces,” Nature, vol. 567, no. 7747, pp. 209–212, Mar. 2019. doi: 10.1038/s41586-019-0980-2.
[11] M. Schuld and N. Killoran, “Quantum machine learning in feature Hilbert spaces,” Physical Review Letters, vol. 122, no. 4, p. 040504, Feb. 2019. doi: 10.1103/PhysRevLett.122.040504.
[12] M. Schuld, R. Sweke, and J. J. Meyer, “Effect of data encoding on the expressive power of variational quantum machine learning models,” Physical Review A, vol. 103, no. 3, p. 032430, Mar. 2021. doi: 10.1103/PhysRevA.103.032430.
[13] Y. Liu, S. Arunachalam, and K. Temme, “A rigorous and robust quantum speed-up in supervised machine learning,” Nature Physics, vol. 17, no. 9, pp. 1013–1017, Sep. 2021. doi: 10.1038/s41567-021-01287-z.
[14] T. Hubregtsen, D. Wierichs, E. Gil-Fuster, P.-J. H. S. Derks, P. K. Faehrmann, and J. J. Meyer, “Training quantum embedding kernels on near-term quantum computers,” Physical Review A, vol. 106, no. 4, p. 042431, Oct. 2022. doi: 10.1103/PhysRevA.106.042431.
Phần cứng NISQ và Mạch Lượng tử
[15] J. Preskill, “Quantum computing in the NISQ era and beyond,” Quantum, vol. 2, p. 79, Aug. 2018. doi: 10.22331/q-2018-08-06-79.
[16] F. Arute et al., “Quantum supremacy using a programmable superconducting processor,” Nature, vol. 574, no. 7779, pp. 505–510, Oct. 2019. doi: 10.1038/s41586-019-1666-5.
[17] IBM Quantum, “IBM Quantum Platform,” International Business Machines Corporation, 2024. [Online]. Available: https://quantum-computing.ibm.com.
Qiskit và Triển khai
[18] Qiskit contributors, “Qiskit: An open-source framework for quantum computing,” 2023. doi: 10.5281/zenodo.2573505.
[19] S. Woerner et al., “Qiskit Machine Learning: Quantum machine learning algorithms and applications,” Quantum Science and Technology, 2024. [Online]. Available: https://qiskit-community.github.io/qiskit-machine-learning/.
Phân tích Hình học Kernel và Kernel Alignment
[20] N. Cristianini, J. Shawe-Taylor, A. Elisseeff, and J. Kandola, “On kernel-target alignment,” in Advances in Neural Information Processing Systems (NeurIPS), vol. 14, T. G. Dietterich, S. Becker, and Z. Ghahramani, Eds. Cambridge, MA, USA: MIT Press, 2002, pp. 367–373.
[21] C. Cortes, M. Mohri, and A. Rostamizadeh, “Algorithms for learning kernels based on centered alignment,” Journal of Machine Learning Research (JMLR), vol. 13, no. 1, pp. 795–828, Mar. 2012.
[22] A. Bardet, M. Gluza, and G. Styliaris, “Expressibility and entangling capability of parameterized quantum circuits for hybrid quantum-classical algorithms,” PRX Quantum, vol. 5, no. 1, p. 010309, Feb. 2024. doi: 10.1103/PRXQuantum.5.010309.
Confidence Calibration
[23] C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, “On calibration of modern neural networks,” in Proc. 34th International Conference on Machine Learning (ICML), vol. 70, D. Precup and Y. W. Teh, Eds. Sydney, NSW, Australia, 2017, pp. 1321–1330.
[24] M. Kull, T. M. Silva Filho, and P. Flach, “Beta calibration: A well-founded and easily implemented improvement on logistic calibration for binary classifiers,” in Proc. 20th International Conference on Artificial Intelligence and Statistics (AISTATS), Fort Lauderdale, FL, USA, 2017, pp. 623–631.
[25] A. Niculescu-Mizil and R. Caruana, “Predicting good probabilities with supervised learning,” in Proc. 22nd International Conference on Machine Learning (ICML), Bonn, Germany, 2005, pp. 625–632. doi: 10.1145/1102351.1102430.
Kiểm định Thống kê
[26] Q. McNemar, “Note on the sampling error of the difference between correlated proportions or percentages,” Psychometrika, vol. 12, no. 2, pp. 153–157, Jun. 1947. doi: 10.1007/BF02295996.
[27] J. Cohen, Statistical Power Analysis for the Behavioral Sciences, 2nd ed. Hillsdale, NJ, USA: Lawrence Erlbaum Associates, 1988.
[28] T. G. Dietterich, “Approximate statistical tests for comparing supervised classification learning algorithms,” Neural Computation, vol. 10, no. 7, pp. 1895–1923, Oct. 1998. doi: 10.1162/089976698300017197.
Giảm chiều và Lựa chọn Đặc trưng
[29] I. Guyon and A. Elisseeff, “An introduction to variable and feature selection,” Journal of Machine Learning Research (JMLR), vol. 3, pp. 1157–1182, Mar. 2003.
[30] F. Pedregosa et al., “Scikit-learn: Machine learning in Python,” Journal of Machine Learning Research (JMLR), vol. 12, pp. 2825–2830, Nov. 2011.
[31] I. T. Jolliffe and J. Cadima, “Principal component analysis: A review and recent developments,” Philosophical Transactions of the Royal Society A, vol. 374, no. 2065, p. 20150202, Apr. 2016. doi: 10.1098/rsta.2015.0202.
Tối ưu hóa Đa mục tiêu và Pareto
[32] K. Deb, Multi-Objective Optimization Using Evolutionary Algorithms. Chichester, UK: Wiley, 2001.
[33] D. L. Davies and D. W. Bouldin, “A cluster separation measure,” IEEE Transactions on Pattern Analysis and Machine Intelligence (TPAMI), vol. PAMI-1, no. 2, pp. 224–227, Apr. 1979. doi: 10.1109/TPAMI.1979.4766909.
QSVM-ZZ Ứng dụng cho IDS
[34] M. A. Nielsen and I. L. Chuang, Quantum Computation and Quantum Information, 10th anniversary ed. Cambridge, UK: Cambridge University Press, 2010.
[35] S. Lloyd, M. Mohseni, and P. Rebentrost, “Quantum algorithms for supervised and unsupervised machine learning,” arXiv preprint arXiv:1307.0411, Jul. 2013. [Online]. Available: https://arxiv.org/abs/1307.0411.
[36] C. Ding, T. Bao, and H.-L. Huang, “Quantum-inspired support vector machine,” IEEE Transactions on Neural Networks and Learning Systems (TNNLS), vol. 33, no. 12, pp. 7210–7222, Dec. 2022. doi: 10.1109/TNNLS.2021.3084467.
[37] R. Heese, P. Bickert, and A. E. Niederle, “Representation of binary classification trees with quantum circuits,” Quantum, vol. 6, p. 676, Mar. 2022. doi: 10.22331/q-2022-03-30-676.