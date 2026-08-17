# QSVM-IDS NISQ — Quantum Kernel SVM for Network Intrusion Detection

Khung khoa học áp dụng **Quantum Support Vector Machine (QSVM)** với **ZZ-FeatureMap** cho
phát hiện xâm nhập mạng, dưới ràng buộc **NISQ** (4 qubit). Mục tiêu: giải thích *khi nào* và
*vì sao* quantum kernel có lợi — và *liệu dự đoán có đáng tin* khi triển khai.

```
NSL-KDD (41 ft) → One-Hot (122D) → SelectKBest (20) → PCA (4D)
                → MinMax [0, π] → ZZ-FeatureMap (4 qubit, reps=2, full) → SVM
```

## Hai bài báo đồng hành

| | Trọng tâm | Câu hỏi | Trạng thái |
|---|---|---|---|
| **Paper 1** | Hiệu năng | *Khi nào QSVM thắng SVM cổ điển?* | Major revision @ IEEE TETC — xem [docs/PAPER1_overview.md](docs/PAPER1_overview.md) |
| **Paper 2** | Độ tin cậy | *Xác suất cảnh báo của QSVM có đáng tin không?* | Đã nộp @ IJNM (Wiley Q2) — xem [docs/PAPER2_overview.md](docs/PAPER2_overview.md) |

Nội dung `paper/paper1/` (TETC) và `paper/paper2/` (bản reliability đã nộp IJNM).

## Hai dataset
| Dataset | Vai trò | Notebooks |
|---|---|---|
| **NSL-KDD** | Benchmark chính (cả 2 paper) | `notebooks/nslkdd/` |
| **UNSW-NB15** | Kiểm chứng cross-dataset | `notebooks/unsw/` |

## Cấu trúc thư mục (theo dataset)
```
data/     { nslkdd/, unsw/ }   raw + processed_data
models/   { nslkdd/, unsw/ }   artifact (pkl/joblib/qsvm_cache)
results/  { nslkdd/, unsw/ }   metric JSON/CSV
reports/  { nslkdd/, unsw/ }   hình PNG/PDF
notebooks/{ nslkdd/, unsw/ }   thí nghiệm
runners/     script Paper 2 reliability
src/         reliability.py (helper Paper 2)
scripts/     tiện ích (check_notebook, extract_results, read_docx)
docs/        tài liệu (2 overview, revision plan, ...)
paper/    { paper1/, paper2/ }
config.py    đường dẫn trung tâm (dùng biến NSLKDD_*/UNSW_*)
```

## Notebooks NSL-KDD (`notebooks/nslkdd/`)
Chạy top-to-bottom: `preprocess` → `selectkbest_nslkdd` (C1) → `pca` (C1) →
`c2_quantum_kernel_expressibility` → `c2_5_fidelity_vs_statevector_kernel_fixed` →
`c3_c_tuning_statevector` → `c3_kernel_geometry_statevector_multirun` →
`c4_robustness_distribution_shift_multirun_fixed` → `c5_confidence_calibration_multirun` →
`c6_learning_curve_sample_complexity` → `c4_paper2_reliability_complete_fixed` (Paper 2).

## Notebooks UNSW-NB15 (`notebooks/unsw/`)
`preprocess` → `selectkbest_unsw` → `pca_unsw` → `c_tuning_statevector` →
`c1_dimreduction_multirun` → `c2_quantum_kernel_expressibility` →
`c3_kernel_geometry_multirun_statevector(_C1)` → `c4_robustness_multirun(_C1)` →
`c5_confidence_calibration_multirun`.
> Kết quả UNSW: QSVM **competitive, không dominant** — lợi thế NSL-KDD phụ thuộc regime/dataset.

## Setup
```bash
python -m venv venv && source venv/Scripts/activate
pip install -r requirements.txt
```

## Tái lập Paper 2 (reliability)
```bash
python runners/run_reliability_verify.py      # rare-attack calibration
python runners/run_reliability_recompute.py   # prior-shift + low-data + Platt
python runners/run_reliability_temporal.py    # temporal (KDDTest-21)
python runners/run_reliability_figures.py      # hình + Cohen's d
```
Build PDF: upload `paper/paper1/` hoặc `paper/paper2/` lên [Overleaf](https://overleaf.com) (pdfLaTeX).

## Ràng buộc chính
- **Zero-leakage:** transformer `fit()` train, `transform()` test.
- **Phần cứng:** cố định 4 feature = 4 qubit.
- **Thống kê:** multi-run (5 seed), mean ± std, McNemar + Cohen's d.
- **Code:** định danh tiếng Anh (PEP 8), comment tiếng Việt, `encoding='utf-8'` mọi file I/O (xem [AGENTS.md](AGENTS.md)).

## Dependencies
`numpy` · `pandas` · `scikit-learn` · `qiskit` 2.3 · `qiskit-machine-learning` 0.9 ·
`xgboost` · `scipy` · `matplotlib` · `seaborn` · `joblib`
