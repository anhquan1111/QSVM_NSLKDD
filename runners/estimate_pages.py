"""Uoc luong so trang cua mot bai IEEEtran hai cot, co hieu chuan.

    python runners/estimate_pages.py paper/paper2_rebuild/main.tex

Truoc day toi doan so trang va doan sai (noi 9-10, ra 7). Script nay khong
doan: no dem so tu prose va so float, roi quy doi bang HAI he so da hieu
chuan tren chinh bai nay bang hai lan do THAT:

    613 dong nguon -> 6 trang
    698 dong nguon -> 7 trang (hon mot chut)

He so duoc luu o CALIBRATION duoi day. Moi lan co so trang that moi thi
THEM vao do, dung sua tay he so.
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (so tu prose, so bang, so hinh) -> so trang THAT.
# CHI dua vao day nhung lan da compile that va dem tay. Dung suy ra.
# So tu / so float lay bang chinh `count()` duoi day tren ban da commit.
CALIBRATION = [
    (2698, 5, 4, 6.0),    # commit e61c4cc, nguoi dung bao "6 trang"
    (3302, 7, 5, 7.2),    # commit 5e9a990, "7 trang qua duoc 1 xiu"
]

# Mo hinh tuyen tinh: trang = OVERHEAD + tu/WORDS_PER_PAGE
#                             + bang*TABLE_PAGE + hinh*FIGURE_PAGE
#
# TABLE_PAGE va FIGURE_PAGE co dinh o gia tri hop ly cho IEEEtran hai cot;
# OVERHEAD va WORDS_PER_PAGE giai tu dung hai diem hieu chuan tren.
# OVERHEAD gom khoi tieu de, abstract, keywords va danh muc tham khao.
TABLE_PAGE = 0.17
FIGURE_PAGE = 0.22


def _fit():
    (w1, t1, f1, p1), (w2, t2, f2, p2) = CALIBRATION[-2:]
    d_float = (t2 - t1) * TABLE_PAGE + (f2 - f1) * FIGURE_PAGE
    wpp = (w2 - w1) / ((p2 - p1) - d_float)
    overhead = p1 - w1 / wpp - t1 * TABLE_PAGE - f1 * FIGURE_PAGE
    return overhead, wpp


OVERHEAD, WORDS_PER_PAGE = _fit()


def count(path: Path) -> tuple[int, int, int]:
    s = io.open(path, encoding="utf-8").read()
    s = re.sub(r"(?<!\\)%.*", "", s)
    body = s.split("\\maketitle", 1)[-1]
    body = body.split("\\begin{thebibliography}", 1)[0]

    n_fig = len(re.findall(r"\\includegraphics", body))
    n_tab = len(re.findall(r"\\begin\{table", body))
    # Bang nam trong file duoc \input
    for m in re.findall(r"\\input\{([^}]*)\}", body):
        p = (path.parent / m)
        p = p if p.suffix else p.with_suffix(".tex")
        if p.exists():
            t = io.open(p, encoding="utf-8").read()
            n_tab += len(re.findall(r"\\begin\{table", t))

    prose = re.sub(r"\\begin\{(table|figure|equation|tabular)\*?\}.*?"
                   r"\\end\{\1\*?\}", " ", body, flags=re.S)
    prose = re.sub(r"\\[a-zA-Z]+\*?", " ", prose)
    prose = re.sub(r"[{}$\\&~^_]", " ", prose)
    words = len(re.findall(r"[A-Za-z][A-Za-z'\-]+", prose))
    return words, n_tab, n_fig


def pages(words: int, n_tab: int, n_fig: int) -> float:
    return (OVERHEAD + words / WORDS_PER_PAGE
            + n_tab * TABLE_PAGE + n_fig * FIGURE_PAGE)


def main() -> int:
    if len(sys.argv) < 2:
        print("dung: python runners/estimate_pages.py <main.tex>")
        return 1
    path = Path(sys.argv[1])
    if not path.is_absolute():
        path = ROOT / path

    print(f"  Mo hinh khop tu {len(CALIBRATION)} lan do that:")
    print(f"    overhead {OVERHEAD:.2f} trang, {WORDS_PER_PAGE:.0f} tu/trang, "
          f"bang {TABLE_PAGE}, hinh {FIGURE_PAGE}")
    for w, t, f, real in CALIBRATION:
        est = pages(w, t, f)
        print(f"    {w:5d} tu, {t} bang, {f} hinh -> uoc {est:4.1f}  "
              f"that {real:4.1f}  lech {est - real:+.1f}")

    w, t, f = count(path)
    est = pages(w, t, f)
    print(f"\n  {path.name}: {w} tu prose, {t} bang, {f} hinh")
    print(f"  -> uoc luong {est:.1f} trang  (khoang {est - 0.6:.1f}-{est + 0.6:.1f})")
    print(f"\n  De dat 10 trang can them khoang "
          f"{max(0, int((10.0 - est) * WORDS_PER_PAGE)):d} tu prose,")
    print("  hoac it hon neu them bang/hinh.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
