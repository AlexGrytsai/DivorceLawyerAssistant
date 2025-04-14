from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Union

from fastapi import UploadFile
from pydantic import HttpUrl

from src.knowledge_storage.schemas import ItemVersionSchema

EntityPath = TypeVar("EntityPath")


class VersionalInterface(ABC, Generic[EntityPath]):
    """
    Interface for entities that support versioning.

    This interface defines operations for managing versions
    of entities in the knowledge storage system.
    """

    @abstractmethod
    async def create_version(
        self, path: EntityPath, content: Union[HttpUrl, str, UploadFile]
    ) -> ItemVersionSchema:
        """Create a new version of an entity.

        Args:
            path: Path to the entity
            content: New content for the version

        Returns:
            Version details
        """
        pass

    @abstractmethod
    async def get_versions(self, path: EntityPath) -> List[ItemVersionSchema]:
        """Get all versions of an entity.

        Args:
            path: Path to the entity

        Returns:
            List of versions
        """
        pass

    @abstractmethod
    async def get_version(
        self, path: EntityPath, version_id: int
    ) -> ItemVersionSchema:
        """Get a specific version of an entity.

        Args:
            path: Path to the entity
            version_id: ID of the version to retrieve

        Returns:
            Version details
        """
        pass
