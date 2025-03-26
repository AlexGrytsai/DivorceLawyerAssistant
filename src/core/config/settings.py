"""
Application settings and configuration.
"""

import os
from types import MappingProxyType

from dotenv import load_dotenv

from src.core.constants import (
    MODEL_TOKEN_LIMITS,
    STATIC_DIR,
    UPLOAD_DIR,
    BASE_STORAGE_CLOUD_URL,
    PROJECT_ID,
    RAG_BUCKET_NAME,
    MAIN_BUCKET_NAME,
)
from src.core.exceptions.config import MissingEnvironmentVariable
from src.core.storage.cloud_storage import CloudStorage
from src.core.storage.interfaces.base_storage_interface import (
    BaseStorageInterface,
)
from src.core.types import TokenLimitsMapping

load_dotenv()


class Settings:

    DEBUG: bool = os.getenv("DEBUG", "True") == "True"

    # Required environment variables
    try:
        BASE_AI_MODEL: str = os.environ["BASE_AI_MODEL"]
        OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]
    except KeyError as e:
        raise MissingEnvironmentVariable(
            f"Missing required environment variable: {e}"
        )

    # Directory settings
    STATIC_DIR: str = STATIC_DIR
    UPLOAD_DIR: str = UPLOAD_DIR
    BASE_STORAGE_CLOUD_URL: str = BASE_STORAGE_CLOUD_URL

    STORAGE: BaseStorageInterface = CloudStorage(
        project_id=PROJECT_ID, bucket_name=MAIN_BUCKET_NAME
    )

    RAG_STORAGE: BaseStorageInterface = CloudStorage(
        project_id=PROJECT_ID, bucket_name=RAG_BUCKET_NAME
    )

    # Model settings
    MODEL_TOKEN_LIMITS: TokenLimitsMapping = MappingProxyType(
        MODEL_TOKEN_LIMITS
    )

    @property
    def get_token_limit(self) -> int:
        """Get token limit for the current model."""
        return self.MODEL_TOKEN_LIMITS.get(self.BASE_AI_MODEL, 0)
