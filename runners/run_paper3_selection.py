"""Hai phep do moi cho bai AICON, dung LAI vat lieu da co tren dia.

    python runners/run_paper3_selection.py

Bai hien co DUNG HAI diem tren tap test (C=0,01 va C=1,0) cong nam diem
cross-validation. Voi hai diem thi "chon C sai lam sup mo hinh" van con la
giai thoai. Script nay bien no thanh phep do, va khong tinh lai kernel
luong tu mot lan nao:

  PHEP DO 1 -- duong cong C day tren TAP TEST.
      Gram luong tu da duoc cache o models/unsw/qsvm_cache/multirun/ (100x100,
      5 run). Chi can SVC(kernel='precomputed').fit tren do voi mot luoi C
      day. Kernel co dien tinh lai tu parquet -- vai mili giay.

  PHEP DO 2 -- ham muc tieu chon mo hinh, DO chu khong phong doan.
      Bai dang khang dinh: "Macro-averaged F1 and balanced accuracy both
      average over classes and therefore assign the constant classifier a
      score near 0.5 ... neither would have selected the degenerate constant
      here." Do la mot cau PHONG DOAN, va no la khuyen nghi chinh cua bai.
      O day ta chay lai dung giao thuc tuning cu (StratifiedKFold 5 fold,
      shuffle, random_state=42, pipeline fit lai trong tung fold) nhung voi
      BA ham muc tieu, roi mang C duoc chon ra danh gia tren tap test.

CONG CU KIEM CHUNG. Truoc khi ghi bat ky so moi nao, script tai lap ba con
so DA CONG BO va dung lai neu lech:
  - diem CV F1 nhi phan cua tung kernel tai 5 gia tri C goc, khop
    models/unsw/c_tuning_results.json;
  - metric tap test tai C da chon, khop results/unsw/c3_results_statevector.json;
  - metric tap test tai C=1,0, khop results/unsw/c3_results_statevector_C1.json.
Khong tai lap duoc thi khong duoc phep viet so moi vao bai.

Ghi ra: results/unsw/paper3/p3_c_curve.csv
        results/unsw/paper3/p3_objective.csv
        results/unsw/paper3/p3_reproduction.json
"""

from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.metrics import (accuracy_score, balanced_accuracy_score,
                             confusion_matrix, f1_score, precision_score,
                             recall_score)
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/unsw/processed_data/multi_run"
CACHE = ROOT / "models/unsw/qsvm_cache/multirun"
OUT = ROOT / "results/unsw/paper3"

# Tat ca hang so duoi day sao y notebooks/unsw/c_tuning_statevector.ipynb va
# notebooks/unsw/c3_kernel_geometry_multirun_statevector.ipynb. Doi mot cai
# la mat tinh tai lap -- _reproduce() se bat duoc.
RANDOM_STATE = 42
RUN_IDS = [1, 2, 3, 4, 5]
K_SELECT = 35
PCA_N = 4
ANGLE_MAX = np.pi
POLY_DEGREE = 2
N_FOLDS = 5
C_GRID_ORIG = [0.01, 0.1, 1.0, 10.0, 100.0]
CONFIG_TAG = "r2_full_k35_p4_cv5_sf1_run1"
TARGET_COL = "label_binary"
# Notebook tuning bo ca 'label'; notebook c3 thi khong. Lay HOP cua hai
# danh sach de khong bao gio cho cot nhan lot vao dac trung.
LABEL_COLS = ["label", "label_binary", "label_multiclass", "attack_category"]
KERNELS = ["quantum", "linear", "poly", "rbf"]

# Luoi C day: 25 diem log-deu tu 1e-3 den 1e2, hop voi nam diem goc de
# duong cong di qua dung cac diem bai da cong bo.
C_DENSE = sorted(set(
    [round(float(c), 10) for c in np.logspace(-3, 2, 21)] + C_GRID_ORIG))

OBJECTIVES = {
    "f1_binary": lambda yt, yp: f1_score(yt, yp, average="binary"),
    "f1_macro": lambda yt, yp: f1_score(yt, yp, average="macro"),
    "balanced_accuracy": balanced_accuracy_score,
}


# ---------------------------------------------------------------- pipeline
def fit_pipeline(X_raw, y):
    sel = SelectKBest(score_func=f_classif, k=K_SELECT).fit(X_raw, y)
    pca = PCA(n_components=PCA_N, random_state=RANDOM_STATE).fit(
        sel.transform(X_raw))
    scaler = MinMaxScaler(feature_range=(0.0, ANGLE_MAX)).fit(
        pca.transform(sel.transform(X_raw)))
    return sel, pca, scaler


def apply_pipeline(pipe, X_raw):
    sel, pca, scaler = pipe
    return scaler.transform(pca.transform(sel.transform(X_raw)))


def classical_gram(name, X_train, X_other):
    """Sao y ham cua notebook c3, ke ca cach tinh gamma='scale'."""
    n_features = X_train.shape[1]
    var_X = X_train.var()
    g = 1.0 / (n_features * var_X) if var_X > 0 else 1.0 / n_features
    if name == "linear":
        return X_other @ X_train.T
    if name == "poly":
        return (g * (X_other @ X_train.T)) ** POLY_DEGREE
    if name == "rbf":
        sq_tr = np.sum(X_train ** 2, axis=1)
        d = (np.sum(X_other ** 2, axis=1)[:, None] + sq_tr[None, :]
             - 2 * (X_other @ X_train.T))
        return np.exp(-g * np.maximum(d, 0))
    raise ValueError(name)


def load_run(run_id):
    tr = pd.read_parquet(DATA / f"train_run{run_id}.parquet")
    te = pd.read_parquet(DATA / f"test_run{run_id}.parquet")
    cols = [c for c in tr.columns if c not in LABEL_COLS]
    return (tr[cols].to_numpy(dtype=np.float64),
            tr[TARGET_COL].to_numpy(dtype=np.int64),
            te[cols].to_numpy(dtype=np.float64),
            te[TARGET_COL].to_numpy(dtype=np.int64))


def quantum_gram(run_id):
    """Doc Gram luong tu DA CACHE. Khong tinh lai mach nao."""
    d = CACHE / f"run_{run_id}"
    tr = np.load(d / f"K_quantum_train_train_{CONFIG_TAG}.npy")
    te = np.load(d / f"K_quantum_test_train_{CONFIG_TAG}.npy")
    return tr, te


def grams_for_run(run_id):
    Xtr_raw, ytr, Xte_raw, yte = load_run(run_id)
    pipe = fit_pipeline(Xtr_raw, ytr)
    Xtr, Xte = apply_pipeline(pipe, Xtr_raw), apply_pipeline(pipe, Xte_raw)
    g = {}
    g["quantum"] = quantum_gram(run_id)
    for k in ("linear", "poly", "rbf"):
        g[k] = (classical_gram(k, Xtr, Xtr), classical_gram(k, Xtr, Xte))
    return g, ytr, yte


def evaluate(K_tr, K_te, ytr, yte, C):
    clf = SVC(kernel="precomputed", C=C, random_state=RANDOM_STATE)
    clf.fit(K_tr, ytr)
    yp = clf.predict(K_te)
    tn, fp, fn, tp = confusion_matrix(yte, yp, labels=[0, 1]).ravel()
    return dict(
        f1=f1_score(yte, yp, average="binary"),
        f1_macro=f1_score(yte, yp, average="macro"),
        balanced_accuracy=balanced_accuracy_score(yte, yp),
        precision=precision_score(yte, yp, average="binary", zero_division=0),
        recall=recall_score(yte, yp, average="binary", zero_division=0),
        accuracy=accuracy_score(yte, yp),
        tn=int(tn), fp=int(fp), fn=int(fn), tp=int(tp),
        degenerate=bool(tn == 0),
    )


# ------------------------------------------------------- cong kiem chung
def _reproduce(grams_by_run, y_by_run):
    """Tai lap ba ket qua DA CONG BO. Lech thi dung han.

    Day la cho duy nhat cho phep script nay viet so moi vao bai: neu
    duong ong o day khong tra ve dung nhung con so da in, thi moi so moi
    no sinh ra deu vo gia tri.
    """
    rep = {}
    ct = json.load(io.open(ROOT / "results/unsw/c_tuning_results.json",
                           encoding="utf-8"))

    # (a) diem CV F1 nhi phan tai nam gia tri C goc, tren train_run1.
    cv = cv_scores(1, ["f1_binary"], C_GRID_ORIG)
    worst = 0.0
    for k in KERNELS:
        for row in ct[k]["scores_per_C"]:
            mine = cv[(k, "f1_binary", round(float(row["C"]), 10))]["mean"]
            worst = max(worst, abs(mine - row["mean"]))
    rep["cv_max_abs_dev"] = worst

    # (b),(c) metric tap test tai C da tune va tai C=1,0.
    for tag, path, c_of in (
            ("tuned", "results/unsw/c3_results_statevector.json",
             lambda k, s: s[k]["C"]),
            ("neutral", "results/unsw/c3_results_statevector_C1.json",
             lambda k, s: 1.0)):
        art = json.load(io.open(ROOT / path, encoding="utf-8"))["summary"]
        dev = 0.0
        for k in KERNELS:
            C = float(c_of(k, art))
            vals = [evaluate(*grams_by_run[r][k], *y_by_run[r], C)
                    for r in RUN_IDS]
            for field in ("f1", "precision", "recall", "accuracy"):
                mine = float(np.mean([v[field] for v in vals]))
                dev = max(dev, abs(mine - art[k][f"{field}_mean"]))
        rep[f"test_{tag}_max_abs_dev"] = dev

    ok = all(v < 1e-9 for v in rep.values())
    rep["reproduced"] = ok
    return rep, ok


# ------------------------------------------------------------ phep do 2
def cv_scores(run_id, objectives, c_grid):
    """Chay lai CV cua buoc tuning, nhung cham diem bang nhieu ham muc tieu.

    Giong notebook o moi cho quan trong: StratifiedKFold(5, shuffle=True,
    random_state=42), pipeline fit LAI trong tung fold. Khac mot cho duy
    nhat, va la khac ve hien thuc chu khong ve toan: kernel cua moi fold
    duoc tinh MOT lan roi dung lai cho ca luoi C, thay vi tinh lai cho tung
    C. SVC(kernel='precomputed') tren cung mot Gram cho ket qua trung khit
    -- do la dieu cong kiem chung (a) xac nhan.
    """
    Xtr_raw, ytr, _, _ = load_run(run_id)
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True,
                          random_state=RANDOM_STATE)
    folds = []
    for tr_idx, va_idx in skf.split(Xtr_raw, ytr):
        pipe = fit_pipeline(Xtr_raw[tr_idx], ytr[tr_idx])
        Xa = apply_pipeline(pipe, Xtr_raw[tr_idx])
        Xb = apply_pipeline(pipe, Xtr_raw[va_idx])
        gk = {}
        for k in KERNELS:
            if k == "quantum":
                gk[k] = (_zz_gram(Xa, Xa), _zz_gram(Xb, Xa))
            else:
                gk[k] = (classical_gram(k, Xa, Xa), classical_gram(k, Xa, Xb))
        folds.append((gk, ytr[tr_idx], ytr[va_idx]))

    out = {}
    for k in KERNELS:
        for C in c_grid:
            preds = []
            for gk, ya, yb in folds:
                clf = SVC(kernel="precomputed", C=C,
                          random_state=RANDOM_STATE)
                clf.fit(gk[k][0], ya)
                preds.append((yb, clf.predict(gk[k][1])))
            for obj in objectives:
                fn = OBJECTIVES[obj]
                sc = np.array([fn(yb, yp) for yb, yp in preds], dtype=float)
                out[(k, obj, round(float(C), 10))] = dict(
                    mean=float(sc.mean()), std=float(sc.std(ddof=1)))
    return out


_FM = None


def _zz_gram(A, B):
    """Kernel luong tu cho cac fold CV -- day la cho DUY NHAT phai tinh mach.

    Gram cache chi co cho cap train/test day du cua tung run, khong co cho
    cac fold ben trong. Voi 4 qubit va 80 diem thi statevector chay het vai
    giay, dung nhu buoc tuning goc da mat 4,9 giay.
    """
    global _FM
    from qiskit.circuit.library import zz_feature_map
    from qiskit_machine_learning.kernels import FidelityStatevectorKernel
    if _FM is None:
        _FM = FidelityStatevectorKernel(
            feature_map=zz_feature_map(feature_dimension=PCA_N, reps=2,
                                       entanglement="full"),
            shots=None, enforce_psd=True, cache_size=None)
    return _FM.evaluate(x_vec=A, y_vec=B) if A is not B else _FM.evaluate(A)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    print("  nap Gram (luong tu: doc cache, co dien: tinh lai) ...")
    grams, ys = {}, {}
    for r in RUN_IDS:
        g, ytr, yte = grams_for_run(r)
        grams[r], ys[r] = g, (ytr, yte)

    print("  cong kiem chung: tai lap ba ket qua da cong bo ...")
    rep, ok = _reproduce(grams, ys)
    for k, v in rep.items():
        print(f"    {k}: {v}")
    if not ok:
        print("\n  DUNG. Khong tai lap duoc so da cong bo, nen khong duoc")
        print("  phep sinh so moi tu duong ong nay.")
        return 1

    # ---- phep do 1: duong cong C day tren tap test -----------------
    print(f"  phep do 1: duong cong C ({len(C_DENSE)} diem x 4 kernel "
          f"x {len(RUN_IDS)} run) ...")
    rows = []
    for r in RUN_IDS:
        for k in KERNELS:
            for C in C_DENSE:
                m = evaluate(*grams[r][k], *ys[r], C)
                rows.append(dict(run=r, kernel=k, C=C, **m))
    curve = pd.DataFrame(rows)
    curve.to_csv(OUT / "p3_c_curve.csv", index=False)
    print(f"    -> {OUT / 'p3_c_curve.csv'}  ({len(curve)} dong)")

    # ---- phep do 2: ham muc tieu chon mo hinh ----------------------
    print("  phep do 2: ba ham muc tieu tren cung luoi C ...")
    cv = cv_scores(1, list(OBJECTIVES), C_DENSE)
    rows = []
    for k in KERNELS:
        for obj in OBJECTIVES:
            grid = [(C, cv[(k, obj, round(float(C), 10))]) for C in C_DENSE]
            # argmax giong buoc tuning goc: max() giu phan tu DAU tien khi
            # hoa, va luoi duyet tu C nho den lon. Chinh quy uoc nay la cai
            # tra ve C=0,01 cho kernel luong tu.
            bestC, best = max(grid, key=lambda t: t[1]["mean"])
            sel = [evaluate(*grams[r][k], *ys[r], bestC) for r in RUN_IDS]
            rows.append(dict(
                kernel=k, objective=obj, selected_C=bestC,
                cv_mean=best["mean"], cv_std=best["std"],
                n_degenerate=int(sum(v["degenerate"] for v in sel)),
                n_runs=len(RUN_IDS),
                test_f1=float(np.mean([v["f1"] for v in sel])),
                test_f1_macro=float(np.mean([v["f1_macro"] for v in sel])),
                test_tn=float(np.mean([v["tn"] for v in sel])),
                test_recall=float(np.mean([v["recall"] for v in sel])),
                test_precision=float(np.mean([v["precision"] for v in sel])),
            ))
    obj_df = pd.DataFrame(rows)
    obj_df.to_csv(OUT / "p3_objective.csv", index=False)
    print(f"    -> {OUT / 'p3_objective.csv'}  ({len(obj_df)} dong)")

    rep["c_grid"] = C_DENSE
    rep["n_runs"] = len(RUN_IDS)
    rep["elapsed_sec"] = time.time() - t0
    json.dump(rep, io.open(OUT / "p3_reproduction.json", "w",
                           encoding="utf-8"), indent=2)
    print(f"    -> {OUT / 'p3_reproduction.json'}")
    print(f"\n  xong trong {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
