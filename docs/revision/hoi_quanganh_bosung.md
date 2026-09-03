Bổ sung 2 câu nữa — t vừa dựng xong pipeline C4 rồi chạy gate đối chiếu với `c2_per_run.csv` ở N=1000.

Tin tốt trước: **5/7 model trùng chính xác tới chữ số cuối** (chênh 0.00e+00 cả 10 run) — QSVM_ZZ, QSVM_Z, SVM_Linear, SVM_RBF, RandomForest. Nên số của m chuẩn, và code t khớp code m.

Hai chỗ lệch:

**3. XGBoost lệch cả 10/10 run, tối đa 0.020 — phụ thuộc số thread của máy**

Cùng seed, cùng data, cùng tham số. Lặp lại trên **cùng** máy thì giống hệt, đổi máy thì khác. Nguyên nhân: `tree_method='hist'` gộp histogram theo thứ tự thread. Máy t 16 core, run 1:

| cấu hình | F1 |
|---|---|
| `n_jobs=-1` (m đang dùng) | 0.836520 |
| `n_jobs=1` | 0.853307 |
| C2 gốc của m | 0.856627 |

Mean 10 run gần như không đổi (0.8503 vs 0.8516) nên **kết luận khoa học không đổi** — XGB vẫn là baseline mạnh nhất, QSVM-ZZ vẫn thứ hai. Nhưng từng run lệch tới 0.02, reviewer chạy lại trên máy khác sẽ ra bảng khác. Mà XGB chính là model mình dùng để nói *"QSVM không thắng được XGBoost"* — luận điểm đó đang tựa trên số không tái tạo được. Đúng chỗ R4-2 soi.

→ M chạy lại C2/C3 với `n_jobs=1` được không? C4 t đã chốt dùng `n_jobs=1`.

**4. Một ô cache C2 không tái tạo được: `SVM_Poly2` run 3**

C2 lưu **0.819928**, t tính lại ra **0.823237**. Đã quét hết `C ∈ {0.1…10}` × {StandardScaler, MinMax} × {degree 2, 3} — không cấu hình nào ra 0.819928.

`run_3_results.json` và `c2_per_run.csv` khớp nhau nên export đúng; có vẻ là entry cũ còn sót. `config_signature` chỉ băm `C2_CONFIG` chứ không băm hyperparameter đã tune lẫn hash artifact C1, nên đổi tuning result thì cache run vẫn không tự invalid.

Ảnh hưởng nhỏ (1/70 ô, mean Poly2 lệch +0.0003) nhưng m chạy lại run 3 với `FORCE_RERUN=True` cho sạch nhé.

---

Tiện thể báo m 1 phát hiện nữa về dữ liệu, không phải lỗi của m nhưng cả bài phải khai:

**`train_run{i}.csv` giàu lớp hiếm gấp ~12 lần tỉ lệ tự nhiên**

| tập | Rare (R2L+U2R) |
|---|---|
| KDDTrain+ đầy đủ | **0.83%** |
| `train_run{i}` (nền của C2/C3 + Table IV) | **10.0%** |
| KDDTest+ | 13.1% |

Không sai — nó làm tập train gần phân bố test hơn. Nhưng bài **chưa hề ghi điều này**, mà nó giải thích một phần R1-9 (*"F1 của classical thấp bất thường so với literature"*): literature thường báo accuracy trên random split của KDDTrain+, còn mình báo macro-F1 trên full KDDTest+ với train được làm giàu lớp hiếm.

T sẽ viết một đoạn khai rõ chuyện này trong phần "protocol vs literature". M nhớ giữ nhất quán khi viết C2/C3 nhé.
