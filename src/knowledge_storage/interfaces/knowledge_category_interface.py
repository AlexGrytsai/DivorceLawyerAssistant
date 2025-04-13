from abc import ABC, abstractmethod
from typing import List, Optional, Union, Dict, Any, Set, Tuple

from fastapi import UploadFile
from pydantic import HttpUrl

from src.knowledge_storage.interfaces import (
    BaseEntityInterface,
    TaggableInterface,
    PermissionInterface,
    VersionalInterface,
    SearchableInterface,
)
from src.knowledge_storage.schemas import (
    CategoryDeleteSchema,
    CategorySchema,
    CategoryRenameSchema,
    SubCategorySchema,
    SubCategoryDeleteSchema,
    SubCategoryRenameSchema,
    ItemCreateSchema,
    ItemDeleteSchema,
    ItemRenameSchema,
    ItemDetailSchema,
    CategoryDetailSchema,
    ItemSchema,
    SubCategoryDetailSchema,
    SmartSearchResponseSchema,
    CategoryUpdateDescriptionSchema,
    CategoryMoveSchema,
    SubCategoryUpdateDescriptionSchema,
    SubCategoryMoveSchema,
    ItemUpdateDescriptionSchema,
    ItemMoveSchema,
    ItemVersionSchema,
    PaginationParams,
    PaginatedResponse,
    PermissionLevel,
)


class KnowledgeCategoryInterface(
    BaseEntityInterface[Tuple[str, str], str, CategorySchema],
    TaggableInterface[str, CategorySchema],
    PermissionInterface[str, CategorySchema],
    VersionalInterface[str],
    SearchableInterface[str],
    ABC,
):
    """
    Interface for managing knowledge categories and their contents.

    This interface defines the contract for implementing knowledge
    category systems, which organize content within knowledge storages.
    It provides methods for managing categories, subcategories, and items,
    including their metadata, permissions, and search capabilities.
    """

    @abstractmethod
    async def create_category(
        self, storage_name: str, name: str, description: Optional[str] = None
    ) -> CategorySchema:
        """
        Create a new category within a storage.

        Args:
            storage_name: Name of the parent storage
            name: Unique name for the category
            description: Optional description of the category

        Returns:
            CategorySchema containing category details
        """
        pass

    @abstractmethod
    async def rename_category(
        self, storage_name: str, old_name: str, new_name: str
    ) -> CategoryRenameSchema:
        """
        Rename an existing category.

        Args:
            storage_name: Name of the parent storage
            old_name: Current name of the category
            new_name: New name for the category

        Returns:
            CategoryRenameSchema with rename operation details
        """
        pass

    @abstractmethod
    async def delete_category(
        self, storage_name: str, name: str
    ) -> CategoryDeleteSchema:
        """
        Delete a category and all its contents.

        Args:
            storage_name: Name of the parent storage
            name: Name of the category to delete

        Returns:
            CategoryDeleteSchema with deletion details
        """
        pass

    @abstractmethod
    async def get_category(
        self, storage_name: str, name: str, is_detail: bool = False
    ) -> Union[CategorySchema, CategoryDetailSchema]:
        """
        Retrieve a category by name.

        Args:
            storage_name: Name of the parent storage
            name: Name of the category to retrieve
            is_detail: If True, returns detailed information including contents

        Returns:
            Category information, optionally with detailed contents
        """
        pass

    @abstractmethod
    async def list_categories(
        self, storage_name: str, pagination: Optional[PaginationParams] = None
    ) -> Union[List[CategorySchema], PaginatedResponse]:
        """
        List all categories in a storage.

        Args:
            storage_name: Name of the parent storage
            pagination: Optional pagination parameters

        Returns:
            List of categories or paginated response
        """
        pass

    @abstractmethod
    async def update_category_description(
        self, storage_name: str, name: str, description: str
    ) -> CategoryUpdateDescriptionSchema:
        """
        Update the description of a category.

        Args:
            storage_name: Name of the parent storage
            name: Name of the category to update
            description: New description text

        Returns:
            CategoryUpdateDescriptionSchema with update details
        """
        pass

    @abstractmethod
    async def move_category(
        self, storage_name: str, name: str, new_storage_name: str
    ) -> CategoryMoveSchema:
        """
        Move a category to a different storage.

        Args:
            storage_name: Current parent storage name
            name: Name of the category to move
            new_storage_name: Target storage name

        Returns:
            CategoryMoveSchema with move operation details
        """
        pass

    @abstractmethod
    async def set_category_permission(
        self,
        storage_name: str,
        name: str,
        user_id: str,
        permission: PermissionLevel,
    ) -> CategorySchema:
        """
        Set the permission level for a user on a category.

        Args:
            storage_name: Name of the parent storage
            name: Name of the category
            user_id: ID of the user
            permission: Permission level to set

        Returns:
            Updated category information
        """
        pass

    @abstractmethod
    async def remove_category_permission(
        self, storage_name: str, name: str, user_id: str
    ) -> CategorySchema:
        """
        Remove user permissions from a category.

        Args:
            storage_name: Name of the parent storage
            name: Name of the category
            user_id: ID of the user

        Returns:
            Updated category information
        """
        pass

    @abstractmethod
    async def add_category_tag(
        self, storage_name: str, name: str, tag: str
    ) -> CategorySchema:
        """
        Add a tag to a category.

        Args:
            storage_name: Name of the parent storage
            name: Name of the category
            tag: Tag to add

        Returns:
            Updated category information
        """
        pass

    @abstractmethod
    async def remove_category_tag(
        self, storage_name: str, name: str, tag: str
    ) -> CategorySchema:
        """
        Remove a tag from a category.

        Args:
            storage_name: Name of the parent storage
            name: Name of the category
            tag: Tag to remove

        Returns:
            Updated category information
        """
        pass

    @abstractmethod
    async def create_subcategory(
        self,
        storage_name: str,
        category_name: str,
        subcategory_name: str,
        description: Optional[str] = None,
    ) -> SubCategorySchema:
        """
        Create a new subcategory within a category.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            subcategory_name: Unique name for the subcategory
            description: Optional description of the subcategory

        Returns:
            SubCategorySchema containing subcategory details
        """
        pass

    @abstractmethod
    async def delete_subcategory(
        self, storage_name: str, category_name: str, subcategory_name: str
    ) -> SubCategoryDeleteSchema:
        """
        Delete a subcategory and all its contents.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            subcategory_name: Name of the subcategory to delete

        Returns:
            SubCategoryDeleteSchema with deletion details
        """
        pass

    @abstractmethod
    async def rename_subcategory(
        self,
        storage_name: str,
        category_name: str,
        old_subcategory_name: str,
        new_subcategory_name: str,
    ) -> SubCategoryRenameSchema:
        """
        Rename an existing subcategory.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            old_subcategory_name: Current name of the subcategory
            new_subcategory_name: New name for the subcategory

        Returns:
            SubCategoryRenameSchema with rename operation details
        """
        pass

    @abstractmethod
    async def get_subcategory(
        self,
        storage_name: str,
        category_name: str,
        subcategory_name: str,
        is_detail: bool = False,
    ) -> Union[SubCategoryDetailSchema, SubCategorySchema]:
        """
        Retrieve a subcategory by name.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            subcategory_name: Name of the subcategory to retrieve
            is_detail: If True, returns detailed information including contents

        Returns:
            Subcategory information, optionally with detailed contents
        """
        pass

    @abstractmethod
    async def list_subcategories(
        self,
        storage_name: str,
        category_name: str,
        pagination: Optional[PaginationParams] = None,
    ) -> Union[List[SubCategorySchema], PaginatedResponse]:
        """
        List all subcategories in a category.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            pagination: Optional pagination parameters

        Returns:
            List of subcategories or paginated response
        """
        pass

    @abstractmethod
    async def update_subcategory_description(
        self,
        storage_name: str,
        category_name: str,
        subcategory_name: str,
        description: str,
    ) -> SubCategoryUpdateDescriptionSchema:
        """
        Update the description of a subcategory.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            subcategory_name: Name of the subcategory to update
            description: New description text

        Returns:
            SubCategoryUpdateDescriptionSchema with update details
        """
        pass

    @abstractmethod
    async def move_subcategory(
        self,
        storage_name: str,
        category_name: str,
        subcategory_name: str,
        new_category_name: str,
    ) -> SubCategoryMoveSchema:
        """
        Move a subcategory to a different category.

        Args:
            storage_name: Name of the parent storage
            category_name: Current parent category name
            subcategory_name: Name of the subcategory to move
            new_category_name: Target category name

        Returns:
            SubCategoryMoveSchema with move operation details
        """
        pass

    @abstractmethod
    async def set_subcategory_permission(
        self,
        storage_name: str,
        category_name: str,
        subcategory_name: str,
        user_id: str,
        permission: PermissionLevel,
    ) -> SubCategorySchema:
        """
        Set the permission level for a user on a subcategory.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            subcategory_name: Name of the subcategory
            user_id: ID of the user
            permission: Permission level to set

        Returns:
            Updated subcategory information
        """
        pass

    @abstractmethod
    async def remove_subcategory_permission(
        self,
        storage_name: str,
        category_name: str,
        subcategory_name: str,
        user_id: str,
    ) -> SubCategorySchema:
        """
        Remove user permissions from a subcategory.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            subcategory_name: Name of the subcategory
            user_id: ID of the user

        Returns:
            Updated subcategory information
        """
        pass

    @abstractmethod
    async def add_subcategory_tag(
        self,
        storage_name: str,
        category_name: str,
        subcategory_name: str,
        tag: str,
    ) -> SubCategorySchema:
        """
        Add a tag to a subcategory.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            subcategory_name: Name of the subcategory
            tag: Tag to add

        Returns:
            Updated subcategory information
        """
        pass

    @abstractmethod
    async def remove_subcategory_tag(
        self,
        storage_name: str,
        category_name: str,
        subcategory_name: str,
        tag: str,
    ) -> SubCategorySchema:
        """
        Remove a tag from a subcategory.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            subcategory_name: Name of the subcategory
            tag: Tag to remove

        Returns:
            Updated subcategory information
        """
        pass

    @abstractmethod
    async def create_item(
        self,
        storage_name: str,
        category_name: str,
        item_name: str,
        item: Union[HttpUrl, str, UploadFile],
        subcategory_name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[Set[str]] = None,
    ) -> ItemCreateSchema:
        """
        Create a new item (document or URL) in a category or subcategory.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            item_name: Unique name for the item
            item: Content to store (URL, file path, or file object)
            subcategory_name: Optional parent subcategory name
            description: Optional description of the item
            tags: Optional set of tags for the item

        Returns:
            ItemCreateSchema containing item details
        """
        pass

    @abstractmethod
    async def create_items(
        self,
        storage_name: str,
        category_name: str,
        items: List[tuple[str, Union[HttpUrl, str, UploadFile]]],
        subcategory_name: Optional[str] = None,
    ) -> List[ItemCreateSchema]:
        """
        Create multiple items in a category or subcategory.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            items: List of (name, content) tuples to create
            subcategory_name: Optional parent subcategory name

        Returns:
            List of ItemCreateSchema containing created items details
        """
        pass

    @abstractmethod
    async def rename_item(
        self,
        storage_name: str,
        category_name: str,
        item_name: str,
        new_item_name: str,
        subcategory_name: Optional[str] = None,
    ) -> ItemRenameSchema:
        """
        Rename an existing item.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            item_name: Current name of the item
            new_item_name: New name for the item
            subcategory_name: Optional parent subcategory name

        Returns:
            ItemRenameSchema with rename operation details
        """
        pass

    @abstractmethod
    async def delete_item(
        self,
        storage_name: str,
        category_name: str,
        item_name: str,
        subcategory_name: Optional[str] = None,
    ) -> ItemDeleteSchema:
        """
        Delete an item.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            item_name: Name of the item to delete
            subcategory_name: Optional parent subcategory name

        Returns:
            ItemDeleteSchema with deletion details
        """
        pass

    @abstractmethod
    async def get_item(
        self,
        storage_name: str,
        category_name: str,
        item_name: str,
        is_detail: bool = False,
        subcategory_name: Optional[str] = None,
    ) -> Union[ItemSchema, ItemDetailSchema]:
        """
        Retrieve an item by name.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            item_name: Name of the item to retrieve
            is_detail: If True, returns detailed information
            subcategory_name: Optional parent subcategory name

        Returns:
            Item information, optionally with detailed contents
        """
        pass

    @abstractmethod
    async def list_items(
        self,
        storage_name: str,
        category_name: str,
        subcategory_name: Optional[str] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> Union[List[ItemDetailSchema], PaginatedResponse]:
        """List all items in a category or subcategory.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            subcategory_name: Optional parent subcategory name
            pagination: Optional pagination parameters

        Returns:
            List of items or paginated response
        """
        pass

    @abstractmethod
    async def update_item_description(
        self,
        storage_name: str,
        category_name: str,
        item_name: str,
        description: str,
        subcategory_name: Optional[str] = None,
    ) -> ItemUpdateDescriptionSchema:
        """
        Update the description of an item.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            item_name: Name of the item to update
            description: New description text
            subcategory_name: Optional parent subcategory name

        Returns:
            ItemUpdateDescriptionSchema with update details
        """
        pass

    @abstractmethod
    async def move_item(
        self,
        storage_name: str,
        category_name: str,
        item_name: str,
        new_category_name: str,
        new_subcategory_name: Optional[str] = None,
        subcategory_name: Optional[str] = None,
    ) -> ItemMoveSchema:
        """
        Move an item to a different category or subcategory.

        Args:
            storage_name: Name of the parent storage
            category_name: Current parent category name
            item_name: Name of the item to move
            new_category_name: Target category name
            new_subcategory_name: Optional target subcategory name
            subcategory_name: Optional current parent subcategory name

        Returns:
            ItemMoveSchema with move operation details
        """
        pass

    @abstractmethod
    async def set_item_permission(
        self,
        storage_name: str,
        category_name: str,
        item_name: str,
        user_id: str,
        permission: PermissionLevel,
        subcategory_name: Optional[str] = None,
    ) -> ItemSchema:
        """
        Set the permission level for a user on an item.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            item_name: Name of the item
            user_id: ID of the user
            permission: Permission level to set
            subcategory_name: Optional parent subcategory name

        Returns:
            Updated item information
        """
        pass

    @abstractmethod
    async def remove_item_permission(
        self,
        storage_name: str,
        category_name: str,
        item_name: str,
        user_id: str,
        subcategory_name: Optional[str] = None,
    ) -> ItemSchema:
        """
        Remove user permissions from an item.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            item_name: Name of the item
            user_id: ID of the user
            subcategory_name: Optional parent subcategory name

        Returns:
            Updated item information
        """
        pass

    @abstractmethod
    async def add_item_tag(
        self,
        storage_name: str,
        category_name: str,
        item_name: str,
        tag: str,
        subcategory_name: Optional[str] = None,
    ) -> ItemSchema:
        """
        Add a tag to an item.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            item_name: Name of the item
            tag: Tag to add
            subcategory_name: Optional parent subcategory name

        Returns:
            Updated item information
        """
        pass

    @abstractmethod
    async def remove_item_tag(
        self,
        storage_name: str,
        category_name: str,
        item_name: str,
        tag: str,
        subcategory_name: Optional[str] = None,
    ) -> ItemSchema:
        """
        Remove a tag from an item.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            item_name: Name of the item
            tag: Tag to remove
            subcategory_name: Optional parent subcategory name

        Returns:
            Updated item information
        """
        pass

    @abstractmethod
    async def update_item_version(
        self,
        storage_name: str,
        category_name: str,
        item_name: str,
        new_version: Union[HttpUrl, str, UploadFile],
        subcategory_name: Optional[str] = None,
    ) -> ItemVersionSchema:
        """
        Create a new version of an item.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            item_name: Name of the item
            new_version: New content for the version
            subcategory_name: Optional parent subcategory name

        Returns:
            ItemVersionSchema with version details
        """
        pass

    @abstractmethod
    async def get_item_versions(
        self,
        storage_name: str,
        category_name: str,
        item_name: str,
        subcategory_name: Optional[str] = None,
    ) -> List[ItemVersionSchema]:
        """
        Get all versions of an item.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            item_name: Name of the item
            subcategory_name: Optional parent subcategory name

        Returns:
            List of item versions
        """
        pass

    @abstractmethod
    async def search_items(
        self,
        storage_name: str,
        category_name: str,
        query: str,
        case_sensitive: bool = False,
        subcategory_name: Optional[str] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> Union[List[ItemDetailSchema], PaginatedResponse]:
        """
        Search for items by name.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            query: Search query
            case_sensitive: Whether to perform case-sensitive search
            subcategory_name: Optional parent subcategory name
            pagination: Optional pagination parameters

        Returns:
            List of matching items or paginated response
        """
        pass

    @abstractmethod
    async def smart_search(
        self,
        storage_name: str,
        query: str,
        category_name: Optional[str] = None,
        num_results: int = 3,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SmartSearchResponseSchema:
        """
        Perform semantic search across items.

        Args:
            storage_name: Name of the parent storage
            query: Search query
            category_name: Optional category to limit search to
            num_results: Maximum number of results to return
            filters: Optional search filters

        Returns:
            SmartSearchResponseSchema with search results
        """
        pass
