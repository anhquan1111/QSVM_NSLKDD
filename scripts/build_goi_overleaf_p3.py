r"""Dung goi Overleaf cho bai AICON 2026 -- ban CO TEN (single-blind).

Vi sao co script rieng thay vi sua thang main.tex: `main.tex` la ban lam
viec, mang chu thich ky thuat can giu lai cho nguoi doc sau. Ban gui di
thi khong nen mang theo. Script doc main.tex, ap dung dung nhung thay doi
liet ke duoi day, roi dong goi -- goc khong bi dung toi.

Script nay CHI xoa chu thich. Khong doi mot chu nao cua bai.

Moi thu khac -- cong tac an danh, link kho ma, viet tat ten, thu tu tac
gia -- nam trong chinh main.tex. Mo main.tex ra la thay dung nhung gi se
in ra; khong co thay doi nao an trong khau dong goi.

Dau % cuoi dong duoc GIU, vi do
la lenh noi dong cua TeX chu khong phai chu thich -- xoa la dinh chu.
Truoc khi ghi, script dung lai luong ky tu ma TeX thuc su doc tu ca hai
ban roi doi chieu; lech mot ky tu la dung han.

Co che \ifanonymous duoc giu nguyen trong goi: neu chair xac nhan lai la
phan bien hai chieu mu that, lat mot dong trong goi la co lai ban an danh.

    python scripts/build_goi_overleaf_p3.py
"""
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BAI = ROOT / "paper" / "paper3_aicon"
RA = BAI / "dist" / "AICON2026_named.zip"

REPO = "https://github.com/anhquan1111/QSVM_NSLKDD"
BO_COMMENT = re.compile(r"(?<!\\)%.*$")

KEM = [
    "tables/numbers_macros.tex",
    "tables/degeneracy_census.tex",
    "tables/objective_table.tex",
    "tables/remedies_table.tex",  # Bang 3, them o ban camera-ready
    "figs/fig1_tuning_trap.pdf",
    "figs/fig2_k_sweep.pdf",
    "figs/fig3_objective.pdf",
]

README = """# AICON2026 -- ban co ten

## Tai len Overleaf

1. **New Project** -> **Upload Project** -> chon file zip nay.
2. Bam **Recompile**. Compiler: **pdfLaTeX**.

`llncs.cls` co san tren Overleaf nen khong dong goi kem.

> Phai la project **MOI**. Tha zip vao mot project dang co thi Overleaf
> giai nen vao thu muc con, `main.tex` va `figs/` nam khac cho nhau va
> bao thieu file.

## Ban nay la ban CO TEN

Trang nop cua Confy+ ghi: *"This conference uses single-blind review
model. The names and affiliations of authors will be shown to the Program
Committee Members and Reviewers."* Nen bai hien du ten bon tac gia.

Neu chair xac nhan lai la phan bien hai chieu mu, doi `\\anonymousfalse`
thanh `\\anonymoustrue` o dau `main.tex` roi recompile -- khoi tac gia,
cau "our own earlier work" o muc 1, muc tai lieu [1] va link kho ma se tu
chuyen sang dang an danh.

## Kiem sau khi build

- **Dem so trang.** Short paper la **6-11 trang**. Ban an danh dung 11
  trang, ban co ten them khoi tac gia va muc tai lieu [1] day du nen co
  the sang trang 12. Qua 11 la phai cat.
- Doi chieu abstract trong PDF voi o Abstract da khai tren Confy+.

## Kiem trong repo

    python runners/make_paper3_figures.py
    python runners/make_paper3_tables.py
    python runners/audit_paper3.py
"""


def tach(dong):
    """Tra ve (phan truoc dau %, co dau % hay khong)."""
    m = BO_COMMENT.search(dong)
    return (dong[:m.start()], True) if m else (dong, False)


def luong_in(text):
    """Luong ky tu TeX thuc su doc -- dung de doi chieu truoc/sau khi don."""
    ra = []
    for dong in text.splitlines():
        truoc, co = tach(dong)
        if co and not truoc.strip():
            continue                  # dong chi co chu thich: TeX nuot ca xuong dong
        ra.append(truoc if co else truoc + "\n")
    out = "".join(ra)
    while "\n\n\n" in out:
        out = out.replace("\n\n\n", "\n\n")
    return out


def xoa_comment(text):
    ra = []
    for dong in text.splitlines():
        truoc, co = tach(dong)
        if co and not truoc.strip():
            continue
        ra.append(truoc.rstrip() + "%" if co else dong)
    s = "\n".join(ra)
    while "\n\n\n" in s:
        s = s.replace("\n\n\n", "\n\n")
    return s


def thay(s, cu, moi, nhan, it_nhat=1):
    n = s.count(cu)
    if n < it_nhat:
        sys.exit("DUNG: khong tim thay {} ({})".format(nhan, cu[:50]))
    return s.replace(cu, moi)


def main():
    goc = (BAI / "main.tex").read_bytes().decode("utf-8").replace("\r\n", "\n")
    s = goc

    truoc_don = s
    s = xoa_comment(s)
    if luong_in(truoc_don) != luong_in(s):
        sys.exit("DUNG: xoa chu thich lam doi phan in ra")

    # cong kiem
    for xau in ("TODO", "FIXME", "\\anonymoustrue"):
        if xau in s:
            sys.exit("DUNG: con sot '{}'".format(xau))
    for xau, can in (("\\anonymousfalse", 1), ("\\documentclass", 1), (REPO, 1),
                     # mot o nhanh an danh (co san), mot o nhanh co ten (vua them)
                     ("\\titlerunning{A Tuning Trap", 2)):
        if s.count(xau) != can:
            sys.exit("DUNG: '{}' xuat hien {} lan, can {}"
                     .format(xau, s.count(xau), can))

    # Moi \\input va \\includegraphics trong bai phai co trong goi. Ban
    # camera-ready them Bang 3 ma quen dua vao KEM: goi van dung "xanh",
    # con Overleaf thi vo build vi thieu file.
    tex = (BAI / "main.tex").read_text(encoding="utf-8")
    can = set(p + ".tex" for p in re.findall(r"\\input\{([^}]+)\}", tex))
    can |= set(re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex))
    ngoai = sorted(can - set(KEM))
    if ngoai:
        sys.exit("DUNG: bai dung file khong co trong goi: " + ", ".join(ngoai))
    thieu = [p for p in KEM if not (BAI / p).exists()]
    if thieu:
        sys.exit("DUNG: thieu file " + ", ".join(thieu))

    RA.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(RA, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("main.tex", s)
        for p in KEM:
            z.write(BAI / p, p)
        z.writestr("README.md", README)

    print("  {}".format(RA.relative_to(ROOT)))
    print("  main.tex : {} dong -> {} dong, {} chu thich da go"
          .format(len(goc.splitlines()), len(s.splitlines()),
                  len(goc.splitlines()) - len(s.splitlines())))
    print("  phan in ra: khong doi mot ky tu")
    print("  kem theo : {} file".format(len(KEM) + 1))
    print("  kich thuoc: {:,} byte".format(RA.stat().st_size))


if __name__ == "__main__":
    main()
