from datetime import datetime, timezone
from typing import Optional, Set

from pydantic import BaseModel, Field


class DocumentSchema(BaseModel):
    name: str
    path: Optional[str] = None
    url: str
    tags: Optional[Set[str]] = None


class DocumentDetailSchema(DocumentSchema):
    size: Optional[int] = None
    content_type: Optional[str] = None
    owner: Optional[str] = "Admin"

    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class DocumentDeleteSchema(BaseModel):
    name: str
    deleted_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
