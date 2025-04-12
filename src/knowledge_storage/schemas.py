from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class KnowledgeSchema(BaseModel):
    name: str
    description: Optional[str] = None

    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class KnowledgeRenameSchema(KnowledgeSchema):
    old_name: str


class KnowledgeDeleteSchema(BaseModel):
    name: str
    delete_time: datetime = Field(default_factory=datetime.now)
