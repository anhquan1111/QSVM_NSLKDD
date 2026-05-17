"""Sửa diacritics tiếng Việt cho 4 notebook bị thiếu dấu.

Script này thay thế nguyên block ``source`` của các markdown cell theo cell_index
đã xác định trước (không động vào code cell hoặc output).
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------------------------
# 1. notebooks/selectkbest_nslkdd.ipynb (13 markdown cell theo cell_index)
# ------------------------------------------------------------------------------
SELECTKBEST_NSL = {
    0: """# SelectKBest Feature Selection — NSL-KDD

**Bước 1 trong pipeline giảm chiều hai giai đoạn (C1):**
```
Raw features (122) → SelectKBest(f_classif, fit on train ONLY) → K features → PCA đa mục tiêu → QSVM
```

**Input:** `NSL_KDD_Train_Cleaned.csv` / `NSL_KDD_Test_Cleaned.csv` từ `preprocess.ipynb`

| Cột nhãn | Mục đích |
|---|---|
| `label_binary` | Target cho f_classif scoring và CV |
| `attack_category` | Stratified sampling (đảm bảo U2R/R2L có mặt) |
| `label_multiclass` | Giữ lại trong output để dùng cho C4 |

---
**Tại sao f_classif (ANOVA F-test) thay vì Mutual Information:**
- `data_preprocessing.py` (reference) dùng `f_classif` vì sau MinMaxScaler các features là continuous float
- MI với continuous features phụ thuộc `n_neighbors` (hyperparameter nhạy cảm) và chậm hơn ~10x
- `f_classif` đảm bảo **zero-leakage**: chỉ fit trên train, transform test theo mask cố định
- MI category vẫn được tính riêng để **phân tích** rare attacks, không dùng để select

**Zero-leakage contract (theo data_preprocessing.py):**
```
selector.fit_transform(X_train, y_train)  ← F-statistics từ train ONLY
selector.transform(X_test)               ← NEVER fit on test
```""",

    1: "## 0. Import & cấu hình",

    3: "## 1. Load dữ liệu & tách features / nhãn",

    5: """## 2. Tính F-scores (f_classif) — score chính để select

`f_classif` (ANOVA F-test) đo **linear separability** giữa Normal và Attack cho từng feature.
Fit trên **train only** — zero-leakage contract.

MI category vẫn được tính riêng để **phân tích** rare attacks — không dùng để select.""",

    7: "## 3. Trực quan hoá scores",

    9: """## 4. Tìm K tối ưu bằng Cross-Validation

K là **số features đưa vào PCA**, không phải số qubit.

**Tiêu chí — Elbow criterion:**
Chọn K nhỏ nhất mà F1 đã **ổn định trong ngưỡng `PLATEAU_THRESHOLD`** so với F1 tối đa.
K lớn hơn mang thêm features redundant vào PCA, làm giảm chất lượng PCA components.

> SVM linear làm proxy classifier — nhanh hơn QSVM ~1000x, mục đích chỉ là chọn K.""",

    12: """## 5. Fit SelectKBest — zero-leakage contract

```
selector.fit_transform(X_train, y_train)  ← F-statistics từ train ONLY
selector.transform(X_test)               ← NEVER fit on test
```""",

    14: "## 6. Sanity checks — zero-leakage verification",

    16: """## 7. Ma trận tương quan — kiểm tra redundancy

Tương quan cao giữa các features được chọn → PCA compress hiệu quả hơn.""",

    18: """## 8. Ablation Study — Justify C1

So sánh 4 cấu hình để chứng minh pipeline 2 bước (SelectKBest → PCA) là tốt nhất.""",

    20: """## 8b. QSVM Comparison — PCA 4D: Full features vs SelectKBest pipeline

So sánh trực tiếp **3 pipeline** dùng **QSVM thật** (ZZFeatureMap + QSVC)
trên tập nhỏ (train=100, test=50) vì QSVM rất chậm.

| Config | Preprocessing | Classifier |
|---|---|---|
| (A) Full → PCA 4D | PCA(4) trực tiếp từ 122 features | QSVM |
| (B) SKB → PCA 4D | SelectKBest(K_FINAL) → PCA(4) [C1 pipeline] | QSVM |
| (C) Full → SVM (baseline) | Không giảm chiều | SVM linear |

> **Mục đích:** Chứng minh SelectKBest trước PCA giúp QSVM tốt hơn PCA trực tiếp từ full features.""",

    23: "## 9. Lưu tất cả output",

    25: "## 10. Paper-ready summary",
}


# ------------------------------------------------------------------------------
# 2. notebooks/pca.ipynb (20 markdown cell theo cell_index)
# ------------------------------------------------------------------------------
PCA_NSL = {
    0: r"""# PCA Tối ưu hoá Đa Mục tiêu với Ràng buộc Phần cứng Lượng tử (v4)
## Contribution 1: Hardware-aware Quantum Embedding Optimization

**Hàm mục tiêu (trên tập candidates đã lọc):**

$$F(n) = \alpha \cdot V(n) + \beta \cdot S_{\text{norm}}(n) - \gamma \cdot Q(n)$$

**Cải tiến :**

| Bước | Mô tả | Cải tiến |
|------|-------|----------|
| **Input** | Đọc từ `NSL_KDD_Train_Selected.csv` (K features sau SelectKBest) | Khớp pipeline |
| **Scaling** | `MinMaxScaler([0, π])` thay vì `StandardScaler` | Dùng cho QSVM |
| **Zero-leakage** | `pca.fit_transform(X_train)` / `pca.transform(X_test)` | Nhất quán `.py` |
| **Artifact** | Lưu `pca.joblib` + `scaler_minmax_pi.joblib` vào `models/` | Reproducible |
| **Sanity checks** | Kiểm tra shape, range [0, π], NaN sau pipeline | Theo `.py` |

**Zero-leakage contract (theo data_preprocessing.py):**
```
pca.fit_transform(X_train)         ← eigenvectors từ train ONLY
pca.transform(X_test)              ← NEVER fit on test
scaler.fit_transform(X_train_pca)  ← min/max từ train ONLY
scaler.transform(X_test_pca)       ← NEVER fit on test
```""",

    1: "## 0. Cấu hình & Imports",

    3: "## 1. Các hàm tiện ích",

    5: """## 2. Tải dữ liệu

**Input:** `NSL_KDD_Train_Cleaned.csv` và `NSL_KDD_Test_Cleaned.csv` và `feature_selector_k20.joblib` từ `selectkbest_nslkdd.ipynb`

**Scaling:** `MinMaxScaler([0, π])` thay vì `StandardScaler` vì:
- Output cuối cùng phải là rotation angle cho RY gate: `|ψ⟩ = RY(x_i)|0⟩`
- `[0, π]` khai thác toàn bộ Bloch hemisphere, không bị wrap-around
- `data_preprocessing.py` dùng chính xác scale này""",

    7: "## 3. Thu thập chỉ số thô cho toàn bộ N_RANGE",

    9: "## 4. Trực quan hoá ràng buộc cứng",

    11: """## 5. Tìm trọng số tối ưu — Simplex Grid Search

Grid search trên simplex α+β+γ=1 dùng Davies-Bouldin Index (O(k·n), nhanh hơn Silhouette ~100x).
Silhouette chỉ dùng để **validate** kết quả cuối cùng.""",

    13: "## 6. Phân tích landscape trọng số",

    15: "## 7. Tính F(n) và chọn n tối ưu",

    17: "## 8. Validation: Silhouette Score cho n tối ưu (chạy 1 lần)",

    19: "## 9. Bootstrap Confidence Intervals cho F(n) và Silhouette",

    21: "## 10. Pareto Frontier — trên candidates hợp lệ",

    23: "## 11. Trực quan hoá hàm mục tiêu F(n)",

    25: r"""## 12. PCA cuối cùng + MinMaxScaler([0, π]) — zero-leakage

**Bước quan trọng nhất theo data_preprocessing.py:**
```
pca.fit_transform(X_train)        ← eigenvectors từ train ONLY
pca.transform(X_test)             ← NEVER fit on test
scaler.fit_transform(X_train_pca) ← min/max từ train ONLY
np.clip(scaler.transform(X_test_pca), 0, π)  ← clip test OOD values
```

Lý do scale `[0, π]` thay vì `[0, 1]`:
- RY gate: `|ψ⟩ = RY(x_i)|0⟩ = cos(x_i/2)|0⟩ + sin(x_i/2)|1⟩`
- `x_i ∈ [0, π]` khai thác toàn bộ Bloch hemisphere phía trên
- Không bị wrap-around (x > 2π sẽ alias), đảm bảo tính injectivity của embedding""",

    27: "## 13. Sanity checks — zero-leakage verification",

    29: "## 14. Trực quan hoá PCA cuối cùng",

    31: "## 15. Pairplot",

    33: "## 16. Phân tích tương quan — Tiền đề cho ZZFeatureMap",

    35: "## 17. Lưu tất cả output + artifacts",

    37: "## 18. Paper-ready summary",
}


# ------------------------------------------------------------------------------
# 3. notebooks_unsw/selectkbest_unsw.ipynb (10 markdown cell theo cell_index)
# ------------------------------------------------------------------------------
SELECTKBEST_UNSW = {
    0: """# SelectKBest Feature Selection — UNSW-NB15 (Phase 2)

**Bước 2 trong pipeline giảm chiều hai giai đoạn, port từ NSL-KDD sang UNSW-NB15:**

```
Raw 186 features (sau OHE) → SelectKBest(f_classif, fit train ONLY) → K* features → PCA(4D) → QSVM(4-qubit)
```

**Input:** `UNSW_Train_Cleaned.parquet` / `UNSW_Test_Cleaned.parquet` từ Phase 1 (`preprocess.ipynb`).

| Cột nhãn | Mục đích |
|---|---|
| `label_binary` | Target cho `f_classif` scoring và Cross-Validation (0=Normal, 1=Attack) |
| `attack_category` | Stratified sampling — bảo toàn rare classes (Analysis/Backdoor/Shellcode/Worms) |
| `label_multiclass` | Giữ nguyên để chuyển tiếp cho phase C4..C6 (multi-class robustness) |

---

### Điểm khác biệt quan trọng so với NSL-KDD

| Khía cạnh | NSL-KDD | UNSW-NB15 |
|---|---|---|
| Format input | CSV | **Parquet** (~10x nhỏ hơn) |
| Số features sau OHE | 122 | **186** |
| K tối ưu đã biết | 20 (validated empirically) | **CHƯA BIẾT — cần phát hiện động** |
| Rare classes | U2R / R2L | **Analysis / Backdoor / Shellcode / Worms** |
| Class balance (train) | 53% Normal | **32% Normal (attack-skewed)** |

> **Yêu cầu Phase 2:** KHÔNG hardcode K=20. Phải dynamic discovery thông qua F1-macro learning curve (LinearSVC proxy) + Elbow Criterion. K tối ưu của UNSW có thể khác NSL-KDD.

### Zero-leakage contract (BẮT BUỘC)

```
selector.fit_transform(X_train, y_train)   ← F-statistics chỉ từ train
selector.transform(X_test)                 ← KHÔNG BAO GIỜ fit on test
```

`f_classif` (ANOVA F-test) được chọn thay Mutual Information vì:
- Sau `MinMaxScaler` các features là continuous float — F-test phù hợp hơn
- F-test deterministic (không phụ thuộc `n_neighbors`) và nhanh hơn ~10x
- Phù hợp với LinearSVC proxy classifier (F-statistic ~ linear separability)
""",

    1: "## 0. Import & cấu hình",

    3: "## 1. Load dữ liệu (parquet) & tách features / nhãn",

    5: """## 2. Tính F-scores (`f_classif`) — điểm số cho SelectKBest

`f_classif` (ANOVA F-test) đo **linear separability** giữa Normal vs Attack cho mỗi feature.

`SelectKBest(f_classif).fit(X_train, y_train)` chỉ xây dựng F-statistics từ **train**, mask cố định được apply lên test — đảm bảo zero-leakage.
""",

    7: "### 2.1 Trực quan hoá F-score distribution",

    9: """## 3. DYNAMIC K DISCOVERY — Elbow Criterion (KHÔNG hardcode K=20)

### Phương pháp

1. **Subset CV:** Sample stratified `N_CV=5000` mẫu từ train, **giữ rare categories (cap ở 40% subset)** (Analysis/Backdoor/Shellcode/Worms tổng ~5009 mẫu, nếu không cap sẽ loại hết Normal khỏi CV). Không oversample (tránh duplicate giữa folds).

2. **Proxy classifier:** `LinearSVC` (hinge loss, dual='auto') — nhanh hơn QSVM ~1000x và correlate tốt với linear separability mà `f_classif` đo.

3. **Loop trên K candidates:** Với mỗi `K ∈ [5, 10, ..., 150]`, build `Pipeline(SelectKBest(K) → StandardScaler → LinearSVC)` — nội ý là `SelectKBest` nằm **trong** Pipeline nên `fit/transform` được áp dụng đúng trong mỗi fold (KHÔNG leak điểm số từ fold validate).

4. **Cross-validation:** 5-fold StratifiedKFold trên `attack_category` (không phải `label_binary`) — đảm bảo mỗi fold có rare classes cân bằng.

5. **Elbow criterion:** Gọi `f1_max = max(f1_mean)`. Chọn `K_FINAL` là K **nhỏ nhất** thoả `f1_mean(K) ≥ f1_max − PLATEAU_THRESHOLD`. Ý nghĩa: K nhỏ nhất mà F1 đã plateau trong ngưỡng 1% so với best — giảm chiều tối đa mà không hi sinh hiệu năng.
""",

    12: """## 4. Trực quan hoá learning curve — K vs F1-macro

Plot dưới đây là **bằng chứng visual** cho elbow. Hai panel:

- **Trái:** F1-macro mean ± std theo K, với vùng plateau (xanh lá) và K_FINAL (đỏ).
- **Phải:** Marginal gain `dF1/dK` — highlight vị trí elbow nơi gain xuống gần 0.
""",

    14: """## 5. Apply SelectKBest trên full train/test (zero-leakage)

Sau khi có `K_FINAL` từ elbow, fit `SelectKBest(K_FINAL)` lên **toàn bộ** `X_train` (KHÔNG phải subset CV) và apply mask lên cả train và test.

```python
selector.fit_transform(X_train, y_train)   # F-statistics từ X_train ONLY
selector.transform(X_test)                 # chỉ apply mask, KHÔNG fit
```
""",

    16: "## 6. Sanity checks — xác nhận zero-leakage và data integrity",

    18: """## 7. Lưu output — parquet (data) + csv (feature names) + joblib (selector)

Format được giữ nhất quán với Phase 1: **parquet** cho data (~10x nhỏ hơn CSV), **csv** cho metadata text có thể inspect bằng Excel, **joblib** cho sklearn objects.
""",
}


# ------------------------------------------------------------------------------
# 4. notebooks_unsw/pca_unsw.ipynb (9 markdown cell theo cell_index)
# ------------------------------------------------------------------------------
PCA_UNSW = {
    0: r"""# PCA + Quantum Scaling — UNSW-NB15 (Phase 3)

**Bước 3 của pipeline giảm chiều hai giai đoạn:**

```
35 features (sau SelectKBest, Phase 2) → PCA(n=4) → MinMax[0, π] → ZZFeatureMap (4 qubits)
```

**Input:** `UNSW_Train_KBest.parquet` / `UNSW_Test_KBest.parquet` từ Phase 2 (35 features + 3 cột nhãn).

| Cột nhãn | Mục đích tiếp theo |
|---|---|
| `label_binary` | Target chính cho QSVM training và đánh giá (0=Normal, 1=Attack) |
| `attack_category` | Stratified analysis cho rare classes (Analysis/Backdoor/Shellcode/Worms) ở Phase C4..C5 |
| `label_multiclass` | Dự phòng cho multi-class robustness experiments |

---

### Tại sao chính xác n=4 components?

**Hard constraint từ phần cứng NISQ:** Pipeline của dự án này nhắm chạy trên circuit 4-qubit. ZZFeatureMap với 4 qubit yêu cầu **chính xác 4 features** làm input. Số features = số qubit không phải giá trị tối ưu một cách toán học — nó là **ràng buộc phần cứng**.

Phase Pareto multi-objective optimization (`notebooks/pca.ipynb` trên NSL-KDD gốc) đã:
- Khảo sát n ∈ {2, 3, ..., 10}
- Tính **objective function** $F(n) = \alpha \cdot V(n) + \beta \cdot S_{\text{norm}}(n) - \gamma \cdot Q(n)$ trong đó V = explained variance, S = silhouette, Q = qubit cost
- Kết luận: n=4 là điểm cân bằng Pareto-optimal với ràng buộc qubit hardware

UNSW-NB15 kế thừa kết luận này (không lặp lại Pareto search) vì:
- Quy mô qubit phải khớp với NSL-KDD để so sánh fair (cùng phần cứng, cùng mô hình quantum)
- Mục tiêu của Phase 3 này là **transfer pipeline**, không phải re-optimize circuit

### Yêu cầu đặc biệt (Professor's request)

**Spearman correlation analysis** sau scaling: chứng minh PCA chỉ xoá **linear correlation** (Pearson ≈ 0) chứ KHÔNG xoá **monotonic non-linear correlation** (Spearman ≠ 0). Đây chính là "nguyên liệu" mà ZZ-entanglement của QSVM khai thác — bằng chứng toán học cho reviewers.

### Zero-leakage contract (BẮT BUỘC, suốt hết pipeline)

```
pca.fit(X_train_kbest)              ← principal axes chỉ từ train
pca.transform(X_train_kbest)        ← project train
pca.transform(X_test_kbest)         ← KHÔNG fit on test

scaler.fit(X_train_pca)             ← min/max chỉ từ train PCA output
scaler.transform(X_train_pca)       ← map train về [0, π]
scaler.transform(X_test_pca)        ← áp dụng min/max của TRAIN
np.clip(test_scaled, 0, π)          ← bảo vệ nếu test outlier vượt range train
```
""",

    1: "## 0. Cấu hình & Imports",

    3: "## 1. Load dữ liệu (parquet) — 35 features + 3 cột nhãn",

    5: """## 2. PCA (n=4 components) — giảm từ 35D về 4D

**Zero-leakage:** `pca.fit(X_train)` xây dựng `n` principal axes từ covariance của **train only**. Cả train và test sau đó được `pca.transform(...)` sử dụng cùng axes đó.

**Tính chất toán học của PCA:**
- Các principal components là **eigenvectors của covariance matrix**, sắp xếp theo độ lớn eigenvalue (= variance giải thích)
- **Linearly orthogonal:** Pearson(PC_i, PC_j) = 0 với i ≠ j (theorem)
- KHÔNG đảm bảo **monotonic non-linear** decorrelation — đây là chính xác vùng đất mà Spearman sẽ phát hiện ở mục 4
""",

    7: """### 2.1 Scree Plot — explained variance ratio

Scree plot cho thấy **distribution of variance** trên các PCs. Với dữ liệu network traffic đã qua SelectKBest, ta kỳ vọng:
- PC1 chủ yếu bắt **traffic volume / rate** (load, bytes, packets)
- PC2-3 bắt **flow timing & sequence** (rtt, syn-ack, jitter)
- PC4 bắt **state/protocol structure** (state_*, proto_*, service_*)

Tổng variance giữ lại với 4 PCs cho biết **chất lượng giảm chiều** — với 35 features đầu vào, nếu ta giữ được >70% có thể chấp nhận; >85% là rất tốt cho ràng buộc 4-qubit.
""",

    9: r"""## 3. Quantum Scaling — map PCA outputs về $[0, \pi]$

PCA outputs có range KHÔNG bị giới hạn. Với 35 features chuẩn hoá [0, 1] đầu vào, PCA output có thể nằm trong $[-3, +5]$ hoặc bất kỳ miền nào tuỳ thuộc covariance structure. Để **encode chúng vào quantum circuit** thông qua `ZZFeatureMap`, ta phải map về **chính xác $[0, \pi]$**.

### Toán học của ZZFeatureMap (Qiskit, $n_{\text{qubits}}=4$, $\text{reps}=2$, $\text{entanglement}=$ 'full')

ZZFeatureMap encode một vector $\vec{x} = (x_0, x_1, x_2, x_3)$ vào trạng thái lượng tử thông qua:

1. **Hadamard layer:** $H^{\otimes 4}$ — đưa tất cả qubit về superposition $|+\rangle$.
2. **Single-qubit phase:** mỗi qubit $i$ nhận toán tử $P(2 x_i) = e^{-i x_i Z_i}$ (= $R_z(2 x_i)$ tính đến global phase).
3. **Two-qubit ZZ entanglement:** với mỗi cặp $(i, j)$ được entangle:
$$\text{CNOT}_{ij}\;\rightarrow\;P\bigl(2 (\pi - x_i)(\pi - x_j)\bigr)\;\rightarrow\;\text{CNOT}_{ij}$$

### Tại sao $[0, \pi]$ chứ không phải range khác?

| Range x | Phase rotation $2x$ | Tính chất | Phù hợp QSVM |
|---|---|---|---|
| $[-1, 1]$ | $[-2, 2]$ | Chỉ dùng $\sim 2/(2\pi) = 32\%$ chu kỳ rotation | KHÔNG: information loss |
| $[0, 1]$ | $[0, 2]$ | Tương tự, dùng phần bé chu kỳ | KHÔNG: under-utilize state space |
| $\boldsymbol{[0, \pi]}$ | $\boldsymbol{[0, 2\pi]}$ | **Chính xác 1 chu kỳ rotation đầy đủ** | **TỐI ƯU** |
| $[0, 2\pi]$ | $[0, 4\pi]$ | 2 chu kỳ — $x_i = 0$ và $x_i = \pi$ encode cùng trạng thái (collision) | KHÔNG: ambiguity |

Với $x_i \in [0, \pi]$, single-qubit phase rotation $2 x_i \in [0, 2\pi]$ đi hết **đúng 1 chu kỳ** — mỗi giá trị PCA tương ứng 1 vị trí duy nhất trên $S^1$ (vòng tròn Bloch).

Two-qubit entanglement angle $2(\pi - x_i)(\pi - x_j) \in [0, 2\pi^2] \approx [0, 19.7]$ tạo **landscape phi tuyến phong phú** — nguồn gốc của quantum kernel advantage so với RBF.

### Zero-leakage trong scaling

```
scaler.fit(X_train_pca)            ← min/max chỉ từ TRAIN
scaler.transform(X_train_pca)      ← map train về [0, π]
scaler.transform(X_test_pca)       ← áp dụng min/max của TRAIN lên test
np.clip(test_scaled, 0, π)         ← defensive: clip nếu test outlier vượt range train
```
""",

    11: r"""## 4. Spearman Correlation Analysis (yêu cầu khoa học của giáo sư)

### Tại sao Spearman, KHÔNG phải Pearson?

PCA đảm bảo **decorrelation tuyến tính** (theorem PCA orthogonality):
$$\rho_{\text{Pearson}}(\text{PC}_i, \text{PC}_j) = 0\quad \forall i \ne j$$

Tuy nhiên, nếu **mối quan hệ giữa các PCs có dạng phi tuyến monotonic** (sigmoidal, exponential, rank-preserving but non-linear), Pearson **bỏ qua** chúng. Spearman bắt được những relationship này vì:
$$\rho_{\text{Spearman}}(X, Y) = \rho_{\text{Pearson}}\bigl(\text{rank}(X),\;\text{rank}(Y)\bigr)$$

Nguyên tắc:
- $\rho_{\text{Pearson}} \approx 0$ và $\rho_{\text{Spearman}} \ne 0$ $\Rightarrow$ tồn tại **non-linear monotonic structure** mà PCA không xoá được.
- Đây chính là **vùng đất mà QSVM ZZ-entanglement khai thác**, trong khi linear classifier và Pearson-based feature engineering bỏ lỡ.

### Ý nghĩa với QSVM và paper

`ZZFeatureMap` two-qubit angle $2(\pi - x_i)(\pi - x_j)$ chứa **product term $x_i \cdot x_j$** (sau khi khai triển) — chính xác là **bilinear cross-feature** structure cần để capture monotonic non-linear correlation. Nếu Spearman matrix gần diagonal (no off-diagonal), QSVM sẽ không có lợi thế rõ rệt. Ngược lại, Spearman off-diagonal ≠ 0 chính là **bằng chứng quantitative cho reviewers**: pipeline của chúng ta có "nguyên liệu" cho quantum advantage.

### Tính chất toán học: MinMax invariance

`MinMaxScaler` là **monotonic affine transformation** per-column ($x \mapsto a x + b$ với $a > 0$). Spearman **bất biến** với monotonic transformations theo định nghĩa (đo trên ranks):
$$\rho_{\text{Spearman}}(\text{PCA}) \equiv \rho_{\text{Spearman}}(\text{MinMax}(\text{PCA}))$$

Ta tính trên `X_train_scaled` vì đó là **đầu vào thực tế** của QSVM, nhưng giá trị sẽ identical nếu tính trên raw PCA — **bằng chứng phụ** rằng scaling không tạo ra correlation giả.
""",

    13: "## 5. Sanity checks — xác nhận zero-leakage và tính đúng đắn của scaling",

    15: """## 6. Lưu output

| Loại | Format | Path | Mục đích |
|---|---|---|---|
| Reduced data (4D scaled) | parquet | `data/unsw_nb15/processed_data/UNSW_*_PCA4D.parquet` | Input cho QSVM training |
| PCA model | joblib | `models_unsw/pca_4components.joblib` | Re-apply transform trên data mới |
| MinMax scaler | joblib | `models_unsw/scaler_minmax_pi.joblib` | Re-apply scaling trên data mới |
| Scree plot | PNG | `reports_unsw/unsw_pca_scree_plot.png` | Paper figure |
| Spearman heatmap | PNG | `reports_unsw/unsw_pca_spearman_heatmap.png` | Paper figure (Professor's request) |""",
}


# ------------------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------------------
def apply_replacements(nb_path: Path, replacements: dict[int, str]) -> None:
    """Cập nhật markdown cells theo cell_index."""
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    cells = nb["cells"]
    applied = 0
    for idx, new_src in replacements.items():
        if idx >= len(cells):
            print(f"  [SKIP] cell_index {idx} ngoài range (notebook chỉ có {len(cells)} cell)")
            continue
        cell = cells[idx]
        if cell.get("cell_type") != "markdown":
            print(f"  [SKIP] cell[{idx}] không phải markdown (là {cell.get('cell_type')})")
            continue
        # Lưu source dạng list of lines giữ trailing newline cho mỗi dòng trừ dòng cuối
        lines = new_src.splitlines(keepends=True)
        # nbformat thường lưu mỗi entry không có trailing \n ở dòng cuối
        if lines and not lines[-1].endswith("\n"):
            pass
        cell["source"] = lines
        applied += 1

    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"  Đã cập nhật {applied}/{len(replacements)} cell trong {nb_path.relative_to(ROOT)}")


def main():
    targets = [
        (ROOT / "notebooks" / "selectkbest_nslkdd.ipynb", SELECTKBEST_NSL),
        (ROOT / "notebooks" / "pca.ipynb", PCA_NSL),
        (ROOT / "notebooks_unsw" / "selectkbest_unsw.ipynb", SELECTKBEST_UNSW),
        (ROOT / "notebooks_unsw" / "pca_unsw.ipynb", PCA_UNSW),
    ]
    for path, repl in targets:
        print(f"\n=== {path.name} ===")
        if not path.exists():
            print(f"  [ERROR] File không tồn tại: {path}")
            continue
        apply_replacements(path, repl)
    print("\nXong.")


if __name__ == "__main__":
    main()
