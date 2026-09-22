"""Dung goi artifact cho Paper 2 de nop len Zenodo.

    python scripts/build_zenodo_paper2.py [thu_muc_dich]

Muc Data Availability cua Paper 2 phai tro toi mot cho cu the. Tro vao repo
GitHub thi co hai van de: repo sua duoc bat cu luc nao (nen khong dam bao
nguoi doc thay dung phien ban bai mo ta), va lich su repo tung chua file ca
nhan. Zenodo giai quyet ca hai: moi phien ban dong bang vinh vien va co DOI.

Goi nay TU CHAY LAI DUOC. Nguoi doc tai ve, cai requirements, chay
`audit_p2_rebuild.py`, va 289 phep kiem se tinh lai TUNG CON SO trong bai tu
artifact. Do moi la thu dang gia -- khong phai mot thu muc code doc suong.

CONG AN TOAN. Paper 2 khong an danh nen ten tac gia la binh thuong. Cai
KHONG duoc phep co: hop dong de tai (CCCD, so tai khoan), anh chan dung tac
gia, va moi thu trong docs/. Script grep ca cay va tu xoa neu con mot cho.
"""

from __future__ import annotations

import io
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Chuoi TUYET DOI khong duoc xuat hien. Day la du lieu ca nhan, khong phai
# ten tac giai -- ten tac gia thi phai co, vi bai nay khong an danh.
# Chi nhung chuoi KHONG THE trung voi van ban tieng Anh. Ban dau danh sach
# co "so the" (dinh chan "so the" = so the ngan hang) va no bao do ngay
# main.tex, vi tieng Anh co cum "...so the comparison is made...". Mot cong
# an toan hay bao nham se bi nguoi ta tat di, nen no phai chinh xac.
FORBIDDEN = ["DeTai10", "hop dong", "CCCD", "so tai khoan",
             "PAPER1_final_report", "can cuoc cong dan", "the ngan hang"]

# File duoi day khong duoc chep, du co lot vao thu muc nao.
FORBIDDEN_NAMES = re.compile(
    r"(DeTai10|hopdong|PAPER1_final_report|\.jpg$|\.jpeg$|\.png$)", re.I)

COPY = [
    # Sinh so lieu -- de nguoi doc chay lai tu dau neu muon
    ("runners/run_p2_rebuild.py", "runners/run_p2_rebuild.py"),
    ("runners/run_p2_rebuild_unsw.py", "runners/run_p2_rebuild_unsw.py"),
    ("runners/analyze_p2_rebuild.py", "runners/analyze_p2_rebuild.py"),
    # Sinh hinh, bang, va BO KIEM
    ("runners/make_p2_rebuild_figures.py", "runners/make_p2_rebuild_figures.py"),
    ("runners/make_p2_rebuild_tables.py", "runners/make_p2_rebuild_tables.py"),
    ("runners/audit_p2_rebuild.py", "runners/audit_p2_rebuild.py"),
    ("runners/check_latex.py", "runners/check_latex.py"),
    ("src", "src"),
    # Artifact bai trich dan
    ("results/nslkdd/p2_rebuild", "results/nslkdd/p2_rebuild"),
    ("results/unsw/p2_rebuild", "results/unsw/p2_rebuild"),
    ("results/nslkdd/p2_verify_calibration.json",
     "results/nslkdd/p2_verify_calibration.json"),
    ("data/nslkdd/processed_data/multi_run/train_run1.csv",
     "data/nslkdd/processed_data/multi_run/train_run1.csv"),
    # Ban thao + hinh + bang: bo kiem doc main.tex de doi chieu tung con so
    # trong cau van voi artifact, nen thieu no thi audit khong chay duoc.
    ("paper/paper2_rebuild/main.tex", "paper/paper2_rebuild/main.tex"),
    ("paper/paper2_rebuild/preamble.tex", "paper/paper2_rebuild/preamble.tex"),
    ("paper/paper2_rebuild/tables", "paper/paper2_rebuild/tables"),
    ("paper/paper2_rebuild/figs", "paper/paper2_rebuild/figs"),
]

REQUIREMENTS = """\
numpy==2.4.3
pandas==2.3.3
scikit-learn==1.8.0
scipy==1.17.1
matplotlib==3.10.8
xgboost
"""

README = r"""# Artifacts for "Are Quantum-Kernel Intrusion Detectors Trustworthy?"

Reproduction package for the paper *Are Quantum-Kernel Intrusion Detectors
Trustworthy? A Reliability and Calibration Benchmark of QSVM Against Strong
Tabular Learners on NSL-KDD and UNSW-NB15*.

Every number that appears in the manuscript is computed from the artifacts in
this package. Nothing in the paper is typed by hand: numbers reach the text
only through generated macros, and the audit script below recomputes each one
and fails if any disagrees.

## What is here

```
runners/    the scripts that generate, analyse, plot and audit
src/        the reliability helpers (ECE, Brier, Platt, isotonic, effect size)
results/    the stored per-run measurements the paper cites
data/       the preprocessed training subset used by the low-data sweep
paper/      the manuscript source, the generated tables, and the figures
```

## Checking the paper

```bash
pip install -r requirements.txt
python runners/audit_p2_rebuild.py
```

This runs 289 checks in three layers:

1. **Every macro recomputes from the artifacts.** Each number cited in the
   prose is regenerated from the stored per-run records and compared to the
   value the manuscript prints.
2. **No number is hand-typed.** A scan rejects any literal decimal that
   appears in a sentence without passing through a generated macro.
3. **The claims still follow.** The invariants the argument rests on are
   asserted directly — for example that the degeneracy identity of
   Section III holds to machine precision on every model and run, that ten
   paired runs are the minimum at which the Wilcoxon test can reach the
   reported significance, and that the sign convention of every recalibration
   number matches the direction the text claims.

The audit also fails if any audit function in the file is never called, a
mistake that occurred once in this project and went unnoticed until a later
review.

## Regenerating the figures and tables

```bash
python runners/make_p2_rebuild_tables.py    # tables + the number macros
python runners/make_p2_rebuild_figures.py   # the six figures
```

Both write into `paper/paper2_rebuild/`. Re-running the audit afterwards
should still pass.

## Regenerating the measurements from scratch

```bash
python runners/run_p2_rebuild.py        # NSL-KDD, 10 paired runs
python runners/run_p2_rebuild_unsw.py   # UNSW-NB15, both circuit widths
python runners/analyze_p2_rebuild.py    # paired tests, Holm correction
```

This retrains every model from scratch and takes considerably longer than the
audit. The quantum kernel is evaluated by exact statevector simulation; no
quantum hardware is required.

## Corpora

The two corpora are public benchmarks and are not redistributed here:
NSL-KDD and UNSW-NB15. The preprocessing pipeline is in the runners, and the
one preprocessed file the low-data sweep needs is included.

## Note on the released measurements

The stored records are the ones the manuscript reports. Where the paper
withdraws a claim made in an earlier version of this work, the earlier
measurement is kept in `results/nslkdd/p2_verify_calibration.json` so that the
comparison in the manuscript can be checked rather than taken on trust.
"""


def main() -> int:
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        ROOT.parent / "paper2-artifacts")
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    n = 0
    for src_rel, dst_rel in COPY:
        src, dst = ROOT / src_rel, dest / dst_rel
        if not src.exists():
            print(f"  THIEU {src_rel}")
            return 1
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(
                src, dst,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc",
                                              "*.jpg", "*.jpeg"))
            n += sum(1 for _ in dst.rglob("*") if _.is_file())
        else:
            shutil.copy2(src, dst)
            n += 1

    io.open(dest / "requirements.txt", "w", encoding="utf-8").write(REQUIREMENTS)
    io.open(dest / "README.md", "w", encoding="utf-8").write(README)
    n += 2

    # ---- CONG AN TOAN ------------------------------------------------
    bad = []
    for p in sorted(dest.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(dest).as_posix()
        if FORBIDDEN_NAMES.search(p.name) and p.suffix.lower() != ".png":
            bad.append((rel, f"ten file: {p.name}"))
        try:
            text = io.open(p, encoding="utf-8", errors="strict").read()
        except (UnicodeDecodeError, OSError):
            continue
        for needle in FORBIDDEN:
            if needle.lower() in text.lower():
                bad.append((rel, needle))

    # Anh chan dung tac gia: khong duoc co file anh nao ngoai hinh cua bai.
    imgs = [p.relative_to(dest).as_posix() for p in dest.rglob("*")
            if p.suffix.lower() in (".jpg", ".jpeg")]
    bad += [(i, "anh chan dung") for i in imgs]

    size = sum(f.stat().st_size for f in dest.rglob("*") if f.is_file())
    print(f"  chep {n} file, {size/1e6:.1f} MB")
    if bad:
        print(f"\n  DUNG -- {len(bad)} cho vi pham:")
        for rel, why in bad[:30]:
            print(f"    {rel}: {why}")
        shutil.rmtree(dest)
        return 1
    print(f"  cong an toan: sach ({len(FORBIDDEN)} chuoi + anh chan dung, "
          f"0 lan khop)")
    print(f"  -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
