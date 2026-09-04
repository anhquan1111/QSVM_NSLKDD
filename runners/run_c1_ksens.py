"""Luat chon so chieu C1 co doi khi thay K khong.

Cau hoi: `K=20` duoc ke thua tu ban da nop bang mot lap luan "elbow" khong dung
(xem `runners/run_ksweep.py`). Neu doi sang K=80 ma `n*` van la 4 thi moi ket
qua downstream giu nguyen cach dien giai; neu `n*` doi thi phai chay lai C4.

Chay:
    python runners/run_c1_ksens.py --max-rss-mb 2000
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from run_ksweep import MemoryGuard  # noqa: E402

K_LIST = [20, 40, 80, 122]
N_GRID = list(range(2, 11))
V_THRESHOLD = 0.85
KTA_EPS = 0.05
KTA_SUBSET = 300
KTA_SEED = 42


def kta(gram: np.ndarray, y: np.ndarray) -> float:
    """Kernel-target alignment, dung dinh nghia cua C1 (khong tam hoa)."""
    yy = np.outer(y, y).astype(float)
    return float((gram * yy).sum() /
                 (np.linalg.norm(gram, "fro") * np.linalg.norm(yy, "fro")))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-rss-mb", type=int, default=2000)
    args = ap.parse_args()

    import c4_pipeline as c4
    from config import LABEL_COLS
    from sklearn.decomposition import PCA
    from sklearn.feature_selection import SelectKBest, f_classif
    from sklearn.preprocessing import MinMaxScaler

    spec = c4.get_spec("nslkdd")
    out = ROOT / "results" / "nslkdd" / "c1_revision"
    out.mkdir(parents=True, exist_ok=True)

    with MemoryGuard(args.max_rss_mb) as guard:
        df = c4.read_table(ROOT / spec.processed_dir / spec.train_file)
        feature_cols = [c for c in df.columns if c not in LABEL_COLS]
        X_all = df[feature_cols].to_numpy(dtype=np.float32)
        y_all = df["label_binary"].to_numpy()

        # Tap con cho KTA: PHAI dung dung giao thuc cua C1 --
        # train_test_split(stratify=attack_category), N=300, seed 42. Neu lay mau
        # kieu khac thi cung mot (K, n) se co hai gia tri KTA khac nhau trong repo,
        # va nguoi doc doi chieu hai artifact se thay mau thuan.
        from sklearn.model_selection import train_test_split
        idx_all = np.arange(len(y_all))
        sub, _ = train_test_split(idx_all, train_size=KTA_SUBSET,
                                  stratify=df["attack_category"].to_numpy(),
                                  random_state=KTA_SEED)
        sub = np.sort(sub)
        y_sub = np.where(y_all[sub] == 1, 1.0, -1.0)
        del df

        # Q(n) cua bai: Q_raw = 10n^2 - 8n, chuan hoa theo n=10 (=920).
        # Da doi chieu voi cot Q_raw trong u1_dimension_metrics.csv.
        def q_raw(n):
            return 10 * n * n - 8 * n

        q = {n: q_raw(n) / q_raw(10) for n in N_GRID}

        rows, summary = [], {}
        for K in K_LIST:
            k = min(K, X_all.shape[1])
            sel = SelectKBest(f_classif, k=k).fit(X_all, y_all)
            X_sel_sub = sel.transform(X_all[sub])
            X_sel_all = sel.transform(X_all)

            for n in N_GRID:
                pca = PCA(n_components=n, random_state=42).fit(X_sel_all)
                v = float(pca.explained_variance_ratio_.sum())
                # Scaler PHAI fit tren FULL TRAIN roi moi transform tap con --
                # dung nhu Block A cua C1_revision.ipynb. Fit ngay tren 300 dong
                # cho ra goc khac han, va KTA se lech toi 0.08.
                scaler = MinMaxScaler((0.0, float(np.pi))).fit(pca.transform(X_sel_all))
                ang = np.clip(scaler.transform(pca.transform(X_sel_sub)),
                              0.0, float(np.pi))
                psi = c4.compute_statevectors_fast(ang, "ZZ", n, 2)
                g = c4.gram_from_statevectors(psi)
                rows.append({"K": K, "n": n, "V": v, "KTA": kta(g, y_sub),
                             "Q": q[n]})
                del psi, g

            block = pd.DataFrame([r for r in rows if r["K"] == K])
            feas1 = block[block.V >= V_THRESHOLD]
            thr = (1 - KTA_EPS) * feas1.KTA.max()
            feas2 = feas1[feas1.KTA >= thr]
            n_star = int(feas2.loc[feas2.Q.idxmin(), "n"])
            summary[K] = {"n_star": n_star,
                          "stage1": feas1.n.tolist(),
                          "kta_max": float(feas1.KTA.max()),
                          "kta_threshold": float(thr),
                          "stage2": feas2.n.tolist()}
            print(f"K={K:4d}  giai doan 1 (V>=0.85): {feas1.n.tolist()}"
                  f"  | KTA_max {feas1.KTA.max():.4f} -> nguong {thr:.4f}"
                  f"  | giai doan 2: {feas2.n.tolist()}  => n* = {n_star}",
                  flush=True)

        df_out = pd.DataFrame(rows)
        df_out.to_csv(out / "c1_ksensitivity.csv", index=False)
        (out / "c1_ksensitivity.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8")
        print(f"\nDa ghi c1_ksensitivity.csv / .json")
        print(f"RSS dinh {guard.peak_mb:.0f} MB / nguong {args.max_rss_mb} MB")

        stars = {K: s["n_star"] for K, s in summary.items()}
        print(f"\n>>> n* theo K: {stars}")
        if len(set(stars.values())) == 1:
            print(">>> n* KHONG doi theo K -- ket qua downstream giu nguyen cach dien giai.")
        else:
            print(">>> n* CO doi theo K -- phai chay lai C4 o K khac de kiem robustness.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
