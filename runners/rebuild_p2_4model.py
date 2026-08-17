"""
Tái dựng kết quả + hình của Paper 2 theo BỘ 4 MODEL (bỏ MLP),
khớp với bộ baseline C4 của đồng nghiệp: {QSVM, SVM-RBF, RandomForest, XGBoost}.

- Chạy lại low-data với SVM-RBF (trước đây thiếu) → p2_lowdata.json (4 model).
- Vẽ lại các hình của tôi (rare ECE/Brier, forest Cohen's d, AUC-PR vs Brier,
  Platt, low-data, reliability diagram) chỉ với 4 model.
- KHÔNG đụng số/hình C4 của đồng nghiệp (prior-shift, temporal).

Chạy: python runners/rebuild_p2_4model.py
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

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.reliability import (  # noqa: E402
    RANDOM_STATE, RARE_GROUPS,
    PlattScaler, adaptive_calibration_curve, cohens_d, get_decision_scores,
    load_pipeline_artifacts, reliability_metrics, transform_pipeline,
)

DATA = ROOT / "data" / "nslkdd" / "processed_data"
MODELS_DIR = ROOT / "models" / "nslkdd"
FIGS = ROOT / "paper" / "paper2" / "figs"
REPORTS = ROOT / "reports" / "nslkdd"
C5_CACHE = MODELS_DIR / "qsvm_cache" / "multirun_c5"
LOWDATA_CACHE = MODELS_DIR / "qsvm_cache" / "p2_lowdata"
CONFIG_TAG = "mr_c5_r2_full_cq1.0_crbf10.0_cpoly0.1_n1000_t100"

MODELS = ["QSVM", "SVM-RBF", "RandomForest", "XGBoost"]
COL = {"QSVM": "#8B5CF6", "SVM-RBF": "#F59E0B", "RandomForest": "#10B981", "XGBoost": "#EF4444"}
plt.rcParams.update({"figure.dpi": 110, "font.size": 10, "axes.grid": True, "grid.alpha": 0.3})


def ml_models():
    """Bộ ML mới khớp baseline đồng nghiệp (RF, XGBoost) — KHÔNG MLP."""
    from sklearn.ensemble import RandomForestClassifier
    m = {"RandomForest": RandomForestClassifier(n_estimators=300, n_jobs=-1, random_state=RANDOM_STATE)}
    from xgboost import XGBClassifier
    m["XGBoost"] = XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.1,
                                 subsample=0.9, colsample_bytree=0.9, eval_metric="logloss",
                                 random_state=RANDOM_STATE, n_jobs=-1)
    return m


def main():
    art_full = load_pipeline_artifacts(MODELS_DIR, DATA)
    feat = art_full[3]
    art = art_full[:3]

    # ── 1. Re-run low-data với 4 model (thêm SVM-RBF) ────────────────────────
    print("[1] Low-data 4-model ...")
    from sklearn.svm import SVC
    sizes = {100: "NSL_KDD_Train_Sample100.csv", 200: "NSL_KDD_Train_Sample200.csv",
             500: "NSL_KDD_Train_Sample500.csv", 1000: "NSL_KDD_Train_Sample1000.csv"}
    te = pd.read_csv(DATA / "NSL_KDD_Test_Sample300.csv")
    Xte = transform_pipeline(te, feat, *art)
    yte = te["label_binary"].to_numpy()
    rare = np.isin(te["attack_category"].to_numpy(), RARE_GROUPS)
    rows = []
    for N, fn in sizes.items():
        tr = pd.read_csv(DATA / fn)
        Xtr = transform_pipeline(tr, feat, *art)
        ytr = tr["label_binary"].to_numpy()
        qp = LOWDATA_CACHE / f"qsvm_N{N}.joblib"
        qsvm = joblib.load(qp)  # đã cache từ lần trước
        mods = {"QSVM": qsvm,
                "SVM-RBF": SVC(kernel="rbf", C=10.0, gamma="scale", random_state=RANDOM_STATE).fit(Xtr, ytr)}
        for nm, mm in ml_models().items():
            mm.fit(Xtr, ytr); mods[nm] = mm
        for nm, mm in mods.items():
            m = reliability_metrics(mm, Xtr, ytr, Xte, yte, rare)
            m.update({"N": N, "model": nm}); rows.append(m)
    json.dump({"rows": rows}, open(ROOT / "results" / "nslkdd" / "p2_lowdata.json", "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("    -> p2_lowdata.json (4 model)")

    # ── 2. Đọc dữ liệu rare + platt (lọc 4 model) ────────────────────────────
    verify = pd.DataFrame(json.load(open(ROOT / "results" / "nslkdd" / "p2_verify_calibration.json", encoding="utf-8"))["per_run"])
    platt = pd.DataFrame(json.load(open(ROOT / "results" / "nslkdd" / "p2_platt.json", encoding="utf-8"))["rows"])
    low = pd.DataFrame(rows)

    # ── 3. Hình rare ECE/Brier ───────────────────────────────────────────────
    agg = verify.groupby("model").agg(["mean", "std"])
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    for a, met, ttl in zip(ax, ["ece_rare", "brier_rare"],
                           ["ECE on rare attacks (lower = more reliable)", "Brier on rare attacks (lower = better)"]):
        means = [agg.loc[m, (met, "mean")] for m in MODELS]
        stds = [agg.loc[m, (met, "std")] for m in MODELS]
        b = a.bar(MODELS, means, yerr=stds, capsize=4, color=[COL[m] for m in MODELS], alpha=0.88)
        b[0].set_edgecolor("black"); b[0].set_linewidth(2)
        a.set_title(ttl); a.set_ylabel(met); a.tick_params(axis="x", rotation=15)
    fig.suptitle("QSVM is the most reliable on rare attacks (5 runs, mean ± std)", fontweight="bold")
    fig.tight_layout(); _save(fig, "p2_fig_ece_brier_rare.png")

    # ── 4. Forest Cohen's d (3 baseline) ─────────────────────────────────────
    q = verify[verify.model == "QSVM"].sort_values("run_id")
    cd = {}
    for m in ["SVM-RBF", "RandomForest", "XGBoost"]:
        b = verify[verify.model == m].sort_values("run_id")
        cd[m] = {"d_ece_rare": cohens_d(q.ece_rare.values, b.ece_rare.values),
                 "d_brier_rare": cohens_d(q.brier_rare.values, b.brier_rare.values),
                 "d_auc_pr": cohens_d(q.auc_pr.values, b.auc_pr.values)}
    json.dump(cd, open(ROOT / "results" / "nslkdd" / "p2_calibration_stats.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    cdf = pd.DataFrame(cd).T
    fig, a = plt.subplots(figsize=(8, 3.6)); ys = np.arange(len(cdf)); off = 0.18
    a.barh(ys + off, cdf.d_ece_rare, 0.34, color="#8B5CF6", label="d(ECE_rare)")
    a.barh(ys - off, cdf.d_brier_rare, 0.34, color="#10B981", label="d(Brier_rare)")
    a.axvline(0, color="k", lw=1); a.axvline(-0.8, color="r", ls=":"); a.axvline(0.8, color="r", ls=":")
    a.set_yticks(ys); a.set_yticklabels(cdf.index)
    a.set_xlabel("Cohen's d (negative ⇒ QSVM more reliable); red lines mark |0.8| large effect")
    a.set_title("QSVM calibration advantage on rare attacks"); a.legend(fontsize=8)
    fig.tight_layout(); _save(fig, "p2_fig_forest_cohensd.png")

    # ── 5. AUC-PR vs Brier ───────────────────────────────────────────────────
    fig, a = plt.subplots(figsize=(6.2, 5))
    for m in MODELS:
        a.scatter(agg.loc[m, ("auc_pr", "mean")], agg.loc[m, ("brier_rare", "mean")],
                  s=180, color=COL[m], edgecolor="black",
                  linewidth=1.5 if m == "QSVM" else 0.5, zorder=3)
        a.annotate(m, (agg.loc[m, ("auc_pr", "mean")], agg.loc[m, ("brier_rare", "mean")]),
                   textcoords="offset points", xytext=(8, 4), fontsize=9)
    a.set_xlabel("AUC-PR (ranking — higher = better) →"); a.set_ylabel("Brier_rare (reliability — lower = better) ↓")
    a.set_title("Good ranking ≠ trustworthy: trees rank high but are over-confident;\nQSVM is the most trustworthy")
    fig.tight_layout(); _save(fig, "p2_fig_aucpr_vs_brier.png")

    # ── 6. Platt before/after (4 model) ──────────────────────────────────────
    g = platt[platt.model.isin(MODELS)].groupby("model")[["ece_before", "ece_after"]].mean().reindex(MODELS)
    fig, a = plt.subplots(figsize=(8, 4.2)); x = np.arange(len(g)); w = 0.38
    a.bar(x - w/2, g.ece_before, w, label="Before Platt", color="#cbd5e1")
    a.bar(x + w/2, g.ece_after, w, label="After Platt", color=[COL[m] for m in g.index], alpha=0.9)
    a.set_xticks(x); a.set_xticklabels(g.index, rotation=10); a.set_ylabel("ECE_full ↓")
    a.set_title("Platt helps QSVM/SVM, harms trees"); a.legend()
    fig.tight_layout(); _save(fig, "p2_fig_platt.png")

    # ── 7. Low-data curves (4 model) ─────────────────────────────────────────
    fig, ax = plt.subplots(1, 3, figsize=(13.5, 4))
    for a, met, ttl in zip(ax, ["ece_full", "brier_full", "auc_pr"],
                           ["ECE_full ↓", "Brier_full ↓", "AUC-PR ↑"]):
        for m in MODELS:
            s = low[low.model == m].sort_values("N")
            a.plot(s.N, s[met], marker="o", color=COL[m], lw=2 if m == "QSVM" else 1.3, label=m)
        a.set_xlabel("Train size N"); a.set_title(ttl); a.set_xscale("log")
    ax[0].legend(fontsize=8)
    fig.suptitle("Reliability under label scarcity", fontweight="bold")
    fig.tight_layout(); _save(fig, "p2_fig_lowdata.png")

    # ── 8. Reliability diagram (4 model, run 1) ──────────────────────────────
    tr = pd.read_csv(DATA / "multi_run" / "train_run1.csv")
    Xtr = transform_pipeline(tr, feat, *art); ytr = tr["label_binary"].to_numpy()
    te1 = pd.read_csv(DATA / "NSL_KDD_Test_Sample100.csv")
    Xte1 = transform_pipeline(te1, feat, *art); yte1 = te1["label_binary"].to_numpy()
    store = joblib.load(C5_CACHE / "run_1" / f"models_{CONFIG_TAG}.joblib")
    mods = {"QSVM": store["qsvm"], "SVM-RBF": store["rbf"]}
    for nm, mm in ml_models().items():
        mm.fit(Xtr, ytr); mods[nm] = mm
    fig, a = plt.subplots(figsize=(5.6, 5.4)); a.plot([0, 1], [0, 1], "k--", lw=1, label="Perfect")
    for nm in MODELS:
        mm = mods[nm]
        p = PlattScaler().fit(get_decision_scores(mm, Xtr), ytr)[0].predict_proba(get_decision_scores(mm, Xte1))
        mc, fp, _ = adaptive_calibration_curve(yte1, p, 10)
        a.plot(mc, fp, marker="o", color=COL[nm], lw=2 if nm == "QSVM" else 1.2, label=nm)
    a.set_xlabel("Mean predicted confidence"); a.set_ylabel("Empirical accuracy")
    a.set_title("Reliability diagram (run 1)\ncloser to diagonal = better calibrated"); a.legend(fontsize=8)
    fig.tight_layout(); _save(fig, "p2_fig_reliability_diagram.png")

    print("[DONE] đã vẽ lại 6 hình 4-model + low-data.")


def _save(fig, name):
    for d in (FIGS, REPORTS):
        fig.savefig(d / name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("    saved", name)


if __name__ == "__main__":
    main()
