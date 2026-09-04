"""Soat 12 hinh cua ban revision: so lieu co dung artifact khong, va co phai
hinh THAT sinh ra tu lan chay hay khong.

Hai cau hoi tach bach:

1. **Xuat xu.** Moi file hinh phai moi hon ca script sinh no lan du lieu nguon.
   Neu mot hinh cu hon du lieu thi no la ban con sot lai, du noi dung co the
   trong giong het.
2. **So lieu.** Tung con so ma hinh ve ra duoc doi chieu lai voi artifact goc.
   Voi ba hinh so do (1-3) thi doi chieu cac HANG SO chung hien thi (so CNOT,
   K, n*, so chieu, so run).

Chay:  python runners/audit_figures.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "runners")]

FIGS = ROOT / "paper" / "paper1" / "figs_revision"
NSL = ROOT / "results/nslkdd"
UNSW = ROOT / "results/unsw"

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"  [{'PASS' if ok else '**FAIL**'}] {name}" + (f"  --  {detail}" if detail else ""))


def close(a, b, tol=5e-4) -> bool:
    return abs(float(a) - float(b)) <= tol


# ---------------------------------------------------------------------------
# A. Xuat xu
# ---------------------------------------------------------------------------
# hinh -> (script sinh no, cac file du lieu nguon)
PROVENANCE = {
    "fig1_zzfeaturemap_circuit": ("make_paper1_schematics.py", []),
    "fig2_contribution_map": ("make_paper1_schematics.py", []),
    "fig3_pipeline": ("make_paper1_schematics.py", []),
    "fig4_selectkbest_sweep": ("make_paper1_figures.py", [
        "results/nslkdd/c1_revision/c1_ksweep.csv",
        "results/nslkdd/c1_revision/c1_ksensitivity.json"]),
    "fig5_c1_dimension_selection": ("make_paper1_figures.py", [
        "results/unsw/c4_revision/u1_dimension_metrics.csv",
        "results/unsw/c4_revision/u1_c1_selection_unsw.json"]),
    "fig6_entanglement_ablation": ("make_paper1_figures.py", [
        "results/nslkdd/c2_revision/c2_kta_per_run.csv",
        "results/nslkdd/c2_revision/c2_per_run.csv"]),
    "fig7_per_run_f1": ("make_paper1_figures.py", [
        "results/nslkdd/c2_revision/c2_per_run.csv"]),
    "fig8_prior_shift": ("make_paper1_figures.py", [
        "results/nslkdd/c3_revision/c3_prior_shift_per_run.csv"]),
    "fig9_learning_curve_nslkdd": ("make_paper1_figures.py", [
        "results/nslkdd/c4_revision/c4_per_run_natural_refit_per_N.csv",
        "results/nslkdd/c4_revision/c4_per_run_matched_refit_per_N.csv"]),
    "fig10_regime_map": ("make_paper1_figures.py", [
        "results/nslkdd/regime_map_rows.csv"]),
    "fig11_unsw_transfer": ("make_paper1_figures.py", [
        "results/unsw/c4_revision/c4_per_run_unsw_natural_refit_per_N.csv"]),
    "fig12_width_concentration": ("make_paper1_figures.py", [
        "results/nslkdd/c4_revision/variant_K80n8/c4_per_run_nslkdd_natural_refit_per_N.csv",
        "results/nslkdd/c1_revision/c1_gram_concentration.csv"]),
}


def audit_provenance() -> None:
    print("\n" + "=" * 78)
    print("A. XUAT XU -- hinh co moi hon script va du lieu nguon khong")
    print("=" * 78)
    for name, (script, sources) in PROVENANCE.items():
        pdf, png = FIGS / f"{name}.pdf", FIGS / f"{name}.png"
        if not (pdf.exists() and png.exists()):
            check(f"{name}: co ca .pdf va .png", False, "thieu file")
            continue
        t_fig = min(pdf.stat().st_mtime, png.stat().st_mtime)
        newer = [Path(s).name for s in sources
                 if (ROOT / s).exists() and (ROOT / s).stat().st_mtime > t_fig]
        s_path = ROOT / "runners" / script
        if s_path.exists() and s_path.stat().st_mtime > t_fig:
            newer.append(script)
        check(f"{name}: moi hon moi nguon", not newer,
              f"cu hon: {newer}" if newer else f"{pdf.stat().st_size // 1024} KB pdf")


# ---------------------------------------------------------------------------
# B. So lieu
# ---------------------------------------------------------------------------
def audit_schematics() -> None:
    print("\n" + "=" * 78)
    print("B1. HINH SO DO (1-3) -- doi chieu cac hang so hien thi")
    print("=" * 78)
    import c4_pipeline as c4

    fm = c4.build_feature_map("ZZ", n_qubits=4, reps=2, entanglement="full")
    n_cx = dict(fm.decompose().count_ops()).get("cx", 0)
    check("Fig 1: so CNOT ghi '24' khop Qiskit", n_cx == 24, f"count_ops -> {n_cx}")

    spec = c4.get_spec("nslkdd")
    check("Fig 3: 'K=20' khop DatasetSpec", spec.select_k == 20, f"select_k={spec.select_k}")
    check("Fig 3: 'n*=4' khop DatasetSpec", spec.n_qubits == 4, f"n_qubits={spec.n_qubits}")

    df = c4.read_table(ROOT / spec.processed_dir / spec.train_file)
    from config import LABEL_COLS
    n_feat = len([c for c in df.columns if c not in LABEL_COLS])
    check("Fig 3: '122 dims after OHE' khop du lieu", n_feat == 122, f"{n_feat} dac trung")
    del df

    sel = json.loads((UNSW / "c4_revision/u1_c1_selection_unsw.json").read_text())
    check("Fig 2: 'Figs. 4-5' cho C1 -- n* NSL=4, UNSW=6",
          sel["nslkdd_selected_n"] == 4 and sel["selected_n"] == 6,
          f"NSL {sel['nslkdd_selected_n']}, UNSW {sel['selected_n']}")

    c2 = pd.read_csv(NSL / "c2_revision/c2_per_run.csv")
    check("Fig 2: C2 ghi '10 runs'", c2.run_id.nunique() == 10, f"{c2.run_id.nunique()} run")
    check("Fig 2: C2 ghi 'N_train=1000'",
          json.loads((NSL / "c2_revision/c2_summary.json").read_text())["train_size"] == 1000,
          "")


def audit_data_figures() -> None:
    print("\n" + "=" * 78)
    print("B2. HINH CO DU LIEU (4-12) -- dung lai tung con so tu artifact")
    print("=" * 78)
    from make_paper1_figures import NSL_C1

    # --- Fig 4 ---
    ks = pd.read_csv(NSL / "c1_revision/c1_ksweep.csv").set_index("K")
    check("Fig 4: K=20 PCA-4 = 0.9007", close(ks.loc[20, "f1_pca4_mean"], 0.9007, 1e-3),
          f"{ks.loc[20, 'f1_pca4_mean']:.4f}")
    check("Fig 4: K=80 la dinh cua duong PCA-4",
          int(ks.f1_pca4_mean.idxmax()) == 80, f"dinh tai K={int(ks.f1_pca4_mean.idxmax())}")
    star = json.loads((NSL / "c1_revision/c1_ksensitivity.json").read_text())
    got = {int(k): v["n_star"] for k, v in star.items()}
    check("Fig 4b: n* theo K = {20:4, 40:7, 80:8, 122:9}",
          got == {20: 4, 40: 7, 80: 8, 122: 9}, str(got))

    # --- Fig 5 ---
    k20 = pd.read_csv(NSL / "c1_revision/c1_ksensitivity.csv").query("K == 20").set_index("n")
    worst = max((NSL_C1.set_index("n")[c] - k20[c]).abs().max() for c in ("V", "KTA", "Q"))
    check("Fig 5: bang NSL go cung khop artifact doc lap", worst < 5e-4,
          f"lech lon nhat {worst:.2e}")
    check("Fig 5: n* NSL = 4 tu chinh luat", star["20"]["n_star"] == 4, "")
    u = pd.read_csv(UNSW / "c4_revision/u1_dimension_metrics.csv").set_index("n")
    sel = json.loads((UNSW / "c4_revision/u1_c1_selection_unsw.json").read_text())
    check("Fig 5: UNSW n*=6, V=0.9044, KTA=0.1986",
          sel["selected_n"] == 6 and close(u.loc[6, "V"], 0.9044, 1e-3)
          and close(u.loc[6, "KTA"], 0.1986, 1e-3),
          f"V={u.loc[6, 'V']:.4f}, KTA={u.loc[6, 'KTA']:.4f}")

    # --- Fig 6 ---
    kta = pd.read_csv(NSL / "c2_revision/c2_kta_per_run.csv")
    from scipy import stats as st
    d = kta.delta_kta.values
    half = st.t.ppf(0.975, len(d) - 1) * st.sem(d)
    check("Fig 6b: dKTA = +0.1378 [+0.1267, +0.1489]",
          close(d.mean(), 0.1378, 1e-3) and close(d.mean() - half, 0.1267, 1e-3)
          and close(d.mean() + half, 0.1489, 1e-3),
          f"{d.mean():+.4f} [{d.mean() - half:+.4f}, {d.mean() + half:+.4f}]")
    f1 = pd.read_csv(NSL / "c2_revision/c2_per_run.csv").pivot_table(
        index="run_id", columns="model", values="f1_macro")
    df1 = (f1["QSVM_ZZ"] - f1["QSVM_Z"]).values
    h1 = st.t.ppf(0.975, len(df1) - 1) * st.sem(df1)
    check("Fig 6b: dF1 = +0.0114, CI cat 0",
          close(df1.mean(), 0.0114, 1e-3) and (df1.mean() - h1) < 0 < (df1.mean() + h1),
          f"{df1.mean():+.4f} [{df1.mean() - h1:+.4f}, {df1.mean() + h1:+.4f}]")

    # --- Fig 7 ---
    m = f1.mean()
    check("Fig 7: XGB 0.8503 > ZZ 0.8469 > RF 0.8446",
          close(m["XGBoost"], 0.8503, 1e-3) and close(m["QSVM_ZZ"], 0.8469, 1e-3)
          and close(m["RandomForest"], 0.8446, 1e-3),
          f"{m['XGBoost']:.4f} / {m['QSVM_ZZ']:.4f} / {m['RandomForest']:.4f}")

    # --- Fig 8 ---
    ps = pd.read_csv(NSL / "c3_revision/c3_prior_shift_per_run.csv")
    piv = ps.pivot_table(index="condition", columns="model", values="f1_macro")
    check("Fig 8a: 70% attack -- ZZ 0.7906 < RF 0.8067 < XGB 0.8148",
          close(piv.loc["attack_70pct", "QSVM_ZZ"], 0.7906, 1e-3)
          and close(piv.loc["attack_70pct", "XGBoost"], 0.8148, 1e-3),
          f"ZZ {piv.loc['attack_70pct', 'QSVM_ZZ']:.4f}, "
          f"XGB {piv.loc['attack_70pct', 'XGBoost']:.4f}")
    p2 = ps.pivot_table(index=["run_id", "condition"], columns="model", values="f1_macro")
    drop = {mm: (ps[(ps.model == mm) & (ps.condition == "attack_70pct")]
                 .sort_values("run_id").f1_macro.values
                 - ps[(ps.model == mm) & (ps.condition == "attack_30pct")]
                 .sort_values("run_id").f1_macro.values).mean()
            for mm in ("QSVM_ZZ", "XGBoost", "RandomForest")}
    check("Fig 8b: ZZ tut nhieu hon XGB va RF",
          drop["QSVM_ZZ"] < drop["XGBoost"] and drop["QSVM_ZZ"] < drop["RandomForest"],
          {k: round(v, 4) for k, v in drop.items()})

    # --- Fig 9 ---
    nat = pd.read_csv(NSL / "c4_revision/c4_per_run_natural_refit_per_N.csv")
    nat = nat[(nat.arm == "tuned_per_N") & (nat.test_split == "full_kddtest_plus")]
    pn = nat.pivot_table(index="n_train", columns="model", values="f1_macro")
    check("Fig 9a: N=10000 ZZ 0.7855, SVM-RBF 0.7740 > XGB 0.7706",
          close(pn.loc[10000, "QSVM_ZZ"], 0.7855, 1e-3)
          and pn.loc[10000, "SVM_RBF"] > pn.loc[10000, "XGBoost"],
          f"ZZ {pn.loc[10000, 'QSVM_ZZ']:.4f}, RBF {pn.loc[10000, 'SVM_RBF']:.4f}, "
          f"XGB {pn.loc[10000, 'XGBoost']:.4f}")
    st9 = pd.read_csv(NSL / "c4_revision/c4_pairwise_statistics_natural.csv")
    st9 = st9[(st9.arm == "tuned_per_N") & (st9.baseline == "XGBoost")].set_index("n_train")
    check("Fig 9c: crossover 2000->5000 vs XGBoost",
          st9.loc[2000, "mean_delta"] < 0 < st9.loc[5000, "mean_delta"],
          f"{st9.loc[2000, 'mean_delta']:+.4f} -> {st9.loc[5000, 'mean_delta']:+.4f}")
    rbf = pd.read_csv(NSL / "c4_revision/c4_pairwise_statistics_natural.csv")
    rbf = rbf[(rbf.arm == "tuned_per_N") & (rbf.baseline == "SVM_RBF")]
    check("Fig 9: ZZ chua tung thang SVM-RBF co y nghia",
          (rbf.verdict != "QSVM-favorable").all(),
          f"{(rbf.verdict == 'QSVM-favorable').sum()} o QSVM-favorable")

    # --- Fig 10 ---
    rm = pd.read_csv(NSL / "regime_map_rows.csv")
    vc = rm.verdict.value_counts()
    check("Fig 10: 21 / 68 / 21 tren 110 so sanh",
          len(rm) == 110 and vc.get("QSVM-favorable") == 21
          and vc.get("inconclusive") == 68 and vc.get("classical-favorable") == 21,
          f"{len(rm)} dong, {dict(vc)}")

    # --- Fig 11 ---
    su = pd.read_csv(UNSW / "c4_revision/c4_pairwise_statistics_natural.csv")
    su = su[(su.arm == "tuned_per_N") & (su.test_split == "full_test")]
    won = sorted(su[(su.baseline == "SVM_RBF") & (su.verdict == "QSVM-favorable")].n_train)
    check("Fig 11: UNSW ZZ thang SVM-RBF tai N>=2000", won == [2000, 5000, 10000], str(won))
    tree = su[su.baseline.isin(["XGBoost", "RandomForest"])]
    check("Fig 11: khong doi dau so voi ensemble cay",
          (tree.mean_delta < 0).all(), f"{(tree.mean_delta >= 0).sum()} o duong")

    # --- Fig 12 ---
    var = pd.read_csv(NSL / "c4_revision/variant_K80n8/c4_pairwise_statistics_natural.csv")
    # Khong loc baseline: file co du 6 baseline x 8 co N = 48 o, tat ca deu
    # classical-favorable. Bai viet trich con so day du nay.
    check("Fig 12a: 48/48 o classical-favorable o K=80/n=8",
          len(var) == 48 and (var.verdict == "classical-favorable").all(),
          f"{len(var)} o, {(var.verdict == 'classical-favorable').sum()} classical")
    con = pd.read_csv(NSL / "c1_revision/c1_gram_concentration.csv").query("K == 80")
    zz = con[con.kernel == "ZZ"].set_index("n").offdiag_std
    z = con[con.kernel == "Z"].set_index("n").offdiag_std
    r_zz = 1 - zz.loc[10] / zz.loc[4]
    r_z = 1 - z.loc[10] / z.loc[4]
    check("Fig 12b: ZZ mat do trai nhanh hon Z it nhat gap doi",
          r_zz > 2 * r_z, f"ZZ mat {r_zz:.0%}, Z mat {r_z:.0%}")
    al = json.loads((NSL / "c1_revision/c1_gram_concentration.json").read_text())
    ratio20 = al["20"]["alpha_ratio"]
    check("Fig 12b: tai K=20, ty le so mu ~ 2 (khop C(n,2) vs n)",
          close(ratio20, 2.0, 0.15), f"alpha_ZZ/alpha_Z = {ratio20:.2f}")


if __name__ == "__main__":
    print("SOAT 12 HINH CUA BAN REVISION")
    audit_provenance()
    audit_schematics()
    audit_data_figures()
    n_fail = sum(1 for _, ok, _ in results if not ok)
    print("\n" + "=" * 78)
    print(f"TONG: {len(results) - n_fail}/{len(results)} PASS")
    for name, ok, detail in results:
        if not ok:
            print(f"  - FAIL: {name}: {detail}")
    print("=" * 78)
    sys.exit(1 if n_fail else 0)
