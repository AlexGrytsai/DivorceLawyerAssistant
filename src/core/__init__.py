import os

from .config import Settings

settings = Settings()

os.makedirs(settings.STATIC_DIR, exist_ok=True)
