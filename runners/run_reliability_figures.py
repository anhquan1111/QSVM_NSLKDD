"""
C1/C2 — Hoàn thiện phần Calibration + Rare-Attack Reliability cho Paper 2.

Đọc kết quả Bước 1 (`p2_verify_calibration.json`), tính Cohen's d (QSVM vs từng
baseline) cho ECE_rare / Brier_rare / AUC-PR, và vẽ các hình chính:
  - Figure: ECE_rare & Brier_rare (bar ± std) — QSVM vs DL/ML
  - Figure: AUC-PR vs Brier_rare (scatter) — minh hoạ "rank tốt nhưng overconfident"

Không tính kernel lượng tử — chỉ dùng số đã có. KHÔNG sửa code cũ.
Chạy: python runners/run_reliability_figures.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.reliability import cohens_d  # noqa: E402

DATA_DIR = ROOT / "data" / "processed_data"
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
IN_PATH = DATA_DIR / "p2_verify_calibration.json"
OUT_STATS = DATA_DIR / "p2_calibration_stats.json"

MODEL_COLORS = {
    "QSVM": "#8B5CF6", "SVM-RBF": "#F59E0B", "MLP": "#3B82F6",
    "RandomForest": "#10B981", "XGBoost": "#EF4444",
}


def main():
    data = json.load(open(IN_PATH, encoding="utf-8"))
    df = pd.DataFrame(data["per_run"])
    models = [m for m in MODEL_COLORS if m in df["model"].unique()]

    # ── Cohen's d: QSVM vs từng baseline (trên 5 run) ────────────────────────
    # d>0 cho ECE/Brier ⇒ QSVM CAO hơn (xấu hơn); ta báo dấu để dễ đọc.
    stats = {}
    q = df[df["model"] == "QSVM"].sort_values("run_id")
    print("=" * 74)
    print("Cohen's d (QSVM − baseline) qua 5 run  | ECE_rare, Brier_rare âm ⇒ QSVM tốt hơn")
    print("=" * 74)
    print(f"{'Baseline':12s} {'d(ECE_rare)':>14s} {'d(Brier_rare)':>14s} {'d(AUC-PR)':>14s}")
    for mdl in models:
        if mdl == "QSVM":
            continue
        b = df[df["model"] == mdl].sort_values("run_id")
        d_ece = cohens_d(q["ece_rare"].values, b["ece_rare"].values)
        d_bri = cohens_d(q["brier_rare"].values, b["brier_rare"].values)
        d_auc = cohens_d(q["auc_pr"].values, b["auc_pr"].values)
        stats[mdl] = {"d_ece_rare": d_ece, "d_brier_rare": d_bri, "d_auc_pr": d_auc}
        print(f"{mdl:12s} {d_ece:>14.3f} {d_bri:>14.3f} {d_auc:>14.3f}")

    json.dump(stats, open(OUT_STATS, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"\n[OK] Cohen's d → {OUT_STATS}")

    agg = df.groupby("model").agg(["mean", "std"])

    # ── Figure 1: ECE_rare & Brier_rare bar ± std ────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, metric, title in zip(
        axes, ["ece_rare", "brier_rare"],
        ["ECE on rare attacks (thấp = đáng tin hơn)", "Brier score on rare attacks (thấp = tốt)"],
    ):
        means = [agg.loc[m, (metric, "mean")] for m in models]
        stds = [agg.loc[m, (metric, "std")] for m in models]
        colors = [MODEL_COLORS[m] for m in models]
        bars = ax.bar(models, means, yerr=stds, capsize=4, color=colors, alpha=0.88)
        bars[models.index("QSVM")].set_edgecolor("black")
        bars[models.index("QSVM")].set_linewidth(2)
        ax.set_title(title, fontsize=11)
        ax.set_ylabel(metric)
        ax.tick_params(axis="x", rotation=20)
    fig.suptitle("Paper 2 — QSVM đáng tin nhất trên tấn công hiếm (5 run, mean ± std)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    f1 = REPORTS_DIR / "p2_fig_ece_brier_rare.png"
    fig.savefig(f1, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {f1}")

    # ── Figure 2: AUC-PR vs Brier_rare scatter ───────────────────────────────
    fig, ax = plt.subplots(figsize=(6.2, 5))
    for m in models:
        ax.scatter(agg.loc[m, ("auc_pr", "mean")], agg.loc[m, ("brier_rare", "mean")],
                   s=180, color=MODEL_COLORS[m], edgecolor="black",
                   linewidth=1.5 if m == "QSVM" else 0.5, zorder=3, label=m)
        ax.annotate(m, (agg.loc[m, ("auc_pr", "mean")], agg.loc[m, ("brier_rare", "mean")]),
                    textcoords="offset points", xytext=(8, 4), fontsize=9)
    ax.set_xlabel("AUC-PR (rank chất lượng — cao = tốt) →")
    ax.set_ylabel("Brier_rare (độ tin cậy — thấp = tốt) ↓")
    ax.set_title("Rank tốt ≠ đáng tin:\ncây (RF/XGB) rank cao nhưng overconfident; QSVM tin cậy nhất",
                 fontsize=10)
    ax.grid(alpha=0.3)
    f2 = REPORTS_DIR / "p2_fig_aucpr_vs_brier.png"
    fig.savefig(f2, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {f2}")


if __name__ == "__main__":
    main()
