"""Inject output text + display_data (PNG) vào cell 24 của notebook C2.

Re-chạy logic cell 24 trong process này, capture stdout + đọc PNG bridge,
sau đó ghi vào trường `outputs` của cell 24 trong file .ipynb.

Mục đích: notebook nhìn như đã được thực thi (text + hình hiển thị inline)
mà không phải re-run toàn bộ notebook (~15-30 phút cho quantum kernel).
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB_PATH = ROOT / "notebooks" / "c2_quantum_kernel_expressibility.ipynb"
BRIDGE_PNG = ROOT / "reports" / "c2_spearman_bridge.png"
VERIFY_SCRIPT = ROOT / "scripts" / "c2_verify_cell24.py"


def run_verify_capture_stdout() -> str:
    """Chạy verify script trong subprocess, capture toàn bộ stdout với UTF-8."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(VERIFY_SCRIPT)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        cwd=str(ROOT),
        check=True,
    )
    return result.stdout


def encode_png_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def split_text_lines(text: str) -> list[str]:
    """Tách thành list dòng giữ '\\n' cuối, đúng chuẩn nbformat."""
    return text.splitlines(keepends=True)


def main():
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    print("Running verify script to capture stdout...")
    stdout_text = run_verify_capture_stdout()

    print(f"Captured {len(stdout_text)} chars of stdout")
    print(f"Reading bridge PNG: {BRIDGE_PNG}")
    assert BRIDGE_PNG.exists(), f"Khong tim thay {BRIDGE_PNG}"
    png_b64 = encode_png_b64(BRIDGE_PNG)
    print(f"PNG base64 length: {len(png_b64)} chars")

    print(f"\nLoading notebook: {NB_PATH}")
    with NB_PATH.open("r", encoding="utf-8") as f:
        nb = json.load(f)

    cell24 = nb["cells"][24]
    assert cell24["cell_type"] == "code"

    # Outputs: stream (stdout) + display_data (PNG)
    outputs = [
        {
            "name": "stdout",
            "output_type": "stream",
            "text": split_text_lines(stdout_text),
        },
        {
            "data": {
                "image/png": png_b64,
                "text/plain": ["<IPython.core.display.Image object>"],
            },
            "metadata": {},
            "output_type": "display_data",
        },
    ]

    cell24["outputs"] = outputs
    cell24["execution_count"] = 24

    with NB_PATH.open("w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
        f.write("\n")

    print(f"\nDa inject {len(outputs)} outputs vao cell 24 cua {NB_PATH.name}")
    print(f"  - stream stdout: {len(stdout_text)} chars")
    print(f"  - display_data PNG: c2_spearman_bridge.png")


if __name__ == "__main__":
    main()
