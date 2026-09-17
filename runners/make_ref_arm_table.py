"""Table IV cua bai. Ghep cap nhanh tham chieu (XGBoost/RF tren DU dac trung) voi QSVM_ZZ cua repo, cung run, cung N,
cung tap test (full KDDTest+), arm tuned_per_N, natural prior. In bang trung binh theo N va hieu ghep cap.
"""
import os
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, t as student_t

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results", "nslkdd", "c4_revision")
ref = pd.read_csv(os.path.join(RES, "ref_arm_fullfeat.csv"))
q = pd.read_csv(os.path.join(RES, "c4_per_run_natural_refit_per_N.csv"))
q = q[(q.test_split == "full_kddtest_plus") & (q.arm == "tuned_per_N")]
runs_done = sorted(set(ref.run_id))
complete = [r for r in runs_done if (ref.run_id == r).sum() == 28]
print(f"run co du 28 o: {complete}  (tong run co du lieu: {runs_done})")
ref = ref[ref.run_id.isin(complete)]
q = q[q.run_id.isin(complete)]

wide_q = q.pivot_table(index=["run_id", "n_train"], columns="model", values="f1_macro")
wide_r = ref.pivot_table(index=["run_id", "n_train"], columns=["featset", "model"], values="f1_macro")
wide_r.columns = [f"{a}:{b}" for a, b in wide_r.columns]
w = wide_q.join(wide_r)

cols = ["QSVM_ZZ", "XGBoost", "RandomForest", "all122:XGBoost", "all122:RandomForest", "k20:XGBoost", "k20:RandomForest"]
print("\nTrung binh macro-F1 theo N (full KDDTest+, tuned per N, natural prior), %d run:" % len(complete))
print(w.groupby("n_train")[cols].mean().round(4).rename(columns={"XGBoost": "XGB(pca4,bai)", "RandomForest": "RF(pca4,bai)"}).to_string())

print("\nHieu ghep cap QSVM_ZZ - baseline (mean [CI95], Wilcoxon p tho):")
rows = []
for b in ["XGBoost", "all122:XGBoost", "k20:XGBoost", "RandomForest", "all122:RandomForest", "k20:RandomForest"]:
    for n, g in w.groupby("n_train"):
        d = (g["QSVM_ZZ"] - g[b]).dropna().to_numpy(float)
        if len(d) < 3:
            continue
        m = d.mean(); half = student_t.ppf(0.975, len(d) - 1) * d.std(ddof=1) / np.sqrt(len(d))
        p = wilcoxon(d, zero_method="wilcox").pvalue if np.any(d != 0) else 1.0
        rows.append(dict(baseline=b, n_train=n, k=len(d), delta=round(m, 4), lo=round(m - half, 4), hi=round(m + half, 4), p=round(p, 3)))
out = pd.DataFrame(rows)
print(out.pivot(index="n_train", columns="baseline", values="delta").to_string())
out.to_csv(os.path.join(RES, "ref_arm_paired.csv"), index=False)
print("\nghi results/ref_arm_paired.csv")

# ---- 13/09: xuat bang + macro cho bai (mot cho o cho moi con so cua nhanh tham chieu) ----
TAB = os.path.join(HERE, "..", "paper", "paper1", "tables")
mean = w.groupby("n_train")[cols].mean()
def dl(b, n):
    r = out[(out.baseline == b) & (out.n_train == n)].iloc[0]
    return r
def fmt_delta(r):
    return f"{r.delta:+.4f}\\ [{r.lo:+.4f},{r.hi:+.4f}]"
def fmt_delta_short(r):
    return f"{r.delta:+.4f}$ $[{r.lo:+.4f},\\,{r.hi:+.4f}]"
xgb = mean["all122:XGBoost"]; peakN = int(xgb.idxmax())
macros = "\n".join([
    "%% Sinh boi runners/make_ref_arm_table.py tu results/nslkdd/c4_revision/ref_arm_fullfeat.csv (%d run). KHONG sua tay." % len(complete),
    "\\newcommand{\\refArmRuns}{%d}" % len(complete),
    "\\newcommand{\\refArmXgbPeak}{%.4f}" % xgb.max(),
    "\\newcommand{\\refArmXgbPeakN}{%d}" % peakN,
    "\\newcommand{\\refArmXgbTenK}{%.4f}" % xgb.loc[10000],
    "\\newcommand{\\refArmDeltaXgbFiveK}{%s}" % fmt_delta_short(dl("all122:XGBoost", 5000)),
    "\\newcommand{\\refArmDeltaXgbTenK}{%s}" % fmt_delta_short(dl("all122:XGBoost", 10000)),
    "\\newcommand{\\refArmDeltaRfTenK}{%s}" % fmt_delta_short(dl("all122:RandomForest", 10000)),
    ""])
open(os.path.join(TAB, "ref_arm_macros.tex"), "w").write(macros)
lines = [
    "%% Sinh boi runners/make_ref_arm_table.py tu results/nslkdd/c4_revision/ref_arm_fullfeat.csv (%d run). KHONG sua tay." % len(complete),
    "\\begin{table*}[t]", "\\centering",
    "\\caption{Reference arm outside the paired protocol: XGBoost and random forest trained on all $122$",
    " one-hot features, on the same nested subsets, seeds and full KDDTest$^+$ as the sweep of",
    " Fig.~\\ref{fig:learning-curve}, natural prior, tuned per $N$ with the grids of Sec.~\\ref{sec:setup}.",
    " Mean macro-$F_1$ over %d runs, and the paired difference \\QSVM{} $-$ full-feature model with a" % len(complete),
    " $t$-based $95\\%$ CI. Not part of any Holm family.}",
    "\\label{tab:ref-arm}", "\\footnotesize", "\\setlength{\\tabcolsep}{3pt}",
    "\\begin{tabular}{@{}r rr rr l l@{}}", "\\toprule",
    " & \\QSVM{} & XGB, $4$-d & XGB, $122$-d & RF, $122$-d & $\\Delta$ vs XGB $122$-d & $\\Delta$ vs RF $122$-d \\\\",
    "$N$ & \\multicolumn{4}{c}{mean macro-$F_1$} & \\multicolumn{2}{c}{mean $[95\\%$ CI$]$} \\\\", "\\midrule"]
for n in mean.index:
    r = mean.loc[n]
    lines.append(f"{int(n)} & {r['QSVM_ZZ']:.4f} & {r['XGBoost']:.4f} & {r['all122:XGBoost']:.4f} & {r['all122:RandomForest']:.4f} & ${fmt_delta(dl('all122:XGBoost', n))}$ & ${fmt_delta(dl('all122:RandomForest', n))}$ \\\\")
lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}", ""]
open(os.path.join(TAB, "ref_arm.tex"), "w").write("\n".join(lines))
print("ghi tables/ref_arm.tex + ref_arm_macros.tex")
