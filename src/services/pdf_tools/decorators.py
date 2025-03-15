import functools
import logging
from typing import Callable

from fastapi import HTTPException, status
from pymupdf import FileNotFoundError
from pymupdf.mupdf import FzErrorBase, FzErrorSystem

logger = logging.getLogger(__name__)


def handle_pymupdf_exceptions(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as exc:
            logger.warning(f"File not found: {exc}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File not found: {exc}",
            )
        except FzErrorSystem as exc:
            logger.warning(f"System error: {exc}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"System error: {exc}",
            )
        except FzErrorBase as exc:
            logger.warning(f"PDF error: {exc}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PDF error: {exc}",
            )
        except Exception as exc:
            logger.error(f"Unexpected error: {exc}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unexpected error: {exc}",
            )

    return wrapper
