from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from src.knowledge_storage.schemas import PermissionLevel

EntityPath = TypeVar("EntityPath")
EntityResult = TypeVar("EntityResult")


class PermissionInterface(ABC, Generic[EntityPath, EntityResult]):
    """Interface for entities that support permission management.

    This interface defines operations for managing user permissions
    on entities in the knowledge storage system.
    """

    @abstractmethod
    async def set_permission(
        self, path: EntityPath, user_id: str, permission: PermissionLevel
    ) -> EntityResult:
        """Set permission level for a user on an entity.

        Args:
            path: Path to the entity
            user_id: ID of the user
            permission: Permission level to set

        Returns:
            Updated entity information
        """
        pass

    @abstractmethod
    async def remove_permission(
        self, path: EntityPath, user_id: str
    ) -> EntityResult:
        """Remove user permissions from an entity.

        Args:
            path: Path to the entity
            user_id: ID of the user

        Returns:
            Updated entity information
        """
        pass

    @abstractmethod
    async def get_permissions(
        self, path: EntityPath
    ) -> dict[str, PermissionLevel]:
        """Get all permissions for an entity.

        Args:
            path: Path to the entity

        Returns:
            Dictionary mapping user IDs to their permission levels
        """
        pass
