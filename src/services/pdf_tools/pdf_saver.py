import asyncio
import io
import logging
import os
from typing import Optional, List, Tuple

from fastapi import UploadFile, Request, HTTPException, status
from starlette.datastructures import Headers

from src.core.config import settings
from src.core.storage.shemas import FileSchema

logger = logging.getLogger(__name__)


def create_new_file_name(
    pdf_path: str,
    suffix_for_new_file: Optional[str] = "",
) -> str:
    file_name, extension = os.path.splitext(os.path.basename(pdf_path))
    if suffix_for_new_file:
        return f"{file_name}_{suffix_for_new_file}{extension}"
    return f"{file_name}{extension}"


def determination_file_size(file_in_bytes: io.BytesIO) -> int:
    file_in_bytes.seek(0, io.SEEK_END)
    file_size = file_in_bytes.tell()
    file_in_bytes.seek(0)

    return file_size


async def save_pdf_to_new_file(
    pdf_buffer: io.BytesIO,
    old_pdf_path: str,
    **kwargs,
) -> FileSchema:
    request: Optional[Request] = kwargs.get("request")
    if request:
        file = UploadFile(
            filename=create_new_file_name(old_pdf_path, "with_simple_check"),
            file=pdf_buffer,
            size=determination_file_size(pdf_buffer),
            headers=Headers({"Content-Type": "application/pdf"}),
        )

        upload_file = await settings.STORAGE(
            file=file,
            request=request,
        )
        if isinstance(upload_file, FileSchema):
            return upload_file
    logger.warning(
        "Request is not provided in function save_pdf_to_new_file "
        "or file was not saved"
    )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Request is not provided in function save_pdf_to_new_file",
    )


async def multi_save_pdf_to_new_file(
    list_pdf_buffer: List[Tuple[io.BytesIO, str]], **kwargs
) -> List[FileSchema]:
    tasks = [
        save_pdf_to_new_file(pdf_buffer=pdf[0], old_pdf_path=pdf[1], **kwargs)
        for pdf in list_pdf_buffer
    ]

    return await asyncio.gather(*tasks)
