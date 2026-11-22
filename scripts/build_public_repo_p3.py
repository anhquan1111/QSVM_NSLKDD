"""Dung repo CONG KHAI rieng cho bai AICON 2026 (Paper 3), tu repo nay.

    python scripts/build_public_repo_p3.py [thu_muc_dich]

Muc Reproducibility cua ban camera-ready tro toi repo nay. Repo goc
(QSVM_NSLKDD) khong dung lam link duoc: no chua ca hai bai khac dang cho
phan bien, va README cua no noi ve NSL-KDD. Script chep ra cay toi thieu du
chay lai moi so trong bai (giong scripts/build_anon_mirror.py), cong them
phan camera-ready, roi:
  - lat main.tex ve ban CO TEN va xoa moi dong comment (ghi chu noi bo);
  - doi link GitHub trong bai thanh link repo nay;
  - thay khoi kiem link mirror an danh trong audit bang kiem link repo nay;
  - quet ca cay tim chuoi rieng tu (email ca nhan, duong dan may). Con mot
    chuoi la DUNG.
Thu muc .git cua dich duoc giu nguyen de commit tiep.
"""
from __future__ import annotations

import io
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_NAME = "aicon2026-tuning-trap"
REPO_URL = f"https://github.com/anhquan1111/{REPO_NAME}"
OLD_URL = "https://github.com/anhquan1111/QSVM_NSLKDD"

# Chuoi khong duoc xuat hien trong cay. Email lien he cua thay Tuan in trong
# bai nen duoc phep; email ca nhan cua cac tac gia khac thi khong.
FORBIDDEN = [
    "votrananhquan", "anh1303052005", "nguyenvan@dut", "/home/quan",
    "C:\\Users", "D:/Documents", "QSVM_NSLKDD", "4open.science",
]

# (nguon, dich). Thu muc thi chep ca cay.
COPY = [
    ("runners/run_paper3_selection.py", "runners/run_paper3_selection.py"),
    ("runners/run_paper3_camera_ready.py", "runners/run_paper3_camera_ready.py"),
    ("runners/make_paper3_figures.py", "runners/make_paper3_figures.py"),
    ("runners/make_paper3_tables.py", "runners/make_paper3_tables.py"),
    ("runners/audit_paper3.py", "runners/audit_paper3.py"),
    ("results/unsw/c_tuning_results.json", "results/unsw/c_tuning_results.json"),
    ("results/unsw/c1_results.json", "results/unsw/c1_results.json"),
    ("results/unsw/c3_results_statevector.json",
     "results/unsw/c3_results_statevector.json"),
    ("results/unsw/c3_results_statevector_C1.json",
     "results/unsw/c3_results_statevector_C1.json"),
    ("results/unsw/c4_results_C1.json", "results/unsw/c4_results_C1.json"),
    ("results/unsw/c4_revision/c4_per_run_unsw_natural_refit_per_N.csv",
     "results/unsw/c4_revision/c4_per_run_unsw_natural_refit_per_N.csv"),
    ("results/unsw/c4_revision/cache/tuned_once_UNSW_NB15.json",
     "results/unsw/c4_revision/cache/tuned_once_UNSW_NB15.json"),
    ("results/unsw/paper3", "results/unsw/paper3"),
    ("models/unsw/qsvm_cache/multirun", "models/unsw/qsvm_cache/multirun"),
    ("data/unsw/processed_data/multi_run", "data/unsw/processed_data/multi_run"),
    ("data/unsw/processed_data/UNSW_Train_Cleaned.parquet",
     "data/unsw/processed_data/UNSW_Train_Cleaned.parquet"),
    ("data/unsw/processed_data/UNSW_Test_Cleaned.parquet",
     "data/unsw/processed_data/UNSW_Test_Cleaned.parquet"),
    ("paper/paper3_aicon/figs", "paper/paper3_aicon/figs"),
    ("paper/paper3_aicon/tables", "paper/paper3_aicon/tables"),
    ("paper/paper3_aicon/main.tex", "paper/paper3_aicon/main.tex"),
]

# Khoi kiem link mirror an danh + cong tac an danh trong audit_paper3.py.
# Trong repo cong khai khong con cong tac, link la link repo nay.
AUDIT_OLD_START = "    # Dong gop thu 4 cua bai la"
AUDIT_OLD_END = '"co bo dung goi Overleaf ban co ten")\n'
AUDIT_NEW = f"""\
    # The Reproducibility section must point at this repository.
    check("{REPO_URL}" in body,
          "Reproducibility section links this repository")
"""

REQUIREMENTS = """\
numpy==2.4.3
pandas==2.3.3
scikit-learn==1.8.0
scipy==1.17.1
matplotlib==3.10.8
pyarrow==25.0.1
qiskit==2.3.0
qiskit-machine-learning==0.9.0
"""

LICENSE = """\
MIT License

Copyright (c) 2026 Quan Tran Anh Vo, Minh Tuan Pham, Quang Anh Nguyen,
Nguyen Nang Hung Van

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

README = r"""# A Tuning Trap in Quantum-Kernel Intrusion Detection

Code, data and audit checks for the paper

> Quan Tran Anh Vo, Minh Tuan Pham, Quang Anh Nguyen, Nguyen Nang Hung Van.
> *When Model Selection Manufactures a Finding: A Tuning Trap in
> Quantum-Kernel Intrusion Detection.* EAI AICON 2026 (to appear in the
> LNICST series, Springer).

Every figure, table and number in the paper can be recomputed from this
repository. The quantum kernel is simulated exactly (statevector); no quantum
hardware and no GPU is needed.

## Contents

```
runners/   the scripts that produce every figure, table and number
results/   the stored measurements the paper cites
models/    cached quantum Gram matrices (5 runs, 100x100, exact statevector)
data/      the preprocessed UNSW-NB15 records and the sampled subsets
paper/     the figures, tables and LaTeX source of the paper
```

## Reproducing the paper

```bash
pip install -r requirements.txt

python runners/run_paper3_selection.py     # selection on the original grid
python runners/run_paper3_camera_ready.py  # remedies, objectives, N = 500
python runners/make_paper3_figures.py      # Figures 1-3
python runners/make_paper3_tables.py       # tables and the number macros
python runners/audit_paper3.py             # every check must pass
```

Tested with Python 3.12 and the versions pinned in `requirements.txt`.

## Reproduction gates

`run_paper3_selection.py` refuses to write a new number unless it first
reproduces already-published ones from the same code path: the
cross-validated F1 at the five original grid points, and the test-set means
at the tuned and at the neutral regularisation constant. It prints the
deviations and exits non-zero if any exceeds 1e-9.

`run_paper3_camera_ready.py` re-draws the five N = 100 subsets from the
cleaned data and requires them to match the stored ones exactly, and
requires its quantum Gram matrices to match the cached ones, before it
measures anything at N = 500.

Small deviations on a different BLAS or scikit-learn build would not change
the argument, but they should be visible rather than silent, which is why
the gates print them.

## The audit

`audit_paper3.py` is the check described in the paper. It asserts that

1. every number in the paper recomputes from the stored artifacts, and no
   literal decimal appears in the prose;
2. the invariants the argument rests on still hold, for instance that on
   the original grid the quantum kernel's best non-degenerate score lies
   below the degenerate floor while each classical kernel's lies above it;
3. the degeneracy census scans all models and all rows, not only the ones
   the finding was expected in.

It also fails if any audit function in the file is never called.

## Data

`data/unsw/processed_data/` holds cleaned records derived from the public
UNSW-NB15 dataset (N. Moustafa and J. Slay, MilCIS 2015). The original
dataset and its terms of use are at
<https://research.unsw.edu.au/projects/unsw-nb15-dataset>.

`results/unsw/c4_revision/` holds measurements from a companion study by the
same authors. The paper recomputes one quantity from them that the companion
does not report.

## Notes

Comments inside the scripts are partly in Vietnamese. The code (names,
functions, outputs) is in English.

## License

Code: MIT (see `LICENSE`). UNSW-NB15 remains under its original terms.
"""


def clean_tex(s: str) -> tuple[str, int]:
    """Lat ve ban co ten, doi link, xoa moi dong comment."""
    s = re.sub(r"\\newif\\ifanonymous\s*\n", "", s)
    s = re.sub(r"\\anonymous(true|false)\s*\n", "", s)
    # Xoa comment TRUOC khi cat nhanh: comment co the chua chu "\fi".
    s = re.sub(r"^[ \t]*%.*\n", "", s, flags=re.M)
    n_cut = 0
    while True:
        m = re.search(r"\\ifanonymous(.*?)\\else(.*?)\\fi", s, re.S)
        if not m:
            break
        s = s[:m.start()] + m.group(2) + s[m.end():]
        n_cut += 1
    s = s.replace(OLD_URL, REPO_URL)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s, n_cut


def main() -> int:
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        ROOT / "paper/paper3_aicon" / REPO_NAME)
    dest.mkdir(parents=True, exist_ok=True)
    for child in dest.iterdir():
        if child.name == ".git":
            continue
        shutil.rmtree(child) if child.is_dir() else child.unlink()

    n_files = 0
    for src_rel, dst_rel in COPY:
        src, dst = ROOT / src_rel, dest / dst_rel
        if not src.exists():
            print(f"  THIEU {src_rel}")
            return 1
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            n_files += sum(1 for _ in dst.rglob("*") if _.is_file())
        else:
            shutil.copy2(src, dst)
            n_files += 1

    tex = dest / "paper/paper3_aicon/main.tex"
    s, n_cut = clean_tex(io.open(tex, encoding="utf-8").read())
    for tok in (r"\ifanonymous", r"\anonymoustrue", r"\anonymousfalse"):
        if tok in s:
            print(f"  DUNG -- con sot {tok} trong main.tex")
            return 1
    if REPO_URL not in s:
        print("  DUNG -- main.tex khong co link repo moi")
        return 1
    io.open(tex, "w", encoding="utf-8").write(s)

    audit = dest / "runners/audit_paper3.py"
    a = io.open(audit, encoding="utf-8").read()
    i, j = a.find(AUDIT_OLD_START), a.find(AUDIT_OLD_END)
    if i < 0 or j < i:
        print("  DUNG -- khong tim thay khoi kiem mirror trong audit_paper3.py")
        return 1
    a = a[:i] + AUDIT_NEW + a[j + len(AUDIT_OLD_END):]
    io.open(audit, "w", encoding="utf-8").write(a)

    for name, text in (("requirements.txt", REQUIREMENTS), ("README.md", README),
                       ("LICENSE", LICENSE),
                       (".gitignore", "__pycache__/\n*.pyc\n.venv/\n")):
        io.open(dest / name, "w", encoding="utf-8").write(text)
        n_files += 1

    # ---- CONG RIENG TU ---------------------------------------------------
    bad = []
    for p in sorted(dest.rglob("*")):
        if not p.is_file() or ".git" in p.relative_to(dest).parts:
            continue
        try:
            text = io.open(p, encoding="utf-8", errors="strict").read()
        except (UnicodeDecodeError, OSError):
            continue          # nhi phan: .npy, .parquet, .pdf
        for needle in FORBIDDEN:
            if needle.lower() in text.lower():
                bad.append((p.relative_to(dest).as_posix(), needle))

    print(f"  chep {n_files} file, giu nhanh co ten o {n_cut} cho trong main.tex")
    if bad:
        print(f"\n  DUNG -- con {len(bad)} chuoi rieng tu:")
        for rel, needle in bad[:40]:
            print(f"    {rel}: {needle!r}")
        return 1
    print(f"  cong rieng tu: sach ({len(FORBIDDEN)} chuoi, 0 lan khop)")
    print(f"  -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
