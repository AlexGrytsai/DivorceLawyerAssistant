import logging
from typing import Dict, List, Optional, Any, Set

from fastapi import UploadFile, Request

from src.core.config import settings
from src.core.constants import ALLOWED_MIME_TYPES_FOR_RAG
from src.services.rag_service import VectorDBInterface
from src.services.rag_service.decorators import (
    handle_index_operation_exceptions,
    handle_namespace_operation_exceptions,
    handle_folder_operation_exceptions,
    handle_document_processing,
    handle_async_search_exceptions,
)
from src.services.rag_service.interfaces import (
    RAGServiceInterface,
    RAGManagerInterface,
)
from src.services.rag_service.langchain_rag_manager import LangChainRAGManager
from src.services.rag_service.pinecone_client import PineconeClient
from src.services.rag_service.schemas import (
    IndexCreateSchema,
    IndexSchema,
    NamespaceCreateSchema,
    NamespaceSchema,
    SearchResponseSchema,
    ProcessingStatusSchema,
    IndexStatsSchema,
    Document,
)
from src.services.storage.interfaces.base_storage_interface import (
    BaseStorageInterface,
)
from src.services.storage.shemas import (
    FileSchema,
    FileDeleteSchema,
    FolderDeleteSchema,
    FolderContentsSchema,
    FolderDataSchema,
    FolderItem,
)
from src.utils.validators.validate_file_mime import validate_file_mime

logger = logging.getLogger(__name__)


class RAGService(RAGServiceInterface):
    def __init__(
        self,
        storage_interface: BaseStorageInterface = settings.RAG_STORAGE,
        vector_db_client: Optional[VectorDBInterface] = None,
        rag_manager: Optional[RAGManagerInterface] = None,
    ):
        self.storage = storage_interface
        self.vector_db_client = vector_db_client or PineconeClient()
        self.rag_manager = rag_manager or LangChainRAGManager()

    @handle_index_operation_exceptions
    async def create_index(
        self,
        index_name: str,
        request: Optional[Request] = None,
        dimension: int = settings.DIMENSIONS_EMBEDDING,
        metric: str = "cosine",
    ) -> IndexCreateSchema:
        logger.info(f"Creating index: {index_name}")

        folder = await self.storage.create_folder(index_name, request)
        success = self.vector_db_client.create_index(
            name=index_name,
            dimension=dimension,
            metric=metric,
        )

        if not success:
            await self.storage.delete_folder(index_name, request)
            raise ValueError(f"Failed to create Vector DB index: {index_name}")

        return IndexCreateSchema(
            name=index_name,
            dimension=dimension,
            metric=metric,
            created_at=folder.create_time,
        )

    @handle_index_operation_exceptions
    async def list_indexes(self) -> List[IndexSchema]:
        logger.info("Listing indexes")

        vector_db_indexes = await self._get_vector_db_indexes()
        storage_folders = await self._get_storage_folders()

        return [
            self._map_index_to_schema(
                folder,
                self.vector_db_client.get_index_stats_schema(
                    folder.folder_name
                ),
            )
            for folder in storage_folders
            if folder.folder_name in vector_db_indexes
        ]

    @handle_index_operation_exceptions
    async def delete_index(
        self,
        index_name: str,
        request: Optional[Request] = None,
    ) -> FolderDeleteSchema:
        logger.info(f"Deleting index: {index_name}")

        success = self.vector_db_client.delete_index(index_name)
        if not success:
            raise ValueError(f"Failed to delete Vector DB index: {index_name}")

        return await self.storage.delete_folder(
            folder_path=f"{index_name}/",
            request=request,
            is_delete_all=True,
        )

    @handle_namespace_operation_exceptions
    async def create_namespace(
        self,
        index_name: str,
        namespace: str,
        request: Optional[Request] = None,
    ) -> NamespaceCreateSchema:
        logger.info(f"Creating namespace: {namespace} in index: {index_name}")

        namespace_path = f"{index_name}/{namespace}/"
        folder = await self.storage.create_folder(namespace_path, request)

        return NamespaceCreateSchema(
            name=namespace,
            index_name=index_name,
            created_at=folder.create_time,
        )

    @handle_namespace_operation_exceptions
    async def list_namespaces(self, index_name: str) -> List[NamespaceSchema]:
        logger.info(f"Listing namespaces for index: {index_name}")

        pinecone_namespaces = self._get_pinecone_namespaces(index_name)
        folder_contents = await self._get_folder_contents(index_name)

        return [
            self._map_namespace_to_schema(item, index_name)
            for item in folder_contents.items
            if item.type == "folder"
            and item.folder_name in pinecone_namespaces
        ]

    @handle_namespace_operation_exceptions
    async def delete_namespace(
        self,
        index_name: str,
        namespace: str,
        request: Optional[Request] = None,
    ) -> FolderDeleteSchema:
        logger.info(
            f"Deleting namespace: {namespace} from index: {index_name}"
        )

        success = self.vector_db_client.delete_from_namespace(
            index_name=index_name,
            namespace=namespace,
            is_delete_all=True,
        )
        if not success:
            raise ValueError(
                f"Failed to delete namespace {namespace} from Vector DB "
                f"index {index_name}"
            )

        namespace_path = f"{index_name}/{namespace}/"
        return await self.storage.delete_folder(
            folder_path=namespace_path, request=request, is_delete_all=True
        )

    @handle_document_processing
    async def upload_file(
        self,
        index_name: str,
        namespace: str,
        file: UploadFile,
        request: Optional[Request] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FileSchema:
        logger.info(
            f"Uploading file: {file.filename} to {index_name}/{namespace}"
        )

        await validate_file_mime([file], ALLOWED_MIME_TYPES_FOR_RAG)
        original_filename = file.filename
        file.filename = f"{index_name}/{namespace}/{original_filename}"

        file_info = await self.storage.upload(file, request)
        await self.rag_manager.process_pdf_file(
            file_path=file_info.url,
            index_name=index_name,
            namespace=namespace,
            metadata=metadata,
        )

        return file_info

    @handle_document_processing
    async def upload_files(
        self,
        index_name: str,
        namespace: str,
        files: List[UploadFile],
        request: Optional[Request] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[FileSchema]:
        logger.info(
            f"Uploading {len(files)} files to {index_name}/{namespace}"
        )

        await self._validate_files(files)
        self._prepare_files_for_upload(files, index_name, namespace)
        files_info = await self.storage.multi_upload(files, request)
        await self._process_uploaded_files(
            files_info, index_name, namespace, metadata
        )

        return files_info

    @handle_folder_operation_exceptions
    async def upload_folder(
        self,
        index_name: str,
        namespace: str,
        folder_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProcessingStatusSchema:
        logger.info(
            f"Processing folder: {folder_path} for {index_name}/{namespace}"
        )

        documents = await self._process_directory(
            folder_path, index_name, namespace, metadata
        )
        return self._create_processing_status(index_name, namespace, documents)

    @handle_document_processing
    async def delete_document(
        self,
        index_name: str,
        namespace: str,
        document_path: str,
        request: Optional[Request] = None,
    ) -> FileDeleteSchema:
        logger.info(
            f"Deleting document: {document_path} from {index_name}/{namespace}"
        )

        file_info = await self._get_document_info(document_path)
        success = self._delete_document_from_db(
            index_name, namespace, file_info
        )

        if not success:
            raise ValueError(
                f"Failed to delete vectors for {document_path} from Pinecone"
            )

        return await self._delete_document_from_storage(document_path, request)

    @handle_async_search_exceptions
    async def search(
        self,
        query: str,
        index_name: str,
        namespace: str,
        top_k: int = 3,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SearchResponseSchema:
        logger.info(
            f"Searching for '{query}' in {index_name}/{namespace}, "
            f"top_k={top_k}"
        )

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

    # Private methods
    async def _get_vector_db_indexes(self) -> Set[str]:
        """Retrieves list of all indexes from vector database."""
        return set(self.vector_db_client.list_indexes())

    async def _get_storage_folders(self) -> List[FolderDataSchema]:
        """Retrieves list of all folders from storage service."""
        return await self.storage.list_folders()

    @staticmethod
    def _map_index_to_schema(
        folder: FolderDataSchema, stats: IndexStatsSchema
    ) -> IndexSchema:
        """Converts folder data and index stats into IndexSchema object."""
        return IndexSchema(
            name=folder.folder_name,
            dimension=stats.dimension,
            metric="cosine",
            created_at=folder.create_time,
        )

    def _get_pinecone_namespaces(self, index_name: str) -> List[str]:
        """Retrieves list of namespaces for given index from vector database."""
        return self.vector_db_client.list_namespaces(index_name)

    async def _get_folder_contents(
        self, index_name: str
    ) -> FolderContentsSchema:
        """Retrieves contents of specified folder from storage service."""
        return await self.storage.get_folder_contents(index_name)

    @staticmethod
    def _map_namespace_to_schema(
        item: FolderItem, index_name: str
    ) -> NamespaceSchema:
        """Converts folder item into NamespaceSchema object."""
        return NamespaceSchema(
            name=item.folder_name,
            index_name=index_name,
            created_at=item.create_time,
        )

    @staticmethod
    async def _validate_files(files: List[UploadFile]) -> None:
        """Validates MIME types of uploaded files against allowed types."""
        await validate_file_mime(files, ALLOWED_MIME_TYPES_FOR_RAG)

    @staticmethod
    def _prepare_files_for_upload(
        files: List[UploadFile], index_name: str, namespace: str
    ) -> None:
        """Prepares file paths for upload by adding index and namespace prefix."""
        for file in files:
            original_filename = file.filename
            file.filename = f"{index_name}/{namespace}/{original_filename}"

    async def _process_uploaded_files(
        self,
        files_info: List[FileSchema],
        index_name: str,
        namespace: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Processes uploaded files through RAG manager for vectorization."""
        for file_info in files_info:
            await self.rag_manager.process_pdf_file(
                file_path=file_info.url,
                index_name=index_name,
                namespace=namespace,
                metadata=metadata,
            )

    async def _process_directory(
        self,
        folder_path: str,
        index_name: str,
        namespace: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Processes all files in directory through RAG manager for vectorization."""
        return await self.rag_manager.process_directory(
            directory_path=folder_path,
            index_name=index_name,
            namespace=namespace,
            metadata=metadata,
        )

    @staticmethod
    def _create_processing_status(
        index_name: str,
        namespace: str,
        documents: List[Document],
    ) -> ProcessingStatusSchema:
        """Creates processing status schema for completed document processing."""
        return ProcessingStatusSchema(
            index_name=index_name,
            namespace=namespace,
            status="completed",
            total_files=len(documents),
            processed_files=len(documents),
        )

    async def _get_document_info(self, document_path: str) -> FileSchema:
        """Retrieves file information from storage service."""
        return await self.storage.get_file(document_path)

    def _delete_document_from_db(
        self,
        index_name: str,
        namespace: str,
        file_info: FileSchema,
    ) -> bool:
        """Deletes document vectors from vector database."""
        return self.vector_db_client.delete_from_namespace(
            index_name=index_name,
            namespace=namespace,
            filter={"source": file_info.url},
        )

    async def _delete_document_from_storage(
        self,
        document_path: str,
        request: Optional[Request] = None,
    ) -> FileDeleteSchema:
        """Deletes document from storage service."""
        return await self.storage.delete_file(document_path, request)
