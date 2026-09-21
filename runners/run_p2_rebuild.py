"""Paper 2 dung lai tu dau: tap test day du, 10 run, khong dung cache.

    python runners/run_p2_rebuild.py

Ba thay doi so voi ban da nop, va ly do:

1. TAP TEST. Ban cu do ECE_rare tren `NSL_KDD_Test_Sample100.csv` -- 100 mau,
   trong do dung **10** mau hiem, chia 5 bin, tuc 2 mau moi bin. KDDTest+ day
   du co 2 952 mau hiem. Ly do ngay xua phai cat nho la chi phi kernel luong
   tu; voi loi tat closed-form thi Gram 22 544 x 1 000 mat 0,15 giay.

2. SO RUN. Ban cu dung 5 run. Voi 5 cap, Wilcoxon hai phia co p nho nhat la
   0,0625 -- KHONG BAO GIO dat duoc p < 0,05, du hieu ung lon den may. Repo co
   san 10 file train_run*.csv.

3. KHONG DUNG CACHE. Model trong `qsvm_cache/multirun_c5/` duoc huan luyen
   tren mot tap 1 000 mau KHAC voi `train_run{i}.csv` hien tai (998/1000 dong
   khac nhau, lech toi 2,95 tren thang [0, pi]). Ban cu nap model do roi fit
   Platt bang `X_train` moi doc tu file -- tuc calibrator cua QSVM duoc fit
   tren diem so cua mot tap no chua tung thay, trong khi calibrator cua cay
   duoc fit dung tren tap chung duoc huan luyen. Bai khang dinh moi baseline
   duoc do "on an identical footing"; dieu do khong dung. O day MOI model deu
   duoc huan luyen lai tren cung mot tap.

Sieu tham so giu nguyen nhu bai da khai: QSVM C=1.0, SVM-RBF C=10,
RandomForest 300 cay, XGBoost 300 cay sau 4, learning rate 0,1.
"""

from __future__ import annotations

import io
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.svm import SVC

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import c4_pipeline as c4  # noqa: E402
from src.reliability import (RANDOM_STATE, RARE_GROUPS,  # noqa: E402
                             load_pipeline_artifacts, make_ml_dl_models,
                             reliability_metrics, transform_pipeline)

DATA = ROOT / "data" / "nslkdd" / "processed_data"
MODELS = ROOT / "models" / "nslkdd"
OUT = ROOT / "results" / "nslkdd" / "p2_rebuild"
OUT.mkdir(parents=True, exist_ok=True)

RUN_IDS = list(range(1, 11))
C_QSVM = 1.0
C_RBF = 10.0
N_QUBITS = 4
ZZ_REPS = 2
CHUNK = 8000   # so dong test moi khoi khi tinh Gram

TEST_SETS = {
    "full_kddtest_plus": "NSL_KDD_Test_Cleaned.csv",
    # KDDTest-21: tap con kho cua KDDTest+, giu lai cac ban ghi ma cac bo phan
    # loai co dien deu sai. Day la phep do troi theo thoi gian (A2) cua ban cu.
    "kddtest21": "NSL_KDD_Test21_Cleaned.csv",
    "sample100_cu": "NSL_KDD_Test_Sample100.csv",  # giu de doi chieu voi ban cu
}


class ClosedFormQSVM:
    """SVC kernel='precomputed' nhung nhan dac trung goc, nhu moi model khac.

    Gram tinh bang |<psi_i|psi_j>|^2 tu statevector dang dong -- doi chieu voi
    kernel Qiskit trong cache thi lech 5,7e-15 tren ma tran 1000x1000.
    Nho vay `reliability_metrics` dung duoc ma khong phai sua gi.
    """

    def __init__(self, C: float = C_QSVM, kernel: str = "ZZ"):
        self.C = C
        self.kernel_name = kernel
        self.svc = SVC(kernel="precomputed", C=C, random_state=RANDOM_STATE)

    def _psi(self, X):
        return c4.compute_statevectors_fast(X, self.kernel_name, N_QUBITS, reps=ZZ_REPS)

    def fit(self, X, y):
        self.psi_train_ = self._psi(X)
        self.svc.fit(c4.gram_from_statevectors(self.psi_train_), y)
        return self

    def _chunked(self, X, fn):
        """Ap `fn` theo tung khoi test.

        Gram day du 22 544 x 1 000 la 172 MB; giu ba tap test cung luc thi
        may het bo nho that. Chia khoi giu no duoi ~60 MB va khong doi ket
        qua mot chu so nao.
        """
        psi = self._psi(X)
        out = [fn(c4.gram_from_statevectors(psi[i:i + CHUNK], self.psi_train_))
               for i in range(0, len(psi), CHUNK)]
        return np.concatenate(out)

    def predict(self, X):
        return self._chunked(X, self.svc.predict)

    def decision_function(self, X):
        return self._chunked(X, self.svc.decision_function)


def build_models(X_train, y_train):
    """Huan luyen lai TAT CA tren cung mot tap -- day la diem mau chot."""
    models = {
        "QSVM": ClosedFormQSVM(C_QSVM, "ZZ").fit(X_train, y_train),
        "SVM-RBF": SVC(kernel="rbf", C=C_RBF, random_state=RANDOM_STATE).fit(
            X_train, y_train),
    }
    for name, mdl in make_ml_dl_models(RANDOM_STATE).items():
        models[name] = mdl.fit(X_train, y_train)
    return models


def main() -> int:
    sel, pca, scaler, feat_cols = load_pipeline_artifacts(MODELS, DATA)

    tests = {}
    for key, fname in TEST_SETS.items():
        df = pd.read_csv(DATA / fname)
        tests[key] = dict(
            X=transform_pipeline(df, feat_cols, sel, pca, scaler),
            y=df["label_binary"].to_numpy(np.int64),
            rare=np.isin(df["attack_category"].to_numpy(), RARE_GROUPS),
        )
        print(f"  test {key:20s} {len(df):6d} mau, "
              f"{int(tests[key]['rare'].sum()):5d} hiem")

    rows = []
    for rid in RUN_IDS:
        t0 = time.time()
        tr = pd.read_csv(DATA / "multi_run" / f"train_run{rid}.csv")
        X_train = transform_pipeline(tr, feat_cols, sel, pca, scaler)
        y_train = tr["label_binary"].to_numpy(np.int64)
        models = build_models(X_train, y_train)

        for tkey, t in tests.items():
            for name, mdl in models.items():
                m = reliability_metrics(mdl, X_train, y_train,
                                        t["X"], t["y"], t["rare"])
                m.update(run_id=rid, model=name, test_set=tkey,
                         n_test=len(t["y"]), n_rare=int(t["rare"].sum()))
                rows.append(m)
        print(f"  run{rid:2d}  {time.time() - t0:5.1f}s", flush=True)

    df = pd.DataFrame(rows)
    csv = OUT / "p2_rebuild_per_run.csv"
    df.to_csv(csv, index=False, encoding="utf-8")

    meta = {
        "n_runs": len(RUN_IDS),
        "test_sets": {k: dict(n_test=int(v["y"].shape[0]),
                              n_rare=int(v["rare"].sum()))
                      for k, v in tests.items()},
        "hyperparameters": {"QSVM_C": C_QSVM, "SVM_RBF_C": C_RBF,
                            "n_qubits": N_QUBITS, "zz_reps": ZZ_REPS},
        "models_retrained_from_scratch": True,
        "cache_used": False,
        "rare_groups": RARE_GROUPS,
    }
    with io.open(OUT / "p2_rebuild_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)

    print(f"\n  -> {csv.relative_to(ROOT).as_posix()}  ({len(df)} dong)")
    for tkey in TEST_SETS:
        sub = df[df.test_set == tkey]
        print(f"\n=== {tkey} ({sub.n_rare.iloc[0]} mau hiem) ===")
        agg = sub.groupby("model")[["ece_rare", "brier_rare", "auc_pr", "f1"]].mean()
        print(agg.sort_values("ece_rare").round(4).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
