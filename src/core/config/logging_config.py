"""
Logging configuration for the application.
"""

import logging.config

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
