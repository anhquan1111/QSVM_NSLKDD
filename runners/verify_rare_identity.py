"""Chung minh bang so: tren tap con MOT lop, ECE suy bien thanh 1 - trung binh(p).

    python runners/verify_rare_identity.py

Day la luan diem phuong phap cua bai, nen phai co artifact chu khong phai mot
cau khang dinh.

Lap luan. Tap tan cong hiem gom toan bo cac ban ghi thuoc vai lop tan cong,
nen nhan nhi phan cua chung deu bang 1. Voi binning theo tan suat bang nhau,
moi bin B chi chua ban ghi lop 1, nen acc(B) = 1 theo dinh nghia. Khi do

    ECE = sum_B (|B|/n) |acc(B) - conf(B)|
        = sum_B (|B|/n) (1 - conf(B))
        = 1 - trung binh(p).

Ve phai khong phu thuoc cach chia bin, nen dai luong nay do DO TU TIN tren
tan cong da biet -- gan voi recall -- chu khong do calibration. Tren toan tap
test thi co ca hai lop, acc(B) bien thien, va ECE do calibration that.

Script kiem ca hai ve tren ca hai dataset, moi model, moi run.
"""

from __future__ import annotations

import io
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners"))

from run_p2_rebuild import build_models  # noqa: E402
from src import c4_pipeline as c4  # noqa: E402
from src.reliability import (N_BINS_FULL, N_BINS_RARE,  # noqa: E402
                             RARE_GROUPS, PlattScaler,
                             adaptive_calibration_curve, compute_ece_mce,
                             get_decision_scores, load_pipeline_artifacts,
                             transform_pipeline)

DATA = ROOT / "data" / "nslkdd" / "processed_data"
MODELS = ROOT / "models" / "nslkdd"
OUT = ROOT / "results" / "nslkdd" / "p2_rebuild"
RUN_IDS = list(range(1, 11))
TOL = 1e-12

_checks: list[tuple[bool, str]] = []


def check(ok, label):
    _checks.append((bool(ok), label))
    return ok


def main() -> int:
    sel, pca, scaler, fc = load_pipeline_artifacts(MODELS, DATA)
    te = pd.read_csv(DATA / "NSL_KDD_Test_Cleaned.csv")
    Xte = transform_pipeline(te, fc, sel, pca, scaler)
    yte = te["label_binary"].to_numpy(np.int64)
    rare = np.isin(te["attack_category"].to_numpy(), RARE_GROUPS)

    # 1. Tien de: tap hiem chi co mot lop.
    check(set(np.unique(yte[rare])) == {1},
          f"NSL-KDD: tap hiem chi co lop 1 (thay {sorted(set(yte[rare]))})")
    u = c4.load_data(dataset="unsw", verbose=False).df_test_full
    ru = np.isin(u["attack_category"].to_numpy(),
                 ["Worms", "Shellcode", "Backdoor", "Analysis"])
    yu = u["label_binary"].to_numpy(np.int64)
    check(set(np.unique(yu[ru])) == {1},
          f"UNSW: tap hiem chi co lop 1 (thay {sorted(set(yu[ru]))})")

    rows = []
    for rid in RUN_IDS:
        tr = pd.read_csv(DATA / "multi_run" / f"train_run{rid}.csv")
        Xtr = transform_pipeline(tr, fc, sel, pca, scaler)
        ytr = tr["label_binary"].to_numpy(np.int64)
        for name, mdl in build_models(Xtr, ytr).items():
            s_tr = get_decision_scores(mdl, Xtr)
            s_te = get_decision_scores(mdl, Xte)
            scl, _, _ = PlattScaler().fit(s_tr, ytr)
            prob = scl.predict_proba(s_te)

            ece_r, _ = compute_ece_mce(yte[rare], prob[rare], N_BINS_RARE)
            closed = 1.0 - float(prob[rare].mean())
            dev = abs(ece_r - closed)
            check(dev < TOL, f"run{rid} {name}: ECE_rare == 1-mean(p) "
                             f"(lech {dev:.2e})")

            # 2. Ve doi lap: tren toan tap test, acc(B) PHAI bien thien, va
            #    ECE_full phai KHAC 1-mean(p) -- neu khong thi phep do cung
            #    suy bien va ca bai sup.
            _, accs, _ = adaptive_calibration_curve(yte, prob, N_BINS_FULL)
            ece_f, _ = compute_ece_mce(yte, prob, N_BINS_FULL)
            check(accs.std() > 0.05,
                  f"run{rid} {name}: acc tung bin bien thien tren toan tap test")
            check(abs(ece_f - (1.0 - prob.mean())) > 0.05,
                  f"run{rid} {name}: ECE_full KHONG suy bien")

            rows.append(dict(run_id=rid, model=name, ece_rare=ece_r,
                             one_minus_mean_p=closed, abs_dev=dev,
                             ece_full=ece_f, acc_bin_std=float(accs.std())))

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "p2_rebuild_identity.csv", index=False, encoding="utf-8")
    with io.open(OUT / "p2_rebuild_identity_meta.json", "w", encoding="utf-8") as f:
        json.dump({"max_abs_dev": float(df.abs_dev.max()),
                   "tolerance": TOL, "n_rows": len(df),
                   "min_acc_bin_std_full": float(df.acc_bin_std.min())}, f, indent=1)

    n_ok = sum(1 for ok, _ in _checks if ok)
    for ok, label in _checks:
        if not ok:
            print(f"  LOI   {label}")
    print(f"\n  Lech lon nhat giua ECE_rare va 1-mean(p): {df.abs_dev.max():.2e}")
    print(f"  Do tan cua acc tung bin tren toan tap test, nho nhat: "
          f"{df.acc_bin_std.min():.3f}")
    print(f"\n  verify_rare_identity  {n_ok}/{len(_checks)}")
    return 0 if n_ok == len(_checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
