"""Patch notebooks_unsw/c4_robustness_multirun_C1.ipynb (1.5-redo).

Goal: C=1.0 neutral cho 4 kernel, reuse cache c4/* va multirun/*, them tn/fp/fn/tp
+ KTA sanity check vs 1.5 + comparison cell 3 experiments.
"""
import json
import shutil
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SRC = 'notebooks_unsw/c4_robustness_multirun.ipynb'
DST = 'notebooks_unsw/c4_robustness_multirun_C1.ipynb'


def code_cell(src: str) -> dict:
    return {'cell_type': 'code', 'execution_count': None, 'metadata': {},
            'outputs': [], 'source': src.splitlines(keepends=True)}


def md_cell(src: str) -> dict:
    return {'cell_type': 'markdown', 'metadata': {},
            'source': src.splitlines(keepends=True)}


def set_src(cell: dict, src: str) -> None:
    cell['source'] = src.splitlines(keepends=True)
    if cell['cell_type'] == 'code':
        cell['outputs'] = []
        cell['execution_count'] = None


shutil.copy2(SRC, DST)
with open(DST, encoding='utf-8') as f:
    nb = json.load(f)

cells = nb['cells']
assert len(cells) == 31, f'Expected 31 cells in cloned notebook, got {len(cells)}'

# ── Cell 0: Markdown intro ─────────────────────────────────────────
set_src(cells[0], """# UNSW-NB15 — C4 Robustness Multi-Run Statevector (C=1.0 NEUTRAL re-run, 1.5-redo)

**Mục tiêu (1.5-redo):** Re-run 1.5 với `C=1.0` cho TẤT CẢ 4 kernel để có số liệu robustness **THẬT** (không phải degeneracy artifact).

**Lý do re-run:** Notebook 1.6 phát hiện C=0.01 (tuned từ 1.3) → QSVM degenerate (predict-all-attack). Trong 1.5 gốc, "robustness" QSVM thật ra là artifact:
- **Perturbation**: F1 invariant với σ ∈ {0.05, 0.1, 0.2} — vì decision = constant (luôn predict Attack), không nhạy noise.
- **Temporal**: std QSVM = 0.004 (rất thấp) — vì 20 cross-run pairs đều predict-all-attack giống nhau.
- **Prior shift**: F1 khớp công thức degenerate `F1 = 2p/(1+p)` đến 4 chữ số (1:9 → 0.948 khớp 0.9474).

**Sau khi sửa C=1.0**, QSVM có decision boundary thực → robustness pattern phản ánh thực sự kernel + data.

**Cache reuse (CỐT LÕI, 100%):** Kernel matrices KHÔNG phụ thuộc C → reuse:
- `models_unsw/qsvm_cache/multirun/run_{i}/` (5 K_train + 5 K_test_base cho i==j temporal & prior subsample)
- `models_unsw/qsvm_cache/c4/temporal/run{i}_test{j}/` (20 cross-pair K_test_train, i≠j)
- `models_unsw/qsvm_cache/c4/perturb/run{i}_sig{ms}/` (15 perturbed K_test_train)

KHÔNG re-compute quantum kernel. KTA QSVM mới phải khớp 1.5 (sanity check).

**Output mới (KHÔNG đụng 1.5 gốc):**
- `models_unsw/c4_results_C1.json` — thêm `tn/fp/fn/tp/precision/recall/C` per kernel entry
- `reports_unsw/c4_{temporal,perturbation,prior}_C1.png`
""")

# ── Cell 4: Constants ──────────────────────────────────────────────
set_src(cells[4], """# Hằng số chung
RANDOM_STATE = 42
RUN_IDS      = [1, 2, 3, 4, 5]
np.random.seed(RANDOM_STATE)

# Pipeline (khớp 1.3 / 1.4a / 1.5 — để cache hit)
N_QUBITS  = 4
K_SELECT  = 35
PCA_N     = 4
ANGLE_MAX = np.pi

# Quantum kernel
ZZ_REPS = 2
ZZ_ENT  = 'full'

# Classical kernel params (khớp SVC defaults — gamma='scale', coef0=0)
POLY_DEGREE = 2

# Target & label cols
TARGET_COL = 'label_binary'
LABEL_COLS = ['label_binary', 'label_multiclass', 'attack_category']

# Paths (notebook chạy ở notebooks_unsw/)
DATA_DIR         = '../data/unsw_nb15/processed_data/multi_run'
MODELS_DIR       = '../models_unsw'
MULTIRUN_CACHE   = f'{MODELS_DIR}/qsvm_cache/multirun'    # cache 1.4a — reuse
C4_CACHE         = f'{MODELS_DIR}/qsvm_cache/c4'          # cache 1.5 — reuse
REPORTS_DIR      = '../reports_unsw'
C_TUNING_JSON    = f'{MODELS_DIR}/c_tuning_results.json'  # CHỈ load để contrast
RESULTS_JSON_OLD = f'{MODELS_DIR}/c4_results.json'        # 1.5 gốc — load để compare
RESULTS_JSON     = f'{MODELS_DIR}/c4_results_C1.json'     # output mới 1.5-redo

# Kernel names + display
KERNEL_NAMES  = ['quantum', 'linear', 'poly', 'rbf']
DISPLAY_NAMES = {'quantum':'QSVM (ZZ)', 'linear':'SVM-Linear', 'poly':'SVM-Poly2', 'rbf':'SVM-RBF'}
COLORS        = {'quantum':'#2C5F8D', 'linear':'#A0C4FF', 'poly':'#7FB069', 'rbf':'#D62828'}

# Config tag (khớp 1.3 / 1.4a / 1.5)
CONFIG_TAG = 'r2_full_k35_p4_cv5_sf1_run1'
C_STRATEGY = 'neutral_C1_no_retune'

# C4 experiment params
PERTURB_SIGMAS = [0.05, 0.10, 0.20]
PRIOR_RATIOS   = [(0.1, 0.9), (0.5, 0.5), (0.9, 0.1)]

# Tạo cache dirs (chỉ để contract — không write thêm nếu cache đã có)
for d in [C4_CACHE, f'{C4_CACHE}/temporal', f'{C4_CACHE}/perturb', REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)

print(f'CONFIG_TAG      : {CONFIG_TAG}')
print(f'C_STRATEGY      : {C_STRATEGY}')
print(f'DATA_DIR        : {DATA_DIR}')
print(f'MULTIRUN_CACHE  : {MULTIRUN_CACHE}  (1.4a — REUSE)')
print(f'C4_CACHE        : {C4_CACHE}        (1.5 — REUSE)')
print(f'RESULTS_JSON_OLD: {RESULTS_JSON_OLD}')
print(f'RESULTS_JSON    : {RESULTS_JSON}')
""")

# ── Cell 5: Markdown — change heading ──────────────────────────────
set_src(cells[5], """## 1c. Set C=1.0 NEUTRAL (KHÔNG tune) + load 1.5 gốc để compare""")

# ── Cell 6: Replace load-C with hardcoded C=1.0 + load old c4_results ──
set_src(cells[6], """# KHÔNG load C_best — set C=1.0 neutral cho 4 kernel
C_BY_KERNEL = {k: 1.0 for k in KERNEL_NAMES}

print(f'=== C NEUTRAL (strategy = {C_STRATEGY}) ===')
for k in KERNEL_NAMES:
    print(f'  {k:>8s}: C={C_BY_KERNEL[k]:.4f}')

# Load 1.5 gốc để compare (KTA sanity + side-by-side)
with open(RESULTS_JSON_OLD, 'r', encoding='utf-8') as f:
    old_results = json.load(f)
print(f'\\n[OK] Loaded 1.5 gốc: {RESULTS_JSON_OLD}')
print(f'  Old config_tag = {old_results["metadata"].get("config_tag", "?")}')
print(f'  Old C_tuned_from = {old_results["metadata"].get("C_tuned_from", "?")}')
old_C = old_results['metadata'].get('C_by_kernel', {})
print(f'  Old C_by_kernel = {old_C}')

assert old_results['metadata']['config_tag'] == CONFIG_TAG, \\
    f'CONFIG_TAG mismatch: 1.5_old={old_results["metadata"]["config_tag"]} vs {CONFIG_TAG}'
print(f'  [OK] CONFIG_TAG khớp 1.5 — cache sẽ hit')
""")

# ── Cell 10: Update fit_eval_kernel to include cm + tn/fp/fn/tp ────
set_src(cells[10], """# Singleton quantum kernel để tránh khởi tạo lặp
_QK = None
def _get_qk():
    global _QK
    if _QK is None:
        fmap = zz_feature_map(N_QUBITS, reps=ZZ_REPS, entanglement=ZZ_ENT)
        _QK  = FidelityStatevectorKernel(feature_map=fmap)
    return _QK

def load_K_train_strict(rid):
    \"\"\"Load K_quantum_train_train từ multirun cache. Fail nếu miss.\"\"\"
    p = f'{MULTIRUN_CACHE}/run_{rid}/K_quantum_train_train_{CONFIG_TAG}.npy'
    if not os.path.exists(p):
        raise FileNotFoundError(f'[CACHE MISS] {p} — 1.5-redo phải reuse cache 1.4a')
    return np.load(p)

def load_K_test_strict(cache_path):
    \"\"\"Load K_quantum_test_train từ cache. Fail nếu miss (1.5-redo KHÔNG re-compute).\"\"\"
    if not os.path.exists(cache_path):
        raise FileNotFoundError(
            f'[CACHE MISS] {cache_path}\\n'
            f'1.5-redo PHẢI reuse cache 1.4a/1.5. KHÔNG re-compute quantum.'
        )
    return np.load(cache_path)

def classical_K(X_train, X_test, kernel_name):
    \"\"\"Tính K_train_train + K_test_train cho linear/poly/rbf khớp SVC defaults.\"\"\"
    if kernel_name == 'linear':
        return X_train @ X_train.T, X_test @ X_train.T

    n_feat = X_train.shape[1]
    var_X  = X_train.var()
    gamma  = 1.0 / (n_feat * var_X) if var_X > 0 else 1.0 / n_feat

    if kernel_name == 'poly':
        return (gamma * (X_train @ X_train.T)) ** POLY_DEGREE, \\
               (gamma * (X_test  @ X_train.T)) ** POLY_DEGREE

    if kernel_name == 'rbf':
        sq_tr = np.sum(X_train**2, axis=1)
        D_tr  = sq_tr[:, None] + sq_tr[None, :] - 2 * (X_train @ X_train.T)
        D_te  = np.sum(X_test**2, axis=1)[:, None] + sq_tr[None, :] - 2 * (X_test @ X_train.T)
        return np.exp(-gamma * np.maximum(D_tr, 0)), np.exp(-gamma * np.maximum(D_te, 0))

    raise ValueError(kernel_name)

def fit_eval_kernel(kernel_name, K_train, K_test_train, y_train, y_test, C):
    \"\"\"Fit SVC precomputed + eval. Trả về dict đầy đủ metrics + tn/fp/fn/tp.\"\"\"
    clf = SVC(kernel='precomputed', C=C, random_state=RANDOM_STATE)
    clf.fit(K_train, y_train)
    y_pred = clf.predict(K_test_train)
    # Binary cm với labels=[0,1] để tránh layout shift khi chỉ có 1 class
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
    tn, fp, fn, tp = int(cm[0,0]), int(cm[0,1]), int(cm[1,0]), int(cm[1,1])
    return {
        'f1':        float(f1_score(y_test, y_pred, average='binary')),
        'precision': float(precision_score(y_test, y_pred, average='binary', zero_division=0)),
        'recall':    float(recall_score(y_test, y_pred, average='binary', zero_division=0)),
        'accuracy':  float(accuracy_score(y_test, y_pred)),
        'tn': tn, 'fp': fp, 'fn': fn, 'tp': tp,
        'n_sv':      int(clf.support_.shape[0]),
        'y_pred':    y_pred.astype(int).tolist(),
        'C':         float(C),
    }
""")

# ── Cell 14: Temporal — use strict cache loads + record tn/fp/fn/tp ──
set_src(cells[14], """temporal_records = []  # list of dicts per pair per kernel
t0_e1 = time.time()
n_pairs = 0
for i in RUN_IDS:
    pi = PER_RUN[i]
    selector_i, pca_i, scaler_i = pi['selector'], pi['pca'], pi['scaler']
    X_train_pipe_i = pi['X_train_pipe']
    y_train_i      = pi['y_train']
    K_q_train_i    = pi['K_q_train']

    # KTA quantum (chỉ phụ thuộc K_train + y_train của run i)
    kta_q_i = compute_kta(K_q_train_i, y_train_i)

    for j in RUN_IDS:
        n_pairs += 1
        pj = PER_RUN[j]
        # Transform test_run{j} qua pipeline_i (zero-leakage)
        X_test_raw_j = pj['X_test_raw']
        y_test_j     = pj['y_test']
        X_test_pipe_j_via_i = apply_pipeline(X_test_raw_j, selector_i, pca_i, scaler_i)

        # ── Quantum: STRICT cache load (1.5-redo KHÔNG re-compute)
        if i == j:
            K_q_test = pi['K_q_test_base']  # đã load từ 1.4a (multirun cache)
        else:
            p = f'{C4_CACHE}/temporal/run{i}_test{j}/K_quantum_test_train_{CONFIG_TAG}.npy'
            K_q_test = load_K_test_strict(p)

        for k in KERNEL_NAMES:
            if k == 'quantum':
                K_tr, K_te = K_q_train_i, K_q_test
                kta_val = kta_q_i
            else:
                K_tr, K_te = classical_K(X_train_pipe_i, X_test_pipe_j_via_i, k)
                kta_val = compute_kta(K_tr, y_train_i)
            res = fit_eval_kernel(k, K_tr, K_te, y_train_i, y_test_j, C_BY_KERNEL[k])
            temporal_records.append({
                'train_run': i, 'test_run': j, 'kernel': k,
                'f1': res['f1'], 'precision': res['precision'], 'recall': res['recall'],
                'accuracy': res['accuracy'],
                'tn': res['tn'], 'fp': res['fp'], 'fn': res['fn'], 'tp': res['tp'],
                'kta': kta_val, 'n_sv': res['n_sv'], 'C': res['C'],
                'y_pred': res['y_pred'], 'y_test': y_test_j.tolist(),
            })
    print(f'  [E1] hoàn tất train_run={i} ({len(RUN_IDS)} test pairs)')
print(f'\\nE1 xong: {n_pairs} pairs trong {time.time()-t0_e1:.1f}s')
""")

# ── Cell 17: Perturbation — strict cache + record tn/fp/fn/tp ──────
set_src(cells[17], """perturb_records = []  # per (run, sigma, kernel)
t0_e2 = time.time()
for rid in RUN_IDS:
    p = PER_RUN[rid]
    selector_i, pca_i, scaler_i = p['selector'], p['pca'], p['scaler']
    X_train_pipe = p['X_train_pipe']
    y_train      = p['y_train']
    y_test       = p['y_test']
    X_test_pca   = p['X_test_pca']  # đã PCA, chưa MinMax
    K_q_train    = p['K_q_train']
    kta_q        = compute_kta(K_q_train, y_train)

    for sigma in PERTURB_SIGMAS:
        rng = np.random.RandomState(RANDOM_STATE + rid * 1000 + int(sigma * 10000))
        noise = rng.normal(0.0, sigma, size=X_test_pca.shape)
        X_test_pipe_noisy = np.clip(scaler_i.transform(X_test_pca + noise), 0.0, ANGLE_MAX)

        # Quantum K_test_train — STRICT cache load (1.5-redo)
        cache_p = f'{C4_CACHE}/perturb/run{rid}_sig{int(sigma*1000):03d}/K_quantum_test_train_{CONFIG_TAG}.npy'
        K_q_test = load_K_test_strict(cache_p)

        for k in KERNEL_NAMES:
            if k == 'quantum':
                K_tr, K_te = K_q_train, K_q_test
                kta_val = kta_q
            else:
                K_tr, K_te = classical_K(X_train_pipe, X_test_pipe_noisy, k)
                kta_val = compute_kta(K_tr, y_train)
            res = fit_eval_kernel(k, K_tr, K_te, y_train, y_test, C_BY_KERNEL[k])
            perturb_records.append({
                'run': rid, 'sigma': sigma, 'kernel': k,
                'f1': res['f1'], 'precision': res['precision'], 'recall': res['recall'],
                'accuracy': res['accuracy'],
                'tn': res['tn'], 'fp': res['fp'], 'fn': res['fn'], 'tp': res['tp'],
                'kta': kta_val, 'n_sv': res['n_sv'], 'C': res['C'],
            })
    print(f'  [E2] run_{rid} xong ({len(PERTURB_SIGMAS)} sigmas)')
print(f'\\nE2 xong trong {time.time()-t0_e2:.1f}s')
""")

# ── Cell 21: Prior shift — record tn/fp/fn/tp ──────────────────────
set_src(cells[21], """prior_records = []
t0_e3 = time.time()
for rid in RUN_IDS:
    p = PER_RUN[rid]
    X_train_pipe = p['X_train_pipe']
    X_test_pipe  = p['X_test_pipe']
    y_train      = p['y_train']
    y_test       = p['y_test']
    K_q_train    = p['K_q_train']
    K_q_test_base = p['K_q_test_base']
    kta_q        = compute_kta(K_q_train, y_train)

    for (rn, ra) in PRIOR_RATIOS:
        rng = np.random.RandomState(RANDOM_STATE + rid * 100 + int(rn * 10))
        sel = stratified_subsample(y_test, rn, ra, rng)
        y_test_sub      = y_test[sel]
        X_test_pipe_sub = X_test_pipe[sel]
        K_q_test_sub    = K_q_test_base[sel, :]  # subset rows — KHÔNG cần cache mới

        for k in KERNEL_NAMES:
            if k == 'quantum':
                K_tr, K_te = K_q_train, K_q_test_sub
                kta_val = kta_q
            else:
                K_tr, K_te = classical_K(X_train_pipe, X_test_pipe_sub, k)
                kta_val = compute_kta(K_tr, y_train)
            res = fit_eval_kernel(k, K_tr, K_te, y_train, y_test_sub, C_BY_KERNEL[k])
            prior_records.append({
                'run': rid, 'ratio_normal': rn, 'ratio_attack': ra,
                'n_test': int(len(y_test_sub)),
                'n_normal': int(np.sum(y_test_sub == 0)),
                'n_attack': int(np.sum(y_test_sub == 1)),
                'kernel': k,
                'f1': res['f1'], 'precision': res['precision'], 'recall': res['recall'],
                'accuracy': res['accuracy'],
                'tn': res['tn'], 'fp': res['fp'], 'fn': res['fn'], 'tp': res['tp'],
                'kta': kta_val, 'n_sv': res['n_sv'], 'C': res['C'],
            })
    print(f'  [E3] run_{rid} xong ({len(PRIOR_RATIOS)} ratios)')
print(f'\\nE3 xong trong {time.time()-t0_e3:.1f}s')
""")

# ── Cell 24: Figure 1 (temporal) — update path + title ─────────────
set_src(cells[24], """# ── Figure 1: E1 Temporal — boxplot F1 cho 4 kernels × 20 pairs ─────────────
fig1, ax1 = plt.subplots(figsize=(10, 6))
data_box = [temporal_df[temporal_df['kernel'] == k]['f1'].values for k in KERNEL_NAMES]
bp = ax1.boxplot(data_box, labels=[DISPLAY_NAMES[k] for k in KERNEL_NAMES],
                 patch_artist=True, widths=0.55, showmeans=True,
                 meanprops=dict(marker='D', markerfacecolor='white',
                                markeredgecolor='black', markersize=7))
for patch, k in zip(bp['boxes'], KERNEL_NAMES):
    patch.set_facecolor(COLORS[k]); patch.set_alpha(0.65)
rng_jit = np.random.RandomState(0)
for i, k in enumerate(KERNEL_NAMES):
    ys = temporal_df[temporal_df['kernel'] == k]['f1'].values
    xs = rng_jit.normal(i + 1, 0.05, size=len(ys))
    ax1.scatter(xs, ys, color=COLORS[k], edgecolor='black',
                s=28, alpha=0.75, linewidth=0.5, zorder=3)
ax1.set_ylabel('F1 (binary)', fontsize=11)
ax1.set_title(f'E1 — Temporal Cross-Run Robustness (C=1.0 NEUTRAL)\\n'
              f'F1 across 25 (train_run × test_run) pairs, 4 kernels',
              fontsize=12, fontweight='bold')
ax1.grid(True, axis='y', alpha=0.3)
plt.tight_layout()
fig1_path = f'{REPORTS_DIR}/c4_temporal_C1.png'
fig1.savefig(fig1_path, dpi=140, bbox_inches='tight')
plt.close(fig1)
print(f'Saved: {fig1_path}')
display(Image(filename=fig1_path))
""")

# ── Cell 25: Figure 2 (perturbation) ───────────────────────────────
set_src(cells[25], """# ── Figure 2: E2 Perturbation — line F1 vs σ với errorbar, 4 kernels ────────
fig2, ax2 = plt.subplots(figsize=(10, 6))
sigmas = sorted(perturb_df['sigma'].unique())
for k in KERNEL_NAMES:
    means = [perturb_df[(perturb_df['kernel']==k) & (perturb_df['sigma']==s)]['f1'].mean()
             for s in sigmas]
    stds  = [perturb_df[(perturb_df['kernel']==k) & (perturb_df['sigma']==s)]['f1'].std()
             for s in sigmas]
    ax2.errorbar(sigmas, means, yerr=stds, marker='o', markersize=8,
                 linewidth=2, capsize=5, label=DISPLAY_NAMES[k],
                 color=COLORS[k], alpha=0.9)
ax2.set_xlabel('Gaussian noise σ (added in PCA space)', fontsize=11)
ax2.set_ylabel('F1 (binary), mean ± std over 5 runs', fontsize=11)
ax2.set_title(f'E2 — Feature Perturbation Robustness (C=1.0 NEUTRAL)\\n'
              f'F1 vs σ, 4 kernels × {len(RUN_IDS)} runs (statevector)',
              fontsize=12, fontweight='bold')
ax2.set_xticks(sigmas)
ax2.grid(True, alpha=0.3)
ax2.legend(loc='best', framealpha=0.9)
plt.tight_layout()
fig2_path = f'{REPORTS_DIR}/c4_perturbation_C1.png'
fig2.savefig(fig2_path, dpi=140, bbox_inches='tight')
plt.close(fig2)
print(f'Saved: {fig2_path}')
display(Image(filename=fig2_path))
""")

# ── Cell 26: Figure 3 (prior) ──────────────────────────────────────
set_src(cells[26], """# ── Figure 3: E3 Prior Shift — grouped bar F1 ở 3 ratios × 4 kernels ───────
fig3, ax3 = plt.subplots(figsize=(11, 6))
ratios = PRIOR_RATIOS
ratio_labels = [f'{int(rn*10)}:{int(ra*10)}\\n(N:A)' for (rn, ra) in ratios]
x = np.arange(len(ratios))
width = 0.20

for idx, k in enumerate(KERNEL_NAMES):
    means = []
    stds  = []
    for (rn, _) in ratios:
        vals = prior_df[(prior_df['kernel']==k) & (prior_df['ratio_normal']==rn)]['f1'].values
        means.append(vals.mean()); stds.append(vals.std())
    ax3.bar(x + (idx - 1.5) * width, means, width, yerr=stds,
            label=DISPLAY_NAMES[k], color=COLORS[k], alpha=0.85,
            capsize=4, edgecolor='black', linewidth=0.8)

ax3.set_xticks(x); ax3.set_xticklabels(ratio_labels)
ax3.set_xlabel('Test class prior (Normal : Attack)', fontsize=11)
ax3.set_ylabel('F1 (binary), mean ± std over 5 runs', fontsize=11)
ax3.set_title(f'E3 — Class Prior Shift Robustness (C=1.0 NEUTRAL)\\n'
              f'F1 across 3 priors × 4 kernels × {len(RUN_IDS)} runs (statevector)',
              fontsize=12, fontweight='bold')
ax3.grid(True, axis='y', alpha=0.3)
ax3.legend(loc='best', framealpha=0.9)
plt.tight_layout()
fig3_path = f'{REPORTS_DIR}/c4_prior_C1.png'
fig3.savefig(fig3_path, dpi=140, bbox_inches='tight')
plt.close(fig3)
print(f'Saved: {fig3_path}')
display(Image(filename=fig3_path))
""")

# ── Cell 28: Save JSON — extended fields + new metadata ────────────
set_src(cells[28], """def _summary_block(df_records, group_keys, kernel_names):
    \"\"\"Helper: gom per_run/per_pair + summary mean±std (kèm precision/recall).\"\"\"
    out_summary = {}
    for k in kernel_names:
        sub = df_records[df_records['kernel'] == k]
        out_summary[k] = {
            'f1_mean':        float(sub['f1'].mean()),
            'f1_std':         float(sub['f1'].std()),
            'precision_mean': float(sub['precision'].mean()),
            'precision_std':  float(sub['precision'].std()),
            'recall_mean':    float(sub['recall'].mean()),
            'recall_std':     float(sub['recall'].std()),
            'acc_mean':       float(sub['accuracy'].mean()),
            'acc_std':        float(sub['accuracy'].std()),
            'kta_mean':       float(sub['kta'].mean()),
            'kta_std':        float(sub['kta'].std()),
            'tn_mean':        float(sub['tn'].mean()),
            'fp_mean':        float(sub['fp'].mean()),
            'fn_mean':        float(sub['fn'].mean()),
            'tp_mean':        float(sub['tp'].mean()),
            'C':              float(sub['C'].iloc[0]),
        }
    return out_summary

def _per_kernel_entry(row):
    \"\"\"Helper: tạo 1 entry per-kernel với đầy đủ fields theo spec 1.5-redo.\"\"\"
    return {
        'f1':        float(row['f1']),
        'precision': float(row['precision']),
        'recall':    float(row['recall']),
        'accuracy':  float(row['accuracy']),
        'tn': int(row['tn']), 'fp': int(row['fp']),
        'fn': int(row['fn']), 'tp': int(row['tp']),
        'kta':       float(row['kta']),
        'n_sv':      int(row['n_sv']),
        'C':         float(row['C']),
    }

# ── E1 Temporal ──
temporal_per_pair = []
for (i, j), g in temporal_df.groupby(['train_run','test_run']):
    entry = {'train_run': int(i), 'test_run': int(j)}
    for k in KERNEL_NAMES:
        row = g[g['kernel']==k].iloc[0]
        entry[k] = _per_kernel_entry(row)
    temporal_per_pair.append(entry)
temporal_block = {'per_pair': temporal_per_pair,
                  'summary':  _summary_block(temporal_df, ['train_run','test_run'], KERNEL_NAMES)}

# ── E2 Perturbation ──
perturb_per_sigma = []
for sigma in PERTURB_SIGMAS:
    sub = perturb_df[perturb_df['sigma'] == sigma]
    per_run_list = []
    for rid in RUN_IDS:
        srid = sub[sub['run'] == rid]
        entry = {'run': int(rid)}
        for k in KERNEL_NAMES:
            row = srid[srid['kernel']==k].iloc[0]
            entry[k] = _per_kernel_entry(row)
        per_run_list.append(entry)
    perturb_per_sigma.append({
        'sigma':   float(sigma),
        'per_run': per_run_list,
        'summary': _summary_block(sub, ['run'], KERNEL_NAMES),
    })
perturb_block = {'per_sigma': perturb_per_sigma}

# ── E3 Prior shift ──
prior_per_ratio = []
for (rn, ra) in PRIOR_RATIOS:
    sub = prior_df[(prior_df['ratio_normal']==rn) & (prior_df['ratio_attack']==ra)]
    per_run_list = []
    for rid in RUN_IDS:
        srid = sub[sub['run'] == rid]
        entry = {'run': int(rid),
                 'n_test':   int(srid['n_test'].iloc[0]),
                 'n_normal': int(srid['n_normal'].iloc[0]),
                 'n_attack': int(srid['n_attack'].iloc[0])}
        for k in KERNEL_NAMES:
            row = srid[srid['kernel']==k].iloc[0]
            entry[k] = _per_kernel_entry(row)
        per_run_list.append(entry)
    prior_per_ratio.append({
        'ratio_normal': float(rn), 'ratio_attack': float(ra),
        'per_run': per_run_list,
        'summary': _summary_block(sub, ['run'], KERNEL_NAMES),
    })
prior_block = {'per_ratio': prior_per_ratio}

# ── Metadata ──
metadata = {
    'regime':              'statevector',
    'backend':             'FidelityStatevectorKernel',
    'n_runs':              len(RUN_IDS),
    'C_strategy':          C_STRATEGY,
    'C_by_kernel':         {k: float(C_BY_KERNEL[k]) for k in KERNEL_NAMES},
    'compared_against':    RESULTS_JSON_OLD,
    'cache_reused_from':   [MULTIRUN_CACHE, C4_CACHE],
    'rationale':           (
        '1.6 (c1_dimreduction_multirun) found C=0.01 (tuned in 1.3) caused QSVM degeneracy '
        '(predict-all-attack). In 1.5 original, "robustness" of QSVM was an artifact: '
        'perturbation F1 invariant (constant prediction), temporal std=0.004 (trivially low), '
        'prior F1 matching degenerate formula F1=2p/(1+p). C=1.0 neutral surfaces real '
        'robustness pattern. Kernel matrices reused 100% — KTA must match 1.5.'
    ),
    'config_tag':          CONFIG_TAG,
    'experiments':         ['temporal', 'perturbation', 'prior_shift'],
    'temporal_pairs':      'all_cross',
    'n_temporal_pairs':    int(len(temporal_per_pair)),
    'perturbation_sigmas': [float(s) for s in PERTURB_SIGMAS],
    'prior_ratios':        [[float(rn), float(ra)] for (rn, ra) in PRIOR_RATIOS],
    'kernels':             KERNEL_NAMES,
    'pipeline':            {'K_select': K_SELECT, 'PCA_N': PCA_N,
                            'angle_max': float(ANGLE_MAX), 'zz_reps': ZZ_REPS,
                            'zz_entanglement': ZZ_ENT, 'poly_degree': POLY_DEGREE},
    'random_state':        RANDOM_STATE,
    'date':                datetime.date.today().isoformat(),
    'reports':             [
        f'{REPORTS_DIR}/c4_temporal_C1.png',
        f'{REPORTS_DIR}/c4_perturbation_C1.png',
        f'{REPORTS_DIR}/c4_prior_C1.png',
    ],
}

payload = {
    'temporal':    temporal_block,
    'perturbation':perturb_block,
    'prior_shift': prior_block,
    'metadata':    metadata,
}

with open(RESULTS_JSON, 'w', encoding='utf-8') as f:
    json.dump(payload, f, indent=2, ensure_ascii=False)
print(f'Saved: {RESULTS_JSON}')
print(f'Size : {os.path.getsize(RESULTS_JSON)} bytes')
""")

# ── Cell 30: Summary header update ─────────────────────────────────
set_src(cells[30], """print('=' * 88)
print('  UNSW-NB15 — C4 ROBUSTNESS MULTI-RUN STATEVECTOR (1.5-REDO, C=1.0 NEUTRAL)')
print('=' * 88)
print(f'  CONFIG_TAG : {CONFIG_TAG}')
print(f'  C_STRATEGY : {C_STRATEGY}')
print(f'  Compared vs: {RESULTS_JSON_OLD}  (1.5 gốc, C tuned)')
print(f'  Regime     : statevector (noiseless)')
print(f'  Cache reuse: 100% từ {MULTIRUN_CACHE} + {C4_CACHE}')
print(f'  Runs       : {len(RUN_IDS)} | Kernels: {KERNEL_NAMES}')
print()

# ── E1 ──
print('── E1: Temporal Cross-Run (mean ± std over all pairs) ───────────────────────')
print(f'  {"Kernel":>10}  {"F1":>16}  {"Accuracy":>16}  {"KTA":>16}')
print('  ' + '-' * 70)
for k in KERNEL_NAMES:
    s = temporal_block['summary'][k]
    print(f'  {k:>10}  {s["f1_mean"]:.4f}±{s["f1_std"]:.4f}    '
          f'{s["acc_mean"]:.4f}±{s["acc_std"]:.4f}    '
          f'{s["kta_mean"]:.4f}±{s["kta_std"]:.4f}')

# ── E2 ──
print()
print('── E2: Feature Perturbation (mean ± std over 5 runs, per σ) ──────────────────')
print(f'  {"Kernel":>10}  ' + '  '.join([f'σ={s:<6g}' for s in PERTURB_SIGMAS]))
print('  ' + '-' * 70)
for k in KERNEL_NAMES:
    row = []
    for blk in perturb_block['per_sigma']:
        s = blk['summary'][k]
        row.append(f'{s["f1_mean"]:.3f}±{s["f1_std"]:.3f}')
    print(f'  {k:>10}  ' + '  '.join([f'{v:<10}' for v in row]))

# ── E3 ──
print()
print('── E3: Class Prior Shift (mean ± std over 5 runs, per ratio N:A) ─────────────')
print(f'  {"Kernel":>10}  ' + '  '.join([f'{int(rn*10)}:{int(ra*10):<6}' for (rn,ra) in PRIOR_RATIOS]))
print('  ' + '-' * 70)
for k in KERNEL_NAMES:
    row = []
    for blk in prior_block['per_ratio']:
        s = blk['summary'][k]
        row.append(f'{s["f1_mean"]:.3f}±{s["f1_std"]:.3f}')
    print(f'  {k:>10}  ' + '  '.join([f'{v:<10}' for v in row]))

# ── QSVM vs RBF head-to-head ──
print()
print('  QSVM vs RBF head-to-head (Δ F1 = QSVM - RBF, mean):')
e1 = temporal_block['summary']
print(f'    E1 temporal           : Δ = {e1["quantum"]["f1_mean"] - e1["rbf"]["f1_mean"]:+.4f}')
for blk in perturb_block['per_sigma']:
    s = blk['summary']
    print(f'    E2 σ={blk["sigma"]:<5g}            : Δ = {s["quantum"]["f1_mean"] - s["rbf"]["f1_mean"]:+.4f}')
for blk in prior_block['per_ratio']:
    s = blk['summary']
    print(f'    E3 ({int(blk["ratio_normal"]*10)}:{int(blk["ratio_attack"]*10)})              : Δ = {s["quantum"]["f1_mean"] - s["rbf"]["f1_mean"]:+.4f}')
print('=' * 88)
print('DONE.')
""")

# ── Insert new cells: KTA sanity check + comparison vs 1.5 ────────
kta_md = md_cell("""## 9b. Sanity check: KTA cache-reuse (KTA mới == KTA 1.5 gốc)

Kernel matrix không phụ thuộc C → KTA QSVM cho cả 3 experiments phải khớp 1.5 đến nhiều chữ số. Cho temporal: per-pair (i,j) KTA chỉ phụ thuộc K_train(i) → check kta_mean của summary block.
""")

kta_code = code_cell("""# Sanity: KTA mean cho mỗi experiment × kernel phải khớp 1.5
print('=== KTA cache-reuse sanity check vs 1.5 ===')
print(f'{"Experiment":<24}  {"Kernel":>8}  {"KTA_new":>12}  {"KTA_old":>12}  {"|delta|":>10}  Status')
print('-' * 90)
max_delta = 0.0
checks = []

# E1 temporal
for k in KERNEL_NAMES:
    new_k = temporal_block['summary'][k]['kta_mean']
    old_k = old_results['temporal']['summary'][k]['kta_mean']
    d = abs(new_k - old_k); max_delta = max(max_delta, d)
    st = 'OK' if d < 1e-6 else 'FAIL'
    checks.append(d < 1e-6)
    print(f'{"E1 temporal":<24}  {k:>8}  {new_k:>12.8f}  {old_k:>12.8f}  {d:>10.2e}  {st}')

# E2 perturbation per sigma
for blk_new, blk_old in zip(perturb_block['per_sigma'], old_results['perturbation']['per_sigma']):
    sigma = blk_new['sigma']
    for k in KERNEL_NAMES:
        new_k = blk_new['summary'][k]['kta_mean']
        old_k = blk_old['summary'][k]['kta_mean']
        d = abs(new_k - old_k); max_delta = max(max_delta, d)
        st = 'OK' if d < 1e-6 else 'FAIL'
        checks.append(d < 1e-6)
        print(f'{f"E2 perturb σ={sigma}":<24}  {k:>8}  {new_k:>12.8f}  {old_k:>12.8f}  {d:>10.2e}  {st}')

# E3 prior per ratio
for blk_new, blk_old in zip(prior_block['per_ratio'], old_results['prior_shift']['per_ratio']):
    rn = blk_new['ratio_normal']; ra = blk_new['ratio_attack']
    for k in KERNEL_NAMES:
        new_k = blk_new['summary'][k]['kta_mean']
        old_k = blk_old['summary'][k]['kta_mean']
        d = abs(new_k - old_k); max_delta = max(max_delta, d)
        st = 'OK' if d < 1e-6 else 'FAIL'
        checks.append(d < 1e-6)
        print(f'{f"E3 prior {int(rn*10)}:{int(ra*10)}":<24}  {k:>8}  {new_k:>12.8f}  {old_k:>12.8f}  {d:>10.2e}  {st}')

assert all(checks), f'KTA mismatch (max |delta|={max_delta:.4e}) — cache reuse broken'
print(f'\\n[OK] KTA cache-reuse verified ({len(checks)} checks) — max |delta|={max_delta:.2e}')
""")

cmp_md = md_cell("""## 9c. Bảng so sánh side-by-side: 1.5 (C tuned) vs 1.5-redo (C=1.0 neutral)

So sánh F1 cho TẤT CẢ entries trong 3 experiments. Cột "deg_dist" cho prior shift cho biết F1 lệch khỏi công thức degenerate `F1=2p/(1+p)` bao nhiêu (1.5 gốc khớp công thức đến 4 chữ số = QSVM predict-all-attack).
""")

cmp_code = code_cell("""# ── E1 Temporal: bảng F1 mean per kernel ──
print('=' * 100)
print('  BẢNG SO SÁNH 1.5-REDO vs 1.5 GỐC (C=1.0 NEUTRAL vs C tuned)')
print('=' * 100)

print('\\n[E1 Temporal — 25 cross-run pairs, mean F1]')
print(f'  {"Kernel":>8}  {"C_old":>6}  {"F1_old":>14}  {"C_new":>6}  {"F1_new":>14}  {"ΔF1":>8}  {"std_old":>8}  {"std_new":>8}')
print('  ' + '-' * 96)
for k in KERNEL_NAMES:
    so = old_results['temporal']['summary'][k]
    sn = temporal_block['summary'][k]
    co = old_results['metadata']['C_by_kernel'][k]
    cn = sn['C']
    df1 = sn['f1_mean'] - so['f1_mean']
    print(f'  {k:>8}  {co:>6g}  {so["f1_mean"]:.4f}±{so["f1_std"]:.3f}  {cn:>6g}  '
          f'{sn["f1_mean"]:.4f}±{sn["f1_std"]:.3f}  {df1:+7.4f}  {so["f1_std"]:>8.4f}  {sn["f1_std"]:>8.4f}')

# ── E2 Perturbation: bảng F1 per (sigma, kernel) ──
print('\\n[E2 Perturbation — F1 mean per σ]')
print(f'  {"Kernel":>8}  {"σ":>6}  {"C_old":>6}  {"F1_old":>14}  {"C_new":>6}  {"F1_new":>14}  {"ΔF1":>8}')
print('  ' + '-' * 88)
for k in KERNEL_NAMES:
    for blk_new, blk_old in zip(perturb_block['per_sigma'], old_results['perturbation']['per_sigma']):
        sigma = blk_new['sigma']
        so = blk_old['summary'][k]
        sn = blk_new['summary'][k]
        co = old_results['metadata']['C_by_kernel'][k]
        cn = sn['C']
        df1 = sn['f1_mean'] - so['f1_mean']
        print(f'  {k:>8}  {sigma:>6.2f}  {co:>6g}  {so["f1_mean"]:.4f}±{so["f1_std"]:.3f}  {cn:>6g}  '
              f'{sn["f1_mean"]:.4f}±{sn["f1_std"]:.3f}  {df1:+7.4f}')
    print('  ' + '-' * 88)

# QSVM perturbation invariance check: range F1 across sigmas
q_f1_per_sigma_old = [b['summary']['quantum']['f1_mean'] for b in old_results['perturbation']['per_sigma']]
q_f1_per_sigma_new = [b['summary']['quantum']['f1_mean'] for b in perturb_block['per_sigma']]
print(f'\\n  QSVM F1 range across σ (max - min):')
print(f'    Old (1.5): {max(q_f1_per_sigma_old) - min(q_f1_per_sigma_old):.6f}  '
      f'→ {q_f1_per_sigma_old}  (invariant = degeneracy)')
print(f'    New (C=1): {max(q_f1_per_sigma_new) - min(q_f1_per_sigma_new):.6f}  '
      f'→ {q_f1_per_sigma_new}  (sensitive = non-degenerate)')

# ── E3 Prior Shift: bảng F1 + deg_dist (lệch khỏi công thức degenerate) ──
def f1_degenerate(ratio_attack):
    # Nếu predict-all-attack: TP=n_attack, FP=n_normal, FN=0, TN=0
    # → precision = n_attack/(n_attack+n_normal) = ra; recall = 1
    # → F1 = 2*ra*1/(ra+1) = 2*ra/(1+ra)
    return 2 * ratio_attack / (1 + ratio_attack)

print('\\n[E3 Prior Shift — F1 mean per ratio Normal:Attack]')
print(f'  {"Kernel":>8}  {"Ratio":>9}  {"F1_deg_formula":>14}  {"F1_old":>14}  {"deg_dist_old":>12}  {"F1_new":>14}  {"deg_dist_new":>12}')
print('  ' + '-' * 100)
for k in KERNEL_NAMES:
    for blk_new, blk_old in zip(prior_block['per_ratio'], old_results['prior_shift']['per_ratio']):
        rn, ra = blk_new['ratio_normal'], blk_new['ratio_attack']
        so = blk_old['summary'][k]
        sn = blk_new['summary'][k]
        f1_deg = f1_degenerate(ra)
        dist_old = abs(so['f1_mean'] - f1_deg)
        dist_new = abs(sn['f1_mean'] - f1_deg)
        print(f'  {k:>8}  {int(rn*10)}:{int(ra*10):<7}  {f1_deg:>14.4f}  '
              f'{so["f1_mean"]:.4f}±{so["f1_std"]:.3f}  {dist_old:>12.4f}  '
              f'{sn["f1_mean"]:.4f}±{sn["f1_std"]:.3f}  {dist_new:>12.4f}')
    print('  ' + '-' * 100)

# QSVM degeneracy signature check
print('\\n  QSVM degeneracy signature (prior shift) — deg_dist = |F1 - 2p/(1+p)|:')
for blk_new, blk_old in zip(prior_block['per_ratio'], old_results['prior_shift']['per_ratio']):
    rn, ra = blk_new['ratio_normal'], blk_new['ratio_attack']
    f1_deg = f1_degenerate(ra)
    dist_old = abs(blk_old['summary']['quantum']['f1_mean'] - f1_deg)
    dist_new = abs(blk_new['summary']['quantum']['f1_mean'] - f1_deg)
    print(f'    {int(rn*10)}:{int(ra*10)}  deg_dist_old={dist_old:.6f}  deg_dist_new={dist_new:.6f}  '
          f'→ old {"≈ degenerate" if dist_old < 0.01 else "non-degenerate"}, '
          f'new {"still degenerate" if dist_new < 0.01 else "non-degenerate (escaped)"}')

# QSVM TN comparison
print('\\n  QSVM TN_mean (cm[0][0]) per experiment — TN > 0 ⇒ thoát degeneracy:')
tn_temp = temporal_block['summary']['quantum']['tn_mean']
print(f'    E1 temporal               : TN_mean = {tn_temp:.2f}')
for blk in perturb_block['per_sigma']:
    print(f'    E2 perturb σ={blk["sigma"]:<5g}      : TN_mean = {blk["summary"]["quantum"]["tn_mean"]:.2f}')
for blk in prior_block['per_ratio']:
    rn, ra = blk['ratio_normal'], blk['ratio_attack']
    print(f'    E3 prior {int(rn*10)}:{int(ra*10)}                : TN_mean = {blk["summary"]["quantum"]["tn_mean"]:.2f}')

# Append comparison vào JSON
payload['comparison_vs_1_5'] = {
    'old_results_path':    RESULTS_JSON_OLD,
    'qsvm_perturb_range_old': float(max(q_f1_per_sigma_old) - min(q_f1_per_sigma_old)),
    'qsvm_perturb_range_new': float(max(q_f1_per_sigma_new) - min(q_f1_per_sigma_new)),
    'qsvm_prior_deg_dist': [
        {
            'ratio': [float(b['ratio_normal']), float(b['ratio_attack'])],
            'deg_dist_old': float(abs(bo['summary']['quantum']['f1_mean'] - f1_degenerate(b['ratio_attack']))),
            'deg_dist_new': float(abs(b['summary']['quantum']['f1_mean'] - f1_degenerate(b['ratio_attack']))),
        }
        for b, bo in zip(prior_block['per_ratio'], old_results['prior_shift']['per_ratio'])
    ],
    'note': '1.5 gốc: QSVM degenerate (F1 invariant với σ, prior F1 khớp 2p/(1+p)). '
            '1.5-redo C=1.0: QSVM sensitive với σ, prior F1 lệch khỏi formula.',
}
with open(RESULTS_JSON, 'w', encoding='utf-8') as f:
    json.dump(payload, f, indent=2, ensure_ascii=False)
print(f'\\n[UPDATED] {RESULTS_JSON} (appended comparison_vs_1_5)')
""")

# Chèn 4 cells trước summary header (cell 30 hiện tại sau khi swap).
# Cell 29 là markdown "## 10. Summary..." — chèn TRƯỚC nó (index 29)
cells.insert(29, kta_md)
cells.insert(30, kta_code)
cells.insert(31, cmp_md)
cells.insert(32, cmp_code)

print(f'After insert: {len(cells)} cells (was 31, +4 = 35)')

with open(DST, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print(f'[WROTE] {DST}')
