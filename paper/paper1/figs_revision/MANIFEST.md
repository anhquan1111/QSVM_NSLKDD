# Xuất xứ hình — bản revision paper 1

*Cập nhật 2026-09-04 (12 hình). Sinh bằng `python runners/make_paper1_figures.py` (hình có dữ liệu)
và `python runners/make_paper1_schematics.py` (hình sơ đồ).*

> ⛔ **Chỉ dùng hình trong thư mục này.** Mọi hình ở `reports/`, `data/*/processed_data/`,
> `results/*/c3_multirun/`, `results/*/c4_multirun/`, `results/*/c4_paper2/` đều là **của code
> cũ, trước revision** — số liệu đã lỗi thời. Danh sách cấm ở §3.

---

## 1. Hình đã xuất — dùng được

> **Cập nhật 2026-09-04 (cắt trang).** Bản thảo còn **9 hình**. Ba hình sơ đồ
> `fig1_zzfeaturemap_circuit`, `fig2_contribution_map`, `fig3_pipeline` **đã bỏ khỏi
> bài** để lọt 12 trang — chúng không chứa dữ liệu nào, nội dung đã có trong thân bài.
> File `.pdf` vẫn còn trên đĩa nhưng không được `\input`, và không còn trong
> `audit_figures.py` (36/36). Chín hình còn lại đã hạ chiều cao và đều chạy full width;
> caption cắt từ trung bình 142 từ xuống ~60.

| Hình | File | Dữ liệu nguồn | Trạng thái |
|---|---|---|---|
| **1** | `fig1_zzfeaturemap_circuit` | Sơ đồ mạch — vẽ tay, số CNOT đối chiếu `count_ops()` của Qiskit = 24 | ✅ **mới 2026-09-04** |
| **2** | `fig2_contribution_map` | Sơ đồ khối — nội dung cập nhật theo bản revision | ✅ **mới 2026-09-04** |
| **3** | `fig3_pipeline` | Sơ đồ khối — **đã bỏ khối Pareto**, thay bằng luật ba giai đoạn | ✅ **mới 2026-09-04** |
| **4** | `fig4_selectkbest_sweep` | `c1_revision/c1_ksweep.csv` — sinh bởi `runners/run_ksweep.py` | ✅ **chạy lại 2026-09-03** |
| **5** | `fig5_c1_dimension_selection` | `C1_revision.ipynb` block C/D/E · `u1_dimension_metrics.csv` · `u1_c1_selection_unsw.json` | ✅ thay hình Pareto cũ |
| **6** | `fig6_entanglement_ablation` | `c2_revision/c2_kta_per_run.csv` · `c2_revision/c2_per_run.csv` (10 run) | ✅ thay hình KTA cũ |
| **7** | `fig7_per_run_f1` | `c2_revision/c2_per_run.csv` (10 run × 7 model) | ✅ thay hình 5 seed cũ |
| **8** | `fig8_prior_shift` | `c3_revision/c3_prior_shift_per_run.csv` (10 run × 7 model × 3 điều kiện) | ✅ thay hình prior-shift cũ |
| **9** | `fig9_learning_curve_nslkdd` | `c4_revision/c4_per_run_{natural,matched}_refit_per_N.csv` + `c4_pairwise_statistics_*` | ✅ thay hình learning curve cũ |
| **10** | `fig10_regime_map` | `results/nslkdd/regime_map_rows.csv` (110 dòng) | ✅ thay regime map cũ |
| **12** | `fig12_width_concentration` | `variant_K80n8/*` · `c1_gram_concentration.csv` · `c1_width_sweep.csv` | ✅ **mới 2026-09-04** |
| **11** | `fig11_unsw_transfer` | `unsw/c4_revision/c4_per_run_unsw_natural_refit_per_N.csv` + pairwise | ✅ **mới** (R1 đòi dataset thứ hai) |

Mỗi hình xuất **cả `.pdf` (vector, nộp bài) và `.png` (xem nhanh)**, 400 dpi,
khổ 7.16 in = đúng chiều rộng 2 cột IEEE, `pdf.fonttype=42` để nhúng font được.

**Điểm chung của 8 hình có dữ liệu**: đều lấy từ artifact `*_revision` (10 run, tune đối xứng,
Wilcoxon ghép cặp + Holm). Không hình nào đụng dữ liệu 5-seed của bản cũ.

---

## 2. Đủ bộ 11 hình

Không còn hình nào phải lấy từ bản cũ. Ba hình sơ đồ (1, 2, 3) không phụ thuộc dữ liệu nên
được vẽ lại bằng matplotlib với cùng bộ token màu; hai chỗ nội dung **phải sửa** so với bản
đã nộp:

- **Fig 2**: cột "Protocol" của C1 ghi luật ba giai đoạn, không còn Pareto; C4 ghi hai chế độ
  lấy mẫu và hai arm tune.
- **Fig 3**: **bỏ hẳn khối "Pareto search"** — thay bằng khối `C1: three-stage selection rule`.
  Giữ khối Pareto là mâu thuẫn với chính phần lý thuyết đã sửa.

---

## 3. ⛔ Hình CẤM dùng — của code cũ

Toàn bộ các thư mục sau sinh ra **trước** bản revision, dùng 5 seed, tune bất đối xứng,
chưa có RF/XGBoost:

```
reports/nslkdd/            (≈70 hình)   c2_*, c5_*, c6_*, pca_*, zzfeaturemap_*, p2_*
reports/unsw/              (≈22 hình)   c1_*, c3_*, c4_*, c5_*, unsw_*
data/nslkdd/processed_data/             c1_fig_pareto_diagnostic.png, c1_tradeoff.png, ...
data/unsw/processed_data/               unsw_selectkbest_cv_curve.png, ...
results/nslkdd/c3_multirun/             c3_multirun_*, c3_reprun4_*
results/nslkdd/c4_multirun/figures/     c4_e1_*, c4_e2_*, c4_e3_*
results/nslkdd/c4_paper2/figures/       (thuộc paper 2, chủ đề khác)
```

**Ba cái dễ nhầm nhất** — trông giống hình bài cần nhưng là bản cũ:

| File cũ | Trông giống | Thực tế |
|---|---|---|
| `data/nslkdd/processed_data/c1_fig_pareto_diagnostic.png` | Fig 5 | Pareto cũ — **chính cái R4 chỉ ra là không lọc gì** |
| `reports/nslkdd/c6_learning_curves_test_f1.png` | Fig 9 | Learning curve cũ — chỉ tới N=1000, không có chế độ natural, không có crossover |
| `results/nslkdd/c3_revision/figures/c3_regime_map_main_full_baselines.png` | Fig 10 | Regime map **chỉ có khối C3**, không phải 110 so sánh gộp C2+C3+C4 |

Hai thư mục **được phép** dùng vì thuộc bản revision, nhưng **không phải hình của bài**
(chỉ là hình chẩn đoán nội bộ):

```
results/nslkdd/c2_revision/figures/     c2_kta.png, c2_paired_f1.png, ...
results/nslkdd/c3_revision/figures/     c3_regime_map_*.png
```

---

## 4. Cách kiểm khi ghép vào bài

```bash
# Sinh lai toan bo hinh cua bai
python runners/make_paper1_figures.py

# Doi chieu so trong hinh voi artifact
python runners/audit_c4.py
```

Trong `.tex` chỉ được trỏ tới `figs_revision/`:

```latex
\includegraphics[width=\textwidth]{figs_revision/fig9_learning_curve_nslkdd.pdf}
```

Nếu thấy bất kỳ `\includegraphics` nào trỏ ra `reports/` hay `processed_data/` thì **sai**.
