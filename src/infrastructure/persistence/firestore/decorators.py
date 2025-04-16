from functools import wraps
from typing import Any, Callable, TypeVar, ParamSpec, Coroutine

from google.api_core import exceptions as google_exceptions

from src.domain.document.exceptions import (
    ValidationError,
    DatabaseConnectionError,
    DatabaseOperationError,
    DocumentNotFoundError,
    DocumentAlreadyExistsError,
    InvalidQueryParameterError,
    UnsupportedOperatorError,
)

ReturnType = TypeVar("ReturnType")
Parameters = ParamSpec("Parameters")


def _process_exception(e: Exception) -> None:
    if isinstance(e, google_exceptions.NotFound):
        raise DocumentNotFoundError(f"Document not found: {e}") from e
    elif isinstance(e, (ValueError, TypeError)):
        raise ValidationError(f"Validation failed: {e}") from e
    elif isinstance(e, google_exceptions.GoogleAPIError):
        if "not found" in str(e).lower():
            raise DocumentNotFoundError(f"Document not found: {e}") from e
        raise DatabaseOperationError(f"Operation failed: {e}") from e
    elif isinstance(e, (InvalidQueryParameterError, UnsupportedOperatorError)):
        raise
    elif isinstance(
        e,
        (
            DatabaseConnectionError,
            DatabaseOperationError,
            ValidationError,
            DocumentNotFoundError,
            DocumentAlreadyExistsError,
        ),
    ):
        raise
    else:
        raise DatabaseConnectionError(f"Unexpected error: {e}") from e


def handle_firestore_database_errors_sync(
    func: Callable[Parameters, ReturnType],
) -> Callable[Parameters, ReturnType]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> ReturnType:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            _process_exception(e)
            raise

    return wrapper


def handle_firestore_database_errors_async(
    func: Callable[Parameters, Coroutine[Any, Any, ReturnType]],
) -> Callable[Parameters, Coroutine[Any, Any, ReturnType]]:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> ReturnType:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            _process_exception(e)
            raise

    return wrapper
