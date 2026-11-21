"""QSVM vs SVM-RBF khi do them gamma (Paper 1 QMI, viec 5).

Doc results/<ds>/c4_rbf_gamma/rbf_gamma_per_run.csv (runners/run_rbf_gamma.py). F1 cua 6 mo
hinh con lai lay tu cache c4_dedup (cung run, cung tap train), roi thay SVM_RBF bang ban
do gamma, dung `c4.build_pairwise_table` de Holm van tinh tren dung ho 3 kernel nhu bai.
Ba bien the RBF: "old" (gamma mac dinh, C cu, fit lai), "1se" (luat cua bai), "best"
(trung binh CV tot nhat).

    uv run python runners/analyze_rbf_gamma.py
    -> results/<ds>/c4_rbf_gamma/rbf_gamma_pairwise.csv   (chi dong baseline SVM_RBF)
    -> results/<ds>/c4_rbf_gamma/rbf_gamma_summary.csv    (F1 trung binh, gamma chon, so lan cham mep)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners")]
from src import c4_pipeline as c4  # noqa: E402
from run_rbf_gamma import CACHE_PREFIX, GAMMA_MULT  # noqa: E402

MODELS = ["QSVM_ZZ", "QSVM_Z", "SVM_Linear", "SVM_Poly2", "SVM_RBF", "RandomForest", "XGBoost"]


def main() -> int:
    pd.set_option("display.width", 200)
    for ds in ("nslkdd", "unsw"):
        out = ROOT / "results" / ds / "c4_rbf_gamma"
        f = out / "rbf_gamma_per_run.csv"
        if not f.exists():
            print(f"{ds}: chua co {f}")
            continue
        runs = pd.read_csv(f, encoding="utf-8")
        cache = ROOT / "results" / ds / "c4_dedup" / "cache"
        long = []
        for r in runs.itertuples():
            meta = json.loads((cache / f"{CACHE_PREFIX[ds]}natural_refit_per_N_tuned_per_N_N{r.N}"
                               f"_run{r.run}.json").read_text(encoding="utf-8"))
            for variant, f1_rbf in (("old", r.f1_rbf_refit_old), ("1se", r.f1_rbf_1se),
                                    ("best", r.f1_rbf_best)):
                for m in MODELS:
                    f1 = f1_rbf if m == "SVM_RBF" else meta["splits"]["full_test"][m]["f1_macro"]
                    long.append({"variant": variant, "N": r.N, "run_id": r.run, "model": m,
                                 "f1_macro": f1})
        st = c4.build_pairwise_table(pd.DataFrame(long), metric="f1_macro",
                                     group_cols=["variant", "N"])
        st = st[st.baseline == "SVM_RBF"][["variant", "N", "mean_delta", "ci_low", "ci_high",
                                            "raw_p", "holm_p", "verdict", "n_runs"]]
        st.to_csv(out / "rbf_gamma_pairwise.csv", index=False, encoding="utf-8")

        g = runs.groupby("N")
        summ = pd.DataFrame({
            "f1_qsvm": g.f1_qsvm.mean(), "f1_rbf_old": g.f1_rbf_refit_old.mean(),
            "f1_rbf_1se": g.f1_rbf_1se.mean(), "f1_rbf_best": g.f1_rbf_best.mean(),
            "gamma_mult_1se_median": g.gamma_mult_1se.median(),
            "n_1se_default_gamma": g.gamma_mult_1se.apply(lambda s: int((s == 1.0).sum())),
            "n_1se_at_gamma_edge": g.gamma_mult_1se.apply(
                lambda s: int(s.isin([min(GAMMA_MULT), max(GAMMA_MULT)]).sum())),
            "n_best_at_gamma_edge": g.gamma_mult_best.apply(
                lambda s: int(s.isin([min(GAMMA_MULT), max(GAMMA_MULT)]).sum())),
            "max_gate_dev": g.apply(lambda d: (d.f1_rbf_refit_old - d.f1_rbf_cache).abs().max(),
                                    include_groups=False),
        }).reset_index()
        summ.to_csv(out / "rbf_gamma_summary.csv", index=False, encoding="utf-8")
        print(f"== {ds}")
        print(summ.round(4).to_string(index=False))
        print(st.pivot_table(index="N", columns="variant", values="verdict",
                             aggfunc="first").to_string())
        print(st.round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
