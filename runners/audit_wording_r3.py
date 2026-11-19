"""Soat cach dung chu ma R3 (TETC, vong R1) bat loi, va dau vet cua ban sua cu.

`audit_prose.py` kiem CON SO trong cau van. Script nay kiem CACH NOI:

  1. "exponential" di cung "concentrat..." -- ta chi do vai do rong mach,
     khong du de goi la tap trung luy thua (R3).
  2. Dong tu nhan qua noi do tap trung voi ket qua -- ta chi co tuong quan (R3).
  3. "parity" / "on par" / "tied" -- khong bac bo duoc khac biet khong phai la
     bang nhau (R3). Bo qua "parity function(s)" (nghia toan hoc o phu luc).
  4. Nhac phan bien hay ban da nop (\\revnote, "reviewer", "submitted version")
     -- AE cua TETC che dieu nay; ban nop tap chi moi khong duoc con.

Moi cau vi pham in ra kem file:dong. Het vi pham -> exit 0.

    uv run python runners/audit_wording_r3.py                    # paper/paper1
    uv run python runners/audit_wording_r3.py paper/paper1_qmi   # ban viet lai
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CAUSAL = (r"\b(destroy\w*|caus\w*|driv\w*|explain\w*|responsible|due to|because"
          r"|leads? to|led to|results? in|follows? it|is why)\b")


def causal_concentration(s: str) -> bool:
    """Cau gan quan he nhan qua cho tuong quan do tap trung <-> ket qua.

    Hai dang: (a) do tap trung / do rong mach + dong tu nhan qua;
    (b) goi so do Gram matrix cua ta la "mechanism". Cau ky thuat co
    "Because ... Gram matrix" (cach tinh kernel) khong bi bat.
    """
    a = re.search(r"concentrat|flatten|widen", s, re.I) and re.search(CAUSAL, s, re.I)
    b = (re.search(r"\bmechanism\b", s, re.I) and re.search(r"Gram|concentrat", s, re.I)
         and re.search(r"\b(we|our|here|this|the)\b", s, re.I))
    return bool(a or b)


def own_exponential(s: str) -> bool:
    """'exponential' + 'concentrat' ma noi ve so do cua ta.

    Cau chi thuat lai dinh ly cua Thanasilp 2024 (co \\cite, khong co
    we/our/here/this) thi duoc phep: do la ket qua cua ho, khong phai cua ta.
    """
    if not (re.search(r"exponential", s, re.I) and re.search(r"concentrat", s, re.I)):
        return False
    cites_theorem = r"\cite{thanasilp2024}" in s
    about_us = re.search(r"\b(we|our|here|this)\b", s, re.I)
    return not cites_theorem or bool(about_us)


RULES: list[tuple[str, callable]] = [
    ("exponential + concentration (noi ve so do cua ta)", own_exponential),
    ("nhan qua: concentration -> ket qua", causal_concentration),
    ("parity / on par / tied",
     lambda s: re.search(r"\bparity\b(?!\s+functions?)|\bon par\b|\btied\b", s, re.I)),
    ("nhac phan bien / ban da nop",
     lambda s: re.search(r"\\revnote|\\begin\{revbody\}|\breviewers?\b"
                         r"|submitted version|\bwe withdraw\b", s, re.I)),
]


def sentences(path: Path) -> list[tuple[int, str]]:
    """Tach file .tex thanh cau, giu so dong bat dau cua moi cau."""
    out: list[tuple[int, str]] = []
    buf, start = [], 0
    for i, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        # Bo chu thich LaTeX (khong dung \%)
        line = re.sub(r"(?<!\\)%.*", "", raw).strip()
        if not line:
            if buf:
                out.append((start, " ".join(buf)))
                buf = []
            continue
        if not buf:
            start = i
        buf.append(line)
        joined = " ".join(buf)
        # Cat cau o dau cham + khoang trang; phan con lai giu cho cau sau
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\\$])", joined)
        if len(parts) > 1:
            for p in parts[:-1]:
                out.append((start, p))
            buf, start = [parts[-1]], i
    if buf:
        out.append((start, " ".join(buf)))
    return out


def main() -> int:
    base = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "paper/paper1")
    files = sorted(base.glob("sections/*.tex")) + sorted(base.glob("*.tex"))
    # Bo thu phan hoi, ban chu thich, va danh muc tham khao (ten bai Thanasilp
    # 2024 co chu "Exponential concentration" -- trich ten bai thi duoc)
    skip = ("response_letter.tex", "main_annotated.tex", "bibliography.tex")
    files = [f for f in files if f.name not in skip]
    if not files:
        print(f"Khong thay file .tex trong {base}")
        return 1
    hits = 0
    for name, rule in RULES:
        found = [(f, ln, s) for f in files for ln, s in sentences(f) if rule(s)]
        print(f"\n== {name}: {len(found)}")
        for f, ln, s in found:
            print(f"  {f.relative_to(ROOT)}:{ln}  {s[:160]}")
        hits += len(found)
    print(f"\nTONG vi pham: {hits}")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
