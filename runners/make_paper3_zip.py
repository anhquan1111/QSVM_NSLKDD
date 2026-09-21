"""Dong goi bai hoi nghi AICON 2026 de tai len Overleaf.

Chay:  python runners/make_paper3_zip.py
Xuat:  paper/paper3_aicon/dist/AICON2026_paper3.zip

May nay khong co LaTeX, nen bai phai compile tren Overleaf. `llncs.cls` co
san o do -- khong can dong goi kem.

Dung lai ba phep tu kiem cua `make_overleaf_zip.py`:
  1. goi phai co DUNG MOT file mang \\documentclass;
  2. moi \\input tro toi mot file CO TRONG GOI;
  3. moi \\includegraphics cung vay.

Phep thu hai chinh la cai bat duoc loi "File preamble.tex not found" hoi
dong goi paper 1.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from make_overleaf_zip import (  # noqa: E402
    check_graphics_resolve,
    check_inputs_resolve,
    check_one_documentclass,
    graphics_of,
    inputs_recursive,
    write_zip,
)

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper" / "paper3_aicon"
OUT_DIR = PAPER / "dist"
MAIN = "main.tex"

HEAD = """\
# AICON 2026 -- paper 3

## Cach tai len

1. Overleaf -> **New Project** -> **Upload Project** -> chon file zip nay.
2. Bam **Recompile**. Xong.

Compiler: **pdfLaTeX**. `llncs.cls` (Springer LNCS/LNICST) co san tren
Overleaf nen khong dong goi kem.

**Dung keo zip nay tha vao mot project Overleaf DANG CO.** Overleaf se giai
nen vao mot thu muc con, roi `main.tex` va `tables/` nam khac cho nhau va bao
thieu file. Phai la project MOI.

## Truoc khi nop qua EAI Confy+

- Giu `\\anonymoustrue` trong `main.tex` -- Confy+ bat buoc PDF an danh.
- Thay dia chi kho ma bang mot mirror an danh
  (`anonymous.4open.science`): repo that mang ten tac gia.
- Khai xung dot loi ich: ba chair cua session deu la dong tac gia paper 1.

## Danh muc file

"""

TAIL = """

## Kiem trong repo truoc khi gui di

    python runners/make_paper3_figures.py
    python runners/make_paper3_tables.py
    python runners/audit_paper3.py
    python runners/check_latex.py paper/paper3_aicon/main.tex
"""


def main() -> int:
    src = PAPER / MAIN
    if not src.exists():
        print(f"  LOI: khong co {src.relative_to(ROOT).as_posix()}")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tex = [src] + inputs_recursive(src, {src}, base=PAPER)
    figs = graphics_of(tex, base=PAPER)
    files = tex + figs

    zp = OUT_DIR / "AICON2026_paper3.zip"
    write_zip(zp, files, HEAD, TAIL, base=PAPER)

    ok = (check_one_documentclass(zp) and check_inputs_resolve(zp)
          and check_graphics_resolve(zp))
    print(f"\n  {'OK ' if ok else 'LOI'}  {zp.name:28s} "
          f"{len(tex)} .tex + {len(figs)} hinh, {zp.stat().st_size / 1024:>4.0f} KB")
    for f in files:
        print(f"         {f.relative_to(PAPER).as_posix()}")
    print(f"\n  Nam trong {OUT_DIR.relative_to(ROOT).as_posix()}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
