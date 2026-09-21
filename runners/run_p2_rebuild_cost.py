"""Paper 2 dung lai -- chi phi tinh toan cua tung nhanh.

    python runners/run_p2_rebuild_cost.py

Bai khuyen mot lua chon mo hinh ma khong bao gio noi lua chon do TON BAO
NHIEU. Voi mot kernel luong tu thi do khong phai chi tiet phu: ly do ban da
nop phai cat tap test xuong 100 mau chinh la chi phi Gram. Con so nay quyet
dinh ket luan cua bai co ap dung duoc o quy mo that hay khong.

Do rieng tung pha (huan luyen / suy dien) de nguoi doc biet phan nao dat.
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
from src.reliability import (load_pipeline_artifacts,  # noqa: E402
                             transform_pipeline)

DATA = ROOT / "data" / "nslkdd" / "processed_data"
MODELS = ROOT / "models" / "nslkdd"
OUT = ROOT / "results" / "nslkdd" / "p2_rebuild"
RUN_IDS = list(range(1, 6))       # 5 run la du de uoc thoi gian


def main() -> int:
    sel, pca, scaler, fc = load_pipeline_artifacts(MODELS, DATA)
    te = pd.read_csv(DATA / "NSL_KDD_Test_Cleaned.csv")
    Xte = transform_pipeline(te, fc, sel, pca, scaler)

    rows = []
    for rid in RUN_IDS:
        tr = pd.read_csv(DATA / "multi_run" / f"train_run{rid}.csv")
        Xtr = transform_pipeline(tr, fc, sel, pca, scaler)
        ytr = tr["label_binary"].to_numpy(np.int64)

        # build_models huan luyen tat ca cung luc, nen do lai tung cai rieng.
        for name, proto in build_models(Xtr, ytr).items():
            cls = type(proto)
            t0 = time.perf_counter()
            if name == "QSVM":
                mdl = cls(); mdl.fit(Xtr, ytr)
            else:
                from sklearn.base import clone
                mdl = clone(proto).fit(Xtr, ytr)
            t_fit = time.perf_counter() - t0

            t0 = time.perf_counter()
            mdl.predict(Xte)
            t_pred = time.perf_counter() - t0

            rows.append(dict(run_id=rid, model=name, fit_s=t_fit,
                             predict_s=t_pred, n_train=len(ytr),
                             n_test=len(Xte)))
        print(f"  run{rid}", flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "p2_rebuild_cost.csv", index=False, encoding="utf-8")
    with io.open(OUT / "p2_rebuild_cost_meta.json", "w", encoding="utf-8") as f:
        json.dump({"n_runs": len(RUN_IDS), "n_train": int(df.n_train.iloc[0]),
                   "n_test": int(df.n_test.iloc[0]),
                   "note": "statevector chinh xac, khong phai phan cung that"},
                  f, indent=1)

    print("\n=== Thoi gian (giay), trung binh "
          f"{len(RUN_IDS)} run, N_train={df.n_train.iloc[0]}, "
          f"N_test={df.n_test.iloc[0]} ===")
    print(df.groupby("model")[["fit_s", "predict_s"]].mean()
            .round(3).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
