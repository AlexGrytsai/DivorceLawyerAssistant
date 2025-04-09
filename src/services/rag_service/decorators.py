import functools
import logging
from typing import Callable

from fastapi import HTTPException, status
from pinecone import PineconeException

logger = logging.getLogger(__name__)


def handle_pinecone_exceptions() -> Callable:
    """
    Generic decorator for handling Pinecone operations.
    Catches PineconeException and other exceptions, logs them,
    and raises appropriate HTTP exceptions.

    Returns:
        Decorated function that handles exceptions
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
    Helper function for async exception handling.
    Executes an async function and catches exceptions, raising HTTP exceptions
    with appropriate error details.

    Args:
        func: Async function to execute
        args: Positional arguments for the function
        kwargs: Keyword arguments for the function
        operation_type: Type of operation for error messages

    Returns:
        Result from the executed function

    Raises:
        HTTPException: With details of the operation failure
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
                "error": f"Error in {operation_type}",
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
    Helper function for document processing exception handling.
    Executes an async function and catches exceptions, extracting file path
    information from arguments if available.

    Args:
        func: Async function to execute
        args: Positional arguments for the function
        kwargs: Keyword arguments for the function
        operation_type: Type of operation for error messages

    Returns:
        Result from the executed function

    Raises:
        HTTPException: With details of the document processing failure
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
    Catches exceptions, logs them, and raises appropriate HTTP exceptions
    with document processing details.

    Returns:
        Decorated async function
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> None:
        return await handle_async_document_exceptions(
            func, args, kwargs, "document processing"
        )

    return wrapper


def handle_async_search_exceptions(func: Callable) -> Callable:
    """
    Decorator for handling exceptions in async search operations.
    Catches exceptions, logs them, and raises appropriate HTTP exceptions
    with search operation details.

    Args:
        func: Function to decorate

    Returns:
        Decorated async function
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Callable:
        return await handle_async_exceptions(func, args, kwargs, "search")

    return wrapper


def handle_pinecone_init_exceptions(func: Callable) -> Callable:
    """
    Decorator for handling exceptions during Pinecone client initialization.
    Catches exceptions, logs them, and raises an HTTP exception with
    appropriate status code and error details.

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
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "Error with Pinecone client initialization",
                    "message": f"Error initializing Pinecone client: {exc}",
                },
            ) from exc

    return wrapper


def handle_index_stats_exceptions(func: Callable) -> Callable:
    """
    Decorator for handling exceptions when retrieving index statistics.
    Uses handle_pinecone_exceptions to handle errors appropriately.

    Args:
        func: Function to decorate

    Returns:
        Decorated function with Pinecone exception handling
    """
    return handle_pinecone_exceptions()(func)


def handle_list_operation_exceptions(func: Callable) -> Callable:
    """
    Decorator for handling exceptions in operations that return lists.
    Uses handle_pinecone_exceptions to handle errors appropriately.

    Args:
        func: Function to decorate

    Returns:
        Decorated function with Pinecone exception handling
    """
    return handle_pinecone_exceptions()(func)


def handle_dict_operation_exceptions(func: Callable) -> Callable:
    """
    Decorator for handling exceptions in operations that return dictionaries.
    Uses handle_pinecone_exceptions to handle errors appropriately.

    Args:
        func: Function to decorate

    Returns:
        Decorated function with Pinecone exception handling
    """
    return handle_pinecone_exceptions()(func)


def handle_boolean_operation_exceptions(func: Callable) -> Callable:
    """
    Decorator for handling exceptions in operations that return boolean values.
    Uses handle_pinecone_exceptions to handle errors appropriately.

    Args:
        func: Function to decorate

    Returns:
        Decorated function with Pinecone exception handling
    """
    return handle_pinecone_exceptions()(func)


def handle_index_operation_exceptions(func: Callable) -> Callable:
    """
    Decorator for handling exceptions in index operations (create, delete).
    Uses handle_pinecone_exceptions to handle errors appropriately.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as exc:
            operation_name = func.__name__
            logger.error(
                f"Error in index operation {operation_name}: {exc}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Error in index operation",
                    "message": f"Error in index operation {operation_name}: {exc}",
                },
            ) from exc
    return wrapper


def handle_namespace_operation_exceptions(func: Callable) -> Callable:
    """
    Decorator for handling exceptions in namespace operations (create, delete).
    Uses handle_pinecone_exceptions to handle errors appropriately.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as exc:
            operation_name = func.__name__
            logger.error(
                f"Error in namespace operation {operation_name}: {exc}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Error in namespace operation",
                    "message": f"Error in namespace operation {operation_name}: {exc}",
                },
            ) from exc
    return wrapper


def handle_folder_operation_exceptions(func: Callable) -> Callable:
    """
    Decorator for handling exceptions in folder operations (upload, delete).
    Uses handle_pinecone_exceptions to handle errors appropriately.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as exc:
            operation_name = func.__name__
            logger.error(
                f"Error in folder operation {operation_name}: {exc}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Error in folder operation",
                    "message": f"Error in folder operation {operation_name}: {exc}",
                },
            ) from exc
    return wrapper
