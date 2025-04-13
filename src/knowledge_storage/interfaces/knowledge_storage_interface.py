from abc import ABC, abstractmethod
from typing import List, Union, Optional

from src.knowledge_storage.interfaces import (
    BaseEntityInterface,
    TaggableInterface,
    PermissionInterface,
)
from src.knowledge_storage.schemas import (
    KnowledgeSchema,
    KnowledgeRenameSchema,
    KnowledgeDeleteSchema,
    KnowledgeDetailSchema,
    KnowledgeUpdateDescriptionSchema,
    PaginationParams,
    PaginatedResponse,
    PermissionLevel,
)


class KnowledgeStorageInterface(
    BaseEntityInterface[str, str, KnowledgeSchema],
    TaggableInterface[str, KnowledgeSchema],
    PermissionInterface[str, KnowledgeSchema],
    ABC,
):
    """
    Interface for managing knowledge storage systems.

    This interface defines the contract for implementing knowledge
    storage systems, which serve as top-level containers for organizing
    corporate knowledge.
    Each storage can contain categories, subcategories, and items.
    """

    @abstractmethod
    async def create_storage(
        self, name: str, description: Optional[str] = None
    ) -> KnowledgeSchema:
        """
        Create a new knowledge storage.

        Args:
            name: Unique name for the storage
            description: Optional description of the storage

        Returns:
            KnowledgeSchema containing storage details
        """
        pass

    @abstractmethod
    async def rename_storage(
        self, old_name: str, new_name: str
    ) -> KnowledgeRenameSchema:
        """
        Rename an existing knowledge storage.

        Args:
            old_name: Current name of the storage
            new_name: New name for the storage

        Returns:
            KnowledgeRenameSchema with rename operation details
        """
        pass

    @abstractmethod
    async def delete_storage(self, name: str) -> KnowledgeDeleteSchema:
        """
        Delete a knowledge storage and all its contents.

        Args:
            name: Name of the storage to delete

        Returns:
            KnowledgeDeleteSchema with deletion details
        """
        pass

    @abstractmethod
    async def get_storage(
        self, name: str, is_detail: bool = False
    ) -> Union[KnowledgeSchema, KnowledgeDetailSchema]:
        """
        Retrieve a knowledge storage by name.

        Args:
            name: Name of the storage to retrieve
            is_detail: If True, returns detailed information including contents

        Returns:
            Storage information, optionally with detailed contents
        """
        pass

    @abstractmethod
    async def list_storages(
        self,
        is_detail: bool = False,
        pagination: Optional[PaginationParams] = None,
    ) -> Union[
        List[Union[KnowledgeSchema, KnowledgeDetailSchema]], PaginatedResponse
    ]:
        """
        List all knowledge storages.

        Args:
            is_detail: If True, returns detailed information for each storage
            pagination: Optional pagination parameters

        Returns:
            List of storages or paginated response
        """
        pass

    @abstractmethod
    async def update_storage_description(
        self, name: str, description: str
    ) -> KnowledgeUpdateDescriptionSchema:
        """
        Update the description of a knowledge storage.

        Args:
            name: Name of the storage to update
            description: New description text

        Returns:
            KnowledgeUpdateDescriptionSchema with update details
        """
        pass

    @abstractmethod
    async def set_storage_permission(
        self, name: str, user_id: str, permission: PermissionLevel
    ) -> KnowledgeSchema:
        """
        Set the permission level for a user on a storage.

        Args:
            name: Name of the storage
            user_id: ID of the user
            permission: Permission level to set

        Returns:
            Updated storage information
        """
        pass

    @abstractmethod
    async def remove_storage_permission(
        self, name: str, user_id: str
    ) -> KnowledgeSchema:
        """
        Remove user permissions from a storage.

        Args:
            name: Name of the storage
            user_id: ID of the user

        Returns:
            Updated storage information
        """
        pass

    @abstractmethod
    async def add_storage_tag(self, name: str, tag: str) -> KnowledgeSchema:
        """
        Add a tag to a storage.

        Args:
            name: Name of the storage
            tag: Tag to add

        Returns:
            Updated storage information
        """
        pass

    @abstractmethod
    async def remove_storage_tag(self, name: str, tag: str) -> KnowledgeSchema:
        """
        Remove a tag from a storage.

        Args:
            name: Name of the storage
            tag: Tag to remove

        Returns:
            Updated storage information
        """
        pass
