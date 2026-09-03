# Kế hoạch thực thi — C4 + UNSW transfer (phần của Quan)

> [!abstract] Nguyên tắc của kế hoạch này
> - **Chia nhỏ**: 11 giai đoạn, ~30 bước. Mỗi bước có **điều kiện qua (exit gate)** rõ ràng, chạy thử được, sai thì quay lui rẻ.
> - **Không bước nào chạy quá 1 lần**: mọi Gram matrix đều cache theo `(N, run, kernel)`.
> - **Mỗi thí nghiệm mới phải trả lời một objection cụ thể của reviewer** — nếu không map được vào ID nào trong [00_STATUS](00_STATUS_paper1.md#phần-2), thì không làm.
> - Sau mỗi bước: ghi kết quả thật vào mục **`📝 Kết quả`** của chính bước đó trong file này.
>
> Bối cảnh + trạng thái: [00_STATUS_paper1.md](00_STATUS_paper1.md)

---

# A. Bốn quyết định protocol — đề xuất và lý do

> [!important] Cần bạn chốt trước khi bắt đầu Giai đoạn 1

### Q1. Representation: re-fit theo từng N, hay dùng artifact C1 đã đóng băng?

**Đề xuất: RE-FIT theo từng N là primary; frozen-C1 là biến thể phụ ở supplementary.**

Lý do:
1. Bản đã nộp (Sec. III-F) **đã cam kết re-fit** — đổi sang freeze là tự mâu thuẫn với chính bài, reviewer sẽ hỏi tại sao đổi.
2. C1 fit PCA trên **toàn bộ 125,973 mẫu train**. Nếu C4 dùng nó rồi train trên 100 mẫu, câu chuyện "low-data advantage" bị rỗng: model đã được hưởng một representation học từ 125k mẫu. R1 đang soi đúng chỗ này.
3. Biến thể frozen vẫn nên có, vì nó chính là điều kiện của C2/C3 → cho phép nói *"kết luận không đổi dưới cả hai giao thức"*.

⚠️ Hệ quả phải viết rõ: dưới re-fit, `n=4` là **thừa kế thiết kế từ C1**, không phải được chọn lại ở mỗi N. Đây là design choice, phải khai báo.

### Q2. Tune C theo từng N, hay dùng C=3.0 đóng băng từ C2?

**Đề xuất: tune đối xứng cho CẢ 7 model tại MỖI N; báo cáo thêm hàng "frozen C2 hyperparameters" để so.**

Lý do:
1. C=3.0 được tune tại N=1000. Áp cho N=100 là **bất lợi cho chính QSVM** — và R4-5 đã cảnh báo đúng kiểu lỗi này ("không tune là design choice có thể đang gây ra kết quả xấu").
2. Nếu chỉ tune classical theo N mà quantum giữ nguyên thì tái phạm đúng R1-3.
3. **Chi phí gần như bằng 0**: kernel không phụ thuộc `C`. Tính Gram **một lần** cho mỗi `(N, run)`, rồi slice theo fold để quét cả lưới `C ∈ {0.1,0.3,0.5,1,3,5,10}`. Chỉ `SVC.fit` chạy lại — vài giây.
4. Quy tắc chọn giữ nguyên 1-SE của C2 → đồng nhất phương pháp giữa các contribution.

### Q3. Test set nào?

**Đề xuất: báo cáo CẢ HAI ở mọi N** — full **KDDTest+ 22,544** (primary, khớp Table VI bản nộp) và **fixed 300** (khớp Table IV / C2).

Đây là cách rẻ nhất và sạch nhất để đóng **R1-8**: thay vì chỉ viết một câu giải thích, ta **đưa số của cả hai giao thức cạnh nhau**, reviewer tự thấy chênh lệch đến từ test set chứ không phải mâu thuẫn.

### Q4. Mở rộng N tới đâu?

**Đề xuất (đã cập nhật sau đo đạc ở S0.2): `N ∈ {100, 200, 500, 1000, 2000, 5000, 10000}`**

> [!success] Chi phí thấp hơn ước tính ban đầu rất nhiều — nhờ đổi kiến trúc tính kernel
> Ước tính đầu tiên của tôi (~7 giờ) dựa trên việc gọi `FidelityStatevectorKernel.evaluate()`, hàm này **mô phỏng lại statevector mỗi lần gọi** → chi phí O(N²) mô phỏng.
>
> Cách đúng: **cache statevector Ψ (N×16 complex)**, rồi `Gram = |Ψ_a† Ψ_b|²` chỉ là một phép matmul với inner dim 16.
>
> Số đo thực tế trên máy này:
>
> | Phép tính | Thời gian |
> |---|---:|
> | Mô phỏng statevector | 0.84 ms/mẫu → **toàn bộ 22,544 mẫu test ≈ 19 giây, tính một lần** |
> | Gram 10000×10000 | 1.7 s |
> | `SVC.fit` precomputed, N=10000 | 1.6 s |
> | Gram 22544×10000 (1.8 GB) | 4.6 s |
> | `predict` N=10000 | 1.2 s |
>
> **Kiểm chứng tính đúng đắn**: Gram tính từ statevector cache so với `FidelityStatevectorKernel.evaluate()` cho `max|Δ| = 4.4e-15` → **giống hệt về số học**, không phải xấp xỉ.

⇒ Toàn bộ Giai đoạn 2 + 3 ước tính **dưới 1 giờ**, không phải 7 giờ. Vì vậy tôi mở rộng dải N lên **10000** — xa gấp **10 lần** so với N=1000 của bản đã nộp, làm câu trả lời cho R1-7 (crossover) thuyết phục hơn hẳn.

`N = 20000` để ở dạng **stretch tuỳ chọn** (S3.3), quyết định sau khi thấy kết quả N=10000; cần `float32` cho Gram để giữ RAM ≈ 3.4 GB.

---

# B. Bản đồ: mỗi giai đoạn đóng objection nào

| Giai đoạn | Nội dung | Đóng item |
|---|---|---|
| 0 | Audit claim + chốt protocol + dọn repo | (chuẩn bị) |
| 1 | Hạ tầng C4 + gate tái tạo C2 | (chất lượng) |
| 2 | Learning curve lõi N ≤ 1000 | R2-3, R1-5 |
| 3 | Mở rộng N → crossover | **R1-7** |
| 4 | Rare-attack margin | **R4-4** |
| 5 | Table IV vs VI + protocol vs literature | **R1-8**, **R1-9** |
| 6 | Note C4 + đồng bộ regime map | R2-4, AE-1 |
| 7 | UNSW: audit + chốt phạm vi | (chuẩn bị) |
| 8 | UNSW: pipeline độc lập + C1 rule + tuning | **R1-2**, **AE-4** |
| 9 | UNSW: stationary + prior-shift + low-data | **R1-2**, **AE-4**, R3-1 |
| 10 | Supplementary + repo + bàn giao số + rebuttal | **R1-10**, **R4-2**, R1-4, AE-1 |

---

# GIAI ĐOẠN 0 — Chuẩn bị (0 compute)

## S0.1 — Truy vết 5 claim C4 của bản nộp
- **Mục tiêu**: biết chính xác `+6.7` và `d=0.68` từ đâu ra, trước khi thay bằng số mới.
- **Việc**: đối chiếu `results/nslkdd/c6_results.json` + notebook C6 cũ với từng câu trong `paper1.pdf` V-D và Fig 10.
- **Output**: `docs/revision/c4_claim_audit.md` — bảng: claim → số trong bài → số tái tạo được → phán quyết (đúng / sai / không tái tạo được).
- **Exit**: mọi claim K1–K5 có phán quyết dứt khoát.
- **📝 Kết quả**: ✅ **Xong** → [c4_claim_audit.md](c4_claim_audit.md). K1/K4/K5 tái tạo khớp 100%. **K2 sai** (+6.7 là Δ vs SVM-Linear trên toàn tập, không phải vs RBF trên rare subset; không có F1 rare nào tồn tại). **K3 không tái tạo được** (số thật +0.4043; nguồn 0.68 gần nhất là `−0.68048` từ C5 với 10 mẫu rare, ngược dấu). **Phát hiện thêm K3b**: cả C5/C6 dùng `|margin|` thay vì signed margin — lỗi phương pháp, phải đổi.

## S0.2 — Chốt và đóng băng protocol C4
- **Việc**: viết `configs/c4_protocol.json` gồm toàn bộ quyết định Q1–Q4, danh sách model, seed, lưới C, định nghĩa rare subset, định nghĩa margin, quy tắc thống kê.
- **Output**: 1 file JSON + 1 đoạn mô tả để dán thẳng vào Methodology.
- **Exit**: file được bạn duyệt; từ đây **không đổi** trừ khi có lỗi khoa học.
- **📝 Kết quả**: ✅ **Xong** → [`configs/c4_protocol.json`](../../configs/c4_protocol.json). Hai điều chỉnh phát sinh: (1) phân tầng nhãn **4 lớp** thay vì 5 (train_run1 chỉ có 6 mẫu U2R → N=100 sẽ mất sạch rare); (2) **cache statevector thay vì cache Gram** → chi phí giảm từ ~7h xuống <1h, nên mở rộng N lên **10000**.

## S0.3 — Dọn repo (theo yêu cầu của bạn Quang Anh)
- **Việc**: bỏ `paper/paper1/manuscript.pdf` (là bài LEO satellite, không liên quan); thêm `.claude/`, `.jupyter_tmp/`, `__pycache__/` vào `.gitignore`; rà file rác trong `runners/`, `scripts/`.
- **Exit**: `git status` sạch, `uv sync` vẫn chạy.
- **📝 Kết quả**: ✅ **Một phần**. `.claude/`+`.jupyter_tmp/` đã có sẵn trong `.gitignore` (bạn Quang Anh đã làm). Đã thêm `results/*/c4_revision/cache/`. **Chưa xoá** `manuscript.pdf` và **chưa gỡ** cache `.npy` của C3 khỏi git — cả hai chờ duyệt.

---

# GIAI ĐOẠN 1 — Hạ tầng C4 (có gate kiểm chứng)

## S1.1 — Module dùng chung `src/c4_pipeline.py`
- **Việc**: loader dữ liệu; pipeline re-fit-per-N và frozen-C1; factory 7 model đúng hợp đồng C2; cache Gram theo `(N, run, kernel, split)`; hàm thống kê (paired Δ, bootstrap CI, Wilcoxon, d_z, Holm) **tái dùng đúng công thức C3** để số liệu có thể so sánh chéo.
- **Exit**: import được, có docstring, không chạy thí nghiệm nào.
- **📝 Kết quả**: ✅ **Xong** → [`src/c4_pipeline.py`](../../src/c4_pipeline.py). Kiểm chứng kernel: `max|Δ|` vs `FidelityStatevectorKernel` = **4.2e-15 (ZZ)** / **4.4e-15 (Z)**. Phát sinh 2 phát hiện lớn: (a) `train_run{i}` **giàu lớp hiếm gấp 12 lần** tỉ lệ tự nhiên → phải tách **2 chế độ lấy mẫu** `matched` / `natural`; (b) KDDTrain+ và KDDTest+ **trùng 610 dòng** (thuộc tính dataset). Gate G3/G4/G5 PASS cả hai chế độ.

## S1.2 — Smoke test
- **Việc**: N=100, 2 run, 7 model, cả 2 test set.
- **Exit**: chạy < 5 phút; không NaN; QSVM-ZZ F1 rơi vào khoảng 0.78–0.85; cache hoạt động (chạy lần 2 phải < 10 s).
- **📝 Kết quả**: ✅ **Xong** — gộp vào S1.3, toàn bộ 10 run × 7 model chạy hết **17 giây**.

## S1.3 — 🚦 GATE: tái tạo C2 tại N=1000
- **Mục tiêu**: chứng minh code của tôi và code bạn Quang Anh cho **cùng một con số** trước khi đi tiếp.
- **Việc**: chạy chế độ frozen-C1 + hyperparameter đóng băng + test 300 + 10 run seed 100–109, so từng run với `results/nslkdd/c2_revision/c2_per_run.csv`.
- **Exit**: model tất định phải khớp **chính xác** (<1e-9) ở ≥9/10 run; XGBoost báo cáo riêng.
- **📝 Kết quả**: ✅ **PASS**.

| Model | Khớp chính xác | max\|chênh\| | mean mới | mean C2 |
|---|---:|---:|---:|---:|
| **QSVM_ZZ** | **10/10** | **0.00e+00** | 0.846888 | 0.846888 |
| **QSVM_Z** | **10/10** | **0.00e+00** | 0.835528 | 0.835528 |
| SVM_Linear | 10/10 | 0.00e+00 | 0.813655 | 0.813655 |
| SVM_RBF | 10/10 | 0.00e+00 | 0.836186 | 0.836186 |
| RandomForest | 10/10 | 0.00e+00 | 0.844636 | 0.844636 |
| SVM_Poly2 | 9/10 | 3.31e-03 | 0.832657 | 0.832326 |
| XGBoost | 0/10 | 2.01e-02 | 0.851617 | 0.851625 |

  → Kiến trúc statevector cache **tương đương tuyệt đối** với `QSVC` của C2.
  → Phát sinh 2 lỗi reproducibility của protocol dùng chung: **XGBoost phụ thuộc số thread** (`n_jobs=-1` vs `n_jobs=1` lệch 0.017 ở run 1) và **một ô cache C2 (`SVM_Poly2` run 3) không tái tạo được**. Chi tiết: [02_PROGRESS](02_PROGRESS.md).

---

# GIAI ĐOẠN 2 — Learning curve lõi

## S2.1 — Chạy N ∈ {100, 200, 500, 1000}
- **Việc**: 4 mốc × 10 run × 7 model × 2 test set, có tune C đối xứng tại mỗi (N, run). Ghi cả `train_f1`, `test_f1`, `n_SV`, `elapsed`, `best_C`.
- **Output**: `results/nslkdd/c4_revision/c4_per_run.csv`, `c4_hyperparameters.csv`, cache Gram.
- **Exit**: 4×10×7 = **280 bản ghi** đủ; audit disjointness; tại N=1000 / test 300, QSVM-ZZ khớp S1.3 trong sai số.
- **Ước tính**: ~1.5–2 h.
- **📝 Kết quả**: *(chưa chạy)*

## S2.2 — Thống kê paired
- **Việc**: tại mỗi N, tính Δ(QSVM-ZZ − baseline) cho cả 6 baseline: mean, median, CI 95%, Wilcoxon, d_z, tỉ lệ run thắng, Holm trong họ theo N, verdict {QSVM / Classical / Inconclusive}.
- **Output**: `c4_pairwise_statistics.csv` (cùng schema với `c3_pairwise_statistics.csv`).
- **Exit**: mọi ô có verdict; **không có ô nào chỉ có mean**.
- **📝 Kết quả**: *(chưa chạy)*

## S2.3 — Hình learning curve v2
- **Việc**: 7 đường + dải CI, log-x, 2 panel (test 300 / test full). Thay Fig 9 cũ.
- **Exit**: hình đọc được ở khổ 1 cột IEEE; xuất PNG + PDF.
- **📝 Kết quả**: *(chưa chạy)*

---

# GIAI ĐOẠN 3 — Crossover (R1-7)

## S3.1 — N = 2000 và 5000
- **Exit**: 2 × 10 × 7 = 140 bản ghi mỗi test set; đo thời gian thực để hiệu chỉnh dự báo cho N=10000.
- **📝 Kết quả**: *(chưa chạy)*

## S3.2 — N = 10000
- **Việc**: dùng `float32` cho Gram test (1.8 GB → 0.9 GB); chunk `predict` theo lô 5000 dòng test.
- **Exit**: 70 bản ghi mỗi test set; RAM đỉnh < 8 GB.
- **📝 Kết quả**: *(chưa chạy)*

## S3.3 — (tuỳ chọn) N = 20000
- **Việc**: chỉ chạy nếu tại N=10000 vẫn **chưa** thấy crossover. Nếu tại N=10000 XGB đã vượt QSVM với CI không cắt 0 thì không cần.
- **Exit**: quyết định có/không kèm lý do bằng số.
- **📝 Kết quả**: *(chưa chạy)*

## S3.3 — Phân tích crossover
- **Việc**: xác định N mà baseline mạnh nhất (XGB) vượt QSVM-ZZ với CI không cắt 0; nếu không có, viết đúng câu *"no crossover observed within the evaluated range"* và đổi từ "low-data regime" thành "small-sample regime".
- **Output**: bảng crossover + đoạn văn.
- **Exit**: có kết luận dứt khoát theo một trong hai hướng — **không được lảng tránh**.
- **📝 Kết quả**: *(chưa chạy)*

---

# GIAI ĐOẠN 4 — Rare-attack margin (R4-4)

## S4.1 — Đóng băng định nghĩa
- **Việc**: chốt và ghi vào protocol: rare = **U2R ∪ R2L** trên KDDTest+ (2,952 mẫu); margin = **signed** `y·f(x)` (có thêm cột |margin| để so với cách tính cũ); Cohen's d tính **across samples** (primary) và **across seeds** (phụ); pooled std.
- **Exit**: định nghĩa viết ra rồi mới tính — tránh lặp lại đúng lỗi của bản nộp.
- **📝 Kết quả**: *(chưa chạy)*

## S4.2 — Bảng rare-attack đầy đủ
- **Việc**: tại **mọi N** (không chỉ 500) × 7 model: `F1_rare`, `recall_rare`, mean/std margin, Cohen's d vs QSVM-ZZ + bootstrap CI (10k resample).
- **Output**: `c4_rare_attack.csv` + bảng chính rút gọn cho bài.
- **Exit**: mọi con số reviewer đòi đều tra được trong bảng.
- **📝 Kết quả**: *(chưa chạy)*

## S4.3 — Chốt số thay cho `+6.7 / d=0.68`
- **Việc**: viết đoạn đính chính cho rebuttal: số cũ sai ở đâu, số mới là gì, tại sao.
- **Exit**: một đoạn văn dùng được nguyên văn trong rebuttal.
- **📝 Kết quả**: *(chưa chạy)*

---

# GIAI ĐOẠN 5 — Nhất quán bảng & bối cảnh literature

## S5.1 — Table IV vs Table VI (R1-8)
- **Việc**: bảng đối chiếu tại N=1000 giữa (test 300, frozen-C1) và (test 22,544, re-fit) + caption giải thích.
- **Exit**: chênh lệch được giải thích **định lượng**, không phải bằng lời.
- **📝 Kết quả**: *(chưa chạy)*

## S5.2 — Subsection "protocol vs literature" (R1-9)
- **Việc**: liệt kê lý do F1 thấp hơn con số thường thấy: macro-F1 (không phải accuracy), full KDDTest+ (không phải random split của KDDTrain+), K=20 + PCA-4 (không phải 122-dim), N ≤ 5000 (không phải 125,973), binary mapping. Kèm 2–3 ref bối cảnh — **báo bạn Quang Anh để gộp vào ngân sách 45 refs**.
- **Exit**: một subsection ~250 từ + danh sách ref đề xuất.
- **📝 Kết quả**: *(chưa chạy)*

---

# GIAI ĐOẠN 6 — Note C4 & đồng bộ

## S6.1 — Note C4
- **Việc**: viết `notebooks/nslkdd/note/C4/C4_results_reviewer_analysis_and_manuscript_revision.md` theo **đúng format** note C1/C2/C3 của bạn Quang Anh (protocol → kết quả → reviewer resolution → hướng sửa manuscript → wording nên/không nên).
- **Exit**: bạn Quang Anh đọc là dùng được ngay.
- **📝 Kết quả**: *(chưa chạy)*

## S6.2 — Đồng bộ regime map
- **Việc**: cung cấp dòng C4 (low-data / rare-attack) cho Fig 10 mới; thống nhất với bạn Quang Anh để dùng **cùng một bộ số** giữa C2/C3/C4.
- **Exit**: một file `regime_map_rows.csv` chung.
- **📝 Kết quả**: *(chưa chạy)*

---

# GIAI ĐOẠN 7 — UNSW: audit và chốt phạm vi

## S7.1 — Kiểm kê hiện trạng
- **Việc**: đối chiếu `notebooks/unsw/` + `results/unsw/` với chuẩn mới. Đã biết trước: N_train=100, 5 run, 4 model, C=1.0 "neutral", không tuning set, không noise → **dưới chuẩn**.
- **Output**: bảng gap "cái gì tái dùng được / cái gì phải chạy lại".
- **Exit**: biết chính xác khối lượng phải chạy lại.
- **📝 Kết quả**: *(chưa chạy)*

## S7.2 — Chốt phạm vi UNSW
- **Đề xuất phạm vi**: C1-rule + stationary benchmark + prior-shift + low-data. **Không** lặp lại noise validation (C2 đã làm trên NSL-KDD; lặp lại chỉ tốn trang mà không trả lời objection mới).
- **Exit**: phạm vi được bạn duyệt.
- **📝 Kết quả**: *(chưa chạy)*

---

# GIAI ĐOẠN 8 — UNSW: pipeline độc lập

## S8.1 — Tiền xử lý UNSW riêng
- **Việc**: pipeline hoàn toàn tách biệt — **cấm** dùng lại scaler/PCA/SelectKBest của NSL-KDD. Ghi rõ categorical handling, split, class mapping.
- **Exit**: audit "no NSL-KDD artifact touched" pass.
- **📝 Kết quả**: *(chưa chạy)*

## S8.2 — Áp luật C1 cho UNSW
- **Việc**: chạy đúng luật 3 tầng của C1 (V ≥ 85% → KTA ≥ 95% → min Q) trên UNSW → `n*_UNSW`.
- **Lưu ý**: `n*_UNSW` **có thể ≠ 4**. Nếu vậy thì đó là **kết quả tốt**: chứng minh C1 là một *thủ tục*, không phải một con số cố định — đây chính là câu trả lời cho R3-1 (novelty = methodology).
- **Exit**: `c1_selection_unsw.json`.
- **📝 Kết quả**: *(chưa chạy)*

## S8.3 — Tuning set + tune C đối xứng
- **Việc**: tuning set riêng của UNSW, 5-fold, 1-SE, cho cả 7 model.
- **Exit**: `unsw_downstream_tuned_parameters.json` cùng schema với C2.
- **📝 Kết quả**: *(chưa chạy)*

---

# GIAI ĐOẠN 9 — UNSW: thí nghiệm

## S9.1 — Stationary, 10 run × 7 model
- **Exit**: 70 bản ghi + thống kê paired đầy đủ.
- **📝 Kết quả**: *(chưa chạy)*

## S9.2 — Prior-shift 3 mức, 10 run
- **Exit**: bảng cùng schema `c3_pairwise_statistics.csv`.
- **📝 Kết quả**: *(chưa chạy)*

## S9.3 — Low-data sweep trên UNSW
- **Exit**: đối chiếu trực tiếp với đường cong NSL-KDD.
- **📝 Kết quả**: *(chưa chạy)*

## S9.4 — Note UNSW + so sánh cross-dataset
- **Việc**: bảng "phát hiện nào transfer, phát hiện nào không" — đây là nội dung khoa học chính của dataset thứ 2.
- **Exit**: note + bảng transfer.
- **📝 Kết quả**: *(chưa chạy)*

---

# GIAI ĐOẠN 10 — Đóng gói và bàn giao

## S10.1 — Supplementary (R1-10)
S1 hyperparameter grid đầy đủ · S2 C1 sweep + ε-sensitivity · S3 noisy simulation · S4 baseline chi tiết · S5 **UNSW-NB15** · S6 rare-attack · S7 thống kê chi tiết · S8 per-seed · S9 derivation nếu giữ.
- **📝 Kết quả**: *(chưa chạy)*

## S10.2 — Reproducibility (R4-2)
`uv sync` chạy sạch · README có lệnh tái tạo từng bảng · pin phiên bản Qiskit/sklearn · seed và config trong repo · repo public.
- **📝 Kết quả**: *(chưa chạy)*

## S10.3 — Bàn giao số cho thầy
`docs/revision/paper1_revision_report.md`: mỗi bảng/hình cũ → số mới → câu chữ đề xuất → item reviewer được đóng.
- **📝 Kết quả**: *(chưa chạy)*

## S10.4 — Draft rebuttal
Point-by-point đủ **33 item**, mỗi item: trích reviewer → việc đã làm → bằng chứng (bảng/hình/file) → chỗ sửa trong bài.
- **📝 Kết quả**: *(chưa chạy)*

---

# C. Bảng thay claim (bàn giao thầy — dùng khi sửa .tex)

| Claim cũ trong `paper1.pdf` | Phải đổi thành |
|---|---|
| *"The quantum advantage is real and measurable in two regimes"* (Conclusion) | *"Within the evaluated baselines and protocol, QSVM-ZZ shows a regime- and comparator-dependent empirical advantage"* |
| *"QSVM-ZZ dominates every classical baseline at every N"* (V-D) | thay bằng kết quả 10-run có CI, đối chiếu cả RF/XGB |
| *"+6.7 points ... Cohen's d of +0.68"* (V-D) | thay bằng số đã kiểm chứng ở S4.3 |
| *"Under class-prior shift the quantum kernel attains the highest mean F1"* (Abstract) | *"...highest mean F1 among the SVM-family baselines; XGBoost is favourable in the attack-heavy condition"* |
| *"NISQ-feasible / NISQ-ready"* | *"NISQ-aware / hardware-constrained; backend-derived noisy simulation, not physical-device validation"* |
| Theorem 1, Def 4, Algorithm 1 (Pareto) | thay bằng luật 3 tầng của C1 revision; **bỏ Theorem 1** |
| Proposition 3 | hạ thành một câu cite, bỏ khung "Proposition" |
| *"we compare against six classical SVM baselines"* | *"...against six SVM configurations and two strong tabular learners (Random Forest, XGBoost)"* |

---

# D. Rủi ro đã nhận diện

| Rủi ro | Xác suất | Xử lý |
|---|---|---|
| Kết quả C4 mới cho thấy XGB thắng QSVM ở nhiều N | Trung bình–cao | Đã có kịch bản: đổi claim thành "competitive in the small-sample regime", đây vẫn là kết quả hợp lệ và R3 sẽ đánh giá cao sự trung thực |
| UNSW cho `n* ≠ 4` | Trung bình | Là **điểm cộng**: chứng minh C1 là thủ tục có thể chuyển giao |
| Bài vượt 12 trang (phí MOPC) | Cao | Đẩy toàn bộ grid/sweep/UNSW/noise chi tiết sang supplementary ngay từ đầu; main paper chỉ giữ bảng tóm tắt |
| Không có `.tex` bản nộp | **Đang xảy ra** | Xin thầy ngay tuần này — chặn khâu bản highlight vàng |
| Số của C2/C3/C4 lệch nhau trong bài | Trung bình | Gate S1.3 + file `regime_map_rows.csv` dùng chung ở S6.2 |

---

# E. Tiến độ

| Giai đoạn | Trạng thái | Ngày |
|---|---|---|
| 0 | ✅ Xong — xem [02_PROGRESS](02_PROGRESS.md) | 2026-09-01 |
| 1 | ✅ Xong — gate G2 PASS | 2026-09-01 |
| 2 | ⬜ | |
| 3 | ⬜ | |
| 4 | ⬜ | |
| 5 | ⬜ | |
| 6 | ⬜ | |
| 7 | ⬜ | |
| 8 | ⬜ | |
| 9 | ⬜ | |
| 10 | ⬜ | |
