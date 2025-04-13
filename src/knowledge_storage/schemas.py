from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Any, Dict, Set
from enum import Enum

from pydantic import BaseModel, Field


class PermissionLevel(str, Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class CreateSchema(BaseModel):
    name: str
    description: Optional[str] = None
    tags: Set[str] = Field(default_factory=set)
    permissions: Dict[str, PermissionLevel] = Field(default_factory=dict)

    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class DeleteSchema(BaseModel):
    name: str
    delete_time: datetime = Field(default_factory=datetime.now)


class UpdateDescriptionSchema(BaseModel):
    name: str
    description: str
    update_time: datetime = Field(default_factory=datetime.now)


class MoveSchema(BaseModel):
    name: str
    new_parent: str
    update_time: datetime = Field(default_factory=datetime.now)


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 10


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class KnowledgeSchema(CreateSchema):
    pass


class KnowledgeDetailSchema(KnowledgeSchema):
    list_category: Optional[List[CategorySchema]]
    list_subcategory: Optional[List[SubCategorySchema]]
    list_item: Optional[List[ItemDetailSchema]]


class KnowledgeRenameSchema(KnowledgeSchema):
    old_name: str


class KnowledgeDeleteSchema(DeleteSchema):
    pass


class KnowledgeUpdateDescriptionSchema(UpdateDescriptionSchema):
    pass


class CategorySchema(CreateSchema):
    knowledge_storage: str


class CategoryDetailSchema(CategorySchema):
    list_subcategory: Optional[List[SubCategorySchema]]
    list_item: Optional[List[ItemSchema]]


class CategoryRenameSchema(CategorySchema):
    old_name: str


class CategoryDeleteSchema(DeleteSchema):
    pass


class CategoryUpdateDescriptionSchema(UpdateDescriptionSchema):
    knowledge_storage: str


class CategoryMoveSchema(MoveSchema):
    knowledge_storage: str


class SubCategorySchema(CategorySchema):
    category: str


class SubCategoryDetailSchema(SubCategorySchema):
    list_item: Optional[List[ItemSchema]]


class SubCategoryRenameSchema(CategoryRenameSchema):
    pass


class SubCategoryDeleteSchema(CategoryDeleteSchema):
    pass


class SubCategoryUpdateDescriptionSchema(UpdateDescriptionSchema):
    knowledge_storage: str
    category: str


class SubCategoryMoveSchema(MoveSchema):
    knowledge_storage: str
    category: str


class ItemSchema(BaseModel):
    name: str
    url: str
    tags: Set[str] = Field(default_factory=set)
    version: int = 1
    permissions: Dict[str, PermissionLevel] = Field(default_factory=dict)

    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class ItemCreateSchema(ItemSchema):
    subcategory: Optional[str] = None
    category: str
    knowledge_storage: str


class ItemDetailSchema(ItemCreateSchema):
    knowledge_storage: str
    category: str
    size: Optional[int] = None
    content_type: Optional[str] = None
    versions: List[int] = Field(default_factory=list)


class ItemRenameSchema(ItemSchema):
    old_name: str


class ItemDeleteSchema(DeleteSchema):
    pass


class ItemUpdateDescriptionSchema(UpdateDescriptionSchema):
    knowledge_storage: str
    category: str
    subcategory: Optional[str] = None


class ItemMoveSchema(MoveSchema):
    knowledge_storage: str
    category: str
    subcategory: Optional[str] = None


class ItemVersionSchema(BaseModel):
    version: int
    url: str
    create_time: datetime
    size: Optional[int] = None
    content_type: Optional[str] = None


class SmartSearchSchema(BaseModel):
    text: str
    item_path: str
    num_page_in_item: Optional[int] = None
    metadata: Dict[str, Any]
    relevance_score: float


class SmartSearchResponseSchema(BaseModel):
    query: str
    results: List[SmartSearchSchema]
    total_results: int
    execution_time: float
