import functools
import logging
from typing import Callable

from fastapi import HTTPException, status
from openai import (
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    RateLimitError,
)

logger = logging.getLogger(__name__)


def reconnection_async(attempts: int = 10) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            remaining_attempts = attempts
            while remaining_attempts > 0:
                try:
                    return await func(*args, **kwargs)
                except APITimeoutError as exc:
                    remaining_attempts -= 1
                    if remaining_attempts == 0:
                        logger.error(
                            f"Request timeout. Please try again later. "
                            f"Message: {exc}"
                        )
                        raise HTTPException(
                            status_code=status.HTTP_408_REQUEST_TIMEOUT,
                            detail="Request timeout. Please try again later.",
                        )
                except (
                    AuthenticationError,
                    InternalServerError,
                    RateLimitError,
                ) as exc:
                    logger.error(exc)
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Service unavailable. Please try again later.",
                    )
                except HTTPException as exc:
                    logger.error(
                        f"Error with fetching data from OpenAI: {exc}"
                    )
                    raise exc

        return wrapper

    return decorator
