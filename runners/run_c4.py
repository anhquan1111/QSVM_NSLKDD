"""Runner cho C4 (revision) — sample-complexity sweep trên NSL-KDD.

Chạy:
    uv run python runners/run_c4.py --regime matched
    uv run python runners/run_c4.py --regime natural
    uv run python runners/run_c4.py --regime matched --runs 1 --n-grid 100 200   # smoke test

Giao thức: `configs/c4_protocol.json`. Xem `docs/revision/01_PLAN_C4_UNSW.md` để biết
mỗi quyết định trả lời objection nào của reviewer.

Mỗi (regime, repr_mode, arm, N, run) được cache thành một JSON; chạy lại sẽ bỏ qua phần
đã có trừ khi truyền --force.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import c4_pipeline as c4  # noqa: E402

ARMS = ("tuned_per_N", "frozen_c2", "tuned_once")
TEST_SETS = ("fixed_300", "full_kddtest_plus")


# ---------------------------------------------------------------------------


def load_frozen_hyperparameters(root: Path) -> dict:
    """Hyperparameter dong bang cua C2 (chi dung cho NSL-KDD, arm `frozen_c2`)."""
    path = root / "results" / "nslkdd" / "c2_revision" / "c2_downstream_tuned_parameters.json"
    with open(path, encoding="utf-8") as fp:
        return {k: v["chosen_params"] for k, v in json.load(fp)["models"].items()}


def tune_once_on_tuning_set(data, spec, protocol, cache_dir, sv_cache, force=False) -> dict:
    """Arm `tuned_once` - tuong ung giao thuc cua C2 cho dataset khong co san
    hyperparameter dong bang: tune mot lan tren tuning set rieng roi ap cho moi N.

    Day la doi chung de tra loi "ket qua co phai artifact cua viec tune lai o moi N khong?".
    """
    cache_path = cache_dir / f"tuned_once_{spec.name.replace('-', '_')}.json"
    if cache_path.exists() and not force:
        with open(cache_path, encoding="utf-8") as fp:
            return json.load(fp)
    rep_ = c4.make_representation("refit_per_N", select_k=spec.select_k,
                                  n_components=spec.n_qubits)
    rep_.fit(data.df_tune, data.feature_cols)
    X_ang, X_pca = rep_.transform(data.df_tune, data.feature_cols)
    y = data.df_tune["label_binary"].to_numpy(np.int64)
    psi = {k: sv_cache.get(X_ang, k, f"{spec.name}_tuneset") for k in ("ZZ", "Z")}
    hp_cfg = protocol["hyperparameter_protocol"]["primary_arm"]
    hp = tune_all_models(
        c4.gram_from_statevectors(psi["ZZ"]), c4.gram_from_statevectors(psi["Z"]),
        X_pca, y, hp_cfg["grids"]["C_svm_and_qsvm"], hp_cfg["grids"]["rf"],
        hp_cfg["grids"]["xgb"], hp_cfg["cv_folds"], 42, 200)
    hp = {k: v for k, v in hp.items() if not k.startswith("_")}
    with open(cache_path, "w", encoding="utf-8") as fp:
        json.dump(hp, fp, indent=1, ensure_ascii=False)
    return hp


def tune_all_models(gram_zz, gram_z, X_pca, y, c_grid, rf_grid, xgb_grid,
                    cv_folds, random_state, run_seed) -> dict:
    """Tune đối xứng cả 7 model trên đúng tập train N mẫu này.

    Kernel lượng tử không phụ thuộc C nên toàn bộ lưới C chỉ là các lần `SVC.fit`
    trên Gram đã có — gần như miễn phí. Ràng buộc C_ZZ = C_Z giữ nguyên tinh thần
    controlled ablation của C2.
    """
    out = {}

    q = c4.tune_quantum_C(gram_zz, y, c_grid, cv_folds, random_state)
    c_q = float(q["chosen"]["C"])
    out["QSVM_ZZ"] = {"C": c_q}
    out["QSVM_Z"] = {"C": c_q}  # ép bằng nhau, đúng protocol C2
    out["_quantum_tuning"] = {"chosen_C": c_q, "rows": q["rows"]}

    for name in c4.SVM_MODELS:
        r = c4.tune_estimator(
            c4.make_svm_estimator(name), {"svc__C": c_grid}, X_pca, y,
            selection="1SE", complexity_fn=lambda p: p["svc__C"],
            cv_folds=cv_folds, random_state=random_state,
        )
        out[name] = dict(r["chosen"]["params"])

    r = c4.tune_estimator(
        c4.make_tree_estimator("RandomForest", {}, run_seed), rf_grid, X_pca, y,
        selection="best_mean", cv_folds=cv_folds, random_state=random_state,
    )
    out["RandomForest"] = dict(r["chosen"]["params"])

    r = c4.tune_estimator(
        c4.make_tree_estimator("XGBoost", {}, run_seed), xgb_grid, X_pca, y,
        selection="best_mean", cv_folds=cv_folds, random_state=random_state,
    )
    out["XGBoost"] = dict(r["chosen"]["params"])
    return out


TEST_CHUNK = 4000


def quantum_predict_chunked(model, psi_test, psi_train, chunk: int = TEST_CHUNK):
    """Dự đoán trên test theo từng lô để chặn trần bộ nhớ.

    Gram test đầy đủ ở N=10000 là 22.544 x 10.000 float64 = 1.68 GiB, chưa kể bản
    trung gian của `np.abs(...)**2` — vượt RAM khả dụng. Chia lô 4.000 dòng test
    giữ mỗi khối ở ~320 MB, và kết quả giống hệt vì Gram tính theo từng hàng độc lập.
    """
    preds, decs = [], []
    for i in range(0, len(psi_test), chunk):
        K = c4.gram_from_statevectors(psi_test[i:i + chunk], psi_train)
        preds.append(model.predict(K))
        decs.append(model.decision_function(K))
        del K
    return np.concatenate(preds), np.concatenate(decs)


def evaluate_split(models_fitted, psi_test, psi_train, X_test_pca, y_test, is_rare) -> dict:
    """Đánh giá cả 7 model trên một test split."""
    res = {}
    for name, model in models_fitted.items():
        if name in c4.QUANTUM_MODELS:
            kern = "ZZ" if name == "QSVM_ZZ" else "Z"
            pred, dec = quantum_predict_chunked(model, psi_test[kern], psi_train[kern])
        else:
            pred = model.predict(X_test_pca)
            dec = (model.decision_function(X_test_pca)
                   if hasattr(model, "decision_function") else
                   model.predict_proba(X_test_pca)[:, 1] - 0.5)
        res[name] = c4.evaluate_predictions(y_test, pred, dec, is_rare)
    return res


def resolve_grid(protocol, spec, regime) -> list[int]:
    """Luoi N day du cua (dataset, regime) - dung de dung chuoi long nhau.

    Phai la luoi DAY DU chu khong phai tap con dang chay, neu khong thi chuoi long
    nhau se khac nhau giua cac lan chay va cache khong con nhat quan.
    """
    key = {"NSL-KDD": "nslkdd", "UNSW-NB15": "unsw"}.get(spec.name, "nslkdd")
    ov = protocol.get("dataset_overrides", {}).get(key)
    if ov and regime in ov.get("regimes", {}):
        return list(ov["regimes"][regime]["n_grid"])
    return list(protocol["sampling"]["regimes"][regime]["n_grid"])


def run_one(data, cache_dir, protocol, regime, repr_mode, arm, n, run_id, run_seed,
            sv_cache, frozen_hp, force=False, spec=None, test_subsample=None) -> dict:
    spec = spec or data.spec or c4.get_spec("nslkdd")
    tag = spec.name.replace("-", "_")
    key = f"{tag}_{regime}_{repr_mode}_{arm}_N{n}_run{run_id}"
    # Statevector CHI phu thuoc representation, KHONG phu thuoc arm (arm chi doi
    # hyperparameter cua classifier). Dung khoa rieng khong co `arm` de hai arm dung
    # chung cache -> giam mot nua chi phi mo phong.
    sv_key = f"{tag}_{regime}_{repr_mode}_N{n}_run{run_id}"
    cache_path = cache_dir / f"{key}.json"
    if cache_path.exists() and not force:
        with open(cache_path, encoding="utf-8") as fp:
            return json.load(fp)

    t0 = time.time()
    fc = data.feature_cols
    grid = resolve_grid(protocol, spec, regime)
    chain = build_chain_cached(data, run_id, grid, run_seed, regime)
    df_train = chain[n]
    y = df_train["label_binary"].to_numpy(np.int64)

    rep = (c4.make_representation(repr_mode, select_k=spec.select_k,
                                  n_components=spec.n_qubits)
           if repr_mode == "refit_per_N" else c4.make_representation(repr_mode))
    rep.fit(df_train, fc)
    X_ang, X_pca = rep.transform(df_train, fc)

    psi_tr = {k: sv_cache.get(X_ang, k, f"{sv_key}_train") for k in ("ZZ", "Z")}
    gram_tr = {"QSVM_ZZ": c4.gram_from_statevectors(psi_tr["ZZ"]),
               "QSVM_Z": c4.gram_from_statevectors(psi_tr["Z"])}

    hp_cfg = protocol["hyperparameter_protocol"]
    if arm == "tuned_per_N":
        hp = tune_all_models(
            gram_tr["QSVM_ZZ"], gram_tr["QSVM_Z"], X_pca, y,
            hp_cfg["primary_arm"]["grids"]["C_svm_and_qsvm"],
            hp_cfg["primary_arm"]["grids"]["rf"],
            hp_cfg["primary_arm"]["grids"]["xgb"],
            hp_cfg["primary_arm"]["cv_folds"], 42, run_seed,
        )
    else:
        hp = {k: dict(v) for k, v in frozen_hp.items()}

    fitted = {}
    for name in c4.QUANTUM_MODELS:
        fitted[name] = c4.make_quantum_svc(hp[name]["C"]).fit(gram_tr[name], y)
    for name in c4.SVM_MODELS:
        params = {k: v for k, v in hp[name].items() if k.startswith("svc__")}
        fitted[name] = c4.make_svm_estimator(name).set_params(**params).fit(X_pca, y)
    for name in c4.TREE_MODELS:
        params = {k: v for k, v in hp[name].items() if not k.startswith("_")}
        fitted[name] = c4.make_tree_estimator(name, params, run_seed).fit(X_pca, y)

    result = {
        "regime": regime, "repr_mode": repr_mode, "arm": arm,
        "n_train": int(n), "run_id": int(run_id), "run_seed": int(run_seed),
        "dataset": spec.name,
        "n_qubits": spec.n_qubits,
        "n_rare_train": int(c4.rare_mask(df_train, spec).sum()),
        "hyperparameters": {k: v for k, v in hp.items() if not k.startswith("_")},
        "quantum_C": float(hp["QSVM_ZZ"]["C"]),
        "splits": {},
    }

    test_full = data.df_test_full
    if test_subsample:
        sub = c4.stratified_indices(c4.stratify_label(test_full, spec),
                                    min(test_subsample, len(test_full)), seed=777)
        test_full = test_full.iloc[np.sort(sub)].reset_index(drop=True)
    for split, df_test in (("fixed_300", data.df_test_300),
                           ("full_test", test_full)):
        X_te_ang, X_te_pca = rep.transform(df_test, fc)
        y_te = df_test["label_binary"].to_numpy(np.int64)
        is_rare = c4.rare_mask(df_test, spec)
        psi_te = {k: sv_cache.get(X_te_ang, k, f"{sv_key}_{split}") for k in ("ZZ", "Z")}
        result["splits"][split] = evaluate_split(
            fitted, psi_te, psi_tr, X_te_pca, y_te, is_rare)

    result["elapsed_sec"] = round(time.time() - t0, 2)
    with open(cache_path, "w", encoding="utf-8") as fp:
        json.dump(result, fp, indent=1, ensure_ascii=False)
    return result


_CHAIN_CACHE: dict = {}


def build_chain_cached(data, run_id, grid, run_seed, regime):
    """Dựng chuỗi subset lồng nhau một lần cho mỗi (run, regime) rồi tái dùng."""
    key = (regime, run_id, tuple(grid))
    if key not in _CHAIN_CACHE:
        _CHAIN_CACHE[key] = c4.build_nested_chain(data, run_id, list(grid), run_seed, regime)
    return _CHAIN_CACHE[key]


def flatten(results: list[dict]) -> pd.DataFrame:
    rows = []
    for r in results:
        for split, models in r["splits"].items():
            for model, metrics in models.items():
                row = {
                    "regime": r["regime"], "repr_mode": r["repr_mode"], "arm": r["arm"],
                    "dataset": r.get("dataset", "NSL-KDD"), "n_train": r["n_train"],
                    "run_id": r["run_id"], "n_rare_train": r["n_rare_train"],
                    "test_split": split, "model": model,
                }
                row.update(metrics)
                rows.append(row)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="nslkdd", choices=list(c4.DATASETS))
    ap.add_argument("--regime", default="matched", choices=list(c4.SAMPLING_REGIMES))
    ap.add_argument("--test-subsample", type=int, default=None,
                    help="chi dung cho smoke test: rut gon test set")
    ap.add_argument("--repr-mode", default="refit_per_N", choices=["refit_per_N", "frozen_c1"])
    ap.add_argument("--arms", nargs="+", default=None,
                    help="mac dinh lay theo dataset: NSL-KDD dung frozen_c2, UNSW dung tuned_once")
    ap.add_argument("--n-grid", nargs="*", type=int, default=None)
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--run-ids", nargs="+", type=int, default=None,
                    help="chay dung cac run nay (de chia viec cho nhieu tien trinh song song; "
                         "cache la file JSON rieng theo (N, run) nen khong dung nhau)")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    root = c4.find_project_root()
    protocol = c4.load_protocol(root)
    out_dir = root / "results" / args.dataset / "c4_revision"
    cache_dir = out_dir / "cache"
    sv_dir = cache_dir / "statevectors"
    for d in (out_dir, cache_dir, sv_dir):
        d.mkdir(parents=True, exist_ok=True)

    spec = c4.get_spec(args.dataset)
    grid = args.n_grid or resolve_grid(protocol, spec, args.regime)
    ov = protocol.get("dataset_overrides", {}).get(args.dataset, {})
    if args.arms is None:
        args.arms = ov.get("arms", ["tuned_per_N", "frozen_c2"])
    if "frozen_c2" in args.arms and args.dataset != "nslkdd":
        raise SystemExit(
            "Arm 'frozen_c2' chi hop le cho NSL-KDD (hyperparameter dong bang cua C2). "
            f"Voi {spec.name} dung 'tuned_once'.")
    run_ids = args.run_ids or list(range(1, args.runs + 1))
    seeds = protocol["sampling"]["run_seeds"]

    print(f"regime={args.regime}  repr={args.repr_mode}  arms={args.arms}")
    print(f"N grid={grid}  runs={run_ids}")

    data = c4.load_data(root, verbose=True, dataset=args.dataset)
    sv_cache = c4.StatevectorCache(sv_dir, n_qubits=spec.n_qubits)
    if "frozen_c2" in args.arms:
        frozen_hp = load_frozen_hyperparameters(root)
    if "tuned_once" in args.arms:
        frozen_hp = tune_once_on_tuning_set(data, spec, protocol, cache_dir, sv_cache)
        print("tuned_once hyperparameters:",
              {k: v for k, v in frozen_hp.items() if k in ("QSVM_ZZ", "SVM_RBF")})
    elif "frozen_c2" not in args.arms:
        frozen_hp = {}

    chk = c4.verify_kernel_equivalence(
        np.random.default_rng(0).uniform(0, np.pi, size=(150, spec.n_qubits)),
        n_qubits=spec.n_qubits)
    assert chk["passed"], f"Kernel không tương đương: {chk}"
    print(f"kernel equivalence: max|Δ| = {chk['max_abs_diff']:.2e}  PASS\n")

    results, t0 = [], time.time()
    for arm in args.arms:
        for n in grid:
            for run_id in run_ids:
                r = run_one(data, cache_dir, protocol, args.regime, args.repr_mode, arm,
                            n, run_id, seeds[run_id - 1], sv_cache, frozen_hp,
                            args.force, spec, args.test_subsample)
                results.append(r)
            done = [x for x in results if x["arm"] == arm and x["n_train"] == n]
            zz = np.mean([x["splits"]["full_test"]["QSVM_ZZ"]["f1_macro"] for x in done])
            xgb = np.mean([x["splits"]["full_test"]["XGBoost"]["f1_macro"] for x in done])
            print(f"[{arm}] N={n:<6} ZZ={zz:.4f}  XGB={xgb:.4f}  "
                  f"({time.time()-t0:.0f}s)", flush=True)

    df = flatten(results)
    suffix = f"{args.dataset}_{args.regime}_{args.repr_mode}"
    if args.run_ids:
        suffix += "_runs" + "-".join(str(r) for r in args.run_ids)
    df.to_csv(out_dir / f"c4_per_run_{suffix}.csv", index=False)
    print(f"\nĐã ghi {len(df)} bản ghi -> c4_per_run_{suffix}.csv")


if __name__ == "__main__":
    main()
