# Paper 2 — bản dựng lại

Bản nộp IJNM bị **desk reject** 05-09-2026, không một dòng phản biện. Thư mục này là bản
dựng lại, nhắm **Security and Privacy** (Wiley, IF 2.9, hybrid OA).

> **Trạng thái:** số liệu, hình, bảng, bộ kiểm xong — **105/105**.
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

## Dựng lại

```bash
python runners/run_p2_rebuild.py          # 10 run, 2 tập test   (~30 giây)
python runners/run_p2_rebuild_extra.py    # low-data, prior shift, Platt  (~2 phút)
python runners/analyze_p2_rebuild.py      # Wilcoxon + bootstrap CI + Holm
python runners/make_p2_rebuild_figures.py # 3 hình
python runners/make_p2_rebuild_tables.py  # bảng + 106 macro số
python runners/audit_p2_rebuild.py        # 105/105
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

Sửa dữ liệu mà kết luận đổi chiều thì bộ kiểm báo ngay, không để bài nói một đằng số liệu
một nẻo.

---

## Còn phải làm

| | Việc |
|---|---|
| 1 | Viết prose — các chỗ `% TODO` |
| 2 | Danh mục tham khảo (giữ của bản đã nộp) |
| 3 | Bàn với thầy: đổi luận điểm chủ đạo là thay đổi lớn |
| 4 | Cân nhắc thêm isotonic + temperature scaling (bản cũ tự khai là giới hạn) |
| 5 | Nhánh đối chứng 122 đặc trưng kèm calibration — tiêu đề có chữ *"Strong Tabular Learners"* |
