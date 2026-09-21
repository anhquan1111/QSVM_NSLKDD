"""Paper 2 dung lai -- do tu tin theo TUNG NHOM TAN CONG, va duong tin cay.

    python runners/run_p2_rebuild_percat.py

Hai thu, ca hai deu la cai bai dang thieu.

A. DO TU TIN THEO NHOM.
   Bai da chung minh: tren mot tap con chi co MOT lop thi ECE = 1 - p_tb.
   Vay thi bao cao dung dai luong do, dung ten cua no, theo tung nhom tan
   cong. Voi nhom Normal (lop 0) thi p_tb THAP moi tot; voi cac nhom tan
   cong (lop 1) thi p_tb CAO moi tot. Do la cau tra loi trung thuc cho cau
   hoi ban dau -- "tin duoc tren loai tan cong nao" -- ma khong phai gia vo
   rang no la calibration.

B. DUONG TIN CAY (reliability diagram).
   Bai dinh nghia ECE o cong thuc (1) roi khong bao gio ve ra duong cong ma
   ECE do. Day la hinh tieu chuan cua mot bai calibration.
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

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners"))

from run_p2_rebuild import build_models  # noqa: E402
from src.reliability import (N_BINS_FULL, PlattScaler,  # noqa: E402
                             adaptive_calibration_curve, get_decision_scores,
                             load_pipeline_artifacts, transform_pipeline)

DATA = ROOT / "data" / "nslkdd" / "processed_data"
MODELS = ROOT / "models" / "nslkdd"
OUT = ROOT / "results" / "nslkdd" / "p2_rebuild"
RUN_IDS = list(range(1, 11))
CATEGORIES = ["Normal", "DoS", "Probe", "R2L", "U2R"]


def main() -> int:
    sel, pca, scaler, fc = load_pipeline_artifacts(MODELS, DATA)
    te = pd.read_csv(DATA / "NSL_KDD_Test_Cleaned.csv")
    Xte = transform_pipeline(te, fc, sel, pca, scaler)
    yte = te["label_binary"].to_numpy(np.int64)
    cat = te["attack_category"].to_numpy()

    counts = {c: int((cat == c).sum()) for c in CATEGORIES}
    print("  so ban ghi moi nhom:", counts)

    cat_rows, curve_rows = [], []
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

            # A. do tu tin trung binh tren tung nhom
            for c in CATEGORIES:
                mask = cat == c
                if not mask.any():
                    continue
                cat_rows.append(dict(
                    run_id=rid, model=name, category=c, n=int(mask.sum()),
                    label=int(yte[mask][0]),
                    mean_prob=float(prob[mask].mean()),
                    std_prob=float(prob[mask].std()),
                ))

            # B. duong tin cay tren toan tap test
            conf, acc, size = adaptive_calibration_curve(yte, prob, N_BINS_FULL)
            for b, (cf, ac, sz) in enumerate(zip(conf, acc, size)):
                curve_rows.append(dict(run_id=rid, model=name, bin=b,
                                       conf=float(cf), acc=float(ac),
                                       size=int(sz)))
        print(f"  run{rid:2d}  {time.time() - t0:5.1f}s", flush=True)

    pc = pd.DataFrame(cat_rows)
    cv = pd.DataFrame(curve_rows)
    pc.to_csv(OUT / "p2_rebuild_percat.csv", index=False, encoding="utf-8")
    cv.to_csv(OUT / "p2_rebuild_curve.csv", index=False, encoding="utf-8")
    with io.open(OUT / "p2_rebuild_percat_meta.json", "w", encoding="utf-8") as f:
        json.dump({"categories": CATEGORIES, "counts": counts,
                   "n_runs": len(RUN_IDS), "n_bins": N_BINS_FULL}, f, indent=1)

    print("\n=== Do tu tin trung binh P(tan cong) theo nhom ===")
    print("    (Normal: THAP moi tot; cac nhom tan cong: CAO moi tot)")
    print(pc.pivot_table(index="category", columns="model",
                         values="mean_prob").reindex(CATEGORIES)
            .round(4).to_string())
    print(f"\n  -> {(OUT / 'p2_rebuild_percat.csv').relative_to(ROOT).as_posix()}")
    print(f"  -> {(OUT / 'p2_rebuild_curve.csv').relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
