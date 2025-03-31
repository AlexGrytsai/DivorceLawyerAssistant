from typing import Optional

from redis import Redis

from src.core.config import settings


def redis_client_for_performance_monitoring() -> Optional[Redis]:
    if settings.DEBUG:
        return Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
