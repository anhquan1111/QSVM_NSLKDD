"""Paper 2 dung lai -- ba phan tich chieu sau.

    python runners/run_p2_rebuild_depth.py

A. PHAN RA BRIER (Murphy). BS = REL - RES + UNC.
   Bai lap luan rang "xep hang" va "do tin cay" la hai truc TACH ROI. Hien
   tai do la mot khang dinh, chung minh bang cach chi vao hai cot khac nhau.
   Phan ra Murphy bien no thanh mot dang thuc: REL do dung phan sai hieu
   chinh, RES do dung phan phan biet, UNC chi phu thuoc du lieu nen giong
   nhau o moi mo hinh. Mot mo hinh co the tot o RES ma te o REL -- do dung
   la dieu bai noi.

B. NGUONG QUYET DINH. Bai vua tim ra: p trung binh tren R2L va U2R deu duoi
   0.5, nen o nguong mac dinh khong detector nao bao dong tren mot ban ghi
   hiem dien hinh. Cau hoi tiep theo la cau ma nguoi van hanh se hoi: ha
   nguong xuong bao nhieu thi bat duoc, va tra gia bang bao nhieu bao dong
   gia. Day la he qua truc tiep cua phat hien tren, khong phai phan tich roi.

C. HIEU CHINH THEO NHOM. Hien tai truoc/sau chi do tren toan tap. Neu hieu
   chinh hau ky lam tot toan cuc ma lam xau tren nhom hiem thi do la dieu
   phai bao.
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
from sklearn.metrics import f1_score

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners"))

from run_p2_rebuild import build_models  # noqa: E402
from run_p2_rebuild_refarm import CALIBRATORS  # noqa: E402
from src.reliability import (N_BINS_FULL, PlattScaler,  # noqa: E402
                             adaptive_calibration_curve, get_decision_scores,
                             load_pipeline_artifacts, transform_pipeline)

DATA = ROOT / "data" / "nslkdd" / "processed_data"
MODELS = ROOT / "models" / "nslkdd"
OUT = ROOT / "results" / "nslkdd" / "p2_rebuild"
RUN_IDS = list(range(1, 11))
CATEGORIES = ["Normal", "DoS", "Probe", "R2L", "U2R"]
RARE = ["R2L", "U2R"]
THRESHOLDS = np.round(np.arange(0.05, 0.96, 0.05), 2)


def murphy(y, prob, n_bins=N_BINS_FULL):
    """BS = REL - RES + UNC theo phan ra Murphy, tren cung cach chia bin
    tan-suat-bang-nhau ma ECE dung."""
    conf, acc, size = adaptive_calibration_curve(y, prob, n_bins)
    n = len(y)
    base = float(np.mean(y))
    rel = float(np.sum(size / n * (conf - acc) ** 2))
    res = float(np.sum(size / n * (acc - base) ** 2))
    unc = base * (1.0 - base)
    return rel, res, unc


def main() -> int:
    sel, pca, scaler, fc = load_pipeline_artifacts(MODELS, DATA)
    te = pd.read_csv(DATA / "NSL_KDD_Test_Cleaned.csv")
    Xte = transform_pipeline(te, fc, sel, pca, scaler)
    yte = te["label_binary"].to_numpy(np.int64)
    cat = te["attack_category"].to_numpy()

    brier_rows, thr_rows, cal_rows, sat_rows = [], [], [], []
    for rid in RUN_IDS:
        t0 = time.time()
        tr = pd.read_csv(DATA / "multi_run" / f"train_run{rid}.csv")
        Xtr = transform_pipeline(tr, fc, sel, pca, scaler)
        ytr = tr["label_binary"].to_numpy(np.int64)

        for name, mdl in build_models(Xtr, ytr).items():
            s_tr = get_decision_scores(mdl, Xtr)
            s_te = get_decision_scores(mdl, Xte)
            scl, _, _ = PlattScaler().fit(s_tr, ytr)
            prob = scl.predict_proba(s_te)

            # --- A. phan ra Brier -------------------------------------
            rel, res, unc = murphy(yte, prob)
            brier_rows.append(dict(run_id=rid, model=name, reliability=rel,
                                   resolution=res, uncertainty=unc,
                                   brier=rel - res + unc))

            # --- B. quet nguong ---------------------------------------
            for t in THRESHOLDS:
                pred = (prob >= t).astype(np.int64)
                row = dict(run_id=rid, model=name, threshold=float(t),
                           f1_macro=float(f1_score(yte, pred, average="macro")),
                           fpr=float(pred[cat == "Normal"].mean()))
                for c in RARE:
                    row[f"recall_{c}"] = float(pred[cat == c].mean())
                thr_rows.append(row)

            # --- D. do BAO HOA va do TRUNG cua diem so -----------------
            #
            # Co che giai thich ca ba ket qua kia. Mot phep hieu chinh hau ky
            # la anh xa DON DIEU, nen no khong the tach hai diem co cung
            # diem so. Neu mot mo hinh phat ra nhieu gia tri trung nhau va
            # don ve hai dau thi thong tin da mat truoc khi hieu chinh bat
            # dau, va khong bo hieu chinh nao lay lai duoc.
            raw = 1.0 / (1.0 + np.exp(-s_te))
            sat_rows.append(dict(
                run_id=rid, model=name,
                sat_raw=float(((raw < 0.01) | (raw > 0.99)).mean()),
                sat_cal=float(((prob < 0.01) | (prob > 0.99)).mean()),
                distinct_frac=float(len(np.unique(np.round(raw, 9))) / len(raw)),
            ))

            # --- C. hieu chinh theo nhom -------------------------------
            for cname, fn in CALIBRATORS.items():
                out = fn(s_tr, ytr, s_te)
                p2 = out[0] if isinstance(out, tuple) else out
                for c in CATEGORIES:
                    mask = cat == c
                    cal_rows.append(dict(run_id=rid, model=name,
                                         calibrator=cname, category=c,
                                         mean_prob=float(p2[mask].mean())))
        print(f"  run{rid:2d}  {time.time() - t0:5.1f}s", flush=True)

    br = pd.DataFrame(brier_rows)
    th = pd.DataFrame(thr_rows)
    cc = pd.DataFrame(cal_rows)
    sa = pd.DataFrame(sat_rows)
    br.to_csv(OUT / "p2_rebuild_brier_decomp.csv", index=False, encoding="utf-8")
    th.to_csv(OUT / "p2_rebuild_threshold.csv", index=False, encoding="utf-8")
    cc.to_csv(OUT / "p2_rebuild_cal_percat.csv", index=False, encoding="utf-8")
    sa.to_csv(OUT / "p2_rebuild_saturation.csv", index=False, encoding="utf-8")
    with io.open(OUT / "p2_rebuild_depth_meta.json", "w", encoding="utf-8") as f:
        json.dump({"n_runs": len(RUN_IDS), "n_bins": N_BINS_FULL,
                   "thresholds": THRESHOLDS.tolist(),
                   "rare_categories": RARE}, f, indent=1)

    print("\n=== A. Phan ra Brier (REL thap tot, RES cao tot) ===")
    print(br.groupby("model")[["reliability", "resolution", "uncertainty",
                               "brier"]].mean().round(4).to_string())
    print("\n=== B. Nguong toi uu macro-F1, va recall U2R o nguong do ===")
    g = th.groupby(["model", "threshold"]).mean(numeric_only=True)
    for mo in br.model.unique():
        s = g.loc[mo]
        t_best = s.f1_macro.idxmax()
        print(f"  {mo:13s} t*={t_best:.2f}  F1={s.f1_macro.max():.4f}  "
              f"recall(U2R)={s.loc[t_best, 'recall_U2R']:.3f} "
              f"(o 0.50: {s.loc[0.50, 'recall_U2R']:.3f})  "
              f"FPR={s.loc[t_best, 'fpr']:.3f}")
    print("\n=== C. Hieu chinh tren nhom hiem ===")
    print(cc[cc.category.isin(RARE)]
          .pivot_table(index="calibrator", columns="model", values="mean_prob")
          .round(4).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
