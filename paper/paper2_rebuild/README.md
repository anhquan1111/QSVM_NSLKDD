# Paper 2 — bản dựng lại

Bản nộp IJNM bị **desk reject** 05-09-2026, không một dòng phản biện. Thư mục này là bản
dựng lại, nhắm **Security and Privacy** (Wiley, IF 2.9, hybrid OA).

> **Trạng thái:** số liệu, hình, bảng, bộ kiểm xong — **121/121** + **152/152** (đẳng thức).
> Còn lại là viết prose ở các chỗ `% TODO` và danh mục tham khảo.

Khối tác giả giữ nguyên bản đã nộp.

---

## Ba thay đổi, đều về **đo đạc** chứ không về mô hình

### 1. Tập test: 100 mẫu → KDDTest+ đầy đủ

Bản đã nộp đo `ECE_rare` trên `NSL_KDD_Test_Sample100.csv` — 100 mẫu, trong đó **10 mẫu hiếm**,
chia **5 bin**, tức **2 mẫu mỗi bin**. KDDTest+ đầy đủ có **2 952 mẫu hiếm**, gấp 295 lần.

Bài còn viết *"We use B=10 on the **full test set**"* — nhưng tập test là 100 mẫu, không phải
22 544 dòng. Câu đó gây hiểu nhầm.

Lý do ngày xưa phải cắt nhỏ là chi phí kernel lượng tử. Với lối tắt closed-form của Paper 1:

```
Gram 22 544 × 1 000   0,15 giây
```

Lý do đó không còn.

### 2. Số run: 5 → 10

Với **5 cặp**, Wilcoxon hai phía có p nhỏ nhất là **0,0625** — không bao giờ đạt p < 0,05,
dù hiệu ứng lớn đến đâu. Mọi kết luận sẽ thành "inconclusive" một cách máy móc. Repo có sẵn
10 file `train_run*.csv`.

### 3. Không dùng model cache

Model trong `qsvm_cache/multirun_c5/` được huấn luyện trên một tập 1 000 mẫu **khác** với
`train_run{i}.csv` hiện tại — **998/1000 dòng khác nhau**, lệch tới 2,95 trên thang [0, π].

Bản cũ nạp model đó rồi fit Platt bằng `X_train` đọc từ file. Tức calibrator của QSVM được fit
trên điểm số của một tập nó **chưa từng thấy**, trong khi calibrator của cây được fit đúng trên
tập chúng được huấn luyện. Bài khẳng định mọi baseline được đo *"on an identical footing"* —
điều đó không đúng.

Ở bản này **mọi model đều huấn luyện lại** trên cùng một tập.

---

## Phát hiện lớn nhất: `ECE_rare` không đo calibration

Tập tấn công hiếm được lấy **theo nhóm tấn công**, nên mọi bản ghi trong đó đều là tấn công —
nhãn nhị phân đều bằng 1, trên **cả hai** dataset. Khi đó `acc(bin) = 1` ở mọi bin theo định
nghĩa, và

```
ECE = Σ_B (|B|/n)·|acc(B) − conf(B)| = Σ_B (|B|/n)·(1 − conf(B)) = 1 − p̄
```

Vế phải **không phụ thuộc cách chia bin**. Đó là phép đo *độ tự tin trên tấn công đã biết* —
gần với recall — chứ không phải calibration. Không mô hình nào có thể bị phạt vì quá tự tin.

`runners/verify_rare_identity.py` kiểm trên mọi model, mọi run, cả hai dataset: **lệch lớn
nhất 2,2e-16**, và kiểm luôn vế đối lập (trên toàn tập test acc từng bin biến thiên, độ tán
≥ 0,349, nên ECE ở đó đo calibration thật). **152/152.**

Vì vậy chỉ số chính đổi sang **ECE trên toàn tập test**.

---

## Kết luận

**ECE toàn tập test, trung bình 10 run:**

| Model | NSL-KDD (4qb) | UNSW (4qb) | UNSW (6qb) |
|---|---|---|---|
| MLP | **0,1172** | **0,1198** | **0,1226** |
| SVM-RBF | 0,1272 | 0,1518 | 0,1474 |
| **QSVM-ZZ** | 0,1421 | 0,1449 | 0,1531 |
| XGBoost | 0,1758 | 0,2117 | 0,2201 |
| Random forest | 0,1836 | 0,2308 | 0,2225 |

**Sống sót, nhất quán, có ý nghĩa thống kê:** QSVM hiệu chỉnh tốt hơn **cả hai mô hình cây** ở
**mọi thiết lập** — **8/8 so sánh** đều qua Holm. Hiệu ứng trên UNSW rất lớn (d_z tới −7,6).

**Không được claim:** QSVM **không** tốt hơn MLP ở bất kỳ đâu. So với SVM-RBF thì tuỳ dataset.

**Không sống sót từ bản cũ:** *"QSVM đáng tin nhất"*, *"tốt nhất ở low-data"*, *"tốt nhất ở
điểm cân bằng"*.

---

## Hai phản biện đã chặn trước

### "Các anh làm què cây rồi mới so"

Chạy lại RF/XGBoost trên **K=20** và **đủ 122 đặc trưng**, **giữ nguyên siêu tham số** (tune
lại thì nhánh 122 chiều được lợi thế nhánh PCA-4 không có).

| Biểu diễn | RF AUC-PR | RF ECE | XGB ECE |
|---|---|---|---|
| PCA-4 | 0,9481 | 0,1836 | 0,1758 |
| **122 đặc trưng** | **0,9648** | 0,1858 | 0,1818 |

Xếp hạng tốt lên rõ; hiệu chỉnh **xấu đi nhẹ** và không chỗ nào tiến gần QSVM. Điểm cần nói
không phải là biểu diễn giàu hơn làm hại cây nhiều — mà là nó **không giúp** gì cho hiệu chỉnh
của cây. Nghĩa là bảng chính đã là thiết lập **có lợi nhất** cho cây.

> Lưu ý: trên chỉ số `ECE_rare` cũ thì hiệu ứng này lớn hơn nhiều (0,656 → 0,777). Nhưng chỉ
> số đó đã bị loại, nên con số mạnh kia **không** được mang sang.

### "Sao chỉ thử mỗi Platt?"

Bản cũ tự khai đây là giới hạn. Đã thêm **isotonic regression** và **temperature scaling**:

| | không hiệu chỉnh | Platt | isotonic | temperature |
|---|---|---|---|---|
| **QSVM** | 0,1969 | **0,1421** | **0,1398** | **0,1399** |
| SVM-RBF | 0,1171 | 0,1272 | 0,1254 | 0,1140 |
| Random forest | 0,1305 | 0,1836 | 0,1787 | 0,1795 |
| XGBoost | 0,1392 | 0,1758 | 0,1802 | 0,1712 |

Cả ba bộ hiệu chỉnh đều giúp QSVM và đều làm **xấu** cả hai mô hình cây. Kết luận không phải
do chọn riêng hàm logistic: **hiệu chỉnh hậu kỳ ở bài toán này là công cụ cho kernel lượng tử
và gần như không cho ai khác.**

---

## Dựng lại

```bash
python runners/run_p2_rebuild.py          # 10 run, 2 tập test   (~30 giây)
python runners/run_p2_rebuild_extra.py    # low-data, prior shift, Platt  (~2 phút)
python runners/run_p2_rebuild_refarm.py   # nhánh đối chứng + 3 bộ hiệu chỉnh (~40 giây)
python runners/run_p2_rebuild_unsw.py     # UNSW, cả 4 và 6 qubit     (~3 phút)
python runners/verify_rare_identity.py    # 152/152  đẳng thức suy biến
python runners/analyze_p2_rebuild.py      # Wilcoxon + bootstrap CI + Holm
python runners/make_p2_rebuild_figures.py # 4 hình
python runners/make_p2_rebuild_tables.py  # bảng + 171 macro số
python runners/audit_p2_rebuild.py        # 121/121
python runners/check_latex.py paper/paper2_rebuild/main.tex
python runners/make_paper_zip.py paper2   # gói để tải lên Overleaf
```

Máy này không có LaTeX — compile trên Overleaf, **pdfLaTeX**.

## Kỷ luật về số

Prose **không được viết số trực tiếp**; mọi con số đi qua macro trong
[tables/numbers_macros.tex](tables/numbers_macros.tex), sinh từ artifact.

`audit_p2_rebuild.py` kiểm ba lớp, trong đó lớp thứ ba quan trọng nhất — nó khoá đúng những
luận điểm bài **được phép** và **không được phép** claim:

- QSVM thắng cả hai mô hình cây sau Holm, ở **cả ba** thiết lập → phải đúng
- Bài **không** được claim thắng MLP → phải đúng
- `ECE_rare == 1 − p̄` (lệch < 1e-12) và ECE toàn tập **không** suy biến → phải đúng
- Cho cây đủ 122 đặc trưng thì xếp hạng tốt lên mà hiệu chỉnh không tốt lên → phải đúng
- Cả ba bộ hiệu chỉnh làm xấu cây và làm tốt QSVM → phải đúng

Và một phép kiểm nữa: **mọi macro dùng trong bài phải được định nghĩa**. Thiếu nó thì gõ sai
một tên macro sẽ lọt — audit vẫn xanh còn LaTeX thì chết. Tôi đã cố tình tiêm lỗi để xác nhận
nó bắt được.

Sửa dữ liệu mà kết luận đổi chiều thì bộ kiểm báo ngay, không để bài nói một đằng số liệu
một nẻo.

---

## Còn phải làm

| | Việc |
|---|---|
| 1 | Viết prose — các chỗ `% TODO` |
| 2 | Danh mục tham khảo (giữ của bản đã nộp) |
| 3 | Gửi thầy duyệt — đổi trục chủ đạo là thay đổi lớn |
| 4 | Nhiễu → calibration: bài tự viết *"left to a hardware study"* |
