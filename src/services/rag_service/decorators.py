import functools
import logging
from typing import Callable, TypeVar

from pinecone import PineconeException

from src.services.rag_service.exceptions import (
    ErrorWithInitializationVectorDBClient,
)
from src.services.rag_service.schemas import PineconeIndexStatsSchema

logger = logging.getLogger(__name__)

T = TypeVar("T")


def handle_pinecone_exceptions(return_value: T = None) -> Callable:
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
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except PineconeException as exc:
                operation_name = func.__name__
                logger.error(
                    f"Error in Pinecone operation {operation_name}: {exc}",
                    exc_info=True,
                )
                return return_value
            except Exception as exc:
                operation_name = func.__name__
                logger.error(
                    f"Unexpected error in {operation_name}: {exc}",
                    exc_info=True,
                )
                return return_value

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
    return handle_pinecone_exceptions(PineconeIndexStatsSchema())(func)


def handle_list_operation_exceptions(func: Callable) -> Callable:
    """
    Decorator for handling exceptions in operations that return lists.
    Catches exceptions, logs them, and returns an empty list.

    Args:
        func: Function to decorate

    Returns:
        Decorated function that returns a list
    """
    return handle_pinecone_exceptions([])(func)


def handle_dict_operation_exceptions(func: Callable) -> Callable:
    """
    Decorator for handling exceptions in operations that return dictionaries.
    Catches exceptions, logs them, and returns an empty dictionary.

    Args:
        func: Function to decorate

    Returns:
        Decorated function that returns a dictionary
    """
    return handle_pinecone_exceptions({})(func)


def handle_boolean_operation_exceptions(func: Callable) -> Callable:
    """
    Decorator for handling exceptions in operations that return boolean values.
    Catches exceptions, logs them, and returns False.

    Args:
        func: Function to decorate

    Returns:
        Decorated function that returns a boolean
    """
    return handle_pinecone_exceptions(False)(func)
