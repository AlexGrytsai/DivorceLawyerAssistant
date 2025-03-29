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

PROJECT_ID: str = os.environ["PROJECT_ID"]
MAIN_BUCKET_NAME: str = os.environ["MAIN_BUCKET_NAME"]
RAG_BUCKET_NAME: str = os.environ["RAG_BUCKET_NAME"]
