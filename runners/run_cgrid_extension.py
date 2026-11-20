"""Mo rong luoi C cua ho SVM/QSVM o N lon (Paper 1 QMI, viec 4 ngay 20-11).

Vi sao: o N=10^4 (natural, tuned_per_N), QSVM chon C=10 -- dung tran luoi
{0.1,...,10} -- o 7/10 run, SVM-RBF cung vay; SVM-linear chon C=0.1 (day luoi) o
10/10 run. Theo luat 1-SE (C nho nhat con trong best - SE), chon dung tran nghia la
diem CV con dang tang o mep luoi. Script dung lai dung tap train cua tung run, do
lai C tren luoi mo rong, roi cham lai tren KDDTest+ day du.

Giu nguyen moi thu khac: 1-SE, 5-fold StratifiedKFold random_state=42 (nhu run_c4),
C_Z = C_ZZ, cay (RF/XGB) khong doi (doc diem tu cache). Khong ghi vao cache cu.

Cong kiem: fit lai voi C cu phai cho lai macro-F1 cua cache c4_dedup (lech <= 1e-3);
khong qua thi dung, khong ghi so moi.

    uv run python runners/run_cgrid_extension.py --n 5000 10000
    -> results/nslkdd/c4_cgrid/cgrid_per_run.csv   (moi N, run, model mot dong)
    -> results/nslkdd/c4_cgrid/cgrid_cv_rows.csv   (diem CV tung C, de kiem 1-SE)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners")]
from src import c4_pipeline as c4  # noqa: E402
import run_dedup_sensitivity as rd  # noqa: E402

GRID_OLD = [0.1, 0.3, 0.5, 1.0, 3.0, 5.0, 10.0]
GRID_EXT = [0.03, 0.1, 0.3, 0.5, 1.0, 3.0, 5.0, 10.0, 30.0, 100.0]
CACHE = ROOT / "results/nslkdd/c4_dedup/cache"
OUT = ROOT / "results/nslkdd/c4_cgrid"
GATE_TOL = 1e-3


def svm_tune(name, X, y, grid):
    r = c4.tune_estimator(c4.make_svm_estimator(name), {"svc__C": grid}, X, y,
                          selection="1SE", complexity_fn=lambda p: p["svc__C"],
                          cv_folds=5, random_state=42)
    rows = [{"C": row["params"]["svc__C"], "mean_score": row["mean_score"],
             "se_score": row["se_score"]} for row in r["rows"]]
    return float(r["chosen"]["params"]["svc__C"]), rows


def one_run(data, spec, protocol, n: int, run_id: int) -> tuple[list[dict], list[dict]]:
    meta = json.loads((CACHE / f"natural_refit_per_N_tuned_per_N_N{n}_run{run_id}.json")
                      .read_text(encoding="utf-8"))
    run_seed, hp = int(meta["run_seed"]), meta["hyperparameters"]
    f1_old = {m: meta["splits"]["full_test"][m]["f1_macro"] for m in rd.MODEL_ORDER}

    grid_n = rd.resolve_grid(protocol, spec, "natural")
    df_train = c4.build_nested_chain(data, run_id, grid_n, run_seed, "natural")[n]
    if int(c4.rare_mask(df_train, spec).sum()) != int(meta["n_rare_train"]):
        raise SystemExit(f"N={n} run{run_id}: tap train khong tai hien duoc")
    y = df_train["label_binary"].to_numpy(np.int64)
    fc = data.feature_cols
    rep = c4.make_representation("refit_per_N", select_k=spec.select_k,
                                 n_components=spec.n_qubits)
    rep.fit(df_train, fc)
    X_ang, X_pca = rep.transform(df_train, fc)
    Xte_ang, Xte_pca = rep.transform(data.df_test_full, fc)
    y_te = data.df_test_full["label_binary"].to_numpy(np.int64)
    psi_tr = {k: c4.compute_statevectors_fast(X_ang, k, spec.n_qubits) for k in ("ZZ", "Z")}
    psi_te = {k: c4.compute_statevectors_fast(Xte_ang, k, spec.n_qubits) for k in ("ZZ", "Z")}
    gram = {k: c4.gram_from_statevectors(psi_tr[k]) for k in ("ZZ", "Z")}

    cv_rows, chosen = [], {}
    q = c4.tune_quantum_C(gram["ZZ"], y, GRID_EXT, 5, 42)
    chosen["QSVM_ZZ"] = chosen["QSVM_Z"] = float(q["chosen"]["C"])
    cv_rows += [{"model": "QSVM_ZZ", "C": r["C"], "mean_score": r["mean_score"],
                 "se_score": r["se_score"]} for r in q["rows"]]
    for name in c4.SVM_MODELS:
        chosen[name], rows = svm_tune(name, X_pca, y, GRID_EXT)
        cv_rows += [{"model": name, **r} for r in rows]

    def score(name, C):
        if name in c4.QUANTUM_MODELS:
            k = "ZZ" if name == "QSVM_ZZ" else "Z"
            model = c4.make_quantum_svc(C).fit(gram[k], y)
            pred, _ = rd.quantum_predict_chunked(model, psi_te[k], psi_tr[k])
        else:
            model = c4.make_svm_estimator(name).set_params(svc__C=C).fit(X_pca, y)
            pred = model.predict(Xte_pca)
        return f1_score(y_te, pred, average="macro")

    out = []
    for name in c4.QUANTUM_MODELS + c4.SVM_MODELS:
        c_old = float(hp[name].get("C", hp[name].get("svc__C")))
        f1_refit = score(name, c_old)
        if abs(f1_refit - f1_old[name]) > GATE_TOL:
            raise SystemExit(f"Cong: N={n} run{run_id} {name} C={c_old}: F1 dung lai "
                             f"{f1_refit:.5f} != cache {f1_old[name]:.5f}")
        f1_new = f1_refit if chosen[name] == c_old else score(name, chosen[name])
        out.append({"N": n, "run": run_id, "model": name, "C_old": c_old,
                    "C_ext": chosen[name], "f1_old": f1_old[name], "f1_refit_old": f1_refit,
                    "f1_ext": f1_new})
    for name in c4.TREE_MODELS:
        out.append({"N": n, "run": run_id, "model": name, "C_old": np.nan, "C_ext": np.nan,
                    "f1_old": f1_old[name], "f1_refit_old": f1_old[name],
                    "f1_ext": f1_old[name]})
    for r in cv_rows:
        r.update(N=n, run=run_id)
    return out, cv_rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, nargs="+", default=[5000, 10000])
    ap.add_argument("--runs", type=int, nargs="+", default=list(range(1, 11)))
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    spec = c4.get_spec("nslkdd")
    protocol = c4.load_protocol(ROOT)
    data = c4.load_data(ROOT, verbose=False, dataset="nslkdd")
    per_run, cv = [], []
    for n in args.n:
        for run_id in args.runs:
            t0 = time.time()
            a, b = one_run(data, spec, protocol, n, run_id)
            per_run += a
            cv += b
            # Ghi sau moi run: may tat giua chung van con phan da xong
            pd.DataFrame(per_run).to_csv(OUT / "cgrid_per_run.csv", index=False, encoding="utf-8")
            pd.DataFrame(cv).to_csv(OUT / "cgrid_cv_rows.csv", index=False, encoding="utf-8")
            ch = {r["model"]: (r["C_old"], r["C_ext"]) for r in a if r["model"] in
                  ("QSVM_ZZ", "SVM_Linear", "SVM_RBF")}
            print(f"N={n} run{run_id} {time.time() - t0:.0f}s  C(old->ext) {ch}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
