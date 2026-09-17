"""Nhanh tham chieu (13/09/2026, Table IV cua bai): baseline cay trong bai (RF, XGBoost) chi nhan 4 thanh phan PCA giong QSVM
(c4_pipeline.Representation: X_pca la dau vao cua nhanh classical). Bai KHONG noi dieu nay, va R1/R2 doc
"XGBoost 0.8503" nhu XGBoost tren du dac trung. Cau hoi thuc dung ("khi nao quantum dang gia") can mot nhanh
tham chieu: cung subset lồng nhau, cung seed, cung tap test, nhung XGBoost/RF tren DU dac trung one-hot (122)
va tren K=20 dac trung da chon. Ket qua ghi results/nslkdd/c4_revision/ref_arm_fullfeat.csv de ghep cap voi QSVM_ZZ cua repo.
"""
import json
import os
import sys
import time
from itertools import product

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..")
sys.path.insert(0, REPO)
os.chdir(REPO)
from src import c4_pipeline as c4  # noqa: E402

OUT = os.path.join(REPO, "results", "nslkdd", "c4_revision")
proto = json.load(open(os.path.join(REPO, "configs", "c4_protocol.json")))
grids = proto["hyperparameter_protocol"]["primary_arm"]["grids"]
cv_folds = proto["hyperparameter_protocol"]["primary_arm"]["cv_folds"]
N_GRID = [100, 200, 500, 1000, 2000, 5000, 10000]
RUNS = list(range(1, 11)); SEEDS = proto["sampling"]["run_seeds"]
FEATSETS = [a for a in sys.argv[1:]] or ["all122", "k20"]

data = c4.load_data(dataset="nslkdd", verbose=False)
fc = data.feature_cols
Xte_all = data.df_test_full[fc].to_numpy(float); yte = data.df_test_full["label_binary"].to_numpy(np.int64)


def tune(est, grid, X, y, seed):
    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42); best = None
    for vals in product(*(grid[k] for k in grid)):
        params = dict(zip(grid, vals)); sc = []
        for tr, va in cv.split(X, y):
            m = clone(est).set_params(**params).fit(X[tr], y[tr]); sc.append(f1_score(y[va], m.predict(X[va]), average="macro"))
        s = float(np.mean(sc))
        if best is None or s > best[0]:
            best = (s, params)
    return best[1]


rows = []
out_csv = os.path.join(OUT, "ref_arm_fullfeat.csv")
done = set()
if os.path.exists(out_csv):
    for r in pd.read_csv(out_csv).itertuples():
        done.add((r.featset, r.model, r.n_train, r.run_id))
for run_id in RUNS:
    seed = SEEDS[run_id - 1]
    chain = c4.build_nested_chain(data, run_id, N_GRID, seed, "natural")
    for n in N_GRID:
        df = chain[n]; y = df["label_binary"].to_numpy(np.int64); Xtr_all = df[fc].to_numpy(float)
        for featset in FEATSETS:
            if featset == "all122":
                Xtr, Xte = Xtr_all, Xte_all
            else:
                sel = SelectKBest(score_func=f_classif, k=min(20, Xtr_all.shape[1])).fit(Xtr_all, y)
                Xtr, Xte = sel.transform(Xtr_all), sel.transform(Xte_all)
            for name, gkey in (("XGBoost", "xgb"), ("RandomForest", "rf")):
                if (featset, name, n, run_id) in done:
                    continue
                t0 = time.time()
                est = c4.make_tree_estimator(name, {}, seed)
                if name == "XGBoost":
                    est.set_params(n_jobs=4)          # chi de tune nhanh; ket qua co the lech +-0.002 so voi n_jobs=1
                params = tune(est, grids[gkey], Xtr, y, seed)
                m = c4.make_tree_estimator(name, params, seed)
                if name == "XGBoost":
                    m.set_params(n_jobs=1)            # fit cuoi: tat dinh nhu repo
                m.fit(Xtr, y); pred = m.predict(Xte)
                row = dict(featset=featset, model=name, n_train=n, run_id=run_id, run_seed=seed,
                           f1_macro=float(f1_score(yte, pred, average="macro")), params=json.dumps(params), secs=round(time.time() - t0, 1))
                rows.append(row); pd.DataFrame([row]).to_csv(out_csv, mode="a", header=not os.path.exists(out_csv), index=False)
                print(f"run{run_id:2d} N={n:5d} {featset:6s} {name:12s} f1={row['f1_macro']:.4f} ({row['secs']}s)", flush=True)
print("done")
