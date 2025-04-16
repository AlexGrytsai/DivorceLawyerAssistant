import functools
import logging
from typing import Callable

from google.api_core.exceptions import ClientError, NotFound
from google.auth.exceptions import GoogleAuthError

from src.domain.storage.exceptions import (
    ErrorWithAuthenticationInGCP,
    ProblemWithRequestToGCP,
    UnexpectedError,
    FileNotFound,
)

logger = logging.getLogger(__name__)


def _handle_gcs_exception(
    exc: Exception, *, include_not_found: bool = False
) -> None:
    if isinstance(exc, GoogleAuthError):
        logger.error("Failed to initialize GCS client", exc_info=True)
        raise ErrorWithAuthenticationInGCP(
            f"Failed to initialize GCS client: {exc}"
        )
    if include_not_found and isinstance(exc, NotFound):
        logger.error("File or folder not found", exc_info=True)
        raise FileNotFound(f"File or folder not found: {exc}") from exc
    if isinstance(exc, ClientError):
        logger.error("Failed to perform GCS operation", exc_info=True)
        raise ProblemWithRequestToGCP(
            f"Failed to perform GCS operation: {exc}"
        ) from exc
    logger.exception("Unexpected error", exc_info=True)
    raise UnexpectedError(f"Unexpected error: {exc}") from exc


def handle_google_storage_exceptions(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            _handle_gcs_exception(exc)

    return wrapper


def async_handle_google_storage_exceptions(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as exc:
            _handle_gcs_exception(exc, include_not_found=True)

    return wrapper
