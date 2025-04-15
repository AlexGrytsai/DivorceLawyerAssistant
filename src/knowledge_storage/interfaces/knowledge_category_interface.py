from abc import ABC, abstractmethod
from typing import List, Optional, Union, Tuple

from src.knowledge_storage.interfaces import (
    BaseEntityInterface,
    TaggableInterface,
    PermissionInterface,
)
from src.knowledge_storage.schemas import (
    CategoryDeleteSchema,
    CategorySchema,
    CategoryRenameSchema,
    SubCategorySchema,
    SubCategoryDeleteSchema,
    SubCategoryRenameSchema,
    CategoryDetailSchema,
    SubCategoryDetailSchema,
    CategoryUpdateDescriptionSchema,
    CategoryMoveSchema,
    SubCategoryUpdateDescriptionSchema,
    SubCategoryMoveSchema,
    PaginationParams,
    PaginatedResponse,
    PermissionLevel,
)


class KnowledgeCategoryInterface(
    BaseEntityInterface[Tuple[str, str], str, CategorySchema],
    TaggableInterface[str, CategorySchema],
    PermissionInterface[str, CategorySchema],
    ABC,
):
    """
    Interface for managing knowledge categories and subcategories in
    a storage system.

    This interface provides methods for:
    - Creating, renaming, and deleting categories and subcategories
    - Managing category descriptions and metadata
    - Moving categories between storages
    - Setting and managing permissions
    - Adding and removing tags
    - Listing and retrieving category information

    Categories are organized in a hierarchical structure:
    Storage -> Category -> Subcategory
    """

    @abstractmethod
    async def create_category(
        self, storage_name: str, name: str, description: Optional[str] = None
    ) -> CategorySchema:
        """
        Create a new category within a storage.

        Args:
            storage_name: Name of the parent storage where the category
                          will be created
            name: Unique name for the category.
                  Must not contain special characters
            description: Optional description of the category's purpose
                         and contents

        Returns:
            CategorySchema containing the created category's details

        Raises:
            ValueError: If category name is invalid or already exists
            StorageNotFoundError: If parent storage does not exist
        """
        pass

    @abstractmethod
    async def rename_category(
        self, storage_name: str, old_name: str, new_name: str
    ) -> CategoryRenameSchema:
        """
        Rename an existing category.

        Args:
            storage_name: Name of the parent storage containing the category
            old_name: Current name of the category to rename
            new_name: New name for the category.
                      Must be unique within the storage

        Returns:
            CategoryRenameSchema with details of the rename operation

        Raises:
            ValueError: If new name is invalid or already exists
            CategoryNotFoundError: If category does not exist
        """
        pass

    @abstractmethod
    async def delete_category(
        self, storage_name: str, name: str
    ) -> CategoryDeleteSchema:
        """
        Delete a category and all its contents.

        Args:
            storage_name: Name of the parent storage containing the category
            name: Name of the category to delete

        Returns:
            CategoryDeleteSchema with details of the deletion operation

        Raises:
            CategoryNotFoundError: If category does not exist
            PermissionError: If user lacks delete permissions
        """
        pass

    @abstractmethod
    async def get_category(
        self, storage_name: str, name: str, is_detail: bool = False
    ) -> Union[CategorySchema, CategoryDetailSchema]:
        """
        Retrieve a category by name.

        Args:
            storage_name: Name of the parent storage containing the category
            name: Name of the category to retrieve
            is_detail: If True, returns detailed information including contents
                       and metadata

        Returns:
            Category information, optionally with detailed contents

        Raises:
            CategoryNotFoundError: If category does not exist
            PermissionError: If user lacks read permissions
        """
        pass

    @abstractmethod
    async def list_categories(
        self, storage_name: str, pagination: Optional[PaginationParams] = None
    ) -> Union[List[CategorySchema], PaginatedResponse]:
        """
        List all categories in a storage.

        Args:
            storage_name: Name of the storage to list categories from
            pagination: Optional parameters for paginated results

        Returns:
            List of categories or paginated response

        Raises:
            StorageNotFoundError: If storage does not exist
            PermissionError: If user lacks list permissions
        """
        pass

    @abstractmethod
    async def update_category_description(
        self, storage_name: str, name: str, description: str
    ) -> CategoryUpdateDescriptionSchema:
        """
        Update the description of a category.

        Args:
            storage_name: Name of the parent storage containing the category
            name: Name of the category to update
            description: New description text

        Returns:
            CategoryUpdateDescriptionSchema with update details

        Raises:
            CategoryNotFoundError: If category does not exist
            PermissionError: If user lacks update permissions
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

        Raises:
            CategoryNotFoundError: If category does not exist
            StorageNotFoundError: If target storage does not exist
            PermissionError: If user lacks move permissions
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
            storage_name: Name of the parent storage containing the category
            name: Name of the category
            user_id: ID of the user to set permissions for
            permission: Permission level to set (READ, WRITE, ADMIN)

        Returns:
            Updated category information

        Raises:
            CategoryNotFoundError: If category does not exist
            UserNotFoundError: If user does not exist
            PermissionError: If current user lacks permission management rights
        """
        pass

    @abstractmethod
    async def remove_category_permission(
        self, storage_name: str, name: str, user_id: str
    ) -> CategorySchema:
        """
        Remove user permissions from a category.

        Args:
            storage_name: Name of the parent storage containing the category
            name: Name of the category
            user_id: ID of the user to remove permissions from

        Returns:
            Updated category information

        Raises:
            CategoryNotFoundError: If category does not exist
            UserNotFoundError: If user does not exist
            PermissionError: If current user lacks permission management rights
        """
        pass

    @abstractmethod
    async def add_category_tag(
        self, storage_name: str, name: str, tag: str
    ) -> CategorySchema:
        """
        Add a tag to a category.

        Args:
            storage_name: Name of the parent storage containing the category
            name: Name of the category
            tag: Tag to add. Must be alphanumeric with optional underscores

        Returns:
            Updated category information

        Raises:
            CategoryNotFoundError: If category does not exist
            ValueError: If tag format is invalid
            PermissionError: If user lacks update permissions
        """
        pass

    @abstractmethod
    async def remove_category_tag(
        self, storage_name: str, name: str, tag: str
    ) -> CategorySchema:
        """
        Remove a tag from a category.

        Args:
            storage_name: Name of the parent storage containing the category
            name: Name of the category
            tag: Tag to remove

        Returns:
            Updated category information

        Raises:
            CategoryNotFoundError: If category does not exist
            ValueError: If tag does not exist
            PermissionError: If user lacks update permissions
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

        Raises:
            CategoryNotFoundError: If parent category does not exist
            ValueError: If subcategory name is invalid or already exists
            PermissionError: If user lacks create permissions
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

        Raises:
            SubCategoryNotFoundError: If subcategory does not exist
            PermissionError: If user lacks delete permissions
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
