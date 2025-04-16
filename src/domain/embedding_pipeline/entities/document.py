from datetime import datetime
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field


class Document(BaseModel):
    name: str
    path: str
    index_name: str
    namespace: Optional[str]
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    content: Optional[str] = None

    @property
    def is_processed(self) -> bool:
        return self.content is not None
