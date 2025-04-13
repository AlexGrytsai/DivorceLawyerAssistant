import os
from typing import Dict

from dotenv import load_dotenv

load_dotenv()

# Model token limits
MODEL_TOKEN_LIMITS: Dict[str, int] = {
    "gpt-4": 10000,
    "gpt-4o": 30000,
    "gpt-4o-2024-08-06": 30000,
    "gpt-4o-realtime-preview": 20000,
    "gpt-4o-mini": 128_000,
    "gpt-4-turbo": 30000,
    "gpt-3.5-turbo": 200000,
    "gpt-3.5-turbo-16k": 160000,
}

# Directory constants
STATIC_DIR: str = "static"
UPLOAD_DIR: str = f"{STATIC_DIR}/uploads/forms"

PROJECT_ID: str = os.getenv("PROJECT_ID", "Unknown")

# Bucket names
MAIN_BUCKET_NAME: str = os.getenv("MAIN_BUCKET_NAME", "Unknown")
RAG_BUCKET_NAME: str = os.getenv("RAG_BUCKET_NAME", "Unknown")

# Allowed mime types
ALLOWED_MIME_TYPES_FOR_FORMS = (
    "application/pdf",
    "application/msword",  # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
)

ALLOWED_MIME_TYPES_FOR_RAG = ("application/pdf",)
