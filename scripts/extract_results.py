"""Trích xuất kết quả số chính từ output của notebook để dùng cho báo cáo."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path


def extract_outputs(path: Path, max_chars: int = 4000) -> str:
    """Lấy toàn bộ stdout/text output text của notebook, ghép lại."""
    with open(path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    parts = []
    for i, c in enumerate(nb.get("cells", [])):
        if c.get("cell_type") != "code":
            continue
        for o in c.get("outputs", []):
            if o.get("output_type") == "stream":
                txt = "".join(o.get("text", []))
                if txt.strip():
                    parts.append(f"[cell {i}] {txt}")
            elif o.get("output_type") in ("execute_result", "display_data"):
                data = o.get("data", {})
                txt = data.get("text/plain", "")
                if isinstance(txt, list):
                    txt = "".join(txt)
                if txt.strip():
                    parts.append(f"[cell {i}] {txt}")
            elif o.get("output_type") == "error":
                parts.append(f"[cell {i}] ERROR {o.get('ename')}: {o.get('evalue')}")

    full = "\n".join(parts)
    return full


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print("===", p, "===")
        print(extract_outputs(Path(p)))
        print()
