from typing import Optional

from redis import Redis

from src.core.config import settings


def redis_client_for_performance_monitoring() -> Redis:
    try:
        return Redis(
            host="localhost",
            port=6379,
            db=0,
            decode_responses=True,
        )
    except Exception as exc:
        # sourcery skip: raise-specific-error
        raise Exception(f"Failed to connect to Redis: {exc}") from exc
