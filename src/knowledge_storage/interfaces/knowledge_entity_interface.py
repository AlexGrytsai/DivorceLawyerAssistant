from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Union, List

from src.knowledge_storage.schemas import (
    CategorySchema,
    SubCategorySchema,
    CategoryRenameSchema,
    SubCategoryRenameSchema,
    CategoryDeleteSchema,
    SubCategoryDeleteSchema,
    CategoryDetailSchema,
    SubCategoryDetailSchema,
    CategoryUpdateDescriptionSchema,
    SubCategoryUpdateDescriptionSchema,
    CategoryMoveSchema,
    SubCategoryMoveSchema,
    PaginationParams,
    PaginatedResponse,
    PermissionLevel,
)


class EntityType(Enum):
    CATEGORY = "category"
    SUBCATEGORY = "subcategory"


class KnowledgeEntityInterface(ABC):
    @abstractmethod
    async def create_entity(
        self,
        storage_name: str,
        parent_name: Optional[str],
        name: str,
        description: Optional[str],
        entity_type: EntityType,
    ) -> Union[CategorySchema, SubCategorySchema]:
        """Generic entity creation method."""
        pass

    @abstractmethod
    async def rename_entity(
        self,
        storage_name: str,
        parent_name: Optional[str],
        old_name: str,
        new_name: str,
        entity_type: EntityType,
    ) -> Union[CategoryRenameSchema, SubCategoryRenameSchema]:
        """Generic entity rename method."""
        pass

    @abstractmethod
    async def delete_entity(
        self,
        storage_name: str,
        parent_name: Optional[str],
        name: str,
        entity_type: EntityType,
    ) -> Union[CategoryDeleteSchema, SubCategoryDeleteSchema]:
        """Generic entity deletion method."""
        pass

    @abstractmethod
    async def get_entity(
        self,
        storage_name: str,
        parent_name: Optional[str],
        name: str,
        is_detail: bool,
        entity_type: EntityType,
    ) -> Union[
        CategorySchema,
        SubCategorySchema,
        CategoryDetailSchema,
        SubCategoryDetailSchema,
    ]:
        """Generic entity retrieval method."""
        pass

    @abstractmethod
    async def list_entities(
        self,
        storage_name: str,
        parent_name: Optional[str],
        pagination: Optional[PaginationParams],
        entity_type: EntityType,
    ) -> Union[
        List[Union[CategorySchema, SubCategorySchema]], PaginatedResponse
    ]:
        """Generic entity listing method."""
        pass

    @abstractmethod
    async def update_entity_description(
        self,
        storage_name: str,
        parent_name: Optional[str],
        name: str,
        description: str,
        entity_type: EntityType,
    ) -> Union[
        CategoryUpdateDescriptionSchema, SubCategoryUpdateDescriptionSchema
    ]:
        """Generic entity description update method."""
        pass

    @abstractmethod
    async def move_entity(
        self,
        storage_name: str,
        parent_name: Optional[str],
        name: str,
        new_parent_name: str,
        entity_type: EntityType,
    ) -> Union[CategoryMoveSchema, SubCategoryMoveSchema]:
        """Generic entity move method."""
        pass

    @abstractmethod
    async def set_entity_permission(
        self,
        storage_name: str,
        parent_name: Optional[str],
        name: str,
        user_id: str,
        permission: PermissionLevel,
        entity_type: EntityType,
    ) -> Union[CategorySchema, SubCategorySchema]:
        """Generic entity permission setting method."""
        pass

    @abstractmethod
    async def remove_entity_permission(
        self,
        storage_name: str,
        parent_name: Optional[str],
        name: str,
        user_id: str,
        entity_type: EntityType,
    ) -> Union[CategorySchema, SubCategorySchema]:
        """Generic entity permission removal method."""
        pass

    @abstractmethod
    async def add_entity_tag(
        self,
        storage_name: str,
        parent_name: Optional[str],
        name: str,
        tag: str,
        entity_type: EntityType,
    ) -> Union[CategorySchema, SubCategorySchema]:
        """Generic entity tag addition method."""
        pass

    @abstractmethod
    async def remove_entity_tag(
        self,
        storage_name: str,
        parent_name: Optional[str],
        name: str,
        tag: str,
        entity_type: EntityType,
    ) -> Union[CategorySchema, SubCategorySchema]:
        """Generic entity tag removal method."""
        pass
