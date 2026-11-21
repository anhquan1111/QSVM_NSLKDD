"""Ket luan ghep cap QSVM_ZZ - baseline tren luoi C cu va luoi mo rong (Paper 1 QMI, viec 4).

Doc results/nslkdd/c4_cgrid/cgrid_per_run.csv (do run_cgrid_extension.py ghi), dung DUNG
`c4.build_pairwise_table` (Wilcoxon hai phia, Holm trong tung ho, CI 95 %) nhu ban do regime.
Cot `grid`: "old" = fit lai voi C da chon tren luoi {0.1..10}; "ext" = C chon lai tren {0.03..100}.

    uv run python runners/analyze_cgrid_extension.py
    -> results/nslkdd/c4_cgrid/cgrid_pairwise.csv
    -> results/nslkdd/c4_cgrid/cgrid_chosen_C.csv  (C chon moi N, model: trung vi, min, max)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import c4_pipeline as c4  # noqa: E402

OUT = ROOT / "results/nslkdd/c4_cgrid"


def main() -> int:
    runs = pd.read_csv(OUT / "cgrid_per_run.csv", encoding="utf-8")
    long = pd.concat([
        runs.assign(grid="old", f1_macro=runs.f1_refit_old),
        runs.assign(grid="ext", f1_macro=runs.f1_ext),
    ]).rename(columns={"run": "run_id"})
    st = c4.build_pairwise_table(long, metric="f1_macro", group_cols=["grid", "N"])
    keep = ["grid", "N", "baseline", "mean_delta", "ci_low", "ci_high", "raw_p", "holm_p",
            "effect_size_dz", "verdict", "n_runs"]
    st = st[keep].sort_values(["N", "baseline", "grid"])
    st.to_csv(OUT / "cgrid_pairwise.csv", index=False, encoding="utf-8")

    svm = runs.dropna(subset=["C_ext"])
    ch = svm.groupby(["N", "model"]).agg(
        C_old_median=("C_old", "median"), C_ext_median=("C_ext", "median"),
        C_ext_min=("C_ext", "min"), C_ext_max=("C_ext", "max"),
        n_ext_at_top=("C_ext", lambda c: int((c == 100.0).sum())),
        n_ext_at_bottom=("C_ext", lambda c: int((c == 0.03).sum())),
        f1_old_mean=("f1_refit_old", "mean"), f1_ext_mean=("f1_ext", "mean")).reset_index()
    ch.to_csv(OUT / "cgrid_chosen_C.csv", index=False, encoding="utf-8")

    pd.set_option("display.width", 200)
    print(st.round(4).to_string(index=False))
    print(ch.round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
