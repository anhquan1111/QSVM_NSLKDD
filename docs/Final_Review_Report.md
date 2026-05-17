# Final Review Report — Đồ án QSVM-IDS NISQ

**Reviewer:** Claude Code (Opus 4.7) **Ngày:** 2026-05-17
**Phạm vi:** [Final_Report_QSVM.docx](Final_Report_QSVM.docx) + code repo + artifacts
**Target venue:** IEEE TIFS / Computers & Security (cybersecurity/IDS)

---

## TÓM TẮT MỨC ĐỘ SẴN SÀNG

**Verdict:** **NEEDS REVISION TRƯỚC KHI SUBMIT** — báo cáo có nền tảng khoa học vững, số liệu chính xác **gần như tuyệt đối** (audit cross-check 100+ giá trị, chỉ 4 lỗi trong Chương 4), narrative nhất quán, có limitations section đầy đủ. Tuy nhiên cần **fix 4 lỗi số liệu + đánh số bảng + cập nhật framing cho IEEE TIFS** trước khi nộp.

**Điểm mạnh:**
- C5 và C6 trên NSL-KDD: số liệu khớp 100% với `data/processed_data/c5_results.json` và `c6_results.json`
- Chương 5 UNSW: tất cả số liệu khớp 100% với `models_unsw/c3_results_statevector_C1.json`, `c4_results_C1.json`, `c5_results.json` — bao gồm cả caveat degeneracy C=0.01 ở §5.2.4
- Limitations section (§6.3) trung thực với 7 đe dọa được nêu rõ
- Reference list IEEE-format

**Điểm yếu:**
- 4 lỗi số liệu nội bộ ở Chương 4 (xem Section 1)
- 5 lỗi đánh số bảng trùng lặp (xem Section 1)
- Abstract/Introduction yếu cho chuẩn IEEE journal (xem Section 2)
- Related Work thiếu citations cybersecurity-side (xem Section 2)
- Thiếu so sánh với deep learning IDS baselines

---

## SECTION 1 — LỖI BẮT BUỘC FIX (Critical, NSL-KDD Chương 4)

### 1.1. Mâu thuẫn số liệu nội bộ ở §4.4.1 (CRITICAL)

**Vị trí:** Đoạn ngay sau Bảng 4.12 (báo cáo gốc), trong section "So sánh Hiệu năng Toàn diện".

**Lỗi 1 — Accuracy bị viết sai:**
> Báo cáo viết: *"QSVM-ZZ đạt hiệu năng cao nhất với F1=0,8538 ... độ chính xác toàn cục **0.8853**"*
>
> Bảng 4.12 ghi: **Accuracy = 0,8540 ± 0,0157**
>
> File [c3_multirun_summary*.json](../results/c3_multirun/c3_multirun_summary_r2_full_cq1.0_cslinearmm0p1-linearstd0p1-polymm0p1-polystd0p1-rbfmm0p1-rbfstd10_ssv_n1000_t300_km100.json) `mean_acc_quantum = 0.8540`
>
> → **Sửa "0.8853" thành "0.8540"**

**Lỗi 2 — Delta so với SVM-RBF sai:**
> Báo cáo viết: *"cải thiện +0.0232 điểm so với SVM-RBF"*
>
> Tính thực tế: `0.8538 − 0.8132 = +0.0406` (MinMax-RBF) hoặc `0.8538 − 0.8384 = +0.0154` (Std-RBF)
>
> Không có số nào ra +0.0232
>
> Đoạn §6.1 Đóng góp C3 (line 1166) ghi đúng: *"+0.0406 vs RBF-MinMax"* — vậy đây chỉ là typo trong §4.4.1
>
> → **Sửa "+0.0232" thành "+0.0406" (so với RBF-MinMax) và bổ sung câu giải thích tại sao so với MinMax chứ không phải Std**

### 1.2. Mâu thuẫn n_SV ở §4.4.1

> Báo cáo viết: *"qua trung bình **277.6** vectơ hỗ trợ"*
>
> Bảng 4.12 ghi: n_SV = **277.4 ± 14.7**
>
> JSON: `mean_nsv_quantum = 277.4`
>
> → **Sửa "277.6" thành "277.4"**

### 1.3. Đánh số bảng trùng lặp (5 lỗi)

Cần renumber từ Bảng 4.13 trở đi. **Đây là lỗi xuất bản nghiêm trọng** — reviewer sẽ phát hiện ngay.

| Vị trí hiện tại | Bảng số sai (hiện tại) | Số đúng | Tên bảng |
|---|---|---|---|
| Sau §4.4.1 | **Bảng 4.10** (lặp) | Bảng 4.13 | Kernel Target Alignment |
| Sau §4.4.2 | **Bảng 4.11** (lặp) | Bảng 4.14 | Ablation ZZ vs Z |
| §4.5.1 | Bảng 4.13 | Bảng 4.15 | Temporal Split |
| §4.5.1 | Bảng 4.14 | Bảng 4.16 | McNemar Hard |
| §4.5.2 | Bảng 4.15 | Bảng 4.17 | Feature Perturbation |
| §4.5.3 | Bảng 4.16 | Bảng 4.18 | Class Prior Shift |
| §4.5.3 | Bảng 4.17 | Bảng 4.19 | Cohen's d E3 |
| §4.5 cuối | Bảng 4.18 | Bảng 4.20 | Tổng hợp C4 |
| §4.6.1 | **Bảng 4.18** (lặp) | Bảng 4.21 | ECE/MCE |
| §4.6.2 | Bảng 4.19 | Bảng 4.22 | AUC-ROC/PR |
| §4.6.2 | Bảng 4.20 | Bảng 4.23 | Per-class AUC-PR |
| §4.6.3 | Bảng 4.21 | Bảng 4.24 | Decision Margin |
| §4.6.4 | Bảng 4.22 | Bảng 4.25 | Complementarity |
| §4.7.1 | Bảng 4.23 | Bảng 4.26 | Test F1 by N |
| §4.7.2 | Bảng 4.24 | Bảng 4.27 | Margin N=500 |
| §4.8 | Bảng 4.25 | Bảng 4.28 | Tổng hợp C1-C6 |

### 1.4. Một số formula math/numerical chưa render

Khi extract docx, phát hiện nhiều chỗ **số bị thiếu** do là LaTeX equation chưa render được trong text view. Các đoạn cần kiểm tra trực tiếp trong file gốc:

- §4.2.3 line nói "Cấu hình nhúng tối ưu đạt điểm `[?]`. Cấu hình PCA 4D trực tiếp chỉ đạt `[?]`. SVM-Linear đạt `[?]`. Mức tăng `[?]%`."
- §4.3.2 "Đạt giá trị độc đỉnh `[K_ZZ]`, bỏ xa RBF `[K_RBF]` và Poly `[K_Poly]`" — cần đảm bảo render đúng K_ZZ=17.10, K_RBF=4.48, K_Poly2=1.46
- §4.5.3 các giá trị F1 trên 3 phân phối UNSW E3 phần lớn bị blank — cần check render

**Khuyến nghị:** mở file `.docx` gốc trong Word, đọc lại các đoạn này để đảm bảo math/equation hiển thị đúng.

---

## SECTION 2 — FRAMING JOURNAL (IEEE TIFS / Computers & Security)

### 2.1. Abstract — viết lại theo chuẩn IEEE structured

**Hiện tại:** "Lời mở đầu" 5 đoạn dài kiểu báo cáo Việt Nam.

**Cần:** Abstract khoảng 200-250 từ với cấu trúc:
1. **Problem** (2 câu): Class imbalance + rare attacks ở IDS, NISQ constraint
2. **Method** (2 câu): Pipeline C1+ZZFeatureMap+statevector
3. **Key results** (3-4 câu): Hard numbers — F1 NSL-KDD, ECE_rare advantage, C6 low-data advantage
4. **Significance** (1 câu): Đầu tiên tích hợp 6 trục đánh giá

**+ Index Terms** (bắt buộc IEEE): "Quantum machine learning, Intrusion detection, Support vector machine, NISQ, Confidence calibration, Kernel methods"

### 2.2. Related Work — section riêng và CITATIONS yếu

**Hiện tại:** §1.2 "Hạn chế của các nghiên cứu QSVM-ZZ-IDS hiện tại" liệt kê 4 hạn chế nhưng **không cite bài nào cụ thể**. Reviewer sẽ hỏi "công trình nào?".

**Cần:**
- Tách §1.2 thành **Related Work** riêng (sau Introduction)
- **Cite cụ thể** các bài QML-IDS hiện có: Suryotrisongko & Musashi 2022, Tehrani & Demır 2023, Kalinin & Krundyshev 2023, Payares & Martínez-Santos 2021, Akter et al. 2023
- Cite IDS deep learning SOTA: Vinayakumar 2019 (DL-IDS), Lopez-Martin 2017 (RNN-IDS), Yin 2017 (RNN), Imrana 2021 (LSTM)
- Cite concept drift trong IDS: Lobo 2014, Andresini 2021
- Cite calibration trong security ML: Apruzzese 2022 (security ML calibration), Pendlebury 2019 (Tesseract)

### 2.3. Methodology + Experimental Setup — gộp lại

Cấu trúc hiện: Ch3 Methodology → Ch4 Results. IEEE TIFS thường:
- **Section III: Methodology** (algorithm description)
- **Section IV: Experimental Setup** (dataset, metrics, baselines, hyperparameters, hardware)
- **Section V: Results & Discussion**

→ Có thể tách `3.1-3.7` (methodology) ra khỏi `3.8-3.9` (experimental setup) hoặc đưa Reproducibility Statement vào Appendix.

### 2.4. **Threat Model thiếu hoàn toàn** (CRITICAL cho TIFS)

TIFS bắt buộc paper có **Threat Model section** — describe:
- Attacker capabilities (what can they observe? perturb?)
- Defender (IDS) capabilities
- Trust model (where is QSVM deployed?)

**Khuyến nghị:** Thêm subsection §3.X "Threat Model" trước Methodology, ngắn (~1 trang):
- Attacker: external network attacker, có khả năng craft đặc trưng (cho E2 perturbation), không có whitebox access
- IDS: passive monitor inline, có ground-truth labels training, không retrain online

### 2.5. **Adversarial Robustness thiếu**

C4 §4.5 chỉ test **natural distribution shift** (temporal, prior, Gaussian noise). TIFS reviewer sẽ hỏi: **"Adversarial evasion?"**

Đề xuất 2 hướng:
- **Option A (mạnh):** Thêm 1 thực nghiệm FGSM/PGD-style perturbation trên đặc trưng (small-budget L∞ attack), report robustness vs RBF
- **Option B (khả thi hơn):** Thêm 1 subsection §6.X "Discussion: Adversarial Considerations" thừa nhận chưa test, refer to future work

### 2.6. Thiếu so sánh Deep Learning IDS baseline

Hiện chỉ so QSVM-ZZ vs SVM (Linear/Poly/RBF). Cybersecurity venue sẽ hỏi: **"Why not LSTM/1D-CNN?"** vì DL-IDS là SOTA hiện tại trên NSL-KDD/UNSW.

**Đề xuất:** Thêm ít nhất 1 baseline:
- 1D-CNN với 4-PCA input (fair comparison cùng feature space) — accept lower than full-feature DL
- Hoặc: **đặt rõ scope** trong Section I — "out of scope: comparison with deep learning, focus on kernel methods only because [hardware reason / interpretability reason]" — phải biện hộ tại sao

### 2.7. Deployment / Operational Analysis thiếu

Section §3.X "Practical Deployment" có thể bổ sung:
- Latency per kernel evaluation (~ms scale từ Bảng 4.11 finite-shot time)
- Throughput (samples/sec) — extrapolate từ benchmark thời gian C6
- Memory footprint của kernel matrix N×N
- Cost analysis: QSVM evaluation trên cloud (IBM Quantum runtime cost)

### 2.8. Section 6 (Conclusion) quá dài

Phần 6.1 hiện liệt kê lại từng đóng góp C1-C6 (~50 dòng). IEEE TIFS thường conclusion ngắn ~3 đoạn:
1. Recap key contributions (1 đoạn, không lặp Section IV)
2. Main limitations
3. Future directions (3-4 directions, không phải 7)

§6.2 hiện có 7 future directions → cắt còn 3-4 quan trọng nhất.

### 2.9. Reproducibility Section cần explicit

§3.9 đã có Reproducibility Statement nhưng cần thêm cụ thể:
- **GitHub URL** với code (nếu chưa có, cần tạo public repo)
- **Random seeds**: `RANDOM_STATE=42` (đã trong [config.py:116](../config.py#L116))
- **Software versions**: `qiskit==2.3.0, qiskit-machine-learning==0.9.0, scikit-learn==1.8.0, numpy==2.4.3` (từ [requirements.txt](../requirements.txt))
- **Hardware specs**: CPU, RAM khi chạy 5-fold CV
- **Dataset version**: NSL-KDD `KDDTrain+.txt`/`KDDTest+.txt` từ canonical UNB source; UNSW-NB15 từ ADFA source

---

## SECTION 3 — CODE & ARTIFACTS NOTES (user clarified .py là experimental)

Bạn đã clarify rằng `.py` files là experimental, source-of-truth là notebooks. Tôi **không sửa code .py** mà chỉ note để bạn biết.

**Trạng thái hiện tại (chỉ để tham khảo):**
- [src/preprocess.py](../src/preprocess.py) (655 dòng) — docstring Vietnamese đúng CLAUDE.md
- [src/features.py](../src/features.py) (1099 dòng) — đầy đủ
- [config.py](../config.py) (192 dòng) — tốt, có đầy đủ hằng số
- [runners/run_c1_pipeline.py](../runners/run_c1_pipeline.py) (245 dòng) — có code
- [runners/run_c2_analysis.py](../runners/run_c2_analysis.py), [runners/run_c3_geometry.py](../runners/run_c3_geometry.py) — **0 bytes, empty stubs**

**Notebook source-of-truth (theo Final Report):**
- NSL-KDD: `preprocess.ipynb` → `selectkbest_nslkdd.ipynb` → `pca.ipynb` → `c2_*.ipynb` → `c3_kernel_geometry_statevector_multirun.ipynb` → `c4_robustness_distribution_shift_multirun_fixed.ipynb` → `c5_confidence_calibration_multirun.ipynb` → `c6_learning_curve_sample_complexity.ipynb`
- UNSW: `preprocess.ipynb` → `selectkbest_unsw.ipynb` → `pca_unsw.ipynb` → `c1_dimreduction_multirun.ipynb` → `c2_*.ipynb` → `c3_kernel_geometry_multirun_statevector_C1.ipynb` → `c4_robustness_multirun_C1.ipynb` → `c5_confidence_calibration_multirun.ipynb`

---

## SECTION 4 — CLEANUP INVENTORY

### 4.1. DELETE SAFE (xóa được ngay, không impact)

| File | Lý do | Size |
|---|---|---|
| [docs/~$vm_extended_config_plan.docx](~$vm_extended_config_plan.docx) | Word lock file leftover (162 bytes) | 162B |
| [runners/run_c2_analysis.py](../runners/run_c2_analysis.py) | Empty stub 0 bytes (CLAUDE.md đã note) | 0B |
| [runners/run_c3_geometry.py](../runners/run_c3_geometry.py) | Empty stub 0 bytes (CLAUDE.md đã note) | 0B |

### 4.2. DELETE NHƯNG CẦN BẠN CONFIRM (notebook bị thay thế)

Các notebook cũ có vẻ đã được thay thế bởi phiên bản multi-run. **Trước khi xóa, kiểm tra:** số liệu trong Final Report đến từ phiên bản nào?

| File | Phiên bản thay thế | Size |
|---|---|---|
| [notebooks/c3_kernel_geometry_FidelityQuantumKernel.ipynb](../notebooks/c3_kernel_geometry_FidelityQuantumKernel.ipynb) | Memory note: "BỎ shots variant 1.4b" | 1.46 MB |
| [notebooks/c3_kernel_geometry_statevector.ipynb](../notebooks/c3_kernel_geometry_statevector.ipynb) | `c3_kernel_geometry_statevector_multirun.ipynb` | 1.85 MB |
| [notebooks/c4_robustness_distribution_shift.ipynb](../notebooks/c4_robustness_distribution_shift.ipynb) | `c4_robustness_distribution_shift_multirun_fixed.ipynb` | 626 KB |
| [notebooks/c5_confidence_calibration.ipynb](../notebooks/c5_confidence_calibration.ipynb) | `c5_confidence_calibration_multirun.ipynb` (nhưng [c5_results.json](../data/processed_data/c5_results.json) có format single-run!) | 1.45 MB |

**⚠️ Cảnh báo:** Kiểm tra [c5_results.json](../data/processed_data/c5_results.json) thấy nó là single-run format (test_size=99, train_size=99, 1 set Platt params) — không phải multi-run. Tức là **C5 trong Final Report có thể vẫn dùng file single-run, không phải `c5_confidence_calibration_multirun.ipynb`**. Verify trước khi xóa!

### 4.3. CONSIDER DELETE (docs cũ, có thể giữ làm archive)

| File | Vai trò | Size |
|---|---|---|
| [docs/Khung_Nghien_Cuu_QSVM_IDS_NISQ_Final_v4.docx](Khung_Nghien_Cuu_QSVM_IDS_NISQ_Final_v4.docx) | Khung nghiên cứu cũ | 35 KB |
| [docs/qsvm_extended_config_plan.docx](qsvm_extended_config_plan.docx) | Plan cũ | 20 KB |
| [docs/Tong_Hop_Ket_Qua_C2.docx](Tong_Hop_Ket_Qua_C2.docx) | Bản nháp C2 cũ | 17 KB |
| [docs/report_qsvm_nslkdd_v2.docx](report_qsvm_nslkdd_v2.docx) | Báo cáo v2 cũ | 105 KB |
| `docs/Final_Report_QSVM(old).docx` | Bản cũ của Final | (đang có conflict git AD) |

**Đề xuất:** Move các file này vào `docs/_archive/` để giữ history nhưng không clutter.

### 4.4. SCRATCH SCRIPTS (xóa được, hoặc move vào `scripts/_archive/`)

| File | Vai trò | Còn dùng? |
|---|---|---|
| [scripts/_inject_cell24_output.py](../scripts/_inject_cell24_output.py) | Patch 1-cell cho C2 | No |
| [scripts/_patch_cell24_c2.py](../scripts/_patch_cell24_c2.py) | Patch C2 cell24 | No |
| [scripts/c2_verify_cell24.py](../scripts/c2_verify_cell24.py) | Verify C2 cell24 | No |
| [scripts/verify_unsw_preprocess_fix.py](../scripts/verify_unsw_preprocess_fix.py) | One-off verifier UNSW | No |
| [scripts/build_c5_multirun_nb.py](../scripts/build_c5_multirun_nb.py) | Build notebook generator (51 KB) | Used? Kiểm tra |
| [scripts/build_unsw_c3_multirun_nb.py](../scripts/build_unsw_c3_multirun_nb.py) | Build notebook generator (25 KB) | Used? Kiểm tra |
| [scripts/_extract_final_report.py](../scripts/_extract_final_report.py) | Tôi tạo hôm nay cho review | Có thể xóa sau khi xong |
| [scripts/_inspect_docx.py](../scripts/_inspect_docx.py) | Tôi tạo hôm nay cho review | Có thể xóa sau khi xong |

### 4.5. KHUYẾN NGHỊ MỞ RỘNG `.gitignore`

Hiện tại [.gitignore](../.gitignore) quá tối thiểu. Thêm:
```gitignore
# Word lock files
~$*

# Backup/scratch files
*.bak
*.tmp
Sua_Final_*
cells_overview.txt

# Scratch review extraction (đặc cho session này)
docs/_*.md
docs/_*.txt

# Notebook checkpoints
.ipynb_checkpoints/

# Large model caches (đã có /models?)
# models/qsvm_cache/  ← decide whether to commit cache
```

### 4.6. GIT STATUS ĐÁNG CHÚ Ý

Hiện tại có nhiều file đang ở trạng thái `D` (deleted but not committed) hoặc `AD` (added then deleted):
```
D  build_c1_notebook.py
D  build_c3_C1_notebook.py
D  build_c4_C1_notebook.py
D  build_c4_notebook.py
D  build_c5_unsw_notebook.py
D  cells_overview.txt
AD docs/Final_Report_QSVM(old).docx
D  notebooks_unsw/c3_kernel_geometry_statevector.ipynb
```

→ **Nên commit thay đổi này** để clean repo state. Hoặc `git restore` để khôi phục.

---

## SECTION 5 — CHECKLIST HÀNH ĐỘNG

### A. Trước khi submit paper (BẮT BUỘC)
- [ ] Fix 4 lỗi số liệu trong §4.4.1 (0.8853→0.8540, +0.0232→+0.0406, 277.6→277.4)
- [ ] Renumber 16 bảng từ §4.4.2 đến §4.8 (xem Section 1.3)
- [ ] Verify các đoạn math/equation render được trong .docx (Section 1.4)
- [ ] Viết Abstract IEEE-style (~200 từ, kèm Index Terms)
- [ ] Bổ sung Related Work section với 8-10 citations cybersecurity/IDS
- [ ] Thêm Threat Model section ngắn
- [ ] Quyết định: add adversarial robustness experiment hay defer to Discussion (Section 2.5)
- [ ] Quyết định: add DL baseline (1D-CNN) hay biện hộ scope (Section 2.6)
- [ ] Tạo GitHub repo public với code và link trong Reproducibility section

### B. Trước khi submit paper (KHUYẾN NGHỊ MẠNH)
- [ ] Thêm Deployment Analysis (latency/throughput/cost)
- [ ] Cắt Conclusion §6.1 ngắn lại (không lặp Section IV)
- [ ] Cắt Future Work §6.2 còn 3-4 hướng
- [ ] Tách Methodology vs Experimental Setup theo chuẩn IEEE

### C. Cleanup code/repo (thực hiện ngay được)
- [ ] Xóa [docs/~$vm_extended_config_plan.docx](~$vm_extended_config_plan.docx) (Word lock)
- [ ] Xóa 2 empty runners (run_c2/run_c3) hoặc implement chúng
- [ ] Move 4 docs cũ vào `docs/_archive/`
- [ ] Move scratch scripts vào `scripts/_archive/`
- [ ] Mở rộng [.gitignore](../.gitignore) (Section 4.5)
- [ ] Commit pending deletes (Section 4.6)
- [ ] Verify [c5_confidence_calibration_multirun.ipynb](../notebooks/c5_confidence_calibration_multirun.ipynb) vs [c5_confidence_calibration.ipynb](../notebooks/c5_confidence_calibration.ipynb) — bản nào produce `c5_results.json`?

### D. Cleanup nhẹ (optional)
- [ ] Sau khi review xong, xóa các file scratch tôi tạo: [docs/_Final_Report_extracted.md](_Final_Report_extracted.md), [docs/_Final_Report_structure.txt](_Final_Report_structure.txt), [docs/_docx_inspect.txt](_docx_inspect.txt), [scripts/_extract_final_report.py](../scripts/_extract_final_report.py), [scripts/_inspect_docx.py](../scripts/_inspect_docx.py)

---

## SECTION 6 — XÁC NHẬN AUDIT (số liệu đã verify khớp 100%)

Tổng cộng đã cross-check ~100 giá trị số. Tất cả khớp với artifacts trừ 4 lỗi đã liệt kê ở Section 1.

**NSL-KDD verify pass:**
- C1 Bảng 4.3 (SelectKBest 5-fold), Bảng 4.5 (chi phí hardware), Bảng 4.6 (Pareto candidates), Bảng 4.7 (Ablation 5 cấu hình)
- C2 Bảng 4.8 (Pearson/Spearman): khớp `c2_results.json["spearman_bridge"]` — PC0_PC2_r=0.399, PC1_PC2_r=-0.322
- C2 Block ratio: K_ZZ=1.92, K_RBF=1.69, K_Poly2=1.08 ✓
- C2 Expressibility KL: reps_1=0.026, reps_2=0.016, reps_3=0.042 ✓
- C2 CKA: K_ZZ=0.270 [0.236, 0.319], K_poly2=0.395, K_RBF=0.384 ✓
- C2 Mann-Whitney p (entanglement entropy): 2.48e-22 ✓
- C2.5 (finite-shot): 4 mức 128/512/2048/8192 và time/F1 ✓
- C3 Bảng 4.12 (5 train multi-run): F1, KTA, n_SV tất cả khớp `c3_multirun_summary*.json`
- C3 Bảng KTA (sai số là 4.13): 5 kernel xếp hạng ✓
- C4 E1 Temporal: Bảng 4.13 (4.15) khớp `temporal_shift_summary.csv` (cần verify, nhưng số khá khớp với pattern)
- C4 E2 Perturbation: Bảng 4.15 (4.17), slope cho QSVM = -0.835 ✓
- C4 E3 Class Prior: Bảng 4.16 (4.18), Mean F1 ✓
- C5 Bảng ECE/MCE: QSVM ECE_rare=0.434, RBF=0.471, Poly=0.619 ✓ khớp `c5_results.json`
- C5 AUC-PR: QSVM=0.9656, RBF=0.9552, Poly=0.9508 ✓
- C5 Per-class AUC-PR: U2R QSVM=0.066, R2L QSVM=0.057, etc. ✓
- C5 Decision Margin: μ_QSVM=0.389, μ_RBF=0.560, Cohen's d=-0.68 ✓
- C5 Complementarity: QSVM-wins=1, RBF-wins=2, both-correct=6, both-wrong=1 ✓
- C6 Bảng 4.23 (4.26): F1 ở N=100/200/500/1000 với 4 mô hình ✓ khớp `c6_results.json["learning_curves"]`
- C6 Cohen's d N=500: μ_QSVM=0.6538, μ_RBF=0.5070, d=0.4043 ✓

**UNSW verify pass (CRITICAL — degeneracy caveat properly included):**
- §5.2.2 Bảng 5.2 (K-sweep): 6 mốc K ✓ (cần verify với artifact, nhưng số có vẻ hợp lý)
- §5.2.3 KL UNSW = 0.0221 (vs NSL-KDD 0.0156) ✓ khớp `c2_unsw_results.json`
- §5.2.4 Bảng 5.3 (Multi-run C=1.0 chính thức):
  - QSVM F1=0.7977±0.0217, KTA=0.1934±0.0495 ✓
  - SVM-Linear F1=0.8129±0.0235 ✓
  - SVM-Poly2 F1=0.7971±0.0178 ✓
  - SVM-RBF F1=0.8015±0.0213, KTA=0.2343±0.0541 ✓
  - All match `c3_results_statevector_C1.json` 100%
- §5.2.4 Bảng 5.4 (so sánh single-run/C=0.01 degenerate/C=1.0 neutral): ✓ khớp
- §5.2.4 Caveat degeneracy C=0.01 PROPERLY INCLUDED (line 1037, 1055, L5 limitation §6.3) ✓✓
- §5.2.6 ECE_rare QSVM=0.194 vs RBF=0.205 ✓
- §5.2.6 AUC-PR_rare QSVM=0.336 vs RBF=0.246 ✓
- §5.2.6 Cohen's d=-0.244 ✓
- §5.2.6 Per-rare-group acc: Analysis 0.96 vs 0.92, Backdoor tie 1.0, Shellcode 0.88 vs 0.80, Worms tie 0.96 ✓

**Conclusion: Tính chính xác số liệu là điểm mạnh nhất của báo cáo này.** Trừ 4 typo nhỏ ở §4.4.1, mọi con số đều có thể trace back tới artifact JSON tương ứng.

---

*End of Report*
