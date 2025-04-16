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


def handle_google_storage_exceptions(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except GoogleAuthError as exc:
            logger.error("Failed to initialize GCS client", exc_info=True)
            raise ErrorWithAuthenticationInGCP(
                f"Failed to initialize GCS client: {exc}"
            )
        except ClientError as exc:
            logger.error("Failed to perform GCS operation", exc_info=True)
            raise ProblemWithRequestToGCP(
                f"Failed to perform GCS operation: {exc}"
            )
        except UnexpectedError as exc:
            logger.exception("Unexpected error", exc_info=True)
            raise UnexpectedError(f"Unexpected error: {exc}") from exc

    return wrapper


def async_handle_google_storage_exceptions(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except GoogleAuthError as exc:
            logger.error("Failed to initialize GCS client", exc_info=True)
            raise ErrorWithAuthenticationInGCP(
                f"Failed to initialize GCS client: {exc}"
            )
        except NotFound as exc:
            logger.error("File or folder not found", exc_info=True)
            raise FileNotFound(f"File or folder not found: {exc}") from exc

        except ClientError as exc:
            logger.error("Failed to perform GCS operation", exc_info=True)

            raise ProblemWithRequestToGCP(
                f"Failed to perform GCS operation: {exc}"
            ) from exc
        except Exception as exc:
            logger.exception("Unexpected error", exc_info=True)

            raise UnexpectedError(f"Unexpected error: {exc}") from exc

    return wrapper
