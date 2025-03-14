import os
from typing import Dict

import pymupdf as fitz


def create_new_file_name(pdf_path: str) -> str:
    file_name, extension = os.path.splitext(pdf_path)
    return f"{file_name}_checked{extension}"


def add_comments_to_widgets(
    pdf_path: str,
    comments: Dict[str, str],
) -> None:
    doc = fitz.open(pdf_path)
    for page in doc:
        page_width = page.rect.width
        for widget in page.widgets():
            if widget.field_name in comments:
                widget_mid_y = widget.rect.y0
                annot_x = page_width - 50
                annot_y = widget_mid_y
                comment_text = comments[widget.field_name]
                page.add_text_annot(
                    (annot_x, annot_y), comment_text, icon="Note"
                )

    doc.save(create_new_file_name(pdf_path))
    doc.close()
