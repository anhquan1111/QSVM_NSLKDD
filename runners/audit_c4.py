"""Soat loi doc lap cho C4 (Quang Anh yeu cau, 2026-09-03).

Nguyen tac: KHONG goi lai ham cua `src/c4_pipeline.py` de tinh thong ke. Moi con
so trong cac file `c4_pairwise_statistics_*.csv` deu duoc dung lai tu dau bang
scipy/numpy o day, roi doi chieu. Neu ca hai duong deu sai giong nhau thi khong
phat hien duoc gi -- nen phan thong ke duoc viet lai doc lap, chi phan nap du
lieu va cac gate ve du lieu moi dung chung code voi pipeline.

Chay:  python runners/audit_c4.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

TOL = 1e-9
FAMILY = {
    "QSVM_Z": "entanglement",
    "SVM_Linear": "classical_kernel",
    "SVM_Poly2": "classical_kernel",
    "SVM_RBF": "classical_kernel",
    "RandomForest": "strong_tabular",
    "XGBoost": "strong_tabular",
}
GROUP_COLS = ["arm", "test_split", "n_train"]

CASES = [
    ("NSL-KDD natural",  "results/nslkdd/c4_revision/c4_per_run_natural_refit_per_N.csv",
                         "results/nslkdd/c4_revision/c4_pairwise_statistics_natural.csv"),
    ("NSL-KDD matched",  "results/nslkdd/c4_revision/c4_per_run_matched_refit_per_N.csv",
                         "results/nslkdd/c4_revision/c4_pairwise_statistics_matched.csv"),
    ("UNSW natural",     "results/unsw/c4_revision/c4_per_run_unsw_natural_refit_per_N.csv",
                         "results/unsw/c4_revision/c4_pairwise_statistics_natural.csv"),
    # Ban phu het arm/split, sinh boi runners/pairwise_all_arms.py
    ("NSL-KDD natural (moi arm)", "results/nslkdd/c4_revision/c4_per_run_natural_refit_per_N.csv",
                         "results/nslkdd/c4_revision/c4_pairwise_statistics_natural_all_arms.csv"),
    ("NSL-KDD matched (moi arm)", "results/nslkdd/c4_revision/c4_per_run_matched_refit_per_N.csv",
                         "results/nslkdd/c4_revision/c4_pairwise_statistics_matched_all_arms.csv"),
    ("UNSW natural (moi arm)", "results/unsw/c4_revision/c4_per_run_unsw_natural_refit_per_N.csv",
                         "results/unsw/c4_revision/c4_pairwise_statistics_natural_all_arms.csv"),
]

results: list[tuple[str, bool, str]] = []


def check(name: str, passed: bool, detail: str = "") -> None:
    results.append((name, passed, detail))
    mark = "PASS" if passed else "**FAIL**"
    print(f"  [{mark}] {name}" + (f"  --  {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# A. Tinh lai thong ke ghep cap tu dau
# ---------------------------------------------------------------------------
def holm(pvals: pd.Series) -> pd.Series:
    out = pd.Series(np.nan, index=pvals.index, dtype=float)
    valid = pvals.dropna().sort_values()
    m = len(valid)
    running = 0.0
    for rank, (idx, v) in enumerate(valid.items(), start=1):
        running = max(running, min(1.0, (m - rank + 1) * float(v)))
        out.loc[idx] = running
    return out


def recompute(per_run: pd.DataFrame, metric="f1_macro") -> pd.DataFrame:
    rows = []
    for keys, block in per_run.groupby(GROUP_COLS, dropna=False):
        wide = block.pivot_table(index="run_id", columns="model", values=metric)
        if "QSVM_ZZ" not in wide.columns:
            continue
        for baseline in FAMILY:
            if baseline not in wide.columns:
                continue
            d = (wide["QSVM_ZZ"] - wide[baseline]).dropna().to_numpy(float)
            mean = float(d.mean())
            half = float(student_t.ppf(0.975, len(d) - 1) * d.std(ddof=1) / np.sqrt(len(d)))
            p = float(wilcoxon(d, zero_method="wilcox", alternative="two-sided").pvalue)
            rows.append(dict(zip(GROUP_COLS, keys)) | {
                "baseline": baseline,
                "baseline_family": FAMILY[baseline],
                "n_runs_recomputed": len(d),
                "mean_delta_recomputed": mean,
                "ci_low_recomputed": mean - half,
                "ci_high_recomputed": mean + half,
                "raw_p_recomputed": p,
                "dz_recomputed": mean / d.std(ddof=1) if d.std(ddof=1) > 0 else np.nan,
            })
    out = pd.DataFrame(rows)
    out["holm_p_recomputed"] = np.nan
    for _, idx in out.groupby(GROUP_COLS + ["baseline_family"], dropna=False).groups.items():
        out.loc[idx, "holm_p_recomputed"] = holm(out.loc[idx, "raw_p_recomputed"])

    def verdict(r):
        if not np.isfinite(r["holm_p_recomputed"]) or r["holm_p_recomputed"] >= 0.05:
            return "inconclusive"
        if r["ci_low_recomputed"] > 0:
            return "QSVM-favorable"
        if r["ci_high_recomputed"] < 0:
            return "classical-favorable"
        return "inconclusive"

    out["verdict_recomputed"] = out.apply(verdict, axis=1)
    return out


def audit_statistics() -> None:
    print("\n" + "=" * 78)
    print("A. THONG KE GHEP CAP -- dung lai tu dau roi doi chieu")
    print("=" * 78)
    for label, per_run_path, stats_path in CASES:
        print(f"\n-- {label} --")
        per_run = pd.read_csv(ROOT / per_run_path)
        committed = pd.read_csv(ROOT / stats_path)
        committed["test_split"] = committed.test_split.replace(
            {"full_kddtest_plus": "full_test"})
        per_run["test_split"] = per_run.test_split.replace(
            {"full_kddtest_plus": "full_test"})

        # A0. Dong trung: pivot_table mac dinh gop trung binh, se nuot lang.
        dup = per_run.duplicated(GROUP_COLS + ["run_id", "model"]).sum()
        check(f"{label}: khong co dong (dieu kien, run, model) trung", dup == 0,
              f"{dup} dong trung" if dup else "")

        # A1. Ghep cap dung run: QSVM_ZZ va baseline phai cung tap run_id.
        bad_pair = []
        for keys, block in per_run.groupby(GROUP_COLS, dropna=False):
            runs = {m: set(g.run_id) for m, g in block.groupby("model")}
            ref = runs.get("QSVM_ZZ", set())
            for b in FAMILY:
                if b in runs and runs[b] != ref:
                    bad_pair.append((keys, b, sorted(ref ^ runs[b])))
        check(f"{label}: moi cap dung dung cung tap run_id", not bad_pair,
              f"{len(bad_pair)} cap lech" if bad_pair else "")

        # A2-A6. Doi chieu tung con so.
        mine = recompute(per_run)
        full = committed.merge(mine, on=GROUP_COLS + ["baseline"],
                               how="outer", indicator=True)
        # Moi dong da cong bo deu phai dung lai duoc tu per-run.
        check(f"{label}: moi dong da cong bo deu tai lap duoc",
              not (full._merge == "left_only").any(),
              f"{int((full._merge == 'left_only').sum())} dong khong dung lai duoc")
        # Chieu nguoc lai KHONG phai loi: co the file phan tich chi luu mot arm.
        missing = full[full._merge == "right_only"]
        if len(missing):
            combos = sorted({(a, t) for a, t in zip(missing.arm, missing.test_split)})
            print(f"         (ghi chu) per-run co {len(missing)} o chua duoc "
                  f"tinh thong ke: arm/split {combos}")
        merged = full[full._merge == "both"]

        for col, ref_col, tol, tag in [
            ("mean_delta", "mean_delta_recomputed", TOL, "mean_delta"),
            ("ci_low", "ci_low_recomputed", TOL, "ci_low"),
            ("ci_high", "ci_high_recomputed", TOL, "ci_high"),
            ("raw_p", "raw_p_recomputed", TOL, "raw_p"),
            ("holm_p", "holm_p_recomputed", TOL, "holm_p"),
            ("effect_size_dz", "dz_recomputed", 1e-8, "effect_size_dz"),
            ("n_runs", "n_runs_recomputed", 0, "n_runs"),
        ]:
            diff = (merged[col] - merged[ref_col]).abs()
            worst = float(diff.max())
            check(f"{label}: {tag} khop", worst <= tol, f"lech lon nhat {worst:.3e}")

        mismatch = merged[merged.verdict != merged.verdict_recomputed]
        check(f"{label}: verdict khop", mismatch.empty,
              f"{len(mismatch)} o lech" if not mismatch.empty else "")

        # A7. Moi o phai co du 10 run, khong NaN o cot quyet dinh.
        check(f"{label}: moi o du 10 run", (committed.n_runs == 10).all(),
              f"co o chi {sorted(committed.n_runs.unique())} run")
        nan_cols = [c for c in ["mean_delta", "ci_low", "ci_high", "raw_p", "holm_p"]
                    if committed[c].isna().any()]
        check(f"{label}: khong NaN o cot quyet dinh", not nan_cols, str(nan_cols))


# ---------------------------------------------------------------------------
# B. Gate ve du lieu -- chay lai tren moi run
# ---------------------------------------------------------------------------
def audit_data_gates() -> None:
    print("\n" + "=" * 78)
    print("B. GATE DU LIEU -- ro ri, long nhau, lop hiem")
    print("=" * 78)
    from c4_pipeline import (build_nested_chain, gate_disjointness, gate_nesting,
                             gate_rare_presence, load_data, load_protocol)

    proto = load_protocol(ROOT)
    for dataset, regimes in [("nslkdd", ["natural", "matched"]), ("unsw", ["natural"])]:
        data = load_data(ROOT, verbose=False, dataset=dataset)
        ov = proto.get("dataset_overrides", {}).get(dataset, {})
        for regime in regimes:
            fails = {"disjoint": [], "nested": [], "rare": []}
            if "regimes" in ov and regime in ov["regimes"]:
                g = list(ov["regimes"][regime]["n_grid"])
            else:
                g = list(proto["sampling"]["regimes"][regime]["n_grid"])
            run_ids = proto["sampling"]["run_ids"]
            run_seeds = proto["sampling"]["run_seeds"]
            for run_id, seed in zip(run_ids, run_seeds):
                subsets = build_nested_chain(data, run_id, g, seed, regime)
                for key, fn in [
                    ("disjoint", lambda: gate_disjointness(data, subsets, run_id, dataset)),
                    ("nested", lambda: gate_nesting(data, subsets, run_id, dataset)),
                    ("rare", lambda: gate_rare_presence(subsets, run_id, dataset)),
                ]:
                    if not fn().passed:
                        fails[key].append(run_id)
            tag = f"{dataset}/{regime}"
            check(f"{tag}: train khong dinh test ({len(run_ids)} run)", not fails["disjoint"],
                  f"run {fails['disjoint']}")
            check(f"{tag}: chuoi con long nhau ({len(run_ids)} run)", not fails["nested"],
                  f"run {fails['nested']}")
            check(f"{tag}: moi N deu co lop hiem ({len(run_ids)} run)", not fails["rare"],
                  f"run {fails['rare']}")


# ---------------------------------------------------------------------------
# C. Nhan luong tu -- duong tat co cho ra dung ket qua Qiskit khong
# ---------------------------------------------------------------------------
def audit_kernel() -> None:
    print("\n" + "=" * 78)
    print("C. NHAN LUONG TU -- duong tat statevector vs Qiskit")
    print("=" * 78)
    from c4_pipeline import verify_kernel_equivalence

    rng = np.random.default_rng(20260903)
    for kernel in ("ZZ", "Z"):
        for n_qubits in (4, 6):
            X = rng.uniform(0, np.pi, size=(24, n_qubits))
            r = verify_kernel_equivalence(X, kernel=kernel, n_qubits=n_qubits)
            err = float(r["max_abs_diff"] if isinstance(r, dict) else r)
            check(f"kernel {kernel}, {n_qubits} qubit: khop Qiskit", err < 1e-10,
                  f"sai so lon nhat {err:.2e}")


# ---------------------------------------------------------------------------
# D. Khang dinh trong bai -- dung lai tu per-run tho
# ---------------------------------------------------------------------------
def audit_claims() -> None:
    print("\n" + "=" * 78)
    print("D. KHANG DINH CHINH -- dung lai tu per-run tho")
    print("=" * 78)
    nat = pd.read_csv(ROOT / "results/nslkdd/c4_revision/c4_per_run_natural_refit_per_N.csv")
    nat = nat[(nat.arm == "tuned_per_N") & (nat.test_split == "full_kddtest_plus")]
    piv = nat.pivot_table(index=["n_train", "run_id"], columns="model", values="f1_macro")

    # Crossover: dau cua delta trung binh so voi XGBoost phai doi tu am sang duong.
    delta = (piv["QSVM_ZZ"] - piv["XGBoost"]).groupby("n_train").mean()
    signs = np.sign(delta.values)
    flips = int((np.diff(signs) != 0).sum())
    where = [f"{delta.index[i]}->{delta.index[i+1]}"
             for i in range(len(signs) - 1) if signs[i] != signs[i + 1]]
    check("crossover vs XGBoost doi dau dung 1 lan", flips == 1, f"doi tai {where}")
    check("crossover nam trong khoang N = 2000-5000", where == ["2000->5000"], str(where))

    # QSVM-ZZ chua tung thang SVM-RBF co y nghia tren NSL-KDD.
    st = pd.read_csv(ROOT / "results/nslkdd/c4_revision/c4_pairwise_statistics_natural.csv")
    st = st[(st.arm == "tuned_per_N") & (st.test_split == "full_test")]
    rbf = st[st.baseline == "SVM_RBF"]
    check("NSL-KDD: khong N nao QSVM-ZZ thang SVM-RBF co y nghia",
          (rbf.verdict != "QSVM-favorable").all(),
          f"co o: {rbf[rbf.verdict == 'QSVM-favorable'].n_train.tolist()}")

    # UNSW thi nguoc lai.
    su = pd.read_csv(ROOT / "results/unsw/c4_revision/c4_pairwise_statistics_natural.csv")
    su = su[(su.arm == "tuned_per_N") & (su.test_split == "full_test")
            & (su.baseline == "SVM_RBF")]
    won = sorted(su[su.verdict == "QSVM-favorable"].n_train)
    check("UNSW: QSVM-ZZ thang SVM-RBF co y nghia tu N>=2000",
          won == [2000, 5000, 10000], f"thang tai N = {won}")

    # Bang tong hop cua ban do che do phai khop file per-run.
    rm = pd.read_csv(ROOT / "results/nslkdd/regime_map_rows.csv")
    c4 = rm[rm.contribution == "C4"]
    merged = c4.merge(
        st.assign(condition="N=" + st.n_train.astype(str),
                  regime="sample_complexity_natural")[
            ["regime", "condition", "baseline", "verdict"]],
        on=["regime", "condition", "baseline"], how="inner", suffixes=("_map", "_src"))
    bad = merged[merged.verdict_map != merged.verdict_src]
    check("ban do che do khop nguon (khoi C4 natural)", bad.empty,
          f"{len(bad)} o lech" if not bad.empty else f"{len(merged)} o da doi chieu")


if __name__ == "__main__":
    print("SOAT LOI C4 -- doi chieu doc lap")
    audit_statistics()
    audit_data_gates()
    audit_kernel()
    audit_claims()

    n_fail = sum(1 for _, ok, _ in results if not ok)
    print("\n" + "=" * 78)
    print(f"TONG: {len(results) - n_fail}/{len(results)} PASS")
    if n_fail:
        print(f"\n{n_fail} muc FAIL:")
        for name, ok, detail in results:
            if not ok:
                print(f"  - {name}: {detail}")
    print("=" * 78)
    sys.exit(1 if n_fail else 0)
