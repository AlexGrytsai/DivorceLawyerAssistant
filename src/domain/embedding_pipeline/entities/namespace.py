from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Namespace(BaseModel):
    name: str
    index_name: str
    create_time: Optional[datetime] = None


class NamespaceStats(BaseModel):
    vector_count: int
