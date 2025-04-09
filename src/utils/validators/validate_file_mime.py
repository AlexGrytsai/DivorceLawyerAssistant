import asyncio
import logging
from typing import List, Tuple

import magic
from fastapi import UploadFile, HTTPException, status

logger = logging.getLogger(__name__)


def get_real_mime_type(file: bytes) -> str:
    mime = magic.Magic(mime=True)
    return mime.from_buffer(file)


async def check_mime_type(
    file: UploadFile,
    allowed_mime_types: Tuple[str, ...],
) -> Tuple[bool, UploadFile]:
    file_bytes = await file.read()
    is_valid = get_real_mime_type(file_bytes) in allowed_mime_types

    return is_valid, file


async def validate_file_mime(
    files: List[UploadFile], allowed_mime_types: Tuple[str, ...]
) -> List[UploadFile]:
    check_results = await asyncio.gather(
        *(check_mime_type(file, allowed_mime_types) for file in files)
    )

    for is_valid, file in check_results:
        if not is_valid:
            logger.warning(f"File {file.filename} has wrong MIME type.")
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=(
                    f"File {file.filename} has wrong MIME type. "
                    f"Allowed MIME types: "
                    f"{', '.join(allowed_mime_types)}"
                ),
            )
        await file.seek(0)

    return files
