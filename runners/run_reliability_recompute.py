"""
Phase 2 (C3 / A1 / C4) — Recompute QSVM + baseline trên các split CALIBRATION
mà JSON cũ không có (prior-shift, low-data) + phân tích Platt before/after.

Nguyên tắc an toàn:
  - KHÔNG sửa code/notebook cũ.
  - KHÔNG ghi đè cache cũ: model QSVM low-data lưu vào thư mục MỚI
    `models/qsvm_cache/p2_lowdata/`. Prior-shift TÁI DÙNG cache C5 (chỉ đọc).

Ba phần:
  C3  Prior-shift reliability  — tái dùng QSVM/SVM đã train (train_run1..5),
                                 đánh giá trên E3a/E3b/E3c. RF/XGB/MLP train mới.
  A1  Low-data reliability     — train MỚI mọi model trên Sample{100,200,500,1000},
                                 test cố định Sample300 → ECE/Brier/AUC-PR theo N.
  C4  Platt before/after       — trên 5 run C5, so ECE trước/sau Platt scaling.

Chạy: python runners/run_reliability_recompute.py
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
    ANGLE_MAX,
    N_BINS_FULL,
    RANDOM_STATE,
    RARE_GROUPS,
    PlattScaler,
    compute_ece_mce,
    get_decision_scores,
    load_pipeline_artifacts,
    make_ml_dl_models,
    reliability_metrics,
    transform_pipeline,
)

DATA_DIR = ROOT / "data" / "processed_data"
MODELS_DIR = ROOT / "models"
C5_CACHE = MODELS_DIR / "qsvm_cache" / "multirun_c5"
P2_LOWDATA_CACHE = MODELS_DIR / "qsvm_cache" / "p2_lowdata"  # THƯ MỤC MỚI
P2_LOWDATA_CACHE.mkdir(parents=True, exist_ok=True)

RUN_IDS = [1, 2, 3, 4, 5]
CONFIG_TAG = "mr_c5_r2_full_cq1.0_crbf10.0_cpoly0.1_n1000_t100"
C_QSVM = 1.0


def build_qsvc():
    """Tạo QSVC ZZFeatureMap(4 qubit, reps=2, full) — giống hệt cấu hình C5."""
    from qiskit.circuit.library import zz_feature_map
    from qiskit_machine_learning.algorithms import QSVC
    from qiskit_machine_learning.kernels import FidelityStatevectorKernel

    fm = zz_feature_map(feature_dimension=4, reps=2, entanglement="full")
    kernel = FidelityStatevectorKernel(feature_map=fm, shots=None, enforce_psd=True, cache_size=None)
    return QSVC(quantum_kernel=kernel, C=C_QSVM, random_state=RANDOM_STATE)


def load_xy(path, feat_cols, art):
    df = pd.read_csv(path)
    X = transform_pipeline(df, feat_cols, *art)
    y = df["label_binary"].to_numpy(dtype=np.int64)
    grp = df["attack_category"].to_numpy()
    return X, y, grp


# ════════════════════════════════════════════════════════════════════════════
# C3 — Prior-shift reliability (tái dùng QSVM/SVM cache; train mới RF/XGB/MLP)
# ════════════════════════════════════════════════════════════════════════════

def run_prior_shift(feat_cols, art):
    print("\n" + "=" * 78)
    print("C3 — PRIOR-SHIFT RELIABILITY (Balanced / Attack-heavy / DoS-only)")
    print("=" * 78)
    mixes = {
        "Balanced_50/50": "NSL_KDD_Test_C4_E3a_Balanced_Sample300.csv",
        "AttackHeavy_30/70": "NSL_KDD_Test_C4_E3b_AttackHeavy_Sample300.csv",
        "DoS_only": "NSL_KDD_Test_C4_E3c_DoSOnly_Sample300.csv",
    }
    per_run = []
    for rid in RUN_IDS:
        train_df = pd.read_csv(DATA_DIR / "multi_run" / f"train_run{rid}.csv")
        X_train = transform_pipeline(train_df, feat_cols, *art)
        y_train = train_df["label_binary"].to_numpy(dtype=np.int64)

        # Tái dùng QSVM + SVM-RBF từ cache C5 (chỉ đọc)
        store = joblib.load(C5_CACHE / f"run_{rid}" / f"models_{CONFIG_TAG}.joblib")
        models = {"QSVM": store["qsvm"], "SVM-RBF": store["rbf"]}
        # Train mới ML/DL trên cùng train_run
        for name, mdl in make_ml_dl_models(RANDOM_STATE).items():
            mdl.fit(X_train, y_train)
            models[name] = mdl

        for mix_name, fname in mixes.items():
            X_test, y_test, grp = load_xy(DATA_DIR / fname, feat_cols, art)
            rare_mask = np.isin(grp, RARE_GROUPS)
            for name, mdl in models.items():
                m = reliability_metrics(mdl, X_train, y_train, X_test, y_test, rare_mask)
                m.update({"run_id": rid, "model": name, "mix": mix_name})
                per_run.append(m)
        print(f"  [run_{rid}] xong 3 mix")

    df = pd.DataFrame(per_run)
    print("\nECE_full (mean±std) theo mix — thấp = đáng tin hơn:")
    piv = df.groupby(["mix", "model"])["ece_full"].agg(["mean", "std"])
    for mix in mixes:
        print(f"  -- {mix} --")
        sub = piv.loc[mix].sort_values("mean")
        for mdl, row in sub.iterrows():
            print(f"     {mdl:12s} {row['mean']:.4f} ± {row['std']:.4f}")
    out = DATA_DIR / "p2_priorshift.json"
    json.dump({"per_run": per_run}, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"[OK] → {out}")


# ════════════════════════════════════════════════════════════════════════════
# A1 — Low-data reliability (train MỚI mọi model; test cố định Sample300)
# ════════════════════════════════════════════════════════════════════════════

def run_low_data(feat_cols, art):
    print("\n" + "=" * 78)
    print("A1 — LOW-DATA RELIABILITY: ECE/Brier/AUC-PR theo train size N")
    print("=" * 78)
    train_sizes = {100: "NSL_KDD_Train_Sample100.csv",
                   200: "NSL_KDD_Train_Sample200.csv",
                   500: "NSL_KDD_Train_Sample500.csv",
                   1000: "NSL_KDD_Train_Sample1000.csv"}
    X_test, y_test, grp = load_xy(DATA_DIR / "NSL_KDD_Test_Sample300.csv", feat_cols, art)
    rare_mask = np.isin(grp, RARE_GROUPS)
    print(f"Test cố định: {X_test.shape} | rare = {int(rare_mask.sum())}\n")

    rows = []
    for N, fname in train_sizes.items():
        X_train, y_train, _ = load_xy(DATA_DIR / fname, feat_cols, art)

        # QSVM: train mới + cache vào thư mục MỚI
        qpath = P2_LOWDATA_CACHE / f"qsvm_N{N}.joblib"
        if qpath.exists():
            qsvm = joblib.load(qpath)
        else:
            t0 = time.time()
            qsvm = build_qsvc()
            qsvm.fit(X_train, y_train)
            joblib.dump(qsvm, qpath)
            print(f"  [QSVM N={N}] train {time.time()-t0:.1f}s")
        models = {"QSVM": qsvm}
        for name, mdl in make_ml_dl_models(RANDOM_STATE).items():
            mdl.fit(X_train, y_train)
            models[name] = mdl

        for name, mdl in models.items():
            m = reliability_metrics(mdl, X_train, y_train, X_test, y_test, rare_mask)
            m.update({"N": N, "model": name})
            rows.append(m)
        q = [r for r in rows if r["N"] == N and r["model"] == "QSVM"][0]
        print(f"  N={N:5d} | QSVM ECE_full={q['ece_full']:.4f} "
              f"Brier_full={q['brier_full']:.4f} AUC-PR={q['auc_pr']:.4f}")

    df = pd.DataFrame(rows)
    print("\nECE_full theo N (thấp = tốt):")
    print(df.pivot(index="N", columns="model", values="ece_full").round(4).to_string())
    out = DATA_DIR / "p2_lowdata.json"
    json.dump({"rows": rows}, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"[OK] → {out}")


# ════════════════════════════════════════════════════════════════════════════
# C4 — Platt scaling before/after (trên 5 run C5)
# ════════════════════════════════════════════════════════════════════════════

def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))


def run_platt_before_after(feat_cols, art):
    print("\n" + "=" * 78)
    print("C4 — PLATT SCALING: ECE before vs after (5 run C5)")
    print("=" * 78)
    X_test, y_test, grp = load_xy(DATA_DIR / "NSL_KDD_Test_Sample100.csv", feat_cols, art)
    rows = []
    for rid in RUN_IDS:
        train_df = pd.read_csv(DATA_DIR / "multi_run" / f"train_run{rid}.csv")
        X_train = transform_pipeline(train_df, feat_cols, *art)
        y_train = train_df["label_binary"].to_numpy(dtype=np.int64)
        store = joblib.load(C5_CACHE / f"run_{rid}" / f"models_{CONFIG_TAG}.joblib")
        models = {"QSVM": store["qsvm"], "SVM-RBF": store["rbf"]}
        for name, mdl in make_ml_dl_models(RANDOM_STATE).items():
            mdl.fit(X_train, y_train)
            models[name] = mdl

        for name, mdl in models.items():
            s_train = get_decision_scores(mdl, X_train)
            s_test = get_decision_scores(mdl, X_test)
            prob_before = _sigmoid(s_test)                       # chưa hiệu chỉnh
            scl, _, _ = PlattScaler().fit(s_train, y_train)
            prob_after = scl.predict_proba(s_test)               # sau Platt
            ece_b, _ = compute_ece_mce(y_test, prob_before, N_BINS_FULL)
            ece_a, _ = compute_ece_mce(y_test, prob_after, N_BINS_FULL)
            rows.append({"run_id": rid, "model": name,
                         "ece_before": ece_b, "ece_after": ece_a})

    df = pd.DataFrame(rows)
    print(f"{'Model':12s} {'ECE before':>14s} {'ECE after':>14s} {'Δ (giảm)':>12s}")
    for mdl in df["model"].unique():
        sub = df[df["model"] == mdl]
        b, a = sub["ece_before"].mean(), sub["ece_after"].mean()
        print(f"{mdl:12s} {b:>14.4f} {a:>14.4f} {b-a:>12.4f}")
    out = DATA_DIR / "p2_platt.json"
    json.dump({"rows": rows}, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"[OK] → {out}")


def main():
    art = load_pipeline_artifacts(MODELS_DIR, DATA_DIR)
    feat_cols = art[3]
    art = art[:3]  # (selector, pca, scaler)
    run_prior_shift(feat_cols, art)
    run_low_data(feat_cols, art)
    run_platt_before_after(feat_cols, art)
    print("\n[DONE] Phase 2 recompute hoàn tất.")


if __name__ == "__main__":
    main()
