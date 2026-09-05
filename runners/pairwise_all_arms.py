"""Bang thong ke ghep cap phu HET moi arm va moi test split.

Vi sao can. `runners/analyze_c4.py` nhan mot cap (arm, test_split) moi lan chay
va GHI DE `c4_pairwise_statistics_{regime}.csv`, nen file cuoi cung chi con
tuy chon chay sau cung -- che do `natural` vi the chi con `tuned_per_N` x
`full_test`, trong khi du lieu per-run co du bon to hop. Nhanh `frozen_c2`
(NSL-KDD) va `tuned_once` (UNSW) chinh la phep thu robustness: crossover co con
khi khong tune lai sieu tham so tai tung N hay khong. Cau hoi do dang bi bo
trong.

Script nay chi doc per-run va ghi ra file MOI (`*_all_arms.csv`); khong dung
den cac file phan tich dang co.

Chay:  python runners/pairwise_all_arms.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import c4_pipeline as c4  # noqa: E402

CASES = [
    ("nslkdd", "natural", "results/nslkdd/c4_revision/c4_per_run_natural_refit_per_N.csv"),
    ("nslkdd", "matched", "results/nslkdd/c4_revision/c4_per_run_matched_refit_per_N.csv"),
    ("unsw", "natural", "results/unsw/c4_revision/c4_per_run_unsw_natural_refit_per_N.csv"),
]


def main() -> None:
    for dataset, regime, per_run_path in CASES:
        spec = c4.get_spec(dataset)
        df = pd.read_csv(ROOT / per_run_path)
        df["test_split"] = df.test_split.replace({"full_kddtest_plus": "full_test"})

        stats = c4.build_pairwise_table(
            df, metric="f1_macro", group_cols=["arm", "test_split", "n_train"])
        stats.insert(0, "dataset", spec.name)
        out = ROOT / "results" / dataset / "c4_revision" / \
            f"c4_pairwise_statistics_{regime}_all_arms.csv"
        stats.to_csv(out, index=False)
        print(f"\n=== {spec.name} · {regime} -> {out.relative_to(ROOT)} "
              f"({len(stats)} dong) ===")

        # Crossover so voi tung ensemble cay, tach theo arm, tren tap test day du.
        blk = stats[stats.test_split == "full_test"]
        for baseline in ("XGBoost", "RandomForest", "SVM_RBF"):
            piv = blk[blk.baseline == baseline].pivot_table(
                index="n_train", columns="arm", values="mean_delta")
            if piv.empty:
                continue
            print(f"\n  mean_delta QSVM_ZZ - {baseline} (dau doi = crossover):")
            print("   " + piv.round(4).to_string().replace("\n", "\n   "))
            for arm in piv.columns:
                s = piv[arm].dropna()
                flips = [f"{s.index[i]}->{s.index[i+1]}"
                         for i in range(len(s) - 1)
                         if (s.values[i] < 0) != (s.values[i + 1] < 0)]
                print(f"     {arm}: doi dau tai {flips or 'khong doi dau'}")


if __name__ == "__main__":
    main()
