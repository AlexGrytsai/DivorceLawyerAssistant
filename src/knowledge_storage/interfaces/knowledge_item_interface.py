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
    ItemCreateSchema,
    ItemDeleteSchema,
    ItemRenameSchema,
    ItemDetailSchema,
    ItemSchema,
    SmartSearchResponseSchema,
    ItemUpdateDescriptionSchema,
    ItemMoveSchema,
    ItemVersionSchema,
    PaginationParams,
    PaginatedResponse,
    PermissionLevel,
)


class KnowledgeItemInterface(
    BaseEntityInterface[Tuple[str, str], str, ItemSchema],
    TaggableInterface[str, ItemSchema],
    PermissionInterface[str, ItemSchema],
    VersionalInterface[str],
    SearchableInterface[str],
    ABC,
):
    """
    Interface for managing knowledge items (documents, URLs) in a storage
    system.

    This interface provides methods for:
    - Creating, renaming, and deleting items
    - Managing item descriptions and metadata
    - Moving items between categories/subcategories
    - Setting and managing permissions
    - Adding and removing tags
    - Version control for items
    - Searching and retrieving item information

    Items are organized in a hierarchical structure:
    Storage -> Category -> Subcategory -> Item
    """

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

        Raises:
            CategoryNotFoundError: If parent category does not exist
            SubCategoryNotFoundError: If specified subcategory does not exist
            ValueError: If item name is invalid or already exists
            PermissionError: If user lacks create permissions
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

        Raises:
            CategoryNotFoundError: If parent category does not exist
            SubCategoryNotFoundError: If specified subcategory does not exist
            ValueError: If any item name is invalid or already exists
            PermissionError: If user lacks create permissions
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

        Raises:
            ItemNotFoundError: If item does not exist
            ValueError: If new name is invalid or already exists
            PermissionError: If user lacks rename permissions
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

        Raises:
            ItemNotFoundError: If item does not exist
            PermissionError: If user lacks delete permissions
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

        Raises:
            ItemNotFoundError: If item does not exist
            PermissionError: If user lacks read permissions
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
        """
        List all items in a category or subcategory.

        Args:
            storage_name: Name of the parent storage
            category_name: Name of the parent category
            subcategory_name: Optional parent subcategory name
            pagination: Optional pagination parameters

        Returns:
            List of items or paginated response

        Raises:
            CategoryNotFoundError: If category does not exist
            SubCategoryNotFoundError: If subcategory does not exist
            PermissionError: If user lacks list permissions
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

        Raises:
            ItemNotFoundError: If item does not exist
            PermissionError: If user lacks update permissions
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

        Raises:
            ItemNotFoundError: If item does not exist
            CategoryNotFoundError: If target category does not exist
            SubCategoryNotFoundError: If target subcategory does not exist
            PermissionError: If user lacks move permissions
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
            permission: Permission level to set (READ, WRITE, ADMIN)
            subcategory_name: Optional parent subcategory name

        Returns:
            Updated item information

        Raises:
            ItemNotFoundError: If item does not exist
            UserNotFoundError: If user does not exist
            PermissionError: If current user lacks permission management rights
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

        Raises:
            ItemNotFoundError: If item does not exist
            UserNotFoundError: If user does not exist
            PermissionError: If current user lacks permission management rights
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
            tag: Tag to add. Must be alphanumeric with optional underscores
            subcategory_name: Optional parent subcategory name

        Returns:
            Updated item information

        Raises:
            ItemNotFoundError: If item does not exist
            ValueError: If tag format is invalid
            PermissionError: If user lacks update permissions
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

        Raises:
            ItemNotFoundError: If item does not exist
            ValueError: If tag does not exist
            PermissionError: If user lacks update permissions
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

        Raises:
            ItemNotFoundError: If item does not exist
            ValueError: If new version is invalid
            PermissionError: If user lacks update permissions
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

        Raises:
            ItemNotFoundError: If item does not exist
            PermissionError: If user lacks read permissions
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

        Raises:
            CategoryNotFoundError: If category does not exist
            SubCategoryNotFoundError: If subcategory does not exist
            PermissionError: If user lacks search permissions
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

        Raises:
            CategoryNotFoundError: If specified category does not exist
            PermissionError: If user lacks search permissions
        """
        pass
