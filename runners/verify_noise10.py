"""Doi chieu doc lap ket qua noise-check 10 run cua C2.

Doc thang 10 file cache thoi, khong goi ham thong ke nao cua pipeline: neu
pipeline va bai bao cung dung mot ham sai thi doi chieu kieu do khong bat
duoc gi. Wilcoxon va khoang tin cay tinh lai bang scipy.

    python runners/verify_noise10.py
"""

from __future__ import annotations

import glob
import io
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "results/nslkdd/c2_revision/cache"
COND = ("ideal_statevector", "ideal_finite_shot", "realistic_noisy_simulator")
MODELS = ("QSVM_ZZ", "QSVM_Z")

PASS: list[str] = []
FAIL: list[str] = []


def check(name: str, ok: bool, got: str = "") -> None:
    (PASS if ok else FAIL).append(f"{name}  --  {got}")


def load() -> dict[tuple[str, str], dict[int, dict]]:
    out: dict[tuple[str, str], dict[int, dict]] = {}
    files = sorted(glob.glob(str(CACHE / "c2_noise_validation_run_*.json")))
    for f in files:
        j = json.load(io.open(f, encoding="utf-8"))
        for r in j["rows"]:
            out.setdefault((r["condition"], r["model"]), {})[r["run_id"]] = r
    return out


def series(d, cond, model, field="f1_macro") -> np.ndarray:
    """Lay theo THU TU run_id -- ghep cap phai dung tren cung mot run."""
    runs = d[(cond, model)]
    return np.array([runs[i][field] for i in sorted(runs)], dtype=float)


def paired(a: np.ndarray, b: np.ndarray) -> tuple[float, float, float, float, float]:
    """Tra ve (mean, ci_low, ci_high, wilcoxon_p, dz) cua a - b."""
    d = a - b
    m = float(d.mean())
    half = float(stats.t.ppf(0.975, len(d) - 1) * stats.sem(d))
    p = float(stats.wilcoxon(a, b).pvalue)
    dz = m / float(d.std(ddof=1))
    return m, m - half, m + half, p, dz


def write_long_table(d) -> Path:
    """Ghi 60 hang (10 run x 3 dieu kien x 2 model) ra mot bang duy nhat.

    Muoi file cache roi rac thi audit_prose khong doc tien; bang nay la dang
    giong cac file c4_per_run_*.csv ma bo kiem da quen dung.
    """
    import csv
    out = ROOT / "results/nslkdd/c2_revision/c2_noise_validation_10run.csv"
    cols = ["run_id", "condition", "model", "kta",
            "relative_frobenius_distance", "f1_macro"]
    rows = []
    for (cond, model), runs in d.items():
        for rid in sorted(runs):
            r = runs[rid]
            rows.append({c: r.get(c, rid if c == "run_id" else None) for c in cols})
    rows.sort(key=lambda r: (r["run_id"], r["condition"], r["model"]))
    with io.open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return out


def main() -> int:
    d = load()
    out = write_long_table(d)
    print(f"da ghi {out.relative_to(ROOT)}  ({len(d) * 10} hang)")
    print()
    n_runs = {k: len(v) for k, v in d.items()}
    check("du 10 run x 3 dieu kien x 2 model = 60 hang",
          set(n_runs.values()) == {10} and len(n_runs) == 6,
          f"{len(n_runs)} to hop, so run: {sorted(set(n_runs.values()))}")

    print("=" * 78)
    print("  A. TRUNG BINH 10 RUN  (so Quang Anh dua ra o muc 1)")
    print("=" * 78)
    # (dieu kien, model, mean bao cao, std bao cao, kta mean, frob mean)
    claims = [
        ("ideal_statevector",         "QSVM_ZZ", 0.8329, 0.0259, 0.1937, 0.0),
        ("ideal_finite_shot",         "QSVM_ZZ", 0.8363, 0.0197, 0.1917, 0.116),
        ("realistic_noisy_simulator", "QSVM_ZZ", 0.8501, 0.0192, 0.1489, 0.602),
        ("ideal_statevector",         "QSVM_Z",  0.8309, 0.0236, 0.0702, 0.0),
        ("ideal_finite_shot",         "QSVM_Z",  0.8323, 0.0237, 0.0694, 0.037),
        ("realistic_noisy_simulator", "QSVM_Z",  0.8307, 0.0230, 0.0678, 0.165),
    ]
    for cond, model, m_c, s_c, kta_c, fro_c in claims:
        f1 = series(d, cond, model)
        kta = series(d, cond, model, "kta")
        fro = series(d, cond, model, "relative_frobenius_distance")
        print(f"  {model:8s} {cond:26s} F1 {f1.mean():.4f} +- {f1.std(ddof=1):.4f}"
              f"   KTA {kta.mean():.4f}   Frob {fro.mean():.4f}")
        check(f"{model}/{cond}: F1 trung binh",
              abs(f1.mean() - m_c) < 5e-5, f"{f1.mean():.4f} vs {m_c}")
        check(f"{model}/{cond}: F1 do lech",
              abs(f1.std(ddof=1) - s_c) < 5e-5, f"{f1.std(ddof=1):.4f} vs {s_c}")
        check(f"{model}/{cond}: KTA trung binh",
              abs(kta.mean() - kta_c) < 5e-5, f"{kta.mean():.4f} vs {kta_c}")
        check(f"{model}/{cond}: Frobenius trung binh",
              abs(fro.mean() - fro_c) < 5e-4, f"{fro.mean():.4f} vs {fro_c}")

    print()
    print("=" * 78)
    print("  B. SO SANH GHEP CAP  (so o muc 2)")
    print("=" * 78)
    pairs = [
        ("QSVM_ZZ noisy - statevector", "QSVM_ZZ", "realistic_noisy_simulator",
         "ideal_statevector", +0.0172, 0.0021, 0.0324, 0.027, 0.81),
        ("QSVM_ZZ shot  - statevector", "QSVM_ZZ", "ideal_finite_shot",
         "ideal_statevector", +0.0033, -0.0093, 0.0160, 0.846, 0.19),
        ("QSVM_Z  noisy - statevector", "QSVM_Z", "realistic_noisy_simulator",
         "ideal_statevector", -0.0002, -0.0115, 0.0111, 1.000, -0.01),
    ]
    for label, model, ca, cb, m_c, lo_c, hi_c, p_c, dz_c in pairs:
        m, lo, hi, p, dz = paired(series(d, ca, model), series(d, cb, model))
        print(f"  {label:30s} {m:+.4f} [{lo:+.4f}, {hi:+.4f}]  p={p:.3f}  dz={dz:+.2f}")
        check(f"{label}: hieu trung binh", abs(m - m_c) < 5e-5, f"{m:+.4f} vs {m_c:+}")
        check(f"{label}: khoang tin cay",
              abs(lo - lo_c) < 5e-5 and abs(hi - hi_c) < 5e-5,
              f"[{lo:+.4f}, {hi:+.4f}] vs [{lo_c:+}, {hi_c:+}]")
        check(f"{label}: Wilcoxon p", abs(p - p_c) < 1e-3, f"{p:.3f} vs {p_c}")
        check(f"{label}: dz", abs(dz - dz_c) < 6e-3, f"{dz:+.2f} vs {dz_c:+}")

    # Khoang cach entanglement theo tung dieu kien
    print()
    for cond in COND:
        m, lo, hi, p, dz = paired(series(d, cond, "QSVM_ZZ"),
                                  series(d, cond, "QSVM_Z"))
        print(f"  ZZ - Z  {cond:26s} {m:+.4f} [{lo:+.4f}, {hi:+.4f}]  "
              f"p={p:.3f}  dz={dz:+.2f}")
    m, lo, hi, p, dz = paired(series(d, "realistic_noisy_simulator", "QSVM_ZZ"),
                              series(d, "realistic_noisy_simulator", "QSVM_Z"))
    check("ZZ-Z duoi nhieu: +0.0194 [+0.0026, +0.0363], p=0.027",
          abs(m - 0.0194) < 5e-5 and abs(p - 0.027) < 1e-3,
          f"{m:+.4f} [{lo:+.4f}, {hi:+.4f}] p={p:.3f}")

    print()
    print("=" * 78)
    print("  C. HOLM: khong phep so sanh nao song sot")
    print("=" * 78)
    # Chin phep so sanh cua chinh phep kiem nay (3 ZZ + 3 Z + 3 entanglement).
    ps = []
    for model in MODELS:
        for ca, cb in (("ideal_finite_shot", "ideal_statevector"),
                       ("realistic_noisy_simulator", "ideal_statevector"),
                       ("realistic_noisy_simulator", "ideal_finite_shot")):
            ps.append(paired(series(d, ca, model), series(d, cb, model))[3])
    for cond in COND:
        ps.append(paired(series(d, cond, "QSVM_ZZ"), series(d, cond, "QSVM_Z"))[3])
    ps_sorted = sorted(ps)
    holm9 = 0.05 / len(ps)
    print(f"  p nho nhat trong {len(ps)} phep so sanh: {ps_sorted[0]:.4f}")
    print(f"  nguong Holm dau tien (family={len(ps)}): {holm9:.4f}")
    check(f"family={len(ps)}: khong phep nao qua Holm",
          ps_sorted[0] > holm9, f"{ps_sorted[0]:.4f} > {holm9:.4f}")
    # Family hep nhat hop ly: chi "noisy vs statevector" cho hai model.
    p_zz = paired(series(d, "realistic_noisy_simulator", "QSVM_ZZ"),
                  series(d, "ideal_statevector", "QSVM_ZZ"))[3]
    p_z = paired(series(d, "realistic_noisy_simulator", "QSVM_Z"),
                 series(d, "ideal_statevector", "QSVM_Z"))[3]
    holm2 = 0.05 / 2
    print(f"  family=2 (noisy vs statevector moi model): nguong {holm2:.4f}, "
          f"p nho nhat {min(p_zz, p_z):.4f}")
    check("family=2: van khong qua Holm",
          min(p_zz, p_z) > holm2, f"{min(p_zz, p_z):.4f} > {holm2:.4f}")

    print()
    print("=" * 78)
    for m in PASS:
        print("  [PASS] " + m)
    for m in FAIL:
        print("  [LOI ] " + m)
    print("=" * 78)
    print(f"TONG: {len(PASS)}/{len(PASS) + len(FAIL)} PASS")
    print("=" * 78)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
