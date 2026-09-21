"""Bang + macro so cho ban dung lai cua Paper 2.

    python runners/make_p2_rebuild_tables.py

Cung ky luat nhu paper 3: prose KHONG duoc viet so truc tiep, moi con so di
qua macro sinh tu artifact, va `audit_p2_rebuild.py` doi chieu mot cho duy nhat.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

IN = ROOT / "results" / "nslkdd" / "p2_rebuild"
OUT = ROOT / "paper" / "paper2_rebuild" / "tables"
OUT.mkdir(parents=True, exist_ok=True)

ORDER = ["QSVM", "SVM-RBF", "MLP", "XGBoost", "RandomForest"]
PRETTY = {"QSVM": r"QSVM-\ZZ{}", "SVM-RBF": "SVM-RBF", "MLP": "MLP",
          "XGBoost": "XGBoost", "RandomForest": "Random forest"}
MACRO = {"QSVM": "Qsvm", "SVM-RBF": "Rbf", "MLP": "Mlp",
         "XGBoost": "Xgb", "RandomForest": "Rf"}


def main_table(df: pd.DataFrame) -> str:
    sub = df[df.test_set == "full_kddtest_plus"]
    g = sub.groupby("model")
    lines = [
        "% Sinh boi runners/make_p2_rebuild_tables.py -- dung sua tay.",
        r"\begin{table}[t]", r"\centering",
        r"\caption{Rare-attack reliability on the full KDDTest+ "
        r"($\pnRare$ rare test records), mean$\pm$std over $\pnRuns$ runs. "
        r"Lower ECE/Brier and higher AUC-PR/$F_1$ are better; best per column "
        r"in bold. The quantum kernel is better calibrated than both tree "
        r"ensembles but not than the classical RBF kernel.}",
        r"\label{tab:rare}",
        r"\begin{tabular}{lcccc}", r"\toprule",
        r"Model & $\ECE_{\text{rare}}$ & $\Brier_{\text{rare}}$ & "
        r"AUC-PR & $F_1$ \\", r"\midrule",
    ]
    best = {c: g[c].mean().idxmin() for c in ("ece_rare", "brier_rare")}
    best.update({c: g[c].mean().idxmax() for c in ("auc_pr", "f1")})
    for m in ORDER:
        cells = []
        for c in ("ece_rare", "brier_rare", "auc_pr", "f1"):
            mu, sd = g[c].mean()[m], g[c].std()[m]
            txt = f"{mu:.4f}$\\pm${sd:.4f}"
            cells.append(f"\\textbf{{{txt}}}" if best[c] == m else txt)
        lines.append(f"{PRETTY[m]} & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(lines)


def macros(df: pd.DataFrame, st: pd.DataFrame, platt: pd.DataFrame) -> str:
    full = df[df.test_set == "full_kddtest_plus"]
    old = df[df.test_set == "sample100_cu"]
    g, go = full.groupby("model"), old.groupby("model")
    m: dict[str, str] = {
        "nRuns": str(full.run_id.nunique()),
        "nTest": f"{int(full.n_test.iloc[0]):,}".replace(",", chr(92) + ","),
        "nRare": f"{int(full.n_rare.iloc[0]):,}".replace(",", chr(92) + ","),
        "nRareOld": str(int(old.n_rare.iloc[0])),
        "nTestOld": str(int(old.n_test.iloc[0])),
        "nTrain": "{:,}".format(int(pd.read_csv(
            ROOT / "data/nslkdd/processed_data/multi_run/train_run1.csv"
        ).shape[0])).replace(",", chr(92) + ","),
    }
    for model, key in MACRO.items():
        for col, tag in (("ece_rare", "EceRare"), ("brier_rare", "BrierRare"),
                         ("auc_pr", "AucPr"), ("f1", "Fone")):
            m[f"{key}{tag}"] = f"{g[col].mean()[model]:.4f}"
            m[f"{key}{tag}Sd"] = f"{g[col].std()[model]:.4f}"
        m[f"{key}EceRareOld"] = f"{go['ece_rare'].mean()[model]:.4f}"
        pl = platt[platt.model == model]
        m[f"{key}PlattBefore"] = f"{pl.ece_before.mean():.4f}"
        m[f"{key}PlattAfter"] = f"{pl.ece_after.mean():.4f}"
        m[f"{key}PlattDelta"] = f"{pl.delta.mean():+.4f}"

    s = st[(st.test_set == "full_kddtest_plus")]
    for _, r in s[s.metric.isin(("ece_rare", "brier_rare"))].iterrows():
        tag = "Ece" if r["metric"] == "ece_rare" else "Brier"
        k = MACRO[r["baseline"]]
        m[f"d{tag}{k}"] = f"{r['mean_delta']:+.4f}"
        m[f"d{tag}{k}Lo"] = f"{r['ci_low']:+.4f}"
        m[f"d{tag}{k}Hi"] = f"{r['ci_high']:+.4f}"
        m[f"d{tag}{k}Holm"] = f"{r['holm_p']:.4f}"
        m[f"d{tag}{k}Dz"] = f"{r['dz']:+.2f}"

    head = ["% Sinh boi runners/make_p2_rebuild_tables.py -- dung sua tay.",
            "% Prose KHONG duoc viet so truc tiep; dung macro o day."]
    return "\n".join(head + [f"\\newcommand{{\\p{k}}}{{{v}}}"
                             for k, v in m.items()]) + "\n"


def main() -> int:
    df = pd.read_csv(IN / "p2_rebuild_per_run.csv")
    st = pd.read_csv(IN / "p2_rebuild_pairwise.csv")
    platt = pd.read_csv(IN / "p2_rebuild_platt.csv")

    for name, text in (("rare_table.tex", main_table(df)),
                       ("numbers_macros.tex", macros(df, st, platt))):
        p = OUT / name
        with io.open(p, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"  -> {p.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
