"""Kiem khai trien bac hai cua nhan ZZ -- Lemma 1.

Ban da nop (Proposition 2) khang dinh

    K(x,x') = 1 - r^2 sum_i D_i^2 - r^2 sum_{i<j} Dphi_ij^2 + O(||D||^4).

Cong thuc do SAI. Script nay chung minh bang so ca hai dieu:

  (A) Voi r=1 cong thuc DUNG phai la
          K = 1 - sum_i D_i^2 - (1/4) sum_{i<j} Dphi_ij^2 + O(||D||^4)
      -- he so 1 va 1/4, khong phai r^2 va r^2. Bac sai so do duoc ~ 4.

  (B) Voi r>=2 -- ke ca r=2 la diem lam viec cua bai -- KHONG co cap he so
      nao lam cho dang hai so hang do dung: khop binh phuong toi thieu chi dat
      R^2 ~ 0.6-0.94 va he so khop khong on dinh theo diem goc. Ly do: cac lop
      Hadamard xen giua lam U(x')^dag U(x) khong con cheo.

Vi sao he so la 1 va 1/4: P(2x) = pha toan cuc * exp(-i x Z) nen so hang don
mang he so x chu khong phai 2x; con bo ba CNOT-RZ(phi)-CNOT = exp(-i phi/2 ZZ)
nen so hang cap mang he so phi/2. Voi |+> = H^{on}|0>, cac ham s_i va s_i s_j
truc chuan duoi phan bo deu tren {-1,+1}^n, nen E[theta]=0 va
K = |E[e^{i theta}]|^2 = 1 - Var(theta) + O(||D||^4).

    python runners/verify_lemma1.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.c4_pipeline import (compute_statevectors_fast,  # noqa: E402
                             gram_from_statevectors, verify_kernel_equivalence)

OK = FAILED = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global OK, FAILED
    if cond:
        OK += 1
        print(f"  [PASS] {name}" + (f"  --  {detail}" if detail else ""))
    else:
        FAILED += 1
        print(f"  [FAIL] {name}  --  {detail}")


def k_exact(x: np.ndarray, xp: np.ndarray, n_q: int, reps: int) -> float:
    psi = compute_statevectors_fast(np.vstack([x, xp]), "ZZ", n_q, reps)
    return float(gram_from_statevectors(psi)[0, 1])


def invariants(x: np.ndarray, xp: np.ndarray, n_q: int) -> tuple[float, float]:
    """Hai bat bien ma Lemma dung: sum D_i^2 va sum Dphi_ij^2."""
    d = x - xp
    lin = float(np.sum(d ** 2))
    pair = 0.0
    for i in range(n_q):
        for j in range(i + 1, n_q):
            pair += (2 * (np.pi - x[i]) * (np.pi - x[j])
                     - 2 * (np.pi - xp[i]) * (np.pi - xp[j])) ** 2
    return lin, float(pair)


def k_corrected(x: np.ndarray, xp: np.ndarray, n_q: int) -> float:
    lin, pair = invariants(x, xp, n_q)
    return 1 - lin - 0.25 * pair


def k_submitted(x: np.ndarray, xp: np.ndarray, n_q: int, reps: int) -> float:
    lin, pair = invariants(x, xp, n_q)
    return 1 - reps ** 2 * lin - reps ** 2 * pair


def fit_two_term(base: np.ndarray, n_q: int, reps: int, rng, eps: float = 1e-3):
    """Khop `1-K = a*lin + b*pair` tren nhieu huong quanh mot diem goc."""
    A, y = [], []
    for _ in range(200):
        u = rng.normal(size=n_q)
        u /= np.linalg.norm(u)
        xp = base + eps * u
        lin, pair = invariants(base, xp, n_q)
        A.append([lin, pair])
        y.append(1 - k_exact(base, xp, n_q, reps))
    A, y = np.array(A), np.array(y)
    c, *_ = np.linalg.lstsq(A, y, rcond=None)
    r2 = 1 - np.sum((y - A @ c) ** 2) / np.sum((y - y.mean()) ** 2)
    return c, float(r2)


def order_of_error(base, n_q, reps, rng, formula) -> tuple[float, float]:
    eps_list = [1e-1, 3e-2, 1e-2, 3e-3, 1e-3]
    errs = []
    for eps in eps_list:
        u = rng.normal(size=n_q)
        u /= np.linalg.norm(u)
        xp = base + eps * u
        errs.append(abs(k_exact(base, xp, n_q, reps) - formula(base, xp)))
    slope = float(np.polyfit(np.log(eps_list), np.log(errs), 1)[0])
    return slope, errs[-1]


def main() -> int:
    print("=" * 78)
    print("  KIEM LEMMA 1 -- khai trien bac hai cua nhan ZZ")
    print("=" * 78)

    rng = np.random.default_rng(2026)

    print("\n0. Nhan dung phai khop Qiskit truoc da")
    for n_q in (4, 6):
        res = verify_kernel_equivalence(rng.uniform(0, np.pi, size=(10, n_q)),
                                        kernel="ZZ", n_qubits=n_q, reps=2)
        check(f"nhan n={n_q} khop Qiskit", bool(res["passed"]),
              f"lech lon nhat {res['max_abs_diff']:.2e}")

    print("\nA. r=1 -- cong thuc SUA LAI (he so 1 va 1/4)")
    for n_q in (3, 4, 6):
        base = rng.uniform(0.4, np.pi - 0.4, n_q)
        c, r2 = fit_two_term(base, n_q, 1, rng)
        check(f"n={n_q}: he so khop ra dung (1, 1/4)",
              abs(c[0] - 1.0) < 1e-3 and abs(c[1] - 0.25) < 1e-3,
              f"a={c[0]:.4f}, b={c[1]:.4f}, R^2={r2:.6f}")
        slope, err = order_of_error(base, n_q, 1, rng,
                                    lambda a, b, n=n_q: k_corrected(a, b, n))
        check(f"n={n_q}: sai so giam bac 4", 3.5 < slope < 4.6,
              f"bac={slope:.2f}, sai so tai eps=1e-3 la {err:.1e}")

    print("\nB. r=1 -- cong thuc CUA BAN DA NOP (he so r^2, r^2)")
    for n_q in (3, 4, 6):
        base = rng.uniform(0.4, np.pi - 0.4, n_q)
        slope, err = order_of_error(base, n_q, 1, rng,
                                    lambda a, b, n=n_q: k_submitted(a, b, n, 1))
        check(f"n={n_q}: cong thuc cu KHONG dat bac 4", slope < 3.0,
              f"bac={slope:.2f} (chi bac hai -> he so bac hai sai)")

    print("\nC. r=2 -- diem lam viec cua bai: khong cap he so nao cuu duoc")
    for n_q, seed in ((4, 1), (4, 2), (6, 3)):
        g = np.random.default_rng(seed)
        base = g.uniform(0.4, np.pi - 0.4, n_q)
        c, r2 = fit_two_term(base, n_q, 2, g)
        check(f"n={n_q} seed={seed}: dang hai so hang khong khop", r2 < 0.99,
              f"R^2={r2:.4f} voi he so tot nhat a={c[0]:.3f}, b={c[1]:.3f}")

    print("\nD. r=2 -- nhung van la mot dang toan phuong day du cua d")
    g = np.random.default_rng(5)
    n_q = 4
    base = g.uniform(0.4, np.pi - 0.4, n_q)
    eps = 1e-3
    B, y = [], []
    for _ in range(400):
        u = g.normal(size=n_q)
        u /= np.linalg.norm(u)
        xp = base + eps * u
        d = (base - xp) / eps
        B.append([d[i] * d[j] * (1 if i == j else 2)
                  for i in range(n_q) for j in range(i, n_q)])
        y.append((1 - k_exact(base, xp, n_q, 2)) / eps ** 2)
    B, y = np.array(B), np.array(y)
    c, *_ = np.linalg.lstsq(B, y, rcond=None)
    r2 = 1 - np.sum((y - B @ c) ** 2) / np.sum((y - y.mean()) ** 2)
    check("dang toan phuong day du khop gan hoan hao", r2 > 0.999,
          f"R^2={r2:.6f} -- nen o r=2 van la metric bac hai, chi la khong "
          f"rut gon ve hai bat bien do")

    print("\n" + "=" * 78)
    print(f"TONG: {OK}/{OK + FAILED} PASS" + (f"  ({FAILED} FAIL)" if FAILED else ""))
    print("=" * 78)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
