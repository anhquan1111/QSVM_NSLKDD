"""Kiem bai hoi nghi AICON 2026 (paper 3).

Chay:  python runners/audit_paper3.py

Bai nay lap luan rang nhung con so khong duoc kiem se danh lua nguoi doc. Vay
thi chinh no phai chiu dung tieu chuan do: MOI con so trong cau van phai doc
nguoc duoc ve artifact.

Ba lop kiem:

  A. Moi macro trong tables/numbers_macros.tex tinh lai duoc tu artifact.
  B. Cau van khong chua so thap phan viet tay -- moi so phai di qua macro.
  C. Cac bat bien cua lap luan van con dung (vd: diem CV tot nhat khong suy
     bien cua kernel luong tu phai THAP HON nguong san, neu khong thi ca cau
     chuyen sup).
"""

from __future__ import annotations

import io
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper" / "paper3_aicon"
BS = chr(92)

_checks: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> None:
    _checks.append((bool(ok), label))


def load(rel: str) -> dict:
    with io.open(ROOT / rel, encoding="utf-8") as f:
        return json.load(f)


def read(p: Path) -> str:
    with io.open(p, encoding="utf-8") as f:
        return f.read()


def parse_macros(text: str) -> dict[str, str]:
    return dict(re.findall(
        BS + BS + r"newcommand\{" + BS + BS + r"p(\w+)\}\{([^}]*)\}", text))


def strip_comments(text: str) -> str:
    """Bo phan sau dau % chua escape, va bo ca khoi thebibliography."""
    text = re.sub(r"(?<!" + BS + BS + r")%.*", "", text)
    return text


# --------------------------------------------------------------------------
# A. Macro khop artifact
# --------------------------------------------------------------------------
def audit_macros(m: dict[str, str]) -> None:
    tune = load("results/unsw/c_tuning_results.json")
    deg = load("results/unsw/c3_results_statevector.json")["summary"]["quantum"]
    per = load("results/unsw/c3_results_statevector.json")["per_run"]
    c1j = load("results/unsw/c3_results_statevector_C1.json")
    neu = c1j["summary"]["quantum"]
    cmp4a = c1j["comparison_vs_1_4a"]
    cmp15 = load("results/unsw/c4_results_C1.json")["comparison_vs_1_5"]
    c1 = load("results/unsw/c1_results.json")

    floor = next(r["mean"] for r in tune["quantum"]["scores_per_C"] if r["C"] == 0.01)
    check(m["degFloor"] == f"{floor:.4f}", "degFloor")
    check(m["degFloorFull"] == f"{floor:.16f}", "degFloorFull")
    check(m["selectedC"] == f"{tune['quantum']['C_best']:g}", "selectedC")
    check(m["cvFolds"] == str(tune["metadata"]["n_folds"]), "cvFolds")
    check(m["cvScoring"] == tune["metadata"]["scoring"], "cvScoring")
    check(m["cGrid"] == ", ".join(f"{c:g}" for c in tune["quantum"]["grid"]), "cGrid")

    qbest = max(r["mean"] for r in tune["quantum"]["scores_per_C"] if r["C"] > 0.1)
    check(m["qBestNonDeg"] == f"{qbest:.4f}", "qBestNonDeg")

    check(m["degRecall"] == f"{deg['recall_mean']:.3f}", "degRecall")
    check(m["degRecallStd"] == f"{deg['recall_std']:.0f}", "degRecallStd")
    check(m["degPrecision"] == f"{deg['precision_mean']:.3f}", "degPrecision")
    check(m["degFone"] == f"{deg['f1_mean']:.4f}", "degFone")
    check(m["degTN"] == f"{cmp4a['tn_mean_old']['quantum']:.1f}", "degTN")

    check(m["neuRecall"] == f"{neu['recall_mean']:.3f}", "neuRecall")
    check(m["neuPrecision"] == f"{neu['precision_mean']:.3f}", "neuPrecision")
    check(m["neuFone"] == f"{neu['f1_mean']:.4f}", "neuFone")
    check(m["neuTN"] == f"{cmp4a['tn_mean_new']['quantum']:.1f}", "neuTN")

    check(m["ktaShared"] == f"{deg['kta_mean']:.6f}", "ktaShared")
    check(m["ktaSharedFull"] == repr(deg["kta_mean"]), "ktaSharedFull")

    check(m["perturbRangeOld"] == f"{cmp15['qsvm_perturb_range_old']:.3f}",
          "perturbRangeOld")
    check(m["perturbRangeNew"] == f"{cmp15['qsvm_perturb_range_new']:.4f}",
          "perturbRangeNew")

    ks = sorted(c1["k_sweep"], key=lambda e: e["K"])
    pf1 = ks[-1]["summary"]["quantum"]["f1_mean"]
    pks = [e["K"] for e in ks
           if abs(e["summary"]["quantum"]["f1_mean"] - pf1) < 1e-15]
    check(m["kPlateauFone"] == f"{pf1:.4f}", "kPlateauFone")
    check(m["kPlateauFrom"] == str(min(pks)), "kPlateauFrom")
    check(m["kSweepRuns"] == str(sum(len(e["per_run"]) for e in ks)), "kSweepRuns")
    check(m["kSweepDeg"] == str(sum(1 for e in ks for r in e["per_run"]
                                    if r["quantum"]["is_degenerate"])), "kSweepDeg")

    check(m["legacySeeds"] == str(len(per)), "legacySeeds")
    check(m["legacyQubits"] == str(load(
        "results/unsw/c3_results_statevector.json")["metadata"]["n_qubits"]),
        "legacyQubits")

    tot = load("results/unsw/paper3/degeneracy_totals.json")
    check(m["revRowsScanned"] == str(tot["n_rows_scanned"]), "revRowsScanned")
    check(m["revModels"] == str(tot["n_models"]), "revModels")
    check(m["revDegRows"] == str(tot["n_degenerate_rows"]), "revDegRows")
    check(m["revQsvmMinRecall"] == f"{tot['qsvm_zz_min_recall_macro']:.3f}",
          "revQsvmMinRecall")

    rev = pd.read_csv(ROOT / "results/unsw/c4_revision"
                      / "c4_per_run_unsw_natural_refit_per_N.csv")
    check(m["revMaxN"] == "{:,}".format(int(rev.n_train.max())).replace(",", BS + ","),
          "revMaxN")
    check(m["revRuns"] == str(int(rev.run_id.nunique())), "revRuns")


# --------------------------------------------------------------------------
# B. Cau van khong chua so viet tay
# --------------------------------------------------------------------------
# Nhung so duoc phep xuat hien trong cau van: chi so mu, so thu tu mac dinh
# cua LaTeX, va cac hang so cau truc cua bai (10^4, 0.1, 1, 0.5 trong the
# grid da noi bang macro). Danh sach nay phai NGAN -- moi lan them mot muc la
# mot lan noi long tieu chuan, nen phai co ly do.
NUMBER_WHITELIST = {
    "0.1",    # gia tri C tren luoi, da neu qua \pcGrid
    "1",      # gia tri C trung tinh
    "1.0",
    "4",      # so chu so lam tron trong caption
    "8",      # doi so cua thebibliography
    "0",      # can duoi cua khoang goc [0, pi]
    "0.5",    # macro-F1 cua bo phan loai hang: hang so toan hoc, khong phai
              # so lieu do duoc -- neu doi thanh so do thi phai thanh macro
}


def audit_selection(m: dict[str, str]) -> None:
    """Khoa muc "What would have caught it" -- phep do moi.

    Muc nay LAT LAI mot cau ban truoc viet suong ("neither would have
    selected the degenerate constant here"). Cau do dung cho kernel luong tu
    va RBF, SAI cho kernel tuyen tinh. Neu artifact duoc sinh lai va so lieu
    doi chieu, cac phep kiem duoi day phai do cho bai truoc khi nguoi doc do.
    """
    cur = pd.read_csv(ROOT / "results/unsw/paper3/p3_c_curve.csv")
    obj = pd.read_csv(ROOT / "results/unsw/paper3/p3_objective.csv")
    rep = load("results/unsw/paper3/p3_reproduction.json")

    # CONG KIEM CHUNG. Duong ong sinh ra so moi phai tra ve dung nhung so
    # DA IN. Khong dat thi moi so o muc nay deu vo gia tri.
    check(bool(rep["reproduced"]), "duong ong tai lap duoc so da cong bo")
    check(rep["cv_max_abs_dev"] == 0.0, "CV tai lap khit tuyet doi")
    check(max(rep["test_tuned_max_abs_dev"],
              rep["test_neutral_max_abs_dev"]) < 1e-12, "test tai lap khit")
    check(m["reproCv"] == f"{rep['cv_max_abs_dev']:g}", "reproCv")

    g = (cur.groupby(["kernel", "C"])
            .agg(f1=("f1", "mean"), f1m=("f1_macro", "mean"),
                 deg=("degenerate", "sum")).reset_index())
    nrun = int(cur.run.nunique())
    check(m["curveRuns"] == str(nrun), "curveRuns")
    check(m["curveNc"] == str(cur.C.nunique()), "curveNc")
    # Luoi day phai CHUA tron ven luoi goc, neu khong thi hai phep do khong
    # so sanh duoc voi nhau.
    dense = set(cur.C.round(10))
    check(all(round(c, 10) in dense for c in (0.01, 0.1, 1.0, 10.0, 100.0)),
          "luoi day chua tron ven luoi goc 5 diem")

    q = g[g.kernel == "quantum"].sort_values("C")
    esc = float(q[q.deg == 0].C.min())
    check(m["curveEscapeC"] == f"{esc:g}", "curveEscapeC")
    # Claim: kernel luong tu thoat trong khoang (0,1 ; 1) -- dung cho ma luoi
    # goc buoc qua. Ca muc dua vao day.
    check(0.1 < esc < 1.0,
          f"quantum thoat giua 0,1 va 1 (thuc te {esc:g})")

    lo = q[q.C == q.C.min()].iloc[0]
    hi = q[q.C == esc].iloc[0]
    check(m["curveFoneRise"] == f"{hi.f1 - lo.f1:+.4f}", "curveFoneRise")
    check(m["curveMacroRise"] == f"{hi.f1m - lo.f1m:+.4f}", "curveMacroRise")
    ratio = (hi.f1m - lo.f1m) / (hi.f1 - lo.f1)
    check(m["curveRiseRatio"] == f"{ratio:.0f}", "curveRiseRatio")
    # Claim trung tam cua Hinh 3(a): macro F1 nhay manh hon HAN.
    check(ratio > 3.0, f"macro F1 nhay manh hon binary F1 ({ratio:.1f}x)")

    for k, tag in (("quantum", "Q"), ("linear", "Lin"), ("rbf", "Rbf")):
        for o, otag in (("f1_binary", "Bin"), ("f1_macro", "Mac"),
                        ("balanced_accuracy", "Bal")):
            r = obj[(obj.kernel == k) & (obj.objective == o)].iloc[0]
            check(m[f"obj{tag}{otag}C"] == f"{r.selected_C:.3g}",
                  f"obj{tag}{otag}C")
            check(m[f"obj{tag}{otag}Deg"]
                  == f"{int(r.n_degenerate)}/{int(r.n_runs)}",
                  f"obj{tag}{otag}Deg")

    # HAI CLAIM cua muc, doc thang tu bang.
    qq = obj[obj.kernel == "quantum"]
    check((qq.n_degenerate == 0).all(),
          "tren luoi day, MOI ham muc tieu deu chon C khong suy bien cho "
          "kernel luong tu")
    ll = obj[obj.kernel == "linear"]
    check((ll.n_degenerate > 0).all(),
          "va o kernel tuyen tinh thi KHONG ham nao tranh duoc -- day la cho "
          "cau 'class-averaged objective la du' bi bac bo")
    check(ll.selected_C.nunique() == 1,
          "ba ham muc tieu tra ve cung mot C cho kernel tuyen tinh")


def audit_macros_defined(tex: str, m: dict) -> None:
    r"""Moi macro \p... DUNG trong bai phai duoc DINH NGHIA.

    Khong co phep kiem nay thi go sai mot ten macro se lot: audit van xanh vi
    no chi doi chieu nhung macro da co, con LaTeX thi chet voi 'Undefined
    control sequence'.
    """
    latex_p = {"paragraph", "pm", "pi", "par", "pageref", "protect",
               "printindex", "pounds", "pagestyle", "pagenumbering"}
    used = {name[1:] for name in re.findall(BS + BS + r"(p[A-Za-z]+)", tex)
            if name not in latex_p}
    missing = sorted(used - set(m))
    check(not missing, f"moi macro dung trong bai deu duoc dinh nghia "
                       f"(thieu: {missing})")


def audit_prose_numbers(tex: str) -> None:
    body = strip_comments(tex)
    # Bo phan preamble va thu muc tai lieu tham khao.
    body = body.split(BS + "maketitle", 1)[-1]
    body = body.split(BS + "begin{thebibliography}", 1)[0]
    # Bo noi dung cac lenh khong phai cau van.
    body = re.sub(BS + BS + r"includegraphics(\[[^\]]*\])?\{[^}]*\}", " ", body)
    body = re.sub(BS + BS + r"(label|ref|input|url|newcommand)\{[^}]*\}", " ", body)

    bad = []
    for tok in re.findall(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])", body):
        if tok not in NUMBER_WHITELIST:
            bad.append(tok)
    check(not bad, f"khong co so viet tay trong cau van (thay: {sorted(set(bad))})")


# --------------------------------------------------------------------------
# C. Bat bien cua lap luan
# --------------------------------------------------------------------------
def audit_invariants() -> None:
    tune = load("results/unsw/c_tuning_results.json")
    scores = {r["C"]: r["mean"] for r in tune["quantum"]["scores_per_C"]}
    floor = scores[0.01]

    # Lap luan trung tam: kernel luong tu KHONG BAO GIO vuot nguong san.
    best_above = max(v for c, v in scores.items() if c > 0.1)
    check(best_above < floor,
          "diem CV tot nhat khong suy bien cua quantum < nguong san")

    # Va cac kernel co dien THI CO vuot -- neu khong, bang doi xung sup.
    for k in ("linear", "poly", "rbf"):
        s = {r["C"]: r["mean"] for r in tune[k]["scores_per_C"]}
        check(max(s.values()) > floor, f"{k} vuot duoc nguong san")

    # Kernel khong doi giua hai che do C.
    a = load("results/unsw/c3_results_statevector.json")["summary"]["quantum"]
    b = load("results/unsw/c3_results_statevector_C1.json")["summary"]["quantum"]
    check(a["kta_mean"] == b["kta_mean"], "KTA trung tung bit giua hai che do C")
    check(a["C"] != b["C"], "hai che do C thuc su khac nhau")

    # Bang kiem dem phai quet toan bo, khong loc truoc.
    df = pd.read_csv(ROOT / "results/unsw/c4_revision"
                     / "c4_per_run_unsw_natural_refit_per_N.csv")
    check(df.model.nunique() == 7, "quet du 7 model o giao thuc revision")
    check((df[df.model == "QSVM_ZZ"].recall_macro.round(10) == 0.5).sum() == 0,
          "khong dong QSVM_ZZ nao suy bien o giao thuc revision")


# --------------------------------------------------------------------------
def audit_assets() -> None:
    figs = ["fig1_tuning_trap", "fig2_k_sweep", "fig3_objective"]
    for rel in [f"figs/{f}.pdf" for f in figs] + [
            "tables/degeneracy_census.tex", "tables/objective_table.tex",
            "tables/numbers_macros.tex", "main.tex"]:
        check((PAPER / rel).exists(), f"co {rel}")
    # Hinh sinh ra ma khong duoc chen vao bai thi coi nhu khong ton tai.
    body = read(PAPER / "main.tex")
    for f in figs:
        check(f"figs/{f}.pdf" in body, f"bai co chen {f}")

    # Dong gop thu 4 cua bai la "phat hanh bo kiem". Neu link mirror van con
    # la placeholder thi phan bien bam vao ra 404, va dong gop do thanh loi
    # noi suong. Day la loai loi khong ai doc lai ma thay.
    # Chi soi RIENG link mirror. `Paper ID \#XXXX` o khoi tac gia la
    # placeholder HOP LE -- Confy+ chua cap so -- nen mot phep kiem quet
    # "XXXX" tren ca bai se bao do vi mot ly do khong phai loi.
    check("4open.science/r/XXXX" not in body,
          "link mirror khong con la placeholder")
    check("anonymous.4open.science/r/" in body,
          "muc Reproducibility co link mirror an danh")

    # CHOT AN TOAN. De xem ten tac gia, nguoi ta se lat \anonymousfalse roi
    # compile. Quen lat lai truoc khi nop la nop mot PDF CO TEN vao mot hoi
    # nghi phan bien hai chieu mu -- bi loai thang, khong can ly do khac.
    # Day la loai loi khong ai doc lai ma thay, vi bai van dep.
    #
    # DEN LUC CAMERA-READY: bai da duoc nhan, luc do lat \anonymousfalse la
    # DUNG, va phai sua chinh phep kiem nay (doi thanh check nguoc lai).
    src = read(PAPER / "main.tex")
    code = re.sub(r"(?<!" + BS + BS + r")%.*", "", src)
    check(BS + "anonymoustrue" in code,
          "con dat \\anonymoustrue -- ban nop PHAI an danh")
    check(BS + "anonymousfalse" not in code,
          "khong bat nham \\anonymousfalse (lo ten trong ban nop)")

    census = pd.read_csv(ROOT / "results/unsw/paper3/degeneracy_census.csv")
    tex = read(PAPER / "tables" / "degeneracy_census.tex")
    n_rows = tex.count(r"\\") - 1  # tru dong tieu de
    check(n_rows == len(census),
          f"bang co {n_rows} dong du lieu, CSV co {len(census)}")


def main() -> int:
    macros = parse_macros(read(PAPER / "tables" / "numbers_macros.tex"))
    audit_macros(macros)
    audit_selection(macros)
    tex = read(PAPER / "main.tex")
    audit_macros_defined(tex, macros)
    audit_prose_numbers(tex)
    audit_invariants()
    audit_assets()

    # TU KIEM: moi ham audit_* phai duoc goi. O audit_p2_rebuild.py da xay ra
    # chuyen ba ham nam trong file ma khong he duoc goi, va audit van bao
    # xanh -- 62 phep kiem la ma chet. Them o day de khong lap lai.
    src = read(Path(__file__))
    defined = set(re.findall(r"^def (audit_\w+)", src, re.M))
    called = set(re.findall(r"^    (audit_\w+)\(", src, re.M))
    dead = sorted(defined - called)
    check(not dead, f"khong co ham audit_* nao la ma chet (chet: {dead})")

    n_ok = sum(1 for ok, _ in _checks if ok)
    for ok, label in _checks:
        if not ok:
            print(f"  LOI   {label}")
    print(f"\n  audit_paper3  {n_ok}/{len(_checks)}")
    return 0 if n_ok == len(_checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
