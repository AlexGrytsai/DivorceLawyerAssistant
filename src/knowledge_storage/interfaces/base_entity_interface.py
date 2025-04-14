from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, Union, List

from src.knowledge_storage.schemas import PaginationParams, PaginatedResponse

EntityParams = TypeVar("EntityParams")
EntityPath = TypeVar("EntityPath")
EntityResult = TypeVar("EntityResult")


class BaseEntityInterface(
    ABC, Generic[EntityParams, EntityPath, EntityResult]
):
    """
    Base interface for all entities in the knowledge storage system.

    This interface defines common operations that can be performed on any
    entity in the system, such as creation, retrieval, updating, and deletion.
    """

    @abstractmethod
    async def create(
        self, path: EntityPath, params: EntityParams
    ) -> EntityResult:
        """Create a new entity.

        Args:
            path: Path to the parent entity
            params: Parameters for entity creation

        Returns:
            Created entity details
        """
        pass

    @abstractmethod
    async def get(
        self, path: EntityPath, is_detail: bool = False
    ) -> EntityResult:
        """Retrieve an entity by its path.

        Args:
            path: Path to the entity
            is_detail: If True, returns detailed information

        Returns:
            Entity information
        """
        pass

    @abstractmethod
    async def delete(self, path: EntityPath) -> EntityResult:
        """Delete an entity.

        Args:
            path: Path to the entity to delete

        Returns:
            Deletion details
        """
        pass

    @abstractmethod
    async def rename(self, path: EntityPath, new_name: str) -> EntityResult:
        """Rename an entity.

        Args:
            path: Path to the entity
            new_name: New name for the entity

        Returns:
            Rename operation details
        """
        pass

    @abstractmethod
    async def update_description(
        self, path: EntityPath, description: str
    ) -> EntityResult:
        """Update entity description.

        Args:
            path: Path to the entity
            description: New description text

        Returns:
            Update details
        """
        pass

    @abstractmethod
    async def list(
        self, path: EntityPath, pagination: Optional[PaginationParams] = None
    ) -> Union[List[EntityResult], PaginatedResponse]:
        """List all entities under a given path.

        Args:
            path: Path to the parent entity
            pagination: Optional pagination parameters

        Returns:
            List of entities or paginated response
        """
        pass
