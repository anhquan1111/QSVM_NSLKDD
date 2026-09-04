"""Kiem cau truc ban thao khi khong co LaTeX tren may.

Khong thay the duoc pdflatex, nhung bat duoc dung nhung loi da that su xay ra
trong repo nay: heredoc an mat dau `\\` cuoi dong bang, `sed` chen CR lam vo
`\\ref{}`, macro dung ma chua dinh nghia, va ky tu `_` `&` `%` lot ra ngoai
che do toan.

    python runners/check_latex.py

Doc tu \\input cua main_revision.tex nen chi kiem dung nhung manh thuc su
duoc dua vao ban thao -- main.tex cu (dung de doi chieu) khong bi tinh.
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "paper/paper1/main_revision.tex"

BS = chr(92)
CMD = re.compile(BS + BS + r"([A-Za-z]+)")

# Macro cua IEEEtran + cac goi duoc nap trong main_revision.tex. Danh sach nay
# co y giu ngan: chi can du de moi macro TU DINH NGHIA bi bo quen thi lo ra.
KNOWN = set("""
documentclass usepackage begin end input include graphicspath newcommand
newtheorem theoremstyle title author thanks markoff markboth maketitle
MakeLowercase textit textbf textsc emph texttt underline
section subsection subsubsection paragraph label ref cite pageref
item itemize enumerate description figure figures table tabular multicolumn
cmidrule toprule midrule bottomrule centering caption includegraphics
footnotesize small normalsize large Large scriptsize tiny
setlength tabcolsep arraystretch columnwidth textwidth linewidth
frac dfrac sum prod int lim max min arg log exp sqrt binom
alpha beta gamma delta epsilon varepsilon zeta eta theta kappa lambda mu nu
xi pi rho sigma tau phi varphi chi psi omega Delta Gamma Lambda Omega Phi Pi
Sigma Theta Xi Psi
mathbb mathcal mathrm mathbf mathit mathsf bm boldsymbol text
leq geq neq approx sim simeq propto times cdot cdots dots ldots ast
in notin subset subseteq cup cap forall exists to rightarrow leftarrow
mapsto langle rangle lvert rvert lVert rVert left right big Big bigl bigr
quad qquad hspace vspace medskip smallskip bigskip par noindent newline
gtrsim lesssim ll gg pm mp infty partial nabla
begingroup endgroup relax protect ensuremath
definition lemma assumption problem remark proof
IEEEkeywords abstract thebibliography bibitem
url href hidelinks
ZZ Zmap QSVM Fmac
""".split()) | set("Bigl Bigr ge le prime v widetilde eqref appendices appendix "
            "tfrac hfill blacksquare otimes dagger mathbb Var".split())

FAIL: list[str] = []
INFO: list[str] = []


def fail(f: str, line: int, msg: str) -> None:
    FAIL.append(f"{f}:{line}: {msg}")


def strip_comments(text: str) -> list[str]:
    """Bo phan chu thich nhung GIU nguyen so dong va giu `\\%`."""
    out = []
    for raw in text.split("\n"):
        keep, i = [], 0
        while i < len(raw):
            c = raw[i]
            if c == BS and i + 1 < len(raw):
                keep.append(raw[i:i + 2])
                i += 2
                continue
            if c == "%":
                break
            keep.append(c)
            i += 1
        out.append("".join(keep))
    return out


def inputs_of(path: Path) -> list[Path]:
    text = io.open(path, encoding="utf-8").read()
    got = []
    for t in re.findall(BS + BS + r"input\{([^}]*)\}", text):
        for cand in (path.parent / t, path.parent / (t + ".tex")):
            if cand.exists():
                got.append(cand)
                break
        else:
            fail(path.name, 0, f"\\input khong co file: {t}")
    return got


def check_file(path: Path) -> tuple[set[str], set[str], set[str], set[str]]:
    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    lines = strip_comments(io.open(path, encoding="utf-8").read())
    body = "\n".join(lines)

    # 1) dong ket thuc hang bang bi an mat mot dau gach cheo
    for i, ln in enumerate(lines, 1):
        r = ln.rstrip()
        if r.endswith(BS) and not r.endswith(BS * 2):
            fail(rel, i, "dong ket thuc bang mot dau \\ don (heredoc an mat?)")

    # 2) can bang $. Math trong dong duoc phep vat qua xuong dong, nhung KHONG
    #    duoc vat qua dong trong -- do la loi that su ("Missing $ inserted").
    open_at = 0
    blank_since = None
    for i, ln in enumerate(lines, 1):
        if not ln.strip():
            if open_at:
                blank_since = blank_since or i
            continue
        for m in re.finditer(r"\$", ln):
            if m.start() and ln[m.start() - 1] == BS:
                continue
            if open_at:
                if blank_since:
                    fail(rel, open_at, "math mode mo o day va vat qua dong "
                                       f"trong (dong {blank_since})")
                open_at, blank_since = 0, None
            else:
                open_at = i
    if open_at:
        fail(rel, open_at, "math mode mo o day va khong duoc dong")

    # 3) moi truong long nhau
    stack: list[tuple[str, int]] = []
    for i, ln in enumerate(lines, 1):
        for kind, name in re.findall(BS + BS + r"(begin|end)\{([^}]*)\}", ln):
            if kind == "begin":
                stack.append((name, i))
            else:
                if not stack:
                    fail(rel, i, f"\\end{{{name}}} khong co \\begin")
                elif stack[-1][0] != name:
                    fail(rel, i, f"\\end{{{name}}} khong khop "
                                 f"\\begin{{{stack[-1][0]}}} dong {stack[-1][1]}")
                    stack.pop()
                else:
                    stack.pop()
    for name, i in stack:
        fail(rel, i, f"\\begin{{{name}}} khong duoc dong")

    # 4) can bang ngoac nhon toan file
    depth = 0
    for i, ln in enumerate(lines, 1):
        j = 0
        while j < len(ln):
            if ln[j] == BS:
                j += 2
                continue
            if ln[j] == "{":
                depth += 1
            elif ln[j] == "}":
                depth -= 1
                if depth < 0:
                    fail(rel, i, "thua dau }")
                    depth = 0
            j += 1
    if depth:
        fail(rel, 0, f"con {depth} dau {{ chua dong")

    # 5) ky tu dac biet lot ra ngoai math -- chi soat `_` va `&` ngoai bang.
    #    Doi so cua nhung lenh duoi day khong phai van ban nen `_` trong do la
    #    hop le (ten file, khoa nhan, ten bien trong \texttt).
    verbatim_arg = re.compile(
        BS + BS + r"(?:input|include|includegraphics(?:\[[^\]]*\])?|graphicspath"
        r"|label|ref|pageref|cite|bibitem|url|href|texttt|path)\{[^}]*\}")
    #    Math trong dong co the vat qua nhieu dong, nen phai theo doi trang thai
    #    xuyen dong chu khong quet tung dong roi cat cap `$...$` tai cho.
    math_env = re.compile(r"(equation|align|gather|eqnarray|displaymath|array"
                          r"|multline|split)\*?")
    in_tab = in_math_env = in_dollar = False
    for i, ln in enumerate(lines, 1):
        if re.search(BS + BS + r"begin\{" + math_env.pattern, ln):
            in_math_env = True
        if re.search(BS + BS + r"end\{" + math_env.pattern, ln):
            in_math_env = False
            continue
        if in_math_env or re.match(r"\s*" + BS + BS
                                   + r"(newcommand|renewcommand)", ln):
            continue
        if re.search(BS + BS + r"begin\{tabular", ln):
            in_tab = True
        if re.search(BS + BS + r"end\{tabular", ln):
            in_tab = False

        # Xoa doi so khong-phai-van-ban, roi xoa moi doan dang o trong math.
        masked = list(verbatim_arg.sub(lambda m: " " * len(m.group()), ln))
        for j, c in enumerate(masked):
            if c == BS:
                continue
            if c == "$" and (j == 0 or masked[j - 1] != BS):
                in_dollar = not in_dollar
                masked[j] = " "
            elif in_dollar:
                masked[j] = " "
        outside = re.sub(BS + BS + r"[A-Za-z]+", "", "".join(masked))
        for ch in ("_",) + (() if in_tab else ("&",)):
            for m in re.finditer(re.escape(ch), outside):
                if m.start() and outside[m.start() - 1] == BS:
                    continue
                fail(rel, i, f"ky tu '{ch}' khong duoc escape va khong o trong $...$")

    cmds = set(CMD.findall(body))
    defs = set(re.findall(BS + BS + r"(?:newcommand|renewcommand)\{?" + BS
                          + BS + r"([A-Za-z]+)", body))
    defs |= set(re.findall(BS + BS + r"newtheorem\{([A-Za-z]+)\}", body))
    labels = set(re.findall(BS + BS + r"label\{([^}]*)\}", body))
    refs = set(re.findall(BS + BS + r"(?:page)?ref\{([^}]*)\}", body))
    cites: set[str] = set()
    for m in re.findall(BS + BS + r"cite\{([^}]*)\}", body):
        cites |= {k.strip() for k in m.split(",") if k.strip()}
    bibs = set(re.findall(BS + BS + r"bibitem\{([^}]*)\}", body))
    return cmds | defs, labels | bibs, refs, cites - bibs


def main() -> int:
    # Doi so tuy chon: duong dan toi mot main .tex khac. Dung de tu kiem chinh
    # bo kiem nay tren mot ban sao da co y lam hong.
    main_tex = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else MAIN
    global ROOT
    if main_tex != MAIN:
        ROOT = main_tex.parent.parent
    files = [main_tex] + inputs_of(main_tex)
    all_cmds: set[str] = set()
    all_lab: set[str] = set()
    all_ref: set[str] = set()
    all_cite: set[str] = set()
    all_bib: set[str] = set()

    for f in files:
        c, lab, ref, cite = check_file(f)
        all_cmds |= c
        all_lab |= lab
        all_ref |= ref
        all_cite |= cite
        body = io.open(f, encoding="utf-8").read()
        all_bib |= set(re.findall(BS + BS + r"bibitem\{([^}]*)\}", body))

    unknown = sorted(all_cmds - KNOWN)
    if unknown:
        INFO.append("macro chua co trong danh sach quen (kiem tay): "
                    + ", ".join(BS + u for u in unknown))

    for r in sorted(all_ref - all_lab):
        if r:
            FAIL.append(f"\\ref{{{r}}} khong co \\label tuong ung")
    for c in sorted(all_cite - all_bib):
        FAIL.append(f"\\cite{{{c}}} khong co \\bibitem tuong ung")

    unused = sorted(all_bib - all_cite)
    if unused:
        INFO.append(f"{len(unused)} muc tai lieu chua duoc trich trong ban "
                    f"revision (binh thuong neu con dang viet): "
                    + ", ".join(unused[:12]) + (" ..." if len(unused) > 12 else ""))

    print("=" * 78)
    print(f"  KIEM CAU TRUC {main_tex.name} -- {len(files)} file")
    print("=" * 78)
    for m in INFO:
        print("  [ghi chu] " + m)
    if FAIL:
        print()
        for m in FAIL:
            print("  [LOI] " + m)
        print(f"\n{len(FAIL)} loi. Khong the coi la bien dich duoc.")
        return 1
    print("\nKhong thay loi cau truc. (Van CAN chay pdflatex truoc khi nop.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
