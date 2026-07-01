"""Sinh sơ đồ pipeline đánh giá reliability cho Paper 2 (Fig. schematic).

Mô phỏng phong cách Fig. 3 của Paper 1: pipeline zero-leakage matched-4D
→ 5 model → Platt → 3 metric → 3 regime. Lưu vào paper2/figs/.
KHÔNG đụng code cũ.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "paper" / "paper2" / "figs" / "p2_fig_pipeline.png"
OUT.parent.mkdir(parents=True, exist_ok=True)


def box(ax, x, y, w, h, text, fc, fs=8.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.02",
                                linewidth=1.0, edgecolor="#334155", facecolor=fc))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, zorder=5)


def arrow(ax, x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=11, linewidth=1.0, color="#475569"))


fig, ax = plt.subplots(figsize=(11, 4.6))
ax.set_xlim(0, 11); ax.set_ylim(0, 4.6); ax.axis("off")

PRE = "#DBEAFE"; QK = "#EDE9FE"; CAL = "#FEF3C7"; MET = "#DCFCE7"; REG = "#FFE4E6"

# Hàng 1: tiền xử lý zero-leakage (fit trên train) -----------------------------
ax.text(0.1, 4.35, "Zero-leakage preprocessing (fit on train only)", fontsize=8.5,
        style="italic", color="#1e3a8a")
pre = [("Raw NSL-KDD\n(122-d after OHE)", 0.1), ("SelectKBest\nANOVA F, K=20", 2.25),
       ("PCA\n4 components", 4.4), ("MinMax\n→ [0, π]", 6.1)]
for txt, x in pre:
    box(ax, x, 3.55, 1.9 if x == 0.1 else 1.55, 0.65, txt, PRE)
arrow(ax, 2.0, 3.875, 2.25, 3.875)
arrow(ax, 3.8, 3.875, 4.4, 3.875)
arrow(ax, 5.95, 3.875, 6.1, 3.875)

# Hàng 2: 5 model phân loại ----------------------------------------------------
ax.text(0.1, 3.15, "Classifiers (matched-4D, same input)", fontsize=8.5,
        style="italic", color="#5b21b6")
models = [("QSVM-ZZ\n4q, r=2, full", QK), ("SVM-RBF", QK),
          ("Random\nForest", QK), ("XGBoost", QK)]
mx = 0.6
for txt, fc in models:
    box(ax, mx, 2.35, 1.7, 0.62, txt, fc)
    mx += 1.95
arrow(ax, 6.875, 3.55, 4.0, 2.97)  # từ MinMax xuống dải model

# Hàng 3: Platt + metrics ------------------------------------------------------
box(ax, 0.1, 1.25, 2.4, 0.66, "Platt scaling\n(fit train → test)", CAL, 8.5)
arrow(ax, 4.0, 2.35, 1.3, 1.91)
mets = [("ECE", 3.1), ("Brier score", 4.5), ("AUC-PR /\nAUC-ROC", 6.3)]
for txt, x in mets:
    box(ax, x, 1.25, 1.5, 0.66, txt, MET, 8.5)
arrow(ax, 2.5, 1.58, 3.1, 1.58)
arrow(ax, 4.6, 1.58, 4.5, 1.58)

# Hàng 4: 3 regime đánh giá ----------------------------------------------------
ax.text(0.1, 0.95, "Evaluation regimes", fontsize=8.5, style="italic", color="#9f1239")
regs = [("Rare attacks\nU2R ∪ R2L  (C1/C2)", 0.1), ("Prior shift\nBal/Atk/DoS  (C3)", 3.7),
        ("Low-data\nN=100..1000  (A1)", 7.3)]
for txt, x in regs:
    box(ax, x, 0.15, 3.4, 0.62, txt, REG, 8.5)
arrow(ax, 3.85, 1.25, 1.8, 0.77)
arrow(ax, 5.25, 1.25, 5.4, 0.77)
arrow(ax, 7.05, 1.25, 9.0, 0.77)

# Nhánh Platt before/after (C4) ------------------------------------------------
box(ax, 8.7, 1.25, 2.1, 0.66, "Platt before/after\n(C4)", CAL, 8.0)
arrow(ax, 7.8, 1.58, 8.7, 1.58)

fig.tight_layout()
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print("[OK]", OUT)
