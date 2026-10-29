"""Cac phep do bo sung cho ban camera-ready AICON 2026, theo y phan bien.

    python runners/run_paper3_camera_ready.py

Ban nop chon C MOT lan tren tap train cua run 1 roi ap cho ca 5 run, chi
voi F1 nhi phan va argmax. Phan bien hoi ba dieu ma ban nop khong do:

  R1.3  chon C dung nam run the nao -- o day chon RIENG trong tung run;
  R4.4  cac cach chua khac: MCC, trong so lop, quy tac 1-SE, pha hoa ve phia
        C lon; R4.3 doi lop duong sang lop thieu so (normal);
  R4.1  do lech theo fold, va lap lai o quy mo lon hon (N = 500);
  R4.2  vi sao kernel luong tu de dinh bay hon -- do THANG DO cua Gram.

Khong tinh lai kernel nao da cache. Kernel luong tu cho cac fold CV va cho
cac run N = 500 thi phai tinh (4 qubit, statevector, vai chuc giay).

CONG KIEM CHUNG (dung han neu truot):
  (a) bo lay mau chep tu notebooks/unsw/preprocess.ipynb dung lai DUNG 10
      file train_run/test_run N = 100 dang dung;
  (b) Gram luong tu tinh moi cho run 1 khop Gram da cache;
  (c) diem CV F1 nhi phan tren run 1, luoi goc, khop c_tuning_results.json.

Ghi ra: results/unsw/paper3/p3cr_selection.csv
        results/unsw/paper3/p3cr_kernel_scale.csv
        results/unsw/paper3/p3cr_gates.json
        data/unsw/processed_data/multi_run_n500/{train,test}_run{1..5}.parquet
"""

from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (balanced_accuracy_score, f1_score,
                             matthews_corrcoef)
from sklearn.model_selection import StratifiedKFold
from sklearn.svm import SVC

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_paper3_selection as base  # noqa: E402

ROOT = base.ROOT
OUT = base.OUT
PROCESSED = ROOT / "data/unsw/processed_data"
N500_DIR = PROCESSED / "multi_run_n500"

RARE_CATEGORIES = ("Analysis", "Backdoor", "Shellcode", "Worms")
N_RUNS = 5
SIZES = [100, 500]

# Lop tan cong (1) la lop DUONG trong ban nop. "f1_normal" dao lai: lop
# normal -- lop thieu so -- la lop duong (R4.3). Bo doan-tat-ca-tan-cong
# khi do co F1 = 0.
OBJECTIVES = {
    "f1_binary": lambda yt, yp: f1_score(yt, yp, average="binary",
                                         zero_division=0),
    "f1_normal": lambda yt, yp: f1_score(yt, yp, pos_label=0,
                                         average="binary", zero_division=0),
    "mcc": matthews_corrcoef,
    "f1_macro": lambda yt, yp: f1_score(yt, yp, average="macro",
                                        zero_division=0),
    "balanced_accuracy": balanced_accuracy_score,
}
GRIDS = {"original": base.C_GRID_ORIG, "dense": base.C_DENSE}
# Ba quy tac chon tren cung mot bang diem CV:
#   first -- argmax, hoa thi lay C NHO nhat (dung nhu ban nop);
#   last  -- argmax, hoa thi lay C LON nhat (pha hoa nguoc chieu);
#   1se   -- C nho nhat co diem >= max - 1 SE (quy tac 1-SE, chuong 7 cua
#            Hastie et al.; giao thuc revision cua Paper 1 dung no).
RULES = ("first", "last", "1se")
CLASS_WEIGHTS = (None, "balanced")


# ------------------------------------------------------------ lay mau
# Chep NGUYEN VAN tu notebooks/unsw/preprocess.ipynb (chi bo print). Cong
# (a) chung minh ban chep cho lai dung cac file N = 100 dang dung.
def stratified_sample_for_qsvm(df, n_samples=1000, min_rare=30,
                               rare_categories=RARE_CATEGORIES,
                               random_state=42):
    rng = np.random.RandomState(random_state)
    sampled = []
    rare_cats = [c for c in rare_categories
                 if c in df["attack_category"].unique()]
    other_cats = [c for c in df["attack_category"].unique()
                  if c not in rare_cats]

    rare_budget = 0
    for cat in rare_cats:
        pool = df[df["attack_category"] == cat]
        n_take = min(min_rare, len(pool)) if len(pool) >= min_rare else min_rare
        replace = len(pool) < n_take
        idx = pool.sample(n=n_take, replace=replace,
                          random_state=rng.randint(1_000_000))
        sampled.append(idx)
        rare_budget += n_take

    remaining = max(0, n_samples - rare_budget)
    other_total = df[df["attack_category"].isin(other_cats)].shape[0]

    if other_total > 0 and remaining > 0:
        allocations = []
        for cat in other_cats:
            pool = df[df["attack_category"] == cat]
            weight = len(pool) / other_total
            exact = remaining * weight
            floor_n = max(1, int(exact))
            remainder = exact - int(exact)
            allocations.append([cat, pool, floor_n, remainder])

        current_total = sum(a[2] for a in allocations)
        deficit = remaining - current_total
        if deficit > 0:
            allocations.sort(key=lambda x: x[3], reverse=True)
            for k in range(deficit):
                allocations[k % len(allocations)][2] += 1
        elif deficit < 0:
            allocations.sort(key=lambda x: x[3])
            need_remove = -deficit
            guard = 0
            while need_remove > 0 and guard < len(allocations) * 100:
                idx = guard % len(allocations)
                if allocations[idx][2] > 1:
                    allocations[idx][2] -= 1
                    need_remove -= 1
                guard += 1

        for cat, pool, n_take, _ in allocations:
            n_take = min(n_take, len(pool))
            idx = pool.sample(n=n_take, random_state=rng.randint(1_000_000))
            sampled.append(idx)

    result = pd.concat(sampled).sample(frac=1, random_state=random_state)
    return result.reset_index(drop=True)


def make_disjoint_runs(df, n_runs, run_size, min_rare, base_seed):
    df_shuffled = df.sample(frac=1, random_state=base_seed).reset_index(drop=True)
    part_size = len(df_shuffled) // n_runs
    runs = []
    for i in range(n_runs):
        start = i * part_size
        end = (i + 1) * part_size if i < n_runs - 1 else len(df_shuffled)
        runs.append(stratified_sample_for_qsvm(
            df_shuffled.iloc[start:end].copy(), n_samples=run_size,
            min_rare=min_rare, random_state=base_seed + i))
    return runs


def build_runs(size):
    """Dung 5 cap run rieng re, cung seed va cung luat voi notebook goc."""
    tr_all = pd.read_parquet(PROCESSED / "UNSW_Train_Cleaned.parquet")
    te_all = pd.read_parquet(PROCESSED / "UNSW_Test_Cleaned.parquet")
    min_rare = max(5, size // 20)
    return (make_disjoint_runs(tr_all, N_RUNS, size, min_rare, 100),
            make_disjoint_runs(te_all, N_RUNS, size, min_rare, 200))


def gate_sampler():
    """Cong (a): ban chep phai cho lai DUNG 10 file N = 100 dang dung."""
    trs, tes = build_runs(100)
    worst = 0.0
    for i in range(N_RUNS):
        for got, name in ((trs[i], "train"), (tes[i], "test")):
            ref = pd.read_parquet(base.DATA / f"{name}_run{i + 1}.parquet")
            if list(got.columns) != list(ref.columns) or got.shape != ref.shape:
                return False, float("inf")
            num = ref.select_dtypes("number").columns
            worst = max(worst, float(np.max(np.abs(
                got[num].to_numpy(float) - ref[num].to_numpy(float)))))
            if not got.drop(columns=num).equals(ref.drop(columns=num)):
                return False, float("inf")
    return worst == 0.0, worst


def write_n500():
    trs, tes = build_runs(500)
    N500_DIR.mkdir(parents=True, exist_ok=True)
    for i in range(N_RUNS):
        trs[i].to_parquet(N500_DIR / f"train_run{i + 1}.parquet", index=False)
        tes[i].to_parquet(N500_DIR / f"test_run{i + 1}.parquet", index=False)


def load_split(size, run_id):
    d = base.DATA if size == 100 else N500_DIR
    tr = pd.read_parquet(d / f"train_run{run_id}.parquet")
    te = pd.read_parquet(d / f"test_run{run_id}.parquet")
    cols = [c for c in tr.columns if c not in base.LABEL_COLS]
    return (tr[cols].to_numpy(np.float64), tr[base.TARGET_COL].to_numpy(np.int64),
            te[cols].to_numpy(np.float64), te[base.TARGET_COL].to_numpy(np.int64))


# ------------------------------------------------------------ kernel
def all_grams(Xa, Xb):
    """Gram (train, train) va (other, train) cho ca bon kernel."""
    g = {"quantum": (base._zz_gram(Xa, Xa), base._zz_gram(Xb, Xa))}
    for k in ("linear", "poly", "rbf"):
        g[k] = (base.classical_gram(k, Xa, Xa), base.classical_gram(k, Xa, Xb))
    return g


def fit_predict(K_tr, K_te, y, C, cw):
    clf = SVC(kernel="precomputed", C=C, class_weight=cw,
              random_state=base.RANDOM_STATE)
    clf.fit(K_tr, y)
    return clf.predict(K_te)


# ------------------------------------------------------------ mot run
def analyse_run(size, run_id):
    Xtr_raw, ytr, Xte_raw, yte = load_split(size, run_id)

    # Pipeline fit LAI trong tung fold CV, roi fit tren ca tap train cho
    # tap test -- dung nhu buoc tuning goc (R1.4).
    skf = StratifiedKFold(n_splits=base.N_FOLDS, shuffle=True,
                          random_state=base.RANDOM_STATE)
    folds = []
    for a, b in skf.split(Xtr_raw, ytr):
        pipe = base.fit_pipeline(Xtr_raw[a], ytr[a])
        folds.append((all_grams(base.apply_pipeline(pipe, Xtr_raw[a]),
                                base.apply_pipeline(pipe, Xtr_raw[b])),
                      ytr[a], ytr[b]))
    pipe = base.fit_pipeline(Xtr_raw, ytr)
    full = all_grams(base.apply_pipeline(pipe, Xtr_raw),
                     base.apply_pipeline(pipe, Xte_raw))

    scale_rows = []
    for k in base.KERNELS:
        K = full[k][0]
        off = K[~np.eye(len(K), dtype=bool)]
        scale_rows.append(dict(
            n=size, run=run_id, kernel=k, diag_mean=float(np.diag(K).mean()),
            offdiag_mean=float(off.mean()), offdiag_std=float(off.std()),
            # Do "phang" cua Gram: off-diagonal chia duong cheo. Gan 1 la
            # moi diem trong giong nhau; gan 0 la Gram gan voi ma tran don vi
            # (kernel concentration theo nghia Thanasilp et al.).
            offdiag_over_diag=float(off.mean() / np.diag(K).mean()),
            train_attack_ratio=float(ytr.mean()),
            test_attack_ratio=float(yte.mean())))

    rows = []
    c_all = base.C_DENSE
    for k in base.KERNELS:
        for cw in CLASS_WEIGHTS:
            # Diem CV cua moi (C, ham muc tieu), cong co bao nhieu fold sup.
            cv = {}
            for C in c_all:
                preds = [(yb, fit_predict(g[k][0], g[k][1], ya, C, cw))
                         for g, ya, yb in folds]
                ndeg = sum(int(np.all(yp == 1)) for _, yp in preds)
                for obj, fn in OBJECTIVES.items():
                    sc = np.array([fn(yb, yp) for yb, yp in preds], float)
                    cv[(obj, C)] = (sc.mean(), sc.std(ddof=1), ndeg)
            test_cache = {}
            for obj, fn in OBJECTIVES.items():
                # Diem cua bo doan-tat-ca-tan-cong tren cung cac fold.
                base_sc = float(np.mean([fn(yb, np.ones_like(yb))
                                         for _, _, yb in folds]))
                for gname, grid in GRIDS.items():
                    tab = [(C, *cv[(obj, round(float(C), 10))]) for C in grid]
                    best = max(t[1] for t in tab)
                    nondeg = [t[1] for t in tab if t[3] == 0]
                    for rule in RULES:
                        if rule == "first":
                            pick = next(t for t in tab if t[1] == best)
                        elif rule == "last":
                            pick = [t for t in tab if t[1] == best][-1]
                        else:
                            se = next(t for t in tab if t[1] == best)[2] / np.sqrt(
                                base.N_FOLDS)
                            pick = next(t for t in tab if t[1] >= best - se)
                        C = pick[0]
                        if (C, cw) not in test_cache:
                            yp = fit_predict(full[k][0], full[k][1], ytr, C, cw)
                            test_cache[(C, cw)] = dict(
                                test_degenerate=bool(np.all(yp == 1)),
                                test_f1=f1_score(yte, yp, zero_division=0),
                                test_f1_macro=f1_score(yte, yp, average="macro",
                                                       zero_division=0),
                                test_mcc=matthews_corrcoef(yte, yp),
                                test_tn=int(np.sum((yp == 0) & (yte == 0))),
                                test_fn=int(np.sum((yp == 0) & (yte == 1))))
                        rows.append(dict(
                            n=size, run=run_id, kernel=k,
                            class_weight=cw or "none", objective=obj,
                            grid=gname, rule=rule, selected_C=C,
                            cv_mean=pick[1], cv_std=pick[2],
                            cv_folds_degenerate=pick[3],
                            cv_constant_baseline=base_sc,
                            cv_best_nondeg=max(nondeg) if nondeg else np.nan,
                            **test_cache[(C, cw)]))
    return rows, scale_rows


# ------------------------------------------------------------ cong (b), (c)
def gate_cache_and_cv():
    Xtr_raw, ytr, Xte_raw, yte = load_split(100, 1)
    pipe = base.fit_pipeline(Xtr_raw, ytr)
    Ktr = base._zz_gram(base.apply_pipeline(pipe, Xtr_raw),
                        base.apply_pipeline(pipe, Xtr_raw))
    Kc, _ = base.quantum_gram(1)
    dev_gram = float(np.max(np.abs(Ktr - Kc)))
    ct = json.load(io.open(ROOT / "results/unsw/c_tuning_results.json",
                           encoding="utf-8"))
    cv = base.cv_scores(1, ["f1_binary"], base.C_GRID_ORIG)
    dev_cv = max(abs(cv[(k, "f1_binary", round(float(r["C"]), 10))]["mean"]
                     - r["mean"]) for k in base.KERNELS
                 for r in ct[k]["scores_per_C"])
    return dev_gram, dev_cv


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    gates = {}

    print("  cong (a): bo lay mau chep tu notebook ...")
    ok_a, dev_a = gate_sampler()
    gates["sampler_reproduces_n100"] = ok_a
    gates["sampler_max_abs_dev"] = dev_a
    print("  cong (b), (c): Gram cache va diem CV goc ...")
    dev_b, dev_c = gate_cache_and_cv()
    gates["quantum_gram_max_abs_dev"] = dev_b
    gates["cv_f1_max_abs_dev"] = dev_c
    ok = ok_a and dev_b < 1e-9 and dev_c < 1e-12
    gates["passed"] = ok
    print("   ", gates)
    if not ok:
        print("\n  DUNG. Khong tai lap duoc vat lieu goc, khong sinh so moi.")
        return 1

    if not (N500_DIR / f"test_run{N_RUNS}.parquet").exists():
        print("  dung 5 cap run N = 500 ...")
        write_n500()

    rows, scale = [], []
    for size in SIZES:
        for r in range(1, N_RUNS + 1):
            t = time.time()
            a, b = analyse_run(size, r)
            rows += a
            scale += b
            print(f"    N={size} run {r}: {time.time() - t:.1f}s")

    pd.DataFrame(rows).to_csv(OUT / "p3cr_selection.csv", index=False)
    pd.DataFrame(scale).to_csv(OUT / "p3cr_kernel_scale.csv", index=False)
    gates["elapsed_sec"] = time.time() - t0
    json.dump(gates, io.open(OUT / "p3cr_gates.json", "w", encoding="utf-8"),
              indent=2)
    print(f"  -> {OUT / 'p3cr_selection.csv'} ({len(rows)} dong)")
    print(f"  xong trong {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
