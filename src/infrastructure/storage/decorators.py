import functools
import logging
from typing import Callable

from src.domain.storage.exceptions import (
    ErrorUploadingFile,
    ErrorDeletingFile,
)

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
            raise ErrorUploadingFile(
                f"Error uploading file: {exc}.\nFile upload was unsuccessful"
            ) from exc

    return wrapper


def handle_delete_file_exceptions(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            return result
        except ErrorDeletingFile as exc:
            file_path = kwargs.get(
                "file_path", "file_path not transferred as a named argument"
            )
            logger.error(f"Error deleting file {file_path}: {exc}")
            raise ErrorDeletingFile(
                f"Error deleting {file_path}: {exc}"
            ) from exc

    return wrapper
