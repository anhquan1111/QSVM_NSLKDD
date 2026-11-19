"""Do nhay cua ban do regime theo cach hieu chinh da so sanh (R3 vong R1).

R3: "Recommendations about when to use the quantum kernel should also reflect
their sensitivity to the chosen multiplicity correction."

Cot `p_value` cua results/nslkdd/regime_map_rows.csv la p DA hieu chinh Holm
trong tung ho baseline. Ban TETC ap them Benjamini-Hochberg len cot do (ra
17/15/78) -- tuc hieu chinh hai lan. Script nay lay p THO (`raw_p`, = Wilcoxon
p) tu file thong ke goc cua tung o roi tinh lai bon cach dem:

    khong hieu chinh | Holm trong ho (so chinh) | BH tren ca khoi | Holm tren ca khoi

cho ca 110 o va rieng khoi 42 o tu nhien (C4 natural).

    uv run python runners/regime_map_multiplicity.py
    -> results/nslkdd/regime_map_multiplicity.csv

Luu y: voi 10 run, p Wilcoxon hai phia nho nhat dat duoc la 2/2^10 = 0.00195;
Holm tren 110 o can p <= 0.05/110 = 0.00045, nen khong o nao co the qua --
do la gioi han cua so run, khong phai bang chung khong co khac biet.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results/nslkdd"
ALPHA = 0.05

SOURCES = {
    "c4_pairwise_statistics_natural.csv": RES / "c4_revision/c4_pairwise_statistics_natural.csv",
    "c4_pairwise_statistics_matched.csv": RES / "c4_revision/c4_pairwise_statistics_matched.csv",
    "c3_pairwise_statistics.csv": RES / "c3_revision/c3_pairwise_statistics.csv",
}
# Ban do dung arm tuned_per_N tren test day du (ten split khac nhau giua hai file)
FULL_TEST = ("full_test", "full_kddtest_plus")


def attach_raw_p(rows: pd.DataFrame) -> pd.Series:
    """Ghep moi o voi dong goc cua no (cung hieu trung binh va cung p Holm)."""
    raw = pd.Series(np.nan, index=rows.index)
    for src, grp in rows.groupby("source"):
        if src == "c2_paired_statistics.csv":
            # C2 chi co 2 o, khong hieu chinh: p trong ban do da la p tho
            raw[grp.index] = grp.p_value
            continue
        d = pd.read_csv(SOURCES[src])
        if "arm" in d:
            d = d[(d.arm == "tuned_per_N") & d.test_split.isin(FULL_TEST)]
        for i, row in grp.iterrows():
            hit = d[np.isclose(d.mean_delta, row.estimate, atol=1e-9)
                    & np.isclose(d.holm_p, row.p_value, atol=1e-9)]
            if len(hit) != 1:
                raise SystemExit(f"Khong ghep duoc {src} {row.condition} {row.baseline}: {len(hit)} dong")
            raw[i] = hit.iloc[0].raw_p
    return raw


def bh(p: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg, tra ve mang bool bac bo."""
    m, order = len(p), np.argsort(p)
    ok = np.where(p[order] <= ALPHA * np.arange(1, m + 1) / m)[0]
    out = np.zeros(m, bool)
    if len(ok):
        out[order[: ok.max() + 1]] = True
    return out


def holm(p: np.ndarray) -> np.ndarray:
    """Holm-Bonferroni tren ca mang."""
    m, out = len(p), np.zeros(len(p), bool)
    for k, j in enumerate(np.argsort(p)):
        if p[j] > ALPHA / (m - k):
            break
        out[j] = True
    return out


def tally(est: np.ndarray, rej: np.ndarray) -> dict[str, int]:
    return {"quantum": int((rej & (est > 0)).sum()),
            "classical": int((rej & (est < 0)).sum()),
            "inconclusive": int((~rej).sum())}


def main() -> int:
    rows = pd.read_csv(RES / "regime_map_rows.csv")
    rows["raw_p"] = attach_raw_p(rows)
    if rows.raw_p.isna().any():
        print("Thieu p tho")
        return 1
    out = []
    blocks = {"all_110": rows,
              "c4_natural_42": rows[rows.source == "c4_pairwise_statistics_natural.csv"]}
    for block, d in blocks.items():
        p, est = d.raw_p.to_numpy(), d.estimate.to_numpy()
        methods = {
            "none": p <= ALPHA,
            "holm_within_family": (d.verdict != "inconclusive").to_numpy(),
            "bh_block": bh(p),
            "holm_block": holm(p),
        }
        for name, rej in methods.items():
            out.append({"block": block, "n_cells": len(d), "correction": name, **tally(est, rej)})
    df = pd.DataFrame(out)
    df["min_raw_p"] = df.block.map({b: blocks[b].raw_p.min() for b in blocks})
    path = RES / "regime_map_multiplicity.csv"
    df.to_csv(path, index=False, encoding="utf-8")
    print(df.to_string(index=False))
    print(f"\nGhi {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
