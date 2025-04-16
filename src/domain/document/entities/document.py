from datetime import datetime, timezone
from typing import Optional, Set

from pydantic import BaseModel, Field


class Document(BaseModel):
    """Schema for basic document information.

    Attributes:
        name: Unique name of the document
        path: Optional file system path to the document
        url: URL or access path to the document
        language: Document language code. Defaults to "en"
        tags: Optional set of tags for categorization
    """

    name: str
    path: Optional[str] = None
    url: str
    language: Optional[str] = "en"
    tags: Optional[Set[str]] = None


class DocumentDetail(Document):
    """Detailed document schema with additional metadata.

    Attributes:
        size: Size of the document in bytes
        content_type: MIME type of the document
        owner: Owner of the document. Defaults to "System"
        create_time: Document creation timestamp
        update_time: Last update timestamp
    """

    size: Optional[int] = None
    content_type: Optional[str] = None
    owner: Optional[str] = "System"

    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class DocumentDelete(BaseModel):
    """Schema for deleted documents.

    Attributes:
        name: Name of the deleted document
        deleted_time: Deletion timestamp with UTC timezone
    """

    name: str
    deleted_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
