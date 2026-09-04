"""Do do tap trung cua Gram theo be rong mach, va uoc luong so mu suy giam.

Vi sao co script rieng. Ban dau so lieu nay duoc sinh bang mot lenh roi, va lenh
do mac dung loi da gap hai lan truoc: fit MinMaxScaler tren TAP CON thay vi tren
toan bo train. Sai so len toi 0.015 (12% tuong doi o n=8), du de lam sai con so
in trong hinh. Moi thu vao bai phai co script tai lap duoc.

Giao thuc khop dung `RefitPerNRepresentation`: SelectKBest -> PCA -> MinMax[0,pi],
ca ba deu fit tren toan bo train roi moi transform tap con. Tap con lay theo dung
cach cua C1: train_test_split(stratify=attack_category), N=300, seed 42.

Ngoai do tap trung, script uoc luong so mu alpha trong std(n) ~ n^(-alpha). Neu
alpha cua ZZ lon hon han cua Z thi do la bang chung dinh luong khop voi cau truc
mach: ZZFeatureMap co C(n,2) pha cap (tang bac hai theo n) trong khi ZFeatureMap
chi co n pha don (tang tuyen tinh).

Chay:  python runners/run_gram_concentration.py --max-rss-mb 2500
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

K_LIST = [20, 80]
N_GRID = list(range(4, 11))
SUBSET = 300
SEED = 42
REPS = 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-rss-mb", type=int, default=2500)
    args = ap.parse_args()

    import c4_pipeline as c4
    from config import LABEL_COLS
    from sklearn.decomposition import PCA
    from sklearn.feature_selection import SelectKBest, f_classif
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import MinMaxScaler

    spec = c4.get_spec("nslkdd")
    out = ROOT / "results" / "nslkdd" / "c1_revision"
    out.mkdir(parents=True, exist_ok=True)

    with MemoryGuard(args.max_rss_mb) as guard:
        df = c4.read_table(ROOT / spec.processed_dir / spec.train_file)
        fc = [c for c in df.columns if c not in LABEL_COLS]
        X = df[fc].to_numpy(dtype=np.float32)
        y = df["label_binary"].to_numpy()
        sub, _ = train_test_split(np.arange(len(y)), train_size=SUBSET,
                                  stratify=df["attack_category"].to_numpy(),
                                  random_state=SEED)
        sub = np.sort(sub)
        del df
        gc.collect()

        rows = []
        for K in K_LIST:
            sel = SelectKBest(f_classif, k=min(K, X.shape[1])).fit(X, y)
            X_sel = sel.transform(X)
            for n in N_GRID:
                pca = PCA(n_components=n, random_state=SEED).fit(X_sel)
                P_all = pca.transform(X_sel)
                # Scaler fit tren FULL TRAIN roi moi transform tap con -- dung
                # nhu RefitPerNRepresentation. Fit ngay tren tap con la sai.
                scaler = MinMaxScaler((0.0, c4.ANGLE_MAX)).fit(P_all)
                ang = np.clip(scaler.transform(pca.transform(X_sel[sub])),
                              0.0, c4.ANGLE_MAX)
                del P_all
                for kern in ("ZZ", "Z"):
                    g = c4.gram_from_statevectors(
                        c4.compute_statevectors_fast(ang, kern, n, REPS))
                    off = g[~np.eye(len(g), dtype=bool)]
                    rows.append({"K": K, "n": n, "kernel": kern,
                                 "offdiag_mean": float(off.mean()),
                                 "offdiag_std": float(off.std())})
                    del g
                    gc.collect()
            print(f"K={K}: xong {len(N_GRID)} be rong", flush=True)

        d = pd.DataFrame(rows)
        d.to_csv(out / "c1_gram_concentration.csv", index=False)

        # std(n) ~ n^(-alpha): hoi quy tuyen tinh tren thang log-log.
        summary = {}
        for K in K_LIST:
            summary[str(K)] = {}
            for kern in ("ZZ", "Z"):
                g = d[(d.K == K) & (d.kernel == kern)].sort_values("n")
                alpha, _ = np.polyfit(np.log(g.n), np.log(g.offdiag_std), 1)
                loss = 1 - g.offdiag_std.iloc[-1] / g.offdiag_std.iloc[0]
                summary[str(K)][kern] = {
                    "alpha": float(-alpha), "loss_4_to_10": float(loss),
                    "std_by_n": {int(r.n): round(r.offdiag_std, 4)
                                 for r in g.itertuples()}}
            a_zz = summary[str(K)]["ZZ"]["alpha"]
            a_z = summary[str(K)]["Z"]["alpha"]
            summary[str(K)]["alpha_ratio"] = float(a_zz / a_z) if a_z else None
            print(f"  K={K}: alpha_ZZ = {a_zz:.3f} | alpha_Z = {a_z:.3f} "
                  f"| ty le = {a_zz / a_z:.2f}x", flush=True)
        (out / "c1_gram_concentration.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8")
        print(f"\nDa ghi c1_gram_concentration.csv / .json")
        print(f"RSS dinh {guard.peak_mb:.0f} MB / nguong {args.max_rss_mb} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
