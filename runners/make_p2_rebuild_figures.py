"""Hinh cho ban dung lai cua Paper 2.

    python runners/make_p2_rebuild_figures.py
    -> paper/paper2_rebuild/figs/{fig1_test_size,fig2_paired,fig3_platt}.{pdf,png}

Bang mau ke thua make_paper1_figures.py (da qua scripts/validate_palette.js).
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib as mpl
import numpy as np
import pandas as pd

mpl.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "results" / "nslkdd" / "p2_rebuild"
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


def fig1_test_size():
    """Cai tap test nho lam doi thu hang -- day la dong gop phuong phap."""
    df = pd.read_csv(IN / "p2_rebuild_per_run.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.16, 2.9), sharey=True,
                             gridspec_kw=dict(wspace=0.08))
    panels = [("sample100_cu", "(a)  Test set of the submitted version"),
              ("full_kddtest_plus", "(b)  Full KDDTest+")]
    for ax, (key, title) in zip(axes, panels):
        sub = df[df.test_set == key]
        n_rare = int(sub.n_rare.iloc[0])
        means = sub.groupby("model").ece_rare.mean()
        sds = sub.groupby("model").ece_rare.std()
        y = np.arange(len(ORDER))
        ax.barh(y, [means[m] for m in ORDER], height=0.62,
                color=[STYLE[m]["color"] for m in ORDER], alpha=0.88, zorder=4)
        ax.errorbar([means[m] for m in ORDER], y,
                    xerr=[sds[m] for m in ORDER], fmt="none",
                    ecolor=INK_MUTED, elinewidth=0.9, capsize=2.5, zorder=5)
        for i, m in enumerate(ORDER):
            ax.text(means[m] + sds[m] + 0.012, i, f"{means[m]:.3f}",
                    va="center", fontsize=7, color=INK_2, zorder=6)
        ax.set_yticks(y)
        ax.set_yticklabels([STYLE[m]["label"] for m in ORDER])
        ax.set_xlim(0, 0.95)
        ax.set_xlabel(r"$\mathrm{ECE}_{\mathrm{rare}}$  (lower is better)")
        ax.set_title(f"{title}\n{n_rare} rare test samples", loc="left",
                     fontsize=8.5)
        tidy(ax, axis="x")
    axes[0].invert_yaxis()      # sharey: chi duoc dao MOT lan cho ca hai truc
    save(fig, "fig1_test_size")


def fig2_paired():
    """Hieu bat cap kem Holm, tren tap test day du."""
    st = pd.read_csv(IN / "p2_rebuild_pairwise.csv")
    st = st[st.test_set == "full_kddtest_plus"]
    fig, axes = plt.subplots(1, 2, figsize=(7.16, 2.5),
                             gridspec_kw=dict(wspace=0.46))
    for ax, metric, title in zip(
            axes, ("ece_rare", "brier_rare"),
            (r"(a)  $\Delta\mathrm{ECE}_{\mathrm{rare}}$",
             r"(b)  $\Delta\mathrm{Brier}_{\mathrm{rare}}$")):
        s = st[st.metric == metric].set_index("baseline").loc[
            ["SVM-RBF", "MLP", "XGBoost", "RandomForest"]].reset_index()
        y = np.arange(len(s))
        for i, r in s.iterrows():
            sig = r["holm_p"] < 0.05
            col = BLUE if (sig and r["mean_delta"] < 0) else (
                ORANGE if sig else NEUTRAL)
            ax.plot([r["ci_low"], r["ci_high"]], [i, i], color=col,
                    lw=2.0, solid_capstyle="round", zorder=4)
            ax.plot([r["mean_delta"]], [i], marker="o", ms=6.5, color=col,
                    mec=SURFACE, mew=0.8, zorder=5)
            ax.text(r["ci_high"] + 0.008, i,
                    f"{'*' if sig else ''}{r['holm_p']:.3f}",
                    va="center", fontsize=6.6, color=INK_2, zorder=6)
        ax.axvline(0, color=INK_MUTED, lw=0.9, ls=(0, (3, 2)), zorder=2)
        ax.set_yticks(y)
        ax.set_yticklabels([STYLE[b]["label"] for b in s["baseline"]])
        ax.invert_yaxis()
        ax.set_xlabel("QSVM $-$ baseline  (negative favours QSVM)")
        ax.set_title(title, loc="left")
        tidy(ax, axis="x")
    save(fig, "fig2_paired")


def fig3_platt():
    """Platt giup DUY NHAT kernel luong tu."""
    df = pd.read_csv(IN / "p2_rebuild_platt.csv")
    g = df.groupby("model")[["ece_before", "ece_after"]].mean()
    fig, ax = plt.subplots(figsize=(3.48, 2.7))
    y = np.arange(len(ORDER)); h = 0.34
    ax.barh(y - h / 2, [g.loc[m, "ece_before"] for m in ORDER], height=h,
            color=NEUTRAL, label="before Platt", zorder=4)
    ax.barh(y + h / 2, [g.loc[m, "ece_after"] for m in ORDER], height=h,
            color=[STYLE[m]["color"] for m in ORDER], alpha=0.9,
            label="after Platt", zorder=4)
    for i, m in enumerate(ORDER):
        d = g.loc[m, "ece_before"] - g.loc[m, "ece_after"]
        ax.text(max(g.loc[m, "ece_before"], g.loc[m, "ece_after"]) + 0.006, i,
                f"{d:+.3f}", va="center", fontsize=6.8,
                color=BLUE if d > 0 else ORANGE, zorder=6)
    ax.set_yticks(y); ax.set_yticklabels([STYLE[m]["label"] for m in ORDER])
    ax.invert_yaxis(); ax.set_xlim(0, 0.255)
    ax.set_xlabel(r"$\mathrm{ECE}$ on full test set")
    ax.set_title("Platt helps only the quantum kernel", loc="left")
    tidy(ax, axis="x")
    ax.legend(loc="lower right", borderpad=0.2, labelspacing=0.3)
    save(fig, "fig3_platt")


def fig4_refarm():
    """Cho cay du dac trung: xep hang tot len, hieu chinh te di."""
    ref = pd.read_csv(IN / "p2_rebuild_refarm.csv")
    reps = ["pca4", "k20", "all122"]
    dims = {r: int(ref[ref["repr"] == r].n_features.iloc[0]) for r in reps}
    labels = [f"{dims[r]}-d" for r in reps]
    x = np.arange(len(reps))

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(7.16, 2.5),
                                 gridspec_kw=dict(wspace=0.30))
    for axis, col, title, better in (
            (ax, "auc_pr", "(a)  Ranking: AUC-PR", "higher is better"),
            (bx, "ece_rare", r"(b)  Reliability: $\mathrm{ECE}_{\mathrm{rare}}$",
             "lower is better")):
        for model in ("RandomForest", "XGBoost"):
            s = ref[ref.model == model].groupby("repr")[col].mean()
            e = ref[ref.model == model].groupby("repr")[col].std()
            st = STYLE[model]
            axis.errorbar(x, [s[r] for r in reps], yerr=[e[r] for r in reps],
                          color=st["color"], marker=st["marker"], ms=6.0,
                          lw=2.0, mec=SURFACE, mew=0.7, capsize=2.5,
                          label=st["label"], zorder=5)
        axis.set_xticks(x)
        axis.set_xticklabels(labels)
        axis.set_xlabel("Representation given to the trees")
        axis.set_title(f"{title}\n{better}", loc="left", fontsize=8.5)
        axis.set_xlim(-0.35, len(reps) - 0.65)
        tidy(axis)
    ax.legend(loc="lower right", borderpad=0.2, labelspacing=0.3)
    save(fig, "fig4_refarm")


def main() -> int:
    print("Hinh cho ban dung lai Paper 2:")
    fig1_test_size()
    fig2_paired()
    fig3_platt()
    fig4_refarm()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
