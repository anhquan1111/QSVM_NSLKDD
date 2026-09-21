"""Dong goi bai de tai len Overleaf.

    python runners/make_paper_zip.py            # dong goi ca hai
    python runners/make_paper_zip.py paper3     # chi bai hoi nghi
    python runners/make_paper_zip.py paper2     # chi Paper 2 dung lai

May nay khong co LaTeX nen bai phai compile tren Overleaf.

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

PAPERS = {
    "paper3": dict(
        dir="paper/paper3_aicon", main="main.tex", zip="AICON2026_paper3.zip",
        cls="llncs.cls (Springer LNCS/LNICST)",
        notes=(
            "## Truoc khi nop qua EAI Confy+\n\n"
            "- Giu `\\anonymoustrue` trong `main.tex` -- Confy+ bat buoc PDF an danh.\n"
            "- Thay dia chi kho ma bang mot mirror an danh\n"
            "  (`anonymous.4open.science`): repo that mang ten tac gia.\n"
            "- Khai xung dot loi ich: ba chair cua session deu la dong tac gia paper 1.\n"
        ),
        checks=("make_paper3_figures", "make_paper3_tables", "audit_paper3"),
    ),
    "paper2": dict(
        dir="paper/paper2_rebuild", main="main.tex",
        zip="Paper2_rebuild.zip",
        cls="IEEEtran.cls",
        notes=(
            "## Con phai lam truoc khi nop\n\n"
            "- Viet prose o cac cho `% TODO` (mo bai, ket luan, chi tiet setup).\n"
            "- Dien `thebibliography` -- giu danh muc cua ban da nop IJNM.\n"
            "- Gui thay duyet: ban nay DOI TRUC chu dao so voi ban da nop.\n"
        ),
        checks=("make_p2_rebuild_figures", "make_p2_rebuild_tables",
                "audit_p2_rebuild", "verify_rare_identity"),
    ),
}

HEAD = """\
# {title}

## Cach tai len

1. Overleaf -> **New Project** -> **Upload Project** -> chon file zip nay.
2. Bam **Recompile**. Xong.

Compiler: **pdfLaTeX**. `{cls}` co san tren Overleaf nen khong dong goi kem.

**Dung keo zip nay tha vao mot project Overleaf DANG CO.** Overleaf se giai
nen vao mot thu muc con, roi `main.tex` va cac thu muc con nam khac cho nhau
va bao thieu file. Phai la project MOI.

{notes}
## Danh muc file

"""


def pack(key: str) -> bool:
    cfg = PAPERS[key]
    paper = ROOT / cfg["dir"]
    src = paper / cfg["main"]
    if not src.exists():
        print(f"  LOI: khong co {src.relative_to(ROOT).as_posix()}")
        return False

    out_dir = paper / "dist"
    out_dir.mkdir(parents=True, exist_ok=True)
    tex = [src] + inputs_recursive(src, {src}, base=paper)
    figs = graphics_of(tex, base=paper)
    files = tex + figs

    tail = ("\n\n## Kiem trong repo truoc khi gui di\n\n"
            + "".join(f"    python runners/{c}.py\n" for c in cfg["checks"])
            + f"    python runners/check_latex.py {cfg['dir']}/{cfg['main']}\n")
    head = HEAD.format(title=cfg["zip"].replace(".zip", ""),
                       cls=cfg["cls"], notes=cfg["notes"])

    zp = out_dir / cfg["zip"]
    write_zip(zp, files, head, tail, base=paper)
    ok = (check_one_documentclass(zp) and check_inputs_resolve(zp)
          and check_graphics_resolve(zp))
    print(f"  {'OK ' if ok else 'LOI'}  {zp.relative_to(ROOT).as_posix():44s} "
          f"{len(tex)} .tex + {len(figs)} hinh, {zp.stat().st_size / 1024:>5.0f} KB")
    return ok


def main() -> int:
    keys = sys.argv[1:] or list(PAPERS)
    bad = [k for k in keys if k not in PAPERS]
    if bad:
        print(f"  LOI: khong biet {bad}; chon trong {list(PAPERS)}")
        return 1
    ok = all(pack(k) for k in keys)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
