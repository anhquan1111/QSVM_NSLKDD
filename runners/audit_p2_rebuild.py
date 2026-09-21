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


def audit_macros_defined(tex, m):
    """Moi macro \\p... DUNG trong bai phai duoc DINH NGHIA.

    Khong co phep kiem nay thi go sai mot ten macro se lot: audit van xanh
    vi no chi doi chieu nhung macro da co, con LaTeX thi chet voi
    'Undefined control sequence'.
    """
    # Bat TEN DAY DU cua lenh (ke ca chu p dau), roi tru ra lenh cua chinh
    # LaTeX. Danh sach nay ngan va on dinh; them muc moi thi phai co ly do.
    latex_p = {"paragraph", "pm", "pi", "par", "pageref", "protect",
               "printindex", "pounds", "pagestyle", "pagenumbering"}
    used = {name[1:] for name in re.findall(BS + BS + r"(p[A-Za-z]+)", tex)
            if name not in latex_p}
    missing = sorted(used - set(m))
    check(not missing, f"moi macro dung trong bai deu duoc dinh nghia "
                       f"(thieu: {missing})")


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


def audit_refarm(m, ref, cal):
    """Nhanh doi chung va ba bo hieu chinh."""
    g = ref.groupby(["repr", "model"])
    for rep, tag in (("pca4", "Pca"), ("k20", "KTwenty"), ("all122", "Full")):
        for model, key in (("RandomForest", "Rf"), ("XGBoost", "Xgb")):
            check(m[f"ref{tag}{key}EceRare"] == f"{g.ece_rare.mean()[(rep, model)]:.4f}",
                  f"ref{tag}{key}EceRare")
            check(m[f"ref{tag}{key}AucPr"] == f"{g.auc_pr.mean()[(rep, model)]:.4f}",
                  f"ref{tag}{key}AucPr")
    c = cal.groupby(["model", "calibrator"]).ece_full.mean()
    for model, key in MACRO.items():
        for cname, tag in (("none", "None"), ("platt", "Platt"),
                           ("isotonic", "Iso"), ("temperature", "Temp")):
            check(m[f"cal{key}{tag}"] == f"{c[(model, cname)]:.4f}", f"cal{key}{tag}")

    # Luan diem A: cho cay du dac trung thi XEP HANG tot hon ma HIEU CHINH te di.
    e = g.ece_rare.mean(); a = g.auc_pr.mean()
    for model in ("RandomForest", "XGBoost"):
        check(e[("all122", model)] > e[("pca4", model)],
              f"{model}: 122 dac trung hieu chinh TE hon PCA-4")
    check(a[("all122", "RandomForest")] > a[("pca4", "RandomForest")],
          "RandomForest: 122 dac trung xep hang TOT hon PCA-4")

    # Luan diem B: hieu chinh hau ky chi giup kernel luong tu.
    for model in ("RandomForest", "XGBoost"):
        for cname in ("platt", "isotonic", "temperature"):
            check(c[(model, cname)] > c[(model, "none")],
                  f"{model}: {cname} lam XAU hon khong hieu chinh")
    for cname in ("platt", "isotonic", "temperature"):
        check(c[("QSVM", cname)] < c[("QSVM", "none")],
              f"QSVM: {cname} lam TOT hon khong hieu chinh")


def main() -> int:
    df = pd.read_csv(IN / "p2_rebuild_per_run.csv")
    st = pd.read_csv(IN / "p2_rebuild_pairwise.csv")
    platt = pd.read_csv(IN / "p2_rebuild_platt.csv")
    m = dict(re.findall(BS + BS + r"newcommand\{" + BS + BS + r"p(\w+)\}\{([^}]*)\}",
                        read(PAPER / "tables" / "numbers_macros.tex")))

    audit_macros(m, df, st, platt)
    tex = read(PAPER / "main.tex")
    audit_macros_defined(tex, m)
    audit_prose_numbers(tex)
    audit_invariants(df, st, platt)
    audit_refarm(m, pd.read_csv(IN / "p2_rebuild_refarm.csv"),
                 pd.read_csv(IN / "p2_rebuild_calibrators.csv"))
    for rel in ("figs/fig1_test_size.pdf", "figs/fig2_paired.pdf",
                "figs/fig3_platt.pdf", "figs/fig4_refarm.pdf",
                "tables/rare_table.tex", "main.tex"):
        check((PAPER / rel).exists(), f"co {rel}")

    n_ok = sum(1 for ok, _ in _checks if ok)
    for ok, label in _checks:
        if not ok:
            print(f"  LOI   {label}")
    print(f"\n  audit_p2_rebuild  {n_ok}/{len(_checks)}")
    return 0 if n_ok == len(_checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
