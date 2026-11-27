"""Sinh cac bang cua ban Paper 1 nop Quantum Machine Intelligence tu CSV.

Ghi vao paper/paper1_qmi/tables/ (bo chu "submitted version", nhan muc moi):
    crossover_arms.tex   <- results/nslkdd/c4_revision/c4_pairwise_statistics_natural_all_arms.csv
    ref_arm.tex          <- results/nslkdd/c4_revision/ref_arm_fullfeat.csv + c4_per_run_natural_refit_per_N.csv
    dedup_sensitivity.tex <- results/{nslkdd,unsw}/c4_dedup/dedup_verdict_changes.csv
    multiplicity.tex     <- results/nslkdd/regime_map_multiplicity.csv
    novel_attacks.tex    <- results/nslkdd/c4_dedup/novel_attack_recall_summary.csv
                            (sinh bang runners/analyze_novel_attacks.py)

    uv run python runners/make_qmi_tables.py

KHONG sua tay file .tex sinh ra; sua o day roi chay lai.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
C4 = ROOT / "results/nslkdd/c4_revision"
OUT = ROOT / "paper/paper1_qmi/tables"
HEAD = "% Sinh boi runners/make_qmi_tables.py tu {src}. KHONG sua tay.\n"


def write(name: str, src: str, body: list[str]) -> None:
    path = OUT / name
    path.write_text(HEAD.format(src=src) + "\n".join(body) + "\n", encoding="utf-8")
    print(f"ghi {path.relative_to(ROOT)}")


def crossover_arms() -> None:
    """Hieu ghep cap QSVM-ZZ - baseline theo N, hai nhanh frozen / tuned."""
    src = "results/nslkdd/c4_revision/c4_pairwise_statistics_natural_all_arms.csv"
    d = pd.read_csv(ROOT / src)
    d = d[(d.test_split == "full_test") & (d.metric == "f1_macro")]
    bases = [("XGBoost", "XGBoost"), ("RandomForest", "Random forest"), ("SVM_RBF", "SVM-RBF")]
    arms = [("frozen_c2", "frozen"), ("tuned_per_N", "tuned")]
    ns = sorted(d.n_train.unique())
    get = {(r.baseline, r.arm, r.n_train): r.mean_delta for r in d.itertuples()}
    # Hang doi dau: N nho nhat ma moi to hop deu duong
    flip = min(n for n in ns if all(get[(b, a, n)] > 0 for b, _ in bases for a, _ in arms))
    body = [
        r"\begin{table}[t]", r"\centering",
        r"\caption{Paired mean difference in macro-$F_1$, \QSVM{} minus baseline, over ten runs on the",
        r"full KDDTest$^+$ set under the natural class prior. \emph{Frozen}: hyper-parameters held at the",
        r"values selected once on the tuning set; \emph{tuned}: every model, quantum and classical,",
        r"tuned at each $N$.",
        rf"All six baseline--arm combinations change sign at the same step, $N={ns[ns.index(flip) - 1]}$ to",
        rf"$N={flip}$ (bold row).}}",
        r"\label{tab:crossover-arms}", r"\footnotesize", r"\setlength{\tabcolsep}{4pt}",
        r"\begin{tabular}{@{}r rr rr rr@{}}", r"\toprule",
        " & " + " & ".join(rf"\multicolumn{{2}}{{c}}{{{lab}}}" for _, lab in bases) + r" \\",
        r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}",
        "$N$ & " + " & ".join(f"{a} & {t}" for _ in bases for a, t in [("frozen", "tuned")]) + r" \\",
        r"\midrule"]
    for n in ns:
        cells = [f"{get[(b, a, n)]:+.4f}" for b, _ in bases for a, _ in arms]
        if n == flip:
            body.append(rf"\textbf{{{n}}} & " + " & ".join(rf"\textbf{{{c}}}" for c in cells) + r" \\")
        else:
            body.append(f"{n} & " + " & ".join(cells) + r" \\")
    body += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    write("crossover_arms.tex", src, body)


def ref_arm() -> None:
    """Nhanh tham chieu: XGBoost/RF tren du 122 dac trung, ghep cap voi QSVM-ZZ cung run, cung N."""
    src = "results/nslkdd/c4_revision/ref_arm_fullfeat.csv"
    ref = pd.read_csv(ROOT / src)
    q = pd.read_csv(C4 / "c4_per_run_natural_refit_per_N.csv")
    q = q[(q.test_split == "full_kddtest_plus") & (q.arm == "tuned_per_N")]
    runs = [r for r in sorted(set(ref.run_id)) if (ref.run_id == r).sum() == 28]
    ref, q = ref[ref.run_id.isin(runs)], q[q.run_id.isin(runs)]
    w = q.pivot_table(index=["run_id", "n_train"], columns="model", values="f1_macro")
    wr = ref.pivot_table(index=["run_id", "n_train"], columns=["featset", "model"], values="f1_macro")
    wr.columns = [f"{a}:{b}" for a, b in wr.columns]
    w = w.join(wr)
    mean = w.groupby("n_train").mean()

    def delta(col: str, n: int) -> str:
        d = (w.xs(n, level="n_train")["QSVM_ZZ"] - w.xs(n, level="n_train")[col]).dropna().to_numpy(float)
        m = d.mean()
        half = student_t.ppf(0.975, len(d) - 1) * d.std(ddof=1) / np.sqrt(len(d))
        return f"${m:+.4f}\\ [{m - half:+.4f},{m + half:+.4f}]$"

    body = [
        r"\begin{table*}[t]", r"\centering",
        r"\caption{Reference arm outside the paired protocol: XGBoost and random forest trained on all",
        r"$122$ one-hot features, on the same nested subsets, seeds and full KDDTest$^+$ as",
        r"Fig.~\ref{fig:learning-curve}, natural prior, tuned per $N$. Mean macro-$F_1$ over",
        rf"{len(runs)} runs, and the paired difference \QSVM{{}} $-$ full-feature model with a $t$-based",
        r"$95\%$ CI. These comparisons belong to no Holm family.}",
        r"\label{tab:ref-arm}", r"\footnotesize", r"\setlength{\tabcolsep}{3pt}",
        r"\begin{tabular}{@{}r rr rr l l@{}}", r"\toprule",
        r" & \QSVM{} & XGB, $4$-d & XGB, $122$-d & RF, $122$-d & $\Delta$ vs XGB $122$-d & $\Delta$ vs RF $122$-d \\",
        r"$N$ & \multicolumn{4}{c}{mean macro-$F_1$} & \multicolumn{2}{c}{mean $[95\%$ CI$]$} \\",
        r"\midrule"]
    for n in mean.index:
        r = mean.loc[n]
        body.append(f"{int(n)} & {r['QSVM_ZZ']:.4f} & {r['XGBoost']:.4f} & {r['all122:XGBoost']:.4f} & "
                    f"{r['all122:RandomForest']:.4f} & {delta('all122:XGBoost', n)} & "
                    f"{delta('all122:RandomForest', n)} \\\\")
    body += [r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
    write("ref_arm.tex", src, body)


def dedup() -> None:
    """Dem verdict truoc / sau khi bo dong test trung train, nhanh tuned_per_N, test day du."""
    src = "results/{nslkdd,unsw}/c4_dedup/dedup_verdict_changes.csv"
    blocks = [("nslkdd", "natural", "NSL-KDD", "natural"),
              ("nslkdd", "matched", "NSL-KDD", "rare-enriched"),
              ("unsw", "natural", "UNSW-NB15", "natural")]
    meta = {ds: pd.read_json(ROOT / f"results/{ds}/c4_dedup/dup_mask_meta.json", typ="series")
            for ds in ("nslkdd", "unsw")}
    body = [
        r"\begin{table}[t]", r"\centering",
        r"\caption{Sensitivity of the training-set-size comparisons to test records duplicated in the",
        r"training data. All seven models were retrained with their stored hyper-parameters (tuned at",
        r"each $N$) and scored on the full test set and on the test set with duplicates removed; both",
        r"columns come from this retraining. A duplicate is a test record whose raw features equal",
        rf"those of any training record: {meta['nslkdd'].n_test_duplicate:,} of",
        rf"{meta['nslkdd'].n_test_raw:,} test records for NSL-KDD ({100 * meta['nslkdd'].frac_test_duplicate:.1f}\%),",
        rf"{meta['unsw'].n_test_duplicate:,} of {meta['unsw'].n_test_raw:,} for UNSW-NB15",
        rf"({100 * meta['unsw'].frac_test_duplicate:.1f}\%). Cells are counted as favouring \QSVM{{}} /",
        r"favouring the classical baseline / inconclusive (Holm-adjusted $p\ge0.05$).}",
        r"\label{tab:dedup}", r"\footnotesize", r"\setlength{\tabcolsep}{4pt}",
        r"\begin{tabular}{@{}ll r ccc@{}}", r"\toprule",
        r"Dataset & Prior & Cells & Full test & Duplicates removed & Changed \\",
        r"\midrule"]
    for ds, regime, name, prior in blocks:
        d = pd.read_csv(ROOT / f"results/{ds}/c4_dedup/dedup_verdict_changes.csv")
        r = d[(d.arm == "tuned_per_N") & (d.regime == regime) & (d.repr_mode == "refit_per_N")
              & d.test_split.isin(["full_test", "full_kddtest_plus"])]
        assert len(r) == 1, (ds, regime, len(r))
        r = r.iloc[0]
        assert r.rerunQ_to_afterC == 0 and r.rerunC_to_afterQ == 0, "co o doi chieu"
        body.append(f"{name} & {prior} & {r.n_cells} & {r.rerun_Q}/{r.rerun_C}/{r.rerun_I} & "
                    f"{r.after_Q}/{r.after_C}/{r.after_I} & {r.n_changed_rerun_to_after} \\\\")
    body += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    write("dedup_sensitivity.tex", src, body)


def multiplicity() -> None:
    """Dem verdict cua ban do regime theo bon cach hieu chinh (R3), 109 o duoc dem va 42 o tu nhien.

    109 = 110 o tru o dKTA (ZZ - Z): o do la kiem tra co che, ve tren Hinh 10 nhung khong dem.
    """
    src = "results/nslkdd/regime_map_multiplicity.csv"
    d = pd.read_csv(ROOT / src).set_index(["block", "correction"])
    rows = [("none", r"None (raw $p\le0.05$ only)"),
            ("holm_within_family", "Holm within baseline family"),
            ("bh_block", r"Benjamini--Hochberg over the block"),
            ("holm_block", "Holm over the block")]
    blocks = [("counted_109", "Counted cells"), ("c4_natural_42", "Natural prior, full test")]
    p_min = d.min_raw_p.min()
    body = [
        r"\begin{table}[t]", r"\centering",
        r"\caption{Verdict counts of the regime map under four multiplicity corrections, recomputed",
        r"from the raw Wilcoxon $p$ of each cell. Counts are favouring \QSVM{} / favouring the classical",
        r"baseline / inconclusive. The alignment cell of the map is a mechanism check and is not counted.",
        r"Holm within the baseline family is the convention used elsewhere in",
        rf"the paper. With ten runs the smallest attainable two-sided $p$ is ${p_min:.5f}$, so Holm over a",
        r"whole block cannot reject any cell.}",
        r"\label{tab:multiplicity}", r"\footnotesize", r"\setlength{\tabcolsep}{4pt}",
        r"\begin{tabular}{@{}l cc@{}}", r"\toprule",
        "Correction & " + " & ".join(
            f"{lab} ({int(d.loc[(b, 'none'), 'n_cells'])})" for b, lab in blocks) + r" \\",
        r"\midrule"]
    for key, lab in rows:
        cells = [f"{int(d.loc[(b, key), 'quantum'])}/{int(d.loc[(b, key), 'classical'])}/"
                 f"{int(d.loc[(b, key), 'inconclusive'])}" for b, _ in blocks]
        body.append(f"{lab} & " + " & ".join(cells) + r" \\")
    body += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    write("multiplicity.tex", src, body)


def tex_int(x) -> str:
    """So nguyen co dau phan nghin kieu LaTeX: 9083 -> 9{,}083."""
    return f"{int(x):,}".replace(",", "{,}")


def novel_attacks() -> None:
    """Recall tan cong kieu da gap / kieu moi va do dac hieu tren binh thuong, N=1000 va 10^4."""
    src = "results/nslkdd/c4_dedup/novel_attack_recall_summary.csv"
    d = pd.read_csv(ROOT / src).set_index(["model", "N"])
    models = [("QSVM_ZZ", r"\QSVM{}"), ("QSVM_Z", r"\QSVMZ{}"), ("SVM_Linear", "SVM-linear"),
              ("SVM_Poly2", "SVM-poly2"), ("SVM_RBF", "SVM-RBF"), ("RandomForest", "Random forest"),
              ("XGBoost", "XGBoost")]
    first = d.iloc[0]
    body = [
        r"\begin{table}[t]", r"\centering",
        r"\caption{Recall on KDDTest$^+$ attacks of types present in KDDTrain$^+$ (seen, "
        rf"${tex_int(first.n_seen)}$ records) and of the ${tex_int(first.n_novel)}$ attack records of types",
        r"absent from it (novel, $17$ types), and specificity on normal traffic, at two training-set",
        r"sizes under the natural prior. Mean of ten runs, tuned arm.}",
        r"\label{tab:novel}", r"\footnotesize", r"\setlength{\tabcolsep}{4pt}",
        r"\begin{tabular}{@{}l cc cc cc@{}}", r"\toprule",
        r" & \multicolumn{2}{c}{Seen types} & \multicolumn{2}{c}{Novel types} & "
        r"\multicolumn{2}{c}{Normal (specificity)} \\",
        r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(l){6-7}",
        r"Model & $N=1000$ & $N=10^4$ & $N=1000$ & $N=10^4$ & $N=1000$ & $N=10^4$ \\",
        r"\midrule"]
    for key, lab in models:
        cells = [f"{d.loc[(key, n), m + '_mean']:.3f}"
                 for m in ("recall_seen", "recall_novel", "specificity_normal") for n in (1000, 10000)]
        body.append(f"{lab} & " + " & ".join(cells) + r" \\")
    body += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    write("novel_attacks.tex", src, body)


def main() -> int:
    OUT.mkdir(exist_ok=True)
    crossover_arms()
    ref_arm()
    dedup()
    multiplicity()
    novel_attacks()
    return 0


if __name__ == "__main__":
    sys.exit(main())
