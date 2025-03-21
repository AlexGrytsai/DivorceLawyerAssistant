import logging.config
import os
from pathlib import Path
from types import MappingProxyType

from dotenv import load_dotenv

from src.core.storage import LocalStorage
from src.core.storage.storage import BaseStorage

load_dotenv()


class Settings:
    DEBUG: bool = os.getenv("DEBUG", "True") == "True"

    BASE_AI_MODEL: str = os.environ["BASE_AI_MODEL"]
    OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]

    STATIC_DIR: str = "static"
    UPLOAD_DIR: str = (
        f"{STATIC_DIR}/uploads/forms"  # str(Path("uploads") / "forms/")
    )
    STORAGE: BaseStorage = LocalStorage(path_to_upload_dir=UPLOAD_DIR)

    _MODEL_TOKEN_LIMITS = {
        "gpt-4": 10000,
        "gpt-4o": 30000,
        "gpt-4o-2024-08-06": 30000,
        "gpt-4o-realtime-preview": 20000,
        "gpt-4-turbo": 30000,
        "gpt-3.5-turbo": 200000,
        "gpt-3.5-turbo-16k": 160000,
    }

    MODEL_TOKEN_LIMITS = MappingProxyType(_MODEL_TOKEN_LIMITS)

    @property
    def get_token_limit(self) -> int:
        return self.MODEL_TOKEN_LIMITS.get(self.BASE_AI_MODEL, 0)


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
        "level": "DEBUG",
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
