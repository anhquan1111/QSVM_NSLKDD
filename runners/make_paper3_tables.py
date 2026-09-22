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
    deg = df[df.recall_macro.round(10) == 0.5]
    rows = []
    for (model, arm, n_train), g in df.groupby(["model", "arm", "n_train"]):
        d = len(g[g.recall_macro.round(10) == 0.5])
        if d == 0:
            continue
        rows.append(dict(
            protocol=f"revision-{arm}", n_qubits=6, n_train=int(n_train),
            n_runs=len(g), model=model, selected_C=None, n_degenerate=d,
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
    }
    return rows, totals


def to_latex(df: pd.DataFrame) -> str:
    lines = [
        "% Sinh boi runners/make_paper3_tables.py -- dung sua tay.",
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Degeneracy census. A model is degenerate on a run when it",
        r"assigns every test record to the attack class ($\mathrm{TN}=0$).",
        r"Collapse is not specific to the quantum kernel: under the tuned",
        r"protocol it occurs for three of the four kernels, under the revision",
        r"protocol only for an RBF kernel, and under a neutral $C$ for none.",
        r"What is specific to the quantum kernel is that it collapsed on",
        r"\emph{every} run, so no value of $C$ on the grid scored above the",
        r"degenerate floor and $\arg\max$ selection locked the collapse in.}",
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
        r"\caption{What selection returns on a denser grid, under three",
        r"objectives. The grid is the same for every row; only the quantity",
        r"$\arg\max$ maximises changes. \emph{Degenerate} counts the runs on",
        r"which the selected model assigns every test record to the attack",
        r"class. Two things follow. A class-averaged objective is not",
        r"sufficient: for the linear kernel all three objectives return the",
        r"same $C$ and that $C$ is still degenerate on one run. And the",
        r"original grid, not only the objective, was part of the failure:",
        r"on this grid even binary $F_1$ finds a non-degenerate maximum for",
        r"the quantum kernel.}",
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

    mac_path = TEX_OUT / "numbers_macros.tex"
    with io.open(mac_path, "w", encoding="utf-8") as f:
        f.write(write_macros(df, totals, objective_macros(obj_df)))

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
