# Paper 1 → QMI: kết quả giai đoạn 1

Kế hoạch: `docs/PAPER1_KE_HOACH_QMI.md`. Cập nhật 19-11-2026.

| Việc | Trạng thái |
|---|---|
| 1.1 Bỏ dòng test trùng train | Đang dựng script (chưa chạy) |
| 1.2 Bỏ "exponential", không nói nhân quả | Xong danh sách câu + máy kiểm |
| 1.3 Bỏ "parity" | Xong danh sách câu + máy kiểm |
| 1.4 Mâu thuẫn enrichment / 7 trên 10 | Chờ thư từ chối nguyên văn |
| 1.5 Nhiễu 10 run | Xong: `runners/verify_noise10.py` chạy lại 40/40, mã thoát 0 |
| 1.6 Đối chiếu Cirillo 2026 | Xong bảng (dưới) |

## Máy kiểm chữ: `runners/audit_wording_r3.py`

`uv run python runners/audit_wording_r3.py [thư mục bài]` (mặc định `paper/paper1`). Bắt bốn loại:
"exponential" nói về số đo của ta; câu nhân quả nối độ tập trung với kết quả; "parity / on par /
tied"; chỗ nhắc phản biện hay bản đã nộp. Ở GĐ 2 chạy trên bản viết lại, phải ra 0.

Trên `paper/paper1` (19-11): exponential 1, nhân quả 10, parity 5, nhắc phản biện 82.
Bắt nhầm đã biết (đọc tay rồi bỏ qua): `02_background.tex:69` (nói về "mechanism" của hai bài
khác). Chỗ trong `\revnote` sẽ mất khi bỏ hết revnote ở GĐ 2.

## 1.2 Câu cần đổi: tập trung Gram matrix

Ta đo 7 độ rộng (n = 4…10): r = +0,77 [+0,04; +0,96] cho ZZ, r = +0,32 [−0,57; +0,87] cho Z; hiệu
hai tương quan z = 0,97, p = 0,33. Chỉ được nói **"đi cùng"**, không nói "gây ra", "cơ chế", "lũy thừa".

| Chỗ | Câu hiện tại | Cách nói mới |
|---|---|---|
| `05_results.tex:285` | "The mechanism is measurable in the Gram matrix…" | Gram matrix đo được độ tập trung; nó đi cùng F1 thấp hơn |
| `05_results.tex:307` | "As the Gram matrix flattens, accuracy follows it down." | Bỏ; thay bằng r và khoảng tin cậy, nói rõ 7 điểm chỉ cho thấy tương quan |
| `05_results.tex:309` | "This is the exponential-concentration phenomenon of [Thanasilp]…" | "phù hợp với dự đoán của [Thanasilp]", không gọi là lũy thừa (7 điểm không phân biệt được lũy thừa với dạng khác) |
| `02_background.tex:35` | "the concentration is what eventually destroys it" | "chúng tôi đo cả hai và thấy độ tập trung đi cùng mức giảm" |
| `02_background.tex:187` | "a measured mechanism, Gram-matrix concentration, that predicts…" | "một đại lượng đo được đi cùng…" |
| `01_introduction.tex:76–79`, tóm tắt `document.tex:70` | "widening destroys the kernel … The mechanism is visible in the Gram matrix" | Phần độ rộng là can thiệp thật (ta đổi n) nên được nói "mạch rộng hơn thì 48/48 so sánh nghiêng cổ điển"; phần Gram matrix chỉ nói "đi cùng" |

Câu ở `02_background.tex:30` thuật lại định lý của Thanasilp (tập trung lũy thừa theo số qubit)
thì **giữ**: đó là kết quả đã chứng minh của họ.

## 1.3 Câu cần đổi: "parity"

Số thật (cột tham chiếu XGBoost đủ 122 đặc trưng, `tables/ref_arm_macros.tex`): Δ tại N = 5000 là
+0,0014 [−0,0064; +0,0091], tại N = 10⁴ là +0,0021 [−0,0052; +0,0094]. Cả hai khoảng chứa 0.
Cách nói mới: "không khác biệt có ý nghĩa (Δ = …, CI 95 % […]); thiết kế này không đủ để kết
luận hai bên ngang nhau." Áp ở: tóm tắt `document.tex:60–65`, `01_introduction.tex:59–67`,
`05_results.tex:211`, `06_regimemap.tex:50`, `08_conclusion.tex:20–24`.

## 1.6 Đối chiếu Cirillo, Esposito, Seo 2026

QMI vol. 8, art. 27, đăng 11-03-2026, DOI 10.1007/s42484-026-00379-4 (đọc toàn văn HTML; số trong
bảng 3, 10, 12, 13, 19–21 của họ không hiện). Bài mình đã trích họ ở `02_background.tex` (II-B).

| | Cirillo et al. 2026 | Bài mình |
|---|---|---|
| Dữ liệu | ToN_IoT (chính) + NSL-KDD (chỉ chạy lại cấu hình tốt nhất) §2.2, §5.1.3 | NSL-KDD + UNSW-NB15 |
| Lấy mẫu | Cố định, cân bằng 15 % mỗi lớp; NSL-KDD 15.114 / 3.780 §4 | Quét N từ 100 tới 10⁴, hai phân phối lớp (tự nhiên, tăng mẫu hiếm); test đầy đủ |
| Mô hình lượng tử | Pegasos-QSVC (SGD, C = 1000), 378 cấu hình, 14 feature map; VQC; HQNN §5 | QSVC kernel chính xác, ZZ (reps 2, full) + đối chứng Z-map |
| Baseline | SVM (kernel không nêu), XGBoost, RF, NN; cách tune không nêu §7 | SVM linear / poly2 / RBF, RF, XGBoost; tune đối xứng |
| Nhiễu | FakeLagosV2, FakeNairobiV2, FakePerth, 1024 shot §4.2 | FakeManilaV2, 10 run |
| Lặp | 4 seed, trung bình ± độ lệch §4.1 | 10 run ghép cặp |
| Thống kê | Không có kiểm định | Wilcoxon ghép cặp, hiệu chỉnh đa so sánh |
| Kết luận | "does not aim to demonstrate quantum advantage" §1; QSVC 95,35 % ở 4 đặc trưng "not attained by the classical models" §7, trong khi XGBoost đạt 99,1 %; CNOT 20–35 cân bằng tốt nhất §8.2 | 110 ô: 21 nghiêng quantum / 21 nghiêng cổ điển / 68 không kết luận; thứ hạng đảo chiều theo N |

**Họ đã làm, mình không được nhận là mới:** QSVM cho IDS trên NSL-KDD có mô hình nhiễu (fake
backend IBM, không phần cứng thật); so ZZ full với Z-map không vướng víu; PCA về 4 qubit; baseline
RF, XGBoost cùng số chiều; nhiều seed.

**Mình khác (dùng để định vị ở GĐ 2):** (1) quét cỡ train và thấy thứ hạng đảo chiều theo N, họ
dùng một cỡ cố định; (2) kiểm định ghép cặp có hiệu chỉnh, họ không có kiểm định, nên câu "not
attained by the classical models" của họ chưa được kiểm; (3) tune đối xứng và tách ba kernel SVM;
(4) đo độ tập trung Gram matrix theo độ rộng; (5) UNSW-NB15 và phân tích dòng test trùng train.
