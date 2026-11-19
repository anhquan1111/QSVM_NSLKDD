"""Dong goi ban Paper 1 cho Quantum Machine Intelligence de tai len Overleaf.

Goi chua main.tex cua paper/paper1_qmi/ va moi file no can (\\input,
\\includegraphics), lan theo de quy. File nao khong co trong paper1_qmi/ thi
lay tu paper/paper1/ (hinh figs_revision/, bang so tables/) va dat o CUNG
duong dan tuong doi -- nen trong goi moi duong dan deu dung nhu luc viet.

    uv run python runners/make_qmi_zip.py
    -> paper/paper1_qmi/build/Paper1_QMI_overleaf.zip

Kiem truoc khi ghi xong: dung mot file co \\documentclass; moi \\input va
\\includegraphics tro toi file co trong goi. Sai thi exit 1.
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QMI = ROOT / "paper/paper1_qmi"
OLD = ROOT / "paper/paper1"
OUT = QMI / "build/Paper1_QMI_overleaf.zip"

# File cua mau Springer: khong duoc \input nen phai them tay
TEMPLATE = ["sn-jnl.cls", "sn-mathphys-num.bst"]

INPUT_RE = re.compile(r"\\input\{([^}]*)\}")
GRAPHIC_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}")


def strip_comments(text: str) -> str:
    """Bo phan sau dau % chua escape: lenh nam trong chu thich khong tinh."""
    return re.sub(r"(?<!\\)%.*", "", text)


def resolve(rel: str, exts: tuple[str, ...]) -> Path | None:
    """Tim file theo thu tu: paper1_qmi/ truoc, paper1/ sau."""
    for base in (QMI, OLD):
        for ext in exts:
            p = base / (rel + ext)
            if p.is_file():
                return p
    return None


def collect(main: Path) -> tuple[dict[str, Path], list[str]]:
    """Tra ve {duong dan trong goi: file nguon} va danh sach loi."""
    files: dict[str, Path] = {"main.tex": main}
    errors: list[str] = []
    todo = [main]
    while todo:
        f = todo.pop()
        text = strip_comments(f.read_text(encoding="utf-8"))
        for rel in INPUT_RE.findall(text):
            p = resolve(rel, ("", ".tex"))
            if p is None:
                errors.append(f"{f.relative_to(ROOT)}: khong thay \\input{{{rel}}}")
                continue
            arc = rel if rel.endswith(".tex") else rel + ".tex"
            if arc not in files:
                files[arc] = p
                todo.append(p)
        for rel in GRAPHIC_RE.findall(text):
            p = resolve(rel, ("", ".pdf", ".png"))
            if p is None:
                errors.append(f"{f.relative_to(ROOT)}: thieu hinh {rel}")
                continue
            files.setdefault(rel if Path(rel).suffix else rel + p.suffix, p)
    for name in TEMPLATE:
        files[name] = QMI / name
    return files, errors


def main() -> int:
    files, errors = collect(QMI / "main.tex")
    docclass = [a for a, p in files.items() if a.endswith(".tex") and
                re.search(r"\\documentclass",
                          strip_comments(p.read_text(encoding="utf-8")))]
    if docclass != ["main.tex"]:
        errors.append(f"can dung mot file \\documentclass, thay: {docclass}")
    if errors:
        for e in errors:
            print("LOI:", e)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, p in sorted(files.items()):
            z.write(p, arc)
    from_old = sorted(a for a, p in files.items() if OLD in p.parents)
    print(f"Ghi {OUT.relative_to(ROOT)}: {len(files)} file "
          f"({len(from_old)} lay tu paper/paper1/)")
    for a in from_old:
        print("  tu paper1:", a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
