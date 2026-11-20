"""Recall theo kieu tan cong da gap / kieu moi tren KDDTest+, theo N (Paper 1 QMI).

Vi sao: khi N tang, macro-F1 cua cac baseline co dien tren KDDTest+ tut (XGBoost,
RF, RBF), con QSVM tang. KDDTest+ co 17 kieu tan cong khong co trong KDDTrain+.
Script tach recall tren tan cong thanh hai nhom (kieu co trong train / kieu moi),
cong them recall tren luu luong binh thuong, de xem phan tut nam o dau.

Khong train gi: doc du doan da luu cua lan chay bo trung
(results/nslkdd/c4_dedup/cache/natural_refit_per_N_tuned_per_N_N*_run*.npz,
split full_test, thu tu dong = data/nslkdd/processed_data/NSL_KDD_Test_Cleaned.csv).

    uv run python runners/analyze_novel_attacks.py
    -> results/nslkdd/c4_dedup/novel_attack_recall_runs.csv   (moi run mot dong)
    -> results/nslkdd/c4_dedup/novel_attack_recall_summary.csv (trung binh, CI 95 %)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "results/nslkdd/c4_dedup/cache"
OUT = ROOT / "results/nslkdd/c4_dedup"
MODELS = ["QSVM_ZZ", "QSVM_Z", "SVM_Linear", "SVM_Poly2", "SVM_RBF", "RandomForest", "XGBoost"]
PATTERN = re.compile(r"natural_refit_per_N_tuned_per_N_N(\d+)_run(\d+)\.npz")


def test_groups() -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    """Mat na dong test: binh thuong, tan cong kieu da gap, tan cong kieu moi."""
    te = pd.read_csv(ROOT / "data/nslkdd/processed_data/NSL_KDD_Test_Cleaned.csv",
                     usecols=["label_binary", "label_multiclass"], encoding="utf-8")
    tr_raw = pd.read_csv(ROOT / "data/nslkdd/raw/KDDTrain+.txt", header=None, encoding="utf-8")
    seen_types = set(tr_raw[41]) - {"normal"}
    attack = te.label_binary.to_numpy() == 1
    seen = attack & te.label_multiclass.isin(seen_types).to_numpy()
    novel = attack & ~seen
    novel_types = sorted(set(te.label_multiclass[novel]))
    return ~attack, seen, novel, novel_types


def main() -> int:
    normal, seen, novel, novel_types = test_groups()
    print(f"Test: {normal.sum()} binh thuong, {seen.sum()} tan cong kieu da gap, "
          f"{novel.sum()} tan cong kieu moi ({len(novel_types)} kieu)")
    rows = []
    for f in sorted(CACHE.glob("natural_refit_per_N_tuned_per_N_N*_run*.npz")):
        n, run = map(int, PATTERN.fullmatch(f.name).groups())
        d = np.load(f)
        for m in MODELS:
            pred = d[f"pred__full_test__{m}"].astype(bool)
            if len(pred) != len(normal):
                print(f"Lech so dong: {f.name}")
                return 1
            rows.append({"N": n, "run": run, "model": m,
                         "recall_seen": pred[seen].mean(),
                         "recall_novel": pred[novel].mean(),
                         "specificity_normal": (~pred[normal]).mean()})
    runs = pd.DataFrame(rows).sort_values(["model", "N", "run"])
    counts = runs.groupby(["model", "N"]).size()
    if (counts != 10).any():
        print("Thieu run:\n", counts[counts != 10])
        return 1
    runs.to_csv(OUT / "novel_attack_recall_runs.csv", index=False, encoding="utf-8")

    def ci(v: pd.Series) -> float:
        return stats.t.ppf(0.975, len(v) - 1) * v.std(ddof=1) / np.sqrt(len(v))

    metrics = ["recall_seen", "recall_novel", "specificity_normal"]
    summ = runs.groupby(["model", "N"])[metrics].agg(["mean", ci])
    summ.columns = [f"{a}_{'mean' if b == 'mean' else 'ci95'}" for a, b in summ.columns]
    summ = summ.reset_index()
    summ["n_seen"], summ["n_novel"], summ["n_normal"] = seen.sum(), novel.sum(), normal.sum()
    summ.to_csv(OUT / "novel_attack_recall_summary.csv", index=False, encoding="utf-8")
    pd.set_option("display.width", 200)
    print(summ.round(3).to_string(index=False))
    print("Kieu moi:", ", ".join(novel_types))
    return 0


if __name__ == "__main__":
    sys.exit(main())
