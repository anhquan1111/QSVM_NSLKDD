"""Bang + macro so cho ban dung lai cua Paper 2.

    python runners/make_p2_rebuild_tables.py

Ky luat: prose KHONG duoc viet so truc tiep, moi con so di qua macro sinh tu
artifact, va `audit_p2_rebuild.py` doi chieu mot cho duy nhat.

CHI SO CHINH LA `ece_full`. Xem dau `analyze_p2_rebuild.py` de biet vi sao
`ece_rare` khong phai phep do calibration.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NSL = ROOT / "results" / "nslkdd" / "p2_rebuild"
UNSW = ROOT / "results" / "unsw" / "p2_rebuild"
OUT = ROOT / "paper" / "paper2_rebuild" / "tables"
OUT.mkdir(parents=True, exist_ok=True)
BS = chr(92)

ORDER = ["QSVM", "SVM-RBF", "MLP", "XGBoost", "RandomForest"]
PRETTY = {"QSVM": r"QSVM-\ZZ{}", "SVM-RBF": "SVM-RBF", "MLP": "MLP",
          "XGBoost": "XGBoost", "RandomForest": "Random forest"}
MACRO = {"QSVM": "Qsvm", "SVM-RBF": "Rbf", "MLP": "Mlp",
         "XGBoost": "Xgb", "RandomForest": "Rf"}
SETTINGS = {"NSL-KDD/full": "Nsl", "UNSW/4qb": "UnswFour", "UNSW/6qb": "UnswSix"}


def num(x, d=4):
    return f"{x:.{d}f}"


def thousands(n):
    return f"{int(n):,}".replace(",", BS + ",")


def main_table(long: pd.DataFrame) -> str:
    """Mot bang, ba thiet lap canh nhau, chi so chinh la ECE toan tap test."""
    lines = [
        "% Sinh boi runners/make_p2_rebuild_tables.py -- dung sua tay.",
        r"\begin{table*}[t]", r"\centering",
        r"\caption{Calibration error on the full test split of each dataset, "
        r"mean$\pm$std over $\pnRuns$ runs. Lower is better; best per column "
        r"in bold. The quantum kernel is better calibrated than both tree "
        r"ensembles in every setting, and is not better than the MLP.}",
        r"\label{tab:main}",
        r"\begin{tabular}{lccc}", r"\toprule",
        r" & NSL-KDD & UNSW-NB15 & UNSW-NB15 \\",
        r"Model & ($\plegacyQubits$ qubits) & ($\plegacyQubits$ qubits) "
        r"& ($\punswQubits$ qubits) \\", r"\midrule",
    ]
    cols = ["NSL-KDD/full", "UNSW/4qb", "UNSW/6qb"]
    best = {c: long[long.setting == c].groupby("model").ece_full.mean().idxmin()
            for c in cols}
    for m in ORDER:
        cells = []
        for c in cols:
            s = long[(long.setting == c) & (long.model == m)].ece_full
            txt = f"{s.mean():.4f}$\\pm${s.std():.4f}"
            cells.append(f"\\textbf{{{txt}}}" if best[c] == m else txt)
        lines.append(f"{PRETTY[m]} & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""]
    return "\n".join(lines)


def macros(long, st, platt, ref, cal, identity) -> str:
    m: dict[str, str] = {}
    nsl = long[long.setting == "NSL-KDD/full"]
    old = long[long.setting == "NSL-KDD/sample100"]
    unsw = long[long.setting == "UNSW/6qb"]

    m["nRuns"] = str(nsl.run_id.nunique())
    m["nTest"] = thousands(nsl.n_test.iloc[0])
    m["nRare"] = thousands(nsl.n_rare.iloc[0])
    m["nRareOld"] = str(int(old.n_rare.iloc[0]))
    m["nTestOld"] = str(int(old.n_test.iloc[0]))
    m["nTrain"] = thousands(pd.read_csv(
        ROOT / "data/nslkdd/processed_data/multi_run/train_run1.csv").shape[0])
    m["unswTest"] = thousands(unsw.n_test.iloc[0])
    m["unswRare"] = thousands(unsw.n_rare.iloc[0])
    m["legacyQubits"] = "4"
    m["unswQubits"] = "6"
    m["identityMaxDev"] = f"{identity:.1e}".replace("e-", r"\times10^{-") + "}"

    for setting, tag in SETTINGS.items():
        sub = long[long.setting == setting]
        for model, key in MACRO.items():
            s = sub[sub.model == model]
            m[f"{tag}{key}EceFull"] = num(s.ece_full.mean())
            m[f"{tag}{key}EceFullSd"] = num(s.ece_full.std())
            m[f"{tag}{key}EceRare"] = num(s.ece_rare.mean())
        p = st[(st.setting == setting) & (st.metric == "ece_full")]
        for _, r in p.iterrows():
            k = MACRO[r["baseline"]]
            m[f"d{tag}{k}"] = f"{r['mean_delta']:+.4f}"
            m[f"d{tag}{k}Lo"] = f"{r['ci_low']:+.4f}"
            m[f"d{tag}{k}Hi"] = f"{r['ci_high']:+.4f}"
            m[f"d{tag}{k}Holm"] = num(r["holm_p"])
            m[f"d{tag}{k}Dz"] = f"{r['dz']:+.2f}"

    for model, key in MACRO.items():
        s = old[old.model == model]
        m[f"{key}EceRareOld"] = num(s.ece_rare.mean())
        pl = platt[platt.model == model]
        m[f"{key}PlattBefore"] = num(pl.ece_before.mean())
        m[f"{key}PlattAfter"] = num(pl.ece_after.mean())
        m[f"{key}PlattDelta"] = f"{pl.delta.mean():+.4f}"

    g = ref.groupby(["repr", "model"])
    for rep, tag in (("pca4", "Pca"), ("k20", "KTwenty"), ("all122", "Full")):
        for model, key in (("RandomForest", "Rf"), ("XGBoost", "Xgb")):
            m[f"ref{tag}{key}EceFull"] = num(g.ece_full.mean()[(rep, model)])
            m[f"ref{tag}{key}AucPr"] = num(g.auc_pr.mean()[(rep, model)])
        m[f"ref{tag}Dims"] = str(int(ref[ref["repr"] == rep].n_features.iloc[0]))

    c = cal.groupby(["model", "calibrator"]).ece_full.mean()
    for model, key in MACRO.items():
        for cname, tag in (("none", "None"), ("platt", "Platt"),
                           ("isotonic", "Iso"), ("temperature", "Temp")):
            m[f"cal{key}{tag}"] = num(c[(model, cname)])

    head = ["% Sinh boi runners/make_p2_rebuild_tables.py -- dung sua tay.",
            "% Prose KHONG duoc viet so truc tiep; dung macro o day."]
    return "\n".join(head + [f"\\newcommand{{\\p{k}}}{{{v}}}"
                             for k, v in m.items()]) + "\n"


def load_long() -> pd.DataFrame:
    n = pd.read_csv(NSL / "p2_rebuild_per_run.csv")
    n["setting"] = "NSL-KDD/" + n.test_set.map(
        {"full_kddtest_plus": "full", "sample100_cu": "sample100"})
    u = pd.read_csv(UNSW / "p2_unsw_per_run.csv")
    u["setting"] = "UNSW/" + u.n_qubits.astype(str) + "qb"
    return pd.concat([n, u], ignore_index=True)


def identity_max_dev() -> float:
    """Sai lech lon nhat giua ECE_rare va 1 - trung binh(p), doc tu artifact.

    Bai khang dinh hai dai luong nay TRUNG nhau tren tap con mot lop; con so
    phai lay tu phep do chu khong viet tay."""
    p = NSL / "p2_rebuild_identity.csv"
    return float(pd.read_csv(p).abs_dev.max()) if p.exists() else float("nan")


def main() -> int:
    long = load_long()
    st = pd.read_csv(NSL / "p2_rebuild_pairwise.csv")
    platt = pd.read_csv(NSL / "p2_rebuild_platt.csv")
    ref = pd.read_csv(NSL / "p2_rebuild_refarm.csv")
    cal = pd.read_csv(NSL / "p2_rebuild_calibrators.csv")

    for name, text in (("main_table.tex", main_table(long)),
                       ("numbers_macros.tex",
                        macros(long, st, platt, ref, cal, identity_max_dev()))):
        p = OUT / name
        with io.open(p, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"  -> {p.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
