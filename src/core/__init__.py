import os

from .config import settings

# Create necessary directories
os.makedirs(settings.STATIC_DIR, exist_ok=True)
