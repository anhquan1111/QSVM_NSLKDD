"""Quet K cho tang SelectKBest -- sinh lai du lieu cho Hinh 4.

Vi sao phai chay lai. Ban revision nhan thang `K=20` lam dau vao va khong quet
lai K, nen con so duy nhat dang co (`K=4: 0.8596 ... K=20: 0.8989`) la cua code
CU. Dua hinh do vao ban revision la tron du lieu hai the he.

Ba khac biet so voi ban cu, deu ghi ro de khong ai tuong la cung mot thi nghiem:

1. **Khong ro ri.** `SelectKBest` duoc fit BEN TRONG tung fold cua CV. Neu fit
   trên toàn bo du lieu roi moi chia fold thi diem CV bi thoi phong -- day la
   loi kinh dien cua khau chon dac trung.
2. **Proxy la `LinearSVC` (liblinear)** chu khong phai `SVC(kernel="linear")`.
   Tren 125.973 hang thi libsvm la O(n^2), khong chay noi; liblinear la O(n).
   Ca hai deu la SVM tuyen tinh nen van dung vai tro "proxy" ma bai mo ta.
3. **Co chot chan bo nho.** Tien trinh tu ket thuc neu RSS vuot `--max-rss-mb`,
   de khong bao gio lam dung may.

Chay:
    python runners/run_ksweep.py --max-rss-mb 2000
"""

from __future__ import annotations

import argparse
import gc
import os
import sys
import threading
import time
from pathlib import Path

# Phai dat TRUOC khi numpy/sklearn duoc nap, neu khong BLAS da chiem thread roi.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import psutil  # noqa: E402
from sklearn.feature_selection import SelectKBest, f_classif  # noqa: E402
from sklearn.metrics import f1_score  # noqa: E402
from sklearn.model_selection import StratifiedKFold  # noqa: E402
from sklearn.decomposition import PCA  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import MinMaxScaler  # noqa: E402
from sklearn.svm import LinearSVC  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

K_GRID = [4, 6, 8, 10, 12, 15, 20, 25, 30, 40, 60, 80, 122]


class MemoryGuard:
    """Theo doi RSS trong mot thread rieng; vuot nguong thi ket thuc tien trinh.

    Bat mem bang `MemoryError` khong du: numpy co the giet ca tien trinh truoc
    khi Python kip nem loi. Nen phai canh chu dong va thoat co trat tu.
    """

    def __init__(self, limit_mb: int, interval: float = 0.5):
        self.limit = limit_mb * 1024 * 1024
        self.interval = interval
        self.peak = 0
        self._proc = psutil.Process()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._watch, daemon=True)

    def _watch(self) -> None:
        while not self._stop.wait(self.interval):
            try:
                rss = self._proc.memory_info().rss
            except psutil.Error:
                return
            self.peak = max(self.peak, rss)
            if rss > self.limit:
                print(f"\n!! DUNG: RSS {rss / 1e6:.0f} MB vuot nguong "
                      f"{self.limit / 1e6:.0f} MB. Thoat de khong lam dung may.",
                      flush=True)
                os._exit(2)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        return False

    @property
    def peak_mb(self) -> float:
        return self.peak / 1e6


def load_matrix(max_rows: int | None):
    """Nap tap train, chi giu cot dac trung, ep ve float32 de halve bo nho."""
    from c4_pipeline import get_spec, read_table
    from config import LABEL_COLS

    spec = get_spec("nslkdd")
    df = read_table(ROOT / spec.processed_dir / spec.train_file)
    feature_cols = [c for c in df.columns if c not in LABEL_COLS]
    y = df["label_binary"].to_numpy()
    X = df[feature_cols].to_numpy(dtype=np.float32)
    del df
    gc.collect()

    if max_rows is not None and len(X) > max_rows:
        rng = np.random.default_rng(42)
        idx = np.sort(rng.choice(len(X), size=max_rows, replace=False))
        X, y = X[idx], y[idx]
    return X, y, feature_cols


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-rss-mb", type=int, default=2000,
                    help="Nguong RSS; vuot thi tien trinh tu thoat.")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--max-rows", type=int, default=None,
                    help="Lay mau bot neu can; mac dinh dung toan bo tap train.")
    ap.add_argument("--max-iter", type=int, default=5000)
    ap.add_argument("--pca-components", type=int, default=4,
                    help="So chieu PCA cua pipeline that (n qubit).")
    args = ap.parse_args()

    out = ROOT / "results" / "nslkdd" / "c1_revision"
    out.mkdir(parents=True, exist_ok=True)

    with MemoryGuard(args.max_rss_mb) as guard:
        t0 = time.time()
        X, y, feature_cols = load_matrix(args.max_rows)
        print(f"Du lieu: {X.shape[0]:,} hang x {X.shape[1]} dac trung "
              f"(float32, {X.nbytes / 1e6:.0f} MB)")
        print(f"Nguong RSS: {args.max_rss_mb} MB | RSS sau khi nap: "
              f"{psutil.Process().memory_info().rss / 1e6:.0f} MB")
        print(f"CV: {args.folds}-fold phan tang, SelectKBest fit TRONG tung fold\n")

        cv = StratifiedKFold(n_splits=args.folds, shuffle=True, random_state=42)

        def build(k, with_pca):
            """SelectKBest -> [PCA(n)] -> MinMax -> LinearSVC, fit trong tung fold."""
            steps = [("select", SelectKBest(f_classif, k=k))]
            if with_pca:
                # Dung dung khau nen cua pipeline that: PCA ve n=4 chieu.
                steps += [("prescale", MinMaxScaler()),
                          ("pca", PCA(n_components=args.pca_components,
                                      random_state=42))]
            steps += [("scale", MinMaxScaler()),
                      ("clf", LinearSVC(C=1.0, dual="auto", max_iter=args.max_iter,
                                        random_state=42))]
            return Pipeline(steps)

        rows = []
        for k in K_GRID:
            if k > X.shape[1]:
                continue
            rec = {"K": k}
            for tag, with_pca in (("raw", False), ("pca4", True)):
                if with_pca and k < args.pca_components:
                    continue
                scores, t_k = [], time.time()
                for tr, te in cv.split(X, y):
                    pipe = build(k, with_pca)
                    pipe.fit(X[tr], y[tr])
                    scores.append(f1_score(y[te], pipe.predict(X[te]),
                                           average="macro"))
                    del pipe
                    gc.collect()
                arr = np.asarray(scores)
                rec[f"f1_{tag}_mean"] = arr.mean()
                rec[f"f1_{tag}_std"] = arr.std(ddof=1)
                rec[f"seconds_{tag}"] = time.time() - t_k
            rows.append(rec | {"n_folds": args.folds})
            print(f"  K={k:4d}  raw = {rec.get('f1_raw_mean', float('nan')):.4f}"
                  f"   PCA-{args.pca_components} = "
                  f"{rec.get('f1_pca4_mean', float('nan')):.4f}"
                  f"   (RSS {psutil.Process().memory_info().rss / 1e6:.0f} MB)",
                  flush=True)

        df = pd.DataFrame(rows)
        path = out / "c1_ksweep.csv"
        df.to_csv(path, index=False)
        print(f"\nDa ghi {path.relative_to(ROOT)}")
        print(f"Tong {time.time() - t0:.0f}s | RSS dinh {guard.peak_mb:.0f} MB "
              f"/ nguong {args.max_rss_mb} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
