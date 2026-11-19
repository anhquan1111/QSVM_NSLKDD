# Paper 1 → QMI: kết quả giai đoạn 1

Kế hoạch: `docs/PAPER1_KE_HOACH_QMI.md`. Cập nhật 19-11-2026.

| Việc | Trạng thái |
|---|---|
| 1.1 Bỏ dòng test trùng train | UNSW xong (2/36 ô đổi, không đổi chiều); NSL-KDD vướng run 2 N = 10⁴ không tái hiện, đang chạy chẩn đoán |
| 1.2 Bỏ "exponential", không nói nhân quả | Xong danh sách câu + máy kiểm |
| 1.3 Bỏ "parity" | Xong danh sách câu + máy kiểm |
| 1.4 Mâu thuẫn enrichment / 7 trên 10 | Tự soi xong 4 chỗ (dưới); chờ thư R3 để đối chiếu |
| 1.5 Nhiễu 10 run | Xong: `runners/verify_noise10.py` chạy lại 40/40, mã thoát 0 |
| 1.6 Đối chiếu Cirillo 2026 | Xong bảng (dưới) |

## 1.1 Bỏ dòng test trùng train

Dòng trùng = dòng test có 41 (NSL-KDD) / 34 (UNSW) đặc trưng thô y hệt một dòng của toàn bộ raw train.
Chạy lại 7 mô hình với siêu tham số đọc từ cache, lưu dự đoán từng dòng, chấm trên test đầy đủ và test
đã bỏ trùng. Script: `runners/run_dedup_sensitivity.py` → `runners/analyze_dedup_sensitivity.py`.
Kết quả: `results/<ds>/c4_dedup/dedup_pairwise_before_after.csv`, `dedup_verdict_changes.csv`.

**UNSW-NB15 (xong 19-11, 120/120 file qua cổng tái hiện, 36 ô ngoài bản đồ 110 ô).** Test bỏ 20.851/82.332
dòng (25,3 %). Ô đổi kết luận, nhánh `tuned_per_N`, test đầy đủ: **2/36**, cả hai từ có ý nghĩa thành không
kết luận, không ô nào đổi chiều:

| N | So với | Trước: Δ, p (Holm) | Sau: Δ [CI 95 %], p |
|---|---|---|---|
| 5000 | SVM-Poly2 | +0,040, 0,049 (nghiêng quantum) | +0,038 [−0,001; +0,078], 0,064 |
| 5000 | XGBoost | −0,016, 0,020 (nghiêng cổ điển) | −0,015 [−0,030; +0,001], 0,064 |

Đếm 36 ô (quantum / cổ điển / không kết luận): trước 12/11/13 → sau 11/10/15. Nhánh `tuned_once`: 2/36 ô
đổi (cùng kiểu, ra không kết luận). Hai ô đổi đều có p sát 0,05 từ trước; bỏ trùng làm hiệu nhỏ lại chút
(|Δ| giảm 0,001–0,002), không đổi dấu.

**NSL-KDD: chưa xong.** Lần chạy đủ dừng ở file 147/260: `natural_refit_per_N_*_N10000_run2` (cả frozen_c2
lẫn tuned_per_N) không tái hiện được. Mọi mô hình đều lệch, kể cả SVM tuyến tính và RF (tất định), nên tập
train dựng lại khác tập của cache gốc. Run 2 ở N = 5000 và run 1, 3 ở N = 10⁴ thì khớp. Đã loại hai giả
thuyết: lưới N khác (thử 52 lưới con) và seed của run khác (thử run 1–10): SVM tuyến tính cache cho
accuracy 0,741661, không cách dựng nào ra số này. Chưa rõ nguyên nhân. Đang chạy nốt các file còn lại ở
chế độ chẩn đoán (`--diagnose`) để biết còn file nào lệch.

**Cách xử lý file không tái hiện (chốt 19-11, chủ nhân giao Claude chọn).**
- *Số chính:* "trước" và "sau" đều lấy từ lần chạy lại (cột `rerun_*` ↔ `after_*`, chạy với
  `--include-failed`). Câu hỏi của 1.1 là bỏ trùng có đổi kết luận không; hai số cùng một lần chạy nên
  phép so vẫn sạch, dù tập train của file đó khác cache gốc. Bài ghi rõ: "2 trong 260 lần huấn luyện
  không dựng lại được đúng tập train gốc; chúng tôi dùng tập dựng lại cho cả hai phía".
- *Kiểm phụ:* bỏ hẳn run 2 ở N = 10⁴ (`--allow-partial`, ô đó còn 9 run). Hai cách cùng kết luận thì
  việc lệch cache không ảnh hưởng; khác nhau thì ghi cả hai.
- Bảng "trước" của bài (cache gốc) không đổi: phân tích đã khớp 168/168 + 120/120 ô với bảng lưu.

**Số trùng trong bài sai định nghĩa.** `07_limitations.tex:122–123` ghi NSL-KDD "610 test rows identical …
in both features and label (617 match on features alone)". Đếm lại trên `KDDTrain+.txt` / `KDDTest+.txt`:
trùng 41 đặc trưng = **664**; trùng đặc trưng + nhãn tấn công = 610; trùng đặc trưng + nhãn nhị phân = 617.
Vậy "617 on features alone" sai, phải là 664. UNSW: bài ghi 25,0 %, mặt nạ ta dùng ra 25,3 % (chỉ theo đặc
trưng); GĐ 2 ghi rõ định nghĩa kèm số. Câu "We have not re-scored … per-row predictions were not retained"
phải thay bằng kết quả mục này.

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

## 1.4 Mâu thuẫn (tự soi, chưa đối chiếu thư R3 nguyên văn)

**(a) "10/10" so với "7/10": lỗi thật, đã kiểm bằng số.** `results/unsw/c4_revision/u1_nstar_robustness.csv`:
n* = 6 ở 10/10 tập con khi ε = 0,02 và 0,05; khi ε = 0,1 chỉ 7/10 (3/10 ra n* = 5). Nhưng
`01_introduction.tex:72–74` ghi gọn "recovered on 10/10 independent subsets", và `03b_theory.tex:143–145`
còn thêm "and under every threshold perturbation we tested", **sai** với chính `05_results.tex:253–254`.
Cách sửa: mọi chỗ ghi đủ "10/10 với ε ≤ 0,05, 7/10 với ε = 0,1". Máy kiểm: luật "10/10 không kèm 7/10"
trong `audit_wording_r3.py` (đang bắt 2 chỗ).

**(b) Nhánh tăng mẫu tấn công hiếm: nói "dẫn" khi chưa có ý nghĩa thống kê.** `05_results.tex:186–196`:
nhánh tăng mẫu để 26/30 ô "không kết luận", nhưng câu sau lại viết "the tree ensembles lead under both
priors" (chỉ là dấu của hiệu, không phải kết luận). Tóm tắt và `01_introduction.tex:67–70` lặp lại "lead".
Số (`results/nslkdd/regime_map_rows.csv`, khối C4, N = 100…2000): so với RF và XGBoost, nhánh tăng
mẫu đạt ý nghĩa ở **0/10** ô (dấu âm 9/10; RF ở N = 200 là +0,003), nhánh tự nhiên **8/10** (trừ N = 2000).
So với SVM-RBF: 0/5 ở cả hai nhánh. 4 ô có kết luận của nhánh tăng mẫu là Linear N = 1000, 2000 (nghiêng
quantum), Z-map và RBF ở N = 2000 (nghiêng cổ điển); không ô nào là cây.
Cách sửa: "dưới phân phối tự nhiên cây dẫn có ý nghĩa ở 8/10 ô; dưới tăng mẫu hiệu cùng dấu âm nhưng
0/10 ô đạt ý nghĩa sau hiệu chỉnh".

**(c) "Tấn công hiếm" hai nghĩa dễ đọc thành ngược nhau.** `05_results.tex:~232`: ở N = 10⁴ phân phối
tự nhiên, QSVM "far better on rare attacks than either tree ensemble" (F1 lớp hiếm 0,507 so với 0,33),
trong khi nhánh tăng mẫu tấn công hiếm thì cây dẫn (F1 macro, N ≤ 2000). Hai câu đo hai thứ khác nhau
(F1 lớp hiếm ở N lớn, F1 macro ở N nhỏ). Cách sửa: nói rõ chỉ số và cỡ N ở cả hai chỗ, một câu nối hai
kết quả.

**(d) Bản đồ 110 ô gộp hai protocol.** 68/110 ô (kể cả hai hiệu ứng lớn nhất, ô C3 cân bằng 50/50) từ
nhánh tăng mẫu, trong khi bài nói nhánh này "không quyết được" về đảo chiều. Bài đã tách đếm (42 ô tự
nhiên: 11/9/22) nhưng tóm tắt vẫn đưa tổng 21/21/68 lên trước. Cách sửa ở GĐ 2: tóm tắt đưa khối tự
nhiên lên trước, tổng 110 ô để sau.

Khi có thư R3 nguyên văn: đối chiếu xem R3 chỉ đúng (a)–(d) hay còn chỗ khác.

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
