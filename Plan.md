# Plan — Sửa code QSVM-IDS theo phản hồi review

> **Ngày tạo**: 2026-05-15
> **Phản hồi từ**: review của bạn cùng đồ án
> **Phạm vi**: C2 + C5 (NSL-KDD) + toàn bộ UNSW generalization

---

## 1. Bối cảnh các vấn đề cần sửa

### 1.1. C2 mục 4.3.1 — Mâu thuẫn Hình 4.8 vs Bảng 4.8
- **Hình 4.8** (Pearson heatmap): hiển thị toàn bộ off-diagonal = `0.0000` (PCA fit trên full train, project trên full train → orthogonality tuyệt đối).
- **Bảng 4.8**: Pearson lệch khỏi 0, đặc biệt PC3–PC4 = +0.2801 (PCA fit trên full train, project trên **subset** → không còn orthogonal).
- **Mâu thuẫn**: cùng tên "Pearson 4 PCA components" nhưng số khác hẳn nhau.
- **Bản chất**: PCA orthogonality chỉ giữ trên đúng data đã fit. Subset → Pearson chỉ "xấp xỉ 0".

### 1.2. C5 — Kết quả cần xét lại
- Cohen's d = **−0.68** trên rare class: margin RBF **LỚN HƠN** QSVM → ngược với câu khẳng định "QSVM margin tighter" trong CLAUDE.md/báo cáo.
- McNemar p = 1.0 (statistical tie do n_rare = 10 quá nhỏ) → cần multi-run để có power.
- Per-group: R2L QSVM=0.6 < RBF=1.0 (RBF perfect).
- ECE_rare (QSVM=0.434 < RBF=0.471) và AUC-PR (QSVM=0.966 > RBF=0.955) vẫn ủng hộ QSVM → narrative cần xoay quanh **calibration** và **AUC-PR**, không phải margin.

### 1.3. UNSW — Generalization thiếu C tuning + thiếu multi-run
- `notebooks_unsw/c3_kernel_geometry_statevector.ipynb` dùng `SVC_C = 1.0` cố định → QSVM F1=0.75 tied với RBF p=0.75 (không thể hiện lợi thế).
- Statevector vốn để test **ideal regime** → không tune C là phí.
- Chưa có UNSW C1 standalone, C4, C5.
- Multi-run parquet đã sẵn ở `data/unsw_nb15/processed_data/multi_run/train_run{1-5}.parquet`.

### 1.4. C6 — Bỏ qua
Bạn cùng đồ án nói "tuỳ sửa cũng được không sửa cũng được" → không động đến.

---

## 2. Phase 1 — Code fixes

| # | Bước | File ảnh hưởng | Output kỳ vọng | Ưu tiên |
|---|---|---|---|---|
| **1.1** | Sửa C2 mục 4.3.1: regenerate Hình 4.8 + Bảng 4.8 trên **full X_train_pca** | `notebooks/c2_quantum_kernel_expressibility.ipynb` (cell 24) | Pearson ≈ 10⁻⁷ (≈0 thực sự), Spearman lớn, `\|ρ−r\|` ≈ \|ρ\|. PNG + bảng nhất quán | **HIGH** |
| **1.2** | Port C5 sang multi-run + sửa narrative Cohen's d | `notebooks/c5_confidence_calibration_multirun.ipynb` (mới) | mean±std cho ECE/AUC/McNemar/Cohen's d trên 5 runs. Cập nhật `c5_results.json` | **HIGH** |
| **1.2.5** | **Fix UNSW preprocess bug** (`stratified_sample_for_qsvm` truncation) + regenerate multi_run parquets | `notebooks_unsw/preprocess.ipynb` (cell ~21, hàm `stratified_sample_for_qsvm`) | 10 parquet files `multi_run/{train,test}_run{1-5}.parquet` đều có shape (100, 189) | **CRITICAL BLOCKER** cho 1.3-1.7 |
| **1.3** | Tạo C tuning notebook cho UNSW (StratifiedKFold CV, clone pattern từ `c3_c_tuning_statevector.ipynb`) | `notebooks_unsw/c_tuning_statevector.ipynb` (mới) | C_best cho `quantum`, `linear`, `poly`, `rbf` — cache `models_unsw/c_tuning_results.json` | **HIGH** (foundation cho 1.4, 1.5) |
| **1.4a** | UNSW C3 multi-run + C tuned (**statevector / ideal**) | `notebooks_unsw/c3_kernel_geometry_multirun_statevector.ipynb` (mới) | 5 runs × 4 kernels với C đã tune, F1 mean±std, McNemar, KTA | **HIGH** |
| **1.4b** | UNSW C3 multi-run + C tuned (**shots / realistic**) — FidelityQuantumKernel shots=4096 | `notebooks_unsw/c3_kernel_geometry_multirun_shots.ipynb` (mới) | So sánh ideal vs realistic regime | **MEDIUM** |
| **1.5** | UNSW C4 multi-run (robustness) — clone từ `c4_robustness_distribution_shift_multirun_fixed.ipynb` | `notebooks_unsw/c4_robustness_multirun.ipynb` (mới) | 3 experiments (temporal/perturbation/prior) × 5 runs × C tuned | **HIGH** |
| **1.6** | UNSW C1 standalone (K-sweep + PCA n-sweep, 5 runs) | `notebooks_unsw/c1_dimreduction_multirun.ipynb` (mới) | Pareto K vs F1 và n vs F1 với mean±std | **MEDIUM** |
| **1.7** | (Optional) UNSW C5 calibration multi-run | `notebooks_unsw/c5_confidence_calibration_multirun.ipynb` (mới) | ECE/AUC-PR rare cho UNSW với 5 runs | **LOW** |

**Thứ tự thực hiện đề xuất**: 1.1 → 1.2 → **1.2.5** → 1.3 → 1.4a → 1.5 → 1.4b → 1.6 → 1.7

**Tổng thời gian ước tính**: 6–10 giờ làm việc liên tục, chia 2–3 buổi.

---

## 3. Phase 2 — Hoàn thiện báo cáo

| # | Bước |
|---|---|
| 2.1 | Upload báo cáo (.docx/.pdf) — đọc cấu trúc + đối chiếu với code mới |
| 2.2 | Cập nhật số liệu/bảng/hình bị ảnh hưởng (4.3.1, C5 results, UNSW section) |
| 2.3 | Viết lại narrative chỗ Cohen's d C5 + chỗ "Pearson = 0" mục 4.3.1 |
| 2.4 | Thêm section UNSW với "2 góc nhìn" (ideal/realistic) — diễn giải lợi thế lượng tử |
| 2.5 | Review cuối: tính nhất quán text–bảng–hình–reference |

---

## 4. Mẹo tối ưu token khi chạy plan

### 4.1. Cấu trúc session
- **Mỗi bước trong Phase 1 → 1 session mới**. Đừng làm 1.1 → 1.2 → 1.3 trong cùng 1 chat dài. Sau mỗi bước xong, `/clear` rồi mở session mới cho bước tiếp theo.
- **Bắt đầu session mới ngắn gọn**: chỉ cần "đọc Plan.md, thực hiện bước 1.X". Tôi sẽ đọc Plan.md (cached) thay vì phải đọc lại lịch sử dài.

### 4.2. Cách hỏi
- **Cụ thể hơn = ít token hơn**. Thay vì "sửa C2", nói "thực hiện bước 1.1 trong Plan.md, sửa cell 24 của c2_quantum_kernel_expressibility.ipynb".
- **Tránh exploratory questions**: không hỏi "tình hình thế nào", "đánh giá xem" — đi thẳng vào hành động.
- **Bảo tôi trả lời ngắn**: thêm câu "trả lời ngắn gọn, chỉ code + 1 dòng giải thích" giảm output tokens.

### 4.3. Tận dụng cache
- Prompt caching của Claude Code lưu context 5 phút. Đặt câu hỏi liên tiếp tận dụng cache; tránh để idle 5+ phút giữa câu hỏi liên quan.
- File đã đọc 1 lần trong session → đọc lại lần 2 chỉ tính ~10% giá.

### 4.4. Quản lý conversation
- Dùng `/compact` khi conversation > 50 turn để nén lịch sử.
- Dùng `/clear` khi muốn reset hoàn toàn (không khôi phục được).
- Tránh để tôi đọc lại file vừa edit để "verify" — Edit tool đã báo lỗi nếu fail rồi.

### 4.5. Subagents khi cần search rộng
- Nếu cần search trên nhiều file (vd tìm tất cả notebook dùng `c5_results.json`), bảo tôi "dùng Explore agent" — kết quả search không vào main context, tiết kiệm đáng kể.
- Chỉ dùng subagent khi search rộng (>3 query), không dùng cho việc đơn giản.

### 4.6. Phase 2 (báo cáo Word)
- File Word dài tốn nhiều token đọc. **Copy-paste từng section** vào chat thay vì attach nguyên file:
  - Section 4.3.1 (C2) → 1 session
  - Section C5 → 1 session
  - Section UNSW → 1 session
- Hoặc convert sang `.md` trước rồi gửi (Word có lots of formatting noise).

### 4.7. Backup quan trọng
- **Commit git sau mỗi bước**: code mới nếu lỗi vẫn có thể revert. Đỡ phải nhờ tôi sửa lại từ đầu (tốn token).

---

## 5. Theo dõi tiến độ

Mỗi khi hoàn thành 1 bước, cập nhật ô tương ứng:

- [x] 1.1 — C2 mục 4.3.1 (Pearson trên full train)
- [x] 1.2 — C5 multi-run + narrative Cohen's d (đã viết notebook, chờ chạy sinh PNG/JSON)
- [x] 1.2.5 — Fix UNSW preprocess bug + regen multi_run parquets (LRM, 10/10 parquet (100,189))
- [ ] 1.3 — UNSW C tuning notebook
- [ ] 1.4a — UNSW C3 multi-run statevector
- [ ] 1.4b — UNSW C3 multi-run shots
- [ ] 1.5 — UNSW C4 multi-run
- [ ] 1.6 — UNSW C1 multi-run (optional)
- [ ] 1.7 — UNSW C5 multi-run (optional)
- [ ] 2.1–2.5 — Hoàn thiện báo cáo (sau khi Phase 1 xong)
