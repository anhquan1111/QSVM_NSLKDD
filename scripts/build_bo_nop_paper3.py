"""Gom bo file nop bai AICON vao MOT thu muc.

    python scripts/build_bo_nop_paper3.py <ban_an_danh.pdf> [ban_co_ten.pdf]

Bai nay nguy hiem hon Paper 2 vi co HAI ban PDF gan giong nhau, va nop nham
ban co ten vao mot hoi nghi phan bien hai chieu mu la bi loai thang. Nen:

  * Ban an danh -> ten file noi ro la ban NOP
  * Ban co ten  -> ten file noi ro la KHONG DUOC NOP, va script tu KIEM
    rang no that su co ten con ban kia that su khong co.

Phep kiem giai nen stream PDF roi doc chu, chu khong tim byte tho -- noi
dung PDF bi nen nen tim byte tho luon tra ve "sach" mot cach gia tao.

TEN FILE LA TIENG ANH. Voi mot hoi nghi mu hai chieu, ten file tieng Viet
la mot goi y ve quoc tich -- phan bien tai file ve la thay ten file.
"""

from __future__ import annotations

import re
import shutil
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "paper" / "paper3_aicon" / "NOP_AICON2026"

# Chuoi danh tinh. Ban an danh KHONG duoc chua cai nao; ban co ten PHAI chua.
IDENTITY = ["Danang", "votrananhquan", "University of Science"]


def pdf_text(path: Path) -> str:
    raw = path.read_bytes()
    out = []
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", raw, re.S):
        try:
            out.append(zlib.decompress(m.group(1)).decode("latin-1"))
        except Exception:
            pass
    blob = " ".join(out)
    return " ".join(re.findall(r"\(((?:[^()\\]|\\.)*)\)", blob))


def found(path: Path) -> list[str]:
    t = pdf_text(path).lower()
    return [n for n in IDENTITY if n.lower() in t]


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    anon = Path(sys.argv[1]).resolve()
    named = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None

    for p in [anon] + ([named] if named else []):
        if not p.exists():
            print(f"  THIEU {p}")
            return 1

    # CONG AN DANH. Nham hai file la hong ca bai, nen kiem truoc khi chep.
    hits = found(anon)
    if hits:
        print(f"  DUNG -- ban dinh nop CO danh tinh: {hits}")
        print(f"         {anon.name}")
        print("         Co the ban da dua nham ban co ten. Kiem lai.")
        return 1
    print(f"  ban an danh sach  : {anon.name}")

    if named:
        nh = found(named)
        if not nh:
            print(f"  CANH BAO -- ban 'co ten' lai KHONG co danh tinh nao:")
            print(f"              {named.name}")
            print("              Hai file co the bi dua nguoc nhau.")
            return 1
        print(f"  ban co ten dung   : {named.name} ({nh})")

    DEST.mkdir(parents=True, exist_ok=True)
    shutil.copy2(anon, DEST / "01_SUBMIT_THIS_anonymous.pdf")
    print(f"  -> 01_SUBMIT_THIS_anonymous.pdf")
    if named:
        shutil.copy2(named, DEST / "99_DO_NOT_SUBMIT_named_preview.pdf")
        print(f"  -> 99_DO_NOT_SUBMIT_named_preview.pdf")

    src = ROOT / "paper/paper3_aicon/dist/AICON2026_paper3.zip"
    if src.exists():
        shutil.copy2(src, DEST / "02_latex_source.zip")
        print(f"  -> 02_latex_source.zip")

    print(f"\n  -> {DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
