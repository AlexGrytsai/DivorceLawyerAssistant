"""
Application settings and configuration.
"""

import os
from types import MappingProxyType

from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone

from src.core.constants import (
    MODEL_TOKEN_LIMITS,
    STATIC_DIR,
    UPLOAD_DIR,
    PROJECT_ID,
    RAG_BUCKET_NAME,
    MAIN_BUCKET_NAME,
)
from src.core.types import TokenLimitsMapping
from src.services.storage import CloudStorage
from src.services.storage.interfaces import BaseStorageInterface

load_dotenv()


class Settings:

    DEBUG: bool = os.getenv("DEBUG", "True") == "True"

    # Required environment variables
    BASE_AI_MODEL: str = os.getenv("BASE_AI_MODEL", "Not Found")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "Not Found")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "Not Found")

    # Directory settings
    STATIC_DIR: str = STATIC_DIR
    UPLOAD_DIR: str = UPLOAD_DIR

    STORAGE: BaseStorageInterface = CloudStorage(
        project_id=PROJECT_ID, bucket_name=MAIN_BUCKET_NAME
    )

    RAG_STORAGE: BaseStorageInterface = CloudStorage(
        project_id=PROJECT_ID, bucket_name=RAG_BUCKET_NAME
    )

    # Model AI settings
    DIMENSIONS_EMBEDDING: int = 3072

    EMBEDDING_DEFAULT: Embeddings = OpenAIEmbeddings(
        openai_api_key=OPENAI_API_KEY,  # type: ignore[call-arg]
        model="text-embedding-3-large",
        dimensions=3072,
    )

    VECTOR_DATABASE_DEFAULT_CLIENT = Pinecone(api_key=PINECONE_API_KEY)

    MODEL_TOKEN_LIMITS: TokenLimitsMapping = MappingProxyType(
        MODEL_TOKEN_LIMITS
    )

    @property
    def get_token_limit(self) -> int:
        """Get token limit for the current model."""
        return self.MODEL_TOKEN_LIMITS.get(self.BASE_AI_MODEL, 0)
