"""
BƯỚC 1 — Kiểm chứng calibration: RandomForest / XGBoost / MLP vs QSVM.

Mục tiêu: TRƯỚC KHI viết narrative, xem QSVM có thật sự thắng về độ tin cậy
(ECE/Brier/AUC-PR) trên nhóm tấn công hiếm khi đối thủ là DL/ML hiện đại hay không.

Thiết kế: tái dùng CHÍNH XÁC 5 train run + test cố định của C5 multirun, cùng
pipeline matched-4D và cùng hàm ECE/Platt. Sanity-check: ECE_rare của QSVM tính
lại phải khớp số đã lưu (~0.4503 mean) ⇒ xác nhận methodology trùng khít.

Chạy từ thư mục gốc:  python runners/run_reliability_verify.py
KHÔNG sửa code/notebook cũ.
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Ép stdout sang UTF-8 để in tiếng Việt trên console Windows (cp1252)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from src.reliability import (  # noqa: E402
    RARE_GROUPS,
    RANDOM_STATE,
    load_pipeline_artifacts,
    make_ml_dl_models,
    reliability_metrics,
    transform_pipeline,
)

DATA_DIR = ROOT / "data" / "processed_data"
MODELS_DIR = ROOT / "models"
CACHE_DIR = MODELS_DIR / "qsvm_cache" / "multirun_c5"
RUN_IDS = [1, 2, 3, 4, 5]
TEST_PATH = DATA_DIR / "NSL_KDD_Test_Sample100.csv"
CONFIG_TAG = "mr_c5_r2_full_cq1.0_crbf10.0_cpoly0.1_n1000_t100"
OUT_PATH = DATA_DIR / "p2_verify_calibration.json"


def main():
    print("=" * 78)
    print("BƯỚC 1 — Kiểm chứng calibration RF/XGBoost/MLP vs QSVM (matched-4D)")
    print("=" * 78)

    selector, pca, scaler, feat_cols = load_pipeline_artifacts(MODELS_DIR, DATA_DIR)

    # ── Test cố định ─────────────────────────────────────────────────────────
    test_df = pd.read_csv(TEST_PATH)
    X_test = transform_pipeline(test_df, feat_cols, selector, pca, scaler)
    y_test = test_df["label_binary"].to_numpy(dtype=np.int64)
    group_test = test_df["attack_category"].to_numpy()
    rare_mask = np.isin(group_test, RARE_GROUPS)
    print(f"Test: {X_test.shape} | rare (U2R/R2L) = {int(rare_mask.sum())} mẫu\n")

    per_run = []  # mỗi phần tử: dict {run_id, model, metrics...}

    for rid in RUN_IDS:
        print(f"[run_{rid}] " + "-" * 60)
        train_df = pd.read_csv(DATA_DIR / "multi_run" / f"train_run{rid}.csv")
        X_train = transform_pipeline(train_df, feat_cols, selector, pca, scaler)
        y_train = train_df["label_binary"].to_numpy(dtype=np.int64)

        models = {}

        # 1) Tái dùng QSVM + SVM-RBF đã train trong cache C5
        cache_file = CACHE_DIR / f"run_{rid}" / f"models_{CONFIG_TAG}.joblib"
        if cache_file.exists():
            import joblib

            store = joblib.load(cache_file)
            models["QSVM"] = store["qsvm"]
            models["SVM-RBF"] = store["rbf"]
        else:
            print(f"  [WARN] thiếu cache {cache_file.name} — bỏ QSVM/SVM-RBF run này")

        # 2) Train baseline ML/DL mới trên cùng matched-4D
        for name, mdl in make_ml_dl_models(RANDOM_STATE).items():
            t0 = time.time()
            mdl.fit(X_train, y_train)
            models[name] = mdl
            print(f"  [train] {name:12s} {time.time() - t0:5.1f}s")

        # 3) Tính metric độ tin cậy cho mọi model
        for name, mdl in models.items():
            m = reliability_metrics(mdl, X_train, y_train, X_test, y_test, rare_mask)
            m.update({"run_id": rid, "model": name})
            per_run.append(m)
            print(f"    {name:12s} ECE_rare={m['ece_rare']:.4f} "
                  f"Brier_rare={m['brier_rare']:.4f} AUC-PR={m['auc_pr']:.4f} "
                  f"F1={m['f1']:.4f}")
        print()

    # ── Tổng hợp mean ± std ───────────────────────────────────────────────────
    df = pd.DataFrame(per_run)
    metrics = ["f1", "acc", "ece_full", "ece_rare", "brier_full", "brier_rare",
               "auc_roc", "auc_pr"]
    summary = df.groupby("model")[metrics].agg(["mean", "std"])

    print("=" * 78)
    print("TỔNG HỢP (mean ± std qua 5 run) — sắp theo ECE_rare tăng dần (thấp = tốt)")
    print("=" * 78)
    order = summary[("ece_rare", "mean")].sort_values().index
    hdr = f"{'Model':12s} {'ECE_rare':>16s} {'Brier_rare':>16s} {'AUC-PR':>16s} {'F1':>16s}"
    print(hdr)
    for mdl in order:
        def cell(metric):
            return f"{summary.loc[mdl, (metric, 'mean')]:.4f}±{summary.loc[mdl, (metric, 'std')]:.4f}"
        print(f"{mdl:12s} {cell('ece_rare'):>16s} {cell('brier_rare'):>16s} "
              f"{cell('auc_pr'):>16s} {cell('f1'):>16s}")

    # ── Sanity check vs C5 đã lưu ─────────────────────────────────────────────
    q_ece_rare = summary.loc["QSVM", ("ece_rare", "mean")] if "QSVM" in summary.index else float("nan")
    print("\n[Sanity] QSVM ECE_rare tính lại = "
          f"{q_ece_rare:.4f}  (C5 đã lưu ≈ 0.4503)")

    # ── Lưu JSON ──────────────────────────────────────────────────────────────
    out = {
        "step": "verify_calibration_baselines",
        "config_tag": CONFIG_TAG,
        "rare_groups": RARE_GROUPS,
        "n_test_rare": int(rare_mask.sum()),
        "per_run": per_run,
        "summary": {
            mdl: {metric: {
                "mean": float(summary.loc[mdl, (metric, "mean")]),
                "std": float(summary.loc[mdl, (metric, "std")]),
            } for metric in metrics}
            for mdl in summary.index
        },
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Đã lưu {OUT_PATH}")


if __name__ == "__main__":
    main()
