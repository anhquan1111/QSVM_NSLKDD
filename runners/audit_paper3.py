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
}


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
    for rel in ("figs/fig1_tuning_trap.pdf", "figs/fig2_k_sweep.pdf",
                "tables/degeneracy_census.tex", "tables/numbers_macros.tex",
                "main.tex"):
        check((PAPER / rel).exists(), f"co {rel}")

    census = pd.read_csv(ROOT / "results/unsw/paper3/degeneracy_census.csv")
    tex = read(PAPER / "tables" / "degeneracy_census.tex")
    n_rows = tex.count(r"\\") - 1  # tru dong tieu de
    check(n_rows == len(census),
          f"bang co {n_rows} dong du lieu, CSV co {len(census)}")


def main() -> int:
    macros = parse_macros(read(PAPER / "tables" / "numbers_macros.tex"))
    audit_macros(macros)
    audit_prose_numbers(read(PAPER / "main.tex"))
    audit_invariants()
    audit_assets()

    n_ok = sum(1 for ok, _ in _checks if ok)
    for ok, label in _checks:
        if not ok:
            print(f"  LOI   {label}")
    print(f"\n  audit_paper3  {n_ok}/{len(_checks)}")
    return 0 if n_ok == len(_checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
