from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateSchema(BaseModel):
    name: str
    description: Optional[str] = None

    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class DeleteSchema(BaseModel):
    name: str
    delete_time: datetime = Field(default_factory=datetime.now)


class KnowledgeSchema(CreateSchema):
    pass


class KnowledgeDetailSchema(KnowledgeSchema):
    list_category: Optional[CategorySchema]


class KnowledgeRenameSchema(KnowledgeSchema):
    old_name: str


class KnowledgeDeleteSchema(DeleteSchema):
    pass


class CategorySchema(CreateSchema):
    knowledge_storage: str


class CategoryRenameSchema(CategorySchema):
    old_name: str


class CategoryDeleteSchema(DeleteSchema):
    pass


class SubCategorySchema(CategorySchema):
    category: str


class SubCategoryRenameSchema(CategoryRenameSchema):
    pass


class SubCategoryDeleteSchema(CategoryDeleteSchema):
    pass


class ItemSchema(BaseModel):
    name: str
    url: str

    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class ItemCreateSchema(ItemSchema):
    subcategory: Optional[str] = None
    category: str
    knowledge_storage: str


class ItemRenameSchema(ItemSchema):
    old_name: str


class ItemDeleteSchema(DeleteSchema):
    pass
