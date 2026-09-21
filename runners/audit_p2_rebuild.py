"""Kiem ban dung lai cua Paper 2.

    python runners/audit_p2_rebuild.py

Ba lop, cung khuon voi audit_paper3.py:
  A. Moi macro trong tables/numbers_macros.tex tinh lai duoc tu artifact.
  B. Cau van khong chua so viet tay.
  C. Cac bat bien cua thiet ke van dung -- day la phan quan trong nhat, vi
     ca bai dung tren chuyen "do dac cho du luc".
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

IN = ROOT / "results" / "nslkdd" / "p2_rebuild"
PAPER = ROOT / "paper" / "paper2_rebuild"
BS = chr(92)
MACRO = {"QSVM": "Qsvm", "SVM-RBF": "Rbf", "MLP": "Mlp",
         "XGBoost": "Xgb", "RandomForest": "Rf"}

_checks: list[tuple[bool, str]] = []


def check(ok, label):
    _checks.append((bool(ok), label))


def read(p):
    with io.open(p, encoding="utf-8") as f:
        return f.read()


def audit_macros(m, df, st, platt):
    full = df[df.test_set == "full_kddtest_plus"]
    old = df[df.test_set == "sample100_cu"]
    g, go = full.groupby("model"), old.groupby("model")

    check(m["nRuns"] == str(full.run_id.nunique()), "nRuns")
    check(m["nRare"] == f"{int(full.n_rare.iloc[0]):,}".replace(",", BS + ","), "nRare")
    check(m["nTest"] == f"{int(full.n_test.iloc[0]):,}".replace(",", BS + ","), "nTest")
    check(m["nRareOld"] == str(int(old.n_rare.iloc[0])), "nRareOld")
    check(m["nTestOld"] == str(int(old.n_test.iloc[0])), "nTestOld")
    ntr = pd.read_csv(ROOT / "data/nslkdd/processed_data/multi_run/train_run1.csv").shape[0]
    check(m["nTrain"] == "{:,}".format(ntr).replace(",", BS + ","), "nTrain")

    for model, key in MACRO.items():
        for col, tag in (("ece_rare", "EceRare"), ("brier_rare", "BrierRare"),
                         ("auc_pr", "AucPr"), ("f1", "Fone")):
            check(m[f"{key}{tag}"] == f"{g[col].mean()[model]:.4f}", f"{key}{tag}")
            check(m[f"{key}{tag}Sd"] == f"{g[col].std()[model]:.4f}", f"{key}{tag}Sd")
        check(m[f"{key}EceRareOld"] == f"{go['ece_rare'].mean()[model]:.4f}",
              f"{key}EceRareOld")
        pl = platt[platt.model == model]
        check(m[f"{key}PlattBefore"] == f"{pl.ece_before.mean():.4f}", f"{key}PlattBefore")
        check(m[f"{key}PlattAfter"] == f"{pl.ece_after.mean():.4f}", f"{key}PlattAfter")
        check(m[f"{key}PlattDelta"] == f"{pl.delta.mean():+.4f}", f"{key}PlattDelta")

    s = st[st.test_set == "full_kddtest_plus"]
    for _, r in s[s.metric.isin(("ece_rare", "brier_rare"))].iterrows():
        tag = "Ece" if r["metric"] == "ece_rare" else "Brier"
        k = MACRO[r["baseline"]]
        check(m[f"d{tag}{k}"] == f"{r['mean_delta']:+.4f}", f"d{tag}{k}")
        check(m[f"d{tag}{k}Holm"] == f"{r['holm_p']:.4f}", f"d{tag}{k}Holm")
        check(m[f"d{tag}{k}Dz"] == f"{r['dz']:+.2f}", f"d{tag}{k}Dz")


NUMBER_WHITELIST = {"1", "4", "20", "0", "5", "1000", "0.0625"}


def audit_prose_numbers(tex):
    body = re.sub(r"(?<!" + BS + BS + r")%.*", "", tex)
    body = body.split(BS + "maketitle", 1)[-1]
    body = body.split(BS + "begin{thebibliography}", 1)[0]
    body = re.sub(BS + BS + r"includegraphics(\[[^\]]*\])?\{[^}]*\}", " ", body)
    body = re.sub(BS + BS + r"(label|ref|input|url|newcommand)\{[^}]*\}", " ", body)
    bad = [t for t in re.findall(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])", body)
           if t not in NUMBER_WHITELIST]
    check(not bad, f"khong co so viet tay trong cau van (thay: {sorted(set(bad))})")


def audit_invariants(df, st, platt):
    full = df[df.test_set == "full_kddtest_plus"]
    old = df[df.test_set == "sample100_cu"]

    # Thiet ke: 10 run, va tap test day du phai lon hon han tap cu.
    check(full.run_id.nunique() == 10, "du 10 run")
    check(full.n_rare.iloc[0] > 100 * old.n_rare.iloc[0],
          "tap test day du co nhieu hon 100 lan mau hiem")

    # Voi 5 cap, Wilcoxon khong bao gio dat p<0.05 -- ly do phai chay 10 run.
    check(stats.wilcoxon(np.arange(1., 6.)).pvalue > 0.05,
          "5 cap: Wilcoxon khong the dat p<0.05")
    check(stats.wilcoxon(np.arange(1., 11.)).pvalue < 0.05,
          "10 cap: Wilcoxon dat duoc p<0.05")

    s = st[st.test_set == "full_kddtest_plus"]
    e = s[s.metric == "ece_rare"].set_index("baseline")
    # Luan diem duoc claim: thang ca hai mo hinh cay sau Holm.
    for b in ("RandomForest", "XGBoost"):
        check(e.loc[b, "holm_p"] < 0.05 and e.loc[b, "mean_delta"] < 0,
              f"QSVM thang {b} sau Holm (ECE_rare)")
    # Luan diem KHONG duoc claim: thang RBF.
    check(e.loc["SVM-RBF", "holm_p"] >= 0.05,
          "QSVM vs SVM-RBF la inconclusive (ECE_rare) -- bai khong duoc claim thang")

    # Platt chi giup DUY NHAT kernel luong tu.
    d = platt.groupby("model").delta.mean()
    helped = sorted(d[d > 0].index)
    check(helped == ["QSVM"], f"Platt chi giup QSVM (thuc te: {helped})")

    # Tren tap test cu, thu hang cua QSVM cao hon -- day la luan diem canh bao.
    r_old = old.groupby("model").ece_rare.mean().rank()["QSVM"]
    r_new = full.groupby("model").ece_rare.mean().rank()["QSVM"]
    check(r_old < r_new,
          f"QSVM xep hang cao hon tren tap test nho ({r_old:.0f} vs {r_new:.0f})")


def main() -> int:
    df = pd.read_csv(IN / "p2_rebuild_per_run.csv")
    st = pd.read_csv(IN / "p2_rebuild_pairwise.csv")
    platt = pd.read_csv(IN / "p2_rebuild_platt.csv")
    m = dict(re.findall(BS + BS + r"newcommand\{" + BS + BS + r"p(\w+)\}\{([^}]*)\}",
                        read(PAPER / "tables" / "numbers_macros.tex")))

    audit_macros(m, df, st, platt)
    audit_prose_numbers(read(PAPER / "main.tex"))
    audit_invariants(df, st, platt)
    for rel in ("figs/fig1_test_size.pdf", "figs/fig2_paired.pdf",
                "figs/fig3_platt.pdf", "tables/rare_table.tex", "main.tex"):
        check((PAPER / rel).exists(), f"co {rel}")

    n_ok = sum(1 for ok, _ in _checks if ok)
    for ok, label in _checks:
        if not ok:
            print(f"  LOI   {label}")
    print(f"\n  audit_p2_rebuild  {n_ok}/{len(_checks)}")
    return 0 if n_ok == len(_checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
