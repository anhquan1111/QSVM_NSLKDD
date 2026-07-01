# Tóm tắt và giải thích Paper 2

> Bản tóm tắt tiếng Việt đi kèm bài báo, giúp người đọc nắm nhanh nội dung và ý nghĩa
> của Paper 2 trước khi đọc bản tiếng Anh đầy đủ.

---

## 1. Paper 2 là gì

Paper 2 là một **bài báo đồng hành (companion paper)** đi cùng Paper 1. Cả hai dùng chung
bộ dữ liệu **NSL-KDD** và chung mô hình **QSVM bốn qubit với ZZFeatureMap**, nhưng trả lời
hai câu hỏi khác nhau:

- **Paper 1:** *Khi nào QSVM thắng các mô hình cổ điển về hiệu năng (độ chính xác, F1)?*
- **Paper 2:** *Liệu dự đoán của QSVM có đủ đáng tin cậy để triển khai trong một hệ thống
  phát hiện xâm nhập thật hay không?*

Nói cách khác, Paper 1 quan tâm mô hình **đoán đúng đến đâu**, còn Paper 2 quan tâm khi mô
hình báo "đây là tấn công với xác suất 90%" thì **con số 90% đó có đáng tin không**. Đây là
hai trục đánh giá độc lập, nên hai bài báo bổ trợ nhau chứ không trùng lặp.

---

## 2. Vì sao chọn hướng "độ tin cậy" thay vì tiếp tục so độ chính xác

Trên dữ liệu dạng bảng như NSL-KDD, các mô hình học máy mạnh (XGBoost, Random Forest) và
mạng nơ-ron thường **chính xác hơn** một QSVM bị giới hạn ở bốn chiều. Nếu cố chứng minh
"QSVM chính xác hơn deep learning / machine learning" thì rất khó thuyết phục và dễ bị phản
biện bác bỏ.

Vì vậy chúng tôi chuyển trọng tâm sang **calibration** (mức độ đáng tin của xác suất dự
đoán). Đây là điểm QSVM thực sự có lợi thế, đồng thời là một **khoảng trống nghiên cứu**:
gần như chưa có công trình nào đánh giá calibration của quantum kernel cho phát hiện xâm
nhập, cũng chưa ai so QSVM với các mô hình cây mạnh trên trục này.

---

## 3. Paper 2 khác Paper 1 ở điểm nào

| Tiêu chí | Paper 1 | Paper 2 |
|---|---|---|
| Câu hỏi | Khi nào QSVM thắng về **hiệu năng**? | Dự đoán QSVM có **đáng tin** không? |
| Thước đo | F1, KTA, accuracy | **ECE, Brier score, AUC-PR** |
| Đối thủ so sánh | Chỉ SVM cổ điển (RBF/Poly/Linear) | Thêm **Random Forest, XGBoost** |
| Phạm vi | Cả khung sáu đóng góp | Chỉ **độ tin cậy / calibration** |
| Kết luận | Lợi thế hiệu năng theo từng chế độ | Lợi thế độ tin cậy theo từng chế độ |

---

## 4. Phương pháp tóm tắt

- **Quy trình chung, không rò rỉ dữ liệu:** mọi mô hình đi qua cùng một pipeline
  (SelectKBest 20 đặc trưng → PCA 4 chiều → chuẩn hóa về `[0, π]`). Nhờ vậy, khác biệt giữa
  các mô hình chỉ đến từ bản thân bộ phân loại, không phải từ khâu xử lý dữ liệu.
- **Bốn mô hình so sánh:** QSVM-ZZ, SVM-RBF, Random Forest, XGBoost.
- **Hiệu chỉnh công bằng:** mọi mô hình đều được Platt scaling (fit trên train, áp dụng trên
  test) trước khi đo calibration.
- **Thống kê chắc chắn:** trung bình qua **năm lần chạy** độc lập (mean ± độ lệch chuẩn), kèm
  **Cohen's d** để đo độ lớn hiệu ứng.

---

## 5. Kết quả chính

### 5.1. Nơi QSVM thắng rõ nhất — nhóm tấn công hiếm (U2R, R2L)

Đây là nhóm dưới 1% dữ liệu, cũng là nhóm **nguy hiểm và khó nhất**. Trên nhóm này, QSVM cho
xác suất **đáng tin nhất** (ECE và Brier thấp nhất):

| Mô hình | ECE (thấp = tốt) | Brier (thấp = tốt) | AUC-PR | F1 |
|---|---|---|---|---|
| **QSVM-ZZ** | **0.450** | **0.329** | 0.931 | 0.776 |
| SVM-RBF | 0.539 | 0.367 | 0.913 | 0.782 |
| Random Forest | 0.647 | 0.629 | 0.947 | 0.785 |
| XGBoost | 0.672 | 0.656 | 0.944 | 0.796 |

Khoảng cách so với hai mô hình cây rất lớn (**Cohen's d từ 1.9 đến 3.6** — mức "hiệu ứng
lớn"). QSVM cũng đáng tin nhất ở **điểm vận hành cân bằng** (ECE 0.099 — thấp nhất) và trong
**điều kiện ít dữ liệu** (từ 200 mẫu trở lên).

### 5.2. Nơi QSVM không dẫn đầu (báo cáo trung thực)

Khi phân phối lệch mạnh (attack-heavy, DoS-only) và khi dữ liệu **trôi dạt theo thời gian**
(KDDTest-21), QSVM chỉ ở mức **cạnh tranh**; Random Forest hiệu chỉnh tốt hơn. Chúng tôi nêu
rõ các điểm thua này để tránh thổi phồng.

### 5.3. Hai phát hiện đáng chú ý

1. **Xếp hạng tốt không đồng nghĩa với đáng tin:** Random Forest và XGBoost xếp hạng (AUC-PR)
   tốt hơn nhưng "quá tự tin" — Brier cao gần gấp đôi QSVM. Với hệ thống an ninh phải dựa vào
   độ tin cậy của cảnh báo, đây là điểm bất lợi của mô hình cây.
2. **Platt scaling chỉ hợp với mô hình dựa trên margin:** nó cải thiện calibration cho QSVM
   và SVM, nhưng làm xấu đi calibration của mô hình cây.

---

## 6. Kết luận và ý nghĩa

Thông điệp tổng quát là **"độ tin cậy theo từng chế độ" (regime-specific reliability)**: QSVM
không phải mô hình chính xác nhất, nhưng là mô hình **đáng tin cậy nhất ở đúng những nơi khó
và nguy hiểm nhất** — tấn công hiếm và điều kiện ít dữ liệu. Kết luận này song song với Paper 1
(lợi thế hiệu năng cũng chỉ xuất hiện theo từng chế độ), nên hai bài củng cố lẫn nhau.

---

## 7. Quan hệ với Paper 1 và cách sử dụng

Paper 2 đóng vai trò một **"lưới an toàn"** cho Paper 1, linh hoạt theo từng tình huống:

| Tình huống Paper 1 | Vai trò của Paper 2 |
|---|---|
| **Bị từ chối** | Là một bài độc lập có thể nộp riêng, tăng cơ hội có ít nhất một bài được chấp nhận |
| **Bị yêu cầu chỉnh sửa lớn** (ví dụ phản biện đòi so sánh với deep learning / machine learning) | Lấy ngay kết quả của Paper 2 để bổ sung và trả lời phản biện |
| **Được chấp nhận** | Nộp tiếp như một bài đồng hành, trích dẫn chéo Paper 1 |

Vì hai bài **khác trục rõ ràng** (hiệu năng và độ tin cậy), việc tồn tại song song là an toàn
về mặt liêm chính học thuật, không bị xem là nộp trùng nội dung.

---

## 8. Ghi chú về phối hợp

Phần đóng góp về robustness dưới **phân phối lệch và trôi dạt thời gian** (prior-shift và
temporal) sử dụng kết quả do thành viên phụ trách *contribution 4* thực hiện; bài báo dùng
đúng số liệu và hình của phần này. Các phần còn lại (calibration, tấn công hiếm, low-data,
Platt scaling) do nhóm thực hiện trên cùng một khung đánh giá để bảo đảm tính nhất quán.
