"""Paper 2 dung lai -- nhanh doi chung 122 dac trung va hai bo hieu chinh khac.

    python runners/run_p2_rebuild_refarm.py

Hai cau hoi, ca hai deu do reviewer se hoi truoc tien.

A. "Cac anh lam que cay roi moi so."
   Tieu de bai co chu *Strong Tabular Learners*, ma cay lai chay tren dung
   bieu dien PCA 4 chieu nhu QSVM. O day RF va XGBoost duoc chay them tren
   DU 122 dac trung one-hot va tren K=20 dac trung da chon, cung 10 run,
   cung tap test, cung giao thuc Platt.

   SIEU THAM SO GIU NGUYEN, chi doi bieu dien. Neu tune lai cho nhanh 122
   chieu thi no duoc mot loi the ma nhanh PCA-4 khong co, va phep so sanh
   khong con co lap duoc anh huong cua rieng bieu dien.

B. "Sao chi thu moi Platt?"
   Ban da nop tu khai day la mot gioi han. O day them isotonic regression va
   temperature scaling, do tren cung 10 run.
"""

from __future__ import annotations

import io
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import (average_precision_score, brier_score_loss,
                             f1_score)

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from run_p2_rebuild import build_models  # noqa: E402
from src.reliability import (N_BINS_FULL, N_BINS_RARE, RANDOM_STATE,  # noqa: E402
                             RARE_GROUPS, PlattScaler, compute_ece_mce,
                             get_decision_scores, load_pipeline_artifacts,
                             make_ml_dl_models, transform_pipeline)

DATA = ROOT / "data" / "nslkdd" / "processed_data"
MODELS = ROOT / "models" / "nslkdd"
OUT = ROOT / "results" / "nslkdd" / "p2_rebuild"
RUN_IDS = list(range(1, 11))
EPS = 1e-6


# ---------------------------------------------------------------------------
# Ba bo hieu chinh, cung mot giao dien: fit tren train, ap cho test.
# ---------------------------------------------------------------------------
def calib_platt(s_tr, y_tr, s_te):
    scl, _, _ = PlattScaler().fit(s_tr, y_tr)
    return scl.predict_proba(s_te)


def calib_isotonic(s_tr, y_tr, s_te):
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    iso.fit(np.asarray(s_tr, float), np.asarray(y_tr, float))
    return np.clip(iso.predict(np.asarray(s_te, float)), EPS, 1 - EPS)


def calib_temperature(s_tr, y_tr, s_te):
    """Mot tham so T > 0, chon bang cach cuc tieu NLL tren train.

    Khac Platt o cho khong co he so chan: chi co mot phep co gian. Do la
    dang duoc dung pho bien cho mang neural, nen dang duoc thu.
    """
    s_tr = np.asarray(s_tr, float)
    y_tr = np.asarray(y_tr, float)

    def nll(log_t):
        p = 1.0 / (1.0 + np.exp(-s_tr / np.exp(log_t)))
        p = np.clip(p, EPS, 1 - EPS)
        return float(-np.mean(y_tr * np.log(p) + (1 - y_tr) * np.log(1 - p)))

    r = minimize_scalar(nll, bounds=(-4.0, 4.0), method="bounded")
    t = float(np.exp(r.x))
    return np.clip(1.0 / (1.0 + np.exp(-np.asarray(s_te, float) / t)), EPS, 1 - EPS), t


CALIBRATORS = {"platt": calib_platt, "isotonic": calib_isotonic,
               "temperature": calib_temperature}


def metrics(y, prob, rare, y_pred=None):
    """Do CA hai truc: xep hang (AUC-PR, F1) va do tin cay (ECE, Brier).

    Can ca hai vi luan diem cua bai la chung TACH ROI nhau -- khong do thi
    khong duoc noi."""
    ece_f, _ = compute_ece_mce(y, prob, N_BINS_FULL)
    ece_r, _ = compute_ece_mce(y[rare], prob[rare], N_BINS_RARE)
    out = dict(ece_full=ece_f, ece_rare=ece_r,
               brier_full=float(brier_score_loss(y, prob)),
               brier_rare=float(brier_score_loss(y[rare], prob[rare])),
               auc_pr=float(average_precision_score(y, prob)))
    if y_pred is not None:
        out["f1"] = float(f1_score(y, y_pred))
    return out


def main() -> int:
    sel, pca, scaler, fc = load_pipeline_artifacts(MODELS, DATA)

    test_df = pd.read_csv(DATA / "NSL_KDD_Test_Cleaned.csv")
    y_te = test_df["label_binary"].to_numpy(np.int64)
    rare = np.isin(test_df["attack_category"].to_numpy(), RARE_GROUPS)
    Xte_pca = transform_pipeline(test_df, fc, sel, pca, scaler)
    Xte_122 = test_df[fc].to_numpy(float)
    print(f"  test: {len(y_te)} mau, {int(rare.sum())} hiem")

    ref_rows, cal_rows = [], []
    for rid in RUN_IDS:
        t0 = time.time()
        tr = pd.read_csv(DATA / "multi_run" / f"train_run{rid}.csv")
        y_tr = tr["label_binary"].to_numpy(np.int64)
        Xtr_pca = transform_pipeline(tr, fc, sel, pca, scaler)
        Xtr_122 = tr[fc].to_numpy(float)

        # ---- A. nhanh doi chung: cung sieu tham so, chi doi bieu dien ----
        k20 = SelectKBest(f_classif, k=20).fit(Xtr_122, y_tr)
        reps = {
            "pca4": (Xtr_pca, Xte_pca),
            "k20": (k20.transform(Xtr_122), k20.transform(Xte_122)),
            "all122": (Xtr_122, Xte_122),
        }
        for rep, (Xa, Xb) in reps.items():
            for name, mdl in make_ml_dl_models(RANDOM_STATE).items():
                if name == "MLP":            # chi hoi ve mo hinh cay
                    continue
                mdl.fit(Xa, y_tr)
                s_tr = get_decision_scores(mdl, Xa)
                s_te = get_decision_scores(mdl, Xb)
                m = metrics(y_te, calib_platt(s_tr, y_tr, s_te), rare,
                            y_pred=mdl.predict(Xb))
                m.update(run_id=rid, model=name, repr=rep,
                         n_features=int(Xa.shape[1]))
                ref_rows.append(m)

        # ---- B. ba bo hieu chinh tren bieu dien PCA-4 chinh --------------
        for name, mdl in build_models(Xtr_pca, y_tr).items():
            s_tr = get_decision_scores(mdl, Xtr_pca)
            s_te = get_decision_scores(mdl, Xte_pca)
            base = metrics(y_te, np.clip(1 / (1 + np.exp(-s_te)), EPS, 1 - EPS), rare)
            base.update(run_id=rid, model=name, calibrator="none", temperature=None)
            cal_rows.append(base)
            for cname, fn in CALIBRATORS.items():
                out = fn(s_tr, y_tr, s_te)
                prob, temp = out if isinstance(out, tuple) else (out, None)
                m = metrics(y_te, prob, rare)
                m.update(run_id=rid, model=name, calibrator=cname, temperature=temp)
                cal_rows.append(m)
        print(f"  run{rid:2d}  {time.time() - t0:5.1f}s", flush=True)

    ref = pd.DataFrame(ref_rows)
    cal = pd.DataFrame(cal_rows)
    ref.to_csv(OUT / "p2_rebuild_refarm.csv", index=False, encoding="utf-8")
    cal.to_csv(OUT / "p2_rebuild_calibrators.csv", index=False, encoding="utf-8")

    print("\n=== A. Cay theo bieu dien (ECE_rare / Brier_rare, 10 run) ===")
    print(ref.pivot_table(index="repr", columns="model",
                          values=["ece_rare", "auc_pr", "f1"]).round(4).to_string())
    print("\n=== B. Bo hieu chinh (ECE tren toan tap test) ===")
    print(cal.pivot_table(index="model", columns="calibrator",
                          values="ece_full").round(4).to_string())

    with io.open(OUT / "p2_rebuild_refarm_meta.json", "w", encoding="utf-8") as f:
        json.dump({"n_runs": len(RUN_IDS),
                   "representations": {k: int(v[0].shape[1]) for k, v in reps.items()},
                   "hyperparameters_held_fixed": True,
                   "calibrators": list(CALIBRATORS)}, f, indent=1)
    print(f"\n  -> {(OUT / 'p2_rebuild_refarm.csv').relative_to(ROOT).as_posix()}")
    print(f"  -> {(OUT / 'p2_rebuild_calibrators.csv').relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
