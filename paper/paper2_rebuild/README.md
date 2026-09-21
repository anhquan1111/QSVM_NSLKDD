# Paper 2 — bản dựng lại

Bản nộp IJNM bị **desk reject** 05-09-2026, không một dòng phản biện. Thư mục này là bản
dựng lại, nhắm **Security and Privacy** (Wiley, IF 2.9, hybrid OA).

> **Trạng thái:** số liệu, hình, bảng, bộ kiểm xong — **151/151**.
> Còn lại là viết prose ở các chỗ `% TODO` trong [main.tex](main.tex) và danh mục tham khảo.

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

## Kết luận đổi thế nào

| | Bản đã nộp (10 mẫu hiếm) | Bản dựng lại (2 952 mẫu hiếm) |
|---|---|---|
| QSVM `ECE_rare` | 0,4503 — **hạng 1/4** | 0,5414 — **hạng 3/5** |
| So với cây | thắng | **vẫn thắng, và có ý nghĩa sau Holm** |
| So với SVM-RBF | thắng | **bất phân thắng bại** |
| So với SVM-RBF (Brier) | — | **thua, có ý nghĩa** |

**Không sống sót:** *"QSVM đáng tin nhất"*, *"tốt nhất ở chế độ low-data"*, *"tốt nhất ở
điểm cân bằng"*.

**Sống sót, và giờ có ý nghĩa thống kê:**

- QSVM hiệu chỉnh **tốt hơn hẳn cả hai mô hình cây** — d_z = −1,46 (RF) và −0,78 (XGB),
  p sau Holm 0,0117 và 0,0273
- **Platt chỉ giúp duy nhất kernel lượng tử** (−0,0547 ECE); làm xấu cả hai mô hình cây,
  và xấu nhẹ cả SVM-RBF. Sắc hơn bản cũ, vốn nói Platt hợp mọi mô hình margin
- Xếp hạng ≠ độ tin cậy: cây có AUC-PR tốt nhất mà calibration tệ nhất

---

## Hai phản biện đã chặn trước

### "Các anh làm què cây rồi mới so"

Tiêu đề có chữ *Strong Tabular Learners* mà cây lại chạy trên đúng PCA 4 chiều như QSVM. Đã
chạy lại RF và XGBoost trên **K=20** và trên **đủ 122 đặc trưng** one-hot — **giữ nguyên siêu
tham số**, chỉ đổi biểu diễn (tune lại thì nhánh 122 chiều được lợi thế nhánh PCA-4 không có,
và phép so sánh không còn cô lập được ảnh hưởng của riêng biểu diễn).

| Biểu diễn | RF AUC-PR | RF ECE_rare | XGB ECE_rare |
|---|---|---|---|
| PCA-4 | 0,9481 | **0,6561** | **0,6210** |
| K=20 | 0,9581 | 0,6726 | 0,6141 |
| **122 đặc trưng** | **0,9648** | 0,7765 | 0,7943 |

Nhiều đặc trưng **không** làm cây đáng tin hơn — nó làm cây **kém tin hơn**, trong khi xếp
hạng thì tốt lên. Đúng cái tách rời mà bài này nói. Nghĩa là bảng chính **không** phải sản
phẩm của một biểu diễn chật chội: đó đã là thiết lập hiệu chỉnh **có lợi nhất** cho cây.

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
python runners/analyze_p2_rebuild.py      # Wilcoxon + bootstrap CI + Holm
python runners/make_p2_rebuild_figures.py # 4 hình
python runners/make_p2_rebuild_tables.py  # bảng + 147 macro số
python runners/audit_p2_rebuild.py        # 151/151
python runners/check_latex.py paper/paper2_rebuild/main.tex
```

Máy này không có LaTeX — compile trên Overleaf, **pdfLaTeX**.

## Kỷ luật về số

Prose **không được viết số trực tiếp**; mọi con số đi qua macro trong
[tables/numbers_macros.tex](tables/numbers_macros.tex), sinh từ artifact.

`audit_p2_rebuild.py` kiểm ba lớp, trong đó lớp thứ ba quan trọng nhất — nó khoá đúng những
luận điểm bài **được phép** và **không được phép** claim:

- QSVM thắng cả hai mô hình cây sau Holm → **phải đúng**
- QSVM vs SVM-RBF là inconclusive → **phải đúng**, bài không được claim thắng
- Platt chỉ giúp QSVM → **phải đúng**
- QSVM xếp hạng cao hơn trên tập test nhỏ → **phải đúng**, đó là luận điểm cảnh báo
- Cho cây đủ 122 đặc trưng thì xếp hạng tốt lên mà hiệu chỉnh tệ đi → **phải đúng**
- Cả ba bộ hiệu chỉnh làm xấu mô hình cây và làm tốt QSVM → **phải đúng**

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
| 3 | Bàn với thầy: đổi luận điểm chủ đạo là thay đổi lớn |
| 4 | Calibration trên UNSW-NB15 — đóng giới hạn "một dataset" bài tự khai |
| 5 | Nhiễu → calibration: bài tự viết *"left to a hardware study"* |
