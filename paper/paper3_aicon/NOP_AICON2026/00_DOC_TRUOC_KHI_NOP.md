# Nộp bài AICON 2026 — special session QI-AI

EAI AICON 2026 · Phú Quốc, 20–22/11/2026 · kỷ yếu Springer **LNICST**
Short paper **6–11 trang** · nộp qua **Confy+** · **phản biện hai chiều mù**

---

## 🔴 Đọc dòng này trước mọi thứ khác

Trong thư mục có **hai** file PDF gần giống nhau. Nộp nhầm là **bị loại
thẳng**, không cần lý do nào khác.

| File | |
|---|---|
| `01_SUBMIT_THIS_anonymous.pdf` | ✅ **NỘP FILE NÀY** — trang 1 ghi *"Anonymous Submission"* |
| `99_DO_NOT_SUBMIT_named_preview.pdf` | ⛔ **KHÔNG NỘP** — có tên 4 tác giả, chỉ để thầy xem |

Đánh số `01` và `99` để hai file không bao giờ nằm cạnh nhau trong danh sách.

Script dựng thư mục này **tự kiểm**: nó giải nén nội dung PDF, xác minh bản
`01` không chứa chuỗi danh tính nào và bản `99` thì có. Đưa ngược hai file
là nó từ chối chạy.

---

## Vì sao phải ẩn danh

Phản biện hai chiều mù: phản biện không biết bạn là ai, bạn không biết họ là
ai. Nên **file PDF nộp lên không được có tên, đơn vị hay email**.

Tên bốn tác giả **khai trong hệ thống Confy+** — ban tổ chức thấy đủ, chỉ
phản biện là không thấy. Sau khi được nhận mới nộp bản camera-ready có tên.

Ba chỗ trong bài bị ẩn theo công tắc `\anonymoustrue`: khối tác giả, câu
*"our own earlier work"* ở §1, và mục tài liệu `[1]` (companion).

---

## Khai trong Confy+

**Title**
```
When Model Selection Manufactures a Finding: A Tuning Trap in
Quantum-Kernel Intrusion Detection
```

**Authors** (đúng thứ tự thầy Vân chốt)

| # | Tên | |
|---|---|---|
| 1 | Nang Hung Van Nguyen | |
| 2 | Quang Anh Nguyen | |
| 3 | Quan Tran Anh Vo | **corresponding author** |
| 4 | Minh Tuan Pham | |

Đơn vị cả bốn: `University of Science and Technology – The University of Danang, Danang 550000, Vietnam`

**Keywords**
```
Quantum kernel; Model selection; Evaluation protocol; Intrusion detection;
Reproducibility
```

---

## ⚠️ Khai xung đột lợi ích — bắt buộc

**Ba chair của special session QI-AI đều là đồng tác giả Paper 1 với nhóm:**
Minh Tuan Pham · Nang Hung Van Nguyen · Phuc Hao Do.

Hai người đầu còn là **đồng tác giả của chính bài này**.

Chair là người phân công phản biện và tham gia quyết định nhận/loại. Chair
vừa là đồng tác giả vừa xử lý bài của mình là **vi phạm quy trình** — kể cả
khi hoàn toàn trung thực.

**Khai không làm bài yếu đi.** Nó chỉ chuyển việc xử lý sang người khác.
Không khai mà bị phát hiện sau khi nhận bài thì hậu quả nặng hơn nhiều.

Làm hai việc:

1. **Trong Confy+**: tìm ô `Conflicts of Interest` — có thì tick đủ ba người
2. **Gửi email cho General Chair / TPC Chair** (không phải ba chair kia):

```
Dear General Chair,

I am writing to declare a conflict of interest for our submission to the
special session "Quantum-Inspired AI for Autonomous SAGINs and
Non-Terrestrial Networks".

Two of the three chairs of that special session are co-authors of this
submission, and the third is a co-author of the authors' companion
manuscript currently under review elsewhere.

We therefore ask that the handling of this submission and the assignment of
reviewers be carried out independently of those three chairs, and that they
be recused from any decision concerning it.

Please let me know if any further detail is needed.

Kind regards,
Quan Tran Anh Vo, on behalf of the authors
```

---

## Mirror ẩn danh

§Reproducibility của bài trỏ tới:
**https://anonymous.4open.science/r/selection-objective-artifacts-A54F**

Đã kiểm: sống, phục vụ đúng nội dung, không lộ tên/email/trường/username.

> Link này **hết hạn 21/03/2027**. Lúc camera-ready phải đổi sang link
> GitHub thật, nếu không bài xuất bản mang một link chết.

---

## Kiểm trước khi nộp

```bash
python runners/audit_paper3.py      # phải ra 92/92
```

Trong đó có chốt an toàn: nếu `\anonymoustrue` bị tắt (quên lật lại sau khi
build bản có tên) thì audit **báo đỏ và exit 1**.

---

## Sau khi được nhận — camera-ready

Chưa cần bây giờ, nhưng ghi lại để khỏi quên:

| | Việc |
|---|---|
| 1 | Sửa bài theo góp ý phản biện |
| 2 | Lật `\anonymousfalse` → hiện tên thật |
| 3 | Trả mục `\bibitem{companion}` về tên thật (lúc đó Paper 1 có thể đã có DOI) |
| 4 | **Đổi link ẩn danh sang link GitHub thật** |
| 5 | Ký **Springer Copyright Transfer Form** |
| 6 | **Ít nhất một tác giả phải đăng ký và đi trình bày** — Springer không in bài không có người trình bày |
