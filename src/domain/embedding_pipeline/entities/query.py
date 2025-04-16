from typing import Optional, Dict, Any

from pydantic import BaseModel


class Query(BaseModel):
    query: str
    index_name: str
    namespace: Optional[str]
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None


class QueryResult(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any]
    score: float
    file_path: str
