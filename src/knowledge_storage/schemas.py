from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class KnowledgeSchema(BaseModel):
    name: str
    description: Optional[str] = None

    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class KnowledgeDetailSchema(KnowledgeSchema):
    list_category: Optional[CategorySchema]


class KnowledgeRenameSchema(KnowledgeSchema):
    old_name: str


class KnowledgeDeleteSchema(BaseModel):
    name: str
    delete_time: datetime = Field(default_factory=datetime.now)


class CategorySchema(BaseModel):
    name: str
    knowledge_storage: str
    description: Optional[str] = None

    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class CategoryRenameSchema(CategorySchema):
    old_name: str


class CategoryDeleteSchema(BaseModel):
    name: str
    delete_time: datetime = Field(default_factory=datetime.now)


class SubCategorySchema(CategorySchema):
    category: str
