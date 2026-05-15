"""Patch cell 24 của c2_quantum_kernel_expressibility.ipynb.

Thay logic tính Spearman trên subset (N=300) bằng tính Pearson + Spearman
trên TOÀN BỘ X_train_full (post-MinMax pipeline). Sinh ra:
  - Bảng 4.8 (Pearson r, Spearman rho, |rho - r|) cho 6 cặp PCA in ra stdout
  - reports/c2_pearson_heatmap_full.png
  - reports/c2_spearman_heatmap_full.png
  - reports/c2_spearman_bridge.png (3-panel: Pearson + Spearman + ZZ network graph)

Chạy 1 lần để patch in-place. Idempotent: re-run sẽ overwrite cell 24 source mới.
"""
import json
from pathlib import Path

NB_PATH = Path(__file__).resolve().parents[1] / "notebooks" / "c2_quantum_kernel_expressibility.ipynb"

NEW_SOURCE = r'''n_pcs = N_QUBITS  # 4 PCA component
ZZ_PAIRS = [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]  # full entanglement, tat ca 6 cap

# ───────────────────────────────────────────────────────────────────────
# Tính Pearson + Spearman trên TOÀN BỘ X_train_full (post-pipeline đầy đủ)
# ───────────────────────────────────────────────────────────────────────
# Phiên bản cũ (sai): tính trên X_c2_sorted (subset N=300 từ test) → Pearson
# off-diagonal != 0 do PCA fit trên train, project subset → mâu thuẫn với
# Hình 4.8 (heatmap full train → off-diag ≈ 0). Đã sửa: cả Pearson lẫn
# Spearman cùng tính trên FULL X_train_full để loại bỏ mâu thuẫn text/bảng.
# Pearson invariant under affine MinMax → giá trị xấp xỉ orthogonality PCA
# (max|off-diag| cỡ 10^-7 do clip + sai số FP64).
N_full = X_train_full.shape[0]
print(f"Tinh tuong quan tren TOAN BO X_train_full: N = {N_full:,} mau, {n_pcs} chieu PC")

pearson_matrix  = np.zeros((n_pcs, n_pcs))
spearman_matrix = np.zeros((n_pcs, n_pcs))
spearman_pval   = np.zeros((n_pcs, n_pcs))

for i in range(n_pcs):
    for j in range(n_pcs):
        if i == j:
            pearson_matrix[i, j]  = 1.0
            spearman_matrix[i, j] = 1.0
            spearman_pval[i, j]   = 0.0
        else:
            pearson_matrix[i, j] = np.corrcoef(X_train_full[:, i], X_train_full[:, j])[0, 1]
            rho, p = spearmanr(X_train_full[:, i], X_train_full[:, j])
            spearman_matrix[i, j] = rho
            spearman_pval[i, j]   = p

pc_labels = [f"PC{i}" for i in range(n_pcs)]

# In ma trận Pearson đầy đủ (định dạng khoa học để thấy off-diagonal ≈ 0)
off_diag_mask = ~np.eye(n_pcs, dtype=bool)
max_abs_pearson = float(np.abs(pearson_matrix[off_diag_mask]).max())
print(f"\nMa tran Pearson r (full X_train, max|off-diag| = {max_abs_pearson:.3e}):")
print("            " + "  ".join(f"{l:>14}" for l in pc_labels))
for i, row in enumerate(pearson_matrix):
    cells = []
    for j, v in enumerate(row):
        if i == j:
            cells.append(f"{v:>+14.6f}")
        else:
            cells.append(f"{v:>+14.3e}")
    print(f"  {pc_labels[i]}:  " + "  ".join(cells))

# In ma trận Spearman đầy đủ
print("\nMa tran Spearman rho (full X_train):")
print("        " + "  ".join(f"{l:>10}" for l in pc_labels))
for i, row in enumerate(spearman_matrix):
    print(f"  {pc_labels[i]}:  " + "  ".join(f"{v:>+10.4f}" for v in row))

# ───────────────────────────────────────────────────────────────────────
# BẢNG 4.8 — 6 cặp ZZ (full entanglement)
# ───────────────────────────────────────────────────────────────────────
print("\n" + "=" * 78)
print("BANG 4.8: Pearson r vs Spearman rho cho 6 cap PCA (Full X_train, N={:,})".format(N_full))
print("=" * 78)
header = f"{'Cap (i,j)':<12} {'Pearson r':>16} {'Spearman rho':>14} {'|rho - r|':>12} {'Trang thai':>14}"
print(header)
print("-" * 78)
table_rows = []
for (i, j) in ZZ_PAIRS:
    r_p  = float(pearson_matrix[i, j])
    r_s  = float(spearman_matrix[i, j])
    diff = abs(r_s - r_p)
    key  = abs(r_s) > 0.3
    status = "THEN CHOT" if key else "—"
    print(f"  PC{i}-PC{j}      {r_p:>+16.3e} {r_s:>+14.4f} {diff:>12.4f} {status:>14}")
    table_rows.append({
        "pair": f"PC{i}-PC{j}", "i": i, "j": j,
        "pearson_r": r_p, "spearman_rho": r_s,
        "abs_diff": diff, "key_pair": bool(key),
    })
print("=" * 78)

# Kiểm tra tái lập kết quả C1 (Spearman trên full train)
r_02 = float(spearman_matrix[0, 2])
r_12 = float(spearman_matrix[1, 2])
print(f"\nKiem tra tai lap C1 (Spearman tren FULL train, N={N_full:,}):")
print(f"  PC0-PC2: rho = {r_02:+.4f}  (C1 bao cao ~+0.40)")
print(f"  PC1-PC2: rho = {r_12:+.4f}  (C1 bao cao ~-0.44)")
c1_ok = abs(r_02 - 0.40) < 0.10 and abs(r_12 + 0.44) < 0.10
print(f"  Tai lap C1: {'DAT' if c1_ok else 'CHENH LECH (kiem tra config pipeline)'}")

# Ánh xạ cặp ZZ → Spearman (dùng cho narrative bridge)
print("\nAnh xa ZZ gate (full entanglement, reps=2) -> Spearman tren full train:")
print(f"{'Cap (i,j)':<12} {'Spearman rho':>14} {'|rho|>0.3?':>12} {'Trang thai'}")
print("-" * 56)
for (i, j) in ZZ_PAIRS:
    r_ij = float(spearman_matrix[i, j])
    key  = abs(r_ij) > 0.3
    status = "THEN CHOT" if key else ""
    print(f"  ({i},{j})        {r_ij:>+14.4f} {str(key):>12}   {status}")

# ───────────────────────────────────────────────────────────────────────
# Lưu PNG 1 — Pearson heatmap riêng (Hình 4.8 mới)
# ───────────────────────────────────────────────────────────────────────
fig_p, ax_p = plt.subplots(1, 1, figsize=(7, 6))
# Scale colorbar theo max|off-diag| để nhìn rõ giá trị cực nhỏ
vmax_p = max(max_abs_pearson, 1e-12)
norm_p = TwoSlopeNorm(vmin=-vmax_p, vcenter=0, vmax=vmax_p)
# Mask đường chéo (=1) bằng cách thay bằng 0 chỉ để hiển thị; vẫn ghi nhãn "1.00"
P_display = pearson_matrix.copy()
np.fill_diagonal(P_display, 0.0)
im_p = ax_p.imshow(P_display, cmap='RdBu_r', norm=norm_p, aspect='auto')
cbar_p = plt.colorbar(im_p, ax=ax_p, fraction=0.046, pad=0.04)
cbar_p.set_label("Pearson r (off-diagonal)", fontsize=10)
ax_p.set_xticks(range(n_pcs))
ax_p.set_yticks(range(n_pcs))
ax_p.set_xticklabels(pc_labels, fontsize=11)
ax_p.set_yticklabels(pc_labels, fontsize=11)
ax_p.set_title(
    f"Hinh 4.8 — Pearson Correlation (Full X_train, N={N_full:,})\n"
    f"PCA orthogonality giu chinh xac: max|off-diag| = {max_abs_pearson:.2e}",
    fontsize=11
)
# Ghi giá trị từng ô — đường chéo = 1.00, off-diag = ký hiệu khoa học
for i in range(n_pcs):
    for j in range(n_pcs):
        if i == j:
            ax_p.text(j, i, "1.00", ha='center', va='center',
                      color='black', fontsize=10, fontweight='bold')
        else:
            ax_p.text(j, i, f"{pearson_matrix[i, j]:+.2e}",
                      ha='center', va='center', color='black', fontsize=8.5)
plt.tight_layout()
out_pearson = os.path.join(REPORTS_DIR, "c2_pearson_heatmap_full.png")
plt.savefig(out_pearson, dpi=150, bbox_inches='tight')
plt.close(fig_p)
print(f"\nDa luu: {out_pearson}")

# ───────────────────────────────────────────────────────────────────────
# Lưu PNG 2 — Spearman heatmap riêng
# ───────────────────────────────────────────────────────────────────────
fig_s, ax_s = plt.subplots(1, 1, figsize=(7, 6))
norm_s = TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)
im_s = ax_s.imshow(spearman_matrix, cmap='RdBu_r', norm=norm_s, aspect='auto')
cbar_s = plt.colorbar(im_s, ax=ax_s, fraction=0.046, pad=0.04)
cbar_s.set_label("Spearman rho", fontsize=10)
ax_s.set_xticks(range(n_pcs))
ax_s.set_yticks(range(n_pcs))
ax_s.set_xticklabels(pc_labels, fontsize=11)
ax_s.set_yticklabels(pc_labels, fontsize=11)
ax_s.set_title(
    f"Spearman Correlation (Full X_train, N={N_full:,})\n"
    "Tuong quan phi tuyen ton tai sau PCA → bien minh ZZFeatureMap",
    fontsize=11
)
for i in range(n_pcs):
    for j in range(n_pcs):
        c = 'white' if abs(spearman_matrix[i, j]) > 0.5 else 'black'
        ax_s.text(j, i, f"{spearman_matrix[i, j]:+.3f}",
                  ha='center', va='center', color=c, fontsize=10, fontweight='bold')
# Khoanh khung vàng cho cặp THEN CHỐT (|rho| > 0.3)
for i in range(n_pcs):
    for j in range(n_pcs):
        if i != j and abs(spearman_matrix[i, j]) > 0.3:
            rect = plt.Rectangle((j - 0.5, i - 0.5), 1, 1,
                                 linewidth=2.5, edgecolor='gold', facecolor='none')
            ax_s.add_patch(rect)
plt.tight_layout()
out_spearman = os.path.join(REPORTS_DIR, "c2_spearman_heatmap_full.png")
plt.savefig(out_spearman, dpi=150, bbox_inches='tight')
plt.close(fig_s)
print(f"Da luu: {out_spearman}")

# ───────────────────────────────────────────────────────────────────────
# Hình ghép — 3 panel: Pearson + Spearman heatmap + ZZ network graph
# ───────────────────────────────────────────────────────────────────────
# Giữ lại variable corr_matrix để tương thích với code cũ phía dưới (nếu có)
corr_matrix = spearman_matrix
pval_matrix = spearman_pval

fig, (ax0, ax1, ax2) = plt.subplots(1, 3, figsize=(18, 5.5))
fig.suptitle(
    "Cau noi Pearson–Spearman → Topology ZZ Gate "
    f"(Full X_train, N={N_full:,})",
    fontsize=13, fontweight='bold'
)

# Panel 0: Pearson heatmap (off-diag scale ~10^-7)
P_disp = pearson_matrix.copy()
np.fill_diagonal(P_disp, 0.0)
norm0 = TwoSlopeNorm(vmin=-vmax_p, vcenter=0, vmax=vmax_p)
im0 = ax0.imshow(P_disp, cmap='RdBu_r', norm=norm0, aspect='auto')
plt.colorbar(im0, ax=ax0, fraction=0.046, pad=0.04, label="Pearson r")
ax0.set_xticks(range(n_pcs)); ax0.set_yticks(range(n_pcs))
ax0.set_xticklabels(pc_labels, fontsize=10); ax0.set_yticklabels(pc_labels, fontsize=10)
ax0.set_title(f"Pearson r\n(max|off-diag| = {max_abs_pearson:.2e})", fontsize=10)
for i in range(n_pcs):
    for j in range(n_pcs):
        if i == j:
            ax0.text(j, i, "1.00", ha='center', va='center', fontsize=9, fontweight='bold')
        else:
            ax0.text(j, i, f"{pearson_matrix[i, j]:+.1e}",
                     ha='center', va='center', fontsize=7.5)

# Panel 1: Heatmap Spearman
norm = TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)
im = ax1.imshow(corr_matrix, cmap='RdBu_r', norm=norm, aspect='auto')
plt.colorbar(im, ax=ax1, fraction=0.046, pad=0.04, label="Spearman r")
ax1.set_xticks(range(n_pcs)); ax1.set_yticks(range(n_pcs))
ax1.set_xticklabels(pc_labels, fontsize=10); ax1.set_yticklabels(pc_labels, fontsize=10)
ax1.set_title("Spearman rho\n(PCA component sau MinMax [0, pi])", fontsize=10)
for i in range(n_pcs):
    for j in range(n_pcs):
        c = 'white' if abs(corr_matrix[i, j]) > 0.5 else 'black'
        ax1.text(j, i, f"{corr_matrix[i, j]:+.2f}",
                 ha='center', va='center', color=c, fontsize=9, fontweight='bold')
for i in range(n_pcs):
    for j in range(n_pcs):
        if i != j and abs(corr_matrix[i, j]) > 0.3:
            rect = plt.Rectangle((j - 0.5, i - 0.5), 1, 1,
                                 linewidth=2.5, edgecolor='gold', facecolor='none')
            ax1.add_patch(rect)

# Panel 2: Sơ đồ mạng/chord (giữ nguyên hành vi cũ — dùng corr_matrix = Spearman)
node_pos = {
    0: np.array([0.0, 1.0]),
    1: np.array([1.0, 1.0]),
    2: np.array([0.0, 0.0]),
    3: np.array([1.0, 0.0]),
}
ax2.set_xlim(-0.4, 1.4); ax2.set_ylim(-0.4, 1.4)
ax2.set_aspect('equal'); ax2.axis('off')
ax2.set_title("So do Mang ZZ Gate\n(Do rong canh ∝ |Spearman r|; do=+, xanh=-)", fontsize=10)

for (i, j) in ZZ_PAIRS:
    r_ij = float(corr_matrix[i, j])
    lw    = abs(r_ij) * 8
    color = '#d62728' if r_ij > 0 else '#1f77b4'
    alpha = 0.4 + 0.5 * abs(r_ij)
    xi, yi = node_pos[i]; xj, yj = node_pos[j]
    ax2.plot([xi, xj], [yi, yj], color=color, linewidth=lw, alpha=alpha, zorder=1)
    mx, my = (xi + xj) / 2, (yi + yj) / 2
    if abs(r_ij) > 0.3:
        ax2.text(mx, my, f"r={r_ij:+.2f}", ha='center', va='center',
                 fontsize=7.5, fontweight='bold', color=color,
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

for node_id, pos in node_pos.items():
    ax2.scatter(*pos, s=800, c='#2ca02c', edgecolors='black', linewidth=1.5, zorder=3)
    ax2.text(pos[0], pos[1], f"PC{node_id}", ha='center', va='center',
             fontsize=9, fontweight='bold', color='white', zorder=4)

legend_elements = [
    mpatches.Patch(color='#d62728', label='Tuong quan duong'),
    mpatches.Patch(color='#1f77b4', label='Tuong quan am'),
    mpatches.Patch(color='gold',    label='|rho| > 0.3 (Cap THEN CHOT)'),
]
ax2.legend(handles=legend_elements, loc='lower center', fontsize=8,
           bbox_to_anchor=(0.5, -0.15))

plt.tight_layout()
out_path = os.path.join(REPORTS_DIR, "c2_spearman_bridge.png")
plt.savefig(out_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"Da luu: {out_path}")
display(Image(filename=out_path))
'''


def split_source_lines(text: str) -> list[str]:
    """Chia chuỗi thành danh sách dòng giữ nguyên ký tự '\\n' cuối mỗi dòng (chuẩn ipynb)."""
    lines = text.splitlines(keepends=True)
    return lines


def main():
    with NB_PATH.open("r", encoding="utf-8") as f:
        nb = json.load(f)

    cell24 = nb["cells"][24]
    assert cell24["cell_type"] == "code", f"Cell 24 phai la code, nhan duoc {cell24['cell_type']}"
    cell24["source"] = split_source_lines(NEW_SOURCE)
    cell24["outputs"] = []
    cell24["execution_count"] = None

    with NB_PATH.open("w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
        f.write("\n")

    print(f"Da patch cell 24 cua {NB_PATH.name}")
    print(f"Source moi: {sum(len(s) for s in cell24['source'])} ky tu")


if __name__ == "__main__":
    main()
