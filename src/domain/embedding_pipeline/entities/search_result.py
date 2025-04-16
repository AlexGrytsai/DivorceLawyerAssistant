from typing import List

from pydantic import BaseModel

from src.domain.embedding_pipeline.entities import QueryResult


class SearchResponseSchema(BaseModel):
    query: str
    results: List[QueryResult]
    total: int
