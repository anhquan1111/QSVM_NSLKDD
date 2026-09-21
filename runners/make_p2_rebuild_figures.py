"""Hinh cho ban dung lai cua Paper 2.

    python runners/make_p2_rebuild_figures.py
    -> paper/paper2_rebuild/figs/{fig1_identity,fig2_paired,fig3_platt,
                                  fig4_refarm}.{pdf,png}

Bang mau ke thua make_paper1_figures.py (da qua scripts/validate_palette.js).
Chi so chinh la ECE tren TOAN tap test; xem dau analyze_p2_rebuild.py.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import numpy as np
import pandas as pd

mpl.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
NSL = ROOT / "results" / "nslkdd" / "p2_rebuild"
UNSW = ROOT / "results" / "unsw" / "p2_rebuild"
OUT = ROOT / "paper" / "paper2_rebuild" / "figs"
OUT.mkdir(parents=True, exist_ok=True)

SURFACE = "#fcfcfb"; INK = "#0b0b0b"; INK_2 = "#52514e"; INK_MUTED = "#7b7a75"
GRID = "#e4e3dd"; SHADE = "#f0efe9"
BLUE = "#2a78d6"; ORANGE = "#eb6834"; AQUA = "#1baf7a"; VIOLET = "#4a3aa7"
NEUTRAL = "#b8b7b0"

STYLE = {
    "QSVM":         dict(color=BLUE,      marker="o", label="QSVM-ZZ"),
    "SVM-RBF":      dict(color="#6f6e69", marker="v", label="SVM-RBF"),
    "MLP":          dict(color=VIOLET,    marker="s", label="MLP"),
    "XGBoost":      dict(color=ORANGE,    marker="^", label="XGBoost"),
    "RandomForest": dict(color=AQUA,      marker="D", label="Random forest"),
}
ORDER = list(STYLE)
SETTINGS = [("NSL-KDD/full", "NSL-KDD\n4 qubits"),
            ("UNSW/4qb", "UNSW-NB15\n4 qubits"),
            ("UNSW/6qb", "UNSW-NB15\n6 qubits")]

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "font.family": "DejaVu Sans", "font.size": 8,
    "axes.labelsize": 8.5, "axes.titlesize": 9, "axes.titleweight": "bold",
    "axes.labelcolor": INK_2, "axes.edgecolor": GRID, "axes.linewidth": 0.8,
    "text.color": INK, "xtick.color": INK_2, "ytick.color": INK_2,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
    "legend.frameon": False, "grid.color": GRID, "grid.linewidth": 0.6,
    "savefig.bbox": "tight", "savefig.dpi": 400, "pdf.fonttype": 42,
})


def tidy(ax, axis="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.set_axisbelow(True)
    ax.grid(True, axis=axis, color=GRID, lw=0.6)
    ax.tick_params(length=2.5, width=0.7)


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}")
    plt.close(fig)
    print(f"  -> {OUT.relative_to(ROOT).as_posix()}/{name}.pdf  (+ .png)")


def load_long():
    n = pd.read_csv(NSL / "p2_rebuild_per_run.csv")
    n["setting"] = "NSL-KDD/" + n.test_set.map(
        {"full_kddtest_plus": "full", "sample100_cu": "sample100"})
    u = pd.read_csv(UNSW / "p2_unsw_per_run.csv")
    u["setting"] = "UNSW/" + u.n_qubits.astype(str) + "qb"
    return pd.concat([n, u], ignore_index=True)


def fig1_identity():
    """Tren tap con mot lop, ECE chinh la 1 - trung binh(p). Va ve doi lap."""
    idf = pd.read_csv(NSL / "p2_rebuild_identity.csv")
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(7.16, 2.75),
                                 gridspec_kw=dict(wspace=0.32))

    lim = [idf.ece_rare.min() - 0.03, idf.ece_rare.max() + 0.03]
    ax.plot(lim, lim, color=INK_MUTED, lw=1.0, ls=(0, (4, 2)), zorder=2)
    for model in ORDER:
        s = idf[idf.model == model]
        st = STYLE[model]
        ax.scatter(s.one_minus_mean_p, s.ece_rare, s=26, color=st["color"],
                   marker=st["marker"], edgecolor=SURFACE, linewidth=0.5,
                   label=st["label"], zorder=5)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel(r"$1-\bar{p}$  on the rare subset")
    ax.set_ylabel(r"measured $\mathrm{ECE}$")
    ax.set_title("(a)  On a single-class subset they are\nthe same number",
                 loc="left", fontsize=8.5)
    ax.text(0.04, 0.93, f"max deviation {idf.abs_dev.max():.1e}",
            transform=ax.transAxes, fontsize=7, color=INK_MUTED, va="top")
    tidy(ax)
    ax.legend(loc="lower right", borderpad=0.2, labelspacing=0.28,
              handletextpad=0.4)

    # (b) do tan cua acc tung bin tren TOAN tap test. Tren tap hiem no bang 0
    # theo dinh nghia nen khong ve thanh -- ve thanh khong se cho ra nhung
    # thanh vo hinh, con tinh hon la noi thang bang mot dong chu.
    y = np.arange(len(ORDER))
    stds = [idf[idf.model == m].acc_bin_std.mean() for m in ORDER]
    bx.barh(y, stds, height=0.60, color=[STYLE[m]["color"] for m in ORDER],
            alpha=0.9, zorder=4)
    for i, v in enumerate(stds):
        bx.text(v + 0.008, i, f"{v:.3f}", va="center", fontsize=7,
                color=INK_2, zorder=6)
    bx.axvline(0, color=ORANGE, lw=1.6, zorder=6)
    bx.text(0.008, len(ORDER) - 0.42,
            "rare subset: exactly 0 for every model,\nby construction",
            fontsize=6.8, color=ORANGE, va="center", ha="left", zorder=7)
    bx.set_yticks(y); bx.set_yticklabels([STYLE[m]["label"] for m in ORDER])
    bx.invert_yaxis(); bx.set_xlim(0, max(stds) * 1.30)
    bx.set_xlabel("std. of per-bin accuracy, full test split")
    bx.set_title("(b)  Calibration is only measurable\nwhere accuracy varies",
                 loc="left", fontsize=8.5)
    tidy(bx, axis="x")
    save(fig, "fig1_identity")


def fig2_paired():
    st = pd.read_csv(NSL / "p2_rebuild_pairwise.csv")
    st = st[st.metric == "ece_full"]
    order = ["SVM-RBF", "MLP", "XGBoost", "RandomForest"]
    fig, axes = plt.subplots(1, 3, figsize=(7.16, 2.4), sharex=True,
                             gridspec_kw=dict(wspace=0.10))
    for ax, (key, title) in zip(axes, SETTINGS):
        s = st[st.setting == key].set_index("baseline").loc[order].reset_index()
        for i, r in s.iterrows():
            sig = r["holm_p"] < 0.05
            col = BLUE if (sig and r["mean_delta"] < 0) else (
                ORANGE if sig else NEUTRAL)
            ax.plot([r["ci_low"], r["ci_high"]], [i, i], color=col, lw=2.0,
                    solid_capstyle="round", zorder=4)
            ax.plot([r["mean_delta"]], [i], marker="o", ms=6.0, color=col,
                    mec=SURFACE, mew=0.8, zorder=5)
        ax.axvline(0, color=INK_MUTED, lw=0.9, ls=(0, (3, 2)), zorder=2)
        ax.set_yticks(range(len(order)))
        ax.set_yticklabels([STYLE[b]["label"] for b in order]
                           if ax is axes[0] else [])
        ax.set_title(title, loc="left", fontsize=8.5)
        # Phai dao TUNG truc: sharex khong chia se truc y, nen chi dao truc
        # dau se lam hai panel kia chay nguoc so voi nhan ben trai.
        ax.invert_yaxis()
        tidy(ax, axis="x")
    axes[1].set_xlabel(r"$\Delta\mathrm{ECE}$:  QSVM $-$ baseline"
                       "   (negative favours QSVM)")
    save(fig, "fig2_paired")


def fig3_platt():
    df = pd.read_csv(NSL / "p2_rebuild_calibrators.csv")
    g = df.groupby(["model", "calibrator"]).ece_full.mean()
    cals = [("none", "none", NEUTRAL), ("platt", "Platt", BLUE),
            ("isotonic", "isotonic", VIOLET), ("temperature", "temperature", AQUA)]
    fig, ax = plt.subplots(figsize=(3.48, 2.8))
    y = np.arange(len(ORDER)); h = 0.20
    for j, (key, lab, col) in enumerate(cals):
        ax.barh(y + (j - 1.5) * h, [g[(m, key)] for m in ORDER], height=h,
                color=col, alpha=0.9, label=lab, zorder=4)
    for i, m in enumerate(ORDER):
        best = min(g[(m, k)] for k, _, _ in cals)
        worst = max(g[(m, k)] for k, _, _ in cals)
        helped = g[(m, "none")] > best
        ax.text(worst + 0.006, i, "helped" if helped else "no gain",
                va="center", fontsize=6.6,
                color=BLUE if helped else ORANGE, zorder=6)
    ax.set_yticks(y); ax.set_yticklabels([STYLE[m]["label"] for m in ORDER])
    ax.invert_yaxis(); ax.set_xlim(0, 0.265)
    ax.set_xlabel(r"$\mathrm{ECE}$ on the full test split")
    ax.set_title("Recalibration helps the quantum\nkernel and nothing else",
                 loc="left")
    tidy(ax, axis="x")
    ax.legend(loc="lower right", borderpad=0.2, labelspacing=0.25, ncol=2,
              columnspacing=0.8)
    save(fig, "fig3_platt")


def fig4_refarm():
    ref = pd.read_csv(NSL / "p2_rebuild_refarm.csv")
    reps = ["pca4", "k20", "all122"]
    dims = {r: int(ref[ref["repr"] == r].n_features.iloc[0]) for r in reps}
    labels = [f"{dims[r]}-d" for r in reps]
    x = np.arange(len(reps))
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(7.16, 2.5),
                                 gridspec_kw=dict(wspace=0.30))
    for axis, col, title, better in (
            (ax, "auc_pr", "(a)  Ranking: AUC-PR", "higher is better"),
            (bx, "ece_full", r"(b)  Calibration: $\mathrm{ECE}$",
             "lower is better")):
        for model in ("RandomForest", "XGBoost"):
            s = ref[ref.model == model].groupby("repr")[col]
            st = STYLE[model]
            axis.errorbar(x, [s.mean()[r] for r in reps],
                          yerr=[s.std()[r] for r in reps],
                          color=st["color"], marker=st["marker"], ms=6.0,
                          lw=2.0, mec=SURFACE, mew=0.7, capsize=2.5,
                          label=st["label"], zorder=5)
        axis.set_xticks(x); axis.set_xticklabels(labels)
        axis.set_xlabel("Representation given to the trees")
        axis.set_title(f"{title}\n{better}", loc="left", fontsize=8.5)
        axis.set_xlim(-0.35, len(reps) - 0.65)
        tidy(axis)
    ax.legend(loc="lower right", borderpad=0.2, labelspacing=0.3)
    save(fig, "fig4_refarm")


def main() -> int:
    print("Hinh cho ban dung lai Paper 2:")
    fig1_identity()
    fig2_paired()
    fig3_platt()
    fig4_refarm()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
