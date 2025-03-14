import os
from typing import Dict, Any

import pymupdf as fitz


def create_new_file_name(pdf_path: str) -> str:
    file_name, extension = os.path.splitext(pdf_path)
    return f"{file_name}_checked{extension}"


def get_comment_position(
    page_width: int, widget: fitz.Widget
) -> tuple[int, int]:
    return page_width - 50, widget.rect.y0


def add_comments_to_widgets(
    pdf_path: str,
    comments: Dict[str, str],
) -> None:
    doc = fitz.open(pdf_path)
    for page in doc:
        for widget in page.widgets():
            if widget.field_name in comments:
                page.add_text_annot(
                    get_comment_position(page.rect.width, widget),
                    comments[widget.field_name],
                    icon="Note",
                )

    doc.save(create_new_file_name(pdf_path))
    doc.close()
