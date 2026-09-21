"""Paper 2 dung lai -- thong ke mo ta hai corpus.

    python runners/run_p2_rebuild_corpora.py

Bai bao cao ket qua tren ca NSL-KDD lan UNSW-NB15 ma chua bao gio TA chung:
bao nhieu ban ghi, ti le tan cong, bao nhieu nhom. Nhung con so do phai den
tu mot runner nhu moi con so khac -- lan dau toi sinh chung bang mot script
roi, va `trace_p2_provenance.py` bat duoc ngay vi artifact thanh mo coi.

Doc THANG cot nhan tu file, khong qua `c4_pipeline.load_data`: ham do nap
toan bo 186 dac trung de do trung lap va can ~250 MB cho UNSW.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "nslkdd" / "p2_rebuild"
COLS = ["attack_category", "label_binary"]

SOURCES = {
    "nsl": ("data/nslkdd/processed_data/NSL_KDD_Train_Cleaned.csv",
            "data/nslkdd/processed_data/NSL_KDD_Test_Cleaned.csv"),
    "unsw": ("data/unsw/processed_data/UNSW_Train_Cleaned.parquet",
             "data/unsw/processed_data/UNSW_Test_Cleaned.parquet"),
}


def load(rel: str) -> pd.DataFrame:
    p = ROOT / rel
    if p.suffix == ".parquet":
        return pd.read_parquet(p, columns=COLS)
    return pd.read_csv(p, usecols=COLS)


def main() -> int:
    out = {}
    for key, (tr_p, te_p) in SOURCES.items():
        tr, te = load(tr_p), load(te_p)
        out[key] = dict(
            n_train=int(len(tr)), n_test=int(len(te)),
            attack_rate_train=round(float((tr.label_binary == 1).mean()), 4),
            attack_rate_test=round(float((te.label_binary == 1).mean()), 4),
            n_categories=int(te.attack_category.nunique()),
            test_counts={str(a): int(b)
                         for a, b in te.attack_category.value_counts().items()},
            source_train=tr_p, source_test=te_p,
        )
        d = out[key]
        print(f"  {key:5s} train {d['n_train']:7d} ({d['attack_rate_train']:.1%} "
              f"tan cong)  test {d['n_test']:7d} "
              f"({d['attack_rate_test']:.1%})  {d['n_categories']} nhom")

    p = OUT / "p2_rebuild_corpora.json"
    with io.open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"\n  -> {p.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
