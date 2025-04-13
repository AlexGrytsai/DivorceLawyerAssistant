from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from langchain.embeddings.base import Embeddings

from .document_processor_interface import DocumentProcessorInterface
from .search_service_interface import SearchServiceInterface
from .vector_db_interface import VectorDBInterface


class RAGManagerInterface(ABC):
    """
    Interface for Retrieval-Augmented Generation (RAG) managers.

    This interface defines the contract for RAG manager implementations,
    providing methods for document processing, vector store management,
    and retrieval operations.
    It serves as a flexible base for different RAG implementations while
    maintaining a consistent API.
    """

    @abstractmethod
    def __init__(
        self,
        vector_db_client: Optional[VectorDBInterface] = None,
        embeddings: Optional[Embeddings] = None,
        document_processor: Optional[DocumentProcessorInterface] = None,
        file_processor_factory: Optional[Any] = None,
        search_service: Optional[SearchServiceInterface] = None,
        directory_processor: Optional[Any] = None,
    ) -> None:
        """
        Initialize the RAG manager with necessary components.

        Args:
            vector_db_client: Client for interacting with the vector database
            embeddings: Embedding model for converting text to vectors
            document_processor: Processor for handling document operations
            file_processor_factory: Factory for creating file processors
            search_service: Service for performing semantic search
            directory_processor: Processor for handling directory operations
        """
        pass

    @abstractmethod
    def get_vector_store(
        self,
        index_name: str,
        namespace: str,
        vector_store: Optional[Any] = None,
    ):
        """
        Get a vector store instance for the specified index and namespace.

        Args:
            index_name: Name of the vector index
            namespace: Namespace within the index
            vector_store: Optional vector store factory

        Returns:
            Vector store instance configured for the specified index and
            namespace
        """
        pass

    @abstractmethod
    async def process_pdf_file(
        self,
        file_path: str,
        index_name: str,
        namespace: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        """
        Process a PDF file and store its contents in the vector database.

        Args:
            file_path: Path to the PDF file
            index_name: Name of the vector index to store embeddings
            namespace: Namespace within the index
            metadata: Additional metadata to associate with the document

        Returns:
            List of processed document schemas
        """
        pass

    @abstractmethod
    async def process_directory(
        self,
        directory_path: str,
        index_name: str,
        namespace: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        """
        Process all compatible files in a directory and store in
        the vector database.

        Args:
            directory_path: Path to the directory containing files to process
            index_name: Name of the vector index to store embeddings
            namespace: Namespace within the index
            metadata: Additional metadata to associate with the documents

        Returns:
            List of processed document schemas
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        index_name: str,
        namespace: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        """
        Perform semantic search using the provided query.

        Args:
            query: Search query text
            index_name: Name of the vector index to search
            namespace: Namespace within the index
            top_k: Number of results to return
            filters: Optional filters to apply to the search

        Returns:
            List of query result schemas containing matched documents
            and metadata
        """
        pass
