"""Do them gamma cua SVM-RBF (Paper 1 QMI, viec 5 ngay 21-11).

Vi sao: trong bai, gamma cua RBF de mac dinh scikit-learn (gamma="scale" = 1/d sau
StandardScaler), chi C duoc do. Phan bien co the noi baseline RBF bi yeu di. Script
dung lai dung tap train cua tung run (natural, tuned_per_N, moi N), do (C, gamma) va
cham lai tren test day du.

Luoi: C trong {0.1,...,10} (luoi cua bai), gamma = m/d voi m trong {0.03,0.1,0.3,1,3,10,30}
(m=1 la gia tri mac dinh). Chon theo 1-SE nhu moi SVM trong bai: trong cac cau hinh
con >= best - SE, lay gamma nho nhat (kernel muot nhat), roi C nho nhat. Ghi them
cau hinh co trung binh CV tot nhat de xem do nhay theo luat chon.
5-fold StratifiedKFold(shuffle, random_state=42) nhu c4.tune_estimator.

Cong kiem: fit lai RBF voi C cu va gamma="scale" phai cho lai macro-F1 trong cache
c4_dedup (lech <= 1e-3); khong qua thi dung.

    uv run python runners/run_rbf_gamma.py --dataset nslkdd unsw
    -> results/<ds>/c4_rbf_gamma/rbf_gamma_per_run.csv
    -> results/<ds>/c4_rbf_gamma/rbf_gamma_cv_rows.csv
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.base import clone
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners")]
from src import c4_pipeline as c4  # noqa: E402
import run_dedup_sensitivity as rd  # noqa: E402

C_GRID = [0.1, 0.3, 0.5, 1.0, 3.0, 5.0, 10.0]
GAMMA_MULT = [0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0]
GATE_TOL = 1e-3
CACHE_PREFIX = {"nslkdd": "", "unsw": "UNSW_NB15_"}


def cv_one(est, X, y, folds, C, g):
    s = []
    for tr, va in folds:
        m = clone(est).set_params(svc__C=C, svc__gamma=g).fit(X[tr], y[tr])
        s.append(f1_score(y[va], m.predict(X[va]), average="macro"))
    s = np.asarray(s)
    return s.mean(), s.std(ddof=1) / np.sqrt(len(s))


def one_run(ds, data, spec, protocol, n, run_id, n_jobs):
    cache = ROOT / "results" / ds / "c4_dedup" / "cache"
    meta = json.loads((cache / f"{CACHE_PREFIX[ds]}natural_refit_per_N_tuned_per_N_N{n}"
                       f"_run{run_id}.json").read_text(encoding="utf-8"))
    run_seed, hp = int(meta["run_seed"]), meta["hyperparameters"]
    f1_cache = {m: meta["splits"]["full_test"][m]["f1_macro"] for m in ("QSVM_ZZ", "SVM_RBF")}

    grid_n = rd.resolve_grid(protocol, spec, "natural")
    df_train = c4.build_nested_chain(data, run_id, grid_n, run_seed, "natural")[n]
    if int(c4.rare_mask(df_train, spec).sum()) != int(meta["n_rare_train"]):
        raise SystemExit(f"{ds} N={n} run{run_id}: tap train khong tai hien duoc")
    y = df_train["label_binary"].to_numpy(np.int64)
    fc = data.feature_cols
    rep = c4.make_representation("refit_per_N", select_k=spec.select_k,
                                 n_components=spec.n_qubits)
    rep.fit(df_train, fc)
    _, X = rep.transform(df_train, fc)
    _, Xte = rep.transform(data.df_test_full, fc)
    y_te = data.df_test_full["label_binary"].to_numpy(np.int64)
    est = c4.make_svm_estimator("SVM_RBF")

    def test_f1(C, g):
        m = clone(est).set_params(svc__C=C, svc__gamma=g).fit(X, y)
        return f1_score(y_te, m.predict(Xte), average="macro")

    c_old = float(hp["SVM_RBF"]["svc__C"])
    f1_gate = test_f1(c_old, "scale")
    if abs(f1_gate - f1_cache["SVM_RBF"]) > GATE_TOL:
        raise SystemExit(f"Cong: {ds} N={n} run{run_id} RBF C={c_old}: F1 dung lai "
                         f"{f1_gate:.5f} != cache {f1_cache['SVM_RBF']:.5f}")

    d = X.shape[1]
    folds = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=42).split(X, y))
    combos = list(product(GAMMA_MULT, C_GRID))
    res = Parallel(n_jobs=n_jobs)(delayed(cv_one)(est, X, y, folds, C, m / d)
                                  for m, C in combos)
    rows = [{"gamma_mult": m, "C": C, "mean_score": s, "se_score": se}
            for (m, C), (s, se) in zip(combos, res)]
    best = max(rows, key=lambda r: r["mean_score"])
    elig = [r for r in rows if r["mean_score"] >= best["mean_score"] - best["se_score"]]
    one_se = min(elig, key=lambda r: (r["gamma_mult"], r["C"]))

    out = {"dataset": ds, "N": n, "run": run_id, "d": d, "C_old": c_old,
           "f1_rbf_cache": f1_cache["SVM_RBF"], "f1_rbf_refit_old": f1_gate,
           "f1_qsvm": f1_cache["QSVM_ZZ"]}
    for tag, r in (("1se", one_se), ("best", best)):
        out[f"gamma_mult_{tag}"], out[f"C_{tag}"] = r["gamma_mult"], r["C"]
        out[f"f1_rbf_{tag}"] = test_f1(r["C"], r["gamma_mult"] / d)
    for r in rows:
        r.update(dataset=ds, N=n, run=run_id)
    return out, rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", nargs="+", default=["nslkdd", "unsw"])
    ap.add_argument("--n", type=int, nargs="*", default=None)
    ap.add_argument("--runs", type=int, nargs="+", default=list(range(1, 11)))
    ap.add_argument("--n-jobs", type=int, default=min(6, os.cpu_count() or 1))
    args = ap.parse_args()
    protocol = c4.load_protocol(ROOT)
    for ds in args.dataset:
        out_dir = ROOT / "results" / ds / "c4_rbf_gamma"
        out_dir.mkdir(parents=True, exist_ok=True)
        spec = c4.get_spec(ds)
        data = c4.load_data(ROOT, verbose=False, dataset=ds)
        grid = args.n or rd.resolve_grid(protocol, spec, "natural")
        # Luoi NSL-KDD co N=20000 nhung ban 4 qubit khong chay muc do: bo N khong co cache
        cache = ROOT / "results" / ds / "c4_dedup" / "cache"
        grid = [n for n in grid if (cache / f"{CACHE_PREFIX[ds]}natural_refit_per_N_tuned_per_N"
                                    f"_N{n}_run{args.runs[0]}.json").exists()]
        per_run, cv = [], []
        for n in grid:
            for run_id in args.runs:
                t0 = time.time()
                a, b = one_run(ds, data, spec, protocol, n, run_id, args.n_jobs)
                per_run.append(a)
                cv += b
                # Ghi sau moi run: may tat giua chung van con phan da xong
                pd.DataFrame(per_run).to_csv(out_dir / "rbf_gamma_per_run.csv", index=False,
                                             encoding="utf-8")
                pd.DataFrame(cv).to_csv(out_dir / "rbf_gamma_cv_rows.csv", index=False,
                                        encoding="utf-8")
                print(f"{ds} N={n} run{run_id} {time.time() - t0:.0f}s  "
                      f"1SE m={a['gamma_mult_1se']} C={a['C_1se']}  "
                      f"F1 {a['f1_rbf_refit_old']:.4f}->{a['f1_rbf_1se']:.4f}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
