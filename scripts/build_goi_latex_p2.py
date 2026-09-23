"""Dung goi LaTeX de NOP, khac goi de mo tren Overleaf.

Goi Overleaf (`runners/make_paper_zip.py`) sinh ra cho chinh minh dung: README
cua no viet tieng Viet va liet ke viec con phai lam ("viet prose o cac cho
TODO", "ban nay doi truc so voi ban da nop IJNM"). Do la ghi chu noi bo. Bien
tap giai nen goi ra la doc duoc -- khong duoc gui di.

Goi nay chi chua thu MA BAN THAO CAN DE COMPILE, cong mot README tieng Anh.
Bo `biographies.tex` va `authors/*.jpg`: main.tex da comment `\\input` chung,
va o dang Main Manuscript thi trang tai len ghi ro "should not include any
supplementary materials".
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "paper" / "paper2_rebuild"
DICH = SRC / "NOP_SECURITY_AND_PRIVACY" / "latex_supplementary.zip"
MAIN = "main.tex"

README = """\
# LaTeX source

Manuscript: "A Reliability and Calibration Benchmark of QSVM Against Strong
Tabular Learners on NSL-KDD and UNSW-NB15"

Compiler: pdfLaTeX.
Document class: IEEEtran (a standard TeX Live / Overleaf class; not bundled).
The reference list is a `thebibliography` environment inside `main.tex`, so no
BibTeX run is required.

## Files

{danh_muc}

## Provenance

Every number and every figure in the manuscript is regenerated from the
artifacts archived at https://doi.org/10.5281/zenodo.22893683
"""

# Dong bi comment khong tinh: main.tex co `%\input{biographies}`.
BO_COMMENT = re.compile(r"(?<!\\)%.*$")


def khong_bi_comment(text: str) -> str:
    return "\n".join(BO_COMMENT.sub("", d) for d in text.splitlines())


def tach(dong: str):
    """Tra ve (phan truoc dau %, co dau % hay khong)."""
    m = BO_COMMENT.search(dong)
    return (dong[:m.start()], True) if m else (dong, False)


def lam_sach_comment(text: str) -> str:
    """Bo het ghi chu, giu dau % noi dong.

    Ban trong repo ghi chu bang tieng Viet: khac ban da nop IJNM cho nao,
    thay Van sua gi, cho nao con `TODO(tac gia)`. Bien tap tai ma nguon ve
    la doc duoc het. Day la ghi chu de lam viec, khong phai thu de gui di.

    Hai truong hop khac nhau:
      - Dong CHI CO comment  -> xoa ca dong. TeX nuot ca dong lan dau
        xuong dong cua no, nen xoa di la tuong duong tuyet doi.
      - Comment nam CUOI dong co noi dung -> cat con lai dau %. Khong duoc
        bo not dau % do: no la lenh NOI dong cua TeX (main.tex co 5 cho),
        bo di se sinh ra mot dau cach thua.
    """
    ra = []
    for dong in text.splitlines():
        truoc, co = tach(dong)
        if co and not truoc.strip():
            continue
        ra.append(truoc + "%" if co else dong)
    # Nhieu dong trong lien nhau = mot dau ngat doan, y het mot dong trong.
    goc = "\n".join(ra)
    while "\n\n\n" in goc:
        goc = goc.replace("\n\n\n", "\n\n")
    return goc


def luong_in(text: str) -> str:
    """Dung lai dung luong ky tu ma TeX thuc su doc, de doi chieu.

    Mo hinh hoa doc lap voi ham lam sach o tren: dong chi co comment thi
    khong sinh ra gi ca, dong ket thuc bang % thi khong sinh dau xuong
    dong. Chay ham nay tren ban goc va ban da lam sach, hai ket qua phai
    trung nhau -- do la bang chung phep lam sach khong dong vao bai.
    """
    ra = []
    for dong in text.splitlines():
        truoc, co = tach(dong)
        if co and not truoc.strip():
            continue
        ra.append(truoc if co else truoc + "\n")
    out = "".join(ra)
    while "\n\n\n" in out:
        out = out.replace("\n\n\n", "\n\n")
    return out


def doc(ten: str) -> str:
    duong = SRC / ten
    if not duong.exists():
        raise SystemExit(f"  THIEU {duong}")
    return khong_bi_comment(duong.read_text(encoding="utf-8"))


def thu_thap(ten: str, da_co: set) -> list:
    """Doc de quy \\input va \\includegraphics tren cac dong con hieu luc."""
    if ten in da_co:
        return []
    da_co.add(ten)
    body = doc(ten)
    ra = [ten]
    for m in re.finditer(r"\\input\{([^}]+)\}", body):
        con = m.group(1)
        if not con.endswith(".tex"):
            con += ".tex"
        ra += thu_thap(con, da_co)
    for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", body):
        g = m.group(1)
        if (SRC / g).exists():
            ten_that = g
        else:
            hop = [g + e for e in (".pdf", ".png", ".jpg")
                   if (SRC / (g + e)).exists()]
            if not hop:
                raise SystemExit(f"  khong tim thay hinh: {g}")
            ten_that = hop[0]
        if ten_that not in da_co:
            da_co.add(ten_that)
            ra.append(ten_that)
    return ra


def main() -> int:
    files = thu_thap(MAIN, set())
    tex = [f for f in files if f.endswith(".tex")]

    # 1. Ca goi phai co DUNG MOT \documentclass.
    n = sum(len(re.findall(r"\\documentclass", doc(f))) for f in tex)
    if n != 1:
        print(f"  goi co {n} documentclass, phai co dung 1")
        return 1

    # 2. Xoa ghi chu noi bo, roi CHUNG MINH phan se in ra khong doi.
    sach = {}
    for f in tex:
        goc = (SRC / f).read_text(encoding="utf-8")
        moi = lam_sach_comment(goc)
        if luong_in(moi) != luong_in(goc):
            print(f"  {f}: lam sach comment da dong vao phan se in ra")
            return 1
        sach[f] = moi

    # 3. Khong con chu nao lo ra, ke ca trong comment.
    for f, t in sach.items():
        for xau in ("TODO", "IJNM", "thay duyet", "Thay Van"):
            if xau in t:
                print(f"  {f} van con chu '{xau}'")
                return 1

    danh_muc = "\n".join(
        f"  {f:24s} {(SRC / f).stat().st_size / 1024:5.0f} KB" for f in files)
    with zipfile.ZipFile(DICH, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            if f in sach:
                z.writestr(f, sach[f])
            else:
                z.write(SRC / f, f)
        z.writestr("README.md", README.format(danh_muc=danh_muc))

    # Ban .tex roi trong thu muc nop phai la CUNG mot noi dung.
    (DICH.parent / "main_document.tex").write_text(sach[MAIN],
                                                   encoding="utf-8")

    print(f"  {DICH.stat().st_size / 1024:6.0f} KB  {DICH.name}")
    for f in files:
        print(f"      {f}")
    print("      README.md  (tieng Anh, khong ghi chu noi bo)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
