from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from src.core.config import settings


class IndexSchema(BaseModel):
    name: str
    dimension: int = 1536
    metric: str = "cosine"
    created_at: Optional[datetime] = None


class IndexCreateSchema(IndexSchema):
    created_at: Optional[datetime] = Field(default_factory=datetime.now)


class IndexStatsSchema(BaseModel):
    namespaces: Dict[str, NamespaceStatsSchema] = Field(default_factory=dict)
    dimension: int = settings.DIMENSIONS_EMBEDDING
    metric: str = "cosine"
    vector_count: int = 0
    total_vector_count: int = 0
    index_fullness: float = 0.0


class NamespaceSchema(BaseModel):
    name: str
    index_name: str
    created_at: Optional[datetime] = None


class NamespaceCreateSchema(NamespaceSchema):
    created_at: Optional[datetime] = Field(default_factory=datetime.now)


class Document(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    file_path: str
    index_name: str
    namespace: str


class DocumentSchema(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    file_path: str
    index_name: str
    namespace: str


class QuerySchema(BaseModel):
    query: str
    index_name: str
    namespace: str
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None


class QueryResultSchema(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any]
    score: float
    file_path: str


class SearchResponseSchema(BaseModel):
    query: str
    results: List[QueryResultSchema]
    total: int


class ProcessingStatusSchema(BaseModel):
    index_name: str
    namespace: str
    status: str
    total_files: int
    processed_files: int
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class NamespaceStatsSchema(BaseModel):
    vector_count: int
