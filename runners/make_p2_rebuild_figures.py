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
    # Dat chu thich o DUOI cung, duoi thanh cuoi -- truoc day no nam giua
    # vung co thanh nen de len nhan truc x.
    bx.text(max(stds) * 0.66, -0.62,
            "on the rare subset this is exactly 0\nfor every model, by construction",
            fontsize=6.8, color=ORANGE, va="center", ha="center", zorder=7)
    bx.set_yticks(y); bx.set_yticklabels([STYLE[m]["label"] for m in ORDER])
    bx.set_ylim(len(ORDER) - 0.4, -1.15)      # chua cho dong chu thich
    bx.set_xlim(0, max(stds) * 1.30)
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
    fig, ax = plt.subplots(figsize=(3.48, 3.0))
    y = np.arange(len(ORDER)); h = 0.20
    for j, (key, lab, col) in enumerate(cals):
        ax.barh(y + (j - 1.5) * h, [g[(m, key)] for m in ORDER], height=h,
                color=col, alpha=0.9, label=lab, zorder=4)
    # Nhan lay tu phep kiem bat cap, khong phai tu viec so hai trung binh.
    # SVM-RBF co trung binh tot len mot chut duoi temperature scaling nhung
    # chi thang 5/10 run (holm = 1,00) -- goi do la "giup" la noi qua.
    ct = pd.read_csv(NSL / "p2_rebuild_cal_tests.csv")
    verdict = ct.groupby("model").overall.first()
    TAG = {"helps": ("helped, 10/10 runs", BLUE),
           "no effect": ("no effect", INK_MUTED),
           "hurts": ("worse, 0/10 runs", ORANGE)}
    for i, m in enumerate(ORDER):
        worst = max(g[(m, k)] for k, _, _ in cals)
        lab, col = TAG[verdict[m]]
        ax.text(worst + 0.006, i, lab, va="center", fontsize=6.6,
                color=col, zorder=6)
    ax.set_yticks(y); ax.set_yticklabels([STYLE[m]["label"] for m in ORDER])
    ax.invert_yaxis(); ax.set_xlim(0, 0.30)
    ax.set_xlabel(r"$\mathrm{ECE}$ on the full test split")
    ax.set_title("Recalibration helps only the\nquantum kernel", loc="left")
    tidy(ax, axis="x")
    # Hang duoi cung la Random forest, thanh cua no dai nhat va con keo theo
    # nhan "no gain" -- goc duoi-phai KHONG trong. Dua legend han ra ngoai,
    # mot hang duoi nhan truc x.
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.20), ncol=4,
              borderpad=0.2, columnspacing=1.0, handletextpad=0.4,
              handlelength=1.2, fontsize=7)
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
    # AUC-PR tang dan sang phai, nen goc duoi-PHAI la cho XGBoost dung o
    # all122. Goc tren-trai moi la vung trong.
    ax.legend(loc="upper left", borderpad=0.2, labelspacing=0.3)
    save(fig, "fig4_refarm")


def fig5_reliability():
    """Duong tin cay -- hinh tieu chuan cua mot bai calibration.

    Bai dinh nghia ECE o cong thuc (1); day la duong cong ma ECE do khoang
    cach toi duong cheo."""
    cv = pd.read_csv(NSL / "p2_rebuild_curve.csv")
    g = cv.groupby(["model", "bin"])[["conf", "acc"]].mean()

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(7.16, 2.9),
                                 gridspec_kw=dict(width_ratios=[1, 1.15],
                                                  wspace=0.28))
    # Duong cheo duoc chu thich TRONG legend. Mot dong chu xoay doc theo no
    # thi khong co cho dat: tam giac duoi-phai la cho duy nhat con trong va
    # legend da chiem.
    ax.plot([0, 1], [0, 1], color=INK_MUTED, lw=1.0, ls=(0, (4, 2)), zorder=2,
            label="perfect calibration")
    for m in ORDER:
        s = g.loc[m]
        st = STYLE[m]
        ax.plot(s.conf, s.acc, color=st["color"], marker=st["marker"], ms=4.5,
                lw=1.6, mec=SURFACE, mew=0.6, label=st["label"], zorder=5)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xlabel("mean predicted probability in bin")
    ax.set_ylabel("observed attack fraction")
    ax.set_title("(a)  Reliability diagram, KDDTest+", loc="left", fontsize=8.5)
    tidy(ax)
    # Duong cong deu NAM TREN duong cheo, nen goc duoi-phai la vung trong
    # duy nhat. Truoc day legend o goc tren-trai de len chinh cac duong.
    ax.legend(loc="lower right", borderpad=0.25, labelspacing=0.3,
              handletextpad=0.4)

    # (b) do tu tin trung binh theo nhom tan cong
    pc = pd.read_csv(NSL / "p2_rebuild_percat.csv")
    cats = ["Normal", "DoS", "Probe", "R2L", "U2R"]
    gp = pc.groupby(["category", "model"]).mean_prob.mean()
    x = np.arange(len(cats)); w = 0.16
    for j, m in enumerate(ORDER):
        bx.bar(x + (j - 2) * w, [gp[(c, m)] for c in cats], width=w,
               color=STYLE[m]["color"], alpha=0.9, label=STYLE[m]["label"],
               zorder=4)
    bx.axhline(0.5, color=ORANGE, lw=1.3, ls=(0, (4, 2)), zorder=5)
    bx.text(len(cats) - 0.45, 0.52, "decision threshold", color=ORANGE,
            fontsize=6.8, ha="right", va="bottom", zorder=6)
    bx.set_xticks(x); bx.set_xticklabels(cats)
    bx.set_ylim(0, 1.18)                      # chua cho hang legend o tren
    bx.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    bx.set_ylabel(r"mean $\hat{p}(\mathrm{attack})$")
    bx.set_title("(b)  Confidence by attack category", loc="left", fontsize=8.5)
    tidy(bx)
    # Khong con cho trong nao ben trong: cot cao toi 0,92. Dat legend THANH
    # MOT HANG phia tren vung ve.
    bx.legend(loc="upper center", bbox_to_anchor=(0.5, 1.02), ncol=5,
              borderpad=0.2, columnspacing=0.7, handletextpad=0.35,
              handlelength=1.2, fontsize=6.6)
    save(fig, "fig5_reliability")


def fig6_threshold():
    """Ha nguong cuu duoc tan cong hiem cho mo hinh margin, khong cuu duoc
    cho cay. Va phan ra Brier tach hai truc ma bai noi."""
    th = pd.read_csv(NSL / "p2_rebuild_threshold.csv")
    br = pd.read_csv(NSL / "p2_rebuild_brier_decomp.csv")
    g = th.groupby(["model", "threshold"]).mean(numeric_only=True)

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(7.16, 2.8),
                                 gridspec_kw=dict(wspace=0.30))
    for m in ORDER:
        s = g.loc[m].sort_index()
        st = STYLE[m]
        ax.plot(s.index, s.recall_U2R, color=st["color"], marker=st["marker"],
                ms=4.0, lw=1.8, mec=SURFACE, mew=0.6, label=st["label"],
                zorder=5)
    ax.axvline(0.5, color=ORANGE, lw=1.3, ls=(0, (4, 2)), zorder=3)
    ax.text(0.52, 0.04, "default", color=ORANGE, fontsize=6.8, rotation=90,
            va="bottom", zorder=6)
    ax.set_xlabel("decision threshold")
    ax.set_ylabel("U2R recall")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_title("(a)  Lowering the threshold rescues only\nthe margin models",
                 loc="left", fontsize=8.5)
    tidy(ax)
    ax.legend(loc="upper right", borderpad=0.2, labelspacing=0.28,
              handletextpad=0.4)

    gb = br.groupby("model")[["reliability", "resolution"]].mean()
    # Random forest (.1548, .0948) nam ngay tren XGBoost (.1524, .0848): dat
    # nhan cua no o DUOI thi dong chu de len dung diem XGBoost. Dao len tren.
    # SVM-RBF thi lech trai de khoi cham MLP.
    PLACE = {"RandomForest": (0, 8, "center"), "SVM-RBF": (-6, -11, "right")}
    for m in ORDER:
        st = STYLE[m]
        dx, dy, ha = PLACE.get(m, (0, -11, "center"))
        bx.scatter(gb.loc[m, "resolution"], gb.loc[m, "reliability"], s=70,
                   color=st["color"], marker=st["marker"], edgecolor=SURFACE,
                   linewidth=0.8, zorder=5)
        bx.annotate(st["label"], (gb.loc[m, "resolution"],
                                  gb.loc[m, "reliability"]),
                    textcoords="offset points", xytext=(dx, dy),
                    ha=ha, fontsize=6.8, color=INK_2, zorder=6)
    bx.set_xlabel("resolution  (higher = discriminates better)")
    bx.set_ylabel("reliability  (lower = better calibrated)")
    bx.set_title("(b)  The two axes are separate", loc="left", fontsize=8.5)
    # Bien trai/phai phai du rong: nhan duoc CAN GIUA diem nen no tran ra
    # ngoai neu de matplotlib tu chon gioi han.
    bx.set_xlim(0.127, 0.162)
    bx.set_ylim(0.022, 0.108)
    tidy(bx)
    save(fig, "fig6_threshold")


def main() -> int:
    print("Hinh cho ban dung lai Paper 2:")
    fig1_identity()
    fig5_reliability()
    fig6_threshold()
    fig2_paired()
    fig3_platt()
    fig4_refarm()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
