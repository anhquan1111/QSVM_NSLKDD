"""Sinh bang cho bai hoi nghi AICON 2026 (paper 3).

Chay:  python runners/make_paper3_tables.py
Xuat:  paper/paper3_aicon/tables/degeneracy_census.tex
       results/unsw/paper3/degeneracy_census.csv

Bang 1 la BANG KIEM DEM SUY BIEN. No phai quet MOI model trong ca hai giao
thuc, khong chi hai cai da biet -- neu khong thi bang chi xac nhan dinh kien
cua nguoi viet.

Dinh nghia suy bien dung o day:

  * Giao thuc cu (nhi phan, N=100): `is_degenerate` da luu san trong artifact,
    hoac recall == 1.0 voi precision == ti le tan cong cua tap test.
  * Giao thuc revision (macro, N toi 10k): `recall_macro == 0.5` -- voi bai
    toan hai lop, du doan hang cho dung 0.5 macro recall.

Ket luan phai rut ra tu so lieu chu khong viet tay: xem `verdict` o cuoi.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BS = chr(92)
TEX_OUT = ROOT / "paper" / "paper3_aicon" / "tables"
CSV_OUT = ROOT / "results" / "unsw" / "paper3"
TEX_OUT.mkdir(parents=True, exist_ok=True)
CSV_OUT.mkdir(parents=True, exist_ok=True)

LEGACY_KERNELS = ["quantum", "linear", "poly", "rbf"]
PRETTY = {
    "quantum": "Quantum (ZZ)", "linear": "SVM-linear",
    "poly": "SVM-poly2", "rbf": "SVM-RBF",
    "QSVM_ZZ": "QSVM-ZZ", "QSVM_Z": "QSVM-Z", "SVM_Linear": "SVM-linear",
    "SVM_Poly2": "SVM-poly2", "SVM_RBF": "SVM-RBF",
    "RandomForest": "Random forest", "XGBoost": "XGBoost",
}

# C ma nhanh `tuned_once` cua giao thuc revision dung o moi N: tune MOT lan
# tren tap tuning 2000 mau, macro F1, quy tac 1-SE (runners/run_c4.py).
REV_TUNED_ONCE_PATH = "results/unsw/c4_revision/cache/tuned_once_UNSW_NB15.json"
REV_TUNED_ONCE = {
    k: v.get("C", v.get("svc__C"))
    for k, v in json.load(io.open(ROOT / REV_TUNED_ONCE_PATH,
                                  encoding="utf-8")).items()
    if isinstance(v, dict) and ("C" in v or "svc__C" in v)
}

# Ten giao thuc nhu muc 2 cua bai dat, khong phai ten arm trong code.
PRETTY_PROTO = {
    "legacy-tuned": "tuned",
    "legacy-neutral": "tuned data, neutral $C$",
    "revision-tuned_once": "revision",
}


def load(rel: str) -> dict:
    with io.open(ROOT / rel, encoding="utf-8") as f:
        return json.load(f)


def census_legacy_tuned() -> list[dict]:
    """Giao thuc cu, C lay tu tune. 4 qubit, N_train = N_test = 100, 5 seed."""
    tune = load("results/unsw/c_tuning_results.json")
    res = load("results/unsw/c3_results_statevector.json")
    rows = []
    for k in LEGACY_KERNELS:
        s = res["summary"][k]
        per = res["per_run"]
        n_runs = len(per)
        # Suy bien = goi MOI ban ghi la tan cong: recall == 1 va precision
        # dung bang ti le tan cong cua tap test.
        n_deg = sum(
            1 for r in per
            if abs(r[k]["recall"] - 1.0) < 1e-12
            and abs(r[k]["precision"] - r[k]["accuracy"]) < 1e-12
        )
        rows.append(dict(
            protocol="legacy-tuned", n_qubits=4, n_train=100, n_runs=n_runs,
            model=k, selected_C=tune[k]["C_best"], n_degenerate=n_deg,
            recall=round(s["recall_mean"], 4), recall_std=round(s["recall_std"], 4),
            precision=round(s["precision_mean"], 4),
        ))
    return rows


def census_legacy_neutral() -> list[dict]:
    """Cung du lieu, nhung C=1.0 cho tat ca, quet qua 7 gia tri K."""
    c1 = load("results/unsw/c1_results.json")
    n_runs = sum(len(e["per_run"]) for e in c1["k_sweep"])
    n_deg = sum(
        1 for e in c1["k_sweep"] for r in e["per_run"]
        if r["quantum"]["is_degenerate"]
    )
    s = c1["k_sweep"][-1]["summary"]["quantum"]
    return [dict(
        protocol="legacy-neutral", n_qubits=4, n_train=100, n_runs=n_runs,
        model="quantum", selected_C=c1["metadata"]["C_for_all"], n_degenerate=n_deg,
        recall=None, recall_std=None, precision=None,
    )]


def census_revision() -> list[dict]:
    """Giao thuc revision: 6 qubit, N toi 10k, 10 run, 7 model, 2 nhanh tune.

    Quet TOAN BO -- moi model, moi N, moi nhanh -- roi chi giu cai nao thuc su
    co suy bien.
    """
    df = pd.read_csv(ROOT / "results/unsw/c4_revision/c4_per_run_unsw_natural_refit_per_N.csv")
    df = df[df.test_split == "full_test"]
    # Phan bien R1: macro recall = 0,5 chua chung minh du doan hang (mo hinh
    # doan bua cung cho 0,5). Them dieu kien: precision macro = accuracy / 2,
    # chi xay ra khi lop kia khong duoc du doan lan nao.
    const = ((df.recall_macro.round(10) == 0.5)
             & ((df.precision_macro - df.accuracy / 2).abs() < 1e-9))
    df = df.assign(_const=const)
    deg = df[df._const]
    rows = []
    for (model, arm, n_train), g in df.groupby(["model", "arm", "n_train"]):
        d = int(g._const.sum())
        if d == 0:
            continue
        rows.append(dict(
            protocol=f"revision-{arm}", n_qubits=6, n_train=int(n_train),
            n_runs=len(g), model=model, selected_C=REV_TUNED_ONCE[model],
            n_degenerate=d,
            recall=round(g.recall_macro.mean(), 4), recall_std=None,
            precision=None,
        ))
    # Ghi lai tong so de doi chieu, ke ca khi khong co suy bien nao.
    totals = {
        "n_rows_scanned": len(df),
        "n_models": df.model.nunique(),
        "n_degenerate_rows": len(deg),
        "models_with_degeneracy": sorted(deg.model.unique().tolist()),
        "qsvm_zz_min_recall_macro": float(df[df.model == "QSVM_ZZ"].recall_macro.min()),
        "degenerate_n_train": sorted(deg.n_train.unique().astype(int).tolist()),
        "degenerate_arms": sorted(deg.arm.unique().tolist()),
        # Ty le tan cong cua tap test day du = accuracy cua bo doan hang.
        "degenerate_accuracy": sorted(deg.accuracy.round(4).unique().tolist()),
        "test_attack_ratio": None,
    }
    return rows, totals


def to_latex(df: pd.DataFrame) -> str:
    lines = [
        "% Sinh boi runners/make_paper3_tables.py -- dung sua tay.",
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Degeneracy census. A model is degenerate on a run when it",
        r"predicts the attack class for every test record, i.e.\ $\mathrm{TN}",
        r"= \mathrm{FN} = 0$, checked directly on the predictions. Tuned rows",
        r"use the $C$ selected once on the training split of run~1. The",
        r"revision row is the RBF kernel at $N_{\text{train}} = 100$ with the",
        r"$C$ tuned once on a separate set; no other model, size or arm of",
        r"that protocol is degenerate.}",
        r"\label{tab:degeneracy}",
        # Ba cot so can phai, ma tieu de lai rong hon so ben duoi, nen khong
        # chen khoang thi tieu de dinh vao nhau: "Selected C Degenerate Runs"
        # doc ra nhu mot cum.
        r"\begin{tabular}{l@{\hskip 1.2em}l@{\hskip 1.4em}r@{\hskip 1.4em}"
        r"r@{\hskip 1.2em}r}",
        r"\toprule",
        r"Protocol & Model & Selected $C$ & Degenerate & Runs \\",
        r"\midrule",
    ]
    prev = None
    for _, r in df.iterrows():
        proto = r["protocol"]
        # Ten arm noi bo (`legacy-tuned`, `revision-tuned_once`) khong xuat
        # hien o dau khac trong bai: muc 2 chi dat ten "tuned" va "revision".
        # De nguyen thi bang va van ban goi hai ten khac nhau cho mot thu,
        # va "legacy-neutral" thi khong duoc dinh nghia o dau ca.
        if proto != prev and proto in PRETTY_PROTO:
            shown = PRETTY_PROTO[proto]
            if proto.startswith("revision"):
                shown += f", $N={int(r['n_train'])}$"
        elif proto != prev:
            shown = proto.replace("_", r"\_")
        else:
            shown = ""
        if prev is not None and proto != prev:
            lines.append(r"\addlinespace[2pt]")
        prev = proto
        c = "--" if pd.isna(r["selected_C"]) else f"{r['selected_C']:g}"
        lines.append(
            f"{shown} & {PRETTY.get(r['model'], r['model'])} & {c} & "
            f"{int(r['n_degenerate'])} & {int(r['n_runs'])} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(lines)


def write_macros(df: pd.DataFrame, totals: dict, extra: dict) -> str:
    """Moi con so bai trich dan deu phai di qua day.

    Cung khuon voi `paper/paper1/tables/ref_arm_macros.tex`: prose khong bao
    gio viet so truc tiep, nen sua artifact la bai tu doi theo, va
    `audit_paper3.py` chi phai doi chieu MOT cho.
    """
    tune = load("results/unsw/c_tuning_results.json")
    deg = load("results/unsw/c3_results_statevector.json")["summary"]["quantum"]
    neu = load("results/unsw/c3_results_statevector_C1.json")["summary"]["quantum"]
    cmp4a = load("results/unsw/c3_results_statevector_C1.json")["comparison_vs_1_4a"]
    cmp15 = load("results/unsw/c4_results_C1.json")["comparison_vs_1_5"]
    c1 = load("results/unsw/c1_results.json")

    floor = next(r["mean"] for r in tune["quantum"]["scores_per_C"] if r["C"] == 0.01)
    q_best_nondeg = max(r["mean"] for r in tune["quantum"]["scores_per_C"] if r["C"] > 0.1)
    ks = sorted(c1["k_sweep"], key=lambda e: e["K"])
    plateau_f1 = ks[-1]["summary"]["quantum"]["f1_mean"]
    plateau_ks = [e["K"] for e in ks
                  if abs(e["summary"]["quantum"]["f1_mean"] - plateau_f1) < 1e-15]

    m = {
        # Cai bay tune
        "degFloor": f"{floor:.4f}",
        "degFloorFull": f"{floor:.16f}",
        "qBestNonDeg": f"{q_best_nondeg:.4f}",
        "selectedC": f"{tune['quantum']['C_best']:g}",
        "cGrid": ", ".join(f"{c:g}" for c in tune["quantum"]["grid"]),
        "cvFolds": str(load("results/unsw/c_tuning_results.json")["metadata"]["n_folds"]),
        "cvScoring": load("results/unsw/c_tuning_results.json")["metadata"]["scoring"],
        # Hau qua tren tap test
        "degRecall": f"{deg['recall_mean']:.3f}",
        "degRecallStd": f"{deg['recall_std']:.0f}",
        "degPrecision": f"{deg['precision_mean']:.3f}",
        "degTN": f"{cmp4a['tn_mean_old']['quantum']:.1f}",
        "neuRecall": f"{neu['recall_mean']:.3f}",
        "neuPrecision": f"{neu['precision_mean']:.3f}",
        "neuTN": f"{cmp4a['tn_mean_new']['quantum']:.1f}",
        "neuFone": f"{neu['f1_mean']:.4f}",
        "degFone": f"{deg['f1_mean']:.4f}",
        # Kernel vo can
        "ktaShared": f"{deg['kta_mean']:.6f}",
        "ktaSharedFull": repr(deg["kta_mean"]),
        # Robustness cung la ao
        "perturbRangeOld": f"{cmp15['qsvm_perturb_range_old']:.3f}",
        "perturbRangeNew": f"{cmp15['qsvm_perturb_range_new']:.4f}",
        # Quet K
        "kPlateauFone": f"{plateau_f1:.4f}",
        "kPlateauFrom": str(min(plateau_ks)),
        "kSweepRuns": str(sum(len(e["per_run"]) for e in ks)),
        "kSweepDeg": str(sum(1 for e in ks for r in e["per_run"]
                             if r["quantum"]["is_degenerate"])),
        # Bang kiem dem
        "revRowsScanned": str(totals["n_rows_scanned"]),
        "revModels": str(totals["n_models"]),
        "revDegRows": str(totals["n_degenerate_rows"]),
        "revDegModel": PRETTY[totals["models_with_degeneracy"][0]],
        "revQsvmMinRecall": f"{totals['qsvm_zz_min_recall_macro']:.3f}",
        "legacyQubits": "4",
        "legacyN": "100",
        "legacySeeds": str(len(load("results/unsw/c3_results_statevector.json")["per_run"])),
        "revQubits": "6",
        "revMaxN": "{:,}".format(int(max(
            pd.read_csv(ROOT / "results/unsw/c4_revision"
                        / "c4_per_run_unsw_natural_refit_per_N.csv").n_train
        ))).replace(",", BS + ","),
        "revRuns": str(int(pd.read_csv(ROOT / "results/unsw/c4_revision"
                       / "c4_per_run_unsw_natural_refit_per_N.csv").run_id.nunique())),
    }
    m.update(extra)
    lines = ["% Sinh boi runners/make_paper3_tables.py -- dung sua tay.",
             "% Prose KHONG duoc viet so truc tiep; dung macro o day."]
    lines += [f"\\newcommand{{\\p{k}}}{{{v}}}" for k, v in m.items()]
    return "\n".join(lines) + "\n"


OBJ_PRETTY = {
    "f1_binary": r"binary $F_1$",
    "f1_macro": r"macro $F_1$",
    "balanced_accuracy": "balanced accuracy",
}


def objective_table() -> tuple[str, pd.DataFrame]:
    """Bang 2 -- ham muc tieu nao tranh duoc cu sup, DO chu khong doan.

    Bai truoc day khang dinh bang lap luan rang macro F1 va balanced accuracy
    "neither would have selected the degenerate constant here". Day la ket
    qua do that, va no chi dung MOT PHAN: dung cho kernel luong tu va RBF,
    SAI cho kernel tuyen tinh, noi ca ba ham muc tieu deu chon cung mot C va
    C do van sup tren mot run. Bang phai cho thay ca cho no sai.
    """
    o = pd.read_csv(CSV_OUT / "p3_objective.csv")
    order = ["quantum", "rbf", "poly", "linear"]
    o["_k"] = o.kernel.map({k: i for i, k in enumerate(order)})
    o["_o"] = o.objective.map({k: i for i, k in enumerate(OBJ_PRETTY)})
    o = o.sort_values(["_k", "_o"])

    lines = [
        "% Sinh boi runners/make_paper3_tables.py -- dung sua tay.",
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{What selection returns on a denser grid under three",
        r"objectives, with $C$ selected once on run~1 and applied to all five",
        r"runs, as in the tuned protocol. CV score is the mean of the five",
        r"per-fold scores. \emph{Degen.} counts the runs on which the selected",
        r"model predicts the attack class for every test record. On this grid",
        r"even binary $F_1$ finds a non-degenerate $C$ for the quantum kernel,",
        r"while for the linear kernel every objective returns a $C$ that is",
        r"degenerate on one run.}",
        r"\label{tab:objective}",
        r"\begin{tabular}{l@{\hskip 1.0em}l@{\hskip 1.4em}r@{\hskip 1.4em}"
        r"r@{\hskip 1.4em}r@{\hskip 1.4em}r}",
        r"\toprule",
        r"Kernel & Selection objective & Returns $C$ & CV score"
        r" & Degen. & Macro $\Fone$ \\",
        r"\midrule",
    ]
    prev = None
    for _, r in o.iterrows():
        if prev is not None and r.kernel != prev:
            lines.append(r"\addlinespace[2pt]")
        shown = PRETTY.get(r.kernel, r.kernel) if r.kernel != prev else ""
        prev = r.kernel
        lines.append(
            f"{shown} & {OBJ_PRETTY[r.objective]} & {r.selected_C:.3g} & "
            f"{r.cv_mean:.4f} & {int(r.n_degenerate)}/{int(r.n_runs)} & "
            f"{r.test_f1_macro:.4f} " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(lines), o


def objective_macros(o: pd.DataFrame) -> dict:
    """Macro cho muc moi. Moi con so bai viet phai di qua day."""
    cur = pd.read_csv(CSV_OUT / "p3_c_curve.csv")
    rep = json.load(io.open(CSV_OUT / "p3_reproduction.json", encoding="utf-8"))
    g = (cur.groupby(["kernel", "C"])
            .agg(f1=("f1", "mean"), f1m=("f1_macro", "mean"),
                 deg=("degenerate", "sum"))
            .reset_index())
    q = g[g.kernel == "quantum"].sort_values("C")
    nrun = int(cur.run.nunique())

    # Bien chuyen: C nho nhat ma khong con run nao sup.
    esc = q[q.deg == 0].C.min()
    lo, hi = q[q.C == q.C.min()].iloc[0], q[q.C == esc].iloc[0]

    def row(k, obj):
        return o[(o.kernel == k) & (o.objective == obj)].iloc[0]

    m = {
        "curveNc": str(len(rep["c_grid"])),
        "curveCmin": f"{min(rep['c_grid']):g}",
        "curveCmax": f"{max(rep['c_grid']):g}",
        "curveRuns": str(nrun),
        # Do "mu" cua F1 nhi phan: di tu day suy bien den diem thoat, F1
        # nhi phan nhuc nhich bao nhieu, macro F1 bao nhieu.
        "curveEscapeC": f"{esc:g}",
        "curveFoneLo": f"{lo.f1:.4f}",
        "curveFoneHi": f"{hi.f1:.4f}",
        "curveFoneRise": f"{hi.f1 - lo.f1:+.4f}",
        "curveMacroLo": f"{lo.f1m:.4f}",
        "curveMacroHi": f"{hi.f1m:.4f}",
        "curveMacroRise": f"{hi.f1m - lo.f1m:+.4f}",
        "curveRiseRatio": f"{(hi.f1m - lo.f1m) / (hi.f1 - lo.f1):.0f}",
        # Cong kiem chung tai lap.
        "reproCv": f"{rep['cv_max_abs_dev']:g}",
        "reproTest": f"{max(rep['test_tuned_max_abs_dev'], rep['test_neutral_max_abs_dev']):.1e}",
    }
    for k, tag in (("quantum", "Q"), ("linear", "Lin"), ("rbf", "Rbf")):
        for obj, otag in (("f1_binary", "Bin"), ("f1_macro", "Mac"),
                          ("balanced_accuracy", "Bal")):
            r = row(k, obj)
            m[f"obj{tag}{otag}C"] = f"{r.selected_C:.3g}"
            m[f"obj{tag}{otag}Deg"] = f"{int(r.n_degenerate)}/{int(r.n_runs)}"
    return m


# --------------------------------------------------------------------------
# Ban camera-ready: cac phep do theo y phan bien (run_paper3_camera_ready.py)
# --------------------------------------------------------------------------
CR_ROWS = [
    # (nhan trong bang, class_weight, objective, rule)
    (r"binary $F_1$, $\arg\max$", "none", "f1_binary", "first"),
    (r"binary $F_1$, one-SE rule", "none", "f1_binary", "1se"),
    (r"binary $F_1$, balanced class weights", "balanced", "f1_binary", "first"),
    (r"binary $F_1$, normal class positive", "none", "f1_normal", "first"),
    (r"macro $F_1$, $\arg\max$", "none", "f1_macro", "first"),
    (r"MCC, $\arg\max$", "none", "mcc", "first"),
]
CR_KERNELS = ["quantum", "linear", "poly", "rbf"]


def cr_table() -> tuple[str, pd.DataFrame]:
    """Bang 3 -- chon C RIENG trong tung run, o N = 100 va N = 500.

    Tra loi R1.3 (chon theo tung run), R4.1 (quy mo lon hon), R4.3 (lop duong
    la lop thieu so) va R4.4 (trong so lop, MCC, quy tac 1-SE). Luoi C goc.
    """
    d = pd.read_csv(CSV_OUT / "p3cr_selection.csv")
    d = d[d.grid == "original"]
    sizes = sorted(d.n.unique())
    lines = [
        "% Sinh boi runners/make_paper3_tables.py -- dung sua tay.",
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Degenerate runs (of five) when $C$ is selected separately",
        r"on each run's own training split, on the original grid, with",
        r"$N = N_{\text{train}} = N_{\text{test}}$. Q, L, P, R",
        r"are the quantum, linear, degree-two polynomial and RBF kernels. At",
        r"$N = 500$ the $\arg\max$ trap disappears, while the one-SE rule and",
        r"class weighting can still return a constant classifier.}",
        r"\label{tab:remedies}",
        r"\setlength{\tabcolsep}{3.2pt}",
        r"\begin{tabular}{l" + "cccc" * len(sizes) + "}",
        r"\toprule",
        " & " + " & ".join(
            # Tieu de ngan: "N_train = N_test = 100" rong hon bon cot so ben
            # duoi, lam bang tran le textwidth 4,8 inch cua llncs.
            rf"\multicolumn{{4}}{{c}}{{$N = {n}$}}"
            for n in sizes) + r" \\",
        "".join(rf"\cmidrule(lr){{{2 + 4 * i}-{5 + 4 * i}}}"
                for i in range(len(sizes))),
        "Selection & " + " & ".join(["Q & L & P & R"] * len(sizes)) + r" \\",
        r"\midrule",
    ]
    for label, cw, obj, rule in CR_ROWS:
        cells = []
        for n in sizes:
            for k in CR_KERNELS:
                q = d[(d.n == n) & (d.kernel == k) & (d.class_weight == cw)
                      & (d.objective == obj) & (d.rule == rule)]
                assert len(q) == 5, (n, k, cw, obj, rule, len(q))
                cells.append(str(int(q.test_degenerate.sum())))
        lines.append(label + " & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(lines), d


def cr_macros() -> dict:
    """Moi con so moi cua ban camera-ready di qua day."""
    d = pd.read_csv(CSV_OUT / "p3cr_selection.csv")
    sc = pd.read_csv(CSV_OUT / "p3cr_kernel_scale.csv")
    gates = json.load(io.open(CSV_OUT / "p3cr_gates.json", encoding="utf-8"))
    cur = pd.read_csv(CSV_OUT / "p3_c_curve.csv")
    tune = load("results/unsw/c_tuning_results.json")
    c4m = load("results/unsw/c4_results_C1.json")["metadata"]
    assert gates["passed"], "cong kiem chung cua run_paper3_camera_ready truot"

    def deg(n, k, cw="none", obj="f1_binary", rule="first", grid="original"):
        q = d[(d.n == n) & (d.kernel == k) & (d.class_weight == cw)
              & (d.objective == obj) & (d.rule == rule) & (d.grid == grid)]
        return int(q.test_degenerate.sum())

    qrows = {r["C"]: r for r in tune["quantum"]["scores_per_C"]}
    floor_std = qrows[0.01]["std"]
    best_nd = max((r for r in tune["quantum"]["scores_per_C"] if r["C"] > 0.1),
                  key=lambda r: r["mean"])
    sel = d[(d.class_weight == "none") & (d.objective == "f1_binary")
            & (d.rule == "first") & (d.grid == "original")]
    n500 = sel[sel.n == 500]
    # Bien sup cua tung kernel tren duong cong C day: C lon nhat ma MOI run
    # deu sup.
    g = cur.groupby(["kernel", "C"]).degenerate.sum().reset_index()
    nrun = int(cur.run.nunique())
    edge = {k: float(g[(g.kernel == k) & (g.degenerate == nrun)].C.max())
            for k in CR_KERNELS}
    spread = sc[sc.n == 100].groupby("kernel").offdiag_std.mean()
    # Cau van dua vao hai dang thuc nay: "\pprLinHundred{} for each classical
    # kernel" va "\pedgeRbf{} for both the RBF and the quantum kernel".
    assert deg(100, "linear") == deg(100, "poly") == deg(100, "rbf")
    assert edge["quantum"] == edge["rbf"]
    # "the order follows the spread": bien sup tang khi do phan tan giam.
    order_edge = sorted(CR_KERNELS, key=lambda k: edge[k])
    order_spread = sorted(CR_KERNELS, key=lambda k: -spread[k])
    assert [k for k in order_edge if k != "quantum"] == [
        k for k in order_spread if k != "quantum"]
    assert spread["quantum"] == spread.min()
    m = {
        # Dinh nghia suy bien da kiem lai (R1.1)
        "curveEvals": str(len(cur)),
        "curveTnZeroFnPos": str(int(((cur.tn == 0) & (cur.fn > 0)).sum())),
        # Do lech theo fold (R4.1)
        "floorFoldStd": f"{floor_std:.3f}",
        "bestNonDegFoldStd": f"{best_nd['std']:.3f}",
        "floorGap": f"{tune['quantum']['scores_per_C'][0]['mean'] - best_nd['mean']:.4f}",
        # Thiet lap (R4 minor)
        "kSelect": "35",
        "trainAttackRatio": f"{sc[sc.n == 100].train_attack_ratio.mean():.2f}",
        "testAttackRatio": f"{sc[sc.n == 100].test_attack_ratio.mean():.3f}",
        "nFiveHundredTrainRatio": f"{sc[sc.n == 500].train_attack_ratio.mean():.2f}",
        "perturbSigmas": ", ".join(f"{x:g}" for x in c4m["perturbation_sigmas"]),
        # Chon theo tung run (R1.3) va quy mo lon hon (R4.1, R4.5)
        "prQHundred": str(deg(100, "quantum")),
        "prLinHundred": str(deg(100, "linear")),
        "prMaxFiveHundred": str(max(deg(500, k) for k in CR_KERNELS)),
        "prOneSeLinFive": str(deg(500, "linear", rule="1se")),
        "prOneSePolyFive": str(deg(500, "poly", rule="1se")),
        "prBalQFive": str(deg(500, "quantum", cw="balanced")),
        "nFiveBaseline": f"{n500.cv_constant_baseline.mean():.3f}",
        "nFiveFoldStdMax": f"{n500.cv_std.max():.3f}",
        "macroHundredLo": f"{sel[sel.n == 100].groupby('kernel').test_f1_macro.mean().min():.2f}",
        "macroHundredHi": f"{sel[sel.n == 100].groupby('kernel').test_f1_macro.mean().max():.2f}",
        "macroFiveLo": f"{n500.groupby('kernel').test_f1_macro.mean().min():.2f}",
        "macroFiveHi": f"{n500.groupby('kernel').test_f1_macro.mean().max():.2f}",
        # Thang do Gram va bien sup (R4.2)
        "edgeQ": f"{edge['quantum']:.2g}",
        "edgeRbf": f"{edge['rbf']:.2g}",
        "edgeLin": f"{edge['linear']:.2g}",
        "edgePoly": f"{edge['poly']:.2g}",
        "spreadQ": f"{spread['quantum']:.2f}",
        "spreadRbf": f"{spread['rbf']:.2f}",
        "spreadLin": f"{spread['linear']:.1f}",
        "spreadPoly": f"{spread['poly']:.1f}",
        # Vi sao RBF sup o giao thuc revision (R4.6)
        "revRbfC": f"{REV_TUNED_ONCE['SVM_RBF']:g}",
        "revTuneN": "2\\,000",
        "nLarge": str(int(d.n.max())),
    }
    return m


def main() -> int:
    rev_rows, totals = census_revision()
    rows = census_legacy_tuned() + census_legacy_neutral() + rev_rows
    df = pd.DataFrame(rows)

    csv_path = CSV_OUT / "degeneracy_census.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")
    tex_path = TEX_OUT / "degeneracy_census.tex"
    with io.open(tex_path, "w", encoding="utf-8") as f:
        f.write(to_latex(df))

    with io.open(CSV_OUT / "degeneracy_totals.json", "w", encoding="utf-8") as f:
        json.dump(totals, f, indent=1)

    obj_tex, obj_df = objective_table()
    obj_path = TEX_OUT / "objective_table.tex"
    with io.open(obj_path, "w", encoding="utf-8") as f:
        f.write(obj_tex)

    cr_tex, _ = cr_table()
    cr_path = TEX_OUT / "remedies_table.tex"
    with io.open(cr_path, "w", encoding="utf-8") as f:
        f.write(cr_tex)

    mac_path = TEX_OUT / "numbers_macros.tex"
    with io.open(mac_path, "w", encoding="utf-8") as f:
        f.write(write_macros(df, totals,
                             {**objective_macros(obj_df), **cr_macros()}))

    print(df.to_string(index=False))
    print()
    print("Quet giao thuc revision:")
    for k, v in totals.items():
        print(f"  {k:28s} {v}")

    # Ket luan phai doc duoc tu so lieu.
    q_deg = df[(df.model.isin(["quantum", "QSVM_ZZ", "QSVM_Z"]))
               & (df.n_degenerate > 0)]
    c_deg = df[(~df.model.isin(["quantum", "QSVM_ZZ", "QSVM_Z"]))
               & (df.n_degenerate > 0)]
    print()
    print(f"  Suy bien o nhanh luong tu : {len(q_deg)} cau hinh")
    print(f"  Suy bien o nhanh co dien  : {len(c_deg)} cau hinh")
    print(f"  -> {csv_path.relative_to(ROOT).as_posix()}")
    print(f"  -> {tex_path.relative_to(ROOT).as_posix()}")
    print(f"  -> {obj_path.relative_to(ROOT).as_posix()}")
    print(f"  -> {mac_path.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
