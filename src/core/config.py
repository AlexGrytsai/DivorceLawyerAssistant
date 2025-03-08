import logging.config
import os

from dotenv import load_dotenv
from redis import Redis

load_dotenv()

redis_client_for_performance_monitoring = Redis(
    host="localhost",
    port=6379,
    db=10,
    decode_responses=True,
)


class Settings:
    DEBUG: bool = True

    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "{levelname} [{asctime}] ({filename}) {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "main": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        }
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
