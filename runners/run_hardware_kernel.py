"""Tinh nhan luong tu tren PHAN CUNG THAT va doi chieu voi mo phong.

Muc dich. R3 liet ke "a hardware implementation" la mot trong nam thu tao nen
dong gop, va che rang "the framing as NISQ-aware is curious because all
experiments are purely done in (ideal) simulations". Script nay dua ra ba muc
tren cung mot tap con va cung mot mach:

    ideal statevector  ->  FakeManilaV2 (nhieu dung tu backend)  ->  QPU that

roi bao cao do tuong dong Frobenius va KTA giua chung.

Chi phi QPU. Nhan fidelity phai chay compute-uncompute cho TUNG CAP mau, nen so
mach tang bac hai: m mau -> m(m-1)/2 mach cho Gram train. Script in ro du toan
truoc khi gui, va KHONG gui neu vuot `--max-circuits`.

Chay thu khong can tai khoan (chi ideal + FakeManila):
    python runners/run_hardware_kernel.py --dry-run

Chay that (can token IBM Quantum da luu):
    python runners/run_hardware_kernel.py --subset 40 --shots 1024
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "runners")]

N_QUBITS = 4
REPS = 2
SELECT_K = 20
SEED = 42


def build_angles(subset: int):
    """Tap con phan tang + goc nhap lieu, dung dung giao thuc C1."""
    import c4_pipeline as c4
    from config import LABEL_COLS
    from sklearn.model_selection import train_test_split

    spec = c4.get_spec("nslkdd")
    df = c4.read_table(ROOT / spec.processed_dir / spec.train_file)
    fc = [c for c in df.columns if c not in LABEL_COLS]
    rep = c4.make_representation("refit_per_N", select_k=SELECT_K,
                                 n_components=N_QUBITS).fit(df, fc)
    idx, _ = train_test_split(np.arange(len(df)), train_size=subset,
                              stratify=df["attack_category"].to_numpy(),
                              random_state=SEED)
    idx = np.sort(idx)
    sub = df.iloc[idx]
    ang, _ = rep.transform(sub, fc)
    y = sub["label_binary"].to_numpy()
    del df
    return ang, y


def kta(gram: np.ndarray, y: np.ndarray) -> float:
    y_pm = np.where(y == 0, -1.0, 1.0)
    yy = np.outer(y_pm, y_pm)
    den = np.linalg.norm(gram, "fro") * np.linalg.norm(yy, "fro")
    return float((gram * yy).sum() / den) if den > 0 else 0.0


def frobenius_similarity(a: np.ndarray, b: np.ndarray) -> float:
    den = np.linalg.norm(a, "fro") * np.linalg.norm(b, "fro")
    return float((a * b).sum() / den) if den > 0 else 0.0


def pair_circuits(ang: np.ndarray):
    """Mach compute-uncompute cho tung cap: U(x_j)^dagger U(x_i) |0>."""
    from qiskit.circuit.library import ZZFeatureMap

    fm = ZZFeatureMap(N_QUBITS, reps=REPS, entanglement="full")
    circuits, pairs = [], []
    for i in range(len(ang)):
        for j in range(i + 1, len(ang)):
            c = (fm.assign_parameters(ang[i])
                 .compose(fm.assign_parameters(ang[j]).inverse()))
            c.measure_all()
            circuits.append(c)
            pairs.append((i, j))
    return circuits, pairs


def gram_from_counts(probs, pairs, m: int) -> np.ndarray:
    """Gram doi xung, duong cheo bang 1 theo dinh nghia fidelity."""
    g = np.eye(m)
    for (i, j), p in zip(pairs, probs):
        g[i, j] = g[j, i] = p
    return g


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subset", type=int, default=40,
                    help="So mau. So mach = m(m-1)/2, tang bac hai.")
    ap.add_argument("--shots", type=int, default=1024)
    ap.add_argument("--max-circuits", type=int, default=5000,
                    help="Chan an toan: khong gui neu vuot nguong nay.")
    ap.add_argument("--backend", default=None,
                    help="Ten backend that. Bo trong = de he thong chon may it ban nhat.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Chi chay ideal + FakeManila, khong dung QPU.")
    args = ap.parse_args()

    import c4_pipeline as c4

    out = ROOT / "results" / "nslkdd" / "c2_revision"
    out.mkdir(parents=True, exist_ok=True)

    ang, y = build_angles(args.subset)
    m = len(ang)
    circuits, pairs = pair_circuits(ang)
    print(f"Tap con: {m} mau, {N_QUBITS} qubit, r={REPS}")
    print(f"So mach compute-uncompute: {len(circuits):,}  "
          f"({m}*{m - 1}/2)")
    print(f"Shots moi mach: {args.shots:,}  "
          f"-> tong {len(circuits) * args.shots:,} lan do")
    if len(circuits) > args.max_circuits:
        print(f"\n!! DUNG: {len(circuits):,} mach vuot nguong "
              f"{args.max_circuits:,}. Giam --subset hoac nang --max-circuits.")
        return 2

    # --- (1) ideal statevector: tham chieu dung ---
    g_ideal = c4.gram_from_statevectors(
        c4.compute_statevectors_fast(ang, "ZZ", N_QUBITS, REPS))
    rows = [{"condition": "ideal_statevector", "backend": "-", "shots": "statevector",
             "kta": kta(g_ideal, y), "frobenius_vs_ideal": 1.0,
             "mean_abs_err_vs_ideal": 0.0, "seconds": 0.0}]
    print(f"\n[1/3] ideal statevector       KTA = {rows[0]['kta']:.4f}")

    # --- (2) FakeManilaV2: nhieu dung tu du lieu hieu chuan cua backend that ---
    from qiskit import transpile
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2

    fake = FakeManilaV2()
    t0 = time.time()
    tqc = transpile(circuits, backend=fake, optimization_level=1,
                    seed_transpiler=SEED)
    sim = AerSimulator(noise_model=NoiseModel.from_backend(fake))
    res = sim.run(tqc, shots=args.shots, seed_simulator=SEED).result()
    zero = "0" * N_QUBITS
    p_fake = [res.get_counts(k).get(zero, 0) / args.shots for k in range(len(tqc))]
    g_fake = gram_from_counts(p_fake, pairs, m)
    rows.append({"condition": "fake_manila_noisy", "backend": fake.name,
                 "shots": args.shots, "kta": kta(g_fake, y),
                 "frobenius_vs_ideal": frobenius_similarity(g_fake, g_ideal),
                 "mean_abs_err_vs_ideal": float(np.abs(g_fake - g_ideal).mean()),
                 "seconds": time.time() - t0})
    print(f"[2/3] FakeManilaV2 (nhieu)    KTA = {rows[-1]['kta']:.4f}  "
          f"FroSim = {rows[-1]['frobenius_vs_ideal']:.4f}  "
          f"MAE = {rows[-1]['mean_abs_err_vs_ideal']:.4f}")
    print(f"      transpile: depth {max(c.depth() for c in tqc)}, "
          f"CNOT {max(dict(c.count_ops()).get('cx', 0) for c in tqc)}")

    # --- (3) QPU that ---
    if args.dry_run:
        print("\n[3/3] BO QUA phan cung (--dry-run).")
    else:
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
        service = QiskitRuntimeService()
        backend = (service.backend(args.backend) if args.backend
                   else service.least_busy(operational=True, simulator=False,
                                           min_num_qubits=N_QUBITS))
        print(f"\n[3/3] Backend that: {backend.name} "
              f"({backend.num_qubits} qubit)")
        t0 = time.time()
        tqc_hw = transpile(circuits, backend=backend, optimization_level=1,
                           seed_transpiler=SEED)
        job = SamplerV2(mode=backend).run(tqc_hw, shots=args.shots)
        print(f"      job id: {job.job_id()} -- dang cho...")
        result = job.result()
        p_hw = []
        for k in range(len(tqc_hw)):
            counts = result[k].data.meas.get_counts()
            p_hw.append(counts.get(zero, 0) / args.shots)
        g_hw = gram_from_counts(p_hw, pairs, m)
        rows.append({"condition": "real_hardware", "backend": backend.name,
                     "shots": args.shots, "kta": kta(g_hw, y),
                     "frobenius_vs_ideal": frobenius_similarity(g_hw, g_ideal),
                     "mean_abs_err_vs_ideal": float(np.abs(g_hw - g_ideal).mean()),
                     "seconds": time.time() - t0, "job_id": job.job_id()})
        print(f"      KTA = {rows[-1]['kta']:.4f}  "
              f"FroSim = {rows[-1]['frobenius_vs_ideal']:.4f}  "
              f"MAE = {rows[-1]['mean_abs_err_vs_ideal']:.4f}")
        np.save(out / "c2_hardware_gram.npy", g_hw)

    df = pd.DataFrame(rows)
    suffix = "_dryrun" if args.dry_run else ""
    df.to_csv(out / f"c2_hardware_validation{suffix}.csv", index=False)
    (out / f"c2_hardware_config{suffix}.json").write_text(json.dumps({
        "subset": m, "n_qubits": N_QUBITS, "reps": REPS, "select_k": SELECT_K,
        "shots": args.shots, "n_circuits": len(circuits), "seed": SEED,
        "dry_run": args.dry_run,
    }, indent=2), encoding="utf-8")
    print(f"\nDa ghi c2_hardware_validation{suffix}.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
