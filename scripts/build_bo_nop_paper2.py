"""Gom moi thu can de nop Paper 2 vao MOT thu muc.

    python scripts/build_bo_nop_paper2.py [duong_dan_ban_thao.pdf]

Truoc day cac file can nop nam rai rac: ban thao PDF o goc repo, goi nguon
trong dist/, cover letter o paper2_rebuild/. Luc nop de lay nham ban cu.

TEN FILE LA TIENG ANH, co chu y. Ten file hien ra truoc mat bien tap va
phan bien khi ho tai ve. Ten tieng Viet vua thieu chuyen nghiep, vua (voi
mot hoi nghi phan bien mu) la mot goi y ve quoc tich. Ten thu muc va file
checklist thi de tieng Viet -- chung khong bao gio duoc tai len.

Ten file danh so theo DUNG thu tu upload cua Research Exchange, va khop voi
nhan ma he thong bat chon (xem 00_DOC_TRUOC_KHI_NOP.md).
"""

from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "paper" / "paper2_rebuild" / "NOP_SECURITY_AND_PRIVACY"

# (nguon, ten khi tai len). Thu tu so khop thu tu upload.
COPY = [
    (ROOT / "Paper2_rebuild.pdf",
     "01_manuscript_pdf.pdf"),
    (ROOT / "paper/paper2_rebuild/main.tex",
     "02_main_document.tex"),
    (ROOT / "paper/paper2_rebuild/dist/Paper2_rebuild.zip",
     "03_latex_supplementary.zip"),
    (ROOT / "paper/paper2_rebuild/cover_letter.tex",
     "04_cover_letter.tex"),
]

# Viet tay, khong dung toi.
KEEP = {"00_DOC_TRUOC_KHI_NOP.md", "04_cover_letter.txt"}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main() -> int:
    if len(sys.argv) > 1:
        COPY[0] = (Path(sys.argv[1]).resolve(), COPY[0][1])

    DEST.mkdir(parents=True, exist_ok=True)
    for src, _ in COPY:
        if not src.exists():
            print(f"  THIEU {src}")
            if src.suffix == ".pdf":
                print("        Ban thao PDF phai build tren Overleaf truoc,")
                print("        hoac chi duong dan: "
                      "python scripts/build_bo_nop_paper2.py <file.pdf>")
            return 1

    for src, name in COPY:
        dst = DEST / name
        old = sha(dst) if dst.exists() else None
        shutil.copy2(src, dst)
        tag = "moi" if old is None else ("DOI" if old != sha(dst)
                                         else "khong doi")
        print(f"  {dst.stat().st_size/1024:7.0f} KB  {name:28s} {tag}")

    for f in sorted(DEST.iterdir()):
        if f.name in KEEP:
            print(f"  {f.stat().st_size/1024:7.0f} KB  {f.name:28s} "
                  f"(giu nguyen)")

    print(f"\n  -> {DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
