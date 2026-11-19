"""Độ nhạy C4 khi bỏ các dòng test trùng với train (đáp phản biện R3).

Phản biện R3 đòi: "phân tích độ nhạy khi bỏ các dòng test trùng với train, nhất
là UNSW-NB15". Cache C4 (`results/<ds>/c4_revision/cache/*.json`) chỉ lưu metric
tổng hợp, không lưu dự đoán từng dòng, nên script này:

1. Với mỗi file cache: dựng lại ĐÚNG tập train con (cùng chuỗi lồng nhau, cùng
   `run_seed`, cùng lưới N đầy đủ của protocol), fit lại representation CHỈ trên
   N dòng train đó, huấn luyện lại 7 mô hình với siêu tham số ĐỌC TỪ CACHE (không
   dò lại), dự đoán trên test đầy đủ và trên fixed_300.
2. Lưu dự đoán + điểm quyết định từng dòng ra `.npz` (thư mục bị gitignore riêng).
3. Mặt nạ trùng: dòng test có bộ đặc trưng THÔ y hệt một dòng bất kỳ của TOÀN BỘ
   raw train (NSL-KDD: 41 cột đặc trưng của KDDTrain+/KDDTest+; UNSW-NB15: mọi
   cột trừ id/label/attack_cat). Lưu một lần mỗi dataset.
4. Chấm metric trên 4 split: full_test, full_test_dedup, fixed_300, fixed_300_dedup.
5. Cổng tái hiện so với cache cũ:
   - CHẶT (≤ 1e-4): f1_macro, accuracy, precision_macro, recall_macro.
   - Metric rare và margin: lệch > 1e-4 vẫn được chấp nhận NẾU suy ra được là do
     lật ≤ 1 dòng test (mỗi mô hình, mỗi split, mỗi file); ghi vào báo cáo cổng.
   Vượt mức đó -> ghi báo cáo và thoát mã 2, không đi tiếp.
   - Ngoại lệ chỉ bật bằng cờ `--allow-xgb-platform-drift`: XGBoost có
     subsample < 1 không tái hiện được trên máy này (cache gốc chạy trên máy/nền
     tảng khác; RNG lấy mẫu dòng của XGBoost phụ thuộc nền tảng). Khi bật, các ô
     đó ghi `xgb_platform_drift` thay vì FAIL; phân tích dùng bản `rerun` làm mốc.

Đường statevector (đo trong lần thử nhỏ 19-11-2026):
   - NSL-KDD: cache gốc sinh bằng `Statevector` của Qiskit -> `--sv-path auto`
     dùng Qiskit, khớp tuyệt đối (lệch 0). Đường nhanh lệch ~1e-15 làm libsvm lật
     2 dòng ở QSVM_Z.
   - UNSW-NB15: cache gốc dùng đường nhanh và có lưu statevector train/fixed_300
     -> đọc lại đúng các mảng đó (chỉ đọc), test đầy đủ tính lại; khớp ≤ 1e-15.

Chạy:
    uv run python runners/run_dedup_sensitivity.py --dataset nslkdd
    uv run python runners/run_dedup_sensitivity.py --dataset unsw
    # thử nhỏ:
    uv run python runners/run_dedup_sensitivity.py --dataset nslkdd \
        --files natural_refit_per_N_tuned_per_N_N1000_run1.json

Phân tích bản đồ regime trước/sau: `runners/analyze_dedup_sensitivity.py`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import c4_pipeline as c4  # noqa: E402

MODEL_ORDER = ["QSVM_ZZ", "QSVM_Z", "SVM_Linear", "SVM_Poly2", "SVM_RBF",
               "RandomForest", "XGBoost"]
STRICT_METRICS = ("f1_macro", "accuracy", "precision_macro", "recall_macro")
STRICT_TOL = 1e-4
# Lệch metric vì một dòng lật: lượng dư cho sai số dấu phẩy động khi suy số dòng lật
FLIP_ROUND_TOL = 0.05
TEST_CHUNK = 4000
SPLIT_ALIASES = {"full_kddtest_plus": "full_test"}

# File cache cũ của NSL-KDD không có tiền tố dataset; file mới có "NSL_KDD_"/"UNSW_NB15_".
NAME_RE = re.compile(
    r"^(?:(?P<prefix>NSL_KDD|UNSW_NB15)_)?(?P<regime>matched|natural)_"
    r"(?P<repr>refit_per_N|frozen_c1)_(?P<arm>tuned_per_N|frozen_c2|tuned_once)_"
    r"N(?P<n>\d+)_run(?P<run>\d+)\.json$")


# ---------------------------------------------------------------------------
# 1. Mặt nạ trùng trên dữ liệu THÔ
# ---------------------------------------------------------------------------


def raw_duplicate_mask(dataset: str) -> tuple[np.ndarray, dict, np.ndarray]:
    """Mặt nạ dòng test (theo thứ tự raw) có đặc trưng thô trùng một dòng raw train.

    Thứ tự dòng của file processed (`*_Test_Cleaned`) trùng thứ tự raw: đã kiểm
    (nhãn khớp 100 %, mọi cột số đơn điệu theo cột raw tương ứng). Hàm vẫn kiểm
    lại nhãn ở `check_alignment` mỗi lần chạy.
    """
    if dataset == "nslkdd":
        raw_dir = ROOT / "data" / "nslkdd" / "raw"
        p_tr, p_te = raw_dir / "KDDTrain+.txt", raw_dir / "KDDTest+.txt"
        tr = pd.read_csv(p_tr, header=None, encoding="utf-8")
        te = pd.read_csv(p_te, header=None, encoding="utf-8")
        feat = list(range(41))            # cột 41 = nhãn, 42 = độ khó
        y_raw = (te[41] != "normal").to_numpy(np.int64)
        feat_desc = "41 cot dac trung KDD (bo cot nhan 41 va do kho 42)"
    else:
        raw_dir = ROOT / "data" / "unsw" / "raw"
        p_tr = raw_dir / "UNSW_NB15_training-set.parquet"
        p_te = raw_dir / "UNSW_NB15_testing-set.parquet"
        tr, te = pd.read_parquet(p_tr), pd.read_parquet(p_te)
        feat = [c for c in tr.columns if c not in ("id", "label", "attack_cat")]
        y_raw = te["label"].to_numpy(np.int64)
        feat_desc = f"{len(feat)} cot (moi cot tru id/label/attack_cat)"
    sig_tr = pd.util.hash_pandas_object(tr[feat], index=False)
    sig_te = pd.util.hash_pandas_object(te[feat], index=False)
    mask = sig_te.isin(set(sig_tr.tolist())).to_numpy()
    meta = {
        "dataset": dataset,
        "definition": "dong test co bo dac trung tho y het mot dong bat ky cua TOAN BO raw train",
        "features": feat_desc,
        "raw_train": str(p_tr.relative_to(ROOT)),
        "raw_test": str(p_te.relative_to(ROOT)),
        "raw_train_sha256": c4.file_sha256(p_tr),
        "raw_test_sha256": c4.file_sha256(p_te),
        "n_train_raw": int(len(tr)),
        "n_test_raw": int(len(te)),
        "n_test_duplicate": int(mask.sum()),
        "frac_test_duplicate": float(mask.mean()),
    }
    return mask, meta, y_raw


def fixed300_indices(data: c4.DataBundle, spec) -> np.ndarray:
    """Chỉ số (trong test đầy đủ) của từng dòng fixed_300, đúng thứ tự `df_test_300`.

    UNSW: fixed_300 do `load_data` lấy bằng `stratified_indices(..., seed=777)`
    rồi sắp tăng dần -> tính lại y hệt. NSL-KDD: fixed_300 là file CSV riêng rút từ
    KDDTest+ -> ghép về bằng chữ ký hàng processed (đặc trưng + nhãn).
    """
    if spec.fixed_test_file is None:
        idx = c4.stratified_indices(c4.stratify_label(data.df_test_full, spec), 300, seed=777)
        return np.sort(idx)
    fc = data.feature_cols
    sig_full = c4.row_signatures(data.df_test_full, fc)
    sig_300 = c4.row_signatures(data.df_test_300, fc)
    first = {}
    for i, s in enumerate(sig_full.tolist()):
        first.setdefault(s, i)
    out = np.array([first[s] for s in sig_300.tolist()], dtype=np.int64)
    return out


def load_or_build_mask(dataset: str, data: c4.DataBundle, spec, out_dir: Path) -> dict:
    """Dựng (hoặc nạp) mặt nạ trùng + chỉ số fixed_300; lưu một lần mỗi dataset."""
    path_npz = out_dir / "dup_mask.npz"
    path_meta = out_dir / "dup_mask_meta.json"
    if path_npz.exists() and path_meta.exists():
        z = np.load(path_npz)
        with open(path_meta, encoding="utf-8") as fp:
            meta = json.load(fp)
        return {"full": z["dup_full"], "fixed_300_idx": z["fixed_300_idx"],
                "fixed_300": z["dup_fixed_300"], "meta": meta}

    mask, meta, y_raw = raw_duplicate_mask(dataset)
    y_proc = data.df_test_full["label_binary"].to_numpy(np.int64)
    if len(y_proc) != len(y_raw) or not np.array_equal(y_proc, y_raw):
        raise SystemExit("Thu tu dong processed khong khop raw (nhan lech) -> dung.")
    idx300 = fixed300_indices(data, spec)
    # NSL-KDD có 3 chữ ký processed lặp trong test: kiểm mọi bản sao cùng trạng thái trùng
    if spec.fixed_test_file is not None:
        sig_full = c4.row_signatures(data.df_test_full, data.feature_cols)
        groups = pd.Series(np.arange(len(sig_full))).groupby(sig_full)
        for s in set(c4.row_signatures(data.df_test_300, data.feature_cols).tolist()):
            members = groups.get_group(s).to_numpy()
            if len(members) > 1 and len(set(mask[members].tolist())) > 1:
                raise SystemExit(f"fixed_300: chu ky {s} lap nhung trang thai trung khac nhau")
    dup300 = mask[idx300]
    meta.update({"fixed_300_source": ("stratified seed 777 tu test day du"
                                      if spec.fixed_test_file is None
                                      else f"{spec.fixed_test_file}, ghep ve test bang chu ky hang"),
                 "n_fixed_300_duplicate": int(dup300.sum())})
    np.savez_compressed(path_npz, dup_full=mask, fixed_300_idx=idx300, dup_fixed_300=dup300)
    with open(path_meta, "w", encoding="utf-8") as fp:
        json.dump(meta, fp, indent=1, ensure_ascii=False)
    return {"full": mask, "fixed_300_idx": idx300, "fixed_300": dup300, "meta": meta}


# ---------------------------------------------------------------------------
# 2. Statevector (đường nhanh dạng đóng hoặc đường Qiskit để chẩn đoán)
# ---------------------------------------------------------------------------

_SV_MEM: dict = {}


def statevectors(X_ang: np.ndarray, kernel: str, n_qubits: int, path: str, key: str,
                 orig_file: Path | None = None):
    """Statevector của một tập; nhớ trong RAM theo khóa để hai arm dùng chung.

    Nếu lần chạy gốc đã lưu statevector của tập này (`orig_file`, chỉ có cho tập
    train và fixed_300 vì mảng > 20.000 dòng không được ghi đĩa) thì ĐỌC LẠI đúng
    mảng đó: tính lại trên máy khác lệch ~1e-16, đủ để libsvm lật vài điểm sát
    biên. Chỉ đọc, không ghi vào cache cũ của C4.
    """
    k = (path, kernel, key)
    if k in _SV_MEM:
        return _SV_MEM[k]
    if orig_file is not None and orig_file.exists():
        psi = np.load(orig_file)
        if len(psi) == len(X_ang):
            # Kiểm mảng cũ đúng là của tập này (lệch dấu phẩy động, không lệch dữ liệu)
            ref = c4.compute_statevectors_fast(X_ang, kernel, n_qubits)
            if np.abs(psi - ref).max() > 1e-10:
                raise SystemExit(f"Statevector goc {orig_file.name} khong khop du lieu dung lai")
            _SV_MEM[k] = psi
            return psi
    if path == "fast":
        psi = c4.compute_statevectors_fast(X_ang, kernel, n_qubits)
    else:
        psi = c4.compute_statevectors(X_ang, c4.build_feature_map(kernel, n_qubits))
    if len(_SV_MEM) >= 8:          # giữ RAM: UNSW test là 84 MB mỗi mảng
        _SV_MEM.pop(next(iter(_SV_MEM)))
    _SV_MEM[k] = psi
    return psi


def quantum_predict_chunked(model, psi_test, psi_train, chunk: int = TEST_CHUNK):
    """Giống `run_c4.quantum_predict_chunked`: Gram test theo lô 4.000 dòng."""
    preds, decs = [], []
    for i in range(0, len(psi_test), chunk):
        K = c4.gram_from_statevectors(psi_test[i:i + chunk], psi_train)
        preds.append(model.predict(K))
        decs.append(model.decision_function(K))
        del K
    return np.concatenate(preds), np.concatenate(decs)


# ---------------------------------------------------------------------------
# 3. Dựng lại một ô cache
# ---------------------------------------------------------------------------

_CHAIN: dict = {}


def resolve_grid(protocol, spec, regime) -> list[int]:
    """Lưới N đầy đủ (giống `run_c4.resolve_grid`) để chuỗi lồng nhau y hệt."""
    key = {"NSL-KDD": "nslkdd", "UNSW-NB15": "unsw"}[spec.name]
    ov = protocol.get("dataset_overrides", {}).get(key)
    if ov and regime in ov.get("regimes", {}):
        return list(ov["regimes"][regime]["n_grid"])
    return list(protocol["sampling"]["regimes"][regime]["n_grid"])


def fit_models(hp: dict, gram_tr: dict, X_pca: np.ndarray, y: np.ndarray, run_seed: int):
    """Fit 7 mô hình với siêu tham số đọc từ cache (cùng cách lọc khóa như run_c4)."""
    fitted = {}
    for name in c4.QUANTUM_MODELS:
        fitted[name] = c4.make_quantum_svc(hp[name]["C"]).fit(gram_tr[name], y)
    for name in c4.SVM_MODELS:
        params = {k: v for k, v in hp[name].items() if k.startswith("svc__")}
        fitted[name] = c4.make_svm_estimator(name).set_params(**params).fit(X_pca, y)
    for name in c4.TREE_MODELS:
        params = {k: v for k, v in hp[name].items() if not k.startswith("_")}
        fitted[name] = c4.make_tree_estimator(name, params, run_seed).fit(X_pca, y)
    return fitted


def predict_all(fitted, psi_te, psi_tr, X_te_pca):
    """Dự đoán + điểm quyết định của 7 mô hình (cùng công thức `evaluate_split`)."""
    out = {}
    for name, model in fitted.items():
        if name in c4.QUANTUM_MODELS:
            kern = "ZZ" if name == "QSVM_ZZ" else "Z"
            pred, dec = quantum_predict_chunked(model, psi_te[kern], psi_tr[kern])
        else:
            pred = model.predict(X_te_pca)
            dec = (model.decision_function(X_te_pca)
                   if hasattr(model, "decision_function") else
                   model.predict_proba(X_te_pca)[:, 1] - 0.5)
        out[name] = (np.asarray(pred).astype(np.int64), np.asarray(dec, dtype=np.float64))
    return out


def rerun_one(cache_path: Path, data, spec, protocol, masks, sv_path: str,
              reuse_orig_sv: bool = True) -> dict:
    """Dựng lại một file cache; trả về metric 4 split + dự đoán từng dòng."""
    with open(cache_path, encoding="utf-8") as fp:
        old = json.load(fp)
    regime, repr_mode, arm = old["regime"], old["repr_mode"], old["arm"]
    n, run_id, run_seed = int(old["n_train"]), int(old["run_id"]), int(old["run_seed"])
    hp = old["hyperparameters"]
    fc = data.feature_cols

    t0 = time.time()
    grid = resolve_grid(protocol, spec, regime)
    ck = (regime, run_id)
    if ck not in _CHAIN:
        _CHAIN.clear()   # chỉ giữ chuỗi của run đang chạy cho đỡ RAM
        _CHAIN[ck] = c4.build_nested_chain(data, run_id, grid, run_seed, regime)
    df_train = _CHAIN[ck][n]
    y = df_train["label_binary"].to_numpy(np.int64)
    n_rare_train = int(c4.rare_mask(df_train, spec).sum())
    if n_rare_train != int(old["n_rare_train"]):
        raise SystemExit(f"{cache_path.name}: n_rare_train {n_rare_train} != cache "
                         f"{old['n_rare_train']} -> tap train con khong tai hien duoc")

    rep = (c4.make_representation(repr_mode, select_k=spec.select_k,
                                  n_components=spec.n_qubits)
           if repr_mode == "refit_per_N" else c4.make_representation(repr_mode))
    rep.fit(df_train, fc)                 # zero-leakage: fit chỉ trên N dòng train
    X_ang, X_pca = rep.transform(df_train, fc)
    sv_key = f"{regime}_{repr_mode}_N{n}_run{run_id}"
    # Khóa statevector của lần chạy gốc (giống `run_c4.run_one`): không phụ thuộc arm
    orig_key = f"{spec.name.replace('-', '_')}_{regime}_{repr_mode}_N{n}_run{run_id}"
    orig_sv_dir = ROOT / "results" / ("nslkdd" if spec.name == "NSL-KDD" else "unsw") \
        / "c4_revision" / "cache" / "statevectors"

    # File cache NSL-KDD kiểu cũ (không có khóa 'dataset') sinh bằng đường Qiskit và
    # không lưu statevector; các psi_* NSL_KDD_* trên đĩa là của 5 file chạy lại bằng
    # đường nhanh -> KHÔNG được dùng cho file kiểu cũ.
    use_orig = reuse_orig_sv and "dataset" in old

    def orig(kernel, split):
        return (orig_sv_dir / f"psi_{kernel}_{orig_key}_{split}.npy") if use_orig else None

    psi_tr = {k: statevectors(X_ang, k, spec.n_qubits, sv_path, f"{sv_key}_train",
                              orig(k, "train"))
              for k in ("ZZ", "Z")}
    gram_tr = {"QSVM_ZZ": c4.gram_from_statevectors(psi_tr["ZZ"]),
               "QSVM_Z": c4.gram_from_statevectors(psi_tr["Z"])}
    fitted = fit_models(hp, gram_tr, X_pca, y, run_seed)

    split_frames = {"fixed_300": (data.df_test_300, masks["fixed_300"]),
                    "full_test": (data.df_test_full, masks["full"])}
    metrics, arrays = {}, {}
    for split, (df_test, dup) in split_frames.items():
        X_te_ang, X_te_pca = rep.transform(df_test, fc)
        y_te = df_test["label_binary"].to_numpy(np.int64)
        is_rare = c4.rare_mask(df_test, spec)
        psi_te = {k: statevectors(X_te_ang, k, spec.n_qubits, sv_path, f"{sv_key}_{split}",
                                  orig(k, split))
                  for k in ("ZZ", "Z")}
        preds = predict_all(fitted, psi_te, psi_tr, X_te_pca)
        keep = ~dup
        metrics[split], metrics[f"{split}_dedup"] = {}, {}
        for name in MODEL_ORDER:
            pred, dec = preds[name]
            metrics[split][name] = c4.evaluate_predictions(y_te, pred, dec, is_rare)
            metrics[f"{split}_dedup"][name] = c4.evaluate_predictions(
                y_te[keep], pred[keep], dec[keep], is_rare[keep])
            arrays[f"pred__{split}__{name}"] = pred.astype(np.int8)
            arrays[f"dec__{split}__{name}"] = dec.astype(np.float32)
        metrics[split]["_n_rows"] = int(len(y_te))
        metrics[f"{split}_dedup"]["_n_rows"] = int(keep.sum())

    return {"old": old, "metrics": metrics, "arrays": arrays,
            "elapsed_sec": round(time.time() - t0, 2),
            "meta": {"regime": regime, "repr_mode": repr_mode, "arm": arm,
                     "n_train": n, "run_id": run_id, "run_seed": run_seed,
                     "n_rare_train": n_rare_train, "dataset": spec.name,
                     "n_qubits": spec.n_qubits, "hyperparameters": hp,
                     "sv_path": sv_path, "reuse_orig_sv": use_orig,
                     "source_cache": cache_path.name}}


# ---------------------------------------------------------------------------
# 4. Cổng tái hiện
# ---------------------------------------------------------------------------


def gate_rows(res: dict, allow_xgb_drift: bool = False) -> list[dict]:
    """So metric full_test và fixed_300 với cache cũ; suy số dòng lật từ lệch metric.

    Không có dự đoán cũ nên số dòng lật là ƯỚC LƯỢNG CẬN DƯỚI:
    - lật toàn split ≈ |Δaccuracy| * n_rows (lật ngược chiều nhau bù trừ nhau);
    - lật trong nhóm rare ≈ |Δrecall_rare| * n_rare (nhóm rare toàn nhãn attack).
    Lấy max của hai ước lượng làm `flips_est`.
    """
    rows = []
    old_splits = {SPLIT_ALIASES.get(k, k): v for k, v in res["old"]["splits"].items()}
    for split in ("full_test", "fixed_300"):
        new_s, old_s = res["metrics"][split], old_splits[split]
        n_rows = new_s["_n_rows"]
        for name in MODEL_ORDER:
            new_m, old_m = new_s[name], old_s[name]
            d_acc = abs(new_m["accuracy"] - old_m["accuracy"])
            flips_all = d_acc * n_rows
            n_rare = new_m.get("n_rare", 0) or 0
            flips_rare = (abs(new_m.get("recall_rare", 0) - old_m.get("recall_rare", 0)) * n_rare
                          if n_rare else 0.0)
            flips_est = max(flips_all, flips_rare)
            for metric, v_old in old_m.items():
                if metric == "n_rare":
                    status = "ok" if int(v_old) == int(new_m.get("n_rare", -1)) else "FAIL"
                    rows.append(dict(split=split, model=name, metric=metric, old=v_old,
                                     new=new_m.get("n_rare"), abs_diff=0.0,
                                     flips_est=flips_est, status=status))
                    continue
                v_new = new_m.get(metric, np.nan)
                diff = abs(float(v_new) - float(v_old))
                if diff <= STRICT_TOL:
                    status = "ok"
                elif metric in STRICT_METRICS:
                    status = "FAIL"
                elif flips_est <= 1.0 + FLIP_ROUND_TOL:
                    status = "tolerated_le1_flip"
                else:
                    status = "FAIL"
                xgb_sub = float(res["meta"]["hyperparameters"]["XGBoost"].get("subsample", 1.0))
                if status == "FAIL" and allow_xgb_drift and name == "XGBoost" and xgb_sub < 1.0:
                    status = "xgb_platform_drift"
                rows.append(dict(split=split, model=name, metric=metric, old=v_old,
                                 new=v_new, abs_diff=diff, flips_est=flips_est,
                                 status=status))
    return rows


# ---------------------------------------------------------------------------
# 5. Chương trình chính
# ---------------------------------------------------------------------------


def list_cache_files(cache_dir: Path, args) -> list[Path]:
    files = []
    for p in sorted(cache_dir.glob("*_run*.json")):
        m = NAME_RE.match(p.name)
        if not m:
            continue
        if args.files and p.name not in args.files:
            continue
        if (not args.files and m["prefix"] == "NSL_KDD"
                and not getattr(args, "include_rerun_controls", False)):
            continue
        if args.n and int(m["n"]) not in args.n:
            continue
        if args.runs and int(m["run"]) not in args.runs:
            continue
        if args.arms and m["arm"] not in args.arms:
            continue
        files.append(p)
    # Gom các arm cùng (regime, repr, run, N) đứng cạnh nhau để dùng chung statevector
    def key(p):
        m = NAME_RE.match(p.name)
        return (m["regime"], m["repr"], int(m["run"]), int(m["n"]), m["arm"], p.name)
    return sorted(files, key=key)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, choices=["nslkdd", "unsw"])
    ap.add_argument("--files", nargs="*", default=None, help="ten file cache cu the")
    ap.add_argument("--n", nargs="*", type=int, default=None)
    ap.add_argument("--runs", nargs="*", type=int, default=None)
    ap.add_argument("--arms", nargs="*", default=None)
    ap.add_argument("--sv-path", default="auto", choices=["auto", "fast", "qiskit"],
                    help="auto: NSL-KDD dung qiskit (cache cu sinh bang Statevector cua "
                         "Qiskit, khop tuyet doi), UNSW dung duong nhanh + statevector goc")
    ap.add_argument("--allow-xgb-platform-drift", action="store_true",
                    help="XGBoost subsample<1 khong tai hien duoc tren may nay (RNG lay mau "
                         "dong khac nen tang): ghi trang thai 'xgb_platform_drift' thay vi FAIL")
    ap.add_argument("--include-rerun-controls", action="store_true",
                    help="NSL-KDD: gom ca 5 file NSL_KDD_matched_* (ban chay lai doi chung)")
    ap.add_argument("--out-tag", default="",
                    help="hau to thu muc ket qua (vd _qiskit) de khong lan voi ban chinh")
    ap.add_argument("--no-reuse-orig-sv", action="store_true",
                    help="khong doc statevector train/fixed_300 da luu cua lan chay goc")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--diagnose", action="store_true",
                    help="chan doan: gap FAIL van chay tiep, van luu ket qua nhung danh dau "
                         "gate_passed=false (phan tich se bo qua file do); cuoi cung thoat 2")
    args = ap.parse_args()

    spec = c4.get_spec(args.dataset)
    protocol = c4.load_protocol(ROOT)
    if args.sv_path == "auto":
        args.sv_path = "qiskit" if args.dataset == "nslkdd" else "fast"
    src_cache = ROOT / "results" / args.dataset / "c4_revision" / "cache"
    out_dir = ROOT / "results" / args.dataset / f"c4_dedup{args.out_tag}"
    out_cache = out_dir / "cache"
    out_cache.mkdir(parents=True, exist_ok=True)
    gi = out_cache / ".gitignore"
    if not gi.exists():
        with open(gi, "w", encoding="utf-8") as fp:
            fp.write("# Du doan tung dong: lon, sinh lai duoc bang runners/run_dedup_sensitivity.py\n*\n")

    data = c4.load_data(ROOT, verbose=False, dataset=args.dataset)
    masks = load_or_build_mask(args.dataset, data, spec, out_dir)
    mm = masks["meta"]
    print(f"{spec.name}: test trung train = {mm['n_test_duplicate']}/{mm['n_test_raw']} "
          f"({100 * mm['frac_test_duplicate']:.2f} %); fixed_300 trung = "
          f"{int(masks['fixed_300'].sum())}/300")

    files = list_cache_files(src_cache, args)
    print(f"{len(files)} file cache se dung lai (sv_path={args.sv_path})", flush=True)
    all_gate, t_all, any_fail = [], time.time(), False
    gate_path = out_dir / f"gate_report{'' if not (args.files or args.n or args.runs or args.arms) else '_partial'}.csv"
    for i, p in enumerate(files, 1):
        stem = p.stem
        out_json, out_npz = out_cache / f"{stem}.json", out_cache / f"{stem}.npz"
        if out_json.exists() and out_npz.exists() and not args.force:
            with open(out_json, encoding="utf-8") as fp:
                saved = json.load(fp)
            # Chỉ bỏ qua file đã QUA cổng; file lưu ở chế độ --diagnose mà rớt cổng thì làm lại
            if saved.get("gate_passed", False):
                all_gate.extend(dict(file=p.name, **r) for r in saved["gate"])
                print(f"[{i}/{len(files)}] {p.name}: da co, bo qua", flush=True)
                continue
        res = rerun_one(p, data, spec, protocol, masks, args.sv_path,
                        reuse_orig_sv=not args.no_reuse_orig_sv)
        rows = gate_rows(res, args.allow_xgb_platform_drift)
        all_gate.extend(dict(file=p.name, **r) for r in rows)
        n_fail = sum(r["status"] == "FAIL" for r in rows)
        n_tol = sum(r["status"] == "tolerated_le1_flip" for r in rows)
        n_drift = sum(r["status"] == "xgb_platform_drift" for r in rows)
        strict_max = max(r["abs_diff"] for r in rows if r["metric"] in STRICT_METRICS)
        all_max = max(r["abs_diff"] for r in rows)
        print(f"[{i}/{len(files)}] {p.name}: {res['elapsed_sec']:.1f}s  "
              f"lech chat max={strict_max:.2e}  lech moi metric max={all_max:.2e}  "
              f"dung sai(<=1 dong)={n_tol}  xgb_drift={n_drift}  FAIL={n_fail}  "
              f"(goc {res['old'].get('elapsed_sec', float('nan'))}s)", flush=True)
        if n_fail:
            pd.DataFrame(all_gate).to_csv(gate_path, index=False, encoding="utf-8")
            bad = [r for r in rows if r["status"] == "FAIL"][:10]
            for r in bad:
                print(f"   FAIL {r['split']} {r['model']} {r['metric']}: "
                      f"cu={r['old']} moi={r['new']} |d|={r['abs_diff']:.2e} "
                      f"lat~{r['flips_est']:.2f}")
            any_fail = True
            if not args.diagnose:
                print(f"Cong tai hien KHONG QUA o {p.name} -> dung. Bao cao: {gate_path}")
                sys.exit(2)
        np.savez_compressed(out_npz, **res["arrays"])
        payload = {**res["meta"], "elapsed_sec": res["elapsed_sec"],
                   "gate_passed": not n_fail, "xgb_platform_drift": bool(n_drift),
                   "splits": res["metrics"], "gate": rows}
        with open(out_json, "w", encoding="utf-8") as fp:
            json.dump(payload, fp, indent=1, ensure_ascii=False, default=float)

    gdf = pd.DataFrame(all_gate)
    gdf.to_csv(gate_path, index=False, encoding="utf-8")
    if len(gdf):
        print("\n=== Cong tai hien: lech tuyet doi lon nhat theo metric ===")
        summ = gdf.groupby("metric").agg(max_abs_diff=("abs_diff", "max"),
                                         n_tolerated=("status", lambda s: (s == "tolerated_le1_flip").sum()),
                                         n_xgb_drift=("status", lambda s: (s == "xgb_platform_drift").sum()),
                                         n_fail=("status", lambda s: (s == "FAIL").sum()))
        print(summ.to_string(float_format=lambda v: f"{v:.2e}"))
        tol = gdf[gdf.status == "tolerated_le1_flip"][["file", "split", "model"]].drop_duplicates()
        print(f"\nO (file, split, model) co lech do lat <=1 dong: {len(tol)}")
        by_model = (gdf.groupby(["split", "model"])
                    .agg(max_abs_diff=("abs_diff", "max"), max_flips_est=("flips_est", "max"),
                         n_fail=("status", lambda s: (s == "FAIL").sum())))
        print("\n=== Theo (split, model) ===")
        print(by_model.to_string(float_format=lambda v: f"{v:.2e}"))
        any_fail = any_fail or bool((gdf.status == "FAIL").any())
    print(f"\nXong {len(files)} file trong {time.time() - t_all:.1f}s. Bao cao cong: {gate_path}")
    if any_fail:
        print("CONG TAI HIEN: CO FAIL (che do --diagnose) -> thoat 2")
        sys.exit(2)


if __name__ == "__main__":
    main()
