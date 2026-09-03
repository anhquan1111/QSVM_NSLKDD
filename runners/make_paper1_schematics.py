"""Ba hinh so do cua paper 1: mach ZZFeatureMap, phan ra dong gop, pipeline.

Ba hinh nay KHONG phu thuoc du lieu -- chung mo ta dinh nghia va quy trinh, nen
ve tay bang matplotlib de kiem soat hoan toan bo cuc va dung chung bo token mau
voi cac hinh co du lieu.

Vi sao khong xuat tu Qiskit: `ZZFeatureMap(4, reps=2).decompose()` cho ra `u` va
`cx` chung chung, mat het nhan `H`, `P(2x_i)` va cau truc CNOT-RZ-CNOT ma bai
can chi ra. So CNOT trong hinh da doi chieu voi `count_ops()` cua Qiskit: 24.

Luu y ve mathtext cua matplotlib: khong nhan `bm` va `ge`; phai dung `mathbf`
va `geq`.

Chay:  python runners/make_paper1_schematics.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper" / "paper1" / "figs_revision"
OUT.mkdir(parents=True, exist_ok=True)

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
INK_MUTED = "#7b7a75"
GRID = "#e4e3dd"
WIRE = "#3f3e3a"

BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
VIOLET = "#4a3aa7"

TINT = {BLUE: "#e3edfa", ORANGE: "#fceae2", AQUA: "#e0f4ed", VIOLET: "#e7e4f5"}

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "font.family": "DejaVu Sans",
    "savefig.bbox": "tight", "savefig.dpi": 400, "pdf.fonttype": 42,
})


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}")
    plt.close(fig)
    print(f"  -> {OUT.relative_to(ROOT)}/{name}.pdf  (+ .png)")


def blank(ax, xlim, ylim):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis("off")


def gate(ax, x, y, label, w=0.5, h=0.34, colour=INK, fill=SURFACE, fs=7.5):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                boxstyle="round,pad=0.02,rounding_size=0.05",
                                fc=fill, ec=colour, lw=1.0, zorder=5))
    ax.text(x, y, label, ha="center", va="center", fontsize=fs, color=INK, zorder=6)


def box(ax, x, y, w, h, title, body=None, colour=BLUE, fs=8, fs_body=7):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=TINT.get(colour, SURFACE), ec=colour, lw=1.2,
                                zorder=5))
    ty = y + (0.16 * h if body else 0)
    ax.text(x, ty, title, ha="center", va="center", fontsize=fs,
            fontweight="bold", color=INK, zorder=6)
    if body:
        ax.text(x, y - 0.22 * h, body, ha="center", va="center",
                fontsize=fs_body, color=INK_2, zorder=6, linespacing=1.35)


def arrow(ax, x0, y0, x1, y1, colour=INK_MUTED, lw=1.1, style="-|>"):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle=style, color=colour, lw=lw,
                                shrinkA=2, shrinkB=2), zorder=4)


# ---------------------------------------------------------------------------
# Fig 1 -- mach ZZFeatureMap
# ---------------------------------------------------------------------------
def figure1():
    fig, axes = plt.subplots(2, 1, figsize=(7.16, 4.7),
                             gridspec_kw={"height_ratios": [1.0, 1.12]})
    ys = [3.4, 2.5, 1.6, 0.7]

    # ---- (a) cau truc theo tang, khoi vuong da duoc truu tuong hoa ----
    ax = axes[0]
    blank(ax, (-0.9, 9.6), (-0.6, 4.3))
    for i, y in enumerate(ys):
        ax.plot([-0.35, 8.7], [y, y], color=WIRE, lw=0.9, zorder=2)
        ax.text(-0.5, y, "$|0\\rangle$", ha="right", va="center", fontsize=8,
                color=INK)
        for x0 in (0.35, 4.60):
            gate(ax, x0, y, "$H$")
            gate(ax, x0 + 1.0, y, f"$P(2x_{{{i + 1}}})$", w=1.05)
    for x0 in (2.60, 6.85):
        ax.add_patch(FancyBboxPatch((x0 - 0.60, ys[-1] - 0.35), 1.20,
                                    ys[0] - ys[-1] + 0.70,
                                    boxstyle="round,pad=0.02,rounding_size=0.06",
                                    fc=TINT[VIOLET], ec=VIOLET, lw=1.3, zorder=5))
        ax.text(x0, (ys[0] + ys[-1]) / 2, "$U_{\\mathrm{ent}}(\\mathbf{x})$",
                ha="center", va="center", fontsize=8.5, color=INK, zorder=6)
    for xa, xb, lab in ((-0.05, 3.25, "Layer $\\ell=1$"),
                        (4.20, 7.50, "Layer $\\ell=2$ (repeat)")):
        ax.annotate("", xy=(xb, -0.10), xytext=(xa, -0.10),
                    arrowprops=dict(arrowstyle="|-|", color=GRID, lw=1.0))
        ax.text((xa + xb) / 2, -0.30, lab, ha="center", va="top", fontsize=7.5,
                color=INK_2, style="italic")
    ax.text(8.9, (ys[0] + ys[-1]) / 2, "$|\\phi(\\mathbf{x})\\rangle$", ha="left",
            va="center", fontsize=9, color=INK)
    ax.text(-0.85, 4.15, "(a)", fontsize=10, fontweight="bold", color=INK)

    # ---- (b) phan ra gate-level cua mot khoi U_ent ----
    ax = axes[1]
    blank(ax, (-0.9, 9.6), (-1.9, 4.3))
    for i, y in enumerate(ys):
        ax.plot([-0.35, 8.9], [y, y], color=WIRE, lw=0.9, zorder=2)
        ax.text(-0.5, y, f"$q_{{{i + 1}}}$", ha="right", va="center", fontsize=8,
                color=INK)

    x = 0.5
    for a, b in [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3)]:
        ya, yb = ys[a], ys[b]
        for xc in (x, x + 1.32):                       # hai CNOT om lay RZ
            ax.plot([xc, xc], [ya, yb], color=WIRE, lw=1.0, zorder=3)
            ax.add_patch(Circle((xc, ya), 0.055, fc=WIRE, ec=WIRE, zorder=6))
            ax.add_patch(Circle((xc, yb), 0.16, fc=SURFACE, ec=WIRE, lw=1.0,
                                zorder=6))
            ax.plot([xc - 0.16, xc + 0.16], [yb, yb], color=WIRE, lw=0.9, zorder=7)
            ax.plot([xc, xc], [yb - 0.16, yb + 0.16], color=WIRE, lw=0.9, zorder=7)
        gate(ax, x + 0.66, yb, f"$R_Z(\\varphi_{{{a + 1}{b + 1}}})$", w=1.05,
             colour=VIOLET, fill=TINT[VIOLET], fs=6.5)
        x += 1.66

    ax.text(x + 0.35, (ys[0] + ys[-1]) / 2, "$\\cdots$", ha="center",
            va="center", fontsize=12, color=INK_MUTED)
    ax.text(-0.85, 4.15, "(b)", fontsize=10, fontweight="bold", color=INK)
    ax.text(-0.35, -0.30,
            "Pair $(3,4)$ omitted for space; the pattern is identical, "
            "$\\mathrm{CNOT}_{34}\\,R_Z(\\varphi_{34})\\,\\mathrm{CNOT}_{34}$.",
            ha="left", va="top", fontsize=7, color=INK_2)
    ax.text(-0.35, -0.80,
            "Full entanglement on 4 qubits gives $\\binom{4}{2}=6$ trios per "
            "layer, so $24$ CNOTs in total at $r=2$.",
            ha="left", va="top", fontsize=7, color=INK_2)
    ax.text(-0.35, -1.30,
            "$\\varphi_{ij}(\\mathbf{x}) = 2(\\pi - x_i)(\\pi - x_j)$ encodes the "
            "pairwise feature interaction into the quantum phase.",
            ha="left", va="top", fontsize=7, color=INK_2)

    fig.suptitle("ZZFeatureMap circuit, $n=4$ qubits, $r=2$ repetitions, "
                 "full entanglement",
                 x=0.012, y=0.995, ha="left", fontsize=10, fontweight="bold",
                 color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    save(fig, "fig1_zzfeaturemap_circuit")


# ---------------------------------------------------------------------------
# Fig 2 -- phan ra bai toan thanh bon dong gop
# ---------------------------------------------------------------------------
def figure2():
    rows = [
        ("C1", BLUE, "Representation",
         "KDDTrain$^+$\nUNSW train",
         "Three-stage rule:\n$V\\geq T$, KTA, min $Q$",
         "$V(n)$, KTA$(n)$,\n$Q(n)$, $n^\\ast$",
         "Figs. 4-5"),
        ("C2", VIOLET, "Entanglement",
         "$N_{\\mathrm{train}}{=}1000$\n10 runs",
         "ZZ vs Z ablation,\npaired within run",
         "$\\Delta$KTA, $\\Delta F_1$,\nnoise validation",
         "Figs. 6-7"),
        ("C3", AQUA, "Distribution shift",
         "KDDTest$^+$,\nKDDTest$^{-21}$",
         "Prior shift, perturbation,\nattack composition",
         "$\\Delta F_1$, Holm,\nMcNemar",
         "Fig. 8"),
        ("C4", ORANGE, "Sample complexity",
         "Nested subsets\n$N{=}10^2$-$10^4$",
         "Two sampling regimes,\ntwo tuning arms",
         "Learning curve,\ncrossover, rare $F_1$",
         "Figs. 9, 11"),
    ]
    fig, ax = plt.subplots(figsize=(7.16, 3.3))
    blank(ax, (-0.2, 10.6), (-0.35, 5.35))

    heads = ["Contribution", "Data", "Protocol", "Metrics", "Reported in"]
    xs = [1.0, 3.1, 5.4, 7.7, 9.7]
    for x, h in zip(xs, heads):
        ax.text(x, 5.05, h, ha="center", va="center", fontsize=8,
                fontweight="bold", color=INK_2)
    ax.plot([-0.1, 10.5], [4.78, 4.78], color=GRID, lw=1.0)

    for i, (cid, colour, name, data, proto, metric, where) in enumerate(rows):
        y = 4.15 - i * 1.12
        box(ax, xs[0], y, 1.75, 0.86, cid, name, colour=colour, fs=9, fs_body=7)
        for x, txt in zip(xs[1:4], (data, proto, metric)):
            ax.text(x, y, txt, ha="center", va="center", fontsize=7,
                    color=INK_2, linespacing=1.4)
        ax.text(xs[4], y, where, ha="center", va="center", fontsize=7.5,
                color=colour, fontweight="bold")
        for a, b in zip(xs[:-1], xs[1:]):
            arrow(ax, a + (0.92 if a == xs[0] else 0.75), y, b - 0.75, y,
                  colour=GRID, lw=0.9)
        if i < len(rows) - 1:
            ax.plot([-0.1, 10.5], [y - 0.56, y - 0.56], color=GRID, lw=0.6)

    fig.suptitle("Each contribution answers one question with its own protocol",
                 x=0.012, y=0.99, ha="left", fontsize=10, fontweight="bold",
                 color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.945))
    save(fig, "fig2_contribution_map")


# ---------------------------------------------------------------------------
# Fig 3 -- pipeline dau-cuoi
# ---------------------------------------------------------------------------
def figure3():
    """Chu mo ta dat DUOI hop chu khong nhet vao trong.

    Nhet ca ten lan mo ta vao trong hop thi be rong hop phai chay theo chuoi
    dai nhat; o kho hai cot IEEE cac hop se de len nhau. Dat mo ta duoi hop
    cho phep hop nho va deu nhau.
    """
    stages = [
        ("Raw data", "122 dims\nafter OHE", BLUE),
        ("SelectKBest", "ANOVA $F$\n$K=20$", BLUE),
        ("PCA", "$n^\\ast=4$\ncomponents", BLUE),
        ("MinMax", "scale to\n$[0,\\pi]$", BLUE),
        ("ZZFeatureMap", "$r=2$, full ent.\nfidelity kernel", VIOLET),
        ("SVC", "precomputed\nGram", AQUA),
    ]
    fig, ax = plt.subplots(figsize=(7.16, 3.2))
    blank(ax, (-0.62, 5.75), (-2.35, 1.75))

    y = 0.0
    for i, (title, body, colour) in enumerate(stages):
        box(ax, i, y, 0.84, 0.40, title, colour=colour, fs=7.2)
        ax.text(i, y - 0.30, body, ha="center", va="top", fontsize=6.6,
                color=INK_2, linespacing=1.35)
        if i:
            arrow(ax, i - 1 + 0.44, y, i - 0.44, y)

    # Khoi C1 cap n* cho tang PCA -- day la cho THAY THE khoi Pareto cu.
    box(ax, 2.0, -1.55, 3.5, 0.52, "C1: three-stage selection rule",
        colour=ORANGE, fs=7.8)
    ax.text(2.0, -1.95, "$V(n)\\geq 0.85$   then   KTA within 5%   then   "
                        "min CNOT cost",
            ha="center", va="top", fontsize=6.8, color=INK_2)
    arrow(ax, 2.0, -1.29, 2.0, -0.88, colour=ORANGE, lw=1.2)
    ax.text(2.10, -1.08, "fixes $n^\\ast$", ha="left", va="center", fontsize=6.8,
            color=ORANGE)

    # Nhanh doi chung cua C2.
    box(ax, 4.0, 1.15, 1.5, 0.42, "ZFeatureMap (control)", colour=VIOLET, fs=7)
    arrow(ax, 4.0, 0.94, 4.0, 0.22, colour=VIOLET, lw=1.0, style="<|-")
    ax.text(4.82, 1.15, "C2 ablation:\nentangling layer\nremoved", ha="left",
            va="center", fontsize=6.6, color=INK_2, linespacing=1.35)

    fig.suptitle("End-to-end pipeline; the C1 rule replaces the Pareto search",
                 x=0.012, y=0.985, ha="left", fontsize=10, fontweight="bold",
                 color=INK)
    fig.text(0.012, 0.055,
             "Every transformer is fit on the training fold only and applied "
             "unchanged to the test fold. In the primary arm the whole front-end "
             "is refit at each $N$,\nso no representation ever sees more data "
             "than the classifier it feeds.",
             ha="left", va="bottom", fontsize=7, color=INK_MUTED, linespacing=1.4)
    fig.tight_layout(rect=(0, 0.10, 1, 0.94))
    save(fig, "fig3_pipeline")


if __name__ == "__main__":
    print("Sinh ba hinh so do")
    figure1()
    figure2()
    figure3()
    print("Xong.")
