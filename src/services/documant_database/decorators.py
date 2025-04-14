from functools import wraps
from typing import Any, Callable, TypeVar, cast, Awaitable, Union, Coroutine

from google.api_core import exceptions as google_exceptions

from src.services.documant_database.exceptions import (
    ValidationError,
    DatabaseConnectionError,
    DatabaseOperationError,
    DocumentNotFoundError,
    DocumentAlreadyExistsError,
)

SyncResultType = TypeVar("SyncResultType")
AsyncResultType = TypeVar("AsyncResultType", bound=Awaitable[Any])


def handle_firestore_database_errors(
    func: Callable[..., Union[SyncResultType, AsyncResultType]],
) -> Callable[..., Union[SyncResultType, AsyncResultType]]:
    @wraps(func)
    def wrapper(
        *args: Any, **kwargs: Any
    ) -> Union[SyncResultType, AsyncResultType]:
        try:
            result = func(*args, **kwargs)
            if isinstance(result, Coroutine):

                async def async_wrapper() -> Any:
                    try:
                        return await result
                    except google_exceptions.NotFound as e:
                        raise DocumentNotFoundError(
                            f"Document not found: {str(e)}"
                        )
                    except (ValueError, TypeError) as e:
                        raise ValidationError(f"Validation failed: {str(e)}")
                    except google_exceptions.GoogleAPIError as e:
                        if "not found" in str(e).lower():
                            raise DocumentNotFoundError(
                                f"Document not found: {str(e)}"
                            )
                        raise DatabaseOperationError(
                            f"Operation failed: {str(e)}"
                        )
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
                        raise DatabaseConnectionError(
                            f"Unexpected error: {str(e)}"
                        )

                return async_wrapper()
            return result
        except google_exceptions.NotFound as e:
            raise DocumentNotFoundError(f"Document not found: {str(e)}")
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Validation failed: {str(e)}")
        except google_exceptions.GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise DocumentNotFoundError(f"Document not found: {str(e)}")
            raise DatabaseOperationError(f"Operation failed: {str(e)}")
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
            raise DatabaseConnectionError(f"Unexpected error: {str(e)}")

    return cast(Callable[..., Union[SyncResultType, AsyncResultType]], wrapper)
