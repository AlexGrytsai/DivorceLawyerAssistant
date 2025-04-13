from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from src.services.rag_service.file_processors.directory_processor import (
    DirectoryProcessor,
)
from src.services.rag_service.schemas import DocumentSchema
from src.services.storage.shemas import (
    FileSchemaForFolder,
    FolderItem,
    FolderContentsSchema,
)


@pytest.fixture
def mock_file_processor_factory():
    return MagicMock()


@pytest.fixture
def mock_rag_storage():
    return AsyncMock()


@pytest.fixture
def directory_processor(mock_file_processor_factory, mock_rag_storage):
    return DirectoryProcessor(
        file_processor_factory=mock_file_processor_factory,
        rag_storage=mock_rag_storage,
    )


@pytest.fixture
def mock_file_schema():
    return FileSchemaForFolder(
        filename="test.pdf",
        path="/test/test.pdf",
        url="/test/test.pdf",
        type="file",
    )


@pytest.fixture
def mock_folder_item():
    return FolderItem(
        folder_name="test_folder",
        folder_path="/test/test_folder",
        type="folder",
    )


@pytest.fixture
def mock_document_schema():
    return DocumentSchema(
        id="test_id",
        text="test text",
        metadata={},
        file_path="/test/test.pdf",
        index_name="test_index",
        namespace="test_namespace",
    )


@pytest.mark.asyncio
async def test_process_directory(
    directory_processor,
    mock_rag_storage,
    mock_file_schema,
    mock_document_schema,
):
    mock_rag_storage.get_folder_contents.return_value = FolderContentsSchema(
        current_path="/test", items=[mock_file_schema]
    )

    processor = AsyncMock()
    processor.process_file.return_value = [mock_document_schema]
    directory_processor.file_processor_factory.get_processor.return_value = (
        processor
    )

    result = await directory_processor.process_directory(
        directory_path="/test",
        index_name="test_index",
        namespace="test_namespace",
    )

    assert len(result) == 1
    assert result[0] == mock_document_schema
    mock_rag_storage.get_folder_contents.assert_called_once_with("/test")
    processor.process_file.assert_called_once()


def test_filter_files(directory_processor, mock_file_schema, mock_folder_item):
    items = [mock_file_schema, mock_folder_item]
    filtered = directory_processor._filter_files(items)

    assert len(filtered) == 1
    assert filtered[0] == mock_file_schema


@pytest.mark.asyncio
async def test_process_single_file(
    directory_processor, mock_file_schema, mock_document_schema
):
    processor = AsyncMock()
    processor.process_file.return_value = [mock_document_schema]
    directory_processor.file_processor_factory.get_processor.return_value = (
        processor
    )

    result = await directory_processor._process_single_file(
        item=mock_file_schema,
        index_name="test_index",
        namespace="test_namespace",
    )

    assert len(result) == 1
    assert result[0] == mock_document_schema
    processor.process_file.assert_called_once()


@pytest.mark.asyncio
async def test_process_files(
    directory_processor, mock_file_schema, mock_document_schema
):
    processor = AsyncMock()
    processor.process_file.return_value = [mock_document_schema]
    directory_processor.file_processor_factory.get_processor.return_value = (
        processor
    )

    result = await directory_processor._process_files(
        files=[mock_file_schema, mock_file_schema],
        index_name="test_index",
        namespace="test_namespace",
    )

    assert len(result) == 2
    assert result[0] == mock_document_schema
    assert result[1] == mock_document_schema
    assert processor.process_file.call_count == 2


@pytest.mark.asyncio
async def test_process_directory_with_unsupported_file(
    directory_processor, mock_rag_storage, mock_file_schema
):
    mock_rag_storage.get_folder_contents.return_value = FolderContentsSchema(
        current_path="/test", items=[mock_file_schema]
    )

    directory_processor.file_processor_factory.get_processor.side_effect = (
        HTTPException(
            status_code=415, detail={"error": "Unsupported file type"}
        )
    )

    with pytest.raises(HTTPException) as exc_info:
        await directory_processor.process_directory(
            directory_path="/test",
            index_name="test_index",
            namespace="test_namespace",
        )

    assert exc_info.value.status_code == 422
    assert "Error processing document" in str(exc_info.value.detail)
