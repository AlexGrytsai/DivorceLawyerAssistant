from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any, Union

from src.knowledge_storage.schemas import (
    PaginationParams,
    PaginatedResponse,
    SmartSearchResponseSchema,
    ItemDetailSchema,
)

EntityPath = TypeVar("EntityPath")


class SearchableInterface(ABC, Generic[EntityPath]):
    """Interface for entities that support search operations.

    This interface defines operations for searching and filtering
    entities in the knowledge storage system.
    """

    @abstractmethod
    async def search(
        self,
        path: EntityPath,
        query: str,
        case_sensitive: bool = False,
        pagination: Optional[PaginationParams] = None,
    ) -> Union[List[ItemDetailSchema], PaginatedResponse]:
        """
        Search for entities by name.

        Args:
            path: Path to search within
            query: Search query
            case_sensitive: Whether to perform case-sensitive search
            pagination: Optional pagination parameters

        Returns:
            List of matching entities or paginated response
        """
        pass

    @abstractmethod
    async def smart_search(
        self,
        path: EntityPath,
        query: str,
        num_results: int = 3,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SmartSearchResponseSchema:
        """
        Perform semantic search across entities.

        Args:
            path: Path to search within
            query: Search query
            num_results: Maximum number of results to return
            filters: Optional search filters

        Returns:
            SmartSearchResponseSchema with search results
        """
        pass
