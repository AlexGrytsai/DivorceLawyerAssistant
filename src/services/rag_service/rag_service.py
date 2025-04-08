import logging
from typing import Dict, List, Optional, Any

from fastapi import UploadFile, Request, HTTPException, status

from src.core.config import settings
from src.core.constants import ALLOWED_MIME_TYPES_FOR_RAG
from src.services.rag_service import VectorDBInterface, LangChainRAGManager
from src.services.rag_service.interfaces import RAGManagerInterface
from src.services.rag_service.pinecone_client import PineconeClient
from src.services.rag_service.schemas import (
    IndexCreateSchema,
    IndexSchema,
    NamespaceCreateSchema,
    NamespaceSchema,
    SearchResponseSchema,
    ProcessingStatusSchema,
)
from src.services.storage.interfaces.base_storage_interface import (
    BaseStorageInterface,
)
from src.services.storage.shemas import (
    FileSchema,
    FileDeleteSchema,
    FolderDeleteSchema,
)
from src.utils.validators.validate_file_mime import validate_file_mime

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(
        self,
        storage_interface: BaseStorageInterface = settings.RAG_STORAGE,
        vector_db_client: Optional[VectorDBInterface] = None,
        rag_manager: Optional[RAGManagerInterface] = None,
    ):
        self.storage = storage_interface
        self.vector_db_client = vector_db_client or PineconeClient()
        self.rag_manager = rag_manager or LangChainRAGManager()

    async def create_index(
        self,
        index_name: str,
        request: Request,
        dimension: int = settings.DIMENSIONS_EMBEDDING,
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
        logger.info(f"Creating index: {index_name}")

        # Create folder for index in storage
        folder = await self.storage.create_folder(index_name, request)

        # Create index in Vector DB
        success = self.vector_db_client.create_index(
            name=index_name,
            dimension=dimension,
            metric=metric,
        )

        if not success:
            logger.warning(
                f"Failed to create Vector DB index: {index_name}, "
                f"but folder was created"
            )

        return IndexCreateSchema(
            name=index_name,
            dimension=dimension,
            metric=metric,
            created_at=folder.create_time,
        )

    async def list_indexes(self) -> List[IndexSchema]:
        """
        Lists all available indexes.

        Returns:
            List of IndexSchema objects
        """
        logger.info("Listing indexes")

        # Get indexes from Pinecone
        vector_db_indexes = set(self.vector_db_client.list_indexes())

        # Get folders from storage
        storage_folders = await self.storage.list_folders()

        # Merge the results
        indexes = []
        for folder in storage_folders:
            folder_name = folder.folder_name
            if folder_name in vector_db_indexes:
                # Get index stats from Vector DB
                stats = self.vector_db_client.get_index_stats_schema(
                    folder_name
                )

                indexes.append(
                    IndexSchema(
                        name=folder_name,
                        dimension=stats.dimension,
                        # Default, as Pinecone doesn't return this
                        metric="cosine",
                        created_at=folder.create_time,
                    )
                )

        return indexes

    async def delete_index(
        self, index_name: str, request: Request
    ) -> FolderDeleteSchema:
        """
        Deletes an index from Vector DB and corresponding folder from storage.

        Args:
            index_name: Name of the index to delete
            request: FastAPI request object

        Returns:
            FileDeleteSchema with deletion information
        """
        logger.info(f"Deleting index: {index_name}")

        # Delete index from Vector DB
        success = self.vector_db_client.delete_index(index_name)

        if not success:
            logger.warning(
                f"Failed to delete Vector DB index: {index_name}, "
                f"proceeding with folder deletion"
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Error deleting index from Vector DB",
                    "message": (
                        f"Failed to delete Vector DB index: {index_name}, "
                        f"proceeding with folder deletion"
                    ),
                },
            )

        # Delete folder from storage
        return await self.storage.delete_folder(index_name, request)

    async def create_namespace(
        self, index_name: str, namespace: str, request: Request
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
        logger.info(f"Creating namespace: {namespace} in index: {index_name}")

        # Create namespace folder path
        namespace_path = f"{index_name}/{namespace}"

        # Create folder in storage
        folder = await self.storage.create_folder(namespace_path, request)

        return NamespaceCreateSchema(
            name=namespace,
            index_name=index_name,
            created_at=folder.create_time,
        )

    async def list_namespaces(self, index_name: str) -> List[NamespaceSchema]:
        """
        Lists all namespaces in an index.

        Args:
            index_name: Name of the index

        Returns:
            List of NamespaceSchema objects
        """
        logger.info(f"Listing namespaces for index: {index_name}")

        # Get namespaces from Vector DB
        pinecone_namespaces = self.vector_db_client.list_namespaces(index_name)

        # Get folders from storage
        folder_contents = await self.storage.get_folder_contents(index_name)

        # Extract namespace folders
        namespaces = []
        for item in folder_contents.items:
            if item.type == "folder":
                folder_name = item.folder_name
                if folder_name in pinecone_namespaces:
                    namespaces.append(
                        NamespaceSchema(
                            name=folder_name,
                            index_name=index_name,
                            created_at=item.create_time,
                        )
                    )

        return namespaces

    async def delete_namespace(
        self, index_name: str, namespace: str, request: Request
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
        logger.info(
            f"Deleting namespace: {namespace} from index: {index_name}"
        )

        # Delete from Vector DB
        success = self.vector_db_client.delete_from_namespace(
            index_name=index_name,
            namespace=namespace,
            delete_all=True,
        )

        if not success:
            logger.warning(
                f"Failed to delete namespace {namespace} from Pinecone index "
                f"{index_name}, proceeding with folder deletion"
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Error deleting namespace from Vector DB",
                    "message": (
                        f"Failed to delete namespace {namespace} from Pinecone"
                        f" index {index_name}, proceeding with folder deletion"
                    ),
                },
            )

        # Delete folder from storage
        namespace_path = f"{index_name}/{namespace}"
        return await self.storage.delete_folder(namespace_path, request)

    async def upload_file(
        self,
        index_name: str,
        namespace: str,
        file: UploadFile,
        request: Request,
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
        logger.info(
            f"Uploading file: {file.filename} " f"to {index_name}/{namespace}"
        )

        # Validate file MIME type
        await validate_file_mime([file], ALLOWED_MIME_TYPES_FOR_RAG)

        # Set file path within namespace
        original_filename = file.filename
        file.filename = f"{index_name}/{namespace}/{original_filename}"

        # Upload file to storage
        file_info = await self.storage.upload(file, request)

        # Process file and add to vector store
        await self.rag_manager.process_pdf_file(
            file_path=file_info.url,
            index_name=index_name,
            namespace=namespace,
            metadata=metadata,
        )

        return file_info

    async def upload_files(
        self,
        index_name: str,
        namespace: str,
        files: List[UploadFile],
        request: Request,
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
        logger.info(
            f"Uploading {len(files)} files " f"to {index_name}/{namespace}"
        )

        # Validate files MIME types
        await validate_file_mime(files, ALLOWED_MIME_TYPES_FOR_RAG)

        # Set files paths within namespace
        for file in files:
            original_filename = file.filename
            file.filename = f"{index_name}/{namespace}/{original_filename}"

        # Upload files to storage
        files_info = await self.storage.multi_upload(files, request)

        # Process files and add to vector store
        for file_info in files_info:
            await self.rag_manager.process_pdf_file(
                file_path=file_info.url,
                index_name=index_name,
                namespace=namespace,
                metadata=metadata,
            )

        return files_info

    async def upload_folder(
        self,
        index_name: str,
        namespace: str,
        folder_path: str,
        request: Request,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProcessingStatusSchema:
        """
        Processes all PDF files in a folder and adds them to vector store.

        Args:
            index_name: Target index name
            namespace: Target namespace
            folder_path: Path to folder with PDF files
            request: FastAPI request object
            metadata: Optional metadata to attach to document chunks

        Returns:
            ProcessingStatusSchema with processing status
        """
        logger.info(
            f"Processing folder: {folder_path} "
            f"for {index_name}/{namespace}"
        )

        try:
            # Process directory
            documents = await self.rag_manager.process_directory(
                directory_path=folder_path,
                index_name=index_name,
                namespace=namespace,
                metadata=metadata,
            )

            return ProcessingStatusSchema(
                index_name=index_name,
                namespace=namespace,
                status="completed",
                total_files=len(documents),
                processed_files=len(documents),
            )
        except Exception as e:
            logger.error(f"Error processing folder {folder_path}: {e}")
            return ProcessingStatusSchema(
                index_name=index_name,
                namespace=namespace,
                status="failed",
                total_files=0,
                processed_files=0,
                error_message=str(e),
            )

    async def delete_document(
        self,
        index_name: str,
        namespace: str,
        document_path: str,
        request: Request,
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
        logger.info(
            f"Deleting document: {document_path} "
            f"from {index_name}/{namespace}"
        )

        # Get a file from storage
        file_info = await self.storage.get_file(document_path)

        # Delete it from Vector DB with filter
        success = self.vector_db_client.delete_from_namespace(
            index_name=index_name,
            namespace=namespace,
            filter={"source": file_info.url},
        )

        if not success:
            logger.warning(
                f"Failed to delete vectors for {document_path} "
                f"from Pinecone, proceeding with file deletion"
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Error deleting namespace from Vector DB",
                    "message": (
                        f"Failed to delete vectors for {document_path} "
                        f"from Pinecone, proceeding with file deletion"
                    ),
                },
            )

        # Delete file from storage
        return await self.storage.delete_file(document_path, request)

    async def search(
        self,
        query: str,
        index_name: str,
        namespace: str,
        top_k: int = 5,
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
        logger.info(
            f"Searching for '{query}' in {index_name}/{namespace}, "
            f"top_k={top_k}"
        )

        # Perform search
        results = await self.rag_manager.search(
            query=query,
            index_name=index_name,
            namespace=namespace,
            top_k=top_k,
            filters=filters,
        )

        return SearchResponseSchema(
            query=query,
            results=results,
            total=len(results),
        )
