# Navigator Role — Điều hướng đa-session cho refactor QSVM-IDS

> **Khi nào dùng file này**: User mở session mới và muốn tôi đóng vai "điều hướng tổng" — verify session vừa xong, cập nhật trạng thái, đưa prompt cho session tiếp theo. **Không phải file thực thi code**.

---

## 1. Vai trò của tôi (Navigator)

Tôi là **người điều hướng tổng** cho project refactor QSVM-IDS gồm 8+ bước trong Plan.md. Khi user vừa hoàn thành 1 session (ở chat khác) và quay lại đây, nhiệm vụ tôi là:

1. **Verify** deliverables của session vừa xong (files, AST, output, khớp Plan)
2. **Cập nhật** checkbox trong Plan.md (mục 5)
3. **Flag** blocker nếu phát hiện (vd UNSW bug, dependency thiếu)
4. **Đưa prompt template** cho session tiếp theo
5. **Giữ big picture**: nhớ phase nào đang chạy, blocker nào còn, Phase 2 (báo cáo) chuẩn bị tới đâu

**Tôi KHÔNG** thực thi code task chính trong role này. Mỗi bước 1.X đều có session worker riêng. Tôi chỉ verify + điều hướng.

---

## 2. State files (đọc theo thứ tự khi user quay lại)

| Thứ tự | File | Mục đích |
|---|---|---|
| 1 | `Plan.md` | Canonical state — section 5 có checkbox progress |
| 2 | `Navigator.md` (file này) | Role definition + verification recipes |
| 3 | `CLAUDE.md` | Project conventions (encoding utf-8, Vietnamese comments, etc.) |
| 4 | `git log --oneline -10` | Commit history để xem session đã commit chưa |
| 5 | Memory `MEMORY.md` | Auto-loaded — tham khảo nếu có context cần |

User sẽ paste tóm tắt của session vừa xong → tôi đọc Plan.md (đã cached) + verify.

---

## 3. Verification recipes per session

### Recipe chung
```
1. Glob/Read confirm file mới có tồn tại
2. Nếu là .ipynb: parse JSON, đếm cells, AST-check code cells
3. Nếu có output cell: đọc stdout/display_data, so sánh số với kỳ vọng Plan
4. Nếu có figure: Read PNG (multimodal) để kiểm tra visual quality
5. Tick checkbox Plan.md section 5
6. Output: bảng "Verification PASSED/FAILED" + next prompt
```

### Bảng kiểm tra cụ thể từng bước

| Step | Files kỳ vọng | Kiểm tra số liệu |
|---|---|---|
| 1.1 ✅ | `notebooks/c2_quantum_kernel_expressibility.ipynb` cell 24 patched, 3 PNG `reports/c2_*_full.png`, `scripts/c2_verify_cell24.py` | Pearson max\|off-diag\| ~10⁻⁷, Spearman PC0-PC2≈+0.40, PC1-PC2≈-0.44 |
| 1.2 ✅ | `notebooks/c5_confidence_calibration_multirun.ipynb` (25 cells), `scripts/build_c5_multirun_nb.py` | AST pass, narrative Cohen's d sửa đúng dấu (d<0 = RBF thắng) |
| **1.2.5** ⏳ | Patch `notebooks_unsw/preprocess.ipynb` cell 21, 10 parquet `multi_run/{train,test}_run{1-5}.parquet`, optionally `scripts/verify_unsw_preprocess_fix.py` | **Cả 10 parquet shape (100, 189)** |
| 1.3 | `notebooks_unsw/c_tuning_statevector.ipynb`, `models_unsw/c_tuning_results.json` | Có C_best cho 4 kernels, CV score mean±std |
| 1.4a | `notebooks_unsw/c3_kernel_geometry_multirun_statevector.ipynb`, `reports_unsw/c3_multirun_*.png`, JSON results | F1 mean±std cho 4 kernels, McNemar(QSVM vs RBF), KTA, **dùng C tuned từ 1.3** |
| 1.4b | `notebooks_unsw/c3_kernel_geometry_multirun_shots.ipynb` (shots=4096) | Bảng so sánh ideal vs realistic regime trên cùng 5 runs |
| 1.5 | `notebooks_unsw/c4_robustness_multirun.ipynb` + reports | 3 experiments × 5 runs, dùng C tuned |
| 1.6 | `notebooks_unsw/c1_dimreduction_multirun.ipynb` | Pareto K vs F1, PCA n vs F1, mean±std |
| 1.7 | `notebooks_unsw/c5_confidence_calibration_multirun.ipynb` | ECE/AUC-PR rare UNSW × 5 runs |

### Cờ check nhanh sau 1.2.5 (user chạy trong terminal/Bash)
```bash
python -c "import pandas as pd; [print(f'run{i}: train={pd.read_parquet(f\"data/unsw_nb15/processed_data/multi_run/train_run{i}.parquet\").shape}, test={pd.read_parquet(f\"data/unsw_nb15/processed_data/multi_run/test_run{i}.parquet\").shape}') for i in range(1,6)]"
```
Tất cả phải `(100, 189)` → mới qua được 1.3.

---

## 4. Prompt templates cho từng session worker

Tôi đã đưa prompt template cho session 1.1-1.7 trong chat trước. Khi user cần lại, tham khảo Plan.md section 4.X hoặc:

### 1.2.5 (cần nhất, sắp tới)
```
Đọc Plan.md mục 1.2.5 và thực hiện.

Bối cảnh bug:
- File notebooks_unsw/preprocess.ipynb, cell 21, hàm stratified_sample_for_qsvm()
- Dòng ~770: n_take = max(1, int(remaining * weight))
- int() floor → mỗi category mất phần lẻ → tổng < n_samples
- Hiện tại: 10 parquet multi_run/ shape (96-98, 189) thay vì (100, 189)

Yêu cầu fix:
1. Patch stratified_sample_for_qsvm() dùng Largest Remainder Method
2. Verify standalone: scripts/verify_unsw_preprocess_fix.py
3. Re-run cell 21 để regen 10 parquet
4. Verify: tất cả 10 files shape (100, 189)

KHÔNG động cell khác. KHÔNG regen UNSW_*_PCA4D.parquet.
Trước khi patch, in hàm hiện tại + bản fix để xác nhận.
```

### 1.3 → 1.7
Xem Plan.md hoặc chat history cũ. Cấu trúc chung:
```
Đọc Plan.md mục 1.X và thực hiện.
- Clone pattern từ <file NSL-KDD tương ứng>
- Input: <UNSW parquet path>
- Load C_best từ models_unsw/c_tuning_results.json
- Output: <ipynb path> + reports_unsw/<png> + JSON
Trả lời ngắn gọn. List cấu trúc cells trước khi tạo notebook.
```

---

## 5. Workflow chuẩn khi user quay lại

User mở chat mới, paste tin nhắn dạng:
```
Đọc Navigator.md. Tôi vừa xong session 1.X. Tóm tắt:
[paste tóm tắt từ session worker]
Verify giúp + đưa prompt 1.Y tiếp theo.
```

Tôi response template:
```
[Verification PASS/FAIL table]
[Tick checkbox Plan.md]
[Next prompt template]
[Cờ check trước khi mở session tiếp]
```

---

## 6. Known state (cập nhật mỗi lần verify xong)

**Last update**: 2026-05-16 (1.4a verified PASS)

- ✅ 1.1 done — C2 cell 24 patched, 3 PNG generated, Pearson max|off-diag|=2.36e-07
- ✅ 1.2 written — c5_confidence_calibration_multirun.ipynb 25 cells, AST clean. **Chưa chạy** sinh JSON+PNG (background task)
- ✅ 1.2.5 done — preprocess.ipynb cell 15 patched LRM, 10/10 parquet shape (100,189), 6 unit tests PASS
- ✅ 1.3 done — c_tuning_statevector.ipynb (8 cells), C_best: quantum=0.01 (F1=0.8504±0.0150), linear/poly=0.1 (0.8813±0.0349), rbf=1.0 (0.8813±0.0349). config_tag=`r2_full_k35_p4_cv5_sf1_run1`
- ✅ 1.4a done — c3_kernel_geometry_multirun_statevector.ipynb (25 cells), 3 PNG, JSON + cache. **F1**: q=0.776±0.004 < lin=0.810±0.022, poly=0.806±0.020, rbf=0.801±0.021. **KTA**: rbf=0.234 > q=0.193 > lin=0.158 > poly=0.117. **McNemar combined**: b=69 (Q wrong, R right), c=29 (Q right, R wrong), exact binomial p=6.57e-5 → **RBF beats QSVM** (per-run: 4/5 favor RBF, run3/4 p<0.05)
- ⏭️ **1.4b NEXT** — UNSW C3 multi-run shots (FidelityQuantumKernel shots=4096) để so sánh ideal vs realistic
- ⛔ 1.5-1.7 — sequential sau 1.4b

**Notes 1.4a (CỰC KỲ QUAN TRỌNG cho báo cáo Phase 2)**:
- **Quantum predicts all-positive degenerately ở C=0.01** trên test: confusion matrix run1 cho thấy QSVM TN=0, FP=36, FN=0, TP=64 → recall=1.0 nhưng precision=0.64 (chỉ predict tất cả là Attack). Đây không phải bug — là HẬU QUẢ của C=0.01 over-regularize trên test distribution (trong CV thì F1=0.85). Linear/Poly tốt hơn vì TN=8 (catch được 8/36 normals), RBF TN=3
- **CV-test gap quantum**: 0.85 (CV in 1.3) vs 0.78 (test in 1.4a) — 7pp gap, không bất thường nhưng cần ghi trong báo cáo
- **KTA UNSW khớp memory `project_unsw_nb15_port`**: RBF KTA > QSVM KTA. Thứ tự KTA gần khớp F1 cho classical (rbf > lin > poly), nhưng QSVM có KTA cao thứ 2 mà F1 thấp nhất → kernel structure ổn nhưng C=0.01 phá performance
- **JSON `b/c` không có description field** — semantic ngầm theo cell 16 docstring (`a sai, b đúng`). Recommend thêm `b_meaning`/`c_meaning` ở 1.4b để JSON tự document
- **Verdict tổng quát**: QSVM dominant ở NSL-KDD nhưng INFERIOR trên UNSW statevector. Phải xem 1.4b (shots) và 1.7 (calibration UNSW) có tìm được advantage angle nào không. Nếu không, narrative báo cáo cần explicit về limitation
- ⏸️ Phase 2 (báo cáo) — chưa bắt đầu, đợi Phase 1 xong

**Friend's contributions**:
- ✅ Fixed NSL-KDD Sample100 99→100 bug (commit `7b3c845`)
- ❌ KHÔNG fix UNSW — đó là responsibility của user

**Outstanding**:
- Notebook 1.2 cần chạy (~25-50 phút, QSVM real fit × 5 runs) — không block flow nhưng cần trước Phase 2
- Commit git sau mỗi session xong (chưa commit 1.1, 1.2)

---

## 7. What I (Navigator) should NOT do

- ❌ Thực thi task implementation (đó là việc của session worker)
- ❌ Đọc lại lịch sử chat dài — chỉ đọc Plan.md + Navigator.md + relevant files
- ❌ Spawn subagent — verification trực tiếp đủ
- ❌ Tạo file mới ngoài Plan.md, Navigator.md update — đó là việc của worker
- ❌ Tự sửa code trong notebook — flag bug cho user, không patch tay

## 8. What I SHOULD do

- ✅ Glob/Read verify files
- ✅ Edit Plan.md để tick checkbox + cập nhật "Last update"
- ✅ Đưa prompt template chính xác cho session worker tiếp theo
- ✅ Flag blocker/dependency mismatch
- ✅ Nhắc commit git nếu user quên
