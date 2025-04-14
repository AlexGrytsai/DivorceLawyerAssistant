from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic


DocumentType = TypeVar("DocumentType")


class DocumentDatabase(ABC, Generic[DocumentType]):
    """
    Abstract base class for document-oriented database operations.
    This interface defines the contract for document database implementations
    such as Firestore, MongoDB, etc.
    """

    @abstractmethod
    async def save(self, collection: str, document: DocumentType) -> str:
        """
        Save a document to the specified collection.

        Args:
            collection: Name of the collection to save the document to
            document: Document to save

        Returns:
            ID of the saved document
        """
        pass

    @abstractmethod
    async def get(
        self, collection: str, document_id: str
    ) -> Optional[DocumentType]:
        """
        Retrieve a document by its ID from the specified collection.

        Args:
            collection: Name of the collection to get the document from
            document_id: ID of the document to retrieve

        Returns:
            Retrieved document or None if not found
        """
        pass

    @abstractmethod
    async def find(
        self,
        collection: str,
        query: Dict[str, Any],
        limit: Optional[int] = None,
        skip: Optional[int] = None,
    ) -> List[DocumentType]:
        """
        Find documents matching the query criteria.

        Args:
            collection: Name of the collection to search in
            query: Dictionary of field-value pairs to match
            limit: Maximum number of documents to return
            skip: Number of documents to skip

        Returns:
            List of matching documents
        """
        pass

    @abstractmethod
    async def update(
        self, collection: str, document_id: str, updates: Dict[str, Any]
    ) -> bool:
        """
        Update a document with the specified changes.

        Args:
            collection: Name of the collection containing the document
            document_id: ID of the document to update
            updates: Dictionary of field-value pairs to update

        Returns:
            True if update was successful, False otherwise
        """
        pass

    @abstractmethod
    async def delete(self, collection: str, document_id: str) -> bool:
        """
        Delete a document by its ID.

        Args:
            collection: Name of the collection containing the document
            document_id: ID of the document to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        pass

    @abstractmethod
    async def filter(
        self,
        collection: str,
        field: str,
        operator: str,
        value: Any,
        limit: Optional[int] = None,
    ) -> List[DocumentType]:
        """
        Filter documents by a specific field using a comparison operator.

        Args:
            collection: Name of the collection to filter
            field: Name of the field to filter on
            operator: Comparison operator (e.g., '==', '>', '<', '>=', '<=')
            value: Value to compare against
            limit: Maximum number of documents to return

        Returns:
            List of documents matching the filter criteria
        """
        pass
