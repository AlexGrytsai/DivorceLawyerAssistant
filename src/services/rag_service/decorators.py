import functools
import logging
from typing import Callable

from fastapi import HTTPException, status
from pinecone import PineconeException

from src.services.rag_service.exceptions import (
    ErrorWithInitializationVectorDBClient,
)

logger = logging.getLogger(__name__)


def handle_pinecone_exceptions() -> Callable:
    """
    Generic decorator for handling Pinecone operations.
    Catches PineconeException and other exceptions, logs them,
    and returns a default value on failure.

    Args:
        return_value: Value to return if an exception occurs

    Returns:
        Decorated function that handles exceptions and returns specified type
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Callable:
            try:
                return func(*args, **kwargs)
            except PineconeException as exc:
                operation_name = func.__name__
                logger.error(
                    f"Error in Pinecone operation {operation_name}: {exc}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "error": "Error with Pinecone operation",
                        "message": f"Error in Pinecone operation "
                        f"{operation_name}: {exc}",
                    },
                ) from exc
            except Exception as exc:
                operation_name = func.__name__
                logger.error(
                    f"Unexpected error in {operation_name}: {exc}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error": "Unexpected error in Pinecone operation",
                        "message": f"Unexpected error in "
                        f"{operation_name}: {exc}",
                    },
                ) from exc

        return wrapper

    return decorator


async def handle_async_exceptions(
    func: Callable,
    args: tuple,
    kwargs: dict,
    operation_type: str,
) -> Callable:
    """
    Helper function for async exception handling
    """
    try:
        return await func(*args, **kwargs)
    except Exception as exc:
        operation_name = func.__name__
        logger.error(
            f"Error in {operation_type} operation {operation_name}: {exc}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Error in {operation_type}",
                "message": f"Error in {operation_type} operation "
                f"{operation_name}: {exc}",
            },
        ) from exc


async def handle_async_document_exceptions(
    func: Callable,
    args: tuple,
    kwargs: dict,
    operation_type: str,
) -> None:
    """
    Helper function for document processing exception handling
    Raises HTTPException.
    """
    try:
        return await func(*args, **kwargs)
    except Exception as exc:
        operation_name = func.__name__
        file_path = kwargs.get("file_path", "") or (
            args[1] if len(args) > 1 else ""
        )

        logger.error(
            f"Error in {operation_type} operation {operation_name}: {exc}",
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Error processing document",
                "message": f"Error in {operation_type} "
                f"operation {operation_name}: {exc}",
                "file_path": file_path,
            },
        ) from exc


def handle_document_processing(
    func: Callable,
) -> Callable:
    """
    Decorator for handling exceptions in document processing operations.
    Catches exceptions, logs them, and raises DocumentProcessingError
    for proper HTTP error handling in FastAPI.

    Returns:
        Decorated async function
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> None:
        return await handle_async_document_exceptions(
            func, args, kwargs, "document processing"
        )

    return wrapper


def handle_async_search_exceptions() -> Callable:
    """
    Decorator for handling exceptions in async search operations.
    Catches exceptions, logs them, and returns specified value.

    Args:
        return_value: Value to return if exception occurs (default: empty list)

    Returns:
        Decorated async function
    """

    def decorator(
        func: Callable,
    ) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Callable:
            return await handle_async_exceptions(func, args, kwargs, "search")

        return wrapper

    return decorator


def handle_pinecone_init_exceptions(func: Callable) -> Callable:
    """
    Decorator for handling exceptions during Pinecone client initialization.
    Catches exceptions, logs them, and raises
    ErrorWithInitializationVectorDBClient.

    Args:
        func: Function to decorate

    Returns:
        Decorated function that handles initialization exceptions
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            logger.error(
                f"Error initializing Pinecone client: {exc}", exc_info=True
            )
            raise ErrorWithInitializationVectorDBClient(
                f"Error initializing Pinecone client: {exc}"
            ) from exc

    return wrapper


def handle_index_stats_exceptions(func: Callable) -> Callable:
    """
    Decorator for handling exceptions when retrieving index statistics.
    Catches exceptions, logs them, and returns empty PineconeIndexStatsSchema.

    Args:
        func: Function to decorate

    Returns:
        Decorated function that returns PineconeIndexStatsSchema
    """
    return handle_pinecone_exceptions()(func)


def handle_list_operation_exceptions(func: Callable) -> Callable:
    """
    Decorator for handling exceptions in operations that return lists.
    Catches exceptions, logs them, and returns an empty list.

    Args:
        func: Function to decorate

    Returns:
        Decorated function that returns a list
    """
    return handle_pinecone_exceptions()(func)


def handle_dict_operation_exceptions(func: Callable) -> Callable:
    """
    Decorator for handling exceptions in operations that return dictionaries.
    Catches exceptions, logs them, and returns an empty dictionary.

    Args:
        func: Function to decorate

    Returns:
        Decorated function that returns a dictionary
    """
    return handle_pinecone_exceptions()(func)


def handle_boolean_operation_exceptions(func: Callable) -> Callable:
    """
    Decorator for handling exceptions in operations that return boolean values.
    Catches exceptions, logs them, and returns False.

    Args:
        func: Function to decorate

    Returns:
        Decorated function that returns a boolean
    """
    return handle_pinecone_exceptions()(func)
