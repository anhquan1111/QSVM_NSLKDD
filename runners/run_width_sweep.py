"""Quet be rong mach o K co dinh: F1 co doan duoc tu do tap trung cua Gram khong.

Vi sao can. R3 doi "a theoretical result establishing a new regime of advantage".
Ta khong the chung minh mot dinh ly moi trong pham vi nay, nhung ta co the dua
ra mot **ranh gioi che do do duoc kem co che**: neu F1 cua nhan ZZ doan duoc tu
mot dai luong hinh hoc do truc tiep tren Gram, thi "che do" khong con la nhan
xet dinh tinh ma la mot quan he dinh luong.

Thiet ke. Giu nguyen K=20 (bieu dien cua bai) va giu nguyen N=1000 + tap test
300 mau cua C2, chi thay doi n. Nho vay hang n=4 phai tai tao dung so C2 --
day la phep tu kiem tra cai san trong thi nghiem.

Chay:  python runners/run_width_sweep.py --max-rss-mb 2500
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "runners")]

from run_ksweep import MemoryGuard  # noqa: E402

N_GRID = list(range(4, 11))
SELECT_K = 20
REPS = 2


def kta(gram: np.ndarray, y: np.ndarray) -> float:
    y_pm = np.where(y == 0, -1.0, 1.0)
    yy = np.outer(y_pm, y_pm)
    den = np.linalg.norm(gram, "fro") * np.linalg.norm(yy, "fro")
    return float((gram * yy).sum() / den) if den > 0 else 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-rss-mb", type=int, default=2500)
    ap.add_argument("--C", type=float, default=3.0,
                    help="Regulariser SVC. Mac dinh 3.0 = dung gia tri C2 da chot "
                         "(c2_summary.json: C_ZZ = C_Z = 3.0), de hang n=4 tai tao "
                         "duoc so cua C2.")
    args = ap.parse_args()

    import c4_pipeline as c4
    from sklearn.metrics import f1_score

    root = ROOT
    proto = c4.load_protocol(root)
    out = root / "results" / "nslkdd" / "c1_revision"
    out.mkdir(parents=True, exist_ok=True)

    with MemoryGuard(args.max_rss_mb) as guard:
        data = c4.load_data(root, verbose=False, dataset="nslkdd")
        fc = data.feature_cols
        df_test = data.df_test_300
        y_test = df_test["label_binary"].to_numpy()
        run_ids = proto["sampling"]["run_ids"]

        rows = []
        for n in N_GRID:
            # Bieu dien fit tren TOAN BO train, dung nhu Block A cua C1 va dung
            # nhu artifact dong bang ma C2 su dung. Neu refit tren 1000 dong thi
            # hang n=4 se khong tai tao duoc C2 (do thu: Z lech toi 0.036).
            rep = c4.make_representation("refit_per_N", select_k=SELECT_K,
                                         n_components=n).fit(data.df_train_all, fc)
            a_te, _ = rep.transform(df_test, fc)
            for run_id in run_ids:
                df_tr = data.run_frames[int(run_id)].reset_index(drop=True)
                y_tr = df_tr["label_binary"].to_numpy()
                a_tr, _ = rep.transform(df_tr, fc)
                for kern in ("ZZ", "Z"):
                    psi_tr = c4.compute_statevectors_fast(a_tr, kern, n, REPS)
                    psi_te = c4.compute_statevectors_fast(a_te, kern, n, REPS)
                    g_tr = c4.gram_from_statevectors(psi_tr)
                    g_te = c4.gram_from_statevectors(psi_te, psi_tr)
                    clf = c4.make_quantum_svc(C=args.C).fit(g_tr, y_tr)
                    f1 = f1_score(y_test, clf.predict(g_te), average="macro")
                    off = g_tr[~np.eye(len(g_tr), dtype=bool)]
                    rows.append({
                        "n": n, "run_id": int(run_id), "kernel": kern,
                        "f1_macro": float(f1), "kta": kta(g_tr, y_tr),
                        "offdiag_mean": float(off.mean()),
                        "offdiag_std": float(off.std()),
                    })
                    del psi_tr, psi_te, g_tr, g_te, clf
                    gc.collect()
            block = pd.DataFrame([r for r in rows if r["n"] == n])
            msg = "  ".join(
                f"{k}: F1 {block[block.kernel == k].f1_macro.mean():.4f} "
                f"std_off {block[block.kernel == k].offdiag_std.mean():.4f}"
                for k in ("ZZ", "Z"))
            print(f"n={n:2d}  {msg}   (RSS "
                  f"{__import__('psutil').Process().memory_info().rss / 1e6:.0f} MB)",
                  flush=True)

        df = pd.DataFrame(rows)
        df.to_csv(out / "c1_width_sweep.csv", index=False)

        # Quan he giua do tap trung va F1, tinh tren trung binh theo n.
        summary = {}
        for kern in ("ZZ", "Z"):
            g = df[df.kernel == kern].groupby("n")[["f1_macro", "offdiag_std"]].mean()
            r = float(np.corrcoef(g.offdiag_std, g.f1_macro)[0, 1])
            slope, intercept = np.polyfit(g.offdiag_std, g.f1_macro, 1)
            summary[kern] = {"pearson_r": r, "slope": float(slope),
                             "intercept": float(intercept),
                             "f1_by_n": g.f1_macro.round(4).to_dict(),
                             "std_by_n": g.offdiag_std.round(4).to_dict()}
            print(f"\n{kern}: F1 vs do trai Gram -- Pearson r = {r:+.4f}, "
                  f"do doc {slope:+.3f}")
        (out / "c1_width_sweep.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8")
        print(f"\nDa ghi c1_width_sweep.csv / .json")
        print(f"RSS dinh {guard.peak_mb:.0f} MB / nguong {args.max_rss_mb} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
