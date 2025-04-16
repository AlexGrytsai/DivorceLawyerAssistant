import logging
from datetime import datetime
from typing import List, Union
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile, HTTPException, status

from src.core.config import settings
from src.core.constants import ALLOWED_MIME_TYPES_FOR_RAG
from src.domain.storage.entities import (
    FolderData,
    FileForFolder,
    File,
    FileDelete,
)
from src.domain.storage.entities.folder import (
    FolderDelete,
    FolderItem,
    FolderContents,
)
from src.domain.storage.repositories import StorageRepository
from src.services.rag_service.interfaces import (
    VectorDBInterface,
    RAGManagerInterface,
)
from src.services.rag_service.rag_service import RAGService
from src.services.rag_service.schemas import (
    IndexCreateSchema,
    IndexSchema,
    NamespaceCreateSchema,
    NamespaceSchema,
    SearchResponseSchema,
    ProcessingStatusSchema,
    IndexStatsSchema,
    Document,
    QueryResultSchema,
)

logger = logging.getLogger(__name__)


@pytest.fixture
def mock_storage():
    mock = AsyncMock(spec=StorageRepository)
    mock.create_folder = AsyncMock()
    mock.delete_folder = AsyncMock()
    mock.list_folders = AsyncMock()
    mock.get_folder_contents = AsyncMock()
    mock.upload = AsyncMock()
    mock.multi_upload = AsyncMock()
    mock.delete_file = AsyncMock()
    mock.get_file = AsyncMock()
    return mock


@pytest.fixture
def mock_vector_db():
    mock = MagicMock(spec=VectorDBInterface)  # Use MagicMock for sync methods
    mock.create_index = MagicMock(return_value=True)
    mock.delete_index = MagicMock(return_value=True)
    mock.list_indexes = MagicMock(return_value=["index1", "index2"])
    # Ensure get_index_stats_schema returns a valid schema instance
    mock.get_index_stats_schema = MagicMock(
        return_value=IndexStatsSchema(
            dimension=settings.DIMENSIONS_EMBEDDING,
            metric="cosine",
            namespaces={},
            total_vector_count=0,
        )
    )
    mock.delete_from_namespace = MagicMock(return_value=True)
    mock.list_namespaces = MagicMock(return_value=["ns1", "ns2"])
    return mock


@pytest.fixture
def mock_rag_manager():
    mock = AsyncMock(spec=RAGManagerInterface)
    mock.process_pdf_file = AsyncMock()
    mock.process_directory = AsyncMock()
    mock.search = AsyncMock()
    return mock


@pytest.fixture
def rag_service(mock_storage, mock_vector_db, mock_rag_manager):
    # Patch settings temporarily if needed, or pass mocks directly
    # For simplicity, passing mocks directly
    service = RAGService(
        storage_interface=mock_storage,
        vector_db_client=mock_vector_db,
        rag_manager=mock_rag_manager,
    )
    return service


# Mock Request object if needed, for now using None
mock_request = None


@pytest.mark.asyncio
class TestRAGService:
    @pytest.fixture(autouse=True)
    def mock_decorators(self):
        def mock_decorator(func):
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    logger.error(f"Error in {func.__name__}: {exc}")
                    raise exc

            return wrapper

        with patch(
            "src.services.rag_service.rag_service.handle_index_operation_exceptions",
            lambda f: mock_decorator(f),
        ), patch(
            "src.services.rag_service.rag_service.handle_namespace_operation_exceptions",
            lambda f: mock_decorator(f),
        ), patch(
            "src.services.rag_service.rag_service.handle_document_processing",
            lambda f: mock_decorator(f),
        ), patch(
            "src.services.rag_service.rag_service.handle_folder_operation_exceptions",
            lambda f: mock_decorator(f),
        ), patch(
            "src.services.rag_service.rag_service.handle_async_search_exceptions",
            lambda f: mock_decorator(f),
        ):
            yield

    # === Index Operations ===

    async def test_create_index_success(
        self, rag_service, mock_storage, mock_vector_db
    ):
        index_name = "test_index"
        dimension = 1024
        metric = "euclidean"
        mock_folder_data = FolderData(
            folder_name=index_name,
            folder_path=index_name,
            create_time=datetime.now(),
        )
        mock_storage.create_folder.return_value = mock_folder_data

        result = await rag_service.create_index(
            index_name, mock_request, dimension, metric
        )

        mock_storage.create_folder.assert_awaited_once_with(
            index_name, mock_request
        )
        mock_vector_db.create_index.assert_called_once_with(
            name=index_name, dimension=dimension, metric=metric
        )
        assert isinstance(result, IndexCreateSchema)
        assert result.name == index_name
        assert result.dimension == dimension
        assert result.metric == metric
        assert result.created_at == mock_folder_data.create_time

    async def test_create_index_storage_fails(
        self, rag_service, mock_storage, mock_vector_db
    ):
        index_name = "storage_fail_index"
        mock_storage.create_folder.side_effect = Exception("Storage error")

        # Decorator handles the exception, so we check mocks were not called
        # after the fail point
        with pytest.raises(Exception, match="Storage error"):
            await rag_service.create_index(index_name, mock_request)

        mock_storage.create_folder.assert_awaited_once_with(
            index_name, mock_request
        )
        mock_vector_db.create_index.assert_not_called()
        # Cleanup shouldn't happen
        mock_storage.delete_folder.assert_not_awaited()

    async def test_list_indexes_success(
        self, rag_service, mock_storage, mock_vector_db
    ):
        mock_db_indexes = ["index1", "index2"]
        mock_storage_folders = [
            FolderData(
                folder_name="index1",
                folder_path="index1",
                create_time=datetime.now(),
            ),
            FolderData(
                folder_name="index2",
                folder_path="index2",
                create_time=datetime.now(),
            ),
            # Folder exists, but no index in DB
            FolderData(folder_name="stale_folder", folder_path="stale_folder"),
        ]
        mock_stats1 = IndexStatsSchema(
            dimension=1536,
            metric="cosine",
            namespaces={},
            total_vector_count=0,
        )
        mock_stats2 = IndexStatsSchema(
            dimension=1024,
            metric="cosine",
            namespaces={},
            total_vector_count=0,
        )

        mock_vector_db.list_indexes.return_value = mock_db_indexes
        mock_storage.list_folders.return_value = mock_storage_folders
        mock_vector_db.get_index_stats_schema.side_effect = [
            mock_stats1,
            mock_stats2,
        ]

        result = await rag_service.list_indexes()

        mock_vector_db.list_indexes.assert_called_once()
        mock_storage.list_folders.assert_awaited_once()
        assert mock_vector_db.get_index_stats_schema.call_count == 2
        mock_vector_db.get_index_stats_schema.assert_any_call("index1")
        mock_vector_db.get_index_stats_schema.assert_any_call("index2")

        assert len(result) == 2
        assert all(isinstance(idx, IndexSchema) for idx in result)
        assert result[0].name == "index1"
        assert result[0].dimension == mock_stats1.dimension
        assert result[0].metric == mock_stats1.metric
        assert result[1].name == "index2"
        assert result[1].dimension == mock_stats2.dimension
        assert result[1].metric == mock_stats2.metric
        assert "stale_folder" not in [idx.name for idx in result]

    async def test_list_indexes_empty(
        self, rag_service, mock_storage, mock_vector_db
    ):
        mock_vector_db.list_indexes.return_value = []
        mock_storage.list_folders.return_value = []

        result = await rag_service.list_indexes()

        mock_vector_db.list_indexes.assert_called_once()
        mock_storage.list_folders.assert_awaited_once()
        mock_vector_db.get_index_stats_schema.assert_not_called()
        assert result == []

    async def test_list_indexes_mismatch(
        self, rag_service, mock_storage, mock_vector_db
    ):
        mock_db_indexes = ["index1"]  # Only index1 in DB
        mock_storage_folders = [
            FolderData(
                folder_name="index1",
                folder_path="index1",
                create_time=datetime.now(),
            ),
            # Only index2 in storage
            FolderData(folder_name="index2", folder_path="index2"),
        ]
        mock_stats1 = IndexStatsSchema(
            dimension=1536,
            metric="cosine",
            namespaces={},
            total_vector_count=0,
        )
        mock_vector_db.list_indexes.return_value = mock_db_indexes
        mock_storage.list_folders.return_value = mock_storage_folders
        mock_vector_db.get_index_stats_schema.return_value = mock_stats1

        result = await rag_service.list_indexes()

        mock_vector_db.list_indexes.assert_called_once()
        mock_storage.list_folders.assert_awaited_once()
        mock_vector_db.get_index_stats_schema.assert_called_once_with("index1")

        assert len(result) == 1
        assert result[0].name == "index1"

    async def test_delete_index_success(
        self, rag_service, mock_storage, mock_vector_db
    ):
        index_name = "index_to_delete"
        mock_delete_result = FolderDelete(
            folder_name=index_name, deleted_time=datetime.now()
        )
        mock_storage.delete_folder.return_value = mock_delete_result

        result = await rag_service.delete_index(index_name, mock_request)

        mock_vector_db.delete_index.assert_called_once_with(index_name)
        mock_storage.delete_folder.assert_awaited_once_with(
            folder_path=f"{index_name}/",
            request=mock_request,
            is_delete_all=True,
        )
        assert result == mock_delete_result

    async def test_delete_index_storage_fails(
        self, rag_service, mock_storage, mock_vector_db
    ):
        index_name = "storage_fail_delete"
        mock_vector_db.delete_index.return_value = True  # Vector DB succeeds
        mock_storage.delete_folder.side_effect = Exception(
            "Storage delete error"
        )

        # Decorator handles the exception
        with pytest.raises(Exception, match="Storage delete error"):
            await rag_service.delete_index(index_name, mock_request)

        mock_vector_db.delete_index.assert_called_once_with(index_name)
        mock_storage.delete_folder.assert_awaited_once_with(
            folder_path=f"{index_name}/",
            request=mock_request,
            is_delete_all=True,
        )

    # === Namespace Operations ===

    async def test_create_namespace_success(self, rag_service, mock_storage):
        index_name = "index1"
        namespace = "new_ns"
        expected_path = f"{index_name}/{namespace}/"
        mock_folder_data = FolderData(
            folder_name=namespace,
            folder_path=expected_path,
            create_time=datetime.now(),
        )
        mock_storage.create_folder.return_value = mock_folder_data

        result = await rag_service.create_namespace(
            index_name, namespace, mock_request
        )

        mock_storage.create_folder.assert_awaited_once_with(
            expected_path, mock_request
        )
        assert isinstance(result, NamespaceCreateSchema)
        assert result.name == namespace
        assert result.index_name == index_name
        assert result.created_at == mock_folder_data.create_time

    async def test_create_namespace_storage_fails(
        self, rag_service, mock_storage
    ):
        index_name = "index1"
        namespace = "fail_ns"
        expected_path = f"{index_name}/{namespace}/"
        mock_storage.create_folder.side_effect = Exception(
            "Cannot create folder"
        )

        # Decorator handles the exception
        with pytest.raises(Exception, match="Cannot create folder"):
            await rag_service.create_namespace(
                index_name, namespace, mock_request
            )

        mock_storage.create_folder.assert_awaited_once_with(
            expected_path, mock_request
        )

    async def test_list_namespaces_success(
        self, rag_service, mock_storage, mock_vector_db
    ):
        index_name = "index1"
        mock_db_namespaces = ["ns1", "ns2"]
        # Fix type hint for items
        mock_folder_items: List[Union[FileForFolder, FolderItem]] = [
            FolderItem(
                folder_name="ns1",
                type="folder",
                folder_path=f"{index_name}/ns1",
                create_time=datetime.now(),
            ),
            FolderItem(
                folder_name="ns2",
                type="folder",
                folder_path=f"{index_name}/ns2",
                create_time=datetime.now(),
            ),
            # Folder exists, not in DB
            FolderItem(
                folder_name="stale_ns_folder",
                type="folder",
                folder_path=f"{index_name}/stale_ns_folder",
            ),
            # File item - should be ignored
            FileForFolder(
                filename="somefile.txt",
                type="file",
                path=f"{index_name}/somefile.txt",
                url="",
            ),
        ]
        mock_folder_contents = FolderContents(
            current_path=index_name, items=mock_folder_items
        )

        mock_vector_db.list_namespaces.return_value = mock_db_namespaces
        mock_storage.get_folder_contents.return_value = mock_folder_contents

        result = await rag_service.list_namespaces(index_name)

        mock_vector_db.list_namespaces.assert_called_once_with(index_name)
        mock_storage.get_folder_contents.assert_awaited_once_with(index_name)

        assert len(result) == 2
        assert all(isinstance(ns, NamespaceSchema) for ns in result)
        assert result[0].name == "ns1"
        assert result[0].index_name == index_name
        assert result[1].name == "ns2"
        assert result[1].index_name == index_name
        assert "stale_ns_folder" not in [ns.name for ns in result]

    async def test_list_namespaces_empty(
        self, rag_service, mock_storage, mock_vector_db
    ):
        index_name = "index_empty_ns"
        mock_vector_db.list_namespaces.return_value = []
        mock_folder_contents = FolderContents(
            current_path=index_name, items=[]
        )
        mock_storage.get_folder_contents.return_value = mock_folder_contents

        result = await rag_service.list_namespaces(index_name)

        mock_vector_db.list_namespaces.assert_called_once_with(index_name)
        mock_storage.get_folder_contents.assert_awaited_once_with(index_name)
        assert result == []

    async def test_list_namespaces_mismatch(
        self, rag_service, mock_storage, mock_vector_db
    ):
        index_name = "index_mismatch_ns"
        mock_db_namespaces = ["ns1"]  # Only ns1 in DB
        mock_folder_items: List[Union[FileForFolder, FolderItem]] = [
            FolderItem(
                folder_name="ns1",
                type="folder",
                folder_path=f"{index_name}/ns1",
                create_time=datetime.now(),
            ),
            # Only ns2 folder exists
            FolderItem(
                folder_name="ns2",
                type="folder",
                folder_path=f"{index_name}/ns2",
            ),
        ]
        mock_folder_contents = FolderContents(
            current_path=index_name, items=mock_folder_items
        )

        mock_vector_db.list_namespaces.return_value = mock_db_namespaces
        mock_storage.get_folder_contents.return_value = mock_folder_contents

        result = await rag_service.list_namespaces(index_name)

        mock_vector_db.list_namespaces.assert_called_once_with(index_name)
        mock_storage.get_folder_contents.assert_awaited_once_with(index_name)

        assert len(result) == 1
        assert result[0].name == "ns1"

    async def test_delete_namespace_success(
        self, rag_service, mock_storage, mock_vector_db
    ):
        index_name = "index1"
        namespace = "ns_to_delete"
        expected_path = f"{index_name}/{namespace}/"
        mock_delete_result = FolderDelete(
            folder_name=namespace, deleted_time=datetime.now()
        )
        mock_storage.delete_folder.return_value = mock_delete_result

        result = await rag_service.delete_namespace(
            index_name, namespace, mock_request
        )

        mock_vector_db.delete_from_namespace.assert_called_once_with(
            index_name=index_name, namespace=namespace, is_delete_all=True
        )
        mock_storage.delete_folder.assert_awaited_once_with(
            folder_path=expected_path, request=mock_request, is_delete_all=True
        )
        assert result == mock_delete_result

    async def test_delete_namespace_storage_fails(
        self, rag_service, mock_storage, mock_vector_db
    ):
        index_name = "index1"
        namespace = "storage_fail_delete_ns"
        expected_path = f"{index_name}/{namespace}/"
        mock_vector_db.delete_from_namespace.return_value = True  # DB succeeds
        mock_storage.delete_folder.side_effect = Exception(
            "Storage NS delete error"
        )

        # Decorator handles the exception
        with pytest.raises(Exception, match="Storage NS delete error"):
            await rag_service.delete_namespace(
                index_name, namespace, mock_request
            )

        mock_vector_db.delete_from_namespace.assert_called_once_with(
            index_name=index_name, namespace=namespace, is_delete_all=True
        )
        mock_storage.delete_folder.assert_awaited_once_with(
            folder_path=expected_path, request=mock_request, is_delete_all=True
        )

    # === Document Operations ===

    @patch(
        "src.services.rag_service.rag_service.validate_file_mime",
        new_callable=AsyncMock,
    )
    async def test_upload_file_success(
        self, mock_validate, rag_service, mock_storage, mock_rag_manager
    ):
        index_name = "index1"
        namespace = "ns1"
        original_filename = "document.pdf"
        expected_path = f"{index_name}/{namespace}/{original_filename}"
        metadata = {"author": "test"}
        # Use MagicMock for UploadFile as it's not awaitable itself
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = original_filename
        # Ensure content_type is set if validate_file_mime uses it
        mock_file.content_type = "application/pdf"

        mock_file_info = File(
            filename=expected_path,
            path=expected_path,
            url="http://storage/path/to/file.pdf",
            size=1000,
            content_type="application/pdf",
        )
        mock_storage.upload.return_value = mock_file_info

        result = await rag_service.upload_file(
            index_name, namespace, mock_file, mock_request, metadata
        )

        mock_validate.assert_awaited_once_with(
            [mock_file], ALLOWED_MIME_TYPES_FOR_RAG
        )
        # Check if filename was modified before upload
        assert mock_file.filename == expected_path
        mock_storage.upload.assert_awaited_once_with(mock_file, mock_request)
        mock_rag_manager.process_pdf_file.assert_awaited_once_with(
            file_path=mock_file_info.url,
            index_name=index_name,
            namespace=namespace,
            metadata=metadata,
        )
        assert result == mock_file_info

    @patch(
        "src.services.rag_service.rag_service.validate_file_mime",
        new_callable=AsyncMock,
    )
    async def test_upload_file_rag_manager_fails(
        self, mock_validate, rag_service, mock_storage, mock_rag_manager
    ):
        index_name = "index1"
        namespace = "ns1"
        original_filename = "rag_fail.pdf"
        expected_path = f"{index_name}/{namespace}/{original_filename}"
        metadata = {"author": "test"}
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = original_filename
        mock_file.content_type = "application/pdf"
        mock_file_info = File(
            filename=expected_path,
            path=expected_path,
            url="http://storage/rag_fail.pdf",
        )
        mock_storage.upload.return_value = mock_file_info
        mock_rag_manager.process_pdf_file.side_effect = Exception(
            "RAG processing error"
        )

        # Decorator handles the exception
        with pytest.raises(Exception, match="RAG processing error"):
            await rag_service.upload_file(
                index_name, namespace, mock_file, mock_request, metadata
            )

        mock_validate.assert_awaited_once_with(
            [mock_file], ALLOWED_MIME_TYPES_FOR_RAG
        )
        assert mock_file.filename == expected_path
        mock_storage.upload.assert_awaited_once_with(mock_file, mock_request)
        mock_rag_manager.process_pdf_file.assert_awaited_once_with(
            file_path=mock_file_info.url,
            index_name=index_name,
            namespace=namespace,
            metadata=metadata,
        )

    @patch(
        "src.services.rag_service.rag_service.validate_file_mime",
        new_callable=AsyncMock,
    )
    async def test_upload_files_success(
        self, mock_validate, rag_service, mock_storage, mock_rag_manager
    ):
        index_name = "index1"
        namespace = "ns1"
        metadata = {"source": "batch"}
        mock_file1 = MagicMock(spec=UploadFile)
        mock_file1.filename = "doc1.pdf"
        mock_file1.content_type = "application/pdf"
        mock_file2 = MagicMock(spec=UploadFile)
        mock_file2.filename = "doc2.pdf"
        mock_file2.content_type = "application/pdf"
        files = [mock_file1, mock_file2]
        expected_path1 = f"{index_name}/{namespace}/doc1.pdf"
        expected_path2 = f"{index_name}/{namespace}/doc2.pdf"
        mock_file_info1 = File(
            filename=expected_path1, path=expected_path1, url="url1"
        )
        mock_file_info2 = File(
            filename=expected_path2, path=expected_path2, url="url2"
        )
        mock_files_info = [mock_file_info1, mock_file_info2]
        mock_storage.multi_upload.return_value = mock_files_info

        result = await rag_service.upload_files(
            index_name, namespace, files, mock_request, metadata
        )

        mock_validate.assert_awaited_once_with(
            files, ALLOWED_MIME_TYPES_FOR_RAG
        )
        # Check filenames modified
        assert mock_file1.filename == expected_path1
        assert mock_file2.filename == expected_path2
        mock_storage.multi_upload.assert_awaited_once_with(files, mock_request)
        assert mock_rag_manager.process_pdf_file.await_count == 2
        mock_rag_manager.process_pdf_file.assert_any_await(
            file_path="url1",
            index_name=index_name,
            namespace=namespace,
            metadata=metadata,
        )
        mock_rag_manager.process_pdf_file.assert_any_await(
            file_path="url2",
            index_name=index_name,
            namespace=namespace,
            metadata=metadata,
        )
        assert result == mock_files_info

    @patch(
        "src.services.rag_service.rag_service.validate_file_mime",
        new_callable=AsyncMock,
    )
    async def test_upload_files_empty_list(
        self, mock_validate, rag_service, mock_storage, mock_rag_manager
    ):
        index_name = "index1"
        namespace = "ns1"
        files: List[UploadFile] = []
        # Mock storage to return [] when called with []
        mock_storage.multi_upload.return_value = []

        result = await rag_service.upload_files(
            index_name, namespace, files, mock_request
        )

        mock_validate.assert_awaited_once_with(
            files, ALLOWED_MIME_TYPES_FOR_RAG
        )
        # Assume storage handles empty list correctly
        mock_storage.multi_upload.assert_awaited_once_with(files, mock_request)
        mock_rag_manager.process_pdf_file.assert_not_awaited()
        # Assuming storage returns [] for empty upload
        assert result == []

    async def test_upload_folder_success(self, rag_service, mock_rag_manager):
        index_name = "index1"
        namespace = "ns1"
        folder_path = "/path/to/folder"
        metadata = {"project": "xyz"}
        # Mock Document requires all fields
        mock_documents = [
            Document(
                id="1",
                text="text1",
                metadata={},
                file_path="f1",
                index_name=index_name,
                namespace=namespace,
            ),
            Document(
                id="2",
                text="text2",
                metadata={},
                file_path="f2",
                index_name=index_name,
                namespace=namespace,
            ),
        ]
        mock_rag_manager.process_directory.return_value = mock_documents

        result = await rag_service.upload_folder(
            index_name, namespace, folder_path, metadata
        )

        mock_rag_manager.process_directory.assert_awaited_once_with(
            directory_path=folder_path,
            index_name=index_name,
            namespace=namespace,
            metadata=metadata,
        )
        assert isinstance(result, ProcessingStatusSchema)
        assert result.index_name == index_name
        assert result.namespace == namespace
        assert result.status == "completed"
        assert result.total_files == 2
        assert result.processed_files == 2

    async def test_upload_folder_no_files_processed(
        self, rag_service, mock_rag_manager
    ):
        index_name = "index1"
        namespace = "ns1"
        folder_path = "/empty/folder"
        metadata = None
        # Simulate empty or no compatible files
        mock_rag_manager.process_directory.return_value = []

        result = await rag_service.upload_folder(
            index_name, namespace, folder_path, metadata
        )

        mock_rag_manager.process_directory.assert_awaited_once_with(
            directory_path=folder_path,
            index_name=index_name,
            namespace=namespace,
            metadata=metadata,
        )
        assert isinstance(result, ProcessingStatusSchema)
        assert result.status == "completed"
        assert result.total_files == 0
        assert result.processed_files == 0

    async def test_delete_document_success(
        self, rag_service, mock_storage, mock_vector_db
    ):
        index_name = "index1"
        namespace = "ns1"
        doc_path = f"{index_name}/{namespace}/doc_to_delete.pdf"
        mock_file_info = File(
            filename=doc_path, path=doc_path, url="http://storage/delete.pdf"
        )
        mock_delete_result = FileDelete(file=doc_path)

        mock_storage.get_file.return_value = mock_file_info
        mock_storage.delete_file.return_value = mock_delete_result
        mock_vector_db.delete_from_namespace.return_value = True

        result = await rag_service.delete_document(
            index_name, namespace, doc_path, mock_request
        )

        mock_storage.get_file.assert_awaited_once_with(doc_path)
        mock_vector_db.delete_from_namespace.assert_called_once_with(
            index_name=index_name,
            namespace=namespace,
            filter_={"source": mock_file_info.url},
        )
        mock_storage.delete_file.assert_awaited_once_with(
            doc_path, mock_request
        )
        assert result == mock_delete_result

    async def test_delete_document_vector_db_fails(
        self, rag_service, mock_storage, mock_vector_db
    ):
        index_name = "index1"
        namespace = "ns1"
        document_path = f"{index_name}/{namespace}/doc_db_fail.pdf"
        mock_file_info = File(
            filename=document_path,
            path=document_path,
            url="http://storage/db_fail.pdf",
        )
        mock_storage.get_file.return_value = mock_file_info
        mock_vector_db.delete_from_namespace.return_value = (
            False  # Simulate DB failure
        )
        expected_error_msg = (
            f"Error in document processing operation delete_document: "
            f"Failed to delete vectors for {document_path} from Pinecone"
        )
        with pytest.raises(HTTPException) as exc_info:
            await rag_service.delete_document(
                index_name, namespace, document_path, mock_request
            )
        assert exc_info.value.status_code == (
            status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        assert expected_error_msg in str(exc_info.value.detail)

    async def test_delete_document_storage_delete_fails(
        self, rag_service, mock_storage, mock_vector_db
    ):
        index_name = "index1"
        namespace = "ns1"
        document_path = f"{index_name}/{namespace}/doc_storage_delete_fail.pdf"
        mock_file_info = File(
            filename=document_path,
            path=document_path,
            url="http://storage/delete_fail.pdf",
        )

        mock_storage.get_file.return_value = mock_file_info
        mock_vector_db.delete_from_namespace.return_value = True  # DB succeeds
        mock_storage.delete_file.side_effect = Exception(
            "Storage delete error"
        )

        # Decorator handles the exception
        with pytest.raises(Exception, match="Storage delete error"):
            await rag_service.delete_document(
                index_name, namespace, document_path, mock_request
            )

        mock_storage.get_file.assert_awaited_once_with(document_path)
        mock_vector_db.delete_from_namespace.assert_called_once_with(
            index_name=index_name,
            namespace=namespace,
            filter_={"source": mock_file_info.url},
        )
        mock_storage.delete_file.assert_awaited_once_with(
            document_path, mock_request
        )

    # === Search Operations ===

    async def test_search_success(self, rag_service, mock_rag_manager):
        query = "test query"
        index_name = "index1"
        namespace = "ns1"
        top_k = 5
        filters = {"year": 2023}
        # Mock QueryResultSchema requires all fields
        mock_search_results = [
            QueryResultSchema(
                id="doc1",
                text="text1",
                metadata={},
                score=0.9,
                file_path="path1",
            ),
            QueryResultSchema(
                id="doc2",
                text="text2",
                metadata={},
                score=0.8,
                file_path="path2",
            ),
        ]
        mock_rag_manager.search.return_value = mock_search_results

        result = await rag_service.search(
            query, index_name, namespace, top_k, filters
        )

        mock_rag_manager.search.assert_awaited_once_with(
            query=query,
            index_name=index_name,
            namespace=namespace,
            top_k=top_k,
            filters=filters,
        )
        assert isinstance(result, SearchResponseSchema)
        assert result.query == query
        assert result.results == mock_search_results
        assert result.total == len(mock_search_results)

    async def test_search_no_results(self, rag_service, mock_rag_manager):
        query = "no match query"
        index_name = "index1"
        namespace = "ns1"
        top_k = 3
        mock_rag_manager.search.return_value = []  # Simulate no results found

        result = await rag_service.search(query, index_name, namespace, top_k)

        mock_rag_manager.search.assert_awaited_once_with(
            query=query,
            index_name=index_name,
            namespace=namespace,
            top_k=top_k,
            filters=None,
        )
        assert isinstance(result, SearchResponseSchema)
        assert result.query == query
        assert result.results == []
        assert result.total == 0

    async def test_search_rag_manager_fails(
        self, rag_service, mock_rag_manager
    ):
        query = "error query"
        index_name = "index1"
        namespace = "ns1"
        mock_rag_manager.search.side_effect = Exception("Search failed")

        # Decorator handles the exception
        with pytest.raises(Exception, match="Search failed"):
            await rag_service.search(query, index_name, namespace)

        mock_rag_manager.search.assert_awaited_once_with(
            query=query,
            index_name=index_name,
            namespace=namespace,
            top_k=3,  # Default value
            filters=None,
        )
