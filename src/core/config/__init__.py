from .settings import Settings
from ...utils.performance_monitoring import (
    redis_client_for_performance_monitoring,
)

# Initialize the project settings
settings = Settings()

# Initialize the Redis client for performance monitoring
if settings.DEBUG:
    redis_client_monitoring = redis_client_for_performance_monitoring()
