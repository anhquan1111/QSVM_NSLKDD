"""Sinh cac hinh cho ban revision cua paper 1 (TETC-2026-05-0252).

Chay:  python runners/make_paper1_figures.py
Xuat:  paper/paper1/figs_revision/{fig5,fig9,fig10,fig11}.{pdf,png}

Ghi chu ve mau. Bang mau da qua `scripts/validate_palette.js` cua skill dataviz:
bon slot duoc nhan manh (blue/orange/aqua/violet) dat moi nguong all-pairs o
che do sang (CVD dE 9.2, normal-vision dE 16.3). Ba duong SVM co dien ha xuong
ba muc xam khac nhau, moi duong mot kieu net va mot marker rieng, nen danh tinh
khong bao gio chi dua vao mau -- dieu bat buoc voi ban in den trang.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy import stats

mpl.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper" / "paper1" / "figs_revision"
OUT.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Token
# --------------------------------------------------------------------------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
INK_MUTED = "#7b7a75"
GRID = "#e4e3dd"
SHADE = "#f0efe9"
SHADE_BLUE = "#e9f0fa"

BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
VIOLET = "#4a3aa7"
NEUTRAL = "#b8b7b0"

# Mau gan theo thuc the, thu tu co dinh, khong bao gio xoay vong.
STYLE: dict[str, dict] = {
    "QSVM_ZZ":      dict(color=BLUE,      ls="-",               marker="o", lw=2.0, ms=6.0, z=6, label="QSVM-ZZ"),
    "QSVM_Z":       dict(color=VIOLET,    ls=(0, (5, 2)),       marker="s", lw=2.0, ms=5.5, z=5, label="QSVM-Z"),
    "XGBoost":      dict(color=ORANGE,    ls="-",               marker="^", lw=2.0, ms=6.0, z=6, label="XGBoost"),
    "RandomForest": dict(color=AQUA,      ls="-",               marker="D", lw=2.0, ms=5.0, z=5, label="Random forest"),
    "SVM_RBF":      dict(color="#6f6e69", ls=(0, (1, 1.6)),     marker="v", lw=1.2, ms=4.0, z=3, label="SVM-RBF"),
    "SVM_Poly2":    dict(color="#94938c", ls=(0, (3, 1, 1, 1)), marker="P", lw=1.2, ms=4.0, z=3, label="SVM-poly2"),
    "SVM_Linear":   dict(color="#b0afa8", ls=(0, (4, 2, 1, 2)), marker="X", lw=1.2, ms=4.0, z=3, label="SVM-linear"),
}
MODEL_ORDER = list(STYLE)
# Cac baseline dua vao panel delta. Co SVM-RBF vi o NSL-KDD tai N=10000 no la
# baseline co dien manh nhat (F1 0.774 > XGBoost 0.771): bo no di thi panel se
# thanh ra chi so voi nhung doi thu de hon. Chi bo SVM-linear va SVM-poly2 --
# hai model yeu ro rang -- va ca hai van co du trong ban do che do (Hinh 10).
STRONG = ["QSVM_Z", "SVM_RBF", "RandomForest", "XGBoost"]
DELTA_JITTER = [0.895, 0.963, 1.035, 1.115]

VERDICT_STYLE = {
    "QSVM-favorable":      dict(color=BLUE,    marker="^", ms=8.0, label="QSVM-favorable"),
    "inconclusive":        dict(color=NEUTRAL, marker="o", ms=6.0, label="Inconclusive"),
    "classical-favorable": dict(color=ORANGE,  marker="v", ms=8.0, label="Classical-favorable"),
}

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans",
    "font.size": 8,
    "axes.labelsize": 8.5,
    "axes.titlesize": 9,
    "axes.titleweight": "bold",
    "axes.labelcolor": INK_2,
    "axes.edgecolor": GRID,
    "axes.linewidth": 0.8,
    "text.color": INK,
    "xtick.color": INK_2,
    "ytick.color": INK_2,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5,
    "legend.frameon": False,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "lines.solid_capstyle": "round",
    "lines.dash_capstyle": "round",
    "savefig.bbox": "tight",
    "savefig.dpi": 400,
    "pdf.fonttype": 42,
})


def tidy(ax):
    """Truc va luoi lui ve sau, du lieu noi len truoc."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.set_axisbelow(True)
    ax.grid(True, axis="y", color=GRID, lw=0.6)
    ax.tick_params(length=2.5, width=0.7)


def save(fig, name):
    """Ghi ra dia roi TRA VE fig, de notebook con hien duoc inline.

    `plt.close` chi go fig khoi trinh quan ly cua pyplot; doi tuong van ve
    lai duoc bang `display(fig)`, nen dong o day khong mat gi ma tranh
    duoc viec giu hang chuc figure trong bo nho.
    """
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}")
    plt.close(fig)
    print(f"  -> {OUT.relative_to(ROOT)}/{name}.pdf  (+ .png)")
    return fig


def ci95(values: np.ndarray) -> float:
    """Nua do rong khoang tin cay 95% dua tren phan phoi t."""
    v = np.asarray(values, dtype=float)
    if len(v) < 2:
        return 0.0
    return float(stats.t.ppf(0.975, len(v) - 1) * stats.sem(v))


def fmt_n(v: int) -> str:
    return f"{v // 1000}k" if v >= 1000 and v % 1000 == 0 else str(v)


def place_right_labels(ax, points, xanchor=None):
    """Dat nhan truc tiep o le phai, day cac nhan ra cho het chong nhau.

    `points` la danh sach (y, text). Nhan mang token muc chu, khong mang mau
    cua duong -- marker ben canh moi la thu cho biet danh tinh.
    """
    if not points:
        return
    lo, hi = ax.get_ylim()
    gap = 0.052 * (hi - lo)
    pts = sorted(points, key=lambda p: p[0])
    ys = [p[0] for p in pts]
    for i in range(1, len(ys)):                      # day len tren
        ys[i] = max(ys[i], ys[i - 1] + gap)
    overflow = ys[-1] - (hi - 0.5 * gap)
    if overflow > 0:                                  # neu tran thi keo ca cum xuong
        ys = [y - overflow for y in ys]
        for i in range(len(ys) - 2, -1, -1):
            ys[i] = min(ys[i], ys[i + 1] - gap)
    if xanchor is None:                       # mac dinh: truc log co le phai RIGHT_MARGIN
        xanchor = ax.get_xlim()[1] / RIGHT_MARGIN * 1.06
    for (_, text), y in zip(pts, ys):
        ax.annotate(text, (xanchor, y), xytext=(2, 0), textcoords="offset points",
                    va="center", ha="left", fontsize=7, color=INK_2, zorder=10)


# --------------------------------------------------------------------------
# Nap du lieu
# --------------------------------------------------------------------------
def load_curve(path: Path, arm: str, test_split: str) -> pd.DataFrame:
    d = pd.read_csv(path)
    d = d[(d.arm == arm) & (d.test_split == test_split)]
    g = d.groupby(["model", "n_train"])["f1_macro"]
    out = g.agg(mean="mean", n_runs="size").reset_index()
    out["ci"] = g.apply(lambda s: ci95(s.values)).values
    return out


def load_pairs(path: Path, arm: str, test_split: str) -> pd.DataFrame:
    """Doc bang thong ke ghep cap.

    Cac file duoc sinh o nhung thoi diem khac nhau nen dat ten tap test khong
    dong nhat (`full_kddtest_plus` vs `full_test`); chuan hoa ve mot ten.
    """
    d = pd.read_csv(path)
    d["test_split"] = d.test_split.replace({"full_kddtest_plus": "full_test"})
    return d[(d.arm == arm) & (d.test_split == test_split)]


# --------------------------------------------------------------------------
# Fig 5 -- lua chon so chieu C1
# --------------------------------------------------------------------------
# NSL-KDD: rut tu output cua notebooks/nslkdd/C1_revision.ipynb (block C, D, E).
NSL_C1 = pd.DataFrame({
    "n":      [2, 3, 4, 5, 6, 7, 8, 9, 10],
    "V":      [0.7418, 0.8210, 0.8662, 0.9040, 0.9391, 0.9524, 0.9643, 0.9729, 0.9810],
    "KTA":    [0.3297, 0.1537, 0.2364, 0.2439, 0.2381, 0.1949, 0.1952, 0.1907, 0.1793],
    "Q":      [0.0261, 0.0717, 0.1391, 0.2283, 0.3391, 0.4717, 0.6261, 0.8022, 1.0000],
    "kta_lo": [0.2861, 0.1323, 0.2119, 0.2224, 0.2224, 0.1851, 0.1848, 0.1799, 0.1696],
    "kta_hi": [0.3903, 0.1822, 0.2762, 0.2801, 0.2685, 0.2209, 0.2220, 0.2183, 0.2080],
})
NSL_C1_META = dict(n_star=4, v_thresh=0.85, feasible=[4, 5, 6], kta_thresh=0.2317)

PANELS_C1 = [
    ("V",   "Variance $V(n)$", "Explained variance"),
    ("KTA", "KTA",             "Kernel-target alignment"),
    ("Q",   "Cost $Q(n)$",     "Hardware cost"),
]


def figure5():
    unsw = pd.read_csv(ROOT / "results/unsw/c4_revision/u1_dimension_metrics.csv")
    sel = json.loads((ROOT / "results/unsw/c4_revision/u1_c1_selection_unsw.json").read_text())
    unsw_meta = dict(
        n_star=sel["selected_n"],
        v_thresh=sel["selection_rule"]["variance_threshold"],
        feasible=sel["kernel_quality_feasible_n"],
        kta_thresh=sel["kta_threshold"],
    )

    rows = [("NSL-KDD", NSL_C1, NSL_C1_META, True),
            ("UNSW-NB15", unsw, unsw_meta, False)]
    fig, axes = plt.subplots(2, 3, figsize=(7.16, 4.4), sharex=True)

    for r, (dname, df, meta, has_ci) in enumerate(rows):
        n = df["n"].values
        infeasible = n[df["V"].values < meta["v_thresh"]]
        xsplit = infeasible.max() + 0.5 if len(infeasible) else None

        for c, (col, ylab, title) in enumerate(PANELS_C1):
            ax = axes[r, c]
            tidy(ax)
            if xsplit is not None:
                ax.axvspan(1.5, xsplit, color=SHADE, lw=0, zorder=0)

            ax.plot(n, df[col], color=BLUE, lw=2.0, marker="o", ms=4.5,
                    mfc=SURFACE, mew=1.5, zorder=5)

            if col == "V":
                ax.axhline(meta["v_thresh"], color=INK_MUTED, lw=1.0, ls=(0, (4, 3)), zorder=2)
                ax.annotate(f"$T={meta['v_thresh']:.2f}$", (10.4, meta["v_thresh"]),
                            xytext=(0, 4), textcoords="offset points",
                            va="bottom", ha="right", fontsize=7, color=INK_2)
            elif col == "KTA":
                if has_ci:
                    ax.fill_between(n, df["kta_lo"], df["kta_hi"], color=BLUE,
                                    alpha=0.14, lw=0, zorder=3)
                ax.axhline(meta["kta_thresh"], color=INK_MUTED, lw=1.0, ls=(0, (4, 3)), zorder=2)
                # Nhan dat phia TREN duong nguong o le phai: o ca hai bo du lieu,
                # duong cong tai n lon deu nam duoi nguong nen cho do trong.
                ax.annotate("$0.95\\,\\mathrm{KTA}_{\\max}$", (10.4, meta["kta_thresh"]),
                            xytext=(0, 4), textcoords="offset points",
                            va="bottom", ha="right", fontsize=7, color=INK_2)
                for nf in meta["feasible"]:
                    ax.plot([nf], [df.loc[df.n == nf, "KTA"].iloc[0]], marker="o", ms=9,
                            mfc="none", mec=BLUE, mew=1.4, zorder=6)

            ystar = float(df.loc[df.n == meta["n_star"], col].iloc[0])
            ax.plot([meta["n_star"]], [ystar], marker="o", ms=6.0, color=BLUE,
                    mec=SURFACE, mew=1.2, zorder=8)
            dy = 15 if col == "Q" else -16
            ax.annotate(f"$n^\\ast\\!=\\!{meta['n_star']}$", (meta["n_star"], ystar),
                        textcoords="offset points", xytext=(-4, dy), ha="center",
                        fontsize=7.5, color=INK, fontweight="bold", zorder=9)

            ax.set_ylabel(ylab, labelpad=2)
            if r == 0:
                ax.set_title(f"({'abc'[c]}) {title}", loc="left", color=INK, pad=6)
            else:
                ax.set_xlabel("Latent dimension / qubits $n$")
            ax.set_xticks(range(2, 11, 2))
            ax.set_xlim(1.5, 10.5)

        axes[r, 0].annotate(dname, (0, 0.5), xycoords="axes fraction",
                            xytext=(-42, 0), textcoords="offset points",
                            rotation=90, va="center", ha="center",
                            fontsize=9, fontweight="bold", color=INK)

    handles = [
        Patch(facecolor=SHADE, edgecolor="none", label="Excluded by stage 1 ($V<T$)"),
        Line2D([], [], color=INK_MUTED, lw=1.0, ls=(0, (4, 3)), label="Stage threshold"),
        Line2D([], [], color=BLUE, lw=0, marker="o", ms=8, mfc="none", mew=1.4,
               label="Passes stages 1-2"),
        Line2D([], [], color=BLUE, lw=6, alpha=0.14, label="95% bootstrap CI (NSL-KDD only)"),
        Line2D([], [], color=BLUE, lw=0, marker="o", ms=6, label="Selected $n^\\ast$ (stage 3)"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=5, bbox_to_anchor=(0.5, -0.075),
               handlelength=1.8, columnspacing=1.4, labelcolor=INK_2)
    fig.suptitle("Three-stage dimension selection reproduces on an unseen dataset",
                 x=0.012, ha="left", fontsize=10, fontweight="bold", color=INK)
    fig.tight_layout(rect=(0.035, 0.0, 1, 0.945))
    return save(fig, "fig5_c1_dimension_selection")


# --------------------------------------------------------------------------
# Fig 9 / Fig 11 -- duong hoc va delta ghep cap
# --------------------------------------------------------------------------
def _plot_curve(ax, curve, ticks):
    """Ve duong hoc; tra ve cac diem cuoi de gan nhan sau khi da chot ylim."""
    ends = []
    for m in MODEL_ORDER:
        s = STYLE[m]
        d = curve[curve.model == m].sort_values("n_train")
        if d.empty:
            continue
        x, y, e = d.n_train.values, d["mean"].values, d["ci"].values
        if s["z"] >= 5:
            ax.fill_between(x, y - e, y + e, color=s["color"], alpha=0.12, lw=0,
                            zorder=s["z"] - 3)
        ax.plot(x, y, color=s["color"], ls=s["ls"], lw=s["lw"], marker=s["marker"],
                ms=s["ms"], mec=SURFACE, mew=0.8, zorder=s["z"])
        if s["z"] >= 5:
            ends.append((float(y[-1]), s["label"]))
    _log_axis(ax, ticks, right_margin=RIGHT_MARGIN)
    ax.set_ylabel("Macro-$F_1$")
    return ends


# Be rong le phai (theo ti le truc log) danh cho cac nhan truc tiep.
RIGHT_MARGIN = 1.95


def _log_axis(ax, ticks, *, right_margin=1.22):
    ax.set_xscale("log")
    ax.set_xlabel("Training-set size $N$ (log scale)")
    ax.set_xticks(ticks)
    ax.set_xticklabels([fmt_n(v) for v in ticks])
    ax.minorticks_off()
    ax.set_xlim(ticks[0] * 0.82, ticks[-1] * right_margin)
    tidy(ax)


def _plot_delta(ax, pairs, ticks, *, band=None):
    """Delta ghep cap kem CI 95%.

    Dung thanh sai so co lech nhe theo truc x thay vi dai to: ba dai chong
    nhau tao thanh mang mau khong doc duoc.
    """
    if band is not None:
        ax.axvspan(*band, color=SHADE_BLUE, lw=0, zorder=0)
    ax.axhline(0.0, color=INK_MUTED, lw=1.0, zorder=2)
    jitter = dict(zip(STRONG, DELTA_JITTER))
    for m in STRONG:
        s = STYLE[m]
        d = pairs[pairs.baseline == m].sort_values("n_train")
        if d.empty:
            continue
        x = d.n_train.values.astype(float)
        y = d.mean_delta.values
        xj = x * jitter[m]
        # Trong panel nay moi baseline deu la nhan vat chinh, nen SVM-RBF duoc
        # ve day bang cac duong khac (mau van la mau cua chinh no o panel tren).
        lw, ms = 2.0, max(s["ms"], 5.5)
        ax.errorbar(xj, y, yerr=[y - d.ci_low.values, d.ci_high.values - y],
                    fmt="none", ecolor=s["color"], elinewidth=1.0, capsize=2.0,
                    capthick=1.0, alpha=0.85, zorder=s["z"] - 1)
        ax.plot(x, y, color=s["color"], ls=s["ls"], lw=lw, zorder=s["z"] - 1)
        ax.plot(xj, y, ls="none", marker=s["marker"], ms=ms, color=s["color"],
                mec=SURFACE, mew=0.8, zorder=s["z"])
        sig = d[d.holm_p < 0.05]
        if not sig.empty:
            ax.plot(sig.n_train.values * jitter[m], sig.mean_delta.values, ls="none",
                    marker="o", ms=ms + 5.5, mfc="none", mec=s["color"], mew=1.3,
                    zorder=s["z"] + 1)
    _log_axis(ax, ticks)
    # Huong cua truc ghi ngay tren nhan truc y. Nhan truc y xoay 90 do nen dau
    # trai cua dong chu roi xuong duoi, dau phai roi len tren -- chi dan dung
    # huong theo cau tao, va khong the va vao du lieu o bat ky panel nao.
    ax.set_ylabel("$\\Delta F_1$ (QSVM-ZZ $-$ baseline)\n"
                  "$\\leftarrow$ baseline  ·  QSVM-ZZ $\\rightarrow$",
                  fontsize=7.5, linespacing=1.5)


def shade_unavailable(ax, from_n, ticks):
    """To vung khong co du lieu, thay vi de truc trong khong giai thich."""
    ax.axvspan(from_n * 1.06, ax.get_xlim()[1], color=SHADE, lw=0, zorder=0)


def _curve_legend(fig, y, ncol=7):
    handles = [Line2D([], [], color=STYLE[m]["color"], ls=STYLE[m]["ls"],
                      lw=STYLE[m]["lw"], marker=STYLE[m]["marker"], ms=STYLE[m]["ms"],
                      mec=SURFACE, mew=0.8, label=STYLE[m]["label"]) for m in MODEL_ORDER]
    handles.append(Line2D([], [], color=INK_2, lw=0, marker="o", ms=8, mfc="none",
                          mew=1.3, label="Holm-adj. $p<0.05$"))
    fig.legend(handles=handles, loc="lower center", ncol=ncol, bbox_to_anchor=(0.5, y),
               handlelength=2.4, columnspacing=1.1, labelcolor=INK_2)


def figure9():
    base = ROOT / "results/nslkdd/c4_revision"
    nat = load_curve(base / "c4_per_run_natural_refit_per_N.csv", "tuned_per_N", "full_kddtest_plus")
    mat = load_curve(base / "c4_per_run_matched_refit_per_N.csv", "tuned_per_N", "full_kddtest_plus")
    pn = load_pairs(base / "c4_pairwise_statistics_natural.csv", "tuned_per_N", "full_test")
    pm = load_pairs(base / "c4_pairwise_statistics_matched.csv", "tuned_per_N", "full_test")

    # Mot truc x chung cho ca bon panel: nhom rare-enriched can kiet o N=2000,
    # neu moi panel mot thang do thi hai cot khong the doc chong len nhau.
    ticks = [100, 200, 500, 1000, 2000, 5000, 10000]

    fig, axes = plt.subplots(2, 2, figsize=(7.16, 5.3))

    e_nat = _plot_curve(axes[0, 0], nat, ticks)
    axes[0, 0].set_title("(a) Natural prior (rare 0.83%)", loc="left", color=INK, pad=6)
    e_mat = _plot_curve(axes[0, 1], mat, ticks)
    axes[0, 1].set_title("(b) Rare-enriched pool (rare 10%)", loc="left", color=INK, pad=6)

    lo = min(nat["mean"].min(), mat["mean"].min()) - 0.025
    hi = max(nat["mean"].max(), mat["mean"].max()) + 0.015
    for ax in (axes[0, 0], axes[0, 1]):
        ax.set_ylim(lo, hi)
    # Chi panel (a) mang nhan truc tiep: o panel (b) duong ket thuc giua do thi
    # nen nhan se roi vao vung xam "khong co du lieu" va gay hieu nham.
    place_right_labels(axes[0, 0], e_nat)
    shade_unavailable(axes[0, 1], 2000, ticks)
    axes[0, 1].annotate("rare-enriched pool\nexhausts at $N=2000$", (2400, lo),
                        xytext=(0, 8), textcoords="offset points", fontsize=7,
                        color=INK_MUTED, va="bottom", ha="left")

    _plot_delta(axes[1, 0], pn, ticks, band=(2000, 5000))
    axes[1, 0].set_title("(c) Paired $\\Delta$, natural prior", loc="left", color=INK, pad=6)
    _plot_delta(axes[1, 1], pm, ticks)
    axes[1, 1].set_title("(d) Paired $\\Delta$, rare-enriched pool", loc="left", color=INK, pad=6)

    d = pd.concat([pn, pm])
    d = d[d.baseline.isin(STRONG)]
    pad = 0.07 * (d.ci_high.max() - d.ci_low.min())
    for ax in axes[1]:
        ax.set_ylim(d.ci_low.min() - pad, d.ci_high.max() + pad)
    shade_unavailable(axes[1, 1], 2000, ticks)
    axes[1, 0].annotate("crossover\n$N\\approx2000$-$5000$", (3200, d.ci_low.min() - pad),
                        xytext=(0, 6), textcoords="offset points",
                        ha="center", va="bottom", fontsize=7.5, color=INK_2)

    _curve_legend(fig, y=-0.02, ncol=8)
    fig.suptitle("Enriching rare attacks removes the crossover: NSL-KDD",
                 x=0.012, ha="left", fontsize=10, fontweight="bold", color=INK)
    fig.tight_layout(rect=(0, 0.035, 1, 0.95))
    return save(fig, "fig9_learning_curve_nslkdd")


def figure11():
    base = ROOT / "results/unsw/c4_revision"
    cur = load_curve(base / "c4_per_run_unsw_natural_refit_per_N.csv", "tuned_per_N", "full_test")
    pairs = load_pairs(base / "c4_pairwise_statistics_natural.csv", "tuned_per_N", "full_test")
    ticks = [100, 500, 1000, 2000, 5000, 10000]

    fig, axes = plt.subplots(1, 2, figsize=(7.16, 3.0))
    ends = _plot_curve(axes[0], cur, ticks)
    axes[0].set_title("(a) UNSW-NB15 learning curve, natural prior", loc="left",
                      color=INK, pad=6)
    axes[0].set_ylim(cur["mean"].min() - 0.03, cur["mean"].max() + 0.02)
    place_right_labels(axes[0], ends)

    _plot_delta(axes[1], pairs, ticks)
    axes[1].set_title("(b) Paired $\\Delta$ vs. each baseline", loc="left", color=INK, pad=6)
    d = pairs[pairs.baseline.isin(STRONG)]
    pad = 0.09 * (d.ci_high.max() - d.ci_low.min())
    axes[1].set_ylim(d.ci_low.min() - pad, d.ci_high.max() + pad)

    # Ghi dung pham vi: doi dau CO xay ra so voi hai baseline kernel
    # (QSVM-Z va SVM-RBF) nhung KHONG xay ra so voi hai ensemble cay,
    # ngay ca tai N = 10.000.
    axes[1].annotate("crosses zero vs. the kernel baselines,",
                     (900, d.ci_low.min() - pad), xytext=(0, 15),
                     textcoords="offset points", ha="center", va="bottom",
                     fontsize=7.5, color=INK_2)
    axes[1].annotate("never vs. the tree ensembles",
                     (900, d.ci_low.min() - pad), xytext=(0, 5),
                     textcoords="offset points", ha="center", va="bottom",
                     fontsize=7.5, color=INK_2)

    _curve_legend(fig, y=-0.03, ncol=8)
    fig.suptitle("On UNSW-NB15 the quantum kernel beats classical kernels, not tree ensembles",
                 x=0.012, y=0.995, ha="left", fontsize=10, fontweight="bold", color=INK)
    fig.tight_layout(rect=(0, 0.045, 1, 0.945))
    return save(fig, "fig11_unsw_transfer")


# --------------------------------------------------------------------------
# Fig 10 -- ban do che do
# --------------------------------------------------------------------------
GROUP_TITLE = {
    "C2": "C2 · kernel level",
    "C3": "C3 · distribution shift",
    "C4": "C4 · sample complexity",
}
ROW_LABEL = {
    ("C2", "ZZ_minus_Z_KTA"): "KTA,  ZZ $-$ Z",
    ("C2", "ZZ_minus_Z_F1"): "$F_1$,  ZZ $-$ Z",
}


def _row_label(r) -> str:
    key = (r.contribution, r.metric)
    if key in ROW_LABEL:
        return ROW_LABEL[key]
    if r.contribution == "C3":
        if r.regime == "prior_shift":
            return f"prior shift,  {r.condition.replace('attack_', '').replace('pct', '%')} attack"
        if r.regime == "temporal":
            return "temporal,  KDDTest$^{-21}$"
        if r.regime == "perturbation":
            return "feature perturbation (slope)"
        if r.regime == "attack_composition":
            return "attack mix,  50% normal / 50% DoS"
    return f"{r.regime.split('_')[-1]},  $N$ = {fmt_n(int(r.condition.split('=')[1]))}"


def figure10():
    d = pd.read_csv(ROOT / "results/nslkdd/regime_map_rows.csv")
    d["row"] = d.apply(_row_label, axis=1)
    cols = ["QSVM_Z", "SVM_Linear", "SVM_Poly2", "SVM_RBF", "RandomForest", "XGBoost"]

    # Bo cuc: moi nhom mot dong tieu de in dam, roi den cac dong du lieu.
    ticks: list[float] = []
    labels: list[str] = []
    bold: list[bool] = []
    ys: dict[tuple[str, str], float] = {}
    y = 0.0
    for contrib in ["C2", "C3", "C4"]:
        sub = d[d.contribution == contrib]
        ticks.append(y); labels.append(GROUP_TITLE[contrib]); bold.append(True)
        y += 1.05
        for row in sub["row"].drop_duplicates():
            ys[(contrib, row)] = y
            ticks.append(y); labels.append(row); bold.append(False)
            y += 1.0
        y += 0.55
    ymax = y - 0.55

    fig, ax = plt.subplots(figsize=(7.16, 5.15))
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)

    for yy in ys.values():
        ax.plot([-0.4, len(cols) - 0.6], [yy, yy], color=GRID, lw=0.7, zorder=0)

    for _, r in d.iterrows():
        key = (r.contribution, r.row)
        if key not in ys or r.baseline not in cols:
            continue
        st = VERDICT_STYLE[r.verdict]
        ax.plot([cols.index(r.baseline)], [ys[key]], marker=st["marker"], ms=st["ms"],
                color=st["color"], mec=SURFACE, mew=1.0, ls="none", zorder=5)

    ax.set_yticks(ticks)
    ax.set_yticklabels(labels, fontsize=7.5)
    for lbl, is_bold in zip(ax.get_yticklabels(), bold):
        lbl.set_color(INK if is_bold else INK_2)
        lbl.set_fontweight("bold" if is_bold else "normal")

    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([STYLE[c]["label"] for c in cols], fontsize=7.5, color=INK_2,
                       rotation=28, ha="left", rotation_mode="anchor")
    ax.xaxis.set_ticks_position("top")
    ax.set_xlim(-0.6, len(cols) - 0.4)
    ax.set_ylim(ymax, -0.6)
    ax.tick_params(length=0)

    counts = d.verdict.value_counts()
    handles = [Line2D([], [], ls="none", marker=VERDICT_STYLE[k]["marker"],
                      ms=VERDICT_STYLE[k]["ms"], color=VERDICT_STYLE[k]["color"],
                      mec=SURFACE, mew=1.0,
                      label=f"{VERDICT_STYLE[k]['label']}  ({counts.get(k, 0)})")
               for k in ("QSVM-favorable", "inconclusive", "classical-favorable")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.02),
              ncol=3, labelcolor=INK_2, handletextpad=0.4, columnspacing=2.0)

    fig.suptitle("Regime map: where the quantum kernel helps, and where it does not",
                 x=0.012, y=0.985, ha="left", fontsize=10, fontweight="bold", color=INK)
    fig.text(0.012, 0.925, "Verdict of QSVM-ZZ against each baseline "
                           "(paired over 10 runs, Holm-corrected within family)",
             ha="left", fontsize=7.5, color=INK_MUTED)
    fig.tight_layout(rect=(0, 0.01, 1, 0.895))
    return save(fig, "fig10_regime_map")


# --------------------------------------------------------------------------
# Fig 4 -- quet K cho tang SelectKBest
# --------------------------------------------------------------------------
def figure4():
    """Quet K, hai duong: truoc va sau khau nen PCA-4 cua pipeline that.

    Hinh cu chi quet K trong {4, 6, 8, 10, 20} roi goi K=20 la "elbow". Mo rong
    luoi den K=122 cho thay do khong phai diem bao hoa ma chi la diem cuoi cua
    luoi quet. Ve ca hai duong de nguoi doc tu thay: giu K=20 la mot lua chon
    giao thuc duoc ke thua, khong phai mot toi uu.
    """
    d = pd.read_csv(ROOT / "results/nslkdd/c1_revision/c1_ksweep.csv")
    fig, ax = plt.subplots(figsize=(7.16, 3.0))
    tidy(ax)

    series = [("f1_raw", BLUE, "-", "o", "SelectKBest only"),
              ("f1_pca4", ORANGE, (0, (5, 2)), "^",
               "SelectKBest $\\to$ PCA-4 (pipeline used)")]
    ends = []
    for col, colour, ls, marker, label in series:
        m, s = d[f"{col}_mean"].values, d[f"{col}_std"].values
        ax.fill_between(d.K, m - s, m + s, color=colour, alpha=0.13, lw=0, zorder=3)
        ax.plot(d.K, m, color=colour, ls=ls, lw=2.0, marker=marker, ms=5.0,
                mec=SURFACE, mew=0.8, zorder=6)
        ends.append((float(m[-1]), label))

    k_used, k_best = 20, int(d.loc[d.f1_pca4_mean.idxmax(), "K"])
    row = d.set_index("K")
    ax.axvline(k_used, color=INK_MUTED, lw=1.0, ls=(0, (4, 3)), zorder=2)
    ax.annotate(f"$K={k_used}$ (fixed by the\nsubmitted protocol)",
                (k_used, ax.get_ylim()[0]), xytext=(6, 6),
                textcoords="offset points", ha="left", va="bottom",
                fontsize=7.5, color=INK_2)
    gap = row.loc[k_best, "f1_pca4_mean"] - row.loc[k_used, "f1_pca4_mean"]
    ax.annotate(f"$+{gap:.3f}$ macro-$F_1$ left on the table at $K={k_best}$",
                (k_best, row.loc[k_best, "f1_pca4_mean"]), xytext=(-6, 14),
                textcoords="offset points", ha="right", va="bottom",
                fontsize=7.5, color=ORANGE)

    ax.set_xscale("log")
    ax.set_xticks(d.K.tolist())
    ax.set_xticklabels([str(k) for k in d.K], fontsize=7)
    ax.minorticks_off()
    ax.set_xlim(3.5, d.K.max() * 2.4)
    ax.set_xlabel("Number of features kept by SelectKBest, $K$ (log scale)")
    ax.set_ylabel("Macro-$F_1$ (proxy linear SVM)")
    place_right_labels(ax, ends, xanchor=d.K.max() * 1.06)

    fig.suptitle("The elbow at $K=20$ was the end of the old sweep, not a plateau",
                 x=0.012, y=0.995, ha="left", fontsize=10, fontweight="bold", color=INK)
    fig.text(0.012, 0.90, "Five-fold stratified CV on the full training set; "
                          "SelectKBest is refit inside each fold. Bands are one "
                          "standard deviation.",
             ha="left", fontsize=7.5, color=INK_MUTED)
    fig.tight_layout(rect=(0, 0.01, 1, 0.87))
    return save(fig, "fig4_selectkbest_sweep")


# --------------------------------------------------------------------------
# Fig 6 -- ablation entanglement (thay hinh KTA cu)
# --------------------------------------------------------------------------
def figure6():
    """Ablation ZZ vs Z, tu du lieu C2 revision (10 run, ghep cap theo run).

    Hinh cu ve KTA cua ca nam kernel voi thanh sai so tren 5 run. Ban revision
    khong tinh KTA cho kernel co dien (khong co trong `c2_per_run.csv`), va dieu
    dang noi cua C2 von la ablation ghep cap chu khong phai bang xep hang KTA.
    Nen hinh moi ve dung phep so sanh ghep cap do.
    """
    base = ROOT / "results/nslkdd/c2_revision"
    kta = pd.read_csv(base / "c2_kta_per_run.csv")
    per_run = pd.read_csv(base / "c2_per_run.csv")
    f1 = per_run.pivot_table(index="run_id", columns="model", values="f1_macro")

    fig, axes = plt.subplots(1, 2, figsize=(7.16, 2.9))

    # (a) Bieu do do doc: moi run mot doan noi Z -> ZZ.
    ax = axes[0]
    tidy(ax)
    for _, r in kta.iterrows():
        ax.plot([0, 1], [r.kta_z, r.kta_zz], color=INK_MUTED, lw=0.8, alpha=0.55,
                zorder=3, marker="o", ms=3.0, mfc=SURFACE, mew=0.8)
    for x, col, c, lab in ((0, "kta_z", VIOLET, "QSVM-Z"), (1, "kta_zz", BLUE, "QSVM-ZZ")):
        m, e = kta[col].mean(), ci95(kta[col].values)
        ax.errorbar([x], [m], yerr=[[e], [e]], fmt="o", ms=7, color=c, mec=SURFACE,
                    mew=1.2, ecolor=c, elinewidth=1.6, capsize=4, zorder=6)
        ax.annotate(f"{m:.3f}", (x, m), xytext=(0, 12), textcoords="offset points",
                    ha="center", fontsize=7.5, color=INK, fontweight="bold")
        ax.annotate(lab, (x, 0), xytext=(0, -22), textcoords="offset points",
                    xycoords=("data", "axes fraction"), ha="center", fontsize=8,
                    color=INK_2)
    ax.set_xticks([])
    ax.set_xlim(-0.45, 1.45)
    ax.set_ylabel("Kernel-target alignment")
    ax.set_title("(a) Entanglement ablation, paired by run", loc="left",
                 color=INK, pad=6)

    # (b) Delta ghep cap cho KTA va F1.
    ax = axes[1]
    tidy(ax)
    ax.axvline(0.0, color=INK_MUTED, lw=1.0, zorder=2)
    rows = [("$\\Delta$ KTA", kta.delta_kta.values, BLUE),
            ("$\\Delta F_1$", (f1["QSVM_ZZ"] - f1["QSVM_Z"]).values, VIOLET)]
    for i, (label, vals, colour) in enumerate(rows):
        y = len(rows) - 1 - i
        m, e = float(np.mean(vals)), ci95(vals)
        ax.errorbar([m], [y], xerr=[[e], [e]], fmt="o", ms=7, color=colour,
                    mec=SURFACE, mew=1.2, ecolor=colour, elinewidth=1.6,
                    capsize=4, zorder=6)
        ax.plot(vals, np.full(len(vals), y) + 0.17, ls="none", marker="o", ms=3,
                color=colour, alpha=0.35, zorder=4)
        ax.annotate(f"{m:+.4f}  [{m - e:+.4f}, {m + e:+.4f}]", (m, y),
                    xytext=(0, -15), textcoords="offset points", ha="center",
                    fontsize=7, color=INK_2)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in reversed(rows)], fontsize=9)
    ax.set_ylim(-0.55, len(rows) - 0.35)
    ax.set_xlabel("Paired difference, QSVM-ZZ $-$ QSVM-Z (10 runs)")
    ax.set_title("(b) Paired effect with 95% CI", loc="left", color=INK, pad=6)
    ax.grid(False, axis="y")

    fig.suptitle("Entanglement moves the kernel geometry far more than the score",
                 x=0.012, y=0.995, ha="left", fontsize=10, fontweight="bold", color=INK)
    fig.tight_layout(rect=(0, 0.03, 1, 0.945))
    return save(fig, "fig6_entanglement_ablation")


# --------------------------------------------------------------------------
# Fig 7 -- phan bo F1 tung run cho ca bay model
# --------------------------------------------------------------------------
def figure7():
    """Phan bo F1 tung run, 10 run, ca bay model -- co ca RF va XGBoost."""
    d = pd.read_csv(ROOT / "results/nslkdd/c2_revision/c2_per_run.csv")
    order = d.groupby("model")["f1_macro"].mean().sort_values().index.tolist()

    fig, ax = plt.subplots(figsize=(7.16, 2.9))
    tidy(ax)
    rng = np.random.default_rng(20260903)
    means = {}
    for i, m in enumerate(order):
        vals = d.loc[d.model == m, "f1_macro"].values
        s = STYLE[m]
        ax.plot(vals, i + rng.uniform(-0.13, 0.13, len(vals)), ls="none", marker="o",
                ms=3.5, color=s["color"], alpha=0.45, zorder=4)
        mean, e = float(vals.mean()), ci95(vals)
        ax.errorbar([mean], [i], xerr=[[e], [e]], fmt=s["marker"], ms=7,
                    color=s["color"], mec=SURFACE, mew=1.2, ecolor=s["color"],
                    elinewidth=1.6, capsize=3.5, zorder=6)
        means[m] = mean
    ax.set_yticks(range(len(order)))
    # Tri so nam trong nhan truc: dat troi trong vung ve thi no roi sang hang ben.
    ax.set_yticklabels([f"{STYLE[m]['label']}   {means[m]:.4f}" for m in order],
                       fontsize=8)
    ax.set_ylim(-0.6, len(order) - 0.4)
    ax.set_xlabel("Macro-$F_1$ (10 independent runs, $N_{\\mathrm{train}}=1000$)")
    ax.grid(False, axis="y")
    ax.grid(True, axis="x", color=GRID, lw=0.6)

    fig.suptitle("With strong tabular baselines the quantum kernel no longer leads",
                 x=0.012, y=0.995, ha="left", fontsize=10, fontweight="bold", color=INK)
    fig.text(0.012, 0.90, "Dots are individual runs; markers are the mean with a 95% "
                          "confidence interval. The intervals overlap: this is an "
                          "ordering of point estimates, not a significant separation.",
             ha="left", fontsize=7.5, color=INK_MUTED)
    fig.tight_layout(rect=(0, 0.01, 1, 0.87))
    return save(fig, "fig7_per_run_f1")


# --------------------------------------------------------------------------
# Fig 8 -- dich chuyen prior lop
# --------------------------------------------------------------------------
def figure8():
    """Dich chuyen prior lop, tu C3 revision (10 run, 7 model, 3 dieu kien)."""
    d = pd.read_csv(ROOT / "results/nslkdd/c3_revision/c3_prior_shift_per_run.csv")
    frac = {"attack_30pct": 30, "attack_50pct": 50, "attack_70pct": 70}
    d["attack_pct"] = d.condition.map(frac)

    fig, axes = plt.subplots(1, 2, figsize=(7.16, 2.9))

    ax = axes[0]
    tidy(ax)
    ends = []
    for m in MODEL_ORDER:
        g = d[d.model == m].groupby("attack_pct")["f1_macro"]
        x = np.array(sorted(g.groups))
        mean = g.mean().values
        err = np.array([ci95(d[(d.model == m) & (d.attack_pct == v)]["f1_macro"].values)
                        for v in x])
        s = STYLE[m]
        if s["z"] >= 5:
            ax.fill_between(x, mean - err, mean + err, color=s["color"], alpha=0.12,
                            lw=0, zorder=s["z"] - 3)
            ends.append((float(mean[-1]), s["label"]))
        ax.plot(x, mean, color=s["color"], ls=s["ls"], lw=s["lw"], marker=s["marker"],
                ms=s["ms"], mec=SURFACE, mew=0.8, zorder=s["z"])
    ax.set_xticks([30, 50, 70])
    ax.set_xlim(25, 104)
    ax.set_xlabel("Attack proportion in the test mixture (%)")
    ax.set_ylabel("Macro-$F_1$")
    ax.set_title("(a) Class-prior shift", loc="left", color=INK, pad=6)
    place_right_labels(ax, ends, xanchor=72)

    # (b) Do sut giam tu 30% len 70% -- ai chiu duoc dich chuyen tot hon.
    ax = axes[1]
    tidy(ax)
    drops = []
    for m in MODEL_ORDER:
        p = d[d.model == m].pivot_table(index="run_id", columns="attack_pct",
                                        values="f1_macro")
        delta = (p[70] - p[30]).values
        drops.append((m, float(np.mean(delta)), ci95(delta)))
    drops.sort(key=lambda r: r[1])
    ax.axvline(0.0, color=INK_MUTED, lw=1.0, zorder=2)
    for i, (m, mean, e) in enumerate(drops):
        s = STYLE[m]
        ax.errorbar([mean], [i], xerr=[[e], [e]], fmt=s["marker"], ms=6.5,
                    color=s["color"], mec=SURFACE, mew=1.2, ecolor=s["color"],
                    elinewidth=1.4, capsize=3, zorder=6)
    ax.set_yticks(range(len(drops)))
    ax.set_yticklabels([STYLE[m]["label"] for m, _, _ in drops], fontsize=8)
    ax.set_ylim(-0.6, len(drops) - 0.4)
    ax.set_xlabel("$F_1$ change from 30% to 70% attacks")
    ax.set_title("(b) Degradation under the shift", loc="left", color=INK, pad=6)
    ax.grid(False, axis="y")
    ax.grid(True, axis="x", color=GRID, lw=0.6)

    fig.suptitle("Under class-prior shift the quantum kernel degrades more than the trees",
                 x=0.012, y=0.995, ha="left", fontsize=10, fontweight="bold", color=INK)
    fig.tight_layout(rect=(0, 0.01, 1, 0.945))
    return save(fig, "fig8_prior_shift")


if __name__ == "__main__":
    print("Sinh hinh cho ban revision paper 1")
    figure4()
    figure5()
    figure6()
    figure7()
    figure8()
    figure9()
    figure10()
    figure11()
    print("Xong.")
