from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, List, Any, Dict, Set

from pydantic import BaseModel, Field


class PermissionLevel(str, Enum):
    """Permission levels for accessing knowledge storage resources.

    READ: Can view content
    WRITE: Can modify content
    ADMIN: Can manage permissions and structure
    """

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class CreateSchema(BaseModel):
    """Base schema for creating new resources.

    Attributes:
        name: Unique name of the resource
        description: Optional description
        tags: Set of tags for categorization
        permissions: Dictionary of user permissions
        create_time: Creation timestamp
        update_time: Last update timestamp
    """

    name: str
    description: Optional[str] = None
    tags: Set[str] = Field(default_factory=set)
    permissions: Dict[str, PermissionLevel] = Field(default_factory=dict)

    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class DeleteSchema(BaseModel):
    """Base schema for deleted resources.

    Attributes:
        name: Name of the deleted resource
        delete_time: Deletion timestamp
    """

    name: str
    delete_time: datetime = Field(default_factory=datetime.now)


class UpdateDescriptionSchema(BaseModel):
    """Schema for updating resource descriptions.

    Attributes:
        name: Name of the resource
        description: New description text
        update_time: Update timestamp
    """

    name: str
    description: str
    update_time: datetime = Field(default_factory=datetime.now)


class MoveSchema(BaseModel):
    """Schema for moving resources between containers.

    Attributes:
        name: Name of the resource
        new_parent: New parent container name
        update_time: Move operation timestamp
    """

    name: str
    new_parent: str
    update_time: datetime = Field(default_factory=datetime.now)


class PaginationParams(BaseModel):
    """Parameters for paginated requests.

    Attributes:
        page: Page number (1-based)
        page_size: Number of items per page
    """

    page: int = 1
    page_size: int = 10


class PaginatedResponse(BaseModel):
    """Response schema for paginated results.

    Attributes:
        items: List of items on the current page
        total: Total number of items
        page: Current page number
        page_size: Number of items per page
        total_pages: Total number of pages
    """

    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class KnowledgeSchema(CreateSchema):
    """Schema for knowledge storage.

    Represents a top-level container for organizing corporate knowledge.
    """

    pass


class KnowledgeDetailSchema(KnowledgeSchema):
    """Detailed schema for knowledge storage including contents.

    Attributes:
        list_category: List of categories in the storage
        list_subcategory: List of subcategories in the storage
        list_item: List of items in the storage
    """

    list_category: Optional[List[CategorySchema]]
    list_subcategory: Optional[List[SubCategorySchema]]
    list_item: Optional[List[ItemDetailSchema]]


class KnowledgeRenameSchema(KnowledgeSchema):
    """Schema for renamed knowledge storage.

    Attributes:
        old_name: Previous name of the storage
    """

    old_name: str


class KnowledgeDeleteSchema(DeleteSchema):
    """Schema for deleted knowledge storage."""

    pass


class KnowledgeUpdateDescriptionSchema(UpdateDescriptionSchema):
    """Schema for updated knowledge storage description."""

    pass


class CategorySchema(CreateSchema):
    """Schema for knowledge category.

    Attributes:
        knowledge_storage: Name of the parent storage
    """

    knowledge_storage: str


class CategoryDetailSchema(CategorySchema):
    """Detailed schema for knowledge category including contents.

    Attributes:
        list_subcategory: List of subcategories in the category
        list_item: List of items in the category
    """

    list_subcategory: Optional[List[SubCategorySchema]]
    list_item: Optional[List[ItemSchema]]


class CategoryRenameSchema(CategorySchema):
    """Schema for renamed category.

    Attributes:
        old_name: Previous name of the category
    """

    old_name: str


class CategoryDeleteSchema(DeleteSchema):
    """Schema for deleted category."""

    pass


class CategoryUpdateDescriptionSchema(UpdateDescriptionSchema):
    """Schema for updated category description.

    Attributes:
        knowledge_storage: Name of the parent storage
    """

    knowledge_storage: str


class CategoryMoveSchema(MoveSchema):
    """Schema for moved category.

    Attributes:
        knowledge_storage: Name of the parent storage
    """

    knowledge_storage: str


class SubCategorySchema(CategorySchema):
    """Schema for knowledge subcategory.

    Attributes:
        category: Name of the parent category
    """

    category: str


class SubCategoryDetailSchema(SubCategorySchema):
    """Detailed schema for knowledge subcategory including contents.

    Attributes:
        list_item: List of items in the subcategory
    """

    list_item: Optional[List[ItemSchema]]


class SubCategoryRenameSchema(CategoryRenameSchema):
    """Schema for renamed subcategory."""

    pass


class SubCategoryDeleteSchema(CategoryDeleteSchema):
    """Schema for deleted subcategory."""

    pass


class SubCategoryUpdateDescriptionSchema(UpdateDescriptionSchema):
    """Schema for updated subcategory description.

    Attributes:
        knowledge_storage: Name of the parent storage
        category: Name of the parent category
    """

    knowledge_storage: str
    category: str


class SubCategoryMoveSchema(MoveSchema):
    """Schema for moved subcategory.

    Attributes:
        knowledge_storage: Name of the parent storage
        category: Name of the parent category
    """

    knowledge_storage: str
    category: str


class ItemSchema(BaseModel):
    """Base schema for knowledge items (documents or URLs).

    Attributes:
        name: Name of the item
        url: URL or path to the item content
        tags: Set of tags for categorization
        version: Current version number
        permissions: Dictionary of user permissions
        create_time: Creation timestamp
        update_time: Last update timestamp
    """

    name: str
    url: str
    tags: Set[str] = Field(default_factory=set)
    version: int = 1
    permissions: Dict[str, PermissionLevel] = Field(default_factory=dict)

    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class ItemCreateSchema(ItemSchema):
    """Schema for creating new items.

    Attributes:
        subcategory: Optional parent subcategory name
        category: Name of the parent category
        knowledge_storage: Name of the parent storage
    """

    subcategory: Optional[str] = None
    category: str
    knowledge_storage: str


class ItemDetailSchema(ItemCreateSchema):
    """Detailed schema for items including metadata.

    Attributes:
        size: Size of the item in bytes
        content_type: MIME type of the item
        versions: List of available version numbers
    """

    knowledge_storage: str
    category: str
    size: Optional[int] = None
    content_type: Optional[str] = None
    versions: List[int] = Field(default_factory=list)


class ItemRenameSchema(ItemSchema):
    """Schema for renamed items.

    Attributes:
        old_name: Previous name of the item
    """

    old_name: str


class ItemDeleteSchema(DeleteSchema):
    """Schema for deleted items."""

    pass


class ItemUpdateDescriptionSchema(UpdateDescriptionSchema):
    """Schema for updated item description.

    Attributes:
        knowledge_storage: Name of the parent storage
        category: Name of the parent category
        subcategory: Optional parent subcategory name
    """

    knowledge_storage: str
    category: str
    subcategory: Optional[str] = None


class ItemMoveSchema(MoveSchema):
    """Schema for moved items.

    Attributes:
        knowledge_storage: Name of the parent storage
        category: Name of the parent category
        subcategory: Optional parent subcategory name
    """

    knowledge_storage: str
    category: str
    subcategory: Optional[str] = None


class ItemVersionSchema(BaseModel):
    """Schema for item versions.

    Attributes:
        version: Version number
        url: URL or path to the version content
        create_time: Version creation timestamp
        size: Size of the version in bytes
        content_type: MIME type of the version
    """

    version: int
    url: str
    create_time: datetime
    size: Optional[int] = None
    content_type: Optional[str] = None


class SmartSearchSchema(BaseModel):
    """Schema for smart search results.

    Attributes:
        text: Relevant text snippet
        item_path: Path to the item containing the result
        num_page_in_item: Optional page number in the item
        metadata: Additional metadata about the result
        relevance_score: Score indicating result relevance
    """

    text: str
    item_path: str
    num_page_in_item: Optional[int] = None
    metadata: Dict[str, Any]
    relevance_score: float


class SmartSearchResponseSchema(BaseModel):
    """Schema for smart search response.

    Attributes:
        query: Original search query
        results: List of search results
        total_results: Total number of results found
        execution_time: Search execution time in seconds
    """

    query: str
    results: List[SmartSearchSchema]
    total_results: int
    execution_time: float
