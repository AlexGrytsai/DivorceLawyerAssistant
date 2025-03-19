import io
import os
from typing import Dict, Tuple

import pymupdf as fitz  # type: ignore

from src.services.pdf_tools.decorators import handle_pymupdf_exceptions


def create_new_file_name(pdf_path: str) -> str:
    file_name, extension = os.path.splitext(os.path.basename(pdf_path))
    return f"{file_name}_checked{extension}"


def get_comment_position(
    page_width: int, widget: fitz.Widget
) -> tuple[int, int]:
    return page_width - 25, widget.rect.y0


@handle_pymupdf_exceptions
async def add_comments_to_widgets(
    pdf_path: str,
    comments: Dict[str, str],
    **kwargs,
) -> Tuple[io.BytesIO, str]:
    doc = fitz.open(pdf_path)
    for page in doc:
        for widget in page.widgets():
            if widget.field_name in comments:
                page.add_text_annot(
                    get_comment_position(page.rect.width, widget),
                    comments[widget.field_name],
                    icon="Note",
                )

    pdf_buffer = io.BytesIO()
    doc.save(pdf_buffer)

    return pdf_buffer, pdf_path
