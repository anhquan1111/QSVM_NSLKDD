"""
A2 — Temporal Reliability: calibration dưới temporal shift (KDDTest-21).

Train trên 5 run (train_run1..5, tái dùng QSVM/SVM cache C5), test trên tập
KHÓ KDDTest-21 — mô phỏng dữ liệu trôi dạt theo thời gian. Đo ECE/Brier/AUC-PR
(full + rare). KHÔNG sửa code cũ; cache QSVM cũ chỉ đọc.

Chạy: python runners/run_reliability_temporal.py
"""
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from src.reliability import (  # noqa: E402
    RANDOM_STATE,
    RARE_GROUPS,
    load_pipeline_artifacts,
    make_ml_dl_models,
    reliability_metrics,
    transform_pipeline,
)

DATA_DIR = ROOT / "data" / "processed_data"
MODELS_DIR = ROOT / "models"
C5_CACHE = MODELS_DIR / "qsvm_cache" / "multirun_c5"
RUN_IDS = [1, 2, 3, 4, 5]
CONFIG_TAG = "mr_c5_r2_full_cq1.0_crbf10.0_cpoly0.1_n1000_t100"
TEST_PATH = DATA_DIR / "NSL_KDD_Test21_Cleaned.csv"
# Subsample test cho QSVM eval nhanh, giữ phân bố lớp (đủ rare U2R/R2L)
TEST_SUBSAMPLE = 2000
OUT = DATA_DIR / "p2_temporal.json"


def main():
    print("=" * 74)
    print("A2 — TEMPORAL RELIABILITY (KDDTest-21, temporal shift)")
    print("=" * 74)
    art_full = load_pipeline_artifacts(MODELS_DIR, DATA_DIR)
    feat_cols = art_full[3]
    art = art_full[:3]

    test_df = pd.read_csv(TEST_PATH)
    # Stratified subsample theo attack_category để eval QSVM nhẹ mà vẫn đủ rare
    if len(test_df) > TEST_SUBSAMPLE:
        test_df = (test_df.groupby("attack_category", group_keys=False)
                   .apply(lambda g: g.sample(min(len(g),
                          max(1, int(round(TEST_SUBSAMPLE * len(g) / len(test_df))))),
                          random_state=RANDOM_STATE)))
    X_test = transform_pipeline(test_df, feat_cols, *art)
    y_test = test_df["label_binary"].to_numpy(dtype=np.int64)
    grp = test_df["attack_category"].to_numpy()
    rare_mask = np.isin(grp, RARE_GROUPS)
    print(f"Test (subsample): {X_test.shape} | rare U2R/R2L = {int(rare_mask.sum())}\n")

    per_run = []
    for rid in RUN_IDS:
        train_df = pd.read_csv(DATA_DIR / "multi_run" / f"train_run{rid}.csv")
        X_train = transform_pipeline(train_df, feat_cols, *art)
        y_train = train_df["label_binary"].to_numpy(dtype=np.int64)

        store = joblib.load(C5_CACHE / f"run_{rid}" / f"models_{CONFIG_TAG}.joblib")
        models = {"QSVM": store["qsvm"], "SVM-RBF": store["rbf"]}
        for name, mdl in make_ml_dl_models(RANDOM_STATE).items():
            mdl.fit(X_train, y_train)
            models[name] = mdl

        t0 = time.time()
        for name, mdl in models.items():
            m = reliability_metrics(mdl, X_train, y_train, X_test, y_test, rare_mask)
            m.update({"run_id": rid, "model": name})
            per_run.append(m)
        print(f"  [run_{rid}] xong ({time.time()-t0:.1f}s)")

    df = pd.DataFrame(per_run)
    metrics = ["ece_full", "brier_full", "ece_rare", "brier_rare", "auc_pr", "f1"]
    summary = df.groupby("model")[metrics].agg(["mean", "std"])
    print("\nTemporal (KDDTest-21) — mean±std, sắp theo ECE_full:")
    order = summary[("ece_full", "mean")].sort_values().index
    print(f"{'Model':13s} {'ECE_full':>14s} {'Brier_full':>14s} {'ECE_rare':>14s} {'AUC-PR':>14s}")
    for mdl in order:
        def c(k):
            return f"{summary.loc[mdl,(k,'mean')]:.4f}±{summary.loc[mdl,(k,'std')]:.3f}"
        print(f"{mdl:13s} {c('ece_full'):>14s} {c('brier_full'):>14s} {c('ece_rare'):>14s} {c('auc_pr'):>14s}")

    out = {"step": "temporal_reliability", "test": "KDDTest-21",
           "n_test": int(len(y_test)), "n_rare": int(rare_mask.sum()),
           "per_run": per_run,
           "summary": {mdl: {k: {"mean": float(summary.loc[mdl, (k, "mean")]),
                                 "std": float(summary.loc[mdl, (k, "std")])}
                             for k in metrics} for mdl in summary.index}}
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"\n[OK] → {OUT}")


if __name__ == "__main__":
    main()
