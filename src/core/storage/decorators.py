import functools
import logging
from typing import Callable

from fastapi import HTTPException, status

from src.core.storage.exceptions import ErrorUploadingFile

logger = logging.getLogger(__name__)


def handle_upload_file_exceptions(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            return result
        except ErrorUploadingFile as exc:
            logger.warning(
                f"Error uploading file: {exc}.\nFile upload was unsuccessful"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": str(exc),
                    "message": "File upload was unsuccessful",
                },
            )

    return wrapper
