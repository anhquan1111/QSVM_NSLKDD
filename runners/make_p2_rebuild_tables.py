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
SETTINGS = {"NSL-KDD/full": "Nsl", "NSL-KDD/test21": "Drift",
            "UNSW/4qb": "UnswFour", "UNSW/6qb": "UnswSix"}


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
        r"\begin{tabular}{lcccc}", r"\toprule",
        r" & NSL-KDD & NSL-KDD & UNSW-NB15 & UNSW-NB15 \\",
        r"Model & KDDTest+ & KDDTest-21 & ($\plegacyQubits$ qubits) "
        r"& ($\punswQubits$ qubits) \\", r"\midrule",
    ]
    cols = ["NSL-KDD/full", "NSL-KDD/test21", "UNSW/4qb", "UNSW/6qb"]
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

    # Low-data (A1) va prior shift (C3): hai phan da tinh o
    # run_p2_rebuild_extra.py. Do tren ECE toan tap test nhu moi cho khac.
    ld = pd.read_csv(NSL / "p2_rebuild_lowdata.csv")
    ns = sorted(ld.n_train.unique())
    m["ldNmin"] = str(int(min(ns)))
    m["ldNmax"] = str(int(max(ns)))
    gl = ld.groupby(["n_train", "model"]).ece_full.mean()
    for model, key in MACRO.items():
        m[f"ld{key}Min"] = num(gl[(min(ns), model)])
        m[f"ld{key}Max"] = num(gl[(max(ns), model)])
    m["ldWinnerMin"] = PRETTY[ld[ld.n_train == min(ns)]
                              .groupby("model").ece_full.mean().idxmin()]

    ps = pd.read_csv(NSL / "p2_rebuild_priorshift.csv")
    gp = ps.groupby(["mix", "model"]).ece_full.mean()
    for mix, tag in (("Balanced_50/50", "Bal"), ("AttackHeavy_30/70", "Att"),
                     ("DoS_only", "Dos")):
        for model, key in MACRO.items():
            m[f"ps{tag}{key}"] = num(gp[(mix, model)])
        m[f"ps{tag}Winner"] = PRETTY[ps[ps["mix"] == mix]
                                     .groupby("model").ece_full.mean().idxmin()]
        m[f"ps{tag}N"] = thousands(ps[ps["mix"] == mix].n_test.iloc[0])

    # Do tu tin theo nhom tan cong, va duong tin cay.
    pc = pd.read_csv(NSL / "p2_rebuild_percat.csv")
    gc2 = pc.groupby(["category", "model"]).mean_prob.mean()
    for cat, tag in (("Normal", "Normal"), ("DoS", "Dos"), ("Probe", "Probe"),
                     ("R2L", "RtoL"), ("U2R", "UtoR")):
        for model, key in MACRO.items():
            m[f"cat{tag}{key}"] = num(gc2[(cat, model)])
        m[f"cat{tag}N"] = thousands(pc[pc.category == cat].n.iloc[0])
        best = gc2[cat].idxmin() if cat == "Normal" else gc2[cat].idxmax()
        m[f"cat{tag}Winner"] = PRETTY[best]
    # Nguong quyet dinh: moi mo hinh deu duoi nguong tren ca hai nhom hiem?
    below = all(gc2[(c, mo)] < 0.5 for c in ("R2L", "U2R") for mo in ORDER)
    m["catRareAllBelow"] = "true" if below else "false"

    cv = pd.read_csv(NSL / "p2_rebuild_curve.csv")
    gcv = cv.groupby(["model", "bin"])[["conf", "acc"]].mean()
    # Duoi-tu-tin = duong nam TREN duong cheo o phan lon cac bin.
    for model, key in MACRO.items():
        s = gcv.loc[model]
        m[f"curve{key}Under"] = str(int((s.acc > s.conf).sum()))
    m["curveNbins"] = str(int(cv.bin.nunique()))

    head = ["% Sinh boi runners/make_p2_rebuild_tables.py -- dung sua tay.",
            "% Prose KHONG duoc viet so truc tiep; dung macro o day."]
    return "\n".join(head + [f"\\newcommand{{\\p{k}}}{{{v}}}"
                             for k, v in m.items()]) + "\n"


def load_long() -> pd.DataFrame:
    n = pd.read_csv(NSL / "p2_rebuild_per_run.csv")
    n["setting"] = "NSL-KDD/" + n.test_set.map(
        {"full_kddtest_plus": "full", "kddtest21": "test21",
         "sample100_cu": "sample100"})
    u = pd.read_csv(UNSW / "p2_unsw_per_run.csv")
    u["setting"] = "UNSW/" + u.n_qubits.astype(str) + "qb"
    return pd.concat([n, u], ignore_index=True)


def identity_max_dev() -> float:
    """Sai lech lon nhat giua ECE_rare va 1 - trung binh(p), doc tu artifact.

    Bai khang dinh hai dai luong nay TRUNG nhau tren tap con mot lop; con so
    phai lay tu phep do chu khong viet tay."""
    p = NSL / "p2_rebuild_identity.csv"
    return float(pd.read_csv(p).abs_dev.max()) if p.exists() else float("nan")


def side_tables(long: pd.DataFrame) -> str:
    """Ba bang phu: low-data, prior shift, va ba bo hieu chinh.

    Truoc day ba phan nay chi nam trong cau van. Bang doc nhanh hon, va no
    la thu reviewer tim dau tien."""
    ld = pd.read_csv(NSL / "p2_rebuild_lowdata.csv")
    ps = pd.read_csv(NSL / "p2_rebuild_priorshift.csv")
    cal = pd.read_csv(NSL / "p2_rebuild_calibrators.csv")
    out = ["% Sinh boi runners/make_p2_rebuild_tables.py -- dung sua tay."]

    ns = sorted(ld.n_train.unique())
    g = ld.groupby(["n_train", "model"]).ece_full.mean()
    out += [r"\begin{table}[t]", r"\centering",
            r"\caption{Calibration error against training-set size on "
            r"KDDTest+, mean over $\pnRuns$ runs. Best per column in bold. "
            r"The quantum kernel leads at the smallest size only.}",
            r"\label{tab:lowdata}",
            r"\begin{tabular}{l" + "c" * len(ns) + "}", r"\toprule",
            "Model & " + " & ".join(f"$N={int(n)}$" for n in ns) + r" \\",
            r"\midrule"]
    best = {n: ld[ld.n_train == n].groupby("model").ece_full.mean().idxmin()
            for n in ns}
    for mdl in ORDER:
        cells = [(r"\textbf{" + num(g[(n, mdl)]) + "}") if best[n] == mdl
                 else num(g[(n, mdl)]) for n in ns]
        out.append(f"{PRETTY[mdl]} & " + " & ".join(cells) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]

    mixes = ["Balanced_50/50", "AttackHeavy_30/70", "DoS_only"]
    gp = ps.groupby(["mix", "model"]).ece_full.mean()
    bp = {mx: ps[ps["mix"] == mx].groupby("model").ece_full.mean().idxmin()
          for mx in mixes}
    out += [r"\begin{table}[t]", r"\centering",
            r"\caption{Calibration error under class-prior shift, mean over "
            r"$\pnRuns$ runs. Each condition is rebuilt from the full test "
            r"split. Best per column in bold.}",
            r"\label{tab:priorshift}",
            r"\begin{tabular}{lccc}", r"\toprule",
            r"Model & Balanced & Attack-heavy & DoS-only \\", r"\midrule"]
    for mdl in ORDER:
        cells = [(r"\textbf{" + num(gp[(mx, mdl)]) + "}") if bp[mx] == mdl
                 else num(gp[(mx, mdl)]) for mx in mixes]
        out.append(f"{PRETTY[mdl]} & " + " & ".join(cells) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]

    gc = cal.groupby(["model", "calibrator"]).ece_full.mean()
    cals = [("none", "none"), ("platt", "Platt"),
            ("isotonic", "isotonic"), ("temperature", "temperature")]
    out += [r"\begin{table}[t]", r"\centering",
            r"\caption{Calibration error before and after post-hoc "
            r"recalibration on KDDTest+, mean over $\pnRuns$ runs. A cell is "
            r"bold when recalibration improves on leaving the native "
            r"probability alone; only the quantum kernel has any.}",
            r"\label{tab:recal}",
            r"\begin{tabular}{lcccc}", r"\toprule",
            r"Model & " + " & ".join(lab for _, lab in cals) + r" \\",
            r"\midrule"]
    for mdl in ORDER:
        base = gc[(mdl, "none")]
        cells = []
        for key, _ in cals:
            v = num(gc[(mdl, key)])
            cells.append(r"\textbf{" + v + "}" if key != "none"
                         and gc[(mdl, key)] < base else v)
        out.append(f"{PRETTY[mdl]} & " + " & ".join(cells) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(out)


def percat_table() -> str:
    """Do tu tin trung binh theo nhom tan cong.

    Tren mot tap con mot lop thi ECE = 1 - p_tb, nen day la dung dai luong
    do, goi dung ten. Normal la lop 0 (thap moi tot), con lai la lop 1."""
    pc = pd.read_csv(NSL / "p2_rebuild_percat.csv")
    cats = ["Normal", "DoS", "Probe", "R2L", "U2R"]
    g = pc.groupby(["category", "model"]).mean_prob.mean()
    n = pc.groupby("category").n.first()
    best = {c: (g[c].idxmin() if c == "Normal" else g[c].idxmax()) for c in cats}
    out = ["% Sinh boi runners/make_p2_rebuild_tables.py -- dung sua tay.",
           r"\begin{table}[t]", r"\centering",
           r"\caption{Mean predicted attack probability by category on "
           r"KDDTest+, over $\pnRuns$ runs. Normal is the negative class, so "
           r"lower is better there and higher is better elsewhere. Every "
           r"model falls below the $0.5$ decision threshold on both rare "
           r"categories.}",
           r"\label{tab:percat}",
           r"\begin{tabular}{lrccccc}", r"\toprule",
           r"Category & $n$ & " + " & ".join(PRETTY[m] for m in ORDER) + r" \\",
           r"\midrule"]
    for c in cats:
        cells = [(r"\textbf{" + num(g[(c, m)]) + "}") if best[c] == m
                 else num(g[(c, m)]) for m in ORDER]
        out.append(f"{c} & {thousands(n[c])} & " + " & ".join(cells) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(out)


def regime_table(long: pd.DataFrame, st: pd.DataFrame) -> str:
    """Ban do che do: tong hop moi dieu kien thanh mot bang khuyen nghi.

    Cot "vs trees" doc tu verdict da hieu chinh Holm, khong viet tay."""
    ld = pd.read_csv(NSL / "p2_rebuild_lowdata.csv")
    ps = pd.read_csv(NSL / "p2_rebuild_priorshift.csv")
    e = st[st.metric == "ece_full"]

    rows = []
    for key, label in (("NSL-KDD/full", "NSL-KDD, operating mix"),
                       ("NSL-KDD/test21", "NSL-KDD, temporal drift"),
                       ("UNSW/4qb", r"UNSW-NB15, $\plegacyQubits$ qubits"),
                       ("UNSW/6qb", r"UNSW-NB15, $\punswQubits$ qubits")):
        sub = long[long.setting == key]
        s = e[e.setting == key].set_index("baseline")
        beats = all(s.loc[b, "verdict"] == "QSVM-favorable"
                    for b in ("RandomForest", "XGBoost"))
        rows.append((label, PRETTY[sub.groupby("model").ece_full.mean().idxmin()],
                     r"\checkmark" if beats else "--"))

    ns = sorted(ld.n_train.unique())
    for n in ns:
        sub = ld[ld.n_train == n].groupby("model").ece_full.mean()
        rows.append((f"Label scarcity, $N={int(n)}$", PRETTY[sub.idxmin()],
                     r"\checkmark" if (sub["QSVM"] < sub["RandomForest"]
                                       and sub["QSVM"] < sub["XGBoost"]) else "--"))
    for mix, lab in (("Balanced_50/50", "Balanced prior"),
                     ("AttackHeavy_30/70", "Attack-heavy prior"),
                     ("DoS_only", "DoS-only prior")):
        sub = ps[ps["mix"] == mix].groupby("model").ece_full.mean()
        rows.append((lab, PRETTY[sub.idxmin()],
                     r"\checkmark" if (sub["QSVM"] < sub["RandomForest"]
                                       and sub["QSVM"] < sub["XGBoost"]) else "--"))

    out = ["% Sinh boi runners/make_p2_rebuild_tables.py -- dung sua tay.",
           r"\begin{table}[t]", r"\centering",
           r"\caption{Reliability regime map. For each condition, the "
           r"best-calibrated model and whether the quantum kernel is better "
           r"calibrated than both tree ensembles. It leads outright only "
           r"under the smallest training budget, and beats both tree "
           r"ensembles everywhere.}",
           r"\label{tab:regime}",
           r"\begin{tabular}{llc}", r"\toprule",
           r"Condition & Best calibrated & Beats both trees \\", r"\midrule"]
    out += [f"{a} & {b} & {c} " + r"\\" for a, b, c in rows]
    out += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(out)


def main() -> int:
    long = load_long()
    st = pd.read_csv(NSL / "p2_rebuild_pairwise.csv")
    platt = pd.read_csv(NSL / "p2_rebuild_platt.csv")
    ref = pd.read_csv(NSL / "p2_rebuild_refarm.csv")
    cal = pd.read_csv(NSL / "p2_rebuild_calibrators.csv")

    for name, text in (("main_table.tex", main_table(long)),
                       ("side_tables.tex", side_tables(long)),
                       ("percat_table.tex", percat_table()),
                       ("regime_table.tex", regime_table(long, st)),
                       ("numbers_macros.tex",
                        macros(long, st, platt, ref, cal, identity_max_dev()))):
        p = OUT / name
        with io.open(p, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"  -> {p.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
