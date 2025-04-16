from datetime import datetime
from typing import Optional, Dict

from pydantic import BaseModel, Field

from src.core.config import settings
from src.domain.embedding_pipeline.entities import NamespaceStats


class IndexVectorDataBase(BaseModel):
    name: str
    dimension: int = 1536
    metric: str = "cosine"
    created_time: Optional[datetime] = None


class IndexStatsSchema(BaseModel):
    namespaces: Dict[str, NamespaceStats] = Field(default_factory=dict)
    dimension: int = settings.DIMENSIONS_EMBEDDING
    metric: str = "cosine"
    vector_count: int = 0
    total_vector_count: int = 0
    index_fullness: float = 0.0
