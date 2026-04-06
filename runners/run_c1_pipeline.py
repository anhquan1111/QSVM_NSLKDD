"""
Runner script cho Contribution 1 (C1): Pipeline tối ưu hóa nhúng lượng tử có ràng buộc phần cứng.

Điều phối toàn bộ pipeline C1 theo thứ tự:
  1. Tải dữ liệu thô NSL-KDD và làm sạch (DataLoader + OHETransformer)
  2. One-Hot Encoding zero-leakage (fit CHỈ trên train)
  3. SelectKBest optimization — tìm K tối ưu qua 5-fold CV
  4. Pareto-optimal PCA — tìm n_components tối ưu theo đa mục tiêu
  5. MinMaxScaler [0, π] cho quantum angle encoding
  6. Lưu tất cả transformers (OHE, SelectKBest, PCA, Scaler) và dữ liệu đã xử lý

Cách chạy (từ thư mục gốc của project):
    python runners/run_c1_pipeline.py
"""

import logging
import sys
import time
from pathlib import Path

import joblib
import numpy as np

# -- Thêm thư mục gốc vào sys.path để import config và src --
ROOT_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR))

from config import (
    DATA_PROCESSED_DIR,
    MODELS_DIR,
    NSLKDD_TEST_RAW,
    NSLKDD_TRAIN_RAW,
)
from src.features import (
    run_c1_feature_pipeline,
    save_features_artifacts,
)
from src.preprocess import (
    get_feature_columns,
    preprocess_nsl_kdd,
    run_sanity_checks,
    save_all_artifacts,
    stratified_sample_for_qsvm,
)

# -- Cấu hình logging với định dạng dễ đọc --
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def main():
    """Hàm chính điều phối toàn bộ pipeline C1."""
    t_start = time.time()
    log.info("=" * 65)
    log.info("BẮT ĐẦU PIPELINE C1: TỐI ƯU HÓA NHÚNG LƯỢNG TỬ (NISQ)")
    log.info("=" * 65)

    # ─────────────────────────────────────────────────────────────
    # Bước 1: Tải dữ liệu thô và tiền xử lý (OHE + MinMax[0,1])
    # ─────────────────────────────────────────────────────────────
    log.info("[1/6] Đang tải và làm sạch dữ liệu thô NSL-KDD...")
    log.info(f"      Train: {NSLKDD_TRAIN_RAW}")
    log.info(f"      Test : {NSLKDD_TEST_RAW}")

    # preprocess_nsl_kdd thực hiện: load → OHE (zero-leakage) → MinMax[0,1]
    train_proc, test_proc, scaler_01, ohe = preprocess_nsl_kdd()

    feat_cols = get_feature_columns(train_proc)
    log.info(f"      -> Train: {train_proc.shape[0]:,} mẫu")
    log.info(f"      -> Test : {test_proc.shape[0]:,} mẫu")
    log.info(f"      -> Số đặc trưng sau OHE: {len(feat_cols)}D")

    # ─────────────────────────────────────────────────────────────
    # Bước 2: Sanity checks
    # ─────────────────────────────────────────────────────────────
    log.info("[2/6] Đang chạy sanity checks...")
    checks = run_sanity_checks(train_proc, test_proc)
    passed = sum(1 for v in checks.values() if v)
    log.info(f"      -> {passed}/{len(checks)} checks PASSED")

    # ─────────────────────────────────────────────────────────────
    # Bước 3: Lưu artifacts tiền xử lý (CSV + OHE transformer)
    # ─────────────────────────────────────────────────────────────
    log.info("[3/6] Đang lưu dữ liệu đã làm sạch và OHE artifacts...")

    # Tạo sample 1000 mẫu stratified (bao gồm U2R/R2L)
    sample_1000 = stratified_sample_for_qsvm(train_proc, n_samples=1000)
    save_all_artifacts(train_proc, test_proc, scaler_01, sample_1000=sample_1000)

    # Lưu OHE transformer
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    ohe_path = MODELS_DIR / "ohe_transformer.joblib"
    if not ohe_path.exists():
        joblib.dump(ohe, ohe_path)
        log.info(f"      -> Đã lưu: {ohe_path.name}")
    else:
        log.info(f"      -> Đã tồn tại, bỏ qua: {ohe_path.name}")

    # Lưu scaler tiền xử lý [0,1] (khác với scaler quantum [0,π])
    scaler_01_path = MODELS_DIR / "scaler_minmax_01.joblib"
    if not scaler_01_path.exists():
        joblib.dump(scaler_01, scaler_01_path)
        log.info(f"      -> Đã lưu: {scaler_01_path.name}")
    else:
        log.info(f"      -> Đã tồn tại, bỏ qua: {scaler_01_path.name}")

    log.info(f"      -> CSV đã lưu tại: {DATA_PROCESSED_DIR}/")

    # ─────────────────────────────────────────────────────────────
    # Bước 4: C1 Feature Pipeline (SelectKBest CV + PCA Pareto)
    # ─────────────────────────────────────────────────────────────
    log.info("[4/6] Đang chạy C1 feature pipeline (SelectKBest + PCA Pareto)...")
    log.info("      Lưu ý: Bước này có thể mất vài phút (5-fold CV + bootstrap).")

    t_pipeline = time.time()
    results = run_c1_feature_pipeline(train_proc, test_proc, run_ablation=True)
    elapsed_pipeline = time.time() - t_pipeline

    # Giải nén kết quả
    X_train  = results["X_train"]
    X_test   = results["X_test"]
    y_train  = results["y_train"]
    y_test   = results["y_test"]
    k_final  = results["k_final"]
    n_chosen = results["n_chosen"]

    log.info(f"      -> Hoàn thành sau {elapsed_pipeline:.1f}s")
    log.info(f"      -> K tối ưu (SelectKBest): {k_final}")
    log.info(f"      -> n_components tối ưu (PCA): {n_chosen} qubit")
    log.info(f"      -> X_train: shape={X_train.shape}, range=[{X_train.min():.4f}, {X_train.max():.4f}]")
    log.info(f"      -> X_test : shape={X_test.shape}, range=[{X_test.min():.4f}, {X_test.max():.4f}]")

    # Tóm tắt phân phối nhãn
    n_normal_tr = (y_train == 0).sum()
    n_attack_tr = (y_train == 1).sum()
    n_normal_te = (y_test == 0).sum()
    n_attack_te = (y_test == 1).sum()
    log.info(f"      -> y_train: Normal={n_normal_tr:,}, Attack={n_attack_tr:,} "
             f"(tỉ lệ Attack: {n_attack_tr / len(y_train):.1%})")
    log.info(f"      -> y_test : Normal={n_normal_te:,}, Attack={n_attack_te:,} "
             f"(tỉ lệ Attack: {n_attack_te / len(y_test):.1%})")

    # ─────────────────────────────────────────────────────────────
    # Bước 5: Lưu transformers C1
    # ─────────────────────────────────────────────────────────────
    log.info("[5/6] Đang lưu transformers C1 (selector, PCA, scaler quantum)...")

    selected_names = None
    optimizer = results.get("optimizer")
    if optimizer is not None and hasattr(optimizer, "selected_features_"):
        selected_names = optimizer.selected_features_

    save_features_artifacts(
        selector=results["selector"],
        pca=results["pca"],
        scaler=results["scaler"],
        k_final=k_final,
        n_chosen=n_chosen,
        cv_results=results["cv_results"],
        ablation_df=results["ablation_df"],
        pareto_results=results["pareto_results"],
        selected_feature_names=selected_names,
    )

    log.info(f"      -> feature_selector_k{k_final}.joblib")
    log.info(f"      -> pca_{n_chosen}components.joblib")
    log.info("      -> scaler_minmax_pi.joblib")
    if results["cv_results"] is not None:
        log.info("      -> selectkbest_cv_results.csv")
    if results["ablation_df"] is not None:
        log.info("      -> ablation_study_results.csv")
    if results["pareto_results"] is not None:
        log.info("      -> pca_pareto_results.csv")

    # ─────────────────────────────────────────────────────────────
    # Bước 6: Lưu numpy arrays (X_train, X_test, y_train, y_test)
    # ─────────────────────────────────────────────────────────────
    log.info("[6/6] Đang lưu dữ liệu đã xử lý dạng numpy arrays (.npy)...")
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    arrays_to_save = {
        "X_train": X_train,
        "X_test":  X_test,
        "y_train": y_train,
        "y_test":  y_test,
    }

    for name, arr in arrays_to_save.items():
        path = DATA_PROCESSED_DIR / f"{name}.npy"
        if not path.exists():
            np.save(str(path), arr)
            log.info(f"      -> Đã lưu {name}.npy (shape={arr.shape}, dtype={arr.dtype})")
        else:
            log.info(f"      -> Đã tồn tại, bỏ qua: {name}.npy")

    # ─────────────────────────────────────────────────────────────
    # Tóm tắt kết quả cuối
    # ─────────────────────────────────────────────────────────────
    elapsed_total = time.time() - t_start
    log.info("")
    log.info("=" * 65)
    log.info("TÓM TẮT KẾT QUẢ PIPELINE C1")
    log.info("=" * 65)
    log.info(
        f"  Pipeline: NSL-KDD (41 fts) "
        f"→ OHE ({len(feat_cols)}D) "
        f"→ SelectKBest ({k_final}D) "
        f"→ PCA ({n_chosen}D) "
        f"→ MinMax[0,π]"
    )

    # F1-macro tốt nhất từ SelectKBest CV
    if results["cv_results"] is not None:
        best_k_row = results["cv_results"].loc[
            results["cv_results"]["f1_mean"].idxmax()
        ]
        log.info(
            f"  SelectKBest: K={int(best_k_row['K'])}, "
            f"F1-macro={best_k_row['f1_mean']:.4f} ± {best_k_row['f1_std']:.4f}"
        )

    # Bootstrap CI cho n_chosen
    ci = results.get("ci")
    if ci is not None and n_chosen in ci:
        ci_n = ci[n_chosen]
        f_mean = ci_n.get("F_mean", float("nan"))
        f_lo, f_hi = ci_n.get("F_ci", (float("nan"), float("nan")))
        sil_mean = ci_n.get("sil_mean", float("nan"))
        log.info(
            f"  PCA Pareto: n={n_chosen}, "
            f"F(n)={f_mean:.4f} [CI 95%: {f_lo:.4f}, {f_hi:.4f}], "
            f"Silhouette={sil_mean:.4f}"
        )

    log.info(f"  Thời gian tổng: {elapsed_total:.1f}s")
    log.info("  PIPELINE C1 HOÀN THÀNH THÀNH CÔNG!")
    log.info("=" * 65)


if __name__ == "__main__":
    main()
