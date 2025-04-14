from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Set

EntityPath = TypeVar("EntityPath")
EntityResult = TypeVar("EntityResult")


class TaggableInterface(ABC, Generic[EntityPath, EntityResult]):
    """Interface for entities that support tagging.

    This interface defines operations for managing tags on entities
    in the knowledge storage system.
    """

    @abstractmethod
    async def add_tag(self, path: EntityPath, tag: str) -> EntityResult:
        """Add a tag to an entity.

        Args:
            path: Path to the entity
            tag: Tag to add

        Returns:
            Updated entity information
        """
        pass

    @abstractmethod
    async def remove_tag(self, path: EntityPath, tag: str) -> EntityResult:
        """Remove a tag from an entity.

        Args:
            path: Path to the entity
            tag: Tag to remove

        Returns:
            Updated entity information
        """
        pass

    @abstractmethod
    async def get_tags(self, path: EntityPath) -> Set[str]:
        """Get all tags for an entity.

        Args:
            path: Path to the entity

        Returns:
            Set of tags
        """
        pass
