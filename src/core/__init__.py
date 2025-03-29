import os

from .config.settings import Settings

# Initialize settings
settings = Settings()

# Create the necessary directories
os.makedirs(settings.STATIC_DIR, exist_ok=True)

__all__ = ["settings"]
