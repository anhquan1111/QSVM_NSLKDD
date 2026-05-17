"""Script kiểm tra notebook: lỗi runtime, markdown tiếng Việt, cấu trúc cell."""
from __future__ import annotations
import json
import re
import sys
import unicodedata
from pathlib import Path


# Bộ ký tự tiếng Việt có dấu (lower)
VN_DIACRITIC_CHARS = set("àáảãạăằắẳẵặâầấẩẫậđèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ")

# Từ tiếng Việt phổ biến (không dấu) → nếu xuất hiện độc lập có nghĩa là mất dấu
SUSPICIOUS_NO_DIACRITIC_WORDS = {
    "tieng viet", "muc tieu", "ket qua", "phan tich", "chuong",
    "nghien cuu", "phuong phap", "thuc hien", "buoc", "khong",
    "tham so", "do chinh xac", "do phuc tap", "ma tran", "tap du lieu",
    "huan luyen", "kiem tra", "danh gia", "so sanh", "mo hinh",
    "luong tu", "co dien", "dac trung", "trich xuat", "chuan hoa",
    "giam chieu", "phan loai", "tan cong", "thong ke", "trung binh",
    "do lech", "chinh quy", "phan phoi", "moi truong", "thiet ke",
    "nhom tan cong", "hieu nang", "diem so", "ket luan", "tong ket",
}


def is_vietnamese_text(text: str) -> bool:
    """Đoán xem text có phải tiếng Việt không (dựa vào dấu hoặc từ phổ biến)."""
    low = text.lower()
    if any(c in VN_DIACRITIC_CHARS for c in low):
        return True
    # Có thể là tiếng Việt không dấu
    for w in SUSPICIOUS_NO_DIACRITIC_WORDS:
        if w in low:
            return True
    return False


def has_diacritics(text: str) -> bool:
    return any(c in VN_DIACRITIC_CHARS for c in text.lower())


def check_notebook(path: Path) -> dict:
    """Trả về dict thông tin kiểm tra notebook."""
    with open(path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    cells = nb.get("cells", [])
    n_cells = len(cells)
    n_code = sum(1 for c in cells if c.get("cell_type") == "code")
    n_md = sum(1 for c in cells if c.get("cell_type") == "markdown")

    # Tìm cell có lỗi (output_type == error) hoặc traceback
    error_cells = []
    for i, c in enumerate(cells):
        if c.get("cell_type") != "code":
            continue
        outputs = c.get("outputs", [])
        for o in outputs:
            if o.get("output_type") == "error":
                ename = o.get("ename", "")
                evalue = o.get("evalue", "")
                error_cells.append({
                    "cell_index": i,
                    "exec_count": c.get("execution_count"),
                    "ename": ename,
                    "evalue": evalue[:200],
                })
                break

    # Kiểm tra markdown tiếng Việt mất dấu
    md_issues = []
    md_total_vn = 0
    md_missing_diacritics = 0
    md_samples = []
    for i, c in enumerate(cells):
        if c.get("cell_type") != "markdown":
            continue
        src = "".join(c.get("source", []))
        if not src.strip():
            continue
        # Bỏ qua dòng code/url/HTML
        clean = re.sub(r"```[\s\S]*?```", "", src)
        clean = re.sub(r"`[^`]*`", "", clean)
        clean = re.sub(r"https?://\S+", "", clean)
        clean = re.sub(r"<[^>]+>", "", clean)
        if is_vietnamese_text(clean):
            md_total_vn += 1
            if not has_diacritics(clean):
                md_missing_diacritics += 1
                md_issues.append({
                    "cell_index": i,
                    "sample": clean.strip()[:150],
                })
        # Lưu vài mẫu để xem
        if len(md_samples) < 3 and clean.strip():
            md_samples.append(clean.strip()[:120])

    # Kiểm tra cấu trúc: code cell nào KHÔNG có markdown đứng trước
    code_without_md = []
    for i, c in enumerate(cells):
        if c.get("cell_type") != "code":
            continue
        # Tìm markdown gần nhất phía trước (trong vòng 1 cell)
        has_md_before = False
        if i > 0 and cells[i - 1].get("cell_type") == "markdown":
            src_md = "".join(cells[i - 1].get("source", [])).strip()
            if src_md:
                has_md_before = True
        # Bỏ qua các code cell chỉ là import / cell rỗng
        src = "".join(c.get("source", [])).strip()
        if not src:
            continue
        # Bỏ qua cell quá ngắn (chỉ là 1-2 dòng import/setup)
        if src.count("\n") < 2 and ("import" in src.lower() or "from" in src.lower()):
            continue
        if not has_md_before:
            code_without_md.append({
                "cell_index": i,
                "exec_count": c.get("execution_count"),
                "first_line": src.splitlines()[0][:100] if src else "",
            })

    return {
        "path": str(path),
        "n_cells": n_cells,
        "n_code": n_code,
        "n_md": n_md,
        "error_cells": error_cells,
        "md_total_vn": md_total_vn,
        "md_missing_diacritics": md_missing_diacritics,
        "md_issues": md_issues[:10],
        "md_samples": md_samples,
        "code_without_md": code_without_md[:15],
        "code_without_md_total": len(code_without_md),
    }


def print_report(info: dict) -> None:
    print(f"=== {info['path']} ===")
    print(f"Cells: {info['n_cells']} (code={info['n_code']}, md={info['n_md']})")
    print(f"Errors: {len(info['error_cells'])}")
    for e in info["error_cells"]:
        print(f"  - cell[{e['cell_index']}] exec={e['exec_count']}: {e['ename']}: {e['evalue']}")
    print(f"Markdown VN cells: {info['md_total_vn']}, missing diacritics: {info['md_missing_diacritics']}")
    for issue in info["md_issues"]:
        print(f"  - cell[{issue['cell_index']}]: {issue['sample']!r}")
    print(f"Code cells WITHOUT markdown header: {info['code_without_md_total']}")
    for c in info["code_without_md"]:
        print(f"  - cell[{c['cell_index']}] exec={c['exec_count']}: {c['first_line']!r}")
    if info["md_samples"]:
        print("Markdown samples:")
        for s in info["md_samples"]:
            print(f"  + {s}")
    print()


if __name__ == "__main__":
    paths = [Path(p) for p in sys.argv[1:]]
    for p in paths:
        info = check_notebook(p)
        print_report(info)
