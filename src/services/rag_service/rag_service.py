import logging
from typing import Dict, List, Optional, Any

from fastapi import UploadFile, Request, HTTPException, status

from src.core.config import settings
from src.core.constants import ALLOWED_MIME_TYPES_FOR_RAG
from src.services.rag_service import VectorDBInterface
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
)
from src.services.storage.interfaces.base_storage_interface import (
    BaseStorageInterface,
)
from src.services.storage.shemas import (
    FileSchema,
    FileDeleteSchema,
    FolderDeleteSchema,
    FolderContentsSchema,
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
            logger.warning(f"Failed to create Vector DB index: {index_name}.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Error creating index in Vector DB",
                    "message": (
                        f"Failed to create Vector DB index: {index_name}",
                    ),
                },
            )

        return IndexCreateSchema(
            name=index_name,
            dimension=dimension,
            metric=metric,
            created_at=folder.create_time,
        )

    async def list_indexes(self) -> List[IndexSchema]:
        logger.info("Listing indexes")

        vector_db_indexes = set(self.vector_db_client.list_indexes())
        storage_folders = await self.storage.list_folders()

        indexes = []
        for folder in storage_folders:
            folder_name = folder.folder_name
            if folder_name in vector_db_indexes:
                stats = self.vector_db_client.get_index_stats_schema(
                    folder_name
                )
                indexes.append(
                    IndexSchema(
                        name=folder_name,
                        dimension=stats.dimension,
                        metric="cosine",
                        created_at=folder.create_time,
                    )
                )

        return indexes

    async def delete_index(
        self,
        index_name: str,
        request: Optional[Request] = None,
    ) -> FolderDeleteSchema:
        logger.info(f"Deleting index: {index_name}")

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

        return await self.storage.delete_folder(
            folder_path=f"{index_name}/",
            request=request,
            is_delete_all=True,
        )

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

    async def list_namespaces(self, index_name: str) -> List[NamespaceSchema]:
        logger.info(f"Listing namespaces for index: {index_name}")

        pinecone_namespaces = self.vector_db_client.list_namespaces(index_name)
        folder_contents: FolderContentsSchema = (
            await self.storage.get_folder_contents(index_name)
        )

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
            logger.warning(
                f"Failed to delete namespace {namespace} from Vector DB index "
                f"{index_name}, proceeding with folder deletion"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Error deleting namespace from Vector DB",
                    "message": (
                        f"Failed to delete namespace {namespace} from "
                        f"Vector DB index {index_name}, "
                        f"proceeding with folder deletion"
                    ),
                },
            )

        namespace_path = f"{index_name}/{namespace}/"
        return await self.storage.delete_folder(
            folder_path=namespace_path, request=request, is_delete_all=True
        )

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

        await validate_file_mime(files, ALLOWED_MIME_TYPES_FOR_RAG)

        for file in files:
            original_filename = file.filename
            file.filename = f"{index_name}/{namespace}/{original_filename}"

        files_info = await self.storage.multi_upload(files, request)

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
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProcessingStatusSchema:
        logger.info(
            f"Processing folder: {folder_path} for {index_name}/{namespace}"
        )

        try:
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
        request: Optional[Request] = None,
    ) -> FileDeleteSchema:
        logger.info(
            f"Deleting document: {document_path} from {index_name}/{namespace}"
        )

        file_info = await self.storage.get_file(document_path)

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

        return await self.storage.delete_file(document_path, request)

    async def search(
        self,
        query: str,
        index_name: str,
        namespace: str,
        top_k: int = 3,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SearchResponseSchema:
        logger.info(
            f"Searching for '{query}' in {index_name}/{namespace}, top_k={top_k}"
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
