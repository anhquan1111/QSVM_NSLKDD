"""Dong goi bo ban thao de tai len Overleaf.

Chi lay dung nhung file main_revision.tex thuc su \\input, cong 12 hinh PDF.
CO Y bo `main.tex` cu: no la ban dung lai tu paper1.pdf de doi chieu, neu de
lan trong zip thi Overleaf rat de chon nham lam tai lieu chinh.

    python runners/make_overleaf_zip.py

Ket qua: paper/paper1/overleaf/TETC-2026-05-0252_revision.zip
"""

from __future__ import annotations

import io
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/paper1"
MAIN = PAPER / "main_revision.tex"
OUT_DIR = PAPER / "overleaf"
ZIP = OUT_DIR / "TETC-2026-05-0252_revision.zip"

BS = chr(92)

README = """\
# TETC-2026-05-0252 -- ban revision, de tai len Overleaf

## Cach dung

1. Overleaf -> New Project -> Upload Project -> chon file zip nay.
2. Menu -> Settings -> Main document: chon `main_revision.tex`.
3. Compiler: pdfLaTeX. Bien dich hai lan (lan dau de sinh .aux cho \\ref).
4. IEEEtran.cls co san tren Overleaf, khong can tai kem.

Zip nay chua HAI tai lieu doc lap, bien dich rieng, ra hai PDF:

| File | La gi | Khi nao doi Main document sang no |
|---|---|---|
| `main_revision.tex` | ban thao revision | mac dinh |
| `response_letter.tex` | thu phan hoi 33 y reviewer | khi muon xuat thu gui AE |

Thu phan hoi KHONG duoc \\input vao ban thao va nguoc lai.

## Kiem truoc khi gui di

Trong repo:

    python runners/check_latex.py     # cau truc .tex
    python runners/audit_c4.py        # 100 kiem dinh thong ke
    python runners/audit_figures.py   #  39 kiem dinh hinh
    python runners/audit_prose.py     #  84 con so trong cau van
    python runners/verify_lemma1.py   #  15 kiem dinh Lemma 1

## Nhung cho CON PHAI DIEN, khong duoc bo qua

- Muc Reproducibility trong `04_setup.tex`: commit hash hien la `19beb18`,
  phai doi thanh commit cuoi truoc khi nop (trong bai co footnote nhac).
- Ngay thang trong `\\thanks{Manuscript received ...}`.
- Toan van QMI 2026 (Springer) va Carducci ICAD 2026 (IEEE Xplore): chi con
  can de dien vai o `n/r` trong Table I. Ca hai trich dan da DAY DU.

## Danh muc file

"""


def inputs_recursive(path: Path, seen: set[Path]) -> list[Path]:
    out: list[Path] = []
    text = io.open(path, encoding="utf-8").read()
    for t in re.findall(BS + BS + r"input\{([^}]*)\}", text):
        for cand in (path.parent / t, path.parent / (t + ".tex")):
            if cand.exists():
                if cand not in seen:
                    seen.add(cand)
                    out.append(cand)
                    out += inputs_recursive(cand, seen)
                break
        else:
            print(f"  CANH BAO: khong tim thay \\input{{{t}}}")
    return out


def graphics_of(files: list[Path]) -> list[Path]:
    out: list[Path] = []
    for f in files:
        text = io.open(f, encoding="utf-8").read()
        for g in re.findall(BS + BS + r"includegraphics(?:\[[^\]]*\])?\{([^}]*)\}",
                            text):
            p = PAPER / g
            if not p.exists() and not p.suffix:
                p = p.with_suffix(".pdf")
            if p.exists():
                out.append(p)
            else:
                print(f"  CANH BAO: thieu hinh {g}")
    return out


def main() -> int:
    if not MAIN.exists():
        print(f"khong co {MAIN}")
        return 1

    tex = [MAIN] + inputs_recursive(MAIN, {MAIN})

    # Thu phan hoi la tai lieu DOC LAP (documentclass rieng), khong duoc
    # \input vao ban thao. Phai them tay, khong thi no rot khoi zip.
    letter = PAPER / "response_letter.tex"
    if letter.exists():
        tex.append(letter)
        tex += inputs_recursive(letter, set(tex))
    else:
        print("  CANH BAO: khong co response_letter.tex")

    figs = graphics_of(tex)
    files = tex + figs

    missing = [f for f in files if not f.exists()]
    if missing:
        print("thieu file:", missing)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    listing = []
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            arc = f.relative_to(PAPER).as_posix()
            z.write(f, arc)
            listing.append(f"- `{arc}`  ({f.stat().st_size / 1024:.0f} KB)")
        z.writestr("README.md", README + "\n".join(listing) + "\n")

    print(f"\nda ghi {ZIP.relative_to(ROOT)}")
    print(f"  {len(tex)} file .tex, {len(figs)} hinh, "
          f"tong {ZIP.stat().st_size / 1024:.0f} KB")
    print("\nDanh sach:")
    for line in listing:
        print("  " + line.replace("`", ""))
    print("\n  KHONG dua vao zip: main.tex (ban dung lai tu paper1.pdf de doi "
          "chieu),\n  cac file .png trung lap voi .pdf, va toan bo paper1.pdf.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
