# KẾ HOẠCH HỢP NHẤT — Paper 2 (dự phòng): Reliability & Calibration của Quantum Kernel IDS

> **File plan DUY NHẤT.** Xương sống = `paper2.md` (hướng reliability/calibration của bạn đồng nghiệp),
> bổ sung "kỷ luật kiểm chứng trước" + bảng tài sản tái dùng từ bản nháp cũ.
>
> - **Paper 1** = `manuscript.pdf` — "NISQ-Aware Quantum Kernel SVM for NIDS" (đã/đang nộp IEEE; trục = *khi nào QSVM thắng hiệu năng*).
> - **Paper 2** = file này — trục = *dự đoán của QSVM có ĐÁNG TIN để triển khai không* (reliability/calibration).
> - **Nguyên tắc:** KHÔNG sửa code cũ. Chỉ thêm file mới. Tái dùng số QSVM đã cache.

---

## 1. Vì sao đổi sang trục reliability (không đấu accuracy)

- Trên accuracy/F1, QSVM 4-qubit (chỉ 4 chiều) **thua đậm** XGBoost/RandomForest/MLP trên dữ liệu bảng → nếu khoe "QSVM chính xác hơn DL/ML" sẽ bị bóc.
- **Calibration/Reliability** là sân QSVM có cửa: DL thường *overconfident*; số C5 đã cho thấy QSVM **ECE_rare thấp hơn** (tốt hơn) và **AUC-PR rare cao nhất** so với SVM.
- Khoảng trống: chưa ai nghiên cứu calibration của quantum kernel cho IDS → góc "first-of-its-kind".

**Bài học bắt buộc:** claim margin cũ của C5 từng bị **đảo ngược** (Cohen's d = −0.68, RBF margin rộng hơn chứ không phải QSVM). ⇒ **Kiểm chứng số THẬT trước khi viết bất kỳ narrative nào.**

---

## 2. Research Questions (từ paper2.md)
- **RQ1** Quantum kernel có over-confident không?
- **RQ2** Dự đoán trên nhóm tấn công hiếm (U2R/R2L) có đáng tin không?
- **RQ3** Độ tin cậy thay đổi thế nào dưới prior shift?
- **RQ4** Platt scaling cải thiện calibration đến đâu?

## 3. Contributions (từ paper2.md)
- **C1** Calibration Analysis — ECE, Brier, Reliability Diagram (nguồn: C5)
- **C2** Rare-Attack Reliability — Precision/Recall, PR curve, AUC-PR (nguồn: C5)
- **C3** Reliability under Prior Shift — ECE/Brier/AUC-PR trên Balanced/Attack-heavy/DoS-only (nguồn: C4)
- **C4** Probability Calibration via Platt Scaling — ECE/Brier before vs after (nguồn: C5)
- **A1** (phụ) Low-data Reliability — ECE(N)/Brier(N)/AUC-PR(N), **KHÔNG dùng F1 learning curve** (nguồn: C6)
- **A2** (phụ) Temporal Reliability — ECE/Brier temporal (nguồn: C4)

## 4. KHÔNG dùng (loại khỏi paper 2)
Kernel geometry/KTA/entanglement ablation (C3 cũ), Gaussian perturbation (C4), sample-complexity advantage & F1 learning curve (C6), Pareto optimization (C1) — vì thuộc trục accuracy/lý thuyết của Paper 1.

---

## 5. Baselines (mở rộng so với paper2.md)
- **Quantum:** QSVM-ZZ (đối tượng chính, tái dùng cache).
- **Classical SVM:** SVM-RBF (giữ liên thông Paper 1; số đã có trong C5).
- **Machine Learning:** **Random Forest, XGBoost**.
- **Deep Learning:** **MLP** (+ tùy chọn 1D-CNN nếu cần).

> Treatment công bằng: **mọi model đều được Platt-scale** (fit train, apply test) trước khi tính ECE/Brier
> — đúng protocol C5. SVM/QSVM dùng `decision_function`; RF/XGB/MLP dùng score (predict_proba/logit) đưa vào Platt.
> AUC-PR/ROC là rank-metric nên Platt không đổi → phản ánh xếp hạng gốc.

---

## 6. KỶ LUẬT THỰC HIỆN — "verify-first" (điểm bổ sung quan trọng)

### BƯỚC 1 — Kiểm chứng rẻ (đang làm) ⏳
Chạy RF/XGBoost/MLP qua **đúng** 5 run + test của C5 (matched-4D), **đúng** hàm ECE/AUC-PR + thêm Brier.
Sanity-check: tự tính lại ECE_rare của QSVM phải khớp **0.4503** (mean) ⇒ xác nhận methodology trùng khít.
**Mục tiêu:** xem QSVM có thật sự thắng calibration/AUC-PR trước DL/ML không.
- Nếu **thắng** → narrative mạnh: "QSVM kém accuracy nhưng đáng tin hơn".
- Nếu **không thắng tuyệt đối** → đổi sang "khảo sát calibration đầu tiên" (thắng ở rare subset, chỉ ra DL overconfident).
**Chốt narrative theo SỐ, không chốt trước.**

### BƯỚC 2 — Làm đầy đủ theo số đã chốt
Thêm Brier + Cohen's d (ECE/Brier/AUC-PR) + Platt before/after + RF/XGB vào C5; đổi C4 từ F1→ECE/Brier/AUC-PR + degradation curve; C6 tính ECE(N)/Brier(N)/AUC-PR(N).

### BƯỚC 3 — Trình bày + viết
Notebook trình bày, hình (8 figure), bảng (5 table), rồi viết paper.

---

## 7. Tài sản tái dùng (KHÔNG tạo lại)

| Cần | Nguồn |
|---|---|
| 5 train run (1000 mẫu) | `data/processed_data/multi_run/train_run{1..5}.csv` |
| Test cố định (rare U2R/R2L) | `data/processed_data/NSL_KDD_Test_Sample100.csv` |
| Model QSVM/SVM đã train mỗi run | `models/qsvm_cache/multirun_c5/run_{1..5}/models_*.joblib` |
| Số QSVM calibration đã tính | `data/processed_data/c5_multirun_per_run.csv`, `c5_results_multirun.json` |
| Prior-shift test | `NSL_KDD_Test_C4_E3a/b/c_*Sample300.csv` |
| Low-data | `NSL_KDD_Train_Sample{100,200,500}.csv` |
| Temporal | `NSL_KDD_Test21_Cleaned.csv` |
| Pipeline giảm chiều | `feature_selector_k20.joblib`, `pca_4components.joblib`, `scaler_minmax_pi.joblib` |
| 122 feature chuẩn | `data/processed_data/feature_columns.csv` |

Hàm chuẩn trích từ `c5_confidence_calibration_multirun.ipynb`: `transform_pipeline`, `PlattScaler`,
`adaptive_calibration_curve` (equal-frequency), `compute_ece_mce` (ECE_full bins=10, ECE_rare bins=5), `cohens_d`.

---

## 8. File MỚI sẽ tạo

```
src/reliability.py                      # hàm dùng chung: ECE/Brier/Platt/model factory RF·XGB·MLP
runners/run_reliability_verify.py       # BƯỚC 1: kiểm chứng calibration RF/XGB/MLP vs QSVM
data/processed_data/p2_verify_*.json    # output Bước 1
runners/run_reliability_full.py         # BƯỚC 2 (sau khi chốt)
notebooks/p2_reliability_calibration.ipynb  # BƯỚC 3 trình bày
reports/p2_*.png                        # hình paper
```
Quy ước: tên hàm/biến tiếng Anh PEP8; comment/docstring + markdown notebook tiếng Việt; mọi `open()` có `encoding='utf-8'`.

---

## 9. Checklist
### Phase 0 ✅
- [x] Đọc & hiểu 3 file; phân tích gap 6 contribution; khảo sát codebase
- [x] Cài `torch 2.12.1+cpu` + `xgboost 3.3.0`
- [x] Trích đúng hàm ECE/Platt/pipeline từ C5; xác định 5 run + test + cache

### Phase 1 — BƯỚC 1 kiểm chứng ✅ XONG
- [x] `src/reliability.py` + `runners/run_reliability_verify.py`
- [x] Sanity-check ECE_rare QSVM = **0.4503** ≡ C5 (methodology trùng khít)
- [x] Bảng ECE/Brier/AUC-PR: QSVM vs SVM-RBF vs RF vs XGB vs MLP → `p2_verify_calibration.json`
- [x] **CHỐT narrative**: QSVM **thắng calibration (ECE_rare 0.4503, Brier_rare 0.3288 — thấp nhất)**
      đánh bại cả MLP/RF/XGBoost; **thua accuracy/F1 & AUC-PR** (RF/XGB rank tốt hơn nhưng
      overconfident, Brier_rare ~0.63). Trục thắng = **calibration/reliability**, KHÔNG phải ranking.

### Phase 2 — đầy đủ ✅ XONG (recompute nhanh, QSVM train 0.1–4.8s)
- [x] C1/C2: Brier + Cohen's d + figures → `p2_calibration_stats.json`, `reports/p2_fig_*.png`
- [x] C3 prior-shift: ECE/Brier/AUC-PR → `p2_priorshift.json`
- [x] A1 low-data: ECE(N)/Brier(N)/AUC-PR(N) → `p2_lowdata.json` (QSVM cache MỚI `p2_lowdata/`)
- [x] C4 Platt before/after → `p2_platt.json`

> **PHÁT HIỆN TRUNG THỰC (đã verify):**
> - QSVM thắng calibration **chỉ trên rare attacks** (ECE_rare/Brier_rare thấp nhất, |d|=1.9–3.6 vs trees).
> - Trên **toàn tập** (prior-shift, low-data) QSVM **chỉ cạnh tranh**; **MLP thường calibrate tốt hơn**.
> - Platt **giúp QSVM/SVM, hại trees/MLP** → đóng góp phương pháp.
> - **Thesis chốt:** "Regime-specific reliability — QSVM đáng tin nhất ở rare attacks", KHÔNG over-claim.

### Phase 3 — trình bày ✅ XONG
- [x] Notebook `notebooks/p2_reliability_calibration.ipynb` (16 cell, 0 lỗi, markdown tiếng Việt)
- [x] 7 hình → `reports/p2_fig_*.png` (ECE/Brier rare, reliability diagram, prior-shift, low-data, Platt, forest plot, AUC-PR vs Brier)
- [x] 3 bảng inline (calibration rare, Cohen's d, Platt before/after) + bảng prior-shift/low-data

### Phase 4 — viết paper ✅ XONG (bản hoàn thiện, phản chiếu Paper 1)
- [x] `paper2/main.tex` — IEEEtran, **8 section giống Paper 1** (Intro, Background+Related, Framework, Setup, Results, Regime Map, Limitations, Conclusion)
- [x] Formal: 2 Definition, 1 Proposition (Platt preserves ranking), 1 Assumption, 1 Problem, 1 Algorithm
- [x] **8 bảng + 9 hình** (gồm sơ đồ pipeline + A2 temporal); tác giả = nhóm Paper 1; bib 15 ref; mọi ref/cite/label khớp
- [x] **A2 Temporal reliability** (`run_reliability_temporal.py` → `p2_temporal.json`): KDDTest-21, mọi model degrade, QSVM hạng 2 (đúng kỳ vọng Paper 1) — đủ C1–C4 + A1 + A2 như plan paper2.md
- [ ] Biên dịch trên Overleaf (máy local không có pdflatex)

---

## 10. Trạng thái quyết định
| # | Vấn đề | Quyết định |
|---|---|---|
| Hướng | Reliability/calibration (paper2.md) hay so accuracy (plan cũ)? | ✅ **Reliability** (paper2.md làm xương sống) |
| Số QSVM | Tái dùng hay chạy lại? | ✅ Tái dùng cache + chỉ recompute nhẹ để lấy Brier |
| Định dạng | LaTeX/Word? | ✅ Chưa viết — làm code+kết quả trước |
| Phạm vi baseline | | QSVM, SVM-RBF, RandomForest, XGBoost, MLP (+1D-CNN tùy chọn) |

**Đang làm: BƯỚC 1 — kiểm chứng calibration RF/XGB/MLP vs QSVM.**
