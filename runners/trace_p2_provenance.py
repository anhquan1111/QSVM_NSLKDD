"""Truy vet xuat xu moi con so trong Paper 2 -- tu cau van ve toi du lieu goc.

    python runners/trace_p2_provenance.py

Bai nay phinh tu 3 trang len gan 10. Cau hoi chinh dang la: co con so nao
duoc BIA ra khong, hay moi thu deu chay tu du lieu that?

Script tra loi bang cach di nguoc chuoi:

    cau van  ->  macro \\pXxx  ->  artifact CSV/JSON  ->  runner sinh ra no
             ->  file du lieu goc ma runner doc

Va bao cao:
  - macro nao duoc dung trong bai va macro nao KHONG (thua thi go bo)
  - artifact nao co runner sinh ra, artifact nao mo coi
  - runner nao doc file du lieu that, va doc file nao
  - co con so nao trong bai KHONG di qua macro
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper" / "paper2_rebuild"
RUNNERS = ROOT / "runners"
BS = chr(92)

# Artifact -> runner sinh ra no. Doc tu chinh ma nguon cac runner chu khong
# khai bao tay, de danh sach nay khong the lech voi thuc te.
ART_RE = re.compile(r'["\'](p2_[a-z0-9_]+\.(?:csv|json))["\']')
# Ten ghep bang f-string, vd  f"p2_rebuild_{name}.csv"  voi name lay tu mot
# tuple ngay tren. Khong bat duoc thi ba artifact bi bao nham la mo coi.
FSTR_RE = re.compile(r'f["\']p2_([a-z0-9_]*)\{(\w+)\}([a-z0-9_]*)\.(csv|json)["\']')
LOOPVAL_RE = re.compile(r'["\'](\w+)["\']\s*\)')
DATA_RE = re.compile(r'["\']([A-Za-z0-9_./-]+\.(?:csv|parquet|joblib))["\']')


def read(p: Path) -> str:
    with io.open(p, encoding="utf-8") as f:
        return f.read()


def main() -> int:
    tex = read(PAPER / "main.tex")
    for extra in ("tables/main_table.tex", "tables/side_tables.tex",
                  "tables/percat_table.tex", "tables/regime_table.tex",
                  "tables/depth_tables.tex"):
        p = PAPER / extra
        if p.exists():
            tex += read(p)

    macros_src = read(PAPER / "tables" / "numbers_macros.tex")
    defined = set(re.findall(
        BS + BS + r"newcommand\{" + BS + BS + r"p(\w+)\}", macros_src))
    latex_p = {"paragraph", "pm", "pi", "par", "pageref", "protect",
               "printindex", "pounds", "pagestyle", "pagenumbering",
               "phi", "psi", "prod", "partial", "perp", "propto", "pmod"}
    used = {n[1:] for n in re.findall(BS + BS + r"(p[A-Za-z]+)", tex)
            if n not in latex_p}

    print("=" * 74)
    print("  1. MACRO")
    print("=" * 74)
    print(f"  dinh nghia : {len(defined)}")
    print(f"  dung trong bai: {len(used & defined)}")
    unused = sorted(defined - used)
    print(f"  dinh nghia ma KHONG dung: {len(unused)}")
    if unused:
        print(f"     {', '.join(unused[:12])}{' ...' if len(unused) > 12 else ''}")
    missing = sorted(used - defined)
    print(f"  dung ma KHONG dinh nghia: {len(missing)}  "
          f"{missing if missing else ''}")

    # --- runner nao sinh ra artifact nao -----------------------------
    print()
    print("=" * 74)
    print("  2. ARTIFACT <- RUNNER <- DU LIEU GOC")
    print("=" * 74)
    produced: dict[str, str] = {}
    reads: dict[str, set[str]] = {}
    # Chi tinh la SINH RA khi ten file xuat hien tren mot dong co to_csv /
    # json.dump / mo de ghi. Truoc day regex bat ca dong DOC, nen no gan
    # gan het artifact cho make_p2_rebuild_tables.py -- chinh script chi doc
    # chung. Mot bao cao truy vet sai xuat xu thi vo dung.
    WRITE = ("to_csv", "json.dump", 'w", encoding', "w\", encoding=")
    for rp in sorted(RUNNERS.glob("*p2_rebuild*.py")) + \
              sorted(RUNNERS.glob("verify_rare_identity.py")):
        src = read(rp)
        lines = src.splitlines()
        for i, ln in enumerate(lines):
            for art in ART_RE.findall(ln):
                window = " ".join(lines[max(0, i - 2):i + 3])
                if any(w in window for w in WRITE):
                    produced.setdefault(art, rp.name)
            # Ten ghep bang f-string: lay cac gia tri chuoi o vai dong tren
            # lam ung vien cho phan {bien}.
            for pre, var, post, ext in FSTR_RE.findall(ln):
                window = " ".join(lines[max(0, i - 2):i + 3])
                if not any(w in window for w in WRITE):
                    continue
                for val in LOOPVAL_RE.findall(" ".join(lines[max(0, i - 8):i])):
                    produced.setdefault(f"p2_{pre}{val}{post}.{ext}", rp.name)
        reads[rp.name] = {d for d in DATA_RE.findall(src)
                          if d.startswith(("data/", "NSL_", "UNSW_"))
                          or "Cleaned" in d or "train_run" in d}

    arts = sorted({a for a in ART_RE.findall(read(
        RUNNERS / "make_p2_rebuild_tables.py"))})
    orphan = []
    for a in arts:
        who = produced.get(a)
        if who:
            print(f"  {a:34s} <- {who}")
        else:
            orphan.append(a)
    if orphan:
        print(f"\n  MO COI (khong runner nao sinh ra): {orphan}")

    print()
    print("  Du lieu goc moi runner doc:")
    for name in sorted(reads):
        if reads[name]:
            for d in sorted(reads[name]):
                exists = (ROOT / d).exists() or (ROOT / "data/nslkdd/processed_data" / d).exists()
                print(f"    {name:32s} {d:46s} {'co' if exists else 'THIEU'}")

    # --- so viet tay trong cau van -----------------------------------
    print()
    print("=" * 74)
    print("  3. SO VIET TAY TRONG CAU VAN")
    print("=" * 74)
    body = re.sub(r"(?<!" + BS + BS + r")%.*", "", read(PAPER / "main.tex"))
    body = body.split(BS + "maketitle", 1)[-1]
    body = body.split(BS + "begin{thebibliography}", 1)[0]
    body = re.sub(BS + BS + r"(label|ref|eqref|input|url|newcommand|cite|ding)"
                  r"\{[^}]*\}", " ", body)
    for nm in ("KDDTest-21", "UNSW-NB15", "NSL-KDD", "KDDTest+"):
        body = body.replace(nm, " ")
    nums = sorted(set(re.findall(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])", body)))
    print(f"  so xuat hien truc tiep: {nums if nums else 'khong co'}")
    print("  (moi so con lai deu la hang so cau truc, xem NUMBER_WHITELIST")
    print("   trong runners/audit_p2_rebuild.py)")

    ok = not missing and not orphan
    print()
    print(f"  => {'TRUY VET DAY DU' if ok else 'CON CHO CHUA TRUY DUOC'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
