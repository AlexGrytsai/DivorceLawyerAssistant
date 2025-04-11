from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from src.services.rag_service.schemas import IndexStatsSchema


class VectorDBInterface(ABC):
    """
    Abstract class for interacting with vector databases.
    Defines a unified interface for different implementations
    (Pinecone, Milvus, etc.)
    """

    @abstractmethod
    def create_index(
        self,
        name: str,
        dimension: int = 1536,
        metric: str = "cosine",
        **kwargs
    ) -> bool:
        """
        Creates a new index in the vector database.

        Args:
            name: Index name
            dimension: Vector dimension
            metric: Distance metric for vector similarity
            **kwargs: Additional parameters specific to the
                particular implementation

        Returns:
            bool: True if the index is created successfully, False otherwise
        """
        pass

    @abstractmethod
    def delete_index(self, name: str) -> bool:
        """
        Deletes an index from the vector database.

        Args:
            name: Index name to delete

        Returns:
            bool: True if the index is deleted successfully, False otherwise
        """
        pass

    @abstractmethod
    def list_indexes(self) -> List[str]:
        """
        Returns a list of all available indexes.

        Returns:
            List[str]: List of index names
        """
        pass

    @abstractmethod
    def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """
        Returns statistics for the specified index.

        Args:
            index_name: Index name

        Returns:
            Dict[str, Any]: Dictionary with index statistics
        """
        pass

    @abstractmethod
    def delete_from_namespace(
        self,
        index_name: str,
        namespace: str,
        ids: Optional[List[str]] = None,
        is_delete_all: bool = False,
        filter_: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Deletes vectors from the specified namespace.

        Args:
            index_name: Index name
            namespace: Namespace name
            ids: List of vector IDs to delete
            is_delete_all: Flag to delete all vectors in the namespace
            filter_: Filter for selective deletion of vectors

        Returns:
            bool: True if the operation is successful, False otherwise
        """
        pass

    @abstractmethod
    def list_namespaces(self, index_name: str) -> List[str]:
        """
        Returns a list of all namespaces in the specified index.

        Args:
            index_name: Index name

        Returns:
            List[str]: List of namespace names
        """
        pass

    @abstractmethod
    def get_index_stats_schema(self, index_name: str) -> IndexStatsSchema:
        """
        Returns schema for the specified index.

        Args:
            index_name: Index name

        Returns:
            IndexStatsSchema: Schema for the index statistics
        """
        pass
