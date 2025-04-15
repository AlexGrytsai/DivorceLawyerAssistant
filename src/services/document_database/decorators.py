from functools import wraps
from typing import Any, Callable, TypeVar, ParamSpec, Coroutine

from google.api_core import exceptions as google_exceptions

from src.services.document_database.exceptions import (
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


def handle_firestore_database_errors_sync(
    func: Callable[Parameters, ReturnType],
) -> Callable[Parameters, ReturnType]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> ReturnType:
        try:
            return func(*args, **kwargs)
        except google_exceptions.NotFound as e:
            raise DocumentNotFoundError(f"Document not found: {e}") from e
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Validation failed: {e}") from e
        except google_exceptions.GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise DocumentNotFoundError(f"Document not found: {e}") from e
            raise DatabaseOperationError(f"Operation failed: {e}") from e
        except (InvalidQueryParameterError, UnsupportedOperatorError):
            raise
        except Exception as e:
            if isinstance(
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
            raise DatabaseConnectionError(f"Unexpected error: {e}") from e

    return wrapper


def handle_firestore_database_errors_async(
    func: Callable[Parameters, Coroutine[Any, Any, ReturnType]],
) -> Callable[Parameters, Coroutine[Any, Any, ReturnType]]:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> ReturnType:
        try:
            return await func(*args, **kwargs)
        except google_exceptions.NotFound as e:
            raise DocumentNotFoundError(f"Document not found: {e}") from e
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Validation failed: {e}") from e
        except google_exceptions.GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise DocumentNotFoundError(f"Document not found: {e}") from e
            raise DatabaseOperationError(f"Operation failed: {e}") from e
        except (InvalidQueryParameterError, UnsupportedOperatorError):
            raise
        except Exception as e:
            if isinstance(
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
            raise DatabaseConnectionError(f"Unexpected error: {e}") from e

    return wrapper
