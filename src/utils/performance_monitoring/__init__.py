from redis import Redis, RedisError


def redis_client_for_performance_monitoring() -> Redis:
    try:
        return Redis(
            host="localhost",
            port=6379,
            db=0,
            decode_responses=True,
        )
    except RedisError as exc:
        # sourcery skip: raise-specific-error
        raise Exception(f"Failed to connect to Redis: {exc}") from exc
