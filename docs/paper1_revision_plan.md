# Kế hoạch Revise Paper 1 — IEEE TETC (Major Revision)

> Manuscript: **TETC-2026-05-0252** — "NISQ-Aware Quantum Kernel SVM for Network
> Intrusion Detection: A Regime-Specific Benchmark on NSL-KDD".
> Quyết định: **Major Revision** (14-Aug-2026). Corres IEEE: **Dr. Minh Tuan Pham**.

## 0. Ràng buộc CỨNG (vi phạm = desk reject)
- ❗ **KHÔNG có major revision vòng 2** → phải làm đạt ngay lần này.
- 📅 **Deadline: 13-Oct-2026.**
- 👥 **KHÔNG thêm/bớt tác giả** so với bản gốc nếu chưa có EiC đồng ý bằng văn bản. Đổi affiliation phải khai ở rebuttal + cover letter.
- 📚 **≤ 45 references.** **KHÔNG đổi self-citation.** Mọi thay đổi bib phải **highlight vàng** + giải trình trong rebuttal.
- 📏 > 12 trang → phí **MOPC** (khai trong cover letter). Bản revised **phải có bio tác giả (<150 từ/người)**.
- 📤 Nộp 3 thứ: (1) bản sạch, (2) bản **highlight vàng** phần đổi, (3) **rebuttal letter** point-by-point + summary of differences.

---

## 1. 🚨 TỐI KHẨN — Liêm chính (làm TRƯỚC TIÊN)
| # | Việc | Chi tiết | Status |
|---|---|---|---|
| 1.1 | Audit TOÀN BỘ references | AE + Rev 2 báo có refs "không tồn tại". Kiểm tra từng ref có thật (DOI/URL). | ☐ |
| 1.2 | Ref [26] Rahman et al. (IEEE Access, QML for cybersecurity) | Nghi **bịa** — không tìm thấy. Xác minh; nếu sai → thay bằng ref thật tương đương. | ☐ |
| 1.3 | Ref [15] Payares & Martínez-Santos | Sai số bài: **116990F → 116990B** (DOI 10.1117/12.2593297). Sửa. | ☐ |
| 1.4 | **Theorem 1 sai** | Paper viết F̃(4) > F̃(3) nhưng Bảng III cho 0.471 < 0.628. Sửa lại phát biểu/chứng minh cho khớp số liệu. | ☐ |
| 1.5 | Kiểm tra Pareto (C1) có thực sự lọc | Rev 4: V(n)↑, F̃(n)↓, Q(n)↓ đơn điệu ⇒ Pareto có thể không lọc gì. Kiểm lại logic, nếu cần đổi cách trình bày đóng góp C1. | ☐ |

---

## 2. Baselines non-SVM (Rev 1, 2, AE) — DÙNG LẠI Paper 2
- Thêm **Random Forest + XGBoost** (đã có sẵn trong Paper 2 / `src/reliability.py`) vào so sánh **accuracy/F1 theo regime**.
- (Tùy chọn) TabNet/FT-Transformer nếu kịp — hoặc soften claim.
- ⚠️ **Ranh giới chống trùng Paper 2:** ở Paper 1 chỉ dùng cho **accuracy/regime**; phần **calibration/ECE để cho Paper 2**, cite sang.
- Status: ☐

## 3. Dataset thứ 2 — UNSW-NB15 (Rev 1, 4, AE)
- Đưa kết quả UNSW (đã có port ở `notebooks_unsw/`) vào **supplementary** + tóm tắt trong bài.
- Reviewer KHÔNG truy cập được supplementary → phải đính kèm bản cho reviewer lần này.
- Verdict UNSW (đã biết): QSVM **competitive, không dominant** → dùng để nói regime-dependent, không thổi phồng.
- Status: ☐

## 4. Nhiễu NISQ thật (Rev 1, 3, AE) — LÀM MỚI
- Hiện chỉ có **shot-noise**. Cần thêm **Aer noise model / IBM FakeBackend** (gate error, readout, decoherence).
- Nếu không kịp/không thuyết phục → **bỏ/giảm nhẹ chữ "NISQ-aware"** cho khớp bằng chứng (Rev 3 gắt điểm này).
- Status: ☐

## 5. Theory section (Rev 3, 4) — CẤU TRÚC LẠI
- "Propositions" là **fact đã biết** → đừng đóng khung thành Theorem + proof. Đổi sang "Background/Observation".
- **Proposition 3**: hiện chỉ cite, chưa dẫn → hoặc dẫn ngắn, hoặc hạ cấp thành nhận xét có cite.
- Sửa Theorem 1 (xem 1.4).
- Status: ☐

## 6. Giảm overclaim (Rev 1, 2, 3)
- "The quantum advantage is real and measurable" → đổi thành **giới hạn trong baseline & setup đã thử**.
- Thừa nhận cải thiện **biên** (F1 0.854 vs 0.838); không claim "general quantum advantage".
- Status: ☐

## 7. References — thêm mới + gọn ≤45 (Rev 1, 2, 3, 4)
Cần thảo luận & phân biệt với bài mình:
- "Benchmarking quantum ML methods for intrusion detection on noisy quantum computers", *Quantum Machine Intelligence*, 2026 (Rev 1).
- arXiv:2403.07059, arXiv:2409.04406 (Rev 3 — benchmarking gần).
- Carducci, "When Does Quantum Computing Provide Advantage for Malware Detection?...", IEEE ICAD 2026, doi:10.1109/ICAD69378.2026.11609075 (Rev 4).
- Thêm refs bối cảnh cho F1 NSL-KDD (giải thích F1 SVM thấp).
- ⚠️ Giữ tổng **≤ 45**; không đụng self-citation; highlight vàng mọi thay đổi.
- Status: ☐

## 8. C-sensitivity / quantum tuning (Rev 1, 4)
- Giải trình vì sao QSVM để **C=1.0** cố định trong khi SVM classical được tune.
- Thêm **sensitivity analysis** QSVM theo nhiều C (đã có `notebooks/c3_c_tuning_statevector.ipynb`).
- Engage literature về quantum kernel tuning; nêu rõ đây là **design choice** (liên quan claim "degrade dưới perturbation σ=0.20").
- Status: ☐

## 9. Reproducibility (Rev 4)
- Dán **link GitHub public** (repo đã dọn sạch): https://github.com/anhquan1111/QSVM_NSLKDD
- ⚠️ Trước khi công bố link: đảm bảo repo không còn file cá nhân (đã xử lý), có README chạy lại được.
- Status: ☐

## 10. Số liệu & làm rõ (Rev 1, 2, 4)
- **Bảng VI (N=1000) lệch Bảng IV** → giải thích/đồng bộ.
- **Thêm số rare-attack N=500** đang bị claim mà không show (+6.7 điểm, Cohen's d=0.68).
- Nêu **crossover** low-data (hoặc giải thích vì sao không có).
- "**Exponential concentration**" của kernel matrix — nêu song song barren plateau (Rev 2).
- Status: ☐

## 11. ⚠️ Quan hệ Paper 1 ↔ Paper 2 (chống trùng lặp)
- 2 bài là **companion**, khác trục (Paper1=hiệu năng, Paper2=calibration). Hợp lệ.
- **Paper 1 revised PHẢI cite Paper 2** và **khai với EiC** trong rebuttal/cover letter (companion under review at IJNM).
- **KHÔNG bê** phần calibration/ECE của Paper 2 vào Paper 1. RF/XGBoost ở Paper 1 chỉ cho accuracy/regime.
- **KHÔNG tái dùng nguyên văn/hình/bảng** giữa 2 bài.
- Status: ☐

## 12. Deliverables khi nộp (13-Oct-2026)
- ☐ Bản sạch (clean, không annotation)
- ☐ Bản annotated (highlight vàng phần đổi + đổi bib)
- ☐ Rebuttal letter: point-by-point tất cả comment + summary of differences + (nếu >12tr) khai MOPC + khai companion Paper 2
- ☐ Supplementary (UNSW) đính kèm cho reviewer
- ☐ Bio tác giả (<150 từ/người)
- ☐ Link portal: ieee.atyponrex.com (trong thư mời)

---

## 13. BỔ SUNG (sau khi soát lại toàn văn thư reviewer — các điểm plan còn sót)
- **13.1 Nền thống kê mỏng (Rev 2):** 5 seeds là yếu cho claim "large effect size" → tăng seed (5→10+) HOẶC bootstrap CI; báo cáo CI thực thay vì chỉ mean±std.
- **13.2 Regime ÂM phải có stats tương xứng (Rev 2):** 2 regime QSVM thua (temporal, perturbation) hiện chỉ giải thích **định tính** ("wrapped phase encoding") trong khi 3 regime dương có full stats → thêm effect-size/CI cho regime âm, HOẶC **hạ giọng "regime map"** cho cân bằng (tránh cherry-picking).
- **13.3 BẢO VỆ NOVELTY (Rev 3 = phiếu REJECT + AE nói "deviating novelty"):** phải viết rõ đóng góp KHÔNG phải kernel mới, mà là (a) phương pháp **regime-specific**, (b) Pareto **có chi phí qubit** (C1), (c) bộ **ablation + calibration + stress-test**. **Phân biệt tường minh** với arXiv:2403.07059 & 2409.04406 (2 bài Rev3 bảo "đã làm rồi") và QMI-2026 (Rev1). Đây là mục sống-còn vì R3 đòi từ chối.
- **13.4 Table I (Rev 1):** cập nhật rõ literature **2025–2026** (không chỉ thêm vài ref lẻ).
- **13.5 CatBoost:** Rev 1 nêu cùng TabNet/FT-Transformer — cân nhắc thêm nếu kịp.

## 14. ⚠️ ĐIỂM CẦN THẢO LUẬN / quyết định trước khi làm
- **MOPC (phí trang):** thêm baseline + noise + UNSW + bio tác giả → gần chắc **>12 trang ⇒ PHẢI TRẢ PHÍ MOPC**. Cần thầy đồng ý chi (khai trong cover letter) HOẶC nén nội dung. Quyết sớm.
- **Ngân sách ref ≤ 45:** đếm ref hiện tại; thêm ~5 ref mới mà **KHÔNG được bỏ self-citation** → có thể phải cắt ref non-self khác. Kiểm tra ngay để khỏi vỡ.
- **⚠️ Số Cohen's d rare N=500 VÊNH:** bài ghi **d = +0.68**, nhưng dữ liệu nội bộ cũ ghi **d = 0.4043**. Rev4 đòi đúng số này → **verify lại số thật** (chạy `run_reliability_*` / notebook C6) trước khi đưa vào rebuttal. Nếu bài in sai → sửa + giải trình.
- **Pushback EiC:** thư cho phép báo EiC nếu ref reviewer gợi ý không liên quan. Với 2 bài Rev3, chọn **thêm + phân biệt** (an toàn hơn) hay **phản biện lên EiC**.
- **Gộp Paper 1+2:** vẫn HOÃN — quyết sau khi Paper 1 xong.

## Thứ tự đề xuất
1) Mục 1 (liêm chính) → 2) Mục 7 refs + 5 theory → 3) Mục 2/3/8 (dùng lại tài sản có sẵn) → 4) Mục 4 (noise, làm mới) → 5) Mục 6/10 (viết lại claim + số liệu) → 6) Mục 12 (đóng gói + rebuttal).
