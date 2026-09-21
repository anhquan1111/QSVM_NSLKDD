"""Thong ke bat cap cho ban dung lai cua Paper 2 -- ca hai dataset.

    python runners/analyze_p2_rebuild.py

Ban da nop chi bao Cohen's d, khong mot phep kiem gia thuyet nao va khong
hieu chinh da so sanh. O day dung dung giao thuc cua Paper 1: Wilcoxon bat
cap + khoang tin cay bootstrap + d_z, roi Holm TRONG TUNG HO baseline.

Vi sao phai 10 run: voi 5 cap, Wilcoxon hai phia co p nho nhat la 0,0625 --
khong bao gio qua duoc 0,05, du hieu ung lon den may.

CHI SO CHINH LA `ece_full`, KHONG PHAI `ece_rare`. Tap tan cong hiem chi co
MOT lop (toan tan cong) tren ca hai dataset, nen acc(bin)=1 o moi bin theo
dinh nghia va

    ECE_rare = sum_b (n_b/n)|1 - conf(b)| = 1 - trung binh(p)

dung den sai so may -- mot phep do DO TU TIN tren tan cong da biet, khong
phai calibration. `ece_rare` van duoc tinh va bao cao, nhung duoi dung ten
cua no. Tren toan tap test thi co ca hai lop nen ECE do calibration that.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NSL = ROOT / "results" / "nslkdd" / "p2_rebuild"
UNSW = ROOT / "results" / "unsw" / "p2_rebuild"
RNG = np.random.default_rng(42)
N_BOOT = 10_000

REFERENCE = "QSVM"
BASELINES = ["SVM-RBF", "MLP", "RandomForest", "XGBoost"]
FAMILY = {"SVM-RBF": "kernel", "MLP": "neural",
          "RandomForest": "tree", "XGBoost": "tree"}
METRICS = ["ece_full", "brier_full", "ece_rare", "brier_rare", "auc_pr", "f1"]
LOWER_BETTER = {"ece_full", "brier_full", "ece_rare", "brier_rare"}


def boot_ci(d, n=N_BOOT, alpha=0.05):
    idx = RNG.integers(0, len(d), size=(n, len(d)))
    means = d[idx].mean(axis=1)
    return float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))


def dz(d):
    s = d.std(ddof=1)
    return float(d.mean() / s) if s > 0 else float("nan")


def holm(pvals):
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj, running = [0.0] * m, 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj


def load_settings() -> pd.DataFrame:
    """Gop hai dataset thanh mot bang dai, khoa boi cot `setting`."""
    frames = []
    n = pd.read_csv(NSL / "p2_rebuild_per_run.csv")
    n["setting"] = "NSL-KDD/" + n.test_set.map(
        {"full_kddtest_plus": "full", "kddtest21": "test21",
         "sample100_cu": "sample100"})
    frames.append(n)
    p = UNSW / "p2_unsw_per_run.csv"
    if p.exists():
        u = pd.read_csv(p)
        u["setting"] = "UNSW/" + u.n_qubits.astype(str) + "qb"
        frames.append(u)
    return pd.concat(frames, ignore_index=True)


def cal_tests() -> pd.DataFrame:
    """Tung bo hieu chinh so voi xac suat goc, bat cap theo run.

    Can co, vi hinh fig3 va muc dong gop deu phat bieu "giup mo hinh nao,
    hai mo hinh nao". Truoc day cau do dua tren so sanh hai TRUNG BINH --
    va no sai: temperature scaling ha ECE cua SVM-RBF tu 0,117 xuong 0,114,
    nhung chi thang o 5/10 run, tuc la khong phan biet duoc voi khong doi.
    Chi co phep kiem bat cap moi tach duoc "giup" khoi "khong tac dung".
    """
    cal = pd.read_csv(NSL / "p2_rebuild_calibrators.csv")
    piv = cal.pivot_table(index=["model", "run_id"], columns="calibrator",
                          values="ece_full")
    methods = ["platt", "isotonic", "temperature"]
    rows = []
    for model in piv.index.get_level_values("model").unique():
        s = piv.loc[model]
        base = s["none"].to_numpy(float)
        recs = []
        for m in methods:
            d = s[m].to_numpy(float) - base
            lo, hi = boot_ci(d)
            recs.append(dict(
                model=model, calibrator=m, n_runs=len(d),
                ece_none=float(base.mean()), ece_cal=float(s[m].mean()),
                mean_delta=float(d.mean()), ci_low=lo, ci_high=hi,
                n_better=int((d < 0).sum()), dz=dz(d),
                wilcoxon_p=float(stats.wilcoxon(d).pvalue)))
        for r, a in zip(recs, holm([r["wilcoxon_p"] for r in recs])):
            r["holm_p"] = a
            r["verdict"] = ("no effect" if a >= 0.05
                            else "helps" if r["mean_delta"] < 0 else "hurts")
        rows += recs
    out = pd.DataFrame(rows)

    # Mot the duy nhat cho ca mo hinh: chi goi la "giup" khi MOI bo hieu
    # chinh deu giup, "hai" khi moi bo deu hai, con lai la khong tac dung.
    best = []
    for model, g in out.groupby("model"):
        v = set(g.verdict)
        best.append(dict(model=model,
                         overall=("helps" if v == {"helps"}
                                  else "hurts" if v == {"hurts"}
                                  else "no effect"),
                         best_delta=float(g.mean_delta.min()),
                         worst_delta=float(g.mean_delta.max())))
    out = out.merge(pd.DataFrame(best), on="model")
    csv = NSL / "p2_rebuild_cal_tests.csv"
    out.to_csv(csv, index=False, encoding="utf-8")
    print("\n  Hieu chinh hau ky so voi xac suat goc (am = tot len):")
    for model, g in out.groupby("model"):
        print(f"    {model:13s} {g.overall.iloc[0]:10s}  " + "  ".join(
            f"{r.calibrator[:4]} {r.mean_delta:+.4f} "
            f"({r.n_better}/{r.n_runs}, holm={r.holm_p:.3f})"
            for r in g.itertuples()))
    print(f"  -> {csv.relative_to(ROOT).as_posix()}  ({len(out)} dong)")
    return out


def main() -> int:
    df = load_settings()
    rows = []
    for setting in df.setting.unique():
        sub = df[df.setting == setting]
        for metric in METRICS:
            if metric not in sub or sub[metric].isna().all():
                continue
            piv = sub.pivot_table(index="run_id", columns="model", values=metric)
            if REFERENCE not in piv:
                continue
            ref = piv[REFERENCE].to_numpy(float)
            recs = []
            for b in BASELINES:
                if b not in piv:
                    continue
                d = ref - piv[b].to_numpy(float)
                lo, hi = boot_ci(d)
                p = stats.wilcoxon(d).pvalue if np.any(d != 0) else 1.0
                recs.append(dict(setting=setting, metric=metric, baseline=b,
                                 family=FAMILY[b], n_runs=len(d),
                                 mean_delta=float(d.mean()), ci_low=lo, ci_high=hi,
                                 wilcoxon_p=float(p), dz=dz(d)))
            for fam in {r["family"] for r in recs}:
                grp = [r for r in recs if r["family"] == fam]
                for r, a in zip(grp, holm([r["wilcoxon_p"] for r in grp])):
                    r["holm_p"] = a
            rows += recs

    out = pd.DataFrame(rows)

    def verdict(r):
        if r["holm_p"] >= 0.05:
            return "inconclusive"
        better = (r["mean_delta"] < 0 if r["metric"] in LOWER_BETTER
                  else r["mean_delta"] > 0)
        return "QSVM-favorable" if better else "baseline-favorable"

    out["verdict"] = out.apply(verdict, axis=1)
    csv = NSL / "p2_rebuild_pairwise.csv"
    out.to_csv(csv, index=False, encoding="utf-8")

    for setting in out.setting.unique():
        s = out[(out.setting == setting) & (out.metric == "ece_full")]
        if s.empty:
            continue
        print(f"\n  {setting}   ECE toan tap test  (am = QSVM tot hon)")
        for _, r in s.iterrows():
            print(f"    vs {r['baseline']:13s} {r['mean_delta']:+.4f} "
                  f"[{r['ci_low']:+.4f},{r['ci_high']:+.4f}]  "
                  f"holm={r['holm_p']:.4f} d_z={r['dz']:+.2f}  {r['verdict']}")
    print(f"\n  -> {csv.relative_to(ROOT).as_posix()}  ({len(out)} dong)")
    cal_tests()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
