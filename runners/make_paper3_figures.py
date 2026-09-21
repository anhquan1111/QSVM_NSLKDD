"""Sinh hinh cho bai hoi nghi AICON 2026 (paper 3).

Chay:  python runners/make_paper3_figures.py
Xuat:  paper/paper3_aicon/figs/{fig1_tuning_trap,fig2_k_sweep}.{pdf,png}

Bai nay noi ve mot ca that: quy trinh tune chon ra C=0.01 va lam QSVM sup ve
du doan hang (tat ca la tan cong). Hinh phai cho thay CO CHE, khong phai chi
ket qua.

Co che nam gon trong Hinh 1(a): F1 cua bo phan loai hang tren cac fold CV la
mot NGUONG SAN. Ca bon kernel deu cham dung san do tai C=0.01. Linear va poly
vuot len tu C=0.1, RBF tu C=1.0 -- con quantum thi KHONG BAO GIO vuot. Nen
`argmax` giu nguyen C=0.01 cho rieng no. Bug khong nam o kernel luong tu; no
nam o cho lay argmax cua mot ham muc tieu co san suy bien.

Bang mau ke thua `runners/make_paper1_figures.py` (da qua
`scripts/validate_palette.js` cua skill dataviz). KHONG goi
`_assert_nsl_c1_matches_artifact()` cua script do: o day khong co hang so
NSL-KDD nao de doi chieu.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import matplotlib as mpl
import numpy as np

mpl.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper" / "paper3_aicon" / "figs"
OUT.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Token -- dong bo voi make_paper1_figures.py
# --------------------------------------------------------------------------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
INK_MUTED = "#7b7a75"
GRID = "#e4e3dd"
SHADE = "#f0efe9"

BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
VIOLET = "#4a3aa7"
NEUTRAL = "#b8b7b0"

# Mau gan theo thuc the, thu tu co dinh. Quantum giu mau xanh cua QSVM_ZZ o
# paper 1; ba kernel co dien ha xuong ba muc xam kem kieu net rieng, nen danh
# tinh khong bao gio chi dua vao mau (bat buoc voi ban in den trang).
KERNEL_STYLE: dict[str, dict] = {
    "quantum": dict(color=BLUE,      ls="-",               marker="o", lw=2.0, ms=6.0, z=6, label="Quantum (ZZ)"),
    "rbf":     dict(color="#6f6e69", ls=(0, (1, 1.6)),     marker="v", lw=1.4, ms=4.5, z=4, label="SVM-RBF"),
    "poly":    dict(color="#94938c", ls=(0, (3, 1, 1, 1)), marker="P", lw=1.4, ms=4.5, z=3, label="SVM-poly2"),
    "linear":  dict(color="#b0afa8", ls=(0, (4, 2, 1, 2)), marker="X", lw=1.4, ms=4.5, z=3, label="SVM-linear"),
}
KERNEL_ORDER = list(KERNEL_STYLE)

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


def load(rel: str) -> dict:
    """Doc JSON ket qua. Luon utf-8 -- Windows mac dinh cp1252."""
    with io.open(ROOT / rel, encoding="utf-8") as f:
        return json.load(f)


def tidy(ax, axis="y"):
    """Truc va luoi lui ve sau, du lieu noi len truoc."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.set_axisbelow(True)
    ax.grid(True, axis=axis, color=GRID, lw=0.6)
    ax.tick_params(length=2.5, width=0.7)


def save(fig, name: str):
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}")
    plt.close(fig)
    print(f"  -> {OUT.relative_to(ROOT).as_posix()}/{name}.pdf  (+ .png)")


# --------------------------------------------------------------------------
# Hinh 1 -- cai bay tune
# --------------------------------------------------------------------------
def fig1_tuning_trap():
    tune = load("results/unsw/c_tuning_results.json")
    deg = load("results/unsw/c3_results_statevector.json")["summary"]["quantum"]
    neu = load("results/unsw/c3_results_statevector_C1.json")["summary"]["quantum"]

    # Nguong san: diem CV ma MOI kernel dat duoc tai C=0.01. Do chinh la F1
    # cua bo phan loai hang. Lay tu chinh artifact chu khong viet tay.
    floor = min(r["mean"] for k in KERNEL_ORDER
                for r in tune[k]["scores_per_C"] if r["C"] == 0.01)
    assert all(
        any(abs(r["mean"] - floor) < 1e-15 for r in tune[k]["scores_per_C"] if r["C"] == 0.01)
        for k in KERNEL_ORDER
    ), "Gia dinh 'moi kernel cham san tai C=0.01' khong con dung"

    fig, (ax, bx) = plt.subplots(
        1, 2, figsize=(7.16, 3.05), gridspec_kw=dict(width_ratios=[1.38, 1.0], wspace=0.34)
    )

    # -- (a) diem CV theo C, voi nguong san --------------------------------
    ax.axhline(floor, color=ORANGE, lw=1.3, ls=(0, (4, 2)), zorder=2)
    # Dat nhan o goc phai tren duong san: vung C in [10,100] phia tren san
    # khong co duong nao di qua.
    ax.text(
        115, floor + 0.0022,
        f"constant all-attack classifier, $F_1={floor:.4f}$",
        color=ORANGE, fontsize=6.8, va="bottom", ha="right", zorder=7,
    )

    for key in KERNEL_ORDER:
        s = KERNEL_STYLE[key]
        rows = sorted(tune[key]["scores_per_C"], key=lambda r: r["C"])
        cs = [r["C"] for r in rows]
        # Linear va poly trung nhau tuyet doi o C>=0.1; day poly xuong mot
        # khoang nho de ca hai cung nhin thay duoc. Chi la dich hien thi.
        off = -0.0016 if key == "poly" else 0.0
        ms = [r["mean"] + off for r in rows]
        ax.plot(cs, ms, color=s["color"], ls=s["ls"], lw=s["lw"],
                marker=s["marker"], ms=s["ms"], mew=0.6, mec=SURFACE,
                zorder=s["z"], label=s["label"])
        # Danh dau gia tri C ma argmax tra ve.
        cb = tune[key]["C_best"]
        mb = next(r["mean"] for r in rows if r["C"] == cb) + off
        ax.plot([cb], [mb], marker="o", ms=s["ms"] + 5.5, mfc="none",
                mec=s["color"], mew=1.5, zorder=s["z"] + 1)

    ax.set_xscale("log")
    ax.set_xlabel("SVM regularisation $C$  (log scale)")
    ax.set_ylabel("5-fold CV $F_1$")
    ax.set_title("(a)  Selection cannot escape the floor", loc="left")
    ax.set_ylim(0.740, 0.903)
    tidy(ax)
    ax.legend(loc="lower left", ncol=2, handlelength=2.3, columnspacing=1.0,
              borderpad=0.2, labelspacing=0.3, bbox_to_anchor=(-0.01, -0.02))

    # -- (b) hau qua tren tap test -----------------------------------------
    # TN khong nam trong summary; lay tu khoi so sanh da luu san.
    cmp_block = load("results/unsw/c3_results_statevector_C1.json")["comparison_vs_1_4a"]
    tn_old = cmp_block["tn_mean_old"]["quantum"]
    tn_new = cmp_block["tn_mean_new"]["quantum"]

    # So mau am cua tap test, doc tu ma tran nham lan da luu chu khong viet tay.
    cm = load("results/unsw/c1_results.json")["k_sweep"][0]["per_run"][0]["quantum"]
    n_neg = cm["tn"] + cm["fp"]

    # Dua TN ve specificity = TN / (so mau am), nen ca bon thanh cung thang
    # [0,1]; so dem that van duoc ghi len nhan.
    labels = ["Recall", "Precision", "Accuracy", "Specificity\n(TN rate)"]
    old = [deg["recall_mean"], deg["precision_mean"], deg["accuracy_mean"], tn_old / n_neg]
    new = [neu["recall_mean"], neu["precision_mean"], neu["accuracy_mean"], tn_new / n_neg]

    y = np.arange(len(labels))
    h = 0.34
    bx.barh(y + h / 2, old, height=h, color=ORANGE, alpha=0.85,
            label="tuned $C=0.01$", zorder=4)
    bx.barh(y - h / 2, new, height=h, color=BLUE, alpha=0.85,
            label="neutral $C=1.0$", zorder=4)

    for i, (o, n) in enumerate(zip(old, new)):
        last = i == len(labels) - 1
        otxt = f"{o:.3f}  ({tn_old:.1f}/{n_neg})" if last else f"{o:.3f}"
        ntxt = f"{n:.3f}  ({tn_new:.1f}/{n_neg})" if last else f"{n:.3f}"
        bx.text(o + 0.015, i + h / 2, otxt, va="center", ha="left",
                fontsize=7, color=INK_2, zorder=5)
        bx.text(n + 0.015, i - h / 2, ntxt, va="center", ha="left",
                fontsize=7, color=INK_2, zorder=5)

    bx.set_yticks(y)
    bx.set_yticklabels(labels)
    bx.invert_yaxis()
    bx.set_xlim(0, 1.46)
    bx.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    bx.set_xlabel("Test-set value")
    bx.set_title("(b)  What the selected $C$ costs", loc="left")
    tidy(bx, axis="x")
    bx.legend(loc="lower left", ncol=2, borderpad=0.2, labelspacing=0.3,
              columnspacing=1.0, bbox_to_anchor=(-0.01, -0.02))

    save(fig, "fig1_tuning_trap")


# --------------------------------------------------------------------------
# Hinh 2 -- kernel vo can
# --------------------------------------------------------------------------
def fig2_k_sweep():
    c1 = load("results/unsw/c1_results.json")
    rows = sorted(c1["k_sweep"], key=lambda e: e["K"])
    ks = [e["K"] for e in rows]
    f1 = [e["summary"]["quantum"]["f1_mean"] for e in rows]
    ndeg = [sum(1 for r in e["per_run"] if r["quantum"]["is_degenerate"]) for e in rows]
    nrun = c1["metadata"]["n_runs"]

    # Nguong suy bien: F1 cua bo phan loai hang, da luu trong tung run.
    floor = rows[0]["per_run"][0]["quantum"]["f1_predict_all_attack"]

    fig, ax = plt.subplots(figsize=(3.48, 2.6))

    ax.axhline(floor, color=ORANGE, lw=1.3, ls=(0, (4, 2)), zorder=2)
    ax.text(10.4, floor - 0.0016, "degenerate $F_1$", color=ORANGE,
            fontsize=7, va="top", ha="left", zorder=6)

    s = KERNEL_STYLE["quantum"]
    ax.plot(ks, f1, color=s["color"], ls=s["ls"], lw=s["lw"], marker=s["marker"],
            ms=s["ms"], mew=0.6, mec=SURFACE, zorder=6)

    # Cao nguyen: ba gia tri K cuoi trung nhau toi 16 chu so.
    plateau = [i for i, v in enumerate(f1) if abs(v - f1[-1]) < 1e-15]
    if len(plateau) > 1:
        ax.axvspan(ks[plateau[0]], ks[-1], color=SHADE, zorder=1)
        ax.text(
            (ks[plateau[0]] * ks[-1]) ** 0.5, 0.7805,
            f"identical to 16 s.f.\n$K \\geq {ks[plateau[0]]}$",
            fontsize=6.8, color=INK_MUTED, ha="center", va="bottom", zorder=5,
        )

    ax.set_xscale("log")
    ax.set_xticks(ks)
    ax.set_xticklabels([str(k) for k in ks])
    ax.minorticks_off()
    ax.set_xlabel("SelectKBest $K$")
    ax.set_ylabel("Macro $F_1$, quantum kernel")
    ax.set_title(f"At $C=1.0$: {sum(ndeg)}/{len(ks) * nrun} runs degenerate", loc="left")
    ax.set_ylim(0.7765, 0.816)
    tidy(ax)

    save(fig, "fig2_k_sweep")


def main() -> int:
    print("Sinh hinh cho paper 3 (AICON 2026):")
    fig1_tuning_trap()
    fig2_k_sweep()
    print(f"\n  Tat ca nam trong {OUT.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
