from typing import Optional

from redis import Redis

from src.core.config import settings


def redis_client_for_performance_monitoring() -> Optional[Redis]:
    if settings.DEBUG:
        return Redis(
            host="localhost",
            port=6379,
            db=0,
            decode_responses=True,
        )
    return None


redis_client_monitoring = redis_client_for_performance_monitoring()
