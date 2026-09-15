"""Dong goi ban thao de tai len Overleaf.

Sinh BON goi. Ba goi dau moi goi chua DUNG MOT tai lieu bien dich duoc, cong
het phan phu thuoc cua no:

    TETC-2026-05-0252_ban_sach.zip       -> main_revision.tex
    TETC-2026-05-0252_ban_danh_dau.zip   -> main_annotated.tex
    TETC-2026-05-0252_thu_phan_hoi.zip   -> response_letter.tex

Trong moi goi do chi co dung mot file mang \\documentclass, nen Overleaf tu
chon dung Main document -- khong phai vao Settings doi tay, va do do khong the
chon nham file roi bao thieu \\input.

Goi thu tu la ban gop ca ba, giu de luu tru:

    TETC-2026-05-0252_revision.zip

Ban da nop 05/2026 nam o v1_submitted/, khong dinh toi goi nao.

    python runners/make_overleaf_zip.py
"""

from __future__ import annotations

import io
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/paper1"
OUT_DIR = PAPER / "v2_revision"

BS = chr(92)

# Ba tai lieu doc lap. Moi cai co \documentclass rieng nen KHONG duoc \input
# vao nhau -- phai dong goi rieng.
DOCS = [
    ("ban_sach", "main_revision.tex", "Ban thao SACH",
     "Ban nop cho tap chi. Khong co nhan danh dau nao."),
    ("ban_danh_dau", "main_annotated.tex", "Ban CO DANH DAU thay doi",
     "Moi tieu de tieu muc co them mot nhan mau -- MOI / VIET LAI / SUA LOI / "
     "GIU -- kem mot cau noi doi cai gi va ma y reviewer tuong ung. Than bai "
     "giong het ban sach, vi ca hai dung chung sections/. TETC bat buoc nop "
     "ban nay kem ban sach."),
    ("thu_phan_hoi", "response_letter.tex", "Thu phan hoi reviewer",
     "33 y, gui ban bien tap."),
]

HEAD = """\
# {title} -- TETC-2026-05-0252

## Cach tai len

1. Overleaf -> **New Project** -> **Upload Project** -> chon file zip nay.
2. Bam **Recompile**. Xong.

Khong phai vao Settings doi gi ca: goi nay chi chua DUNG MOT file co
`\\documentclass` (`{main}`), nen Overleaf tu nhan dung Main document.

**Dung keo file zip nay tha vao mot project Overleaf DANG CO.** Lam vay
Overleaf giai nen vao mot thu muc con: file main nam mot noi con
`preamble.tex` nam noi khac, va bao `File preamble.tex not found`.
Phai la project MOI.

Compiler: pdfLaTeX. `IEEEtran.cls` co san tren Overleaf, khong can tai kem.
Tai lieu tham khao dung `thebibliography`, khong can chay BibTeX.

{blurb}

## Danh muc file

"""

TAIL_MAIN = """

## Nhung cho CON PHAI DIEN truoc khi nop

- `sections/04_setup.tex`: commit hash dang la `19beb18`, phai doi thanh
  commit cuoi (trong bai co footnote nhac toi no).
- `document.tex`: ngay thang trong `\\thanks{Manuscript received ...}`.
- Toan van QMI 2026 (Springer) va Carducci ICAD 2026 (IEEE Xplore): chi con
  can de dien vai o `n/r` trong Table I. Ca hai trich dan da DAY DU.

## Kiem trong repo truoc khi gui di

    python runners/check_latex.py     # cau truc .tex
    python runners/audit_c4.py        # 100 kiem dinh thong ke
    python runners/audit_figures.py   #  36 kiem dinh hinh
    python runners/audit_prose.py     # 132 con so trong cau van
    python runners/verify_lemma1.py   #  15 kiem dinh Lemma 1
"""

README_ALL = """\
# TETC-2026-05-0252 -- goi GOP ca ba tai lieu

Goi nay co BA file mang `\\documentclass`, nen Overleaf se chon bua mot cai lam
Main document. Muon bien dich MOT tai lieu thi tai len goi rieng cua no, khong
phai chinh gi ca:

| Muon xuat cai gi | Tai len goi nao |
|---|---|
| Ban thao sach | `TETC-2026-05-0252_ban_sach.zip` |
| Ban co danh dau thay doi | `TETC-2026-05-0252_ban_danh_dau.zip` |
| Thu phan hoi reviewer | `TETC-2026-05-0252_thu_phan_hoi.zip` |

Dung goi gop nay thi phai vao **Menu -> Settings -> Main document** chon dung
file, roi Recompile.

## Danh muc file

"""


def strip_comments(text: str) -> str:
    """Bo phan sau dau % chua duoc escape. Mot cau chu thich nhac toi
    \\documentclass khong duoc tinh la mot tai lieu that."""
    return re.sub(r"(?<!" + BS + BS + r")%.*", "", text)


def inputs_recursive(path: Path, seen: set[Path]) -> list[Path]:
    out: list[Path] = []
    text = io.open(path, encoding="utf-8").read()
    # LaTeX phan giai \input theo thu muc TAI LIEU CHINH, khong theo thu muc
    # cua file chua lenh -- nen \input{figs_revision/x} viet trong sections/
    # van tro toi paper/paper1/figs_revision/x.
    for t in re.findall(BS + BS + r"input\{([^}]*)\}", text):
        for cand in (PAPER / t, PAPER / (t + ".tex"),
                     path.parent / t, path.parent / (t + ".tex")):
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
                if p not in out:
                    out.append(p)
            else:
                print(f"  CANH BAO: thieu hinh {g}")
    return out


def write_zip(zip_path: Path, files: list[Path], head: str, tail: str = "") -> None:
    listing = []
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            arc = f.relative_to(PAPER).as_posix()
            # Dong nhat ve LF: checkout tren Windows co the cho CRLF con
            # Overleaf chay Linux.
            if f.suffix == ".tex":
                z.writestr(arc, f.read_bytes().replace(b"\r\n", b"\n"))
            else:
                z.write(f, arc)
            listing.append(f"- `{arc}`  ({f.stat().st_size / 1024:.0f} KB)")
        z.writestr("README.md", head + "\n".join(listing) + "\n" + tail)


def check_one_documentclass(zip_path: Path) -> bool:
    """Overleaf chon Main document bang cach do \\documentclass. Goi co hai file
    nhu vay thi no co the chon nham -- dung cai loi da xay ra."""
    with zipfile.ZipFile(zip_path) as z:
        hits = [n for n in z.namelist() if n.endswith(".tex")
                and re.search(BS + BS + r"documentclass",
                              strip_comments(z.read(n).decode("utf-8")))]
    if len(hits) != 1:
        print(f"  LOI: {zip_path.name} co {len(hits)} file \\documentclass: {hits}")
        return False
    return True


def check_inputs_resolve(zip_path: Path) -> bool:
    """Moi \\input trong goi phai tro toi mot file CO TRONG GOI. Day chinh la
    phep kiem bat duoc 'File preamble.tex not found'."""
    ok = True
    with zipfile.ZipFile(zip_path) as z:
        names = set(z.namelist())
        for n in sorted(x for x in names if x.endswith(".tex")):
            for t in re.findall(BS + BS + r"input\{([^}]*)\}",
                                z.read(n).decode("utf-8")):
                if t not in names and t + ".tex" not in names:
                    print(f"  LOI: {zip_path.name}: {n} goi \\input{{{t}}} "
                          f"nhung goi khong co file do")
                    ok = False
    return ok


def check_graphics_resolve(zip_path: Path) -> bool:
    ok = True
    with zipfile.ZipFile(zip_path) as z:
        names = set(z.namelist())
        for n in sorted(x for x in names if x.endswith(".tex")):
            for g in re.findall(BS + BS + r"includegraphics(?:\[[^\]]*\])?\{([^}]*)\}",
                                z.read(n).decode("utf-8")):
                if g not in names and not any(
                        g + ext in names for ext in (".pdf", ".png", ".jpg")):
                    print(f"  LOI: {zip_path.name}: thieu hinh {g}")
                    ok = False
    return ok


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    combined: list[Path] = []
    made: list[tuple[Path, int, int]] = []

    for key, name, title, blurb in DOCS:
        src = PAPER / name
        if not src.exists():
            print(f"  LOI: khong co {name}")
            return 1
        tex = [src] + inputs_recursive(src, {src})
        figs = graphics_of(tex)
        files = tex + figs

        head = HEAD.format(title=title, main=name, blurb=blurb)
        tail = "" if key == "thu_phan_hoi" else TAIL_MAIN
        zp = OUT_DIR / f"TETC-2026-05-0252_{key}.zip"
        write_zip(zp, files, head, tail)

        for f in files:
            if f not in combined:
                combined.append(f)
        made.append((zp, len(tex), len(figs)))

    zp_all = OUT_DIR / "TETC-2026-05-0252_revision.zip"
    write_zip(zp_all, combined, README_ALL, TAIL_MAIN)

    print()
    ok = True
    for zp, ntex, nfig in made:
        good = (check_one_documentclass(zp) and check_inputs_resolve(zp)
                and check_graphics_resolve(zp))
        ok &= good
        print(f"  {'OK ' if good else 'LOI'}  {zp.name:40s} "
              f"{ntex:2d} .tex + {nfig} hinh, {zp.stat().st_size / 1024:>4.0f} KB")
    good_all = check_inputs_resolve(zp_all) and check_graphics_resolve(zp_all)
    ok &= good_all
    print(f"  {'OK ' if good_all else 'LOI'}  {zp_all.name:40s} "
          f"goi gop, {zp_all.stat().st_size / 1024:>16.0f} KB")
    print(f"\n  Tat ca nam trong {OUT_DIR.relative_to(ROOT)}")
    print("  KHONG dua vao goi: thu muc v1_submitted/ (ban da nop).")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
