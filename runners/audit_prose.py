"""Doi chieu tung con so VIET TRONG THAN BAI nguoc ve artifact.

`audit_c4.py` kiem thong ke, `audit_figures.py` kiem hinh. Con thieu mot cho:
so go tay vao cau van. Do la cho de sai nhat va cung la cho reviewer doc dau
tien. Script nay dong cho do lai.

Cach lam: moi muc kiem gom mot chuoi PHAI CO trong file .tex va mot ham tinh
lai gia tri do tu artifact. Neu artifact doi ma cau van khong doi -> FAIL.
Neu cau van bi go sai mot chu so -> FAIL. Neu ai do sua cau van ma quen chay
lai -> FAIL.

    python runners/audit_prose.py
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SEC = ROOT / "paper/paper1/sections"
NSL = ROOT / "results/nslkdd"
UNSW = ROOT / "results/unsw"

TEXT: dict[str, str] = {}
for f in sorted(SEC.glob("*.tex")):
    TEXT[f.name] = io.open(f, encoding="utf-8").read()
for extra in ("limitations_revision.tex", "theory_revision.tex",
              "main_revision.tex", "appendix_lemma.tex",
              "response_letter.tex"):
    p = ROOT / "paper/paper1" / extra
    if p.exists():
        TEXT[extra] = io.open(p, encoding="utf-8").read()

OK = FAILED = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global OK, FAILED
    if cond:
        OK += 1
        print(f"  [PASS] {name}" + (f"  --  {detail}" if detail else ""))
    else:
        FAILED += 1
        print(f"  [FAIL] {name}  --  {detail}")


def says(where: str, phrase: str) -> bool:
    """Cau van co xuat hien dung nhu the khong."""
    if where == "*":
        return any(phrase in t for t in TEXT.values())
    return phrase in TEXT.get(where, "")


def claim(name: str, where: str, phrase: str, value: float, fmt: str) -> None:
    """Chuoi `phrase` phai co trong file, VA gia tri tinh lai phai ra dung no."""
    want = fmt.format(value)
    in_text = says(where, phrase)
    matches = want in phrase
    check(name, in_text and matches,
          f"van ban: {'co' if in_text else 'KHONG CO'} | "
          f"tinh lai: {want} | trich: {phrase[:58]}")


# ---------------------------------------------------------------------------
def nsl_c4(regime: str = "natural", arm: str = "tuned_per_N") -> pd.DataFrame:
    d = pd.read_csv(NSL / f"c4_revision/c4_pairwise_statistics_{regime}.csv")
    d["test_split"] = d.test_split.replace({"full_kddtest_plus": "full_test"})
    return d[(d.arm == arm) & (d.test_split == "full_test")]


def nsl_runs(regime: str = "natural") -> pd.DataFrame:
    d = pd.read_csv(NSL / f"c4_revision/c4_per_run_{regime}_refit_per_N.csv")
    d["test_split"] = d.test_split.replace({"full_kddtest_plus": "full_test"})
    return d[(d.arm == "tuned_per_N") & (d.test_split == "full_test")]


def section_c1() -> None:
    print("\nA. Muc V-A -- chon so chieu")
    ks = pd.read_csv(NSL / "c1_revision/c1_ksweep.csv")
    claim("F1 tho tai K=122", "05_results.tex",
          "monotonically to $0.9727$ at the full $K=122$",
          float(ks[ks.K == 122].f1_raw_mean.iloc[0]), "{:.4f}")
    claim("dinh PCA-4 tai K=80", "05_results.tex",
          "peaks at $0.9283$ at $K=80$",
          float(ks[ks.K == 80].f1_pca4_mean.iloc[0]), "{:.4f}")
    claim("PCA-4 tai K=20", "05_results.tex",
          "$K=20$ the projected value is $0.9007$",
          float(ks[ks.K == 20].f1_pca4_mean.iloc[0]), "{:.4f}")

    gain = float(ks[ks.K == 80].f1_pca4_mean.iloc[0]
                 - ks[ks.K == 20].f1_pca4_mean.iloc[0])
    claim("chenh lech K=20 -> K=80", "05_results.tex",
          "buys $0.028$\nmacro-$F_1$ for the classical proxy", gain, "{:.3f}")

    j = json.load(open(NSL / "c1_revision/c1_ksensitivity.json"))
    check("n* theo K = 4,7,8,9", says("05_results.tex",
          "$n^\\ast = 4, 7, 8, 9$ for $K = 20, 40, 80, 122$")
          and [j[k]["n_star"] for k in ("20", "40", "80", "122")] == [4, 7, 8, 9],
          str([j[k]["n_star"] for k in ("20", "40", "80", "122")]))
    claim("KTA_max tai K=20", "05_results.tex",
          "$\\mathrm{KTA}_{\\max}=0.2439$", j["20"]["kta_max"], "{:.4f}")
    claim("nguong giai doan 2", "05_results.tex",
          "threshold of $0.2317$", j["20"]["kta_threshold"], "{:.4f}")
    check("tap giai doan 2 = {4,5,6}",
          says("05_results.tex", "narrows this to $\\{4,5,6\\}$")
          and j["20"]["stage2"] == [4, 5, 6], str(j["20"]["stage2"]))


def section_c2() -> None:
    print("\nB. Muc V-B -- kho sat entanglement")
    a = pd.read_csv(NSL / "c2_revision/c2_aggregate.csv").set_index("model")
    order = ["XGBoost", "QSVM_ZZ", "RandomForest", "SVM_RBF", "QSVM_Z",
             "SVM_Poly2", "SVM_Linear"]
    got = list(a.f1_macro_mean.sort_values(ascending=False).index)
    check("thu tu 7 model dung nhu cau van", got == order, " > ".join(got))
    claim("XGBoost dan dau", "05_results.tex",
          "XGBoost $0.8503$", float(a.loc["XGBoost"].f1_macro_mean), "{:.4f}")
    claim("QSVM_ZZ thu hai", "05_results.tex",
          "\\QSVM{} $0.8469$", float(a.loc["QSVM_ZZ"].f1_macro_mean), "{:.4f}")

    p = pd.read_csv(NSL / "c2_revision/c2_paired_statistics.csv").set_index("effect")
    p = p.rename(columns={"ci95_low": "ci_low", "ci95_high": "ci_high"})
    kta = p.loc["ZZ_minus_Z_KTA"]
    f1 = p.loc["ZZ_minus_Z_F1"]
    claim("dKTA", "05_results.tex", "$\\Delta\\mathrm{KTA} = +0.1378$",
          float(kta.estimate), "{:.4f}")
    claim("dF1", "05_results.tex", "= +0.0114$ $[-0.0054,+0.0281]$",
          float(f1.estimate), "{:.4f}")
    check("hai dau mut CI cua dF1 go dung",
          f"[{f1.ci_low:+.4f},{f1.ci_high:+.4f}]".replace("+0.0", "+0.0")
          in TEXT["05_results.tex"].replace(" ", ""),
          f"[{f1.ci_low:+.4f}, {f1.ci_high:+.4f}]")
    check("CI cua dF1 that su cat 0", f1.ci_low < 0 < f1.ci_high,
          f"[{f1.ci_low:+.4f}, {f1.ci_high:+.4f}]")

    n = pd.read_csv(NSL / "c2_revision/c2_noise_f1_summary.csv").set_index("model")
    for lbl, col, mdl in (("ZZ ideal", "ideal_statevector", "QSVM_ZZ"),
                          ("ZZ shot", "ideal_finite_shot", "QSVM_ZZ"),
                          ("ZZ noisy", "realistic_noisy_simulator", "QSVM_ZZ")):
        v = float(n.loc[mdl][col])
        check(f"nhieu: {lbl} = {v:.4f}", f"${v:.4f}$" in TEXT["05_results.tex"],
              f"{v:.4f}")
    check("cau van noi ro nhieu KHONG lam giam",
          says("05_results.tex", "the noisy value is not lower than the ideal"),
          "phai giu -- day la cho de bi doc thanh 'nhieu giup'")


def section_c3() -> None:
    print("\nC. Muc V-C -- dich chuyen phan bo")
    rm = pd.read_csv(NSL / "regime_map_rows.csv")
    ps = rm[rm.regime == "prior_shift"]
    for cond, base in (("attack_50pct", "QSVM_Z"), ("attack_70pct", "QSVM_Z")):
        r = ps[(ps.condition == cond) & (ps.baseline == base)].iloc[0]
        check(f"prior {cond} vs Z = {r.estimate:+.4f}",
              f"${r.estimate:+.4f}$".replace("+", "+") in TEXT["05_results.tex"],
              f"{r.estimate:+.4f}")
    r70 = ps[(ps.condition == "attack_70pct") & (ps.baseline == "XGBoost")].iloc[0]
    claim("70% vs XGBoost", "05_results.tex", "($-0.0242$",
          float(r70.estimate), "{:+.4f}")
    check("70% vs XGBoost la classical-favorable",
          r70.verdict == "classical-favorable", r70.verdict)

    pert = rm[rm.regime == "perturbation"]
    check("nhieu dac trung: 6/6 classical-favorable",
          len(pert) == 6 and (pert.verdict == "classical-favorable").all(),
          f"{len(pert)} o")
    lo, hi = pert.estimate.max(), pert.estimate.min()
    check("do doc tu -0.69 den -1.11",
          says("05_results.tex", "slopes from $-0.69$ to $-1.11$")
          and abs(lo - (-0.6933)) < 5e-4 and abs(hi - (-1.1082)) < 5e-4,
          f"{hi:.4f} .. {lo:.4f}")

    comp = rm[rm.regime == "attack_composition"]
    check("thanh phan tan cong: 4 QSVM-favorable + 2 inconclusive",
          (comp.verdict == "QSVM-favorable").sum() == 4
          and (comp.verdict == "inconclusive").sum() == 2,
          comp.verdict.value_counts().to_dict())

    tmp = rm[rm.regime == "temporal"]
    check("thoi gian: 3 classical-favorable, 0 QSVM-favorable",
          (tmp.verdict == "classical-favorable").sum() == 3
          and (tmp.verdict == "QSVM-favorable").sum() == 0,
          tmp.verdict.value_counts().to_dict())


def section_c4() -> None:
    print("\nD. Muc V-D -- do phuc tap mau va cho doi dau")
    d = nsl_runs()
    lo = d[d.n_train == 100].groupby("model").f1_macro.mean()
    hi = d[d.n_train == 10000].groupby("model").f1_macro.mean()
    claim("N=100: XGBoost dan dau", "05_results.tex", "XGBoost $0.7802$",
          float(lo["XGBoost"]), "{:.4f}")
    claim("N=100: QSVM_ZZ chot bang", "05_results.tex", "\\QSVM{} $0.6989$",
          float(lo["QSVM_ZZ"]), "{:.4f}")
    check("N=100: QSVM_ZZ that su gan chot",
          list(lo.sort_values(ascending=False).index)[-2] == "QSVM_ZZ",
          " > ".join(lo.sort_values(ascending=False).index))
    claim("N=10000: QSVM_ZZ dan dau", "05_results.tex", "\\QSVM{} $0.7855$",
          float(hi["QSVM_ZZ"]), "{:.4f}")
    check("N=10000: QSVM_ZZ that su dung dau",
          hi.idxmax() == "QSVM_ZZ",
          " > ".join(hi.sort_values(ascending=False).index))

    s = nsl_c4()
    x2 = s[(s.n_train == 2000) & (s.baseline == "XGBoost")].iloc[0]
    x5 = s[(s.n_train == 5000) & (s.baseline == "XGBoost")].iloc[0]
    xa = s[(s.n_train == 10000) & (s.baseline == "XGBoost")].iloc[0]
    check("doi dau 2000 -> 5000 vs XGBoost",
          says("05_results.tex", "($-0.0129 \\rightarrow +0.0100$)")
          and x2.mean_delta < 0 < x5.mean_delta,
          f"{x2.mean_delta:+.4f} -> {x5.mean_delta:+.4f}")
    claim("Holm tai N=5000", "05_results.tex", "$p_{\\text{Holm}}=0.027$",
          float(x5.holm_p), "{:.3f}")
    claim("dz tai N=5000", "05_results.tex", "$d_z=1.22$",
          float(x5.effect_size_dz), "{:.2f}")
    claim("Holm tai N=10000", "05_results.tex", "$p_{\\text{Holm}}=0.0078$",
          float(xa.holm_p), "{:.4f}")

    rbf = s[s.baseline == "SVM_RBF"]
    check("khong o nao thang SVM-RBF co y nghia",
          (rbf.verdict == "QSVM-favorable").sum() == 0
          and says("05_results.tex", "never demonstrably beats an RBF"),
          rbf.verdict.value_counts().to_dict())

    lin = s[(s.baseline == "SVM_Linear") & (s.verdict == "QSVM-favorable")]
    pol = s[(s.baseline == "SVM_Poly2") & (s.verdict == "QSVM-favorable")]
    check("linear tu N=1000, poly2 tu N=2000",
          lin.n_train.min() == 1000 and pol.n_train.min() == 2000,
          f"linear {lin.n_train.min()}, poly2 {pol.n_train.min()}")
    rf = s[(s.baseline == "RandomForest") & (s.verdict == "QSVM-favorable")]
    check("random forest chi co y nghia tai N=10000",
          list(rf.n_train) == [10000], str(list(rf.n_train)))

    m = nsl_c4("matched")
    check("matched: 26/30 khong ket luan duoc",
          len(m) == 30 and (m.verdict == "inconclusive").sum() == 26,
          f"{len(m)} o, {m.verdict.value_counts().to_dict()}")
    check("matched khong the vuot N=2000", m.n_train.max() == 2000,
          f"N max = {m.n_train.max()}")
    cfg = json.load(open(ROOT / "configs/c4_protocol.json"))
    reason = cfg["sampling"]["regimes"]["matched"]["ceiling_reason"]
    check("ly do tran N=2000 co ghi '59%' va cau van trich dung",
          "59%" in reason and says("05_results.tex", "share $59\\%$ of their rare"),
          reason[:60])

    arms = pd.read_csv(NSL / "c4_revision/c4_pairwise_statistics_natural_all_arms.csv")
    arms["test_split"] = arms.test_split.replace(
        {"full_kddtest_plus": "full_test"})
    arms = arms[arms.test_split == "full_test"]
    flips = 0
    for arm in ("frozen_c2", "tuned_per_N"):
        for b in ("XGBoost", "RandomForest", "SVM_RBF"):
            g = arms[(arms.arm == arm) & (arms.baseline == b)].set_index("n_train")
            if g.loc[2000, "mean_delta"] < 0 < g.loc[5000, "mean_delta"]:
                flips += 1
    check("6/6 to hop doi dau trong khoang 2000->5000", flips == 6,
          f"{flips}/6")


def section_rare() -> None:
    print("\nE. Muc V-E -- tan cong hiem")
    r = pd.read_csv(NSL / "c4_revision/c4_rare_attack_natural.csv")
    r = r[r.n_train == 10000].set_index("model").f1_rare
    for mdl, txt in (("SVM_RBF", "SVM-RBF $0.585$"),
                     ("QSVM_ZZ", "\\QSVM{} $0.507$"),
                     ("XGBoost", "XGBoost $0.334$"),
                     ("RandomForest", "random forest $0.331$")):
        claim(f"rare F1 {mdl}", "05_results.tex", txt, float(r[mdl]), "{:.3f}")
    check("SVM-RBF that su dung dau ve rare F1", r.idxmax() == "SVM_RBF",
          " > ".join(r.sort_values(ascending=False).index))
    gap = float(r["SVM_RBF"] - r["QSVM_ZZ"])
    claim("khoang cach RBF - ZZ", "05_results.tex", "better still, by $0.078$",
          gap, "{:.3f}")
    check("co cau rut lai khang dinh +6.7 diem",
          says("05_results.tex", "we withdraw the number")
          and says("01_introduction.tex", "is withdrawn"),
          "phai giu ca hai cho")


def section_unsw() -> None:
    print("\nF. Muc V-F -- chuyen sang UNSW-NB15")
    u = json.load(open(UNSW / "c4_revision/u1_c1_selection_unsw.json"))
    claim("UNSW n*", "05_results.tex", "returns $n^\\ast=6$",
          float(u["selected_n"]), "{:.0f}")
    claim("UNSW V", "05_results.tex", "$V=0.9044$",
          float(u["selected_variance"]), "{:.4f}")
    claim("UNSW KTA", "05_results.tex", "$\\mathrm{KTA}=0.1986$",
          float(u["selected_kta"]), "{:.4f}")
    claim("UNSW so cong hai qubit", "05_results.tex", "and $60$ two-qubit gates",
          float(u["selected_cnot_total"]), "{:.0f}")
    rb = u["robustness_10_subsets"]["n_star_by_eps"]
    check("10/10 tai eps 0.02 va 0.05, 7/10 tai 0.1",
          rb["0.02"].get("6") == 10 and rb["0.05"].get("6") == 10
          and rb["0.1"].get("6") == 7, json.dumps(rb))

    su = pd.read_csv(UNSW / "c4_revision/c4_pairwise_statistics_natural.csv")
    su["test_split"] = su.test_split.replace({"full_test_set": "full_test"})
    su = su[(su.arm == "tuned_per_N") & (su.test_split == "full_test")
            & (su.n_train == 10000)].set_index("baseline")
    claim("UNSW vs SVM-RBF", "05_results.tex", "($+0.0401$",
          float(su.loc["SVM_RBF"].mean_delta), "{:+.4f}")
    claim("UNSW vs Z", "05_results.tex", "($+0.0449$",
          float(su.loc["QSVM_Z"].mean_delta), "{:+.4f}")
    claim("UNSW vs XGBoost", "05_results.tex", "($-0.0204$ at $N=10^4$",
          float(su.loc["XGBoost"].mean_delta), "{:+.4f}")
    sall = pd.read_csv(UNSW / "c4_revision/c4_pairwise_statistics_natural.csv")
    sall["test_split"] = sall.test_split.replace({"full_test_set": "full_test"})
    sall = sall[(sall.arm == "tuned_per_N") & (sall.test_split == "full_test")]
    tree = sall[sall.baseline.isin(["XGBoost", "RandomForest"])]
    check("UNSW: khong doi dau voi ensemble cay o bat ky N nao",
          (tree.mean_delta < 0).all(), f"{(tree.mean_delta >= 0).sum()} o duong")


def section_width() -> None:
    print("\nG. Muc V-G -- be rong mach")
    v = pd.read_csv(NSL / "c4_revision/variant_K80n8/"
                          "c4_pairwise_statistics_natural.csv")
    check("48/48 classical-favorable",
          len(v) == 48 and (v.verdict == "classical-favorable").all()
          and says("05_results.tex", "produces $48$ paired comparisons"),
          f"{len(v)} o, {(v.verdict == 'classical-favorable').sum()} classical")
    z = v[v.baseline == "QSVM_Z"]
    check("ZZ tut duoi Z o MOI co N", (z.mean_delta < 0).all(),
          f"{(z.mean_delta >= 0).sum()} o khong am")
    check("bien do 0.082 .. 0.171",
          says("05_results.tex", "by $0.082$ to $0.171$")
          and abs(abs(z.mean_delta).min() - 0.0824) < 5e-4
          and abs(abs(z.mean_delta).max() - 0.1705) < 5e-4,
          f"{abs(z.mean_delta).min():.4f} .. {abs(z.mean_delta).max():.4f}")

    c = json.load(open(NSL / "c1_revision/c1_gram_concentration.json"))
    claim("alpha ZZ tai K=20", "05_results.tex",
          "$\\alpha_{\\ZZ}=0.590$", c["20"]["ZZ"]["alpha"], "{:.3f}")
    claim("alpha Z tai K=20", "05_results.tex",
          "$\\alpha_{\\Zmap}=0.292$", c["20"]["Z"]["alpha"], "{:.3f}")
    claim("ty le alpha", "05_results.tex", "a ratio of $2.02$",
          c["20"]["alpha_ratio"], "{:.2f}")
    claim("ZZ mat do trai tai K=80", "05_results.tex",
          "loses $49\\%$", c["80"]["ZZ"]["loss_4_to_10"] * 100, "{:.0f}")
    claim("Z mat do trai tai K=80", "05_results.tex",
          "against $18\\%$", c["80"]["Z"]["loss_4_to_10"] * 100, "{:.0f}")

    w = pd.read_csv(NSL / "c1_revision/c1_width_sweep.csv")
    g = w.groupby(["kernel", "n"]).agg(f1=("f1_macro", "mean"),
                                       sd=("offdiag_std", "mean")).reset_index()
    for k, txt, fmt in (("ZZ", "$r=+0.77$", "{:.2f}"),
                        ("Z", "$r=+0.32$", "{:.2f}")):
        a = g[g.kernel == k]
        r = float(np.corrcoef(a.f1, a.sd)[0, 1])
        claim(f"tuong quan do trai-F1 ({k})", "05_results.tex", txt, r, fmt)


def section_map() -> None:
    print("\nH. Muc VI -- ban do che do")
    rm = pd.read_csv(NSL / "regime_map_rows.csv")
    vc = rm.verdict.value_counts().to_dict()
    check("21 / 21 / 68 tren 110",
          len(rm) == 110 and vc["QSVM-favorable"] == 21
          and vc["classical-favorable"] == 21 and vc["inconclusive"] == 68,
          f"{len(rm)} dong, {vc}")
    for where in ("01_introduction.tex", "06_regimemap.tex",
                  "08_conclusion.tex", "main_revision.tex"):
        check(f"con so 21/21/68 xuat hien trong {where}",
              "21" in TEXT[where] and "68" in TEXT[where],
              "ban do phai duoc ke DU ca ba nhom, khong chi ke 21 thang")

    sig = rm[(rm.verdict != "inconclusive") & (rm.metric != "slope_advantage")]
    inc = rm[(rm.verdict == "inconclusive") & (rm.metric != "slope_advantage")]
    claim("|delta| nho nhat con ket luan duoc", "06_regimemap.tex",
          "anywhere in the map is $0.010$", float(sig.estimate.abs().min()),
          "{:.3f}")
    claim("|delta| lon nhat van khong ket luan", "06_regimemap.tex",
          "as large as\n$0.031$", float(inc.estimate.abs().max()), "{:.3f}")
    claim("trung vi o khong ket luan", "06_regimemap.tex",
          "inconclusive cell sits at $0.014$",
          float(inc.estimate.abs().median()), "{:.3f}")

    lo = nsl_c4()
    small = lo[(lo.n_train <= 500)
               & (lo.baseline.isin(["XGBoost", "RandomForest"]))]
    check("N<=500: thua ca hai ensemble cay o moi co",
          (small.verdict == "classical-favorable").all()
          and says("06_regimemap.tex", "by up to $0.081$"),
          f"{(small.verdict != 'classical-favorable').sum()} o khong phai")


def section_lemma() -> None:
    """Phu luc A -- he so 1 va 1/4 phai la so tinh duoc, khong phai so go tay."""
    print("\nI. Phu luc A -- Lemma 1")
    sys.path.insert(0, str(ROOT))
    from src.c4_pipeline import (compute_statevectors_fast,
                                 gram_from_statevectors)

    def fit(n_q: int, reps: int, seed: int, eps: float = 1e-3):
        g = np.random.default_rng(seed)
        base = g.uniform(0.4, np.pi - 0.4, n_q)
        A, y = [], []
        for _ in range(150):
            u = g.normal(size=n_q)
            u /= np.linalg.norm(u)
            xp = base + eps * u
            psi = compute_statevectors_fast(np.vstack([base, xp]), "ZZ",
                                            n_q, reps)
            k = float(gram_from_statevectors(psi)[0, 1])
            d = base - xp
            pair = sum((2 * (np.pi - base[i]) * (np.pi - base[j])
                        - 2 * (np.pi - xp[i]) * (np.pi - xp[j])) ** 2
                       for i in range(n_q) for j in range(i + 1, n_q))
            A.append([float(np.sum(d ** 2)), pair])
            y.append(1 - k)
        A, y = np.array(A), np.array(y)
        c, *_ = np.linalg.lstsq(A, y, rcond=None)
        r2 = 1 - np.sum((y - A @ c) ** 2) / np.sum((y - y.mean()) ** 2)
        return c, float(r2)

    # Khop bang sai phan huu han nen chu so thu tu dao dong theo diem goc;
    # bai viet ghi 3 chu so, va o day kiem bang dung sai chu khong bang chuoi.
    c, r2 = fit(4, 1, 2026)
    check("he so don le tai r=1 bang 1.000",
          abs(c[0] - 1.0) < 1e-3 and says("appendix_lemma.tex", "$a=1.000$"),
          f"a = {c[0]:.4f}")
    check("he so cap tai r=1 bang 0.250",
          abs(c[1] - 0.25) < 1e-3 and says("appendix_lemma.tex", "$b=0.250$"),
          f"b = {c[1]:.4f}")
    check("R^2 = 1.000000 tai r=1",
          round(r2, 6) == 1.0 and says("appendix_lemma.tex", "$R^{2}=1.000000$"),
          f"R^2 = {r2:.6f}")

    _, r2b = fit(4, 2, 1)
    check("r=2: dang hai so hang KHONG khop (0.60--0.94)",
          0.60 <= r2b <= 0.94
          and (says("*", "$R^{2}=0.60$ to $0.94$")
               or says("*", "$R^2=0.60$--$0.94$")), f"R^2 = {r2b:.4f}")
    check("erratum liet ke DU 4 muc",
          says("theory_revision.tex", "Four defects")
          and all(f"\\textbf{{({r})" in TEXT["theory_revision.tex"]
                  for r in ("i", "ii", "iii", "iv")),
          "muc (iii) la cai khong reviewer nao bat")
    check("Lemma khong con dung he so r^2",
          "r^2\\sum" not in TEXT["theory_revision.tex"].replace(" ", "")
          or says("theory_revision.tex", "had incorrect coefficients"),
          "phai chi con xuat hien trong phan erratum")


def section_letter() -> None:
    """Thu phan hoi gui reviewer -- moi con so trong do cung phai doi chieu duoc.

    Day la tai lieu reviewer doc KY nhat, va la cho duy nhat ta tu khai loi.
    Mot con so lech trong thu con hai hon lech trong bai.
    """
    print("\nJ. Thu phan hoi diem-theo-diem")
    L = "response_letter.tex"
    if L not in TEXT:
        check("co file thu phan hoi", False, "chua tao")
        return

    # R1-8: bang tach hai nguon chenh lech Table IV vs Table VI
    t = pd.read_csv(NSL / "c4_revision/c4_table_iv_vs_vi.csv")
    t = t.set_index(["repr_mode", "test_split"])
    cells = [("frozen_c1", "fixed_300", "QSVM_ZZ"),
             ("frozen_c1", "fixed_300", "XGBoost"),
             ("frozen_c1", "full_kddtest_plus", "QSVM_ZZ"),
             ("frozen_c1", "full_kddtest_plus", "XGBoost"),
             ("refit_per_N", "fixed_300", "QSVM_ZZ"),
             ("refit_per_N", "fixed_300", "XGBoost"),
             ("refit_per_N", "full_kddtest_plus", "QSVM_ZZ"),
             ("refit_per_N", "full_kddtest_plus", "XGBoost")]
    bad = [f"{r}/{s}/{m}" for r, s, m in cells
           if f"{t.loc[(r, s), m]:.4f}" not in TEXT[L]]
    check("R1-8: ca 8 o cua bang trong thu khop artifact", not bad, str(bad))
    d_split = float(t.loc[("frozen_c1", "fixed_300"), "QSVM_ZZ"]
                    - t.loc[("frozen_c1", "full_kddtest_plus"), "QSVM_ZZ"])
    d_repr = float(t.loc[("refit_per_N", "fixed_300"), "QSVM_ZZ"]
                   - t.loc[("frozen_c1", "fixed_300"), "QSVM_ZZ"])
    claim("R1-8: phan do tap test gay ra", L, "about $-0.051$ macro-$F_1$",
          -d_split, "{:+.3f}")
    claim("R1-8: phan do refit gay ra", L, "for about $+0.006$",
          d_repr, "{:+.3f}")

    # R1-9: giao thuc, khong phai model, giai thich F1 thap
    p = pd.read_csv(NSL / "c4_revision/c4_protocol_vs_literature.csv")
    p = p.set_index(["setup", "model"]).f1_macro
    for setup, mdl in (("A_full122_fulltrain_KDDTestPlus", "RandomForest"),
                       ("A_full122_fulltrain_KDDTestPlus", "XGBoost"),
                       ("B_full122_randomsplit_KDDTrain", "RandomForest"),
                       ("B_full122_randomsplit_KDDTrain", "XGBoost")):
        v = float(p.loc[(setup, mdl)])
        check(f"R1-9: {setup[0]} / {mdl} = {v:.4f}", f"{v:.4f}" in TEXT[L],
              f"{v:.4f}")

    # R4-5: bay gio moi co so cho lop hiem -- dung cho reviewer hoi thang
    r = pd.read_csv(NSL / "c4_revision/c4_rare_attack_natural.csv")
    r = r[r.n_train == 10000].set_index("model").f1_rare
    miss = [m for m in ("SVM_RBF", "QSVM_ZZ", "QSVM_Z", "XGBoost",
                        "RandomForest", "SVM_Poly2", "SVM_Linear")
            if f"{r[m]:.3f}" not in TEXT[L]]
    check("R4-5: ca 7 gia tri F1 lop hiem co trong thu", not miss, str(miss))

    # Nhung cho thu KHONG duoc phep noi giam nhe
    for what, phrase in (
            ("rut 5 khang dinh", "are withdrawn"),
            ("khong tai tao duoc so rare cu", "cannot be reproduced"),
            ("XGBoost dung tren QSVM", "XGBoost attains\n$0.8503$"),
            ("SVM-RBF manh hon ve rare", "SVM-RBF is better still"),
            ("khong chay tren phan cung that", "not do is execute on a quantum processor"),
            ("khong them CatBoost/TabNet", "did \\emph{not} add CatBoost"),
            ("tu khai loi Lemma", "had incorrect coefficients"),
            ("tu khai tap train giau lop hiem", "were\nrare-enriched"),
            ("thay ref [26] bang bai CO THAT", "10.3390/fi18050234"),
            ("khong nhan be rong mach la truc cua minh",
             "an axis we can claim as ours, and we no longer do"),
            ("da doc toan van ca bon bai truoc khi so sanh",
             "read all four in full before answering"),
            ("noi ro Carducci chi doc duoc abstract",
             "suggestive rather than as evidence"),
            ("noi ro cai gi KHONG xac dinh duoc ve Carducci",
             "not the qubit count nor whether")):
        check(f"thu noi thang: {what}", says(L, phrase), phrase[:40])

    # Bai hua "Sec IV-D co link repo va commit hash" -- phai co that, va hash
    # phai la mot commit CO THAT trong repo nay.
    import subprocess
    setup = TEXT.get("04_setup.tex", "")
    m = re.search(r"commit\s*\n?\\texttt\{([0-9a-f]{7,40})\}", setup)
    check("bai co ghi link repo", "github.com/anhquan1111/QSVM_NSLKDD" in setup,
          "thu khang dinh muc IV-D co link -- phai dung")
    if m:
        rc = subprocess.run(["git", "cat-file", "-e", m.group(1) + "^{commit}"],
                            cwd=ROOT, capture_output=True)
        check(f"commit hash {m.group(1)} co that trong repo", rc.returncode == 0,
              "hash go tay khong tro toi commit nao" if rc.returncode else "co")
    else:
        check("bai co ghi commit hash", False, "khong tim thay")

    # So bo audit ghi trong bai phai khop so bo audit that su co
    for name, n in (("audit\\_c4.py} (100", 100), ("audit\\_figures.py} (36", 36),
                    ("verify\\_lemma1.py} (15", 15)):
        check(f"bai ghi dung so kiem dinh cua {name.split('}')[0]}",
              name in setup, str(n))

    # Thu khang dinh da trich va ban ve Carducci -- phai co that o CA BA cho,
    # khong duoc chi hua trong thu.
    bib = io.open(ROOT / "paper/paper1/bibliography_revision.tex",
                  encoding="utf-8").read()
    check("Carducci co bibitem that",
          "bibitem{carducci2026}" in bib.replace(chr(92), ""),
          "thu noi 'cited', phai co that")
    check("Carducci duoc ban trong than bai chu khong chi trong thu",
          "carducci2026" in TEXT.get("02_background.tex", ""),
          "R4-1 doi 'discussed', khong phai chi liet ke")

    rm = pd.read_csv(NSL / "regime_map_rows.csv")
    vc = rm.verdict.value_counts()
    check("thu ke du 21/21/68 chu khong chi ke phan thang",
          all(str(v) in TEXT[L] for v in (vc["QSVM-favorable"],
                                          vc["classical-favorable"],
                                          vc["inconclusive"])),
          f"{vc.to_dict()}")
    check("thu dem dung 33 item",
          "33" in TEXT[L] and "29" in TEXT[L], "6+10+6+5+6 = 33, 29 xong + 4 mot phan")


def main() -> int:
    global OK, FAILED
    print("=" * 78)
    print("  DOI CHIEU SO LIEU TRONG THAN BAI VOI ARTIFACT")
    print("=" * 78)
    missing = [f for f in ("01_introduction.tex", "05_results.tex",
                           "06_regimemap.tex", "08_conclusion.tex")
               if f not in TEXT]
    if missing:
        print(f"  Thieu file: {missing}")
        return 1
    for fn in (section_c1, section_c2, section_c3, section_c4, section_rare,
               section_unsw, section_width, section_map, section_lemma, section_letter):
        fn()
    # Thu phan hoi trich dan chinh so kiem dinh cua script nay. Reviewer se
    # chay thu -- neu con so trong thu lech voi con so script in ra thi do
    # dung la kieu cau tha reviewer nay se bat. Nen tu doi chieu luon.
    # +1 vi chinh muc kiem nay cung duoc dem, nen con so thu trich phai la
    # tong CUOI CUNG ma script in ra.
    total = OK + FAILED + 1
    L = TEXT.get("response_letter.tex", "")
    if L:
        quoted = f"{total}/{total}"
        # Chi tinh phan than bai cua thu, khong tinh dong chu thich LaTeX,
        # neu khong thi chu thich se lam muc kiem nay tu thoa man chinh no.
        body = "\n".join(ln for ln in L.split("\n")
                         if not ln.lstrip().startswith("%"))
        if quoted in body:
            OK += 1
            print(f"\n  [PASS] thu trich dung so kiem dinh cua chinh script nay"
                  f"  --  {quoted}")
        else:
            FAILED += 1
            print(f"\n  [FAIL] thu trich sai so kiem dinh cua audit_prose"
                  f"  --  phai ghi {quoted}")

    print("\n" + "=" * 78)
    print(f"TONG: {OK}/{OK + FAILED} PASS" + (f"  ({FAILED} FAIL)" if FAILED else ""))
    print("=" * 78)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
