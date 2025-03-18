from redis import Redis

from core import settings

if settings.DEBUG:
    redis_client_for_performance_monitoring = Redis(
        host="localhost",
        port=6379,
        db=10,
        decode_responses=True,
    )
else:
    redis_client_for_performance_monitoring = None
