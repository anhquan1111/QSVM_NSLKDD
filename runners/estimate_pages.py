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
    (5191, 9, 6, 9.0),    # 2026-09-21, co ca 4 tieu su, "van con 9 trang"
    (6503, 9, 6, 12.0),   # 2026-09-21 ban cuoi, do that tren Overleaf
]

# CANH BAO. Mo hinh tuyen tinh khop tu HAI diem dau du doan diem thu ba la
# 10,8 trang, con thuc te la 9,0 -- lech 1,8. Ly do: float khong chiem cho
# tuyen tinh. Khi bai dai ra, bang va hinh don vao chung trang va chia nhau
# khoang trong, nen chi phi bien cua moi float GIAM dan. Mot mo hinh cong
# don khong bat duoc dieu do.
#
# Vi vay script khong con bao mot con so tuyet doi nhu the no chac chan. No
# bao DO DOC CUC BO giua hai lan do that gan nhat -- dai luong duy nhat o
# day thuc su dung duoc, vi cau hoi luon la "them bao nhieu chu thi len mot
# trang" chu khong phai "bai nay day bao nhieu trang".

# Mo hinh tuyen tinh: trang = OVERHEAD + tu/WORDS_PER_PAGE
#                             + bang*TABLE_PAGE + hinh*FIGURE_PAGE
#
# TABLE_PAGE va FIGURE_PAGE co dinh o gia tri hop ly cho IEEEtran hai cot;
# OVERHEAD va WORDS_PER_PAGE giai tu dung hai diem hieu chuan tren.
# OVERHEAD gom khoi tieu de, abstract, keywords va danh muc tham khao.
TABLE_PAGE = 0.17
FIGURE_PAGE = 0.22
# Mot khoi IEEEbiography: anh 1in x 1.25in cong khoang 90 tu tieu su, chiem
# khoang mot phan tu cot. Khong nam trong hai diem hieu chuan (luc do bai
# chua co tieu su), nen day la uoc, va se duoc chinh khi co so trang that.
BIO_PAGE = 0.25


def _fit():
    (w1, t1, f1, p1), (w2, t2, f2, p2) = CALIBRATION[-2:]
    d_float = (t2 - t1) * TABLE_PAGE + (f2 - f1) * FIGURE_PAGE
    wpp = (w2 - w1) / ((p2 - p1) - d_float)
    overhead = p1 - w1 / wpp - t1 * TABLE_PAGE - f1 * FIGURE_PAGE
    return overhead, wpp


OVERHEAD, WORDS_PER_PAGE = _fit()


def count(path: Path) -> tuple[int, int, int, int]:
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

    n_bio = 0
    # PHAI bo comment truoc khi quet \input. Khi tieu su bi tat bang cach
    # comment dong `%\input{biographies}`, ban cu van dem du 4 khoi va bao
    # them ~1 trang khong ton tai.
    whole = re.sub(r"(?<!\\)%.*", "",
                   io.open(path, encoding="utf-8").read())
    for m in re.findall(r"\\input\{([^}]*)\}", whole):
        q = path.parent / m
        q = q if q.suffix else q.with_suffix(".tex")
        if q.exists():
            n_bio += len(re.findall(r"\\begin\{IEEEbiography",
                                    io.open(q, encoding="utf-8").read()))
    return words, n_tab, n_fig, n_bio


# Chieu cao vung chu cua IEEEtran journal, letterpaper. Hai cot nen mot
# trang chua 2 x TEXT_HEIGHT_IN "inch-cot".
TEXT_HEIGHT_IN = 9.25


def _pdf_size_in(p: Path) -> tuple[float, float] | None:
    """Kho that cua mot hinh, doc tu MediaBox. Khong doan ti le."""
    try:
        raw = p.read_bytes()
    except OSError:
        return None
    m = re.search(rb"/MediaBox\s*\[\s*([\d.+-]+)\s+([\d.+-]+)\s+"
                  rb"([\d.+-]+)\s+([\d.+-]+)", raw)
    if not m:
        return None
    x0, y0, x1, y1 = (float(v) for v in m.groups())
    return (x1 - x0) / 72.0, (y1 - y0) / 72.0


# Cho ma SAU hinh chiem tai lan do that gan nhat (9,0 trang), tinh bang
# chinh cong thuc `figure_space` duoi day tren kho ve luc do -- moi hinh khi
# ay deu la `figure` mot cot:
#   fig1 7,16x2,75  fig2 7,16x2,40  fig3 3,48x2,80
#   fig4 7,16x2,50  fig5 7,16x2,90  fig6 7,16x2,80
# => 1,337 + 1,166 + 2,800 + 1,215 + 1,409 + 1,361 = 9,29 inch-cot.
# So nay la mot phan cua diem hieu chuan: sua kho hinh thi DUNG sua no.
#
# CAP NHAT 2026-09-22. Lan do that moi nhat (6503 tu -> 12,0 trang) duoc
# lay TREN CHINH bo hinh hien tai, do 23,15 inch-cot, va tren ban con du 4
# khoi tieu su. Neu cu de moc cu 9,29 thi cho ma hinh chiem bi cong HAI
# LAN -- mot lan da nam trong diem 12,0 trang, mot lan qua so hieu chinh --
# va script in ra "thieu -1,0 trang" cung khoang nguoc dau.
CALIB_FIG_COLIN = 23.15
# So khoi tieu su co trong lan do that moi nhat. Ban hien tai da bo chung
# (tap chi Wiley khong in tieu su), nen phai TRU ra.
CALIB_N_BIO = 4

# Diem KIEM CHUNG cho rieng so hang hinh. Ban "Paper2_rebuild__8_.pdf"
# (2026-09-21) co dung 6467 tu nhu ban hien tai nhung NAM hinh hai cot:
#   fig1 2x2,75  fig2 2x2,40  fig3 3,00  fig4 2x2,50  fig5 2x2,90
#   fig6 2x2,80  => 29,70 inch-cot, tuc +1,10 trang so voi hieu chuan.
# Mo hinh khi ay bao 11,3 trang; do that ra 12,0. Tuc la no THIEU 0,7
# trang khi float lon: float khong don sat nhau ma de lai khoang hong o
# cuoi cot. Con so in ra duoi day vi the la CAN DUOI.
VALIDATION = (6467, 29.70, 12.0)


def figure_space(path: Path) -> tuple[float, list[str], list[str]]:
    """Cho ma toan bo hinh chiem, do bang "inch-cot".

    Phep noi suy theo so tu khong thay duoc hai thay doi vua roi: mot so
    hinh doi sang `figure*`, va nhung hinh con lai duoc VE LAI o kho mot
    cot nen cao gap ba lan truoc. Ca hai deu an vao so trang.

    Mot hinh ve o kho W x H:
      - `figure`:  bi thu ve be rong cot, cao H*(3,48/W) inch-cot;
      - `figure*`: cao H inch tren CA HAI cot, tuc 2H inch-cot.
    Ham tra ve CHENH LECH so voi CALIB_FIG_COLIN, quy ra trang.
    """
    s = io.open(path, encoding="utf-8").read()
    s = re.sub(r"(?<!\\)%.*", "", s)
    total, wide, narrow = 0.0, [], []
    for star, block in re.findall(
            r"\\begin\{figure(\*?)\}(.*?)\\end\{figure\*?\}", s, re.S):
        g = re.search(r"\\includegraphics\[[^]]*\]\{([^}]*)\}", block)
        if not g:
            continue
        size = _pdf_size_in(path.parent / g.group(1))
        if size is None:
            continue
        w_in, h_in = size
        if star:
            total += 2.0 * h_in
            wide.append(Path(g.group(1)).stem)
        else:
            total += h_in * (3.48 / w_in if w_in else 1.0)
            narrow.append(Path(g.group(1)).stem)
    return (total - CALIB_FIG_COLIN) / (2.0 * TEXT_HEIGHT_IN), wide, narrow


def pages(words: int, n_tab: int, n_fig: int, n_bio: int = 0) -> float:
    return (OVERHEAD + words / WORDS_PER_PAGE
            + n_tab * TABLE_PAGE + n_fig * FIGURE_PAGE
            + n_bio * BIO_PAGE)


def main() -> int:
    if len(sys.argv) < 2:
        print("dung: python runners/estimate_pages.py <main.tex>")
        return 1
    path = Path(sys.argv[1])
    if not path.is_absolute():
        path = ROOT / path

    print("  Cac lan do THAT:")
    for w, t, f, real in CALIBRATION:
        print(f"    {w:5d} tu, {t:2d} bang, {f} hinh  ->  {real:4.1f} trang")

    (w1, _, _, p1), (w2, _, _, p2) = CALIBRATION[-2:]
    slope = (w2 - w1) / (p2 - p1)          # tu tren mot trang, cuc bo
    print(f"\n  Do doc cuc bo (hai lan do gan nhat): {slope:.0f} tu / trang")

    w, t, f, b = count(path)
    print(f"\n  {path.name}: {w} tu prose, {t} bang, {f} hinh, {b} tieu su")
    delta_w = w - w2
    est = p2 + delta_w / slope
    print(f"  So voi lan do cuoi ({w2} tu -> {p2:.1f} trang): "
          f"{delta_w:+d} tu")
    print(f"  -> uoc {est:.1f} trang tu rieng so tu. Day la NOI SUY tu do "
          f"doc cuc bo,")
    print(f"     khong phai mot mo hinh tuyet doi; lan truoc mo hinh tuyet "
          f"doi lech 1,8 trang.")

    d_fig, wide, narrow = figure_space(path)
    print(f"\n  Hinh: {len(wide)} hai cot ({', '.join(wide) or '-'}), "
          f"{len(narrow)} mot cot")
    if abs(d_fig) > 0.05:
        print(f"  Cho ma hinh chiem, so voi lan do that gan nhat "
              f"(tinh tu kho that cua tung .pdf): {d_fig:+.1f} trang")
        est += d_fig
    else:
        print(f"  Kho hinh khong doi so voi lan do that gan nhat "
              f"(lech {d_fig:+.2f} trang) -- khong hieu chinh.")

    d_bio = (b - CALIB_N_BIO) * BIO_PAGE
    if abs(d_bio) > 0.05:
        print(f"  Tieu su: {b} khoi, lan do that co {CALIB_N_BIO} "
              f"-> {d_bio:+.1f} trang")
        est += d_bio

    print(f"\n  -> uoc {est:.1f} trang.")
    print(f"     Day la noi suy tu MOT diem do that gan nhat cong ba so "
          f"hieu chinh (tu, hinh, tieu su).")
    print(f"     Ba lan truoc mo hinh deu doan HUT khi bo cuc doi nhieu "
          f"(1,8 roi 0,7 trang), nen doc {est:.1f} nhu CAN DUOI.")
    for target in (10.0, 11.0):
        need = (target - est) * slope
        if need > 0:
            print(f"     de dat {target:.0f} trang: them ~{int(need)} tu")
        else:
            print(f"     da qua {target:.0f} trang khoang "
                  f"{int(-need)} tu")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
