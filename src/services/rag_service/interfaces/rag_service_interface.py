from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from fastapi import UploadFile, Request

from src.services.rag_service.schemas import (
    IndexCreateSchema,
    IndexSchema,
    NamespaceCreateSchema,
    NamespaceSchema,
    SearchResponseSchema,
    ProcessingStatusSchema,
)
from src.services.storage.shemas import (
    FileSchema,
    FileDeleteSchema,
    FolderDeleteSchema,
)


class RAGServiceInterface(ABC):
    @abstractmethod
    async def create_index(
        self,
        index_name: str,
        request: Optional[Request] = None,
        dimension: int = 1024,
        metric: str = "cosine",
    ) -> IndexCreateSchema:
        """
        Creates a new index in Vector DB and corresponding folder in storage.

        Args:
            index_name: Name of the index
            request: FastAPI request object
            dimension: Vector dimension
            metric: Distance metric for vector similarity

        Returns:
            IndexCreateSchema with index information
        """
        pass

    @abstractmethod
    async def list_indexes(self) -> List[IndexSchema]:
        """
        Lists all available indexes.

        Returns:
            List of IndexSchema objects
        """
        pass

    @abstractmethod
    async def delete_index(
        self,
        index_name: str,
        request: Optional[Request] = None,
    ) -> FolderDeleteSchema:
        """
        Deletes an index from Vector DB and corresponding folder from storage.

        Args:
            index_name: Name of the index to delete
            request: FastAPI request object

        Returns:
            FileDeleteSchema with deletion information
        """
        pass

    @abstractmethod
    async def create_namespace(
        self,
        index_name: str,
        namespace: str,
        request: Optional[Request] = None,
    ) -> NamespaceCreateSchema:
        """
        Creates a namespace folder within an index.

        Args:
            index_name: Parent index name
            namespace: Namespace name
            request: FastAPI request object

        Returns:
            NamespaceCreateSchema with namespace information
        """
        pass

    @abstractmethod
    async def list_namespaces(self, index_name: str) -> List[NamespaceSchema]:
        """
        Lists all namespaces in an index.

        Args:
            index_name: Name of the index

        Returns:
            List of NamespaceSchema objects
        """
        pass

    @abstractmethod
    async def delete_namespace(
        self,
        index_name: str,
        namespace: str,
        request: Optional[Request] = None,
    ) -> FolderDeleteSchema:
        """
        Deletes a namespace from an index and its folder from storage.

        Args:
            index_name: Parent index name
            namespace: Namespace to delete
            request: FastAPI request object

        Returns:
            FileDeleteSchema with deletion information
        """
        pass

    @abstractmethod
    async def upload_file(
        self,
        index_name: str,
        namespace: str,
        file: UploadFile,
        request: Optional[Request] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FileSchema:
        """
        Uploads a file to a namespace, validates it, processes it,
        and adds it to vector store.

        Args:
            index_name: Target index name
            namespace: Target namespace
            file: File to upload
            request: FastAPI request object
            metadata: Optional metadata to attach to document chunks

        Returns:
            FileSchema with uploaded file information
        """
        pass

    @abstractmethod
    async def upload_files(
        self,
        index_name: str,
        namespace: str,
        files: List[UploadFile],
        request: Optional[Request] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[FileSchema]:
        """
        Uploads multiple files to a namespace, validates them,
        processes them, and adds them to vector store.

        Args:
            index_name: Target index name
            namespace: Target namespace
            files: Files to upload
            request: FastAPI request object
            metadata: Optional metadata to attach to document chunks

        Returns:
            List of FileSchema with uploaded files information
        """
        pass

    @abstractmethod
    async def upload_folder(
        self,
        index_name: str,
        namespace: str,
        folder_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProcessingStatusSchema:
        """
        Processes all PDF files in a folder and adds them to vector store.

        Args:
            index_name: Target index name
            namespace: Target namespace
            folder_path: Path to folder with PDF files
            metadata: Optional metadata to attach to document chunks

        Returns:
            ProcessingStatusSchema with processing status
        """
        pass

    @abstractmethod
    async def delete_document(
        self,
        index_name: str,
        namespace: str,
        document_path: str,
        request: Optional[Request] = None,
    ) -> FileDeleteSchema:
        """
        Deletes a document from storage and its vectors from Vector DB.

        Args:
            index_name: Index name
            namespace: Namespace
            document_path: Path to document
            request: FastAPI request object

        Returns:
            FileDeleteSchema with deletion information
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        index_name: str,
        namespace: str,
        top_k: int = 3,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SearchResponseSchema:
        """
        Performs semantic search in the specified namespace.

        Args:
            query: Search query
            index_name: Index to search in
            namespace: Namespace to search in
            top_k: Number of results to return
            filters: Optional filters for search

        Returns:
            SearchResponseSchema with search results
        """
        pass
