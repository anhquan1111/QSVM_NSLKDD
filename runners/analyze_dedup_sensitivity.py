"""Bản đồ regime C4 trước/sau khi bỏ dòng test trùng train (đáp phản biện R3).

Đọc kết quả của `runners/run_dedup_sensitivity.py` (`results/<ds>/c4_dedup/cache/*.json`)
và cache C4 gốc (`results/<ds>/c4_revision/cache/*.json`), dựng lại bảng so sánh ghép
cặp QSVM_ZZ vs 6 baseline bằng ĐÚNG `c4.build_pairwise_table` (Wilcoxon hai phía,
CI95 t, Holm trong từng (ô điều kiện, họ baseline), verdict cần Holm p < 0,05 và CI
không chứa 0) — cùng hàm mà `analyze_c4.py` / `pairwise_all_arms.py` dùng.

Ba phiên bản cho mỗi ô:
    before  : metric trong cache gốc (số bài đã công bố)
    rerun   : test đầy đủ, từ dự đoán chạy lại (cùng mô hình với `after`)
    after   : test đã bỏ dòng trùng train
`rerun` cần vì XGBoost có subsample < 1 không tái hiện bit-by-bit trên máy này; so
`rerun -> after` là phép so ghép cặp sạch (cùng mô hình, chỉ khác tập test).

Kiểm trước khi phân tích: bảng `before` phải khớp `c4_pairwise_statistics_*_all_arms.csv`
và 72 ô C4 của `results/nslkdd/regime_map_rows.csv` (bản đồ 110 ô). 38 ô C2/C3 của
bản đồ KHÔNG được chạy lại (thí nghiệm khác, không thuộc cache C4).

Chạy:
    uv run python runners/analyze_dedup_sensitivity.py
    uv run python runners/analyze_dedup_sensitivity.py --allow-partial   # khi mới thử nhỏ

Xuất ra `results/<ds>/c4_dedup/`:
    dedup_pairwise_before_after.csv   — mỗi dòng một ô (điều kiện x baseline)
    dedup_verdict_changes.csv         — đếm ô đổi kết luận theo nhóm
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import c4_pipeline as c4  # noqa: E402

MODELS = ["QSVM_ZZ", "QSVM_Z", "SVM_Linear", "SVM_Poly2", "SVM_RBF",
          "RandomForest", "XGBoost"]
CELL = ["regime", "repr_mode", "arm", "test_split", "n_train"]
SHORT = {"QSVM-favorable": "Q", "classical-favorable": "C", "inconclusive": "I"}
N_RUNS = 10


def flatten(rec: dict, splits: dict, source: str) -> list[dict]:
    rows = []
    for split, models in splits.items():
        split = {"full_kddtest_plus": "full_test"}.get(split, split)
        for model in MODELS:
            if model not in models:
                continue
            rows.append({"regime": rec["regime"], "repr_mode": rec["repr_mode"],
                         "arm": rec["arm"], "n_train": int(rec["n_train"]),
                         "run_id": int(rec["run_id"]), "test_split": split,
                         "model": model, "f1_macro": models[model]["f1_macro"],
                         "source": source})
    return rows


def load_original(ds: str) -> pd.DataFrame:
    rows = []
    for p in sorted((ROOT / "results" / ds / "c4_revision" / "cache").glob("*_run*.json")):
        if p.name.startswith("NSL_KDD_"):      # 5 file chạy lại đối chứng, không thuộc bài
            continue
        with open(p, encoding="utf-8") as fp:
            rec = json.load(fp)
        rows += flatten(rec, rec["splits"], "before")
    return pd.DataFrame(rows)


def load_rerun(ds: str, include_failed: bool) -> tuple[pd.DataFrame, dict]:
    rows, info = [], {"n_files": 0, "n_skipped_gate": 0, "n_xgb_drift": 0}
    for p in sorted((ROOT / "results" / ds / "c4_dedup" / "cache").glob("*_run*.json")):
        if p.name.startswith("NSL_KDD_"):
            continue
        with open(p, encoding="utf-8") as fp:
            rec = json.load(fp)
        if not rec.get("gate_passed", False) and not include_failed:
            info["n_skipped_gate"] += 1
            continue
        info["n_files"] += 1
        info["n_xgb_drift"] += int(bool(rec.get("xgb_platform_drift")))
        sp = rec["splits"]
        rows += flatten(rec, {"full_test": sp["full_test"], "fixed_300": sp["fixed_300"]}, "rerun")
        rows += flatten(rec, {"full_test": sp["full_test_dedup"],
                              "fixed_300": sp["fixed_300_dedup"]}, "after")
    return pd.DataFrame(rows), info


def pairwise(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    st = c4.build_pairwise_table(df, metric="f1_macro", group_cols=CELL)
    keep = CELL + ["baseline", "mean_delta", "ci_low", "ci_high", "raw_p", "holm_p",
                   "effect_size_dz", "verdict", "n_runs"]
    return st[keep]


def check_before(ds: str, before: pd.DataFrame) -> list[str]:
    """Bảng `before` dựng lại phải khớp bảng thống kê đã lưu và bản đồ regime."""
    msgs = []
    d = ROOT / "results" / ds / "c4_revision"
    for regime in ("natural", "matched"):
        f = d / f"c4_pairwise_statistics_{regime}_all_arms.csv"
        if not f.exists():
            continue
        ref = pd.read_csv(f)
        ref["test_split"] = ref.test_split.replace({"full_kddtest_plus": "full_test"})
        mine = before[(before.regime == regime) & (before.repr_mode == "refit_per_N")]
        m = ref.merge(mine, on=["arm", "test_split", "n_train", "baseline"],
                      suffixes=("_ref", "_new"))
        bad = m[(np.abs(m.mean_delta_ref - m.mean_delta_new) > 1e-12)
                | (m.verdict_ref != m.verdict_new)]
        msgs.append(f"{ds}/{regime}: {len(m)}/{len(ref)} o khop bang luu, lech {len(bad)}")
        if len(m) != len(ref) or len(bad):
            raise SystemExit("Bang 'before' khong khop bang thong ke da luu -> dung: " + msgs[-1])
    if ds == "nslkdd":
        rm = pd.read_csv(ROOT / "results" / "nslkdd" / "regime_map_rows.csv")
        rm = rm[rm.contribution == "C4"].copy()
        rm["regime_short"] = rm.regime.str.replace("sample_complexity_", "", regex=False)
        rm["n_train"] = rm.condition.str.split("=").str[1].astype(int)
        mine = before[(before.repr_mode == "refit_per_N") & (before.arm == "tuned_per_N")
                      & (before.test_split == "full_test")]
        m = rm.merge(mine, left_on=["regime_short", "n_train", "baseline"],
                     right_on=["regime", "n_train", "baseline"], suffixes=("_map", "_new"))
        bad = m[(np.abs(m.estimate - m.mean_delta) > 1e-9) | (m.verdict_map != m.verdict_new)]
        msgs.append(f"regime_map_rows C4: {len(m)}/{len(rm)} o khop, lech {len(bad)}")
        if len(m) != len(rm) or len(bad):
            raise SystemExit("Bang 'before' khong khop regime_map_rows.csv -> dung: " + msgs[-1])
    return msgs


def merge_versions(before, rerun, after, ds: str) -> pd.DataFrame:
    key = CELL + ["baseline"]
    vals = ["mean_delta", "ci_low", "ci_high", "holm_p", "verdict", "n_runs"]
    out = before[key + vals].rename(columns={v: f"before_{v}" for v in vals})
    for name, tab in (("rerun", rerun), ("after", after)):
        if tab.empty:
            for v in vals:
                out[f"{name}_{v}"] = np.nan
            continue
        out = out.merge(tab[key + vals].rename(columns={v: f"{name}_{v}" for v in vals}),
                        on=key, how="left")
    out.insert(0, "dataset", c4.get_spec(ds).name)
    out["complete"] = (out.after_n_runs == N_RUNS) & (out.rerun_n_runs == N_RUNS)
    out["in_regime_map_110"] = ((out.dataset == "NSL-KDD") & (out.repr_mode == "refit_per_N")
                                & (out.arm == "tuned_per_N") & (out.test_split == "full_test"))
    out["changed_before_to_after"] = out.complete & (out.before_verdict != out.after_verdict)
    out["changed_rerun_to_after"] = out.complete & (out.rerun_verdict != out.after_verdict)
    out["changed_before_to_rerun"] = out.complete & (out.before_verdict != out.rerun_verdict)
    return out


def count_changes(tab: pd.DataFrame) -> pd.DataFrame:
    rows = []
    grp = ["dataset", "regime", "repr_mode", "arm", "test_split", "in_regime_map_110"]
    for keys, blk in tab.groupby(grp, dropna=False):
        comp = blk[blk.complete]
        row = dict(zip(grp, keys))
        row.update({"n_cells": len(blk), "n_complete": len(comp),
                    "n_changed_before_to_after": int(comp.changed_before_to_after.sum()),
                    "n_changed_rerun_to_after": int(comp.changed_rerun_to_after.sum()),
                    "n_changed_before_to_rerun": int(comp.changed_before_to_rerun.sum())})
        for col in ("before", "rerun", "after"):
            for v, s in SHORT.items():
                row[f"{col}_{s}"] = int((comp[f"{col}_verdict"] == v).sum())
        # Ma trận chuyển rerun -> after (Q/C/I)
        for a, sa in SHORT.items():
            for b, sb in SHORT.items():
                row[f"rerun{sa}_to_after{sb}"] = int(((comp.rerun_verdict == a)
                                                       & (comp.after_verdict == b)).sum())
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", default=["nslkdd", "unsw"])
    ap.add_argument("--allow-partial", action="store_true",
                    help="chay ca khi chua du 10 run moi o (thu nho); o thieu ghi complete=False")
    ap.add_argument("--include-failed", action="store_true",
                    help="gom ca file khong qua cong tai hien (chi de go loi)")
    args = ap.parse_args()

    summary = []
    for ds in args.datasets:
        out_dir = ROOT / "results" / ds / "c4_dedup"
        out_dir.mkdir(parents=True, exist_ok=True)
        before = pairwise(load_original(ds))
        for msg in check_before(ds, before):
            print("  [kiem before]", msg)
        rr, info = load_rerun(ds, args.include_failed)
        print(f"{ds}: {info['n_files']} file chay lai qua cong "
              f"(bo {info['n_skipped_gate']} file khong qua cong; "
              f"{info['n_xgb_drift']} file co XGBoost lech nen tang)")
        if rr.empty and not args.allow_partial:
            raise SystemExit(f"{ds}: chua co ket qua chay lai nao")
        rerun = pairwise(rr[rr.source == "rerun"]) if len(rr) else pd.DataFrame()
        after = pairwise(rr[rr.source == "after"]) if len(rr) else pd.DataFrame()
        tab = merge_versions(before, rerun, after, ds)
        if not args.allow_partial and not tab.complete.all():
            raise SystemExit(f"{ds}: {(~tab.complete).sum()} o chua du {N_RUNS} run "
                             f"-> chay du truoc, hoac dung --allow-partial")
        tab.to_csv(out_dir / "dedup_pairwise_before_after.csv", index=False, encoding="utf-8")
        cnt = count_changes(tab)
        cnt.to_csv(out_dir / "dedup_verdict_changes.csv", index=False, encoding="utf-8")
        summary.append(cnt)
        print(f"  -> {out_dir.relative_to(ROOT)}/dedup_pairwise_before_after.csv ({len(tab)} o)")

    allc = pd.concat(summary, ignore_index=True)
    show = ["dataset", "regime", "repr_mode", "arm", "test_split", "in_regime_map_110",
            "n_cells", "n_complete", "n_changed_before_to_after", "n_changed_rerun_to_after",
            "n_changed_before_to_rerun"]
    print("\n=== So o doi ket luan (chi tinh o du 10 run) ===")
    print(allc[show].to_string(index=False))
    rm = allc[allc.in_regime_map_110]
    print(f"\nBan do regime (khoi C4, 72/110 o): {int(rm.n_complete.sum())} o du 10 run, "
          f"{int(rm.n_changed_before_to_after.sum())} o doi ket luan truoc->sau. "
          "38 o C2/C3 khong chay lai.")
    un = allc[(allc.dataset == "UNSW-NB15") & (allc.arm == "tuned_per_N")
              & (allc.test_split == "full_test")]
    if len(un):
        print(f"UNSW-NB15 (36 o, ngoai ban do 110 o): {int(un.n_complete.sum())} o du 10 run, "
              f"{int(un.n_changed_before_to_after.sum())} o doi ket luan truoc->sau.")


if __name__ == "__main__":
    main()
