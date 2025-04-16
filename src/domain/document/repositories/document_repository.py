from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union

from src.domain.document.entities import (
    DocumentDetail,
    Document,
    DocumentDelete,
)
from src.domain.document.value_objects import SearchQuery


class DocumentRepository(ABC):
    """
    Document repository interface.
    Defines the contract for all document storage implementations.
    """

    @abstractmethod
    async def save(self, collection: str, document: DocumentDetail) -> str:
        """
        Save a document to the specified collection.

        Args:
            collection: Collection name to save the document
            document: Document to save

        Returns:
            Name of the saved document

        Raises:
            DocumentAlreadyExistsError: If a document with the same name already exists
            ValidationError: If document data fails validation
            DatabaseConnectionError: If database connection fails
            DatabaseOperationError: If operation fails for other reasons
        """
        pass

    @abstractmethod
    async def get_document(
        self, collection: str, document_name: str, is_detail: bool = False
    ) -> Union[Document, DocumentDetail]:
        """
        Get a document by name from the specified collection.

        Args:
            collection: Collection name to search for the document
            document_name: Name of the document to retrieve
            is_detail: Flag to get detailed information about the document

        Returns:
            Document as DocumentSchema or DocumentDetailSchema

        Raises:
            DocumentNotFoundError: If document is not found
            DatabaseConnectionError: If database connection fails
            DatabaseOperationError: If operation fails for other reasons
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
    ) -> List[Union[Document, DocumentDetail]]:
        """
        Get all documents from the specified collection.

        Args:
            collection: Collection name to retrieve documents
            sort_direction: Sort direction ('asc' or 'desc')
            limit: Maximum number of documents to return
            order_by: Field to sort results by
            is_detail: Flag to get detailed information about documents

        Returns:
            List of documents in the collection

        Raises:
            DatabaseConnectionError: If database connection fails
            DatabaseOperationError: If operation fails for other reasons
        """
        pass

    @abstractmethod
    async def find(
        self,
        collection: str,
        query: List[SearchQuery],
        limit: Optional[int] = None,
        skip: Optional[int] = None,
    ) -> List[Document]:
        """
        Find documents matching query criteria.

        Args:
            collection: Collection name to search
            query: List of search parameters
            limit: Maximum number of documents to return
            skip: Number of documents to skip

        Returns:
            List of found documents

        Raises:
            InvalidQueryParameterError: If query parameters are invalid
            DatabaseConnectionError: If database connection fails
            DatabaseOperationError: If operation fails for other reasons
        """
        pass

    @abstractmethod
    async def update(
        self,
        collection: str,
        document_name: str,
        updates: DocumentDetail,
    ) -> None:
        """
        Update a document with specified changes.

        Args:
            collection: Collection name containing the document
            document_name: Name of the document to update
            updates: Object with updated document data

        Raises:
            DocumentNotFoundError: If document is not found
            ValidationError: If update data fails validation
            DatabaseConnectionError: If database connection fails
            DatabaseOperationError: If operation fails for other reasons
        """
        pass

    @abstractmethod
    async def delete(
        self, collection: str, document_name: str
    ) -> DocumentDelete:
        """
        Delete a document by its name.

        Args:
            collection: Collection name containing the document
            document_name: Name of the document to delete

        Raises:
            DocumentNotFoundError: If document is not found
            DatabaseConnectionError: If database connection fails
            DatabaseOperationError: If operation fails for other reasons
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
    ) -> List[DocumentDetail]:
        """
        Filter documents by a specific field.

        Args:
            collection: Collection name to filter
            field: Field name to filter by
            operator: Comparison operator ('==', '>', '<', '>=', '<=')
            value: Value to compare against
            limit: Maximum number of documents to return

        Returns:
            List of documents matching the filter criteria

        Raises:
            UnsupportedOperatorError: If operator is not supported
            ValidationError: If filter parameters are invalid
            DatabaseConnectionError: If database connection fails
            DatabaseOperationError: If operation fails for other reasons
        """
        pass
