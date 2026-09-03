"""Phân tích kết quả C4 cho một dataset: bảng learning curve, thống kê paired
(CI / Wilcoxon / d_z / Holm), rare-attack, và phát hiện crossover.

Chạy:
    uv run python runners/analyze_c4.py --dataset unsw --regime natural
    uv run python runners/analyze_c4.py --dataset nslkdd --regime natural

Xuất ra `results/<dataset>/c4_revision/`:
    c4_pairwise_statistics_<regime>.csv   — cùng schema với c3_pairwise_statistics.csv
    c4_rare_attack_<regime>.csv
    c4_crossover_<regime>.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import c4_pipeline as c4  # noqa: E402

MODEL_ORDER = ["QSVM_ZZ", "QSVM_Z", "SVM_Linear", "SVM_Poly2", "SVM_RBF",
               "RandomForest", "XGBoost"]


def load_per_run(root: Path, dataset: str, regime: str, repr_mode: str) -> pd.DataFrame:
    """Gom mọi mảnh CSV của cùng cấu hình (kể cả các mảnh chạy song song theo run)."""
    d = root / "results" / dataset / "c4_revision"
    # Chấp nhận cả hai quy ước tên: có tiền tố dataset (mới) và không có (các file
    # NSL-KDD sinh ra trước khi pipeline hỗ trợ nhiều dataset).
    pats = [f"c4_per_run_{dataset}_{regime}_{repr_mode}*.csv",
            f"c4_per_run_{regime}_{repr_mode}*.csv"]
    files = [f for p in pats for f in sorted(d.glob(p))]
    if not files:
        raise SystemExit(f"Không tìm thấy file nào khớp {pats} trong {d}")
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    return df.drop_duplicates(subset=["arm", "n_train", "run_id", "test_split", "model"])


def curve_table(block: pd.DataFrame, metric="f1_macro") -> pd.DataFrame:
    cols = [m for m in MODEL_ORDER if m in block.model.unique()]
    return block.pivot_table(index="n_train", columns="model", values=metric,
                             aggfunc="mean")[cols]


def crossover_rows(stats: pd.DataFrame) -> pd.DataFrame:
    """Với mỗi baseline, tìm mốc N mà verdict đổi từ classical sang QSVM."""
    out = []
    for base, blk in stats.groupby("baseline"):
        blk = blk.sort_values("n_train")
        v = blk.verdict.tolist()
        ns = blk.n_train.tolist()
        first_q = next((ns[i] for i, x in enumerate(v) if x == "QSVM-favorable"), None)
        last_c = next((ns[i] for i in range(len(v) - 1, -1, -1)
                       if v[i] == "classical-favorable"), None)
        out.append(dict(baseline=base, last_classical_favorable_N=last_c,
                        first_qsvm_favorable_N=first_q,
                        crossover=(last_c is not None and first_q is not None
                                   and last_c < first_q)))
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="unsw", choices=list(c4.DATASETS))
    ap.add_argument("--regime", default="natural")
    ap.add_argument("--repr-mode", default="refit_per_N")
    ap.add_argument("--arm", default="tuned_per_N")
    ap.add_argument("--test-split", default="full_test")
    args = ap.parse_args()

    root = c4.find_project_root()
    out = root / "results" / args.dataset / "c4_revision"
    spec = c4.get_spec(args.dataset)
    df = load_per_run(root, args.dataset, args.regime, args.repr_mode)
    if "full_kddtest_plus" in df.test_split.unique():
        df["test_split"] = df.test_split.replace({"full_kddtest_plus": "full_test"})

    print(f"=== {spec.name} · regime={args.regime} · {len(df)} bản ghi ===")
    print(f"  arm={sorted(df.arm.unique())}  N={sorted(df.n_train.unique())}  "
          f"run={df.run_id.nunique()}  model={df.model.nunique()}")

    block = df[(df.arm == args.arm) & (df.test_split == args.test_split)]
    if block.empty:
        raise SystemExit(f"Không có dữ liệu cho arm={args.arm}, split={args.test_split}")

    print(f"\n=== Learning curve (mean macro-F1, {args.arm}, {args.test_split}) ===")
    print(curve_table(block).round(4).to_string())

    # --- thống kê paired, cùng công thức/Holm như C3 ---
    stats = c4.build_pairwise_table(block, metric="f1_macro", group_cols=["n_train"])
    stats.insert(0, "dataset", spec.name)
    stats.insert(1, "arm", args.arm)
    stats.insert(2, "test_split", args.test_split)
    stats.to_csv(out / f"c4_pairwise_statistics_{args.regime}.csv", index=False)
    print(f"\n=== Verdict QSVM_ZZ vs baseline (Holm) ===")
    print(stats.pivot_table(index="n_train", columns="baseline", values="verdict",
                            aggfunc="first").to_string())

    print("\n=== Chi tiết vs tree ensembles ===")
    t = stats[stats.baseline.isin(["XGBoost", "RandomForest"])]
    print(t[["n_train", "baseline", "mean_delta", "ci_low", "ci_high", "holm_p",
             "effect_size_dz", "verdict"]].sort_values(["baseline", "n_train"])
          .to_string(index=False, float_format=lambda v: f"{v:.4f}"))

    cx = crossover_rows(stats)
    cx.to_csv(out / f"c4_crossover_{args.regime}.csv", index=False)
    print("\n=== Crossover ===")
    print(cx.to_string(index=False))

    # --- rare-attack ---
    rows = []
    for n, blk in block.groupby("n_train"):
        p = lambda c: blk.pivot_table(index="run_id", columns="model", values=c)
        f1r, rc = p("f1_rare"), p("recall_rare")
        mg, sg = p("rare_margin_signed_mean"), p("rare_margin_signed_std")
        ma, sa = p("rare_margin_abs_mean"), p("rare_margin_abs_std")
        for m in MODEL_ORDER:
            if m not in f1r.columns:
                continue
            r = dict(dataset=spec.name, n_train=n, model=m,
                     f1_rare=f1r[m].mean(), recall_rare=rc[m].mean(),
                     margin_signed_mean=mg[m].mean(), margin_abs_mean=ma[m].mean())
            if m != "QSVM_ZZ":
                r["d_signed_vs_ZZ"] = float(np.mean(
                    (mg["QSVM_ZZ"] - mg[m]) / np.sqrt((sg["QSVM_ZZ"] ** 2 + sg[m] ** 2) / 2)))
                r["d_absmargin_vs_ZZ"] = float(np.mean(
                    (ma["QSVM_ZZ"] - ma[m]) / np.sqrt((sa["QSVM_ZZ"] ** 2 + sa[m] ** 2) / 2)))
                s = c4.paired_effect_summary((f1r["QSVM_ZZ"] - f1r[m]).to_numpy())
                r.update({"delta_f1_rare": s["mean_delta"], "ci_low": s["ci_low"],
                          "ci_high": s["ci_high"], "wilcoxon_p": s["wilcoxon_p"],
                          "verdict": s["verdict"]})
            rows.append(r)
    rare = pd.DataFrame(rows)
    rare.to_csv(out / f"c4_rare_attack_{args.regime}.csv", index=False)
    print("\n=== F1 trên rare subset ===")
    print(rare.pivot_table(index="n_train", columns="model",
                           values="f1_rare").round(4).to_string())
    print("\n=== Signed margin trên rare (ÂM = nằm sai phía biên) ===")
    print(rare.pivot_table(index="n_train", columns="model",
                           values="margin_signed_mean").round(4).to_string())

    # --- ablation ZZ vs Z ---
    print("\n=== Ablation ZZ − Z theo N ===")
    for n, blk in block.groupby("n_train"):
        w = blk.pivot_table(index="run_id", columns="model", values="f1_macro")
        s = c4.paired_effect_summary((w["QSVM_ZZ"] - w["QSVM_Z"]).to_numpy())
        print(f"  N={n:<6} {s['mean_delta']:+.4f}  CI[{s['ci_low']:+.4f},{s['ci_high']:+.4f}]"
              f"  p={s['wilcoxon_p']:.4f}  d_z={s['effect_size_dz']:+.2f}  {s['verdict']}")

    print(f"\nĐã ghi vào {out}")


if __name__ == "__main__":
    main()
