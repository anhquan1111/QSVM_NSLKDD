"""UNSW-NB15: n=6 (luat chon be rong) co tot hon n=4, n=8 khong (Paper 1 QMI, viec 5).

Doc ket qua quet N (natural, tuned_per_N, K=35, test day du) o ba be rong:
  n=6: results/unsw/c4_revision/c4_per_run_unsw_natural_refit_per_N.csv (ket qua cua bai)
  n=4, n=8: results/unsw/c4_revision/variant_K35n{4,8}/c4_per_run_unsw_natural_refit_per_N.csv
            (runners/run_c4.py --dataset unsw --regime natural --arms tuned_per_N --n-qubits n)
Cung seed nen cung tap train o moi (N, run); script kiem n_rare_train khop truoc khi ghep cap.

    uv run python runners/analyze_unsw_width.py
    -> results/unsw/c4_revision/width_compare_qsvm.csv     (QSVM n - QSVM n=6, ghep cap; Holm 2 be rong / N)
    -> results/unsw/c4_revision/width_compare_pairwise.csv (QSVM vs 6 baseline o tung be rong, nhu ban do)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners")]
from src import c4_pipeline as c4  # noqa: E402

BASE = ROOT / "results/unsw/c4_revision"
FILES = {6: BASE / "c4_per_run_unsw_natural_refit_per_N.csv",
         4: BASE / "variant_K35n4/c4_per_run_unsw_natural_refit_per_N.csv",
         8: BASE / "variant_K35n8/c4_per_run_unsw_natural_refit_per_N.csv"}


def read_width(f: Path) -> pd.DataFrame:
    """CSV cua run_c4; neu thieu (may gac tat o buoc ghi cuoi) thi gom tu cache JSON."""
    if f.exists():
        return pd.read_csv(f, encoding="utf-8")
    from run_c4 import flatten
    files = sorted((f.parent / "cache").glob("*natural_refit_per_N_tuned_per_N_N*_run*.json"))
    return flatten([json.loads(p.read_text(encoding="utf-8")) for p in files])


def load() -> pd.DataFrame:
    parts = []
    for n, f in FILES.items():
        d = read_width(f)
        d = d[(d.arm == "tuned_per_N") & (d.test_split == "full_test")]
        parts.append(d.assign(width=n))
    df = pd.concat(parts)
    # Chuoi tap train long nhau phu thuoc ca luoi N: luoi khac thi tap con khac du
    # n_rare_train van khop (rut mau phan tang). Loi 21-11: bien the UNSW roi ve luoi NSL-KDD.
    grids = {n: tuple(sorted(d.n_train.unique())) for n, d in df.groupby("width")}
    if len(set(grids.values())) != 1:
        raise SystemExit(f"Luoi N khac nhau giua cac be rong -> tap train khac: {grids}")
    rare = df.groupby(["n_train", "run_id", "width"]).n_rare_train.first().unstack("width")
    if (rare.nunique(axis=1) != 1).any():
        raise SystemExit("Tap train lech giua cac be rong -> khong ghep cap duoc:\n"
                         + rare[rare.nunique(axis=1) != 1].to_string())
    counts = df.groupby(["width", "n_train"]).run_id.nunique()
    if (counts != 10).any():
        raise SystemExit("Thieu run:\n" + counts[counts != 10].to_string())
    return df


def main() -> int:
    df = load()
    q = df[df.model == "QSVM_ZZ"].pivot_table(index=["n_train", "run_id"], columns="width",
                                               values="f1_macro")
    rows = []
    for n_train, block in q.groupby(level="n_train"):
        for w in (4, 8):
            r = {"n_train": n_train, "width": w, "f1_mean_w": block[w].mean(),
                 "f1_mean_6": block[6].mean()}
            r.update(c4.paired_effect_summary((block[w] - block[6]).to_numpy()))
            rows.append(r)
    comp = pd.DataFrame(rows)
    comp["holm_p"] = np.nan
    for _, idx in comp.groupby("n_train").groups.items():
        comp.loc[idx, "holm_p"] = c4.holm_adjust(comp.loc[idx, "raw_p"])
    comp.to_csv(BASE / "width_compare_qsvm.csv", index=False, encoding="utf-8")

    st = c4.build_pairwise_table(df, metric="f1_macro", group_cols=["width", "n_train"])
    st = st[["width", "n_train", "baseline", "mean_delta", "ci_low", "ci_high", "raw_p",
             "holm_p", "verdict"]]
    st.to_csv(BASE / "width_compare_pairwise.csv", index=False, encoding="utf-8")

    pd.set_option("display.width", 200)
    cols = ["n_train", "width", "f1_mean_w", "f1_mean_6", "mean_delta", "ci_low", "ci_high",
            "raw_p", "holm_p"]
    print(comp[cols].round(4).to_string(index=False))
    print(st.pivot_table(index=["n_train", "baseline"], columns="width", values="verdict",
                         aggfunc="first").to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
