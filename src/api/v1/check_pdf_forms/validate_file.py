import asyncio
import logging
from typing import List, Tuple

import magic
from fastapi import UploadFile, HTTPException, status

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES_FOR_FORMS = (
    "application/pdf",
    "application/msword",  # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
)


def get_real_mime_type(file: bytes) -> str:
    mime = magic.Magic(mime=True)
    return mime.from_buffer(file)


async def check_mime_type(file: UploadFile) -> Tuple[bool, str]:
    file_bytes = await file.read()
    is_valid = get_real_mime_type(file_bytes) in ALLOWED_MIME_TYPES_FOR_FORMS

    return is_valid, file.filename


async def validate_files(files: List[UploadFile]) -> List[UploadFile]:
    check_results = await asyncio.gather(
        *(check_mime_type(file) for file in files)
    )

    for is_valid, filename in check_results:
        if not is_valid:
            logger.warning(f"File {filename} has wrong MIME type.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"File {filename} has wrong MIME type. "
                    f"Allowed MIME types: "
                    f"{', '.join(ALLOWED_MIME_TYPES_FOR_FORMS)}"
                ),
            )

    return files
