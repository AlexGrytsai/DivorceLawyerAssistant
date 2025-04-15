from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union, NamedTuple

from src.services.document_database.schemas import (
    DocumentDetailSchema,
    DocumentSchema,
)


class SearchQueryParameter(NamedTuple):
    field: str
    operator: str
    value: Union[str, int, float, bool]


class DocumentDatabaseInterface(ABC):
    """
    Abstract base class for document-oriented database operations.
    This interface defines the contract for document database implementations
    such as Firestore, MongoDB, etc.
    """

    @abstractmethod
    async def save(
        self, collection: str, document: DocumentDetailSchema
    ) -> str:
        """
        Save a document to the specified collection.

        Args:
            collection: Name of the collection to save the document to
            document: Document to save

        Returns:
            ID of the saved document

        Raises:
            ValidationError: If document validation fails
            DatabaseConnectionError: If connection to database fails
            DatabaseOperationError: If operation fails for any other reason
        """
        pass

    @abstractmethod
    async def get_document(
        self, collection: str, document_name: str, is_detail: bool = False
    ) -> Union[DocumentSchema, DocumentDetailSchema]:
        """
        Retrieve a document by its ID from the specified collection.

        Args:
            collection: Name of the collection to get the document from
            document_name: Name of the document to retrieve
            is_detail: Whether to return a detailed document

        Returns:
            Retrieved document

        Raises:
            DocumentNotFoundError: If a document does not exist
            DatabaseConnectionError: If connection to a database fails
            DatabaseOperationError: If operation fails for any other reason
        """
        pass

    @abstractmethod
    async def get_collection(
        self,
        collection: str,
        sort_direction: str,
        limit: Optional[int] = None,
        order_by: str = "name",
        is_detail: bool = False,
    ) -> List[Union[DocumentSchema, DocumentDetailSchema]]:
        """
        Retrieve all documents from the specified collection.

        Args:
            collection: Name of the collection to get all documents from
            sort_direction: Direction to sort results ('asc' or 'desc')
            limit: Maximum number of documents to return (0 for unlimited)
            order_by: Field name to order results by
            is_detail: Whether to return detailed document objects

        Returns:
            List of all documents in the collection

        Raises:
            DatabaseConnectionError: If connection to a database fails
            DatabaseOperationError: If operation fails for any other reason
        """
        pass

    @abstractmethod
    async def find(
        self,
        collection: str,
        query: List[SearchQueryParameter],
        limit: Optional[int] = None,
        skip: Optional[int] = None,
    ) -> List[DocumentSchema]:
        """
        Find documents matching the query criteria.

        Args:
            collection: Name of the collection to search in
            query: Dictionary of field-value pairs to match
            limit: Maximum number of documents to return
            skip: Number of documents to skip

        Returns:
            List of matching documents

        Raises:
            ValidationError: If query parameters are invalid
            DatabaseConnectionError: If connection to a database fails
            DatabaseOperationError: If operation fails for any other reason
        """
        pass

    @abstractmethod
    async def update(
        self, collection: str, document_id: str, updates: DocumentDetailSchema
    ) -> None:
        """
        Update a document with the specified changes.

        Args:
            collection: Name of the collection containing the document
            document_id: ID of the document to update
            updates: Dictionary of field-value pairs to update

        Raises:
            DocumentNotFoundError: If a document does not exist
            ValidationError: If update data is invalid
            DatabaseConnectionError: If connection to a database fails
            DatabaseOperationError: If operation fails for any other reason
        """
        pass

    @abstractmethod
    async def delete(self, collection: str, document_id: str) -> None:
        """
        Delete a document by its ID.

        Args:
            collection: Name of the collection containing the document
            document_id: ID of the document to delete

        Raises:
            DocumentNotFoundError: If a document does not exist
            DatabaseConnectionError: If connection to a database fails
            DatabaseOperationError: If operation fails for any other reason
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
    ) -> List[DocumentDetailSchema]:
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

        Raises:
            ValidationError: If filter parameters are invalid
            DatabaseConnectionError: If connection to a database fails
            DatabaseOperationError: If operation fails for any other reason
        """
        pass
