"""Thong ke bat cap cho ban dung lai cua Paper 2.

    python runners/analyze_p2_rebuild.py

Ban da nop chi bao Cohen's d, khong mot phep kiem gia thuyet nao va khong
hieu chinh da so sanh. O day dung dung giao thuc cua Paper 1: Wilcoxon bat
cap + khoang tin cay bootstrap + d_z, roi Holm TRONG TUNG HO baseline.

Vi sao phai 10 run: voi 5 cap, Wilcoxon hai phia co p nho nhat la 0,0625 --
khong bao gio qua duoc 0,05, du hieu ung lon den may. Moi ket luan se thanh
"inconclusive" mot cach may moc, khong phai vi du lieu yeu.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

IN_DIR = ROOT / "results" / "nslkdd" / "p2_rebuild"
RNG = np.random.default_rng(42)
N_BOOT = 10_000

REFERENCE = "QSVM"
BASELINES = ["SVM-RBF", "MLP", "RandomForest", "XGBoost"]
# Ho baseline -- Holm ap TRONG tung ho, giong Paper 1. Gop het vao mot ho la
# tu phat minh ra mot phep hieu chinh khac voi bai companion.
FAMILY = {"SVM-RBF": "kernel", "MLP": "neural",
          "RandomForest": "tree", "XGBoost": "tree"}
METRICS = ["ece_rare", "brier_rare", "ece_full", "brier_full", "auc_pr", "f1"]
# Voi ECE/Brier thi THAP hon la tot hon; AUC-PR va F1 thi CAO hon tot hon.
LOWER_BETTER = {"ece_rare", "brier_rare", "ece_full", "brier_full"}


def boot_ci(d: np.ndarray, n=N_BOOT, alpha=0.05):
    idx = RNG.integers(0, len(d), size=(n, len(d)))
    means = d[idx].mean(axis=1)
    return float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))


def dz(d: np.ndarray) -> float:
    s = d.std(ddof=1)
    return float(d.mean() / s) if s > 0 else float("nan")


def holm(pvals: list[float]) -> list[float]:
    """Holm-Bonferroni, tra ve p da hieu chinh, giu nguyen thu tu dau vao."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj


def main() -> int:
    df = pd.read_csv(IN_DIR / "p2_rebuild_per_run.csv")
    rows = []

    for test_set in df.test_set.unique():
        sub = df[df.test_set == test_set]
        for metric in METRICS:
            piv = sub.pivot_table(index="run_id", columns="model", values=metric)
            ref = piv[REFERENCE].to_numpy(float)
            recs = []
            for b in BASELINES:
                d = ref - piv[b].to_numpy(float)          # QSVM tru baseline
                lo, hi = boot_ci(d)
                p = stats.wilcoxon(d).pvalue if np.any(d != 0) else 1.0
                recs.append(dict(
                    test_set=test_set, metric=metric, baseline=b,
                    family=FAMILY[b], n_runs=len(d),
                    mean_delta=float(d.mean()), ci_low=lo, ci_high=hi,
                    wilcoxon_p=float(p), dz=dz(d),
                ))
            # Holm trong tung ho.
            for fam in {r["family"] for r in recs}:
                grp = [r for r in recs if r["family"] == fam]
                adj = holm([r["wilcoxon_p"] for r in grp])
                for r, a in zip(grp, adj):
                    r["holm_p"] = a
            rows += recs

    out = pd.DataFrame(rows)

    def verdict(r):
        if r["holm_p"] >= 0.05:
            return "inconclusive"
        better = r["mean_delta"] < 0 if r["metric"] in LOWER_BETTER else r["mean_delta"] > 0
        return "QSVM-favorable" if better else "baseline-favorable"

    out["verdict"] = out.apply(verdict, axis=1)
    csv = IN_DIR / "p2_rebuild_pairwise.csv"
    out.to_csv(csv, index=False, encoding="utf-8")

    for test_set in out.test_set.unique():
        print(f"\n{'=' * 74}\n  {test_set}\n{'=' * 74}")
        for metric in ("ece_rare", "brier_rare"):
            s = out[(out.test_set == test_set) & (out.metric == metric)]
            print(f"\n  {metric}   (QSVM tru baseline; am = QSVM tot hon)")
            for _, r in s.iterrows():
                print(f"    vs {r['baseline']:13s} {r['mean_delta']:+.4f} "
                      f"[{r['ci_low']:+.4f},{r['ci_high']:+.4f}]  "
                      f"p={r['wilcoxon_p']:.4f} holm={r['holm_p']:.4f} "
                      f"d_z={r['dz']:+.2f}  {r['verdict']}")

    print(f"\n  -> {csv.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
