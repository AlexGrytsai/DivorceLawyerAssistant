import io
import os
from typing import Dict

import pymupdf as fitz  # type: ignore
from fastapi import UploadFile
from starlette.datastructures import Headers

from src.core import settings
from src.core.storage.shemas import FileDataSchema
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
) -> FileDataSchema:
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
    pdf_buffer.seek(0, io.SEEK_END)
    file_size = pdf_buffer.tell()
    pdf_buffer.seek(0)

    doc.close()

    file = UploadFile(
        filename=create_new_file_name(pdf_path),
        file=pdf_buffer,
        size=file_size,
        headers=Headers({"Content-Type": "application/pdf"}),
    )

    upload_file = await settings.STORAGE(
        file=file,
        request=kwargs.get("request"),
    )

    return upload_file
