"""Kiem ban dung lai cua Paper 2.

    python runners/audit_p2_rebuild.py

Bon lop:
  A. Moi macro trong tables/numbers_macros.tex tinh lai duoc tu artifact.
  B. Moi macro DUNG trong bai deu duoc DINH NGHIA. Thieu lop nay thi go sai
     mot ten macro se lot -- audit xanh con LaTeX chet.
  C. Cau van khong chua so viet tay.
  D. Cac bat bien cua LAP LUAN. Day la lop quan trong nhat: no khoa dung
     nhung gi bai duoc phep va khong duoc phep claim, nen sua du lieu ma ket
     luan doi chieu thi bao ngay.
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NSL = ROOT / "results" / "nslkdd" / "p2_rebuild"
UNSW = ROOT / "results" / "unsw" / "p2_rebuild"
PAPER = ROOT / "paper" / "paper2_rebuild"
BS = chr(92)

MACRO = {"QSVM": "Qsvm", "SVM-RBF": "Rbf", "MLP": "Mlp",
         "XGBoost": "Xgb", "RandomForest": "Rf"}
SETTINGS = {"NSL-KDD/full": "Nsl", "NSL-KDD/test21": "Drift",
            "UNSW/4qb": "UnswFour", "UNSW/6qb": "UnswSix"}
TREES = ("RandomForest", "XGBoost")

_checks: list[tuple[bool, str]] = []


def check(ok, label):
    _checks.append((bool(ok), label))


def read(p):
    with io.open(p, encoding="utf-8") as f:
        return f.read()


def load_long():
    n = pd.read_csv(NSL / "p2_rebuild_per_run.csv")
    n["setting"] = "NSL-KDD/" + n.test_set.map(
        {"full_kddtest_plus": "full", "kddtest21": "test21",
         "sample100_cu": "sample100"})
    u = pd.read_csv(UNSW / "p2_unsw_per_run.csv")
    u["setting"] = "UNSW/" + u.n_qubits.astype(str) + "qb"
    return pd.concat([n, u], ignore_index=True)


# --- A -----------------------------------------------------------------
def audit_macros(m, long, st, platt, ref, cal, idf):
    nsl = long[long.setting == "NSL-KDD/full"]
    check(m["nRuns"] == str(nsl.run_id.nunique()), "nRuns")
    check(m["nRareOld"] == str(int(
        long[long.setting == "NSL-KDD/sample100"].n_rare.iloc[0])), "nRareOld")
    check(m["identityMaxDev"].startswith(f"{idf.abs_dev.max():.1e}"[:3]),
          "identityMaxDev")

    for setting, tag in SETTINGS.items():
        sub = long[long.setting == setting]
        for model, key in MACRO.items():
            s = sub[sub.model == model]
            check(m[f"{tag}{key}EceFull"] == f"{s.ece_full.mean():.4f}",
                  f"{tag}{key}EceFull")
        p = st[(st.setting == setting) & (st.metric == "ece_full")]
        for _, r in p.iterrows():
            k = MACRO[r["baseline"]]
            check(m[f"d{tag}{k}"] == f"{r['mean_delta']:+.4f}", f"d{tag}{k}")
            check(m[f"d{tag}{k}Holm"] == f"{r['holm_p']:.4f}", f"d{tag}{k}Holm")
            check(m[f"d{tag}{k}Dz"] == f"{r['dz']:+.2f}", f"d{tag}{k}Dz")

    g = ref.groupby(["repr", "model"])
    for rep, tag in (("pca4", "Pca"), ("k20", "KTwenty"), ("all122", "Full")):
        for model, key in (("RandomForest", "Rf"), ("XGBoost", "Xgb")):
            check(m[f"ref{tag}{key}EceFull"] == f"{g.ece_full.mean()[(rep, model)]:.4f}",
                  f"ref{tag}{key}EceFull")
    c = cal.groupby(["model", "calibrator"]).ece_full.mean()
    for model, key in MACRO.items():
        for cname, tag in (("none", "None"), ("platt", "Platt"),
                           ("isotonic", "Iso"), ("temperature", "Temp")):
            check(m[f"cal{key}{tag}"] == f"{c[(model, cname)]:.4f}", f"cal{key}{tag}")
        pl = platt[platt.model == model]
        check(m[f"{key}PlattDelta"] == f"{pl.delta.mean():+.4f}", f"{key}PlattDelta")


# --- B -----------------------------------------------------------------
def audit_macros_defined(tex, m):
    latex_p = {"paragraph", "pm", "pi", "par", "pageref", "protect",
               "printindex", "pounds", "pagestyle", "pagenumbering",
               "phi", "psi", "prod", "partial", "perp", "propto", "pmod"}
    used = {name[1:] for name in re.findall(BS + BS + r"(p[A-Za-z]+)", tex)
            if name not in latex_p}
    missing = sorted(used - set(m))
    check(not missing, f"moi macro dung trong bai deu duoc dinh nghia "
                       f"(thieu: {missing})")


# --- C -----------------------------------------------------------------
NUMBER_WHITELIST = {
    "0", "1", "2", "4", "5",
    "0.0625",   # p nho nhat Wilcoxon dat duoc voi 5 cap -- hang so toan hoc
    "0.05",     # muc y nghia alpha
    "0.01", "0.99",  # nguong DINH NGHIA "bao hoa" -- tham so cua phep do,
                     # khong phai ket qua do duoc
}


def audit_prose_numbers(tex):
    body = re.sub(r"(?<!" + BS + BS + r")%.*", "", tex)
    body = body.split(BS + "maketitle", 1)[-1]
    body = body.split(BS + "begin{thebibliography}", 1)[0]
    body = re.sub(BS + BS + r"includegraphics(\[[^\]]*\])?\{[^}]*\}", " ", body)
    # `\ding{55}` la ma ky hieu pifont, khong phai so lieu -- bo cung voi cac
    # lenh khac truoc khi quet so.
    body = re.sub(BS + BS + r"(label|ref|eqref|input|url|newcommand|cite|ding)"
                  r"\{[^}]*\}", " ", body)
    # Ten rieng co chu so (KDDTest-21, UNSW-NB15, ...) khong phai so lieu.
    # Bo chung truoc khi quet, thay vi noi long danh sach so duoc phep.
    # `T2026-02-10TN` la ma de tai va `0009-...` la ORCID: dinh danh, khong
    # phai so do duoc. Bo chung o day chu KHONG them vao NUMBER_WHITELIST --
    # noi long danh sach so duoc phep se lam ca phep kiem yeu di.
    for name in ("KDDTest-21", "UNSW-NB15", "NSL-KDD", "KDDTest+",
                 "KDD'99", "MilCIS", "T2026-02-10TN", "0009-0000-9420-1767"):
        body = body.replace(name, " ")
    bad = [t for t in re.findall(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])", body)
           if t not in NUMBER_WHITELIST]
    check(not bad, f"khong co so viet tay trong cau van (thay: {sorted(set(bad))})")


# --- D -----------------------------------------------------------------
def audit_invariants(long, st, platt, ref, cal, idf):
    nsl = long[long.setting == "NSL-KDD/full"]
    old = long[long.setting == "NSL-KDD/sample100"]

    check(nsl.run_id.nunique() == 10, "du 10 run")
    check(nsl.n_rare.iloc[0] > 100 * old.n_rare.iloc[0],
          "tap test day du co nhieu hon 100 lan mau hiem")
    check(stats.wilcoxon(np.arange(1., 6.)).pvalue > 0.05,
          "5 cap: Wilcoxon khong the dat p<0.05")
    check(stats.wilcoxon(np.arange(1., 11.)).pvalue < 0.05,
          "10 cap: Wilcoxon dat duoc p<0.05")

    # Dang thuc suy bien -- luan diem phuong phap cua bai.
    check(idf.abs_dev.max() < 1e-12,
          f"ECE_rare == 1-mean(p) (lech max {idf.abs_dev.max():.1e})")
    check(idf.acc_bin_std.min() > 0.05,
          "ECE tren toan tap test KHONG suy bien (acc tung bin bien thien)")

    # Luan diem chinh: thang CA HAI mo hinh cay o MOI thiet lap, sau Holm.
    e = st[st.metric == "ece_full"]
    for setting in SETTINGS:
        s = e[e.setting == setting].set_index("baseline")
        for b in TREES:
            check(s.loc[b, "holm_p"] < 0.05 and s.loc[b, "mean_delta"] < 0,
                  f"{setting}: QSVM thang {b} sau Holm")
        # Luan diem KHONG duoc claim: thang MLP.
        check(not (s.loc["MLP", "holm_p"] < 0.05
                   and s.loc["MLP", "mean_delta"] < 0),
              f"{setting}: bai KHONG duoc claim thang MLP")

    # Nhanh doi chung: du dac trung thi xep hang tot len, hieu chinh te di.
    g = ref.groupby(["repr", "model"])
    for model in TREES:
        check(g.ece_full.mean()[("all122", model)]
              > g.ece_full.mean()[("pca4", model)],
              f"{model}: 122 dac trung hieu chinh TE hon PCA-4")
    check(g.auc_pr.mean()[("all122", "RandomForest")]
          > g.auc_pr.mean()[("pca4", "RandomForest")],
          "RandomForest: 122 dac trung xep hang TOT hon PCA-4")

    # Hieu chinh hau ky chi giup kernel luong tu.
    c = cal.groupby(["model", "calibrator"]).ece_full.mean()
    for model in TREES:
        for cname in ("platt", "isotonic", "temperature"):
            check(c[(model, cname)] > c[(model, "none")],
                  f"{model}: {cname} lam XAU hon khong hieu chinh")
    for cname in ("platt", "isotonic", "temperature"):
        check(c[("QSVM", cname)] < c[("QSVM", "none")],
              f"QSVM: {cname} lam TOT hon khong hieu chinh")
    d = platt.groupby("model").delta.mean()
    check(sorted(d[d > 0].index) == ["QSVM"],
          f"Platt chi giup QSVM (thuc te: {sorted(d[d > 0].index)})")


def audit_percat(m, pc, cv):
    """Cac luan diem moi: do tu tin theo nhom, va duoi-tu-tin."""
    g = pc.groupby(["category", "model"]).mean_prob.mean()
    for cat, tag in (("Normal", "Normal"), ("DoS", "Dos"), ("Probe", "Probe"),
                     ("R2L", "RtoL"), ("U2R", "UtoR")):
        for model, key in MACRO.items():
            check(m[f"cat{tag}{key}"] == f"{g[(cat, model)]:.4f}",
                  f"cat{tag}{key}")

    # Bai claim: QSVM tu tin nhat tren U2R. Neu doi chieu thi phai bao.
    check(g["U2R"].idxmax() == "QSVM",
          f"QSVM tu tin nhat tren U2R (thuc te: {g['U2R'].idxmax()})")
    # Bai claim: QSVM YEU NHAT tren Probe -- mot ket qua am, phai giu.
    check(g["Probe"].idxmin() == "QSVM",
          f"QSVM yeu nhat tren Probe (thuc te: {g['Probe'].idxmin()})")
    # Bai claim: MOI mo hinh deu duoi nguong 0.5 tren ca hai nhom hiem.
    below = [(c, mo) for c in ("R2L", "U2R") for mo in MACRO
             if g[(c, mo)] >= 0.5]
    check(not below, f"moi mo hinh duoi nguong 0.5 tren R2L va U2R "
                     f"(vuot: {below})")

    # Bai claim: MOI mo hinh deu DUOI-tu-tin, tuc acc > conf o da so bin.
    gc = cv.groupby(["model", "bin"])[["conf", "acc"]].mean()
    nb = cv.bin.nunique()
    for model in MACRO:
        s = gc.loc[model]
        n_under = int((s.acc > s.conf).sum())
        check(n_under > nb / 2,
              f"{model} duoi-tu-tin ({n_under}/{nb} bin tren duong cheo)")


def audit_census(m, st):
    """Kiem dem toan bo so sanh, va hai claim manh rut ra tu no.

    `ece_rare` bi loai khoi kiem dem: muc III chung minh no bang dung
    1 - p_bar tren tap mot lop va KHONG phai sai so hieu chinh, nen dem no
    vao bang tong la bai tu mau thuan. `brier_rare` o lai.
    """
    cen = st[(st.setting != "NSL-KDD/sample100")
             & (st.metric != "ece_rare")]
    vc = cen.verdict.value_counts()
    check(m["cenTotal"] == str(len(cen)), "cenTotal")
    check(m["cenQsvm"] == str(int(vc.get("QSVM-favorable", 0))), "cenQsvm")
    check(m["cenBase"] == str(int(vc.get("baseline-favorable", 0))), "cenBase")
    check(m["cenIncon"] == str(int(vc.get("inconclusive", 0))), "cenIncon")

    # Bai khang dinh: QSVM KHONG THANG mot so sanh xep hang nao. Day la mot
    # ket qua am ma bai tu nguyen bao cao, nen phai khoa lai.
    rank = cen[cen.metric.isin(["auc_pr", "f1"])]
    check((rank.verdict == "QSVM-favorable").sum() == 0,
          f"QSVM khong thang so sanh xep hang nao "
          f"(thuc te: {(rank.verdict == 'QSVM-favorable').sum()})")

    # Va: loi the cua no nam o calibration. Neu ti le nay tut ve gan 0 thi
    # cau chuyen cua bai sai.
    cal2 = cen[cen.metric.isin(["ece_full", "brier_full"])]
    n_win = int((cal2.verdict == "QSVM-favorable").sum())
    check(n_win >= len(cal2) // 3,
          f"loi the cua QSVM nam o calibration ({n_win}/{len(cal2)})")

    # LOP D. Ban truoc cong bo tong 96 roi chi tach hai ho 32+32=64: ba
    # muoi hai so sanh khong duoc goi ten, va chung chua 15 trong 31 lan
    # thang cua QSVM. Nguoi doc cong lai la thay. Tu gio ba ho phai phu
    # KIN kiem dem, va tung con so phai khop artifact.
    fams = {"Cal": ["ece_full", "brier_full"],
            "Rank": ["auc_pr", "f1"],
            "Rare": ["brier_rare"]}
    covered = 0
    for tag, metrics in fams.items():
        sub = cen[cen.metric.isin(metrics)]
        covered += len(sub)
        check(m[f"cen{tag}Total"] == str(len(sub)), f"cen{tag}Total")
        check(m[f"cen{tag}Qsvm"]
              == str(int((sub.verdict == "QSVM-favorable").sum())),
              f"cen{tag}Qsvm")
    check(covered == len(cen),
          f"ba ho phu kin kiem dem ({covered}/{len(cen)}) -- neu lech thi "
          f"co metric khong duoc goi ten trong muc VI-A")
    check(sum(int(m[f"cen{t}Qsvm"]) for t in fams) == int(m["cenQsvm"]),
          "tong thang ba ho = cenQsvm")
    check(m["cenDropped"] == str(len(
        st[(st.setting != "NSL-KDD/sample100")
           & (st.metric == "ece_rare")])), "cenDropped")


def audit_caltests(m, ct):
    """Phep kiem bat cap cho ba bo hieu chinh, va claim rut ra tu no.

    Lop D cho mot cau tung SAI: muc dong gop viet "giup kernel luong tu va
    HAI moi mo hinh con lai". Temperature scaling ha ECE trung binh cua
    SVM-RBF tu 0,1171 xuong 0,1140 -- tuc la khong hai -- nhung chi thang
    5/10 run (Holm = 1,00), nen no khong "giup" ma cung khong "hai". Bai gio
    noi dung ba the, va day la cho khoa no lai.
    """
    for model, key in MACRO.items():
        g = ct[ct.model == model]
        check(m[f"ctest{key}"] == g.overall.iloc[0], f"ctest{key}")
        # DAU: macro theo quy uoc "cai thien" (duong = tot len), artifact
        # theo quy uoc "sau - truoc". Sai dau o day thi ca doan van doc
        # nguoc y nghia ma van khop tung chu so.
        check(m[f"ctest{key}Best"] == f"{-g.mean_delta.min():+.4f}",
              f"ctest{key}Best dao dau dung")
        check(m[f"ctest{key}Worst"] == f"{-g.mean_delta.max():+.4f}",
              f"ctest{key}Worst dao dau dung")
        for cname, tag in (("platt", "Platt"), ("isotonic", "Iso"),
                           ("temperature", "Temp")):
            r = g[g.calibrator == cname].iloc[0]
            check(m[f"ctest{key}{tag}D"] == f"{-r.mean_delta:+.4f}",
                  f"ctest{key}{tag}D")
            check(m[f"ctest{key}{tag}N"]
                  == f"{int(r.n_better)}/{int(r.n_runs)}",
                  f"ctest{key}{tag}N")
            # The cua tung bo phai nhat quan voi the chung cua mo hinh.
            want = ("helps" if (r.holm_p < 0.05 and r.mean_delta < 0)
                    else "hurts" if r.holm_p < 0.05 else "no effect")
            check(g.overall.iloc[0] in (want, "no effect"),
                  f"the chung cua {key} khong mau thuan voi {tag}")

    # Ba claim cua bai, doc thang tu artifact.
    ov = ct.groupby("model").overall.first()
    check(ov["QSVM"] == "helps", "QSVM duoc hieu chinh giup")
    check(all(ov[b] == "hurts" for b in (*TREES, "MLP")),
          "MLP va ca hai cay deu bi hieu chinh lam hai")
    check(ov["SVM-RBF"] == "no effect",
          "SVM-RBF la mot KET QUA RONG, bai khong duoc noi la no bi hai")
    # Khong mo hinh nao ngoai QSVM duoc giup -- cau "helps the quantum
    # kernel and no other model" nam o abstract va o ket luan.
    check(sum(v == "helps" for v in ov) == 1,
          "dung mot mo hinh duoc hieu chinh giup")
    # Va cau "in every run": moi bo hieu chinh phai thang du 10/10.
    q = ct[ct.model == "QSVM"]
    check((q.n_better == q.n_runs).all(),
          "ca ba bo hieu chinh giup QSVM o MOI run")
    h = ct[ct.model.isin([*TREES, "MLP"])]
    check((h.n_better == 0).all(),
          "khong bo hieu chinh nao giup MLP hay cay o bat ky run nao")


def audit_regime(long, st):
    """Ban do che do: QSVM phai thang ca hai cay o MOI dieu kien."""
    e = st[st.metric == "ece_full"]
    for setting in SETTINGS:
        s = e[e.setting == setting].set_index("baseline")
        for b in TREES:
            check(s.loc[b, "verdict"] == "QSVM-favorable",
                  f"ban do: {setting} vs {b}")
    ld = pd.read_csv(NSL / "p2_rebuild_lowdata.csv")
    for n, sub in ld.groupby("n_train"):
        g = sub.groupby("model").ece_full.mean()
        for b in TREES:
            check(g["QSVM"] < g[b], f"ban do: N={int(n)} vs {b}")
    ps = pd.read_csv(NSL / "p2_rebuild_priorshift.csv")
    for mix, sub in ps.groupby("mix"):
        g = sub.groupby("model").ece_full.mean()
        for b in TREES:
            check(g["QSVM"] < g[b], f"ban do: {mix} vs {b}")


def main() -> int:
    long = load_long()
    st = pd.read_csv(NSL / "p2_rebuild_pairwise.csv")
    platt = pd.read_csv(NSL / "p2_rebuild_platt.csv")
    ref = pd.read_csv(NSL / "p2_rebuild_refarm.csv")
    cal = pd.read_csv(NSL / "p2_rebuild_calibrators.csv")
    idf = pd.read_csv(NSL / "p2_rebuild_identity.csv")
    m = dict(re.findall(BS + BS + r"newcommand\{" + BS + BS + r"p(\w+)\}\{([^}]*)\}",
                        read(PAPER / "tables" / "numbers_macros.tex")))

    tex = read(PAPER / "main.tex") + read(PAPER / "tables" / "main_table.tex")
    audit_macros(m, long, st, platt, ref, cal, idf)
    audit_macros_defined(tex, m)
    audit_prose_numbers(read(PAPER / "main.tex"))
    audit_invariants(long, st, platt, ref, cal, idf)
    audit_percat(m, pd.read_csv(NSL / "p2_rebuild_percat.csv"),
                 pd.read_csv(NSL / "p2_rebuild_curve.csv"))
    audit_census(m, st)
    audit_caltests(m, pd.read_csv(NSL / "p2_rebuild_cal_tests.csv"))
    audit_regime(long, st)

    # TU KIEM: moi ham audit_* dinh nghia trong file nay PHAI duoc goi o day.
    #
    # Da xay ra that: audit_percat, audit_census va audit_regime nam trong
    # file suot may lan sua ma khong he duoc goi -- mot patch noi day chung
    # vao main() truot am tham, va audit van bao xanh. Nhung luan diem tuong
    # ung coi nhu chua bao gio duoc kiem. Mot bo kiem co ham chet thi te hon
    # khong co bo kiem, vi no tao cam giac an toan gia.
    src = read(Path(__file__))
    defined = set(re.findall(r"^def (audit_\w+)", src, re.M))
    called = set(re.findall(r"^    (audit_\w+)\(", src, re.M))
    dead = sorted(defined - called)
    check(not dead, f"khong co ham audit_* nao la ma chet (chet: {dead})")

    figs = ["fig1_identity", "fig2_paired", "fig3_platt", "fig4_refarm",
            "fig5_reliability", "fig6_threshold"]
    for rel in [f"figs/{f}.pdf" for f in figs] + ["tables/main_table.tex",
                                                  "tables/side_tables.tex",
                                                  "tables/percat_table.tex",
                                                  "tables/regime_table.tex",
                                                  "main.tex"]:
        check((PAPER / rel).exists(), f"co {rel}")
    # Hinh sinh ra ma khong duoc chen vao bai thi coi nhu khong ton tai --
    # da xay ra that voi fig1_identity, hinh cua chinh luan diem trung tam.
    body = read(PAPER / "main.tex")
    for f in figs:
        check(f"figs/{f}.pdf" in body, f"bai co chen {f}")

    # Nam tuyen bo bat buoc cua Wiley. Thieu mot cai la ban thao bi tra lai
    # o vong bien tap, truoc khi co ai doc toi phuong phap.
    for sec in ("Author Contributions", "Funding", "Data Availability",
                "Conflict of Interest", "Ethics Statement",
                "Use of AI Tools"):
        check(f"section*{{{sec}" in body, f"co muc {sec}")

    # O xac nhan luc nop doi khai dung cong cu AI NGAY TRONG BAI, khong chi
    # tick o. Tick ma bai khong co doan khai la ky vao mot dieu khong dung.
    # Doan khai phai neu TEN cong cu -- "an AI tool" chung chung khong dat.
    check("Claude" in body and "Anthropic" in body,
          "khai bao AI co neu ten cong cu")
    check("not an author" in body,
          "khai bao AI noi ro cong cu khong phai tac gia")

    # Muc Data Availability phai tro toi mot DOI THAT. Doan van do la thu
    # bien tap doc dau tien, va mot placeholder lot ra ban nop thi khong ai
    # doc lai ma thay. `\url{}` duoc loai khoi phep quet so viet tay nen
    # khong co gi khac bat duoc cho nay.
    check("doi.org/10.5281/zenodo." in body,
          "Data Availability tro toi DOI Zenodo")
    check("XXXX" not in body and "zenodo.XXX" not in body,
          "khong con placeholder trong bai")

    n_ok = sum(1 for ok, _ in _checks if ok)
    for ok, label in _checks:
        if not ok:
            print(f"  LOI   {label}")
    print(f"\n  audit_p2_rebuild  {n_ok}/{len(_checks)}")
    return 0 if n_ok == len(_checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
