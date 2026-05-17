"""Đọc file .docx, in nguyên văn toàn bộ paragraph + bảng + dấu vết ảnh.

Cú pháp: python scripts/read_docx.py <path.docx> [--images]
"""
from __future__ import annotations
import sys
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn


def iter_block_items(parent):
    """Yield paragraphs + tables theo đúng thứ tự xuất hiện trong document."""
    from docx.document import Document as _Document
    from docx.table import _Cell, Table
    from docx.text.paragraph import Paragraph

    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise TypeError(parent)
    for child in parent_elm.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, parent)
        elif child.tag == qn("w:tbl"):
            yield Table(child, parent)


def has_image(paragraph):
    """Check paragraph có chứa ảnh (drawing/pic) không."""
    for run in paragraph.runs:
        if run._element.findall(".//" + qn("w:drawing")):
            return True
        if run._element.findall(".//" + qn("w:pict")):
            return True
    return False


def get_image_names(doc):
    """Lấy danh sách ảnh nhúng trong document.part.rels."""
    names = []
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            names.append(rel.target_ref)
    return names


def dump_docx(path: Path, dump_images: bool = False):
    doc = Document(str(path))
    from docx.text.paragraph import Paragraph
    from docx.table import Table

    para_idx = 0
    table_idx = 0
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            style = block.style.name if block.style else ""
            text = block.text.strip()
            img_mark = "  [IMAGE]" if has_image(block) else ""
            if text or img_mark:
                print(f"[P{para_idx:04d}|{style[:20]:<20}]{img_mark} {text}")
            para_idx += 1
        elif isinstance(block, Table):
            print(f"\n[T{table_idx:02d}] ===== TABLE {table_idx} ({len(block.rows)} rows × {len(block.columns)} cols) =====")
            for r, row in enumerate(block.rows):
                cells = [cell.text.strip().replace("\n", " | ") for cell in row.cells]
                print(f"  R{r}: " + " || ".join(cells))
            print(f"[T{table_idx:02d}] ===== END TABLE =====\n")
            table_idx += 1

    print("\n" + "=" * 80)
    print(f"TOTAL paragraphs (incl. empty): {para_idx}")
    print(f"TOTAL tables                  : {table_idx}")
    images = get_image_names(doc)
    print(f"TOTAL embedded images         : {len(images)}")
    if dump_images:
        for name in images:
            print(f"  - {name}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python read_docx.py <file.docx> [--images]")
        sys.exit(1)
    dump_docx(Path(sys.argv[1]), dump_images="--images" in sys.argv)
