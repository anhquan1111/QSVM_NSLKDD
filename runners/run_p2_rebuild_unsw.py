"""Paper 2 dung lai -- calibration tren UNSW-NB15.

    python runners/run_p2_rebuild_unsw.py

Dong cai gioi han ban da nop tu khai: *"Results are on NSL-KDD ... the
reliability picture should likewise be confirmed cross-dataset."*

Hai quyet dinh thiet ke, ca hai deu de tranh lap lai loi da tim ra o NSL-KDD:

1. TAP TEST DAY DU. Statevector da cache cho UNSW chi co split `fixed_300`.
   Do lai tren 300 mau la lap lai dung cai loi 10-mau ma ban dung lai nay ra
   doi de sua. Tap test UNSW day du co 82 332 dong, trong do 1 682 thuoc bon
   lop hiem. Statevector sinh lai tu dau, vi voi dang dong thi no re.

2. CA 4 LAN 6 QUBIT. Luat C1 tra ve n*=6 cho UNSW va n*=4 cho NSL-KDD, nen
   so thang hai dataset la doi CA dataset LAN so qubit cung luc -- mot
   confound. Chay ca hai be rong thi tach duoc hai anh huong do.

Gram day du la 82 332 x 1 000 float64 = 659 MB nen tap test duoc chia khoi.
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
from sklearn.metrics import average_precision_score, brier_score_loss, f1_score
from sklearn.svm import SVC

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import c4_pipeline as c4  # noqa: E402
from src.reliability import (N_BINS_FULL, N_BINS_RARE, RANDOM_STATE,  # noqa: E402
                             PlattScaler, compute_ece_mce, get_decision_scores,
                             compute_ece_mce as _ece, make_ml_dl_models)

OUT = ROOT / "results" / "unsw" / "p2_rebuild"
OUT.mkdir(parents=True, exist_ok=True)

RUN_IDS = list(range(1, 11))
N_TRAIN = 1000          # khop voi NSL-KDD de so sanh duoc
WIDTHS = {4: "4 qubit (nhu NSL-KDD)", 6: "6 qubit (luat C1 tra ve cho UNSW)"}
C_QSVM, C_RBF = 1.0, 10.0
CHUNK = 8000            # so dong test moi khoi, giu Gram duoi ~65 MB


def gram_chunked(psi_test, psi_train, fn):
    """Ap `fn` theo tung khoi de khong dung 659 MB Gram mot luc."""
    out = []
    for i in range(0, len(psi_test), CHUNK):
        g = c4.gram_from_statevectors(psi_test[i:i + CHUNK], psi_train)
        out.append(fn(g))
    return np.concatenate(out)


class QSVM:
    def __init__(self, n_qubits: int, C: float = C_QSVM):
        self.n_qubits = n_qubits
        self.svc = SVC(kernel="precomputed", C=C, random_state=RANDOM_STATE)

    def _psi(self, X):
        return c4.compute_statevectors_fast(X, "ZZ", self.n_qubits, reps=2)

    def fit(self, X, y):
        self.psi_train_ = self._psi(X)
        self.svc.fit(c4.gram_from_statevectors(self.psi_train_), y)
        return self

    def decision_function(self, X):
        return gram_chunked(self._psi(X), self.psi_train_, self.svc.decision_function)

    def predict(self, X):
        return gram_chunked(self._psi(X), self.psi_train_, self.svc.predict)


def evaluate(model, Xtr, ytr, Xte, yte, rare):
    s_tr = get_decision_scores(model, Xtr)
    s_te = get_decision_scores(model, Xte)
    scl, _, _ = PlattScaler().fit(s_tr, ytr)
    prob = scl.predict_proba(s_te)
    ece_f, _ = compute_ece_mce(yte, prob, N_BINS_FULL)
    ece_r, _ = compute_ece_mce(yte[rare], prob[rare], N_BINS_RARE)
    return dict(ece_full=ece_f, ece_rare=ece_r,
                brier_full=float(brier_score_loss(yte, prob)),
                brier_rare=float(brier_score_loss(yte[rare], prob[rare])),
                auc_pr=float(average_precision_score(yte, prob)),
                f1=float(f1_score(yte, model.predict(Xte))))


def main() -> int:
    data = c4.load_data(dataset="unsw", verbose=False)
    spec = data.spec
    fc = data.feature_cols
    test_df = data.df_test_full
    yte = test_df["label_binary"].to_numpy(np.int64)
    rare = np.isin(test_df["attack_cat"].to_numpy() if "attack_cat" in test_df
                   else test_df["attack_category"].to_numpy(),
                   list(spec.rare_categories))
    print(f"  UNSW test: {len(yte)} dong, {int(rare.sum())} hiem "
          f"({rare.mean():.2%}), lop hiem = {spec.rare_categories}")

    seeds = json.load(io.open(ROOT / "configs/c4_protocol.json",
                              encoding="utf-8"))["sampling"]["run_seeds"]

    rows = []
    for rid in RUN_IDS:
        t0 = time.time()
        chain = c4.build_nested_chain(data, rid, [N_TRAIN], seeds[rid - 1], "natural")
        df_tr = chain[N_TRAIN]
        ytr = df_tr["label_binary"].to_numpy(np.int64)

        for nq in WIDTHS:
            rep = c4.make_representation("refit_per_N", select_k=spec.select_k,
                                         n_components=nq).fit(df_tr, fc)
            ang_tr, pca_tr = rep.transform(df_tr, fc)
            ang_te, pca_te = rep.transform(test_df, fc)

            models = {"QSVM": (QSVM(nq).fit(ang_tr, ytr), ang_tr, ang_te),
                      "SVM-RBF": (SVC(kernel="rbf", C=C_RBF,
                                      random_state=RANDOM_STATE).fit(pca_tr, ytr),
                                  pca_tr, pca_te)}
            for name, mdl in make_ml_dl_models(RANDOM_STATE).items():
                models[name] = (mdl.fit(pca_tr, ytr), pca_tr, pca_te)

            for name, (mdl, Xa, Xb) in models.items():
                m = evaluate(mdl, Xa, ytr, Xb, yte, rare)
                m.update(run_id=rid, model=name, n_qubits=nq, n_train=N_TRAIN,
                         n_test=len(yte), n_rare=int(rare.sum()))
                rows.append(m)
        print(f"  run{rid:2d}  {time.time() - t0:5.1f}s", flush=True)
        pd.DataFrame(rows).to_csv(OUT / "p2_unsw_per_run.csv",
                                  index=False, encoding="utf-8")

    df = pd.DataFrame(rows)
    with io.open(OUT / "p2_unsw_meta.json", "w", encoding="utf-8") as f:
        json.dump({"n_runs": len(RUN_IDS), "n_train": N_TRAIN,
                   "n_test": int(len(yte)), "n_rare": int(rare.sum()),
                   "rare_categories": list(spec.rare_categories),
                   "widths": list(WIDTHS), "select_k": spec.select_k,
                   "cache_used": False}, f, indent=1)

    for nq in WIDTHS:
        print(f"\n=== UNSW, {WIDTHS[nq]} ===")
        s = df[df.n_qubits == nq].groupby("model")[
            ["ece_rare", "brier_rare", "auc_pr", "f1"]].mean()
        print(s.sort_values("ece_rare").round(4).to_string())
    print(f"\n  -> {(OUT / 'p2_unsw_per_run.csv').relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
