"""Paper 2 dung lai -- ba phan con lai: low-data (A1), prior shift (C3), Platt (C4).

    python runners/run_p2_rebuild_extra.py

Cung ba thay doi nhu `run_p2_rebuild.py`: khong dung cache, 10 run, va tap
test du lon.

Rieng prior shift: ban cu dung ba file Sample300 co san (300 mau moi che do).
O day cac che do duoc dung lai TU KDDTest+ day du theo dung ti le cu, nen moi
che do co hang nghin mau thay vi 300. Ti le lay tu `p2_priorshift.json`:
Balanced 50/50, AttackHeavy 30/70, DoS-only.
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

from run_p2_rebuild import build_models  # noqa: E402
from src.reliability import (N_BINS_FULL, RARE_GROUPS,  # noqa: E402
                             PlattScaler, compute_ece_mce, get_decision_scores,
                             load_pipeline_artifacts, reliability_metrics,
                             transform_pipeline)

DATA = ROOT / "data" / "nslkdd" / "processed_data"
MODELS = ROOT / "models" / "nslkdd"
OUT = ROOT / "results" / "nslkdd" / "p2_rebuild"
OUT.mkdir(parents=True, exist_ok=True)

RUN_IDS = list(range(1, 11))
N_GRID = [100, 200, 500, 1000]
MIXES = {"Balanced_50/50": 0.50, "AttackHeavy_30/70": 0.70, "DoS_only": None}


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.asarray(x, dtype=float)))


def stratified_subsample(df, n, seed):
    """Lay n mau, phan tang tren nhan bon lop nhu bai mo ta."""
    key = df["attack_category"].where(~df["attack_category"].isin(RARE_GROUPS), "Rare")
    out = (df.groupby(key, group_keys=False)
             .apply(lambda g: g.sample(max(1, round(n * len(g) / len(df))),
                                       random_state=seed))
           )
    return out.sample(min(n, len(out)), random_state=seed)


def build_shift_sets(test_df, seed=42):
    """Dung lai ba che do prior shift tu KDDTest+ day du, giu dung ti le cu."""
    rng = np.random.default_rng(seed)
    cat = test_df["attack_category"].to_numpy()
    normal_idx = np.where(cat == "Normal")[0]
    attack_idx = np.where(cat != "Normal")[0]
    dos_idx = np.where(cat == "DoS")[0]

    sets = {}
    for name, ratio in MIXES.items():
        if ratio is None:                       # DoS-only: Normal + DoS thoi
            idx = np.concatenate([normal_idx, dos_idx])
        else:
            # ratio = ti le TAN CONG mong muon; lay toi da ma van giu dung ti le.
            n_att = min(len(attack_idx), int(len(normal_idx) * ratio / (1 - ratio)))
            n_nor = min(len(normal_idx), int(n_att * (1 - ratio) / ratio))
            idx = np.concatenate([rng.choice(normal_idx, n_nor, replace=False),
                                  rng.choice(attack_idx, n_att, replace=False)])
        sets[name] = np.sort(idx)
    return sets


def main() -> int:
    sel, pca, scaler, fc = load_pipeline_artifacts(MODELS, DATA)

    test_df = pd.read_csv(DATA / "NSL_KDD_Test_Cleaned.csv")
    X_test = transform_pipeline(test_df, fc, sel, pca, scaler)
    y_test = test_df["label_binary"].to_numpy(np.int64)
    rare_test = np.isin(test_df["attack_category"].to_numpy(), RARE_GROUPS)

    shift = build_shift_sets(test_df)
    for k, idx in shift.items():
        att = (y_test[idx] == 1).mean()
        print(f"  che do {k:20s} {len(idx):6d} mau, ti le tan cong {att:.3f}, "
              f"{int(rare_test[idx].sum()):5d} hiem")

    lowdata, priorshift, platt = [], [], []

    for rid in RUN_IDS:
        t0 = time.time()
        tr = pd.read_csv(DATA / "multi_run" / f"train_run{rid}.csv")
        y_full = tr["label_binary"].to_numpy(np.int64)
        X_full = transform_pipeline(tr, fc, sel, pca, scaler)

        # --- A1: low-data -------------------------------------------------
        for n in N_GRID:
            sub = tr if n >= len(tr) else stratified_subsample(tr, n, seed=rid)
            Xs = transform_pipeline(sub, fc, sel, pca, scaler)
            ys = sub["label_binary"].to_numpy(np.int64)
            if len(np.unique(ys)) < 2:
                continue
            for name, mdl in build_models(Xs, ys).items():
                m = reliability_metrics(mdl, Xs, ys, X_test, y_test, rare_test)
                m.update(run_id=rid, model=name, n_train=int(len(ys)))
                lowdata.append(m)

        # --- C3 + C4 dung model huan luyen tren ca 1000 mau ----------------
        models = build_models(X_full, y_full)
        for name, mdl in models.items():
            for mix, idx in shift.items():
                m = reliability_metrics(mdl, X_full, y_full, X_test[idx],
                                        y_test[idx], rare_test[idx])
                m.update(run_id=rid, model=name, mix=mix, n_test=len(idx))
                priorshift.append(m)

            s_tr = get_decision_scores(mdl, X_full)
            s_te = get_decision_scores(mdl, X_test)
            scl, _, _ = PlattScaler().fit(s_tr, y_full)
            eb, _ = compute_ece_mce(y_test, _sigmoid(s_te), N_BINS_FULL)
            ea, _ = compute_ece_mce(y_test, scl.predict_proba(s_te), N_BINS_FULL)
            platt.append(dict(run_id=rid, model=name,
                              ece_before=eb, ece_after=ea, delta=eb - ea))
        print(f"  run{rid:2d}  {time.time() - t0:5.1f}s", flush=True)

    for rows, name in ((lowdata, "lowdata"), (priorshift, "priorshift"),
                       (platt, "platt")):
        p = OUT / f"p2_rebuild_{name}.csv"
        pd.DataFrame(rows).to_csv(p, index=False, encoding="utf-8")
        print(f"  -> {p.relative_to(ROOT).as_posix()}  ({len(rows)} dong)")

    with io.open(OUT / "p2_rebuild_shift_meta.json", "w", encoding="utf-8") as f:
        json.dump({k: dict(n=len(v), attack_ratio=float((y_test[v] == 1).mean()),
                           n_rare=int(rare_test[v].sum()))
                   for k, v in shift.items()}, f, indent=1)

    print("\n=== C4 Platt: ECE truoc -> sau (trung binh 10 run) ===")
    dp = pd.DataFrame(platt)
    print(dp.groupby("model")[["ece_before", "ece_after", "delta"]].mean()
            .round(4).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
