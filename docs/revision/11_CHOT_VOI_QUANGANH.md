# Gửi Quang Anh chốt trước khi viết bài

*Quan, 2026-09-04. Tiếp nối `05_TOM_TAT_CHO_QUANGANH.md`. Deadline 13-10, không có major revision lần hai.*

Toàn bộ thí nghiệm đã xong. Trước khi bắt tay viết bản thảo, m xem qua và chốt giúp
**5 mục ở phần A** — đó là những chỗ đổi cách kể của bài, t không muốn tự quyết một mình.
Phần B trở đi là để m nắm, không cần trả lời.

---

## A. Năm mục cần m chốt

### A1. 🔴 Năm khẳng định của bản đã nộp phải rút

| Bản đã nộp | Số thật sau khi chạy lại |
|---|---|
| Lợi thế ở **chế độ ít dữ liệu** | **Ngược lại** — cổ điển thắng ở N nhỏ, QSVM thắng ở N lớn (crossover N≈2000–5000) |
| "+6.7 điểm rare, Cohen's d=+0.68" | **Không tái tạo được** — code cũ không có metric rare nào |
| Theorem 1: n\*=4 cực đại hoá J | **Sai** — J cực đại tại n=2 |
| QSVM 0.854 > SVM-RBF 0.838 | Thêm baseline mạnh: **XGBoost 0.8503 > QSVM 0.8469** > RF 0.8446 |
| Prior-shift là "bằng chứng mạnh nhất" | QSVM-ZZ **thua** XGBoost (−0.017) và RF (−0.013), chỉ thắng SVM-RBF |

**Chốt gì**: m đồng ý rút cả 5 chứ? T không thấy cách nào giữ mà không sai số liệu.

### A2. 🔴 Bỏ hẳn Theorem 1 + Pareto, không vá

Chứng minh Theorem 1 viết *"F̃(4) > F̃(3)"*, nhưng Table III của chính bài ghi
`F̃(4)=0.471 < F̃(3)=0.628`. Và bước Pareto **không lọc gì** (mọi candidate đều Pareto-optimal
vì V tăng, F̃ giảm, Q tăng đơn điệu) — đúng như R4 chỉ ra.

Thay bằng **luật ba giai đoạn từ vựng**, không trọng số: `V(n)≥0.85` → `KTA ≥ 0.95·KTA_max`
→ `min Q(n)`. Trên NSL-KDD ra `n*=4`, trên UNSW ra `n*=6` — cùng luật, không sửa tham số.

**Chốt gì**: bỏ hẳn thay vì cố sửa Theorem 1, m thấy được không?

### A3. 🟡 Tự khai thêm một lỗi reviewer CHƯA bắt

Caption Table III ghi `F̃(n) = 1/DBI(n)` nhưng số trong cột là **thống kê Fisher**
(1/DBI thật là 1.143/0.982/0.922 tại n=2,3,4). Trong `main.tex` cùng cột đó lại gắn nhãn
`"1−V"` — cũng sai. Nhãn sai được mang theo qua nhiều bản.

**Chốt gì**: t đề nghị **tự khai trong bài**. Không ai bắt, nhưng nếu reviewer đối chiếu
supplementary là thấy, và lúc đó mất hết thiện chí. M thấy sao?

### A4. 🟡 Cách trả lời R3 (reviewer đề nghị từ chối)

R3 chê không có "kernel mới / feature map mới / phương pháp mới / phần cứng / lý thuyết mới".
**Ta vẫn không có.** T đề nghị ba nước, không cãi thẳng:

1. **Chỉ ra R3 tự mâu thuẫn** — R3 dẫn hai bài benchmark thuần tuý (arXiv:2403.07059,
   2409.04406) làm bằng chứng "kết quả đã có", nhưng **cả hai bài đó cũng không có** kernel
   mới / feature map mới / phương pháp mới / phần cứng / lý thuyết mới. Theo tiêu chí R3 đưa
   ra thì chính hai bài họ tin cậy cũng không đăng được. Viết lịch sự, nêu sự thật.
2. **Đưa thứ gần nhất mình giao được**: quan hệ định lượng giữa cấu trúc mạch và hành vi —
   xem A5.
3. **Đổi khung từ "lợi thế" sang "ranh giới"** — dữ liệu giờ nói về giới hạn, không nói về
   lợi thế.

**Chốt gì**: m có thấy nước 1 quá mạnh tay không? T nghĩ là công bằng, nhưng muốn m cân.

### A5. 🟢 Kết quả mới đề nghị đưa vào bài

| # | Kết quả | Trả lời ai |
|---|---|---|
| 1 | Crossover đổi dấu tại `2000→5000` ở **6/6 tổ hợp** {XGB, RF, RBF} × {đóng băng, tune lại} | R1-7 · chặn phản biện "chỉ do tune lại" |
| 2 | **K càng lớn càng cần nhiều qubit**: K=20→n\*=4 (24 CNOT), K=80→n\*=8 (112 CNOT) | biện minh K=20 bằng ngân sách NISQ |
| 3 | Mở rộng mạch **phá hỏng** nhân: ở K=80/n=8 thì **32/32 ô** classical-favorable | **R3-4** |
| 4 | Độ trải Gram **dự đoán** F1: Pearson **r=+0.77** (ZZ) vs +0.32 (Z) | **R3** — cơ chế định lượng |
| 5 | Số mũ suy giảm `std(n)~n^(-α)`: tỉ lệ **α_ZZ/α_Z = 2.02** tại K=20, khớp `C(n,2)∝n²` vs `n` | **R3** — khớp cấu trúc mạch |

**Chốt gì**: m thấy 5 cái này đủ để bù cho phần rút ở A1 không?

---

## B. Để m nắm, không cần trả lời

### B1. Số của m được dùng nguyên

- **C2**: giữ nguyên. Noise validation m duyệt rồi (`evaluate_in_blocks`). Kết luận không đổi:
  KTA **+0.1378** [+0.1267, +0.1489] có ý nghĩa, F1 chỉ **+0.0114** [−0.0054, +0.0281] — CI cắt 0.
- **C3**: lấy số máy t như m dặn.
- **File phản hồi reviewer về RF/XGBoost** của m đã vào `notebooks/nslkdd/note/general/`.
  T sửa hai chỗ: gỡ 5 chuỗi `citeturn23file4...` (rác của công cụ soạn thảo), và
  XGBoost `0.8493` → **`0.8503`** cho khớp artifact trong repo. Số 0.8493 là máy m; đối chiếu
  `master` vs `revisionC4` thì **mọi số quantum trùng khít tới bit**, chỉ XGBoost (+0.00101)
  và SVM_Poly2 (+0.00033) lệch — đúng hai phát hiện #6/#7. Thứ tự xếp hạng không đổi.

### B2. Hình: 12 hình, tất cả sinh lại từ dữ liệu revision

⛔ **Mọi hình trong `reports/`, `data/*/processed_data/`, `results/*/c3_multirun/`,
`c4_multirun/` đều KHÔNG dùng được** — của code cũ, 5 seed, tune bất đối xứng, chưa có RF/XGB.
Chỉ dùng `paper/paper1/figs_revision/`. Xem `MANIFEST.md` trong đó.

Ba file dễ nhầm nhất: `c1_fig_pareto_diagnostic.png` (chính cái Pareto R4 chê),
`c6_learning_curves_test_f1.png` (chỉ tới N=1000, không có crossover),
`c3_regime_map_main_full_baselines.png` (chỉ khối C3, không phải 110 so sánh).

### B3. Hai bộ audit tự động

```bash
python runners/audit_c4.py       # 100/100 PASS
python runners/audit_figures.py  #  39/39 PASS
```

`audit_c4.py` **không dùng lại hàm thống kê của `c4_pipeline.py`** — viết lại từ đầu bằng
scipy rồi đối chiếu. Dùng chính code sinh ra số để kiểm số đó thì lỗi chung sẽ lọt.

`audit_figures.py` kiểm hai thứ: **xuất xứ** (hình phải mới hơn script và dữ liệu nguồn) và
**số liệu** (từng con số dựng lại từ artifact).

Hai bộ này bắt được **4 lỗi thật** trong chính code t viết — trong đó có một lỗi làm `n*` ra
5 thay vì 4. Không soát thì đã đi thẳng vào bài.

### B4. Bài trùng đề tài, chưa ai nhắc

**Gillani et al. (13-08-2026), arXiv:2608.18155** — trùng **NSL-KDD + UNSW-NB15**, trùng
official split, trùng baseline RF/XGBoost, có noise sweep và hiệu chỉnh đa so sánh.
Kết luận của họ: cho model cổ điển dùng cùng front-end thì "quantum advantage" **biến mất**,
lợi thế quy về tiền xử lý.

Điều này **xác nhận** phát hiện độc lập của ta (phân rã A/B/C cô lập SelectKBest+PCA refit),
nên viết theo hướng *independent corroboration*. Nhưng **phải trích** — nộp sau họ 2 tháng mà
lờ đi là reviewer tự tìm ra.

⚠️ Nó cũng có calibration-aware metrics, tức **chạm vào Paper 2**. Ta nộp IJNM 04-08, họ 13-08
— trước 9 ngày nên không mất quyền ưu tiên, nhưng nếu IJNM cho revise thì phải trích.

---

## C. Việc còn lại

| # | Việc | Ai |
|---|---|---|
| 1 | 🚨 **`.tex` nguồn không còn** → t dựng lại từ `paper1.pdf` | Quan |
| 2 | Sửa ref [15] `116990F`→`116990B`; kiểm và bỏ ref [26] Rahman; giữ ≤45 ref | thầy |
| 3 | Toàn văn QMI 2026 (Springer chặn) + Carducci ICAD 2026 (IEEE chặn) | thư viện trường |
| 4 | Link repo + commit hash cho mục Reproducibility | Quan |
| 5 | Rebuttal điểm-theo-điểm 33 item | Quan |
| 6 | **Tuỳ chọn**: chạy nhân trên QPU IBM thật — script xong, chờ token | Quan |

### Về mục 6

`runners/run_hardware_kernel.py` đã chạy thử `--dry-run` thông toàn bộ. Ba mức trên **cùng một
tập con và cùng một mạch**:

| Mức | KTA | FroSim vs ideal |
|---|---|---|
| ideal statevector | 0.2727 | 1.0000 |
| FakeManilaV2 (nhiễu) | 0.2195 | 0.8945 |
| QPU thật | *chờ token* | |

40 mẫu → 780 mạch, ~2 phút QPU. Nó xoá đúng một mục trong danh sách của R3, nhưng **không
chạm vào lập luận cốt lõi của họ**. T xếp là tuỳ chọn, làm sau khi bản thảo xong.

---

## Tóm lại

**Về mức độ chặt chẽ: đạt Q1, và vượt xa bản đã nộp.** Bản cũ có một định lý sai, một bước
Pareto không lọc gì, một khẳng định không tái tạo được. Bản mới thay tất cả bằng số đo được,
kiểm định có hiệu chỉnh đa so sánh, và hai bộ audit tự động.

**Rủi ro còn lại**: R3 có đổi ý không, và có viết kịp 39 ngày không. AE đã viết *"the majority
of reviewers see sufficient new contribution"* nên AE không đứng về phía R3.

**Điều quan trọng nhất khi viết**: đóng khung là *"chúng tôi đo lại nghiêm ngặt hơn và tìm ra
bức tranh có cấu trúc"*, **không phải** *"chúng tôi rút lại các khẳng định"*. Cùng một sự thật,
hai cách kể, hai kết cục.
