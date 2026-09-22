"""Gom moi thu can de nop Paper 2 vao MOT thu muc.

    python scripts/build_bo_nop_paper2.py [duong_dan_ban_thao.pdf]

Truoc day cac file can nop nam rai rac: ban thao PDF o goc repo, goi nguon
trong dist/, cover letter o paper2_rebuild/. Luc nop de lay nham ban cu.
Script nay gom chung lai va dan nhan theo thu tu 01/02/03.

Hai file tai lieu trong thu muc dich (00_DOC_TRUOC_KHI_NOP.md va
03_cover_letter.txt) la viet tay, script KHONG ghi de.

CHAY LAI moi khi sua bai, neu khong se nop nham ban cu.
"""

from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "paper" / "paper2_rebuild" / "NOP_SECURITY_AND_PRIVACY"

# (nguon, ten trong thu muc nop)
COPY = [
    (ROOT / "Paper2_rebuild.pdf", "01_ban_thao.pdf"),
    (ROOT / "paper/paper2_rebuild/dist/Paper2_rebuild.zip", "02_nguon_latex.zip"),
    (ROOT / "paper/paper2_rebuild/cover_letter.tex", "03_cover_letter.tex"),
]

# Viet tay, khong dung toi.
KEEP = {"00_DOC_TRUOC_KHI_NOP.md", "03_cover_letter.txt"}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main() -> int:
    if len(sys.argv) > 1:
        COPY[0] = (Path(sys.argv[1]).resolve(), "01_ban_thao.pdf")

    DEST.mkdir(parents=True, exist_ok=True)
    for src, name in COPY:
        if not src.exists():
            print(f"  THIEU {src}")
            if name == "01_ban_thao.pdf":
                print("        Ban thao PDF phai build tren Overleaf truoc.")
                print("        Hoac chi duong dan: "
                      "python scripts/build_bo_nop_paper2.py <file.pdf>")
            return 1

    for src, name in COPY:
        dst = DEST / name
        old = sha(dst) if dst.exists() else None
        shutil.copy2(src, dst)
        new = sha(dst)
        tag = "moi" if old is None else ("DOI" if old != new else "khong doi")
        print(f"  {dst.stat().st_size/1024:7.0f} KB  {name:24s} {tag}")

    for f in sorted(DEST.iterdir()):
        if f.name in KEEP:
            print(f"  {f.stat().st_size/1024:7.0f} KB  {f.name:24s} (giu nguyen)")

    print(f"\n  -> {DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
