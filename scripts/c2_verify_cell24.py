"""Standalone reproduction của cell 24 (sau khi patch) — KHÔNG cần chạy notebook.

Tái dựng X_train_full qua pipeline OHE→SelectKBest→PCA→MinMax→clip[0, π], rồi
tính Pearson + Spearman trên FULL X_train_full. Sinh ra:
  - reports/c2_pearson_heatmap_full.png      (Hình 4.8 mới)
  - reports/c2_spearman_heatmap_full.png
  - reports/c2_spearman_bridge.png           (3-panel ghép)
  - In Bảng 4.8 ra stdout (paste vào báo cáo Word).

Dùng để verify nhanh trước khi tốn 15-30 phút chạy `jupyter nbconvert --execute`.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm
from scipy.stats import spearmanr

# ── Constants (sao chép từ notebook để đảm bảo bit-exact reproducibility) ──
N_QUBITS = 4
RANDOM_STATE = 42

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = ROOT / "data" / "processed_data"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

LABEL_COLS = ["label", "label_binary", "label_multiclass", "attack_category"]
ZZ_PAIRS = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]


def load_X_train_full() -> np.ndarray:
    """Tái dựng X_train_full chính xác như cell 13 của notebook C2."""
    train_df = pd.read_csv(PROCESSED_DATA_DIR / "NSL_KDD_Train_Cleaned.csv")
    selector = joblib.load(MODELS_DIR / "feature_selector_k20.joblib")
    pca = joblib.load(MODELS_DIR / "pca_4components.joblib")
    scaler = joblib.load(MODELS_DIR / "scaler_minmax_pi.joblib")

    feature_cols = [c for c in train_df.columns if c not in LABEL_COLS]
    X_raw = train_df[feature_cols].values.astype(np.float64)

    X_sel = selector.transform(X_raw)
    X_pca = pca.transform(X_sel)
    X_full = np.clip(scaler.transform(X_pca), 0, np.pi)
    assert X_full.shape[1] == N_QUBITS
    return X_full


def compute_correlations(X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Tính ma trận Pearson + Spearman (rho, p-value) trên toàn bộ X."""
    n_pcs = X.shape[1]
    pearson = np.zeros((n_pcs, n_pcs))
    spearman = np.zeros((n_pcs, n_pcs))
    pvals = np.zeros((n_pcs, n_pcs))
    for i in range(n_pcs):
        for j in range(n_pcs):
            if i == j:
                pearson[i, j] = 1.0
                spearman[i, j] = 1.0
                pvals[i, j] = 0.0
            else:
                pearson[i, j] = np.corrcoef(X[:, i], X[:, j])[0, 1]
                rho, p = spearmanr(X[:, i], X[:, j])
                spearman[i, j] = rho
                pvals[i, j] = p
    return pearson, spearman, pvals


def print_matrices(pearson: np.ndarray, spearman: np.ndarray, n_full: int) -> float:
    n_pcs = pearson.shape[0]
    pc_labels = [f"PC{i}" for i in range(n_pcs)]
    off_diag = ~np.eye(n_pcs, dtype=bool)
    max_abs_pearson = float(np.abs(pearson[off_diag]).max())

    print(f"\nMa tran Pearson r (full X_train, max|off-diag| = {max_abs_pearson:.3e}):")
    print("            " + "  ".join(f"{l:>14}" for l in pc_labels))
    for i, row in enumerate(pearson):
        cells = []
        for j, v in enumerate(row):
            cells.append(f"{v:>+14.6f}" if i == j else f"{v:>+14.3e}")
        print(f"  {pc_labels[i]}:  " + "  ".join(cells))

    print("\nMa tran Spearman rho (full X_train):")
    print("        " + "  ".join(f"{l:>10}" for l in pc_labels))
    for i, row in enumerate(spearman):
        print(f"  {pc_labels[i]}:  " + "  ".join(f"{v:>+10.4f}" for v in row))

    return max_abs_pearson


def print_table_4_8(pearson: np.ndarray, spearman: np.ndarray, n_full: int):
    print("\n" + "=" * 78)
    print(f"BANG 4.8: Pearson r vs Spearman rho cho 6 cap PCA (Full X_train, N={n_full:,})")
    print("=" * 78)
    print(f"{'Cap (i,j)':<12} {'Pearson r':>16} {'Spearman rho':>14} {'|rho - r|':>12} {'Trang thai':>14}")
    print("-" * 78)
    for (i, j) in ZZ_PAIRS:
        r_p = float(pearson[i, j])
        r_s = float(spearman[i, j])
        diff = abs(r_s - r_p)
        status = "THEN CHOT" if abs(r_s) > 0.3 else "—"
        print(f"  PC{i}-PC{j}      {r_p:>+16.3e} {r_s:>+14.4f} {diff:>12.4f} {status:>14}")
    print("=" * 78)


def save_pearson_heatmap(pearson: np.ndarray, max_abs_off: float, n_full: int):
    n_pcs = pearson.shape[0]
    pc_labels = [f"PC{i}" for i in range(n_pcs)]
    fig, ax = plt.subplots(figsize=(7, 6))
    vmax = max(max_abs_off, 1e-12)
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    P_disp = pearson.copy()
    np.fill_diagonal(P_disp, 0.0)
    im = ax.imshow(P_disp, cmap="RdBu_r", norm=norm, aspect="auto")
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Pearson r (off-diagonal)", fontsize=10)
    ax.set_xticks(range(n_pcs)); ax.set_yticks(range(n_pcs))
    ax.set_xticklabels(pc_labels, fontsize=11); ax.set_yticklabels(pc_labels, fontsize=11)
    ax.set_title(
        f"Hinh 4.8 — Pearson Correlation (Full X_train, N={n_full:,})\n"
        f"PCA orthogonality giu chinh xac: max|off-diag| = {max_abs_off:.2e}",
        fontsize=11,
    )
    for i in range(n_pcs):
        for j in range(n_pcs):
            if i == j:
                ax.text(j, i, "1.00", ha="center", va="center", fontsize=10, fontweight="bold")
            else:
                ax.text(j, i, f"{pearson[i, j]:+.2e}", ha="center", va="center", fontsize=8.5)
    plt.tight_layout()
    out = REPORTS_DIR / "c2_pearson_heatmap_full.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Da luu: {out}")


def save_spearman_heatmap(spearman: np.ndarray, n_full: int):
    n_pcs = spearman.shape[0]
    pc_labels = [f"PC{i}" for i in range(n_pcs)]
    fig, ax = plt.subplots(figsize=(7, 6))
    norm = TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)
    im = ax.imshow(spearman, cmap="RdBu_r", norm=norm, aspect="auto")
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Spearman rho", fontsize=10)
    ax.set_xticks(range(n_pcs)); ax.set_yticks(range(n_pcs))
    ax.set_xticklabels(pc_labels, fontsize=11); ax.set_yticklabels(pc_labels, fontsize=11)
    ax.set_title(
        f"Spearman Correlation (Full X_train, N={n_full:,})\n"
        "Tuong quan phi tuyen ton tai sau PCA → bien minh ZZFeatureMap",
        fontsize=11,
    )
    for i in range(n_pcs):
        for j in range(n_pcs):
            c = "white" if abs(spearman[i, j]) > 0.5 else "black"
            ax.text(j, i, f"{spearman[i, j]:+.3f}", ha="center", va="center",
                    color=c, fontsize=10, fontweight="bold")
    for i in range(n_pcs):
        for j in range(n_pcs):
            if i != j and abs(spearman[i, j]) > 0.3:
                rect = plt.Rectangle((j - 0.5, i - 0.5), 1, 1,
                                     linewidth=2.5, edgecolor="gold", facecolor="none")
                ax.add_patch(rect)
    plt.tight_layout()
    out = REPORTS_DIR / "c2_spearman_heatmap_full.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Da luu: {out}")


def save_bridge_3panel(pearson: np.ndarray, spearman: np.ndarray,
                       max_abs_off: float, n_full: int):
    n_pcs = pearson.shape[0]
    pc_labels = [f"PC{i}" for i in range(n_pcs)]
    fig, (ax0, ax1, ax2) = plt.subplots(1, 3, figsize=(18, 5.5))
    fig.suptitle(
        f"Cau noi Pearson–Spearman → Topology ZZ Gate (Full X_train, N={n_full:,})",
        fontsize=13, fontweight="bold",
    )

    # Panel 0: Pearson
    P_disp = pearson.copy(); np.fill_diagonal(P_disp, 0.0)
    vmax = max(max_abs_off, 1e-12)
    norm0 = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    im0 = ax0.imshow(P_disp, cmap="RdBu_r", norm=norm0, aspect="auto")
    plt.colorbar(im0, ax=ax0, fraction=0.046, pad=0.04, label="Pearson r")
    ax0.set_xticks(range(n_pcs)); ax0.set_yticks(range(n_pcs))
    ax0.set_xticklabels(pc_labels, fontsize=10); ax0.set_yticklabels(pc_labels, fontsize=10)
    ax0.set_title(f"Pearson r\n(max|off-diag| = {max_abs_off:.2e})", fontsize=10)
    for i in range(n_pcs):
        for j in range(n_pcs):
            if i == j:
                ax0.text(j, i, "1.00", ha="center", va="center", fontsize=9, fontweight="bold")
            else:
                ax0.text(j, i, f"{pearson[i, j]:+.1e}", ha="center", va="center", fontsize=7.5)

    # Panel 1: Spearman heatmap
    norm = TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)
    im = ax1.imshow(spearman, cmap="RdBu_r", norm=norm, aspect="auto")
    plt.colorbar(im, ax=ax1, fraction=0.046, pad=0.04, label="Spearman r")
    ax1.set_xticks(range(n_pcs)); ax1.set_yticks(range(n_pcs))
    ax1.set_xticklabels(pc_labels, fontsize=10); ax1.set_yticklabels(pc_labels, fontsize=10)
    ax1.set_title("Spearman rho\n(PCA component sau MinMax [0, pi])", fontsize=10)
    for i in range(n_pcs):
        for j in range(n_pcs):
            c = "white" if abs(spearman[i, j]) > 0.5 else "black"
            ax1.text(j, i, f"{spearman[i, j]:+.2f}", ha="center", va="center",
                     color=c, fontsize=9, fontweight="bold")
    for i in range(n_pcs):
        for j in range(n_pcs):
            if i != j and abs(spearman[i, j]) > 0.3:
                rect = plt.Rectangle((j - 0.5, i - 0.5), 1, 1,
                                     linewidth=2.5, edgecolor="gold", facecolor="none")
                ax1.add_patch(rect)

    # Panel 2: ZZ network graph
    node_pos = {0: np.array([0.0, 1.0]), 1: np.array([1.0, 1.0]),
                2: np.array([0.0, 0.0]), 3: np.array([1.0, 0.0])}
    ax2.set_xlim(-0.4, 1.4); ax2.set_ylim(-0.4, 1.4)
    ax2.set_aspect("equal"); ax2.axis("off")
    ax2.set_title("So do Mang ZZ Gate\n(Do rong canh ∝ |Spearman r|; do=+, xanh=-)", fontsize=10)
    for (i, j) in ZZ_PAIRS:
        r_ij = float(spearman[i, j])
        lw = abs(r_ij) * 8
        color = "#d62728" if r_ij > 0 else "#1f77b4"
        alpha = 0.4 + 0.5 * abs(r_ij)
        xi, yi = node_pos[i]; xj, yj = node_pos[j]
        ax2.plot([xi, xj], [yi, yj], color=color, linewidth=lw, alpha=alpha, zorder=1)
        mx, my = (xi + xj) / 2, (yi + yj) / 2
        if abs(r_ij) > 0.3:
            ax2.text(mx, my, f"r={r_ij:+.2f}", ha="center", va="center",
                     fontsize=7.5, fontweight="bold", color=color,
                     bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))
    for node_id, pos in node_pos.items():
        ax2.scatter(*pos, s=800, c="#2ca02c", edgecolors="black", linewidth=1.5, zorder=3)
        ax2.text(pos[0], pos[1], f"PC{node_id}", ha="center", va="center",
                 fontsize=9, fontweight="bold", color="white", zorder=4)
    legend_elements = [
        mpatches.Patch(color="#d62728", label="Tuong quan duong"),
        mpatches.Patch(color="#1f77b4", label="Tuong quan am"),
        mpatches.Patch(color="gold", label="|rho| > 0.3 (Cap THEN CHOT)"),
    ]
    ax2.legend(handles=legend_elements, loc="lower center", fontsize=8,
               bbox_to_anchor=(0.5, -0.15))

    plt.tight_layout()
    out = REPORTS_DIR / "c2_spearman_bridge.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Da luu: {out}")


def main():
    # Đảm bảo stdout là UTF-8 trên Windows để in được các ký tự Unicode
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    print("Loading X_train_full ...")
    X_train_full = load_X_train_full()
    n_full = X_train_full.shape[0]
    print(f"  X_train_full shape = {X_train_full.shape}, "
          f"range [{X_train_full.min():.4f}, {X_train_full.max():.4f}]")

    print("\nComputing Pearson + Spearman ...")
    pearson, spearman, _ = compute_correlations(X_train_full)

    max_abs_off = print_matrices(pearson, spearman, n_full)
    print_table_4_8(pearson, spearman, n_full)

    # Kiểm tra tái lập kết quả Spearman C1
    r_02 = float(spearman[0, 2])
    r_12 = float(spearman[1, 2])
    print(f"\nKiem tra tai lap C1 (Spearman tren FULL train, N={n_full:,}):")
    print(f"  PC0-PC2: rho = {r_02:+.4f}  (C1 bao cao ~+0.40)")
    print(f"  PC1-PC2: rho = {r_12:+.4f}  (C1 bao cao ~-0.44)")

    print("\nSaving figures ...")
    save_pearson_heatmap(pearson, max_abs_off, n_full)
    save_spearman_heatmap(spearman, n_full)
    save_bridge_3panel(pearson, spearman, max_abs_off, n_full)
    print("\nDONE.")


if __name__ == "__main__":
    main()
