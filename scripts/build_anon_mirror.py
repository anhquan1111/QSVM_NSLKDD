"""Dung cay thu muc AN DANH cho ban nop AICON, tu repo nay.

    python scripts/build_anon_mirror.py [thu_muc_dich]

Bai AICON nop qua Confy+ nen PDF phai an danh, va muc Reproducibility tro
toi mot mirror tren anonymous.4open.science. Repo goc KHONG dung thang lam
mirror duoc, vi hai ly do:

  1. Ten that nam rai rac ngoai thu muc paper/ -- README.md, README.vi.md,
     configs/c4_protocol.json, docs/, runners/audit_prose.py.
  2. results/ nang 3,8 GB. Phan bien khong can, va cung khong tai noi.

Script nay chep ra mot cay toi thieu nhung DU DE CHAY LAI: toan bo artifact
bai trich dan chi khoang 3 MB, ke ca Gram luong tu da cache va parquet da
tien xu ly. Nguoi phan bien chay duoc tung lenh trong README.

CONG AN DANH. Sau khi chep, script grep ca cay tim ten that, email va ten
tai khoan GitHub. Con mot chuoi la DUNG, khong xuat. Day la cho duy nhat
dang tin: danh sach chep tay thi som muon cung sot.
"""

from __future__ import annotations

import io
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Chuoi TUYET DOI khong duoc xuat hien trong cay. Them vao khi co tac gia moi.
FORBIDDEN = [
    "Quan Tran Anh", "Tran Anh Quan", "votrananhquan", "anhquan1111",
    "Minh Tuan Pham", "Minh~Tuan~Pham", "Nang Hung Van", "Nang~Hung~Van",
    "Quang Anh Nguyen", "Quang~Anh~Nguyen", "Nguyen Quang Anh",
    "Phuc Hao Do", "Phuc~Hao~Do", "pmtuan", "nguyenvan@dut",
    "dut.udn.vn", "Danang", "Da Nang", "QSVM_NSLKDD",
]

# (nguon, dich). Thu muc thi chep ca cay.
COPY = [
    ("runners/run_paper3_selection.py", "runners/run_paper3_selection.py"),
    ("runners/make_paper3_figures.py", "runners/make_paper3_figures.py"),
    ("runners/make_paper3_tables.py", "runners/make_paper3_tables.py"),
    ("runners/audit_paper3.py", "runners/audit_paper3.py"),
    ("runners/check_latex.py", "runners/check_latex.py"),
    ("results/unsw/c_tuning_results.json", "results/unsw/c_tuning_results.json"),
    ("results/unsw/c1_results.json", "results/unsw/c1_results.json"),
    ("results/unsw/c3_results_statevector.json",
     "results/unsw/c3_results_statevector.json"),
    ("results/unsw/c3_results_statevector_C1.json",
     "results/unsw/c3_results_statevector_C1.json"),
    ("results/unsw/c4_results_C1.json", "results/unsw/c4_results_C1.json"),
    ("results/unsw/c4_revision/c4_per_run_unsw_natural_refit_per_N.csv",
     "results/unsw/c4_revision/c4_per_run_unsw_natural_refit_per_N.csv"),
    ("results/unsw/paper3", "results/unsw/paper3"),
    ("models/unsw/qsvm_cache/multirun", "models/unsw/qsvm_cache/multirun"),
    ("data/unsw/processed_data/multi_run", "data/unsw/processed_data/multi_run"),
    ("paper/paper3_aicon/figs", "paper/paper3_aicon/figs"),
    ("paper/paper3_aicon/tables", "paper/paper3_aicon/tables"),
    ("paper/paper3_aicon/main.tex", "paper/paper3_aicon/main.tex"),
]

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

README = r"""# Artifacts for "When Model Selection Manufactures a Finding"

Anonymous artifact mirror for the submitted short paper. Everything the paper
reports can be recomputed from this tree; nothing here is a summary of a
result computed elsewhere.

## What is here

```
runners/    the four scripts that produce every figure, table and number
results/    the stored measurements the paper cites
models/     cached quantum Gram matrices (5 runs, 100x100, exact statevector)
data/       the preprocessed UNSW-NB15 subsets used by the tuned protocol
paper/      the figures and tables as they appear, plus the LaTeX source
```

Total size is a few megabytes. No quantum hardware and no GPU is required;
the whole pipeline runs on a laptop in well under a minute.

## Reproducing the paper

```bash
pip install -r requirements.txt

python runners/run_paper3_selection.py   # Section 7 measurement (~15 s)
python runners/make_paper3_figures.py    # Figures 1-3
python runners/make_paper3_tables.py     # Tables 1-2 and the number macros
python runners/audit_paper3.py           # 88 checks
```

## The reproduction gate

`run_paper3_selection.py` refuses to emit a new number unless it first
reproduces three already-published ones from the same code path: the
cross-validated F1 at the five original grid points, and the test-set means
at the tuned and at the neutral regularisation constant. It prints the
deviations and exits non-zero if any exceeds 1e-9. On the reference machine
the cross-validated scores agree exactly (deviation 0.0) and the test-set
means agree to 2.2e-16.

Small deviations on a different BLAS or scikit-learn build would not
invalidate the argument, but they should be visible rather than silent,
which is why the gate prints them.

## The audit

`audit_paper3.py` is the check described in Section 8. It asserts three
things:

1. every number in the paper recomputes from the stored artifacts, and no
   literal decimal appears in a sentence;
2. the invariants the argument rests on still hold -- for instance that on
   the original grid the quantum kernel's best non-degenerate score lies
   *below* the degenerate floor while each classical kernel's lies above it;
3. the degeneracy census scans all models and all rows rather than the ones
   the finding was expected in.

It also fails if any audit function in the file is never called, which is a
mistake that happened once in this project and went unnoticed.

## Notes

The LaTeX source in `paper/` is the anonymous build. The author block and
the companion-manuscript reference are withheld for review, as they are in
the submitted PDF.

`results/unsw/c4_revision/` holds one CSV from the companion study's runs.
The paper recomputes a quantity from it that the companion does not report;
Section 6 states this.
"""


def main() -> int:
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        ROOT.parent / "tuning-trap-artifacts")
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

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

    # main.tex mang ten that trong nhanh \else cua cong tac an danh. Ban
    # an danh chi dung nhanh \ifanonymous, nen nhanh kia phai bi CAT khoi
    # cay chu khong chi bi tat.
    tex = dest / "paper/paper3_aicon/main.tex"
    s = io.open(tex, encoding="utf-8").read()

    # Phai bo KHAI BAO co truoc. `\newif\ifanonymous` cung chua chuoi
    # "\ifanonymous", nen neu quet thang thi no bi tinh la mot khoi dieu
    # kien, an mat mot \else that, va de lai mot \ifanonymous khong co \fi
    # -- LaTeX bao "Incomplete \iftrue" va bai khong build duoc.
    s = re.sub(r"\\newif\\ifanonymous\s*\n", "", s)
    s = re.sub(r"\\anonymous(true|false)\s*\n", "", s)

    n_cut = 0
    while True:
        m = re.search(r"\\ifanonymous(.*?)\\else(.*?)\\fi", s, re.S)
        if not m:
            break
        s = s[:m.start()] + m.group(1) + s[m.end():]
        n_cut += 1
    # Ghi chu dau file con nhac toi cong tac vua bi go. Trong ban mirror no
    # khong con dung nua, nen bo di thay vi de lai mot chi dan sai.
    s = re.sub(r"^%.*\\anonymous(true|false).*\n", "", s, flags=re.M)
    s = re.sub(r"^%\s*Submission is ANONYMISED.*\n", "", s, flags=re.M)

    # Con sot mot cai NGOAI comment la bai khong compile duoc. Kiem, dung tin.
    code = re.sub(r"(?<!\\)%.*", "", s)
    for tok in (r"\ifanonymous", r"\anonymoustrue", r"\anonymousfalse"):
        if tok in code:
            print(f"  DUNG -- con sot {tok} trong main.tex (ngoai comment)")
            shutil.rmtree(dest)
            return 1
    io.open(tex, "w", encoding="utf-8").write(s)

    io.open(dest / "requirements.txt", "w", encoding="utf-8").write(REQUIREMENTS)
    io.open(dest / "README.md", "w", encoding="utf-8").write(README)
    io.open(dest / ".gitignore", "w", encoding="utf-8").write(
        "__pycache__/\n*.pyc\n.venv/\n")
    n_files += 3

    # ---- CONG AN DANH ------------------------------------------------
    bad = []
    for p in sorted(dest.rglob("*")):
        if not p.is_file():
            continue
        try:
            text = io.open(p, encoding="utf-8", errors="strict").read()
        except (UnicodeDecodeError, OSError):
            continue          # nhi phan: .npy, .parquet, .pdf, .png
        for needle in FORBIDDEN:
            if needle.lower() in text.lower():
                bad.append((p.relative_to(dest).as_posix(), needle))

    print(f"  chep {n_files} file, cat {n_cut} nhanh \\else khoi main.tex")
    if bad:
        print(f"\n  DUNG -- con {len(bad)} cho lo danh tinh:")
        for rel, needle in bad[:40]:
            print(f"    {rel}: {needle!r}")
        shutil.rmtree(dest)
        return 1
    print(f"  cong an danh: sach ({len(FORBIDDEN)} chuoi, 0 lan khop)")
    print(f"  -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
