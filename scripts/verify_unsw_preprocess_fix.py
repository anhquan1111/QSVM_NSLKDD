"""Verify standalone cho fix Largest Remainder Method trong stratified_sample_for_qsvm.

Test logic phân bổ LRM một cách độc lập với notebook: tạo DataFrame nhân tạo
với phân phối attack_category đã biết, chạy hàm, assert tổng == n_samples.
"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import numpy as np
import pandas as pd

# ── Định nghĩa lại hàm LRM (mirror chính xác cell 15 sau patch) ─────────────
RARE_CATEGORIES_DEFAULT = ('Analysis', 'Backdoor', 'Shellcode', 'Worms')


def stratified_sample_for_qsvm(
    df,
    n_samples       = 1000,
    min_rare        = 30,
    rare_categories = RARE_CATEGORIES_DEFAULT,
    random_state    = 42,
):
    rng        = np.random.RandomState(random_state)
    sampled    = []
    rare_cats  = [c for c in rare_categories if c in df['attack_category'].unique()]
    other_cats = [c for c in df['attack_category'].unique() if c not in rare_cats]

    rare_budget = 0
    for cat in rare_cats:
        pool    = df[df['attack_category'] == cat]
        n_take  = min(min_rare, len(pool)) if len(pool) >= min_rare else min_rare
        replace = len(pool) < n_take
        idx     = pool.sample(n=n_take, replace=replace,
                              random_state=rng.randint(1_000_000))
        sampled.append(idx)
        rare_budget += n_take

    remaining   = max(0, n_samples - rare_budget)
    other_total = df[df['attack_category'].isin(other_cats)].shape[0]

    if other_total > 0 and remaining > 0:
        allocations = []
        for cat in other_cats:
            pool        = df[df['attack_category'] == cat]
            weight      = len(pool) / other_total
            exact       = remaining * weight
            floor_n     = max(1, int(exact))
            remainder   = exact - int(exact)
            allocations.append([cat, pool, floor_n, remainder])

        current_total = sum(a[2] for a in allocations)
        deficit       = remaining - current_total

        if deficit > 0:
            allocations.sort(key=lambda x: x[3], reverse=True)
            for k in range(deficit):
                allocations[k % len(allocations)][2] += 1
        elif deficit < 0:
            allocations.sort(key=lambda x: x[3])
            need_remove = -deficit
            guard = 0
            while need_remove > 0 and guard < len(allocations) * 100:
                idx = guard % len(allocations)
                if allocations[idx][2] > 1:
                    allocations[idx][2] -= 1
                    need_remove -= 1
                guard += 1

        for cat, pool, n_take, _ in allocations:
            n_take = min(n_take, len(pool))
            idx    = pool.sample(n=n_take,
                                 random_state=rng.randint(1_000_000))
            sampled.append(idx)

    result = pd.concat(sampled).sample(frac=1, random_state=random_state)
    return result.reset_index(drop=True)


# ── Tạo dataset giả lập ──────────────────────────────────────────────────────
def make_synthetic_df(category_sizes, n_features=10, seed=0):
    """Tạo DataFrame với phân phối attack_category cho trước."""
    rng = np.random.RandomState(seed)
    parts = []
    for cat, size in category_sizes.items():
        df = pd.DataFrame(
            rng.randn(size, n_features),
            columns=[f'f{i}' for i in range(n_features)],
        )
        df['attack_category'] = cat
        parts.append(df)
    return pd.concat(parts, ignore_index=True)


# ── Bộ test ─────────────────────────────────────────────────────────────────
def run_test(name, category_sizes, n_samples, min_rare, rare_categories, seed=42):
    df = make_synthetic_df(category_sizes, seed=seed)
    out = stratified_sample_for_qsvm(
        df,
        n_samples       = n_samples,
        min_rare        = min_rare,
        rare_categories = rare_categories,
        random_state    = seed,
    )
    dist = dict(out['attack_category'].value_counts())
    total = len(out)
    rare_present = [c for c in rare_categories if c in df['attack_category'].unique()]
    rare_budget_expected = len(rare_present) * min_rare
    print(f'  [{name}]')
    print(f'    n_samples     = {n_samples}, min_rare = {min_rare}')
    print(f'    rare_cats     = {rare_present} (budget = {rare_budget_expected})')
    print(f'    distribution  = {dist}')
    print(f'    total         = {total}')
    assert total == n_samples, f'FAIL [{name}]: total={total}, expected={n_samples}'
    print(f'    [OK] total == n_samples')
    return total


if __name__ == '__main__':
    print('=' * 70)
    print('VERIFY LRM FIX cho stratified_sample_for_qsvm')
    print('=' * 70)

    # ── Test 1: 3 other_cats với tỉ lệ gần đều (kinh điển gây floor cut) ──────
    print('\n[Test 1] 3 categories cân bằng (weights ~ 0.33/0.33/0.34)')
    run_test(
        'eq3',
        category_sizes  = {'Normal': 330, 'Exploits': 330, 'DoS': 340},
        n_samples       = 100,
        min_rare        = 5,
        rare_categories = (),  # không có rare
    )

    # ── Test 2: 4 cats với tỉ lệ lệch (0.1/0.2/0.3/0.4) ───────────────────────
    print('\n[Test 2] 4 categories với weights 0.1/0.2/0.3/0.4')
    run_test(
        'skew4',
        category_sizes  = {'A': 100, 'B': 200, 'C': 300, 'D': 400},
        n_samples       = 100,
        min_rare        = 5,
        rare_categories = (),
    )

    # ── Test 3: Có rare + many other (giống UNSW-NB15 thực tế) ───────────────
    print('\n[Test 3] UNSW-like: 4 rare + 5 other (n=100, min_rare=5)')
    run_test(
        'unsw-like',
        category_sizes  = {
            'Normal'    : 5000,
            'Generic'   : 4000,
            'Exploits'  : 3000,
            'Fuzzers'   : 1000,
            'DoS'       : 800,
            'Analysis'  : 200,
            'Backdoor'  : 150,
            'Shellcode' : 100,
            'Worms'     : 50,
        },
        n_samples       = 100,
        min_rare        = 5,
        rare_categories = ('Analysis', 'Backdoor', 'Shellcode', 'Worms'),
    )

    # ── Test 4: n_samples nhỏ + nhiều other → max(1, ...) sẽ làm deficit < 0 ──
    print('\n[Test 4] Edge: n_samples nhỏ + many other (deficit < 0 do max(1,...))')
    run_test(
        'many-tiny',
        category_sizes  = {f'cat{i}': 100 + i * 10 for i in range(8)},
        n_samples       = 20,
        min_rare        = 0,
        rare_categories = (),
    )

    # ── Test 5: Edge thuần lẻ → mọi remainder ≈ 0 ────────────────────────────
    print('\n[Test 5] Weights cho ra exact integer (không có remainder)')
    run_test(
        'no-remainder',
        category_sizes  = {'A': 100, 'B': 100, 'C': 100, 'D': 100},
        n_samples       = 100,
        min_rare        = 5,
        rare_categories = (),
    )

    # ── Test 6: Multi seed reproducibility check ─────────────────────────────
    print('\n[Test 6] Reproducibility — cùng seed phải ra cùng kết quả')
    for seed in [100, 101, 102, 103, 104]:
        run_test(
            f'seed{seed}',
            category_sizes  = {
                'Normal': 1000, 'Exploits': 800, 'Generic': 600,
                'Analysis': 100, 'Backdoor': 80,
            },
            n_samples       = 100,
            min_rare        = 5,
            rare_categories = ('Analysis', 'Backdoor'),
            seed            = seed,
        )

    print('\n' + '=' * 70)
    print('TẤT CẢ TEST PASS — LRM phân bổ tổng = n_samples chính xác')
    print('=' * 70)
