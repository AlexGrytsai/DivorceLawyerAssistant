import functools
import logging
from typing import Callable

from fastapi import HTTPException, status
from google.api_core.exceptions import ClientError
from google.auth.exceptions import GoogleAuthError

from src.core.exceptions.storage import (
    ErrorUploadingFile,
    ErrorDeletingFile,
    ErrorWithAuthenticationInGCP,
    ProblemWithRequestToGCP,
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": str(exc),
                    "message": "File upload was unsuccessful",
                },
            )

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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": str(exc),
                    "message": f"Error deleting {file_path}",
                },
            )

    return wrapper


def handle_cloud_storage_exceptions(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except GoogleAuthError as exc:
            logger.error("Failed to initialize GCS client", exc)
            raise ErrorWithAuthenticationInGCP(
                f"Failed to initialize GCS client: {exc}"
            )
        except ClientError as exc:
            logger.error("Failed to perform GCS operation", exc)
            raise ProblemWithRequestToGCP(
                f"Failed to perform GCS operation: {exc}"
            )
        except Exception as exc:
            logger.error("Unexpected error", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": str(exc),
                    "message": "Unexpected error",
                },
            )

    return wrapper
