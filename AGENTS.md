# AGENTS.md

Hướng dẫn cho AI agent (Claude Code / v.v.) khi làm việc trong repo này.
**Các chỉ dẫn ở đây GHI ĐÈ hành vi mặc định và phải được tuân thủ.**

## Tổng quan dự án

**QSVM-IDS NISQ** — Khung khoa học áp dụng **Quantum Support Vector Machine (QSVM)** với
**ZZFeatureMap** cho phát hiện xâm nhập mạng, dưới ràng buộc phần cứng NISQ (4 qubit).
Mục tiêu không chỉ benchmark mà là **giải thích khi nào / vì sao** quantum kernel có lợi,
và **liệu dự đoán có đáng tin** khi triển khai.

Pipeline chung:
`NSL-KDD (41 ft) → One-Hot (122D) → SelectKBest (20D) → PCA (4D) → MinMax[0,π] → QSVM (ZZFeatureMap 4-qubit, reps=2, full)`

### Hai bài báo (xem chi tiết trong `docs/`)
| | Trọng tâm | Trạng thái | Doc |
|---|---|---|---|
| **Paper 1** | Hiệu năng theo regime (khi nào QSVM thắng SVM cổ điển) | **Major revision @ IEEE TETC** (hạn 13-Oct-2026) | [docs/PAPER1_overview.md](docs/PAPER1_overview.md) + [docs/paper1_revision_plan.md](docs/paper1_revision_plan.md) |
| **Paper 2** | Độ tin cậy / calibration (vs RF, XGBoost) | **Đã nộp @ IJNM (Wiley, Q2)** | [docs/PAPER2_overview.md](docs/PAPER2_overview.md) |

## Cấu trúc thư mục (tổ chức theo dataset)
```
data/     { nslkdd/, unsw/ }   # raw + processed_data  (raw NSL-KDD bị gitignore, auto-download)
models/   { nslkdd/, unsw/ }   # artifact: *.pkl, *.joblib, qsvm_cache/ (cache gitignore)
results/  { nslkdd/, unsw/ }   # metric JSON/CSV + thư mục con c3_multirun/c4_multirun/c4_paper2
paper/paper1/figs_revision/   # hình của bản revision (reports/ cũ đã gỡ)
notebooks/{ nslkdd/, unsw/ }   # thí nghiệm chính (executable chính của dự án)
runners/                       # 6 script Paper 2 reliability (import src.reliability)
src/                           # reliability.py (helper Paper 2) + __init__.py
scripts/                       # 3 tiện ích: check_notebook, extract_results, read_docx
docs/                          # tài liệu (2 overview, revision plan, final report, archive)
paper/    { paper1/, paper2/ } # LaTeX + PDF (paper2 = bản reliability đã nộp IJNM)
config.py                      # ĐƯỜNG DẪN TRUNG TÂM — xem bên dưới
```

### `config.py` là nguồn path chuẩn
Đọc path qua config, đừng hardcode. Biến chính:
`NSLKDD_RAW_DIR`, `NSLKDD_PROCESSED_DIR`, `UNSW_RAW_DIR`, `UNSW_PROCESSED_DIR`,
`NSLKDD_MODELS_DIR`, `UNSW_MODELS_DIR`, `NSLKDD_RESULTS_DIR`, `UNSW_RESULTS_DIR`,
`NSLKDD_REPORTS_DIR`, `UNSW_REPORTS_DIR`, `QSVM_CACHE_DIR`, `TRAIN/TEST_DATA_PATHS`.
`DATA_RAW_DIR`/`DATA_PROCESSED_DIR` là alias tương thích ngược (trỏ NSL-KDD).

## Môi trường & chạy (uv)
Dự án dùng **uv** (Astral). Nguồn phụ thuộc: `pyproject.toml` + `uv.lock`.
```bash
uv sync                    # tạo .venv + cài đúng theo uv.lock
uv run python ...          # chạy trong env (không cần activate)
uv run jupyter notebook    # mở notebook
# hoặc activate: source .venv/Scripts/activate  (Windows)
```
Thêm gói: `uv add <pkg>` (tự cập nhật pyproject + lock). Cần `requirements.txt` cho pip? Sinh lại bằng `uv export --format requirements-txt > requirements.txt`.
- **Notebook** là executable chính (`notebooks/nslkdd/`, `notebooks/unsw/`) — tự chứa, sinh hình + JSON.
- **Runners** (Paper 2): `python runners/run_reliability_verify.py` (rồi recompute/temporal/figures).
- **Kernel matrix rất chậm** (hàng giờ CPU) — LUÔN kiểm `models/*/qsvm_cache/` trước khi tính lại.
- Dữ liệu thô NSL-KDD auto-download qua `gdown` khi chạy notebook (nếu đã cài gdown).

## Ràng buộc thiết kế (bất di bất dịch)
- **Zero-leakage:** mọi transformer (OHE, SelectKBest, PCA, MinMax) `fit()` CHỈ trên train, rồi `transform()` test.
- **Phần cứng:** cố định 4 feature = 4 qubit.
- **ZZFeatureMap:** `reps=2`, `entanglement='full'`.
- **Thống kê:** 5-fold stratified CV; báo cáo mean ± std; McNemar cho so sánh classifier; Cohen's d cho effect size. Tránh overclaim.

## Quy tắc ngôn ngữ & code
- **Logic code** (biến, hàm, class): **tiếng Anh**, chuẩn PEP 8.
- **Comment & docstring** trong `.py`: **tiếng Việt**.
- **Markdown cell / giải thích trong `.ipynb`**: **tiếng Việt**.
- **Mã hóa file I/O:** MỌI thao tác `open()` PHẢI có `encoding='utf-8'` (Windows mặc định cp1252 gây lỗi Unicode với tiếng Việt). Không bao giờ `open(file)` thiếu utf-8.

## Lưu ý còn tồn (residual)
- Notebook `c5`/`c6` khi chạy lại ghi JSON kết quả vào `data/nslkdd/processed_data` thay vì `results/nslkdd` (dùng chung `DATA_DIR`) — cần tách `RESULTS_DIR` khi review.
- File cá nhân (ảnh tác giả, hợp đồng có PII) đã chuyển ra ngoài repo (folder `_PRIVATE_move_out_of_repo/`, đã gitignore). Repo là **PUBLIC**.
