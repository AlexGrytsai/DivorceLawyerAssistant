import uuid
from datetime import datetime
from typing import Dict, Optional, Set, Any

from pydantic import BaseModel, Field


class Document(BaseModel):
    """
    Document entity representing a document in the system.
    This is the aggregate root for document-related operations.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    path: str
    url: Optional[str] = None
    content_type: str
    size: int
    tags: Set[str] = Field(default_factory=set)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    owner: str = "System"
    created_at: datetime
    updated_at: datetime

    def add_tag(self, tag: str) -> None:
        """Add a tag to the document"""
        self.tags.add(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the document"""
        if tag in self.tags:
            self.tags.remove(tag)

    def update_description(self, new_description: str) -> None:
        """Update the document description"""
        self.description = new_description
        self.updated_at = datetime.now()
