"""Patch notebooks_unsw/c3_kernel_geometry_multirun_statevector_C1.ipynb (1.4a-redo).

Workflow Buoc B:
- Doi C tuned tu 1.3 -> C=1.0 neutral cho tat ca 4 kernel
- Doi RESULTS_JSON va PNG paths -> suffix _C1
- Add strict cache-hit assertion (KHONG re-compute quantum)
- Add KTA cache-reuse sanity check (KTA moi == KTA 1.4a goc)
- Add b_meaning/c_meaning vao McNemar payload
- Add side-by-side comparison cell (1.4a tuned vs C=1.0)
- Update metadata: C_strategy, cache_reused_from, compared_against, rationale
"""
import json
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

NB_PATH = 'notebooks_unsw/c3_kernel_geometry_multirun_statevector_C1.ipynb'


def code_cell(src: str) -> dict:
    return {
        'cell_type': 'code',
        'execution_count': None,
        'metadata': {},
        'outputs': [],
        'source': src.splitlines(keepends=True),
    }


def md_cell(src: str) -> dict:
    return {
        'cell_type': 'markdown',
        'metadata': {},
        'source': src.splitlines(keepends=True),
    }


def set_src(cell: dict, src: str) -> None:
    cell['source'] = src.splitlines(keepends=True)
    if cell['cell_type'] == 'code':
        cell['outputs'] = []
        cell['execution_count'] = None


with open(NB_PATH, encoding='utf-8') as f:
    nb = json.load(f)

cells = nb['cells']
assert len(cells) == 25, f'Expected 25 cells in cloned notebook, got {len(cells)}'

# ── Cell 0: Markdown intro — đổi tiêu đề + thêm rationale ───────────
set_src(cells[0], """# UNSW-NB15 — C3 Kernel Geometry Multi-Run Statevector (C=1.0 NEUTRAL re-run)

**Mục tiêu (1.4a-redo):** Re-run 1.4a với `C=1.0` cho TẤT CẢ 4 kernel (neutral, KHÔNG tune) để có số liệu "có ý nghĩa" cho báo cáo.

**Lý do re-run:** Notebook 1.6 (`c1_dimreduction_multirun.ipynb`) phát hiện C=0.01 (tuned trong 1.3 qua CV f1 trên imbalanced fold) làm QSVM **degenerate** (predict-all-attack: TN=0, recall=1.0 nhưng precision=0.64) trên test set của 1.4a gốc. Với `C=1.0` fixed, QSVM thoát degeneracy 0/5 runs ở mọi K, F1 plateau ~0.811 (K≥80) — competitive linear.

**Cache reuse (CỐT LÕI):** Kernel matrices KHÔNG phụ thuộc C, chỉ `SVC.fit` thay đổi. Notebook này REUSE 100% cache `models_unsw/qsvm_cache/multirun/run_{i}/` từ 1.4a. KHÔNG re-compute quantum kernel. **KTA mới phải khớp 1.4a gốc** (kernel matrix giống nhau → sanity check cache reuse).

**Kernels so sánh:** `quantum` (ZZFeatureMap reps=2 entanglement='full') · `linear` · `poly (degree=2)` · `rbf (gamma='scale')` — **tất cả C=1.0**.

**Output mới (KHÔNG ghi đè 1.4a):**
- `models_unsw/c3_results_statevector_C1.json`
- `reports_unsw/c3_multirun_statevector_C1_{f1_boxplot,kta_bar,confmat}.png`
""")

# ── Cell 3: Constants — thêm RESULTS_JSON_OLD, đổi RESULTS_JSON, thêm C_STRATEGY ──
set_src(cells[3], """# ── Hằng số toàn cục ───────────────────────────────────────────────
RANDOM_STATE = 42
RUN_IDS      = [1, 2, 3, 4, 5]

# Pipeline (khớp 1.3 và 1.4a gốc — để cache khớp file name)
N_QUBITS     = 4
K_SELECT     = 35
PCA_N        = 4
ANGLE_MAX    = np.pi

# Quantum kernel
ZZ_REPS      = 2
ZZ_ENT       = 'full'

# Classical kernel params (khớp SVC defaults dùng trong c_tuning)
POLY_DEGREE  = 2
RBF_GAMMA    = 'scale'

# Cột target & loại bỏ khỏi features
TARGET_COL   = 'label_binary'
LABEL_COLS   = ['label_binary', 'label_multiclass', 'attack_category']

# Đường dẫn (relative tới notebooks_unsw/ — notebook chạy ở thư mục đó)
DATA_DIR         = '../data/unsw_nb15/processed_data/multi_run'
MODELS_DIR       = '../models_unsw'
CACHE_DIR        = f'{MODELS_DIR}/qsvm_cache/multirun'
REPORTS_DIR      = '../reports_unsw'
C_TUNING_JSON    = f'{MODELS_DIR}/c_tuning_results.json'      # CHỈ load để so sánh, KHÔNG dùng C_best
RESULTS_JSON_OLD = f'{MODELS_DIR}/c3_results_statevector.json'   # 1.4a gốc — để compare KTA + table
RESULTS_JSON     = f'{MODELS_DIR}/c3_results_statevector_C1.json' # output mới của 1.4a-redo

CONFIG_TAG       = 'r2_full_k35_p4_cv5_sf1_run1'    # PHẢI khớp 1.4a để cache hit
C_STRATEGY       = 'neutral_C1_no_retune'           # đánh dấu phân biệt với 1.4a (C_tuned_from_1.3)

KERNEL_NAMES  = ['quantum', 'linear', 'poly', 'rbf']
COLORS        = {'quantum': '#1565C0', 'linear': '#E53935',
                 'poly':    '#43A047', 'rbf':    '#8E24AA'}
DISPLAY_NAMES = {'quantum': 'QSVM\\n(ZZFeatureMap)',
                 'linear':  'SVM-Linear',
                 'poly':    f'SVM-Poly\\n(deg={POLY_DEGREE})',
                 'rbf':     'SVM-RBF\\n(gamma=scale)'}

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
np.random.seed(RANDOM_STATE)

print(f'CONFIG_TAG : {CONFIG_TAG}')
print(f'C_STRATEGY : {C_STRATEGY}')
print(f'CACHE_DIR  : {CACHE_DIR}  (REUSE từ 1.4a)')
print(f'RUN_IDS    : {RUN_IDS}')
""")

# ── Cell 4: Markdown — đổi heading "Load C tuned" → "Set C=1.0 neutral" ──
set_src(cells[4], """## 2. Set C=1.0 NEUTRAL (KHÔNG tune) + load 1.4a gốc để compare

Khác 1.4a gốc: KHÔNG load `C_best` từ `c_tuning_results.json`. Set `C=1.0` cho TẤT CẢ 4 kernel để loại bỏ artifact tuning (1.6 đã chứng minh C=0.01 → QSVM degenerate).

Đồng thời load JSON kết quả 1.4a gốc để dùng cho:
- Sanity check KTA (kernel matrix giống nhau → KTA mới == KTA 1.4a)
- Bảng so sánh side-by-side cuối notebook
""")

# ── Cell 5: Replace load-C-tuned with hardcoded C=1.0 + load OLD JSON ──
set_src(cells[5], """# ── KHÔNG load C_best — set C=1.0 neutral cho 4 kernel ─────────
C_BY_KERNEL = {k: 1.0 for k in KERNEL_NAMES}

print(f'=== C NEUTRAL (strategy = {C_STRATEGY}) ===')
for k in KERNEL_NAMES:
    print(f'  {k:>8s}: C={C_BY_KERNEL[k]:.4f}')

# Load 1.4a gốc để compare (KTA sanity + side-by-side table)
with open(RESULTS_JSON_OLD, 'r', encoding='utf-8') as f:
    old_results = json.load(f)
print(f'\\n[OK] Loaded 1.4a gốc: {RESULTS_JSON_OLD}')
print(f'  Old C_tuned_from = {old_results["metadata"].get("C_tuned_from", "?")}')
print(f'  Old config_tag   = {old_results["metadata"].get("config_tag", "?")}')

# Cross-check config_tag để đảm bảo cache đã compute với cùng pipeline (k35/pca4/...)
assert old_results['metadata']['config_tag'] == CONFIG_TAG, \\
    f'CONFIG_TAG mismatch: notebook={CONFIG_TAG}, 1.4a_old={old_results["metadata"]["config_tag"]} → cache có thể không hit'
print('  [OK] CONFIG_TAG khớp 1.4a — cache sẽ hit')

# Sanity: in C cũ của 1.4a để contrast
print('\\n=== C cũ trong 1.4a gốc (tuned từ 1.3) — để contrast ===')
for k in KERNEL_NAMES:
    c_old = old_results['summary'][k]['C']
    print(f'  {k:>8s}: C_old={c_old:<6g}  →  C_new={C_BY_KERNEL[k]:.4f}')
""")

# ── Cell 8: Quantum kernel helper — STRICT cache hit (no re-compute) ──
set_src(cells[8], """# Quantum kernel cache helper — STRICT cache-hit (1.4a-redo: KHÔNG re-compute quantum)
def get_quantum_kernel_train_test(X_train, X_test, run_id):
    \"\"\"Load K_train_train + K_test_train từ cache 1.4a.
    FAIL LOUDLY nếu cache miss (contract: 1.4a-redo phải reuse 100%).
    \"\"\"
    run_cache = f'{CACHE_DIR}/run_{run_id}'
    p_tr = f'{run_cache}/K_quantum_train_train_{CONFIG_TAG}.npy'
    p_te = f'{run_cache}/K_quantum_test_train_{CONFIG_TAG}.npy'

    if not (os.path.exists(p_tr) and os.path.exists(p_te)):
        raise FileNotFoundError(
            f'[CACHE MISS] run_{run_id}: cần cả 2 file:\\n  {p_tr}\\n  {p_te}\\n'
            f'1.4a-redo PHẢI reuse cache 1.4a. KHÔNG re-compute quantum. '
            f'Kiểm tra models_unsw/qsvm_cache/multirun/run_{run_id}/'
        )

    K_tr = np.load(p_tr)
    K_te = np.load(p_te)
    print(f'    [CACHE HIT] quantum K (run {run_id})  '
          f'K_tr.shape={K_tr.shape}, K_te.shape={K_te.shape}')
    return K_tr, K_te

def get_classical_kernel_train_test(X_train, X_test, kernel_name):
    \"\"\"Tính kernel matrix linear/poly/rbf khớp SVC defaults (gamma='scale', coef0=0).\"\"\"
    if kernel_name == 'linear':
        K_tr = X_train @ X_train.T
        K_te = X_test  @ X_train.T
        return K_tr, K_te

    n_features = X_train.shape[1]
    var_X = X_train.var()
    gamma_scale = 1.0 / (n_features * var_X) if var_X > 0 else 1.0 / n_features

    if kernel_name == 'poly':
        # SVC poly: (gamma * <x,y> + coef0)^degree, coef0=0
        K_tr = (gamma_scale * (X_train @ X_train.T)) ** POLY_DEGREE
        K_te = (gamma_scale * (X_test  @ X_train.T)) ** POLY_DEGREE
        return K_tr, K_te

    if kernel_name == 'rbf':
        # K(x,y) = exp(-gamma * ||x-y||^2)
        sq_tr = np.sum(X_train**2, axis=1)
        D_tr  = sq_tr[:, None] + sq_tr[None, :] - 2 * (X_train @ X_train.T)
        D_te  = np.sum(X_test**2, axis=1)[:, None] + sq_tr[None, :] - 2 * (X_test @ X_train.T)
        K_tr  = np.exp(-gamma_scale * np.maximum(D_tr, 0))
        K_te  = np.exp(-gamma_scale * np.maximum(D_te, 0))
        return K_tr, K_te

    raise ValueError(f'Unknown classical kernel: {kernel_name}')
""")

# ── Cell 16: McNemar — thêm b_meaning/c_meaning vào per_run dict ──
set_src(cells[16], """def mcnemar_exact(y_true, y_pred_a, y_pred_b):
    \"\"\"McNemar exact binomial 2-sided. Trả về (b, c, p_value).
    Quy ước (khớp 1.4a):
      - b = số mẫu A sai, B đúng
      - c = số mẫu A đúng, B sai
    Ở đây A = QSVM, B = RBF nên: b lớn → RBF lợi thế hơn.
    \"\"\"
    a_correct = (y_pred_a == y_true)
    b_correct = (y_pred_b == y_true)
    b = int(np.sum((~a_correct) & b_correct))   # A=Q sai, B=R đúng
    c = int(np.sum(a_correct & (~b_correct)))   # A=Q đúng, B=R sai
    n = b + c
    if n == 0:
        return b, c, 1.0
    p = float(binomtest(min(b, c), n=n, p=0.5).pvalue)
    return b, c, p

# Quy ước semantic cho JSON (fix gap của 1.4a)
B_MEANING = 'QSVM wrong, RBF right'
C_MEANING = 'QSVM right, RBF wrong'

mcnemar_per_run = []
total_b, total_c = 0, 0
for rid, res in all_results.items():
    y_true = np.array(res['y_test'])
    y_q    = np.array(res['per_kernel']['quantum']['y_pred'])
    y_r    = np.array(res['per_kernel']['rbf']['y_pred'])
    b, c, p = mcnemar_exact(y_true, y_q, y_r)
    total_b += b
    total_c += c
    mcnemar_per_run.append({
        'run':       rid,
        'b':         b,
        'c':         c,
        'p_value':   p,
        'b_meaning': B_MEANING,
        'c_meaning': C_MEANING,
    })
    print(f'  run_{rid}: b={b:>3d} ({B_MEANING}), c={c:>3d} ({C_MEANING}), p={p:.4f}')

# Combined: pool b, c rồi exact binomial
n_total = total_b + total_c
if n_total > 0:
    p_combined = float(binomtest(min(total_b, total_c), n=n_total, p=0.5).pvalue)
else:
    p_combined = 1.0
print(f'\\n=== McNemar COMBINED (pooled b={total_b}, c={total_c}) ===')
print(f'  p_value (exact binomial 2-sided) = {p_combined:.6g}')
print(f'  Median per-run p_value           = {np.median([r["p_value"] for r in mcnemar_per_run]):.4f}')

if p_combined < 0.05:
    rbf_f1 = agg.loc["rbf", "f1_mean"]; q_f1 = agg.loc["quantum", "f1_mean"]
    if q_f1 > rbf_f1:
        print('  → QSVM TỐT HƠN RBF có ý nghĩa thống kê (p<0.05)')
    else:
        print('  → RBF TỐT HƠN QSVM có ý nghĩa thống kê (p<0.05)')
else:
    print('  → KHÔNG có khác biệt thống kê QSVM vs RBF (p>=0.05)')
""")

# ── Cell 18: Figure 1 boxplot — đổi path + title ──
set_src(cells[18], """# ── Figure 1: F1 boxplot 4 kernels ────────────────────────────────
fig1, ax1 = plt.subplots(figsize=(10, 6))
data_box = [per_run_df[per_run_df["kernel"]==k]["f1"].values for k in KERNEL_NAMES]
bp = ax1.boxplot(data_box, labels=[DISPLAY_NAMES[k] for k in KERNEL_NAMES],
                 patch_artist=True, widths=0.55, showmeans=True,
                 meanprops=dict(marker="D", markerfacecolor="white",
                                markeredgecolor="black", markersize=7))
for patch, k in zip(bp["boxes"], KERNEL_NAMES):
    patch.set_facecolor(COLORS[k]); patch.set_alpha(0.65)
# Scatter raw points
for i, k in enumerate(KERNEL_NAMES):
    ys = per_run_df[per_run_df["kernel"]==k]["f1"].values
    xs = np.random.normal(i+1, 0.05, size=len(ys))
    ax1.scatter(xs, ys, color=COLORS[k], edgecolor="black", s=40, zorder=3, alpha=0.85)
# Annotate mean±std
for i, k in enumerate(KERNEL_NAMES):
    m = agg.loc[k, "f1_mean"]; s = agg.loc[k, "f1_std"]
    ax1.text(i+1, ax1.get_ylim()[1]*0.98 if i==0 else m+s+0.01,
             f"{m:.3f}±{s:.3f}", ha="center", fontsize=9, fontweight="bold")
ax1.set_ylabel("F1 (binary)", fontsize=11)
ax1.set_title(f"Figure 1: F1 binary — 5 runs × 4 kernels (UNSW-NB15, statevector)\\n"
              f"CONFIG_TAG={CONFIG_TAG} | C=1.0 NEUTRAL (strategy={C_STRATEGY})",
              fontsize=11, fontweight="bold")
ax1.grid(axis="y", alpha=0.3)
plt.tight_layout()
fig1_path = f"{REPORTS_DIR}/c3_multirun_statevector_C1_f1_boxplot.png"
fig1.savefig(fig1_path, dpi=150, bbox_inches="tight")
plt.close(fig1)
print(f"[SAVED] {fig1_path}")
display(Image(fig1_path))
""")

# ── Cell 19: Figure 2 KTA — đổi path + title (KTA phải giống 1.4a) ──
set_src(cells[19], """# ── Figure 2: KTA bar chart mean±std ──────────────────────────────
# Lưu ý: KTA chỉ phụ thuộc kernel matrix + labels (không phụ thuộc C) → KTA mới phải khớp 1.4a gốc
fig2, ax2 = plt.subplots(figsize=(10, 6))
means = [agg.loc[k, "kta_mean"] for k in KERNEL_NAMES]
stds  = [agg.loc[k, "kta_std"]  for k in KERNEL_NAMES]
xpos  = np.arange(len(KERNEL_NAMES))
bars  = ax2.bar(xpos, means, yerr=stds, color=[COLORS[k] for k in KERNEL_NAMES],
                capsize=8, edgecolor="black", linewidth=1.2, alpha=0.85)
for i, (m, s) in enumerate(zip(means, stds)):
    ax2.text(i, m + s + 0.005, f"{m:.4f}\\n±{s:.4f}",
             ha="center", fontsize=9, fontweight="bold")
ax2.set_xticks(xpos)
ax2.set_xticklabels([DISPLAY_NAMES[k] for k in KERNEL_NAMES])
ax2.set_ylabel("KTA (Kernel Target Alignment)", fontsize=11)
ax2.set_title(f"Figure 2: KTA mean±std — 5 runs × 4 kernels (C=1.0 neutral)\\n"
              f"KTA chỉ phụ thuộc kernel matrix → giống 1.4a gốc (sanity cache reuse)",
              fontsize=11, fontweight="bold")
ax2.grid(axis="y", alpha=0.3)
ax2.set_ylim(bottom=0)
plt.tight_layout()
fig2_path = f"{REPORTS_DIR}/c3_multirun_statevector_C1_kta_bar.png"
fig2.savefig(fig2_path, dpi=150, bbox_inches="tight")
plt.close(fig2)
print(f"[SAVED] {fig2_path}")
display(Image(fig2_path))
""")

# ── Cell 20: Figure 3 confmat — đổi path + title ──
set_src(cells[20], """# ── Figure 3: Confusion matrices 4 kernels (representative run = F1 QSVM cao nhất) ──
q_f1_per_run = {rid: r["per_kernel"]["quantum"]["f1"] for rid, r in all_results.items()}
rep_run = max(q_f1_per_run, key=q_f1_per_run.get)
print(f"Representative run = run_{rep_run} (QSVM F1={q_f1_per_run[rep_run]:.4f})")

fig3, axes3 = plt.subplots(1, 4, figsize=(18, 5))
fig3.suptitle(f"Figure 3: Confusion Matrices — Representative run_{rep_run} (UNSW-NB15, C=1.0 neutral)\\n"
              f"Test size = {len(all_results[rep_run]['y_test'])}", fontsize=12, fontweight="bold")
for ax, k in zip(axes3, KERNEL_NAMES):
    cm = np.array(all_results[rep_run]["per_kernel"][k]["cm"])
    f1 = all_results[rep_run]["per_kernel"][k]["f1"]
    im = ax.imshow(cm, cmap="Blues", vmin=0)
    for (i, j), v in np.ndenumerate(cm):
        ax.text(j, i, str(v), ha="center", va="center", fontsize=14,
                color="white" if v > cm.max()*0.55 else "black", fontweight="bold")
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(["Normal", "Attack"]); ax.set_yticklabels(["Normal", "Attack"])
    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    ax.set_title(f"{DISPLAY_NAMES[k]}\\nF1={f1:.4f}", fontsize=10, fontweight="bold")
plt.tight_layout()
fig3_path = f"{REPORTS_DIR}/c3_multirun_statevector_C1_confmat.png"
fig3.savefig(fig3_path, dpi=150, bbox_inches="tight")
plt.close(fig3)
print(f"[SAVED] {fig3_path}")
display(Image(fig3_path))
""")

# ── Cell 22: JSON save — update metadata cho 1.4a-redo + new PNG paths + b_meaning ──
set_src(cells[22], """import datetime

per_run_payload = []
for rid in RUN_IDS:
    res = all_results[rid]
    entry = {"run": rid}
    for k in KERNEL_NAMES:
        m = res["per_kernel"][k]
        entry[k] = {
            "f1":        m["f1"],
            "precision": m["precision"],
            "recall":    m["recall"],
            "accuracy":  m["accuracy"],
            "kta":       m["kta"],
            "n_sv":      m["n_sv"],
            "C":         m["C"],
        }
    per_run_payload.append(entry)

summary_payload = {}
for k in KERNEL_NAMES:
    summary_payload[k] = {
        "f1_mean":       float(agg.loc[k, "f1_mean"]),
        "f1_std":        float(agg.loc[k, "f1_std"]),
        "precision_mean":float(agg.loc[k, "precision_mean"]),
        "precision_std": float(agg.loc[k, "precision_std"]),
        "recall_mean":   float(agg.loc[k, "recall_mean"]),
        "recall_std":    float(agg.loc[k, "recall_std"]),
        "accuracy_mean": float(agg.loc[k, "accuracy_mean"]),
        "accuracy_std":  float(agg.loc[k, "accuracy_std"]),
        "kta_mean":      float(agg.loc[k, "kta_mean"]),
        "kta_std":       float(agg.loc[k, "kta_std"]),
        "n_sv_mean":     float(agg.loc[k, "n_sv_mean"]),
        "n_sv_std":      float(agg.loc[k, "n_sv_std"]),
        "C":             float(C_BY_KERNEL[k]),
    }

mcnemar_payload = {
    "per_run":         mcnemar_per_run,
    "combined_b":      total_b,
    "combined_c":      total_c,
    "combined_n":      total_b + total_c,
    "p_value":         p_combined,
    "median_p_value":  float(np.median([r["p_value"] for r in mcnemar_per_run])),
    "test":            "exact_binomial_2sided",
    "comparison":      "QSVM vs RBF",
    "b_meaning":       B_MEANING,
    "c_meaning":       C_MEANING,
}

metadata_payload = {
    "regime":             "statevector",
    "backend":            "FidelityStatevectorKernel",
    "n_runs":             len(RUN_IDS),
    "C_strategy":         C_STRATEGY,
    "C_by_kernel":        {k: float(C_BY_KERNEL[k]) for k in KERNEL_NAMES},
    "compared_against":   RESULTS_JSON_OLD,
    "cache_reused_from":  CACHE_DIR,
    "rationale":          (
        "1.6 (c1_dimreduction_multirun) found C=0.01 (tuned via CV f1 on imbalanced fold in 1.3) "
        "caused QSVM degeneracy (predict-all-attack: TN=0, recall=1.0 but precision=0.64) on test "
        "set of 1.4a. C=1.0 neutral chosen to surface non-degenerate QSVM performance — "
        "quantum kernel matrices reused 100% from 1.4a cache (kernel does not depend on C, only "
        "SVC.fit changes). KTA must equal 1.4a values (sanity check for cache reuse)."
    ),
    "config_tag":         CONFIG_TAG,
    "n_qubits":           N_QUBITS,
    "k_select":           K_SELECT,
    "pca_n":              PCA_N,
    "zz_reps":            ZZ_REPS,
    "zz_entanglement":    ZZ_ENT,
    "poly_degree":        POLY_DEGREE,
    "rbf_gamma":          RBF_GAMMA,
    "random_state":       RANDOM_STATE,
    "date":               datetime.date.today().isoformat(),
    "data_dir":           DATA_DIR,
    "reports":            [
        f"{REPORTS_DIR}/c3_multirun_statevector_C1_f1_boxplot.png",
        f"{REPORTS_DIR}/c3_multirun_statevector_C1_kta_bar.png",
        f"{REPORTS_DIR}/c3_multirun_statevector_C1_confmat.png",
    ],
}

final_payload = {
    "per_run":             per_run_payload,
    "summary":             summary_payload,
    "mcnemar_qsvm_vs_rbf": mcnemar_payload,
    "metadata":            metadata_payload,
}

with open(RESULTS_JSON, "w", encoding="utf-8") as fp:
    json.dump(final_payload, fp, indent=2, ensure_ascii=False)
print(f"[SAVED] {RESULTS_JSON}")
print(f"  per_run    : {len(per_run_payload)} runs × {len(KERNEL_NAMES)} kernels")
print(f"  summary    : {list(summary_payload.keys())}")
print(f"  mcnemar    : combined_n={mcnemar_payload['combined_n']}, p={mcnemar_payload['p_value']:.4g}")
""")

# ── Cell 24: Summary header — update strategy label ──
set_src(cells[24], """print('=' * 80)
print('  UNSW-NB15 — C3 KERNEL GEOMETRY MULTI-RUN STATEVECTOR (1.4a-REDO, C=1.0 NEUTRAL)')
print('=' * 80)
print(f'  CONFIG_TAG   : {CONFIG_TAG}')
print(f'  C_STRATEGY   : {C_STRATEGY}')
print(f'  Compared vs  : {RESULTS_JSON_OLD}  (1.4a gốc, C tuned)')
print(f'  Regime       : statevector (noiseless), FidelityStatevectorKernel')
print(f'  Cache reuse  : 100% từ {CACHE_DIR}')
print()
print(f'  {"Kernel":>10}  {"C":>6}  {"F1 mean±std":>16}  {"Acc mean±std":>16}  {"KTA mean±std":>16}  {"nSV mean":>9}')
print('  ' + '-' * 86)
for k in KERNEL_NAMES:
    s = summary_payload[k]
    print(f'  {k:>10}  {s["C"]:>6g}  '
          f'{s["f1_mean"]:.4f}±{s["f1_std"]:.4f}    '
          f'{s["accuracy_mean"]:.4f}±{s["accuracy_std"]:.4f}    '
          f'{s["kta_mean"]:.4f}±{s["kta_std"]:.4f}    '
          f'{s["n_sv_mean"]:>6.1f}')

# Verdict
q = summary_payload['quantum']; r = summary_payload['rbf']; lin = summary_payload['linear']
gap_f1_qr  = q['f1_mean']  - r['f1_mean']
gap_f1_ql  = q['f1_mean']  - lin['f1_mean']
gap_kta_qr = q['kta_mean'] - r['kta_mean']
print()
print(f'  QSVM vs RBF    gap: ΔF1={gap_f1_qr:+.4f}  ΔKTA={gap_kta_qr:+.4f}')
print(f'  QSVM vs Linear gap: ΔF1={gap_f1_ql:+.4f}')
print(f'  McNemar QSVM vs RBF combined p-value: {p_combined:.6g}  '
      f'({"khác biệt" if p_combined < 0.05 else "không khác biệt"} thống kê)')
print('=' * 80)
""")

# ── Insert new cells: KTA cache-reuse assertion + side-by-side comparison ──
# Insert before final summary (cell 24).
kta_assert_md = md_cell("""## 11. Sanity check: KTA cache-reuse (KTA mới == KTA 1.4a gốc)

Kernel matrix không phụ thuộc C → KTA (chỉ phụ thuộc K_train_train + y_train) phải khớp 1.4a gốc đến nhiều chữ số. Nếu lệch > 1e-6 → cache mismatch bug.
""")

kta_assert_code = code_cell("""# Sanity assertion: KTA mới phải bằng KTA 1.4a gốc (tolerance 1e-6)
print('=== KTA cache-reuse sanity check ===')
print(f'  {"Kernel":>10}  {"KTA_new (1.4a-redo)":>22}  {"KTA_old (1.4a)":>20}  {"|delta|":>12}  Status')
print('  ' + '-' * 80)
max_delta = 0.0
for k in KERNEL_NAMES:
    kta_new = float(agg.loc[k, 'kta_mean'])
    kta_old = float(old_results['summary'][k]['kta_mean'])
    delta = abs(kta_new - kta_old)
    max_delta = max(max_delta, delta)
    status = 'OK' if delta < 1e-6 else 'FAIL'
    print(f'  {k:>10}  {kta_new:>22.10f}  {kta_old:>20.10f}  {delta:>12.2e}  {status}')

assert max_delta < 1e-6, (
    f'KTA mismatch (max |delta|={max_delta:.4e} > 1e-6) → cache reuse bug. '
    f'Kernel matrix mới khác 1.4a gốc — KHÔNG được phép xảy ra vì cache files giống nhau.'
)
print(f'\\n[OK] KTA cache-reuse verified — max |delta|={max_delta:.2e} < 1e-6 cho cả 4 kernel.')
""")

comparison_md = md_cell("""## 12. Bảng so sánh side-by-side: 1.4a tuned vs 1.4a-redo C=1.0

So sánh trực tiếp F1 và TN mean (Normal đúng) giữa hai strategy. TN tăng từ ~0 → > 0 chứng minh QSVM đã thoát degeneracy.
""")

comparison_code = code_cell("""# ── Bảng side-by-side: F1 mean±std + TN mean (mean của cm[0][0] trên 5 runs) ──
def tn_mean(results_dict, kernel):
    \"\"\"Trung bình TN (cm[0][0]) qua 5 runs cho 1 kernel — chỉ ra QSVM thoát degeneracy hay không.\"\"\"
    tns = []
    if isinstance(results_dict, dict) and 'per_run' in results_dict and isinstance(results_dict['per_run'], list):
        # JSON layout (1.4a old hoặc new sau khi load)
        for entry in results_dict['per_run']:
            # Trong JSON KHÔNG có cm — phải tính lại từ y_test + y_pred. Nhưng JSON KHÔNG lưu y_test/y_pred.
            # Đối với 1.4a-redo (all_results in-memory): có sẵn cm
            return None
    return tns

# Lấy TN mean cho new (in-memory, có cm)
tn_new = {}
for k in KERNEL_NAMES:
    tns = [all_results[rid]['per_kernel'][k]['cm'][0][0] for rid in RUN_IDS]
    tn_new[k] = float(np.mean(tns))

# Lấy TN mean cho old (1.4a): JSON cũ KHÔNG có cm → để N/A
# (Nếu cần verify thủ công, đọc cell output của 1.4a notebook hoặc re-run.)
# Heuristic: 1.4a QSVM degenerate → TN_old=0 theo memory note 1.4a (line 141 Navigator);
# classical TN_old đọc gián tiếp qua precision: TN = N_actual_neg - FP, FP = TP*(1-precision)/precision...
# Phức tạp + sai số. Đơn giản: dùng marker "n/a (no cm in 1.4a JSON)" cho old, hoặc compute via metric algebra:
# Đối với binary: support_neg đã biết (đọc từ y_test trong all_results), precision/recall biết → suy ra TN/FP/TP/FN.
def reconstruct_cm_from_metrics(precision, recall, accuracy, n_total, n_pos):
    \"\"\"Reconstruct 2x2 cm từ metrics (binary). Trả về (TN, FP, FN, TP).\"\"\"
    if recall == 0 or precision == 0:
        TP = 0; FN = n_pos; FP = 0; TN = n_total - n_pos
        return TN, FP, FN, TP
    TP = recall * n_pos
    FN = n_pos - TP
    if precision > 0:
        FP = TP / precision - TP
    else:
        FP = 0
    n_neg = n_total - n_pos
    TN = n_neg - FP
    return int(round(TN)), int(round(FP)), int(round(FN)), int(round(TP))

tn_old = {k: [] for k in KERNEL_NAMES}
for entry_old in old_results['per_run']:
    rid = entry_old['run']
    # Dùng y_test của run hiện tại (cùng cấu trúc parquet → cùng n_total/n_pos)
    y_test_run = np.array(all_results[rid]['y_test'])
    n_total = len(y_test_run)
    n_pos = int((y_test_run == 1).sum())
    for k in KERNEL_NAMES:
        m_old = entry_old[k]
        TN, _, _, _ = reconstruct_cm_from_metrics(
            m_old['precision'], m_old['recall'], m_old['accuracy'], n_total, n_pos
        )
        tn_old[k].append(TN)
tn_old_mean = {k: float(np.mean(v)) for k, v in tn_old.items()}

# In bảng side-by-side
print('=' * 100)
print('  BẢNG SO SÁNH: 1.4a TUNED (C tuned từ 1.3) vs 1.4a-REDO (C=1.0 NEUTRAL)')
print('=' * 100)
print(f'  {"Kernel":>10}  {"C_old":>6}  {"F1_old":>14}  {"C_new":>6}  {"F1_new":>14}  '
      f'{"ΔF1":>8}  {"TN_old":>8}  {"TN_new":>8}  {"ΔTN":>7}')
print('  ' + '-' * 100)
for k in KERNEL_NAMES:
    f1_old = old_results['summary'][k]['f1_mean']
    f1o_s  = old_results['summary'][k]['f1_std']
    c_old  = old_results['summary'][k]['C']
    f1_new = summary_payload[k]['f1_mean']
    f1n_s  = summary_payload[k]['f1_std']
    c_new  = summary_payload[k]['C']
    df1    = f1_new - f1_old
    dtn    = tn_new[k] - tn_old_mean[k]
    print(f'  {k:>10}  {c_old:>6g}  {f1_old:.4f}±{f1o_s:.3f}  {c_new:>6g}  '
          f'{f1_new:.4f}±{f1n_s:.3f}  {df1:+7.4f}  {tn_old_mean[k]:>8.1f}  '
          f'{tn_new[k]:>8.1f}  {dtn:+7.1f}')
print('=' * 100)

# Diagnostic: nếu QSVM TN_new > 0 → thoát degeneracy
q_tn_new = tn_new['quantum']
q_tn_old = tn_old_mean['quantum']
if q_tn_old < 1.0 and q_tn_new > 1.0:
    print(f'\\n  ✅ QSVM thoát degeneracy: TN_mean {q_tn_old:.1f} → {q_tn_new:.1f}')
elif q_tn_old < 1.0 and q_tn_new < 1.0:
    print(f'\\n  ⚠️ QSVM VẪN degenerate ở C=1.0: TN_mean = {q_tn_new:.1f}')
else:
    print(f'\\n  Note: QSVM old không degenerate (TN_old={q_tn_old:.1f})')

# Lưu side-by-side vào JSON output cũng (append vào final_payload đã save)
final_payload['comparison_vs_1_4a'] = {
    'old_results_path': RESULTS_JSON_OLD,
    'tn_mean_old':      tn_old_mean,
    'tn_mean_new':      tn_new,
    'note':             'TN_old reconstructed from precision/recall/accuracy (1.4a JSON does not store cm)',
}
with open(RESULTS_JSON, 'w', encoding='utf-8') as fp:
    json.dump(final_payload, fp, indent=2, ensure_ascii=False)
print(f'\\n  [UPDATED] {RESULTS_JSON} (added comparison_vs_1_4a)')
""")

# Chèn 4 cell mới TRƯỚC cell summary (hiện tại là cell 24, index 24)
# Vị trí chèn: index 23 (sau cell 22 JSON save, trước cell 23 "## 10. Summary" markdown)
# Cell 23 hiện là "## 10. Summary" markdown → chèn vào trước nó (index 23)
cells.insert(23, kta_assert_md)
cells.insert(24, kta_assert_code)
cells.insert(25, comparison_md)
cells.insert(26, comparison_code)

print(f'After insert: {len(cells)} cells (was 25, +4 = 29)')

# Ghi notebook
with open(NB_PATH, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f'[WROTE] {NB_PATH}')
