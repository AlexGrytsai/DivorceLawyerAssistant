from functools import wraps
from typing import (
    Any,
    Callable,
    TypeVar,
    Coroutine,
    ParamSpec,
    overload,
)

from google.api_core import exceptions as google_exceptions

from src.services.document_database.exceptions import (
    ValidationError,
    DatabaseConnectionError,
    DatabaseOperationError,
    DocumentNotFoundError,
    DocumentAlreadyExistsError,
)

ReturnType = TypeVar("ReturnType")
Parameters = ParamSpec("Parameters")


# For synchronous functions
@overload
def handle_firestore_database_errors(  # noqa
    func: Callable[Parameters, ReturnType],
) -> Callable[Parameters, ReturnType]: ...


# For asynchronous functions
@overload
def handle_firestore_database_errors(  # noqa
    func: Callable[Parameters, Coroutine[Any, Any, ReturnType]],
) -> Callable[Parameters, Coroutine[Any, Any, ReturnType]]: ...


def handle_firestore_database_errors(func):
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        try:
            result = func(*args, **kwargs)
            if isinstance(result, Coroutine):

                async def async_wrapper():
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

    return wrapper
