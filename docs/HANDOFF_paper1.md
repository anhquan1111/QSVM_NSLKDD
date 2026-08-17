# HANDOFF — Ngữ cảnh dự án & Hoàn thiện Paper 1

> File bàn giao để tiếp tục ở phiên chat/AI khác. Gồm: **prompt dán sẵn**, tình hình,
> quyết định đã chốt, và việc cần làm cho Paper 1.

---

## 📋 PROMPT DÁN SẴN (copy nguyên khối này vào AI mới)

```
Tôi đang làm dự án nghiên cứu QSVM cho phát hiện xâm nhập mạng (repo: github.com/anhquan1111/QSVM_NSLKDD, PUBLIC).
Có 2 bài báo:
- Paper 1 (IEEE TETC, mã TETC-2026-05-0252): "NISQ-Aware Quantum Kernel SVM ... Regime-Specific Benchmark on NSL-KDD" — đang MAJOR REVISION, hạn 13-Oct-2026, KHÔNG có vòng 2.
- Paper 2 (đã nộp IJNM/Wiley Q2): bản reliability/calibration (companion).

Tôi (Vo Tran Anh Vo / Quan) là chủ nhiệm đề tài, corresponding author cả 2 bài.
Mục tiêu phiên này: (1) hiểu rõ lại toàn bộ code & phương pháp; (2) hoàn thiện Paper 1 theo yêu cầu reviewer.

Hãy đọc theo thứ tự: docs/HANDOFF_paper1.md (file này) → AGENTS.md → docs/PAPER1_overview.md →
docs/paper1_revision_plan.md → docs/PAPER2_overview.md. Rồi giúp tôi làm Paper 1.
Ràng buộc: giữ bản sắc bài (4-qubit NISQ, low-data, Pareto PCA = đóng góp C1); không phá lõi để chạy theo mọi gợi ý reviewer.
Code: định danh tiếng Anh (PEP 8), comment/markdown tiếng Việt, open() luôn encoding='utf-8'. Dùng uv (uv sync / uv run).
```

---

## 1. Dự án là gì (30 giây)
QSVM (Quantum SVM, ZZFeatureMap, 4 qubit) cho IDS trên NSL-KDD (+ UNSW-NB15 cross-check).
Pipeline: `NSL-KDD → OHE 122D → SelectKBest 20D → PCA 4D → MinMax[0,π] → QSVM`.
Luận điểm: **regime-specific** — QSVM không thắng mọi lúc, mà thắng ở **đúng chế độ** (low-data, tấn công hiếm).
Chi tiết cấu trúc & guidelines: **AGENTS.md**.

## 2. Hai bài báo
| | Paper 1 (TETC) | Paper 2 (IJNM) |
|---|---|---|
| Trục | Hiệu năng/regime (F1, KTA) | Độ tin cậy/calibration (ECE, Brier) |
| Baseline | SVM cổ điển | + RandomForest, XGBoost |
| Trạng thái | **Major revision** (hạn 13-Oct-2026) | Đã nộp, under review |
| Thứ tự tác giả | Pham → Do → Hung Van → Quang Anh → **Quan (cuối, corres)** | Hung Van → **Quan (#2, corres+submit)** → Quang Anh → Pham |
| Doc | PAPER1_overview.md + paper1_revision_plan.md | PAPER2_overview.md |

## 3. PAPER 1 — việc cần làm (nhiệm vụ chính)
Chi tiết checklist: **docs/paper1_revision_plan.md**. Tóm tắt:

**🚨 Ưu tiên 1 — Liêm chính:**
- Audit toàn bộ references (≤45). **[26] Rahman nghi BỊA**; **[15]** sai số bài (116990F→116990B); AE nói còn refs không tồn tại.
- **Theorem 1 SAI** (viết F̃(4)>F̃(3) nhưng Bảng III cho 0.471<0.628). Kéo theo nghi **Pareto (C1) không thực sự lọc** → phải kiểm chứng lại logic.

**Ưu tiên 2 — Thêm bằng chứng (reviewer đòi):**
- Baseline **non-SVM**: RandomForest, XGBoost (đã có ở src/reliability.py, Paper 2) — CHỈ dùng cho accuracy/regime; có thể thêm FT-Transformer/TabNet.
- **UNSW-NB15** làm dataset thứ 2 + supplementary (đã port sẵn ở notebooks/unsw/).
- **Nhiễu NISQ thật**: Aer/FakeBackend noise model (MIỄN PHÍ, chạy local) — hoặc bỏ chữ "NISQ-aware".
- **C-sensitivity** QSVM (giải trình vì sao C=1.0 cố định).
- **Link code GitHub** (reproducibility, Reviewer 4 đòi).

**Ưu tiên 3 — Viết lại:**
- **Giảm overclaim** ("quantum advantage is real" → giới hạn baseline/setup; F1 0.854 vs 0.838 là biên).
- Cấu trúc lại Theory (Propositions là fact đã biết, đừng đóng khung định lý).
- Sửa số liệu lệch (Bảng VI N=1000 vs Bảng IV; thêm số rare-attack N=500).

**Ràng buộc nộp:** không đổi tác giả/self-citation; highlight vàng thay đổi; >12 trang → phí MOPC; bio tác giả (<150 từ); nộp bản sạch + bản highlight + rebuttal letter point-by-point.

## 4. ✅ Quyết định PHƯƠNG PHÁP đã chốt (đừng litigate lại)
| Vấn đề | Quyết định | Lý do |
|---|---|---|
| Tăng số qubit/feature (4)? | **KHÔNG** — giữ 4-qubit, chỉ thêm note scaling n=5,6,8 | 4-qubit là bản sắc/tiền đề NISQ; đổi = mất định danh |
| Tăng N? | **Nhẹ** — thêm mốc N=2000 nếu chạy nổi + tăng seed (5→10); khung low-data là chủ đích | Kernel O(N²) chậm; low-data là đóng góp C6 |
| Thay PCA bằng NN autoencoder / transformer? | **KHÔNG** — giữ PCA | NN gánh phần phi tuyến → **mờ quantum advantage**; overfit ở low-data; phá C1 (interpretable, gate-cost). Có thể thêm transformer làm **baseline classifier**, KHÔNG phải reducer |
| Bộ dataset thứ 3 (CIC-IDS)? | **KHÔNG** dưới deadline | UNSW đã đủ (reviewer chấp nhận); mỗi bộ = tính lại kernel tốn giờ |
| Gộp Paper 2 vào Paper 1? | **HOÃN** — làm xong tất cả rồi tính | Nếu gộp phải RÚT Paper 2 khỏi IJNM trước (tránh dual-submission); gộp không đổi tier journal nhưng mạnh hơn; đánh đổi: mất 1 công bố + credit corres Paper 2 của Quan |

**Nguyên tắc lõi:** phần cổ điển càng đơn giản càng tốt để lợi thế thuộc kernel lượng tử. Giữ lõi (4-qubit, low-data, Pareto PCA); sửa lỗi thật (theorem/refs); thêm baseline+noise+dataset; hạ giọng claim.

## 5. Câu hỏi chiến lược còn mở
- **Gộp hay giữ 2 bài?** → quyết sau khi Paper 1 xong. Nếu gộp: rút IJNM (Wiley Research Exchange → Withdraw, hoặc email editor — đang giai đoạn đầu nên dễ). Cân nhắc: 2 bài (Quan corres cả 2) > 1 bài về CV.

## 6. Trạng thái repo (đã dọn xong)
- Cấu trúc theo dataset: `data|models|results|reports|notebooks / {nslkdd,unsw}`. Path đã fix + config.py trung tâm.
- Notebook = nơi làm chính (C1–C6). runners/ + src/reliability.py = pipeline Paper 2.
- Dùng **uv** (pyproject.toml + uv.lock). File cá nhân (PII, ảnh) đã đưa ra ngoài repo.
- 2 residual nhỏ: c5/c6 ghi JSON vào data/nslkdd thay vì results/nslkdd (chưa sửa).

## 7. Đọc gì trước
HANDOFF (file này) → AGENTS.md → PAPER1_overview.md → paper1_revision_plan.md → PAPER2_overview.md → rồi code (config.py → notebooks/nslkdd theo thứ tự → src/reliability.py + runners).
