from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, create_autospec

import pytest
from fastapi import UploadFile, Request
from fastapi.exceptions import HTTPException

from src.services.storage.interfaces.base_storage_interface import (
    BaseStorageInterface,
)
from src.services.storage.shemas import (
    FileSchema,
    FileDeleteSchema,
    FolderDataSchema,
    FolderDeleteSchema,
    FolderContentsSchema,
    FileSchemaForFolder,
    FolderItem,
)


@pytest.fixture
def mock_upload_file():
    file = MagicMock(spec=UploadFile)
    file.filename = "test.txt"
    file.content_type = "text/plain"
    return file


@pytest.fixture
def mock_request():
    return MagicMock(spec=Request)


@pytest.fixture
def mock_storage_interface():
    mock = AsyncMock(spec=BaseStorageInterface)
    return mock


@pytest.fixture
def file_schema():
    return FileSchema(
        filename="test.txt",
        path="/test/test.txt",
        url="http://example.com/test.txt",
        size=100,
        content_type="text/plain",
    )


@pytest.fixture
def file_delete_schema():
    return FileDeleteSchema(
        file=Path("/test/test.txt"),
        date_deleted=datetime.now(timezone.utc),
    )


@pytest.fixture
def folder_data_schema():
    return FolderDataSchema(
        folder_name="test_folder",
        folder_path="/test",
        create_time=datetime.now(timezone.utc),
        update_time=datetime.now(timezone.utc),
    )


@pytest.fixture
def folder_delete_schema():
    return FolderDeleteSchema(
        folder_name="test_folder",
        deleted_time=datetime.now(timezone.utc),
    )


@pytest.fixture
def folder_contents_schema():
    return FolderContentsSchema(
        current_path="/test",
        items=[
            FileSchemaForFolder(
                filename="test.txt",
                path="/test/test.txt",
                url="http://example.com/test.txt",
                type="file",
            ),
            FolderItem(
                folder_name="subfolder",
                folder_path="/test/subfolder",
                type="folder",
            ),
        ],
    )


class TestBaseStorageInterface:
    async def test_call_with_single_file(
        self,
        mock_storage_interface,
        mock_upload_file,
        mock_request,
        file_schema,
    ):
        async def side_effect(request=None, file=None, files=None):
            if file is not None:
                return await mock_storage_interface.upload(file=file, request=request)
            return None
            
        mock_storage_interface.side_effect = side_effect
        mock_storage_interface.upload.return_value = file_schema
        
        result = await mock_storage_interface(
            request=mock_request, file=mock_upload_file
        )
        
        assert result == file_schema
        mock_storage_interface.upload.assert_called_once_with(
            file=mock_upload_file, request=mock_request
        )

    async def test_call_with_multiple_files(
        self,
        mock_storage_interface,
        mock_upload_file,
        mock_request,
        file_schema,
    ):
        async def side_effect(request=None, file=None, files=None):
            if files is not None:
                return await mock_storage_interface.multi_upload(files=files, request=request)
            return None
            
        mock_storage_interface.side_effect = side_effect
        mock_storage_interface.multi_upload.return_value = [file_schema]
        
        result = await mock_storage_interface(
            request=mock_request, files=[mock_upload_file]
        )
        
        assert result == [file_schema]
        mock_storage_interface.multi_upload.assert_called_once_with(
            files=[mock_upload_file], request=mock_request
        )

    async def test_call_with_no_files(
        self, mock_storage_interface, mock_request
    ):
        mock_storage_interface.side_effect = HTTPException(
            status_code=400, detail="No file or files provided"
        )
        with pytest.raises(HTTPException) as exc_info:
            await mock_storage_interface(request=mock_request)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "No file or files provided"

    async def test_upload(
        self,
        mock_storage_interface,
        mock_upload_file,
        mock_request,
        file_schema,
    ):
        mock_storage_interface.upload.return_value = file_schema
        result = await mock_storage_interface.upload(
            file=mock_upload_file, request=mock_request
        )
        assert result == file_schema

    async def test_multi_upload(
        self,
        mock_storage_interface,
        mock_upload_file,
        mock_request,
        file_schema,
    ):
        mock_storage_interface.multi_upload.return_value = [file_schema]
        result = await mock_storage_interface.multi_upload(
            files=[mock_upload_file], request=mock_request
        )
        assert result == [file_schema]

    async def test_delete_file(
        self, mock_storage_interface, mock_request, file_delete_schema
    ):
        mock_storage_interface.delete_file.return_value = file_delete_schema
        result = await mock_storage_interface.delete_file(
            file_path="/test/test.txt", request=mock_request
        )
        assert result == file_delete_schema

    async def test_create_folder(
        self, mock_storage_interface, mock_request, folder_data_schema
    ):
        mock_storage_interface.create_folder.return_value = folder_data_schema
        result = await mock_storage_interface.create_folder(
            folder_path="/test", request=mock_request
        )
        assert result == folder_data_schema

    async def test_rename_folder(
        self, mock_storage_interface, mock_request, folder_data_schema
    ):
        mock_storage_interface.rename_folder.return_value = folder_data_schema
        result = await mock_storage_interface.rename_folder(
            old_path="/old", new_path="/new", request=mock_request
        )
        assert result == folder_data_schema

    async def test_delete_folder(
        self, mock_storage_interface, mock_request, folder_delete_schema
    ):
        mock_storage_interface.delete_folder.return_value = (
            folder_delete_schema
        )
        result = await mock_storage_interface.delete_folder(
            folder_path="/test", request=mock_request, is_delete_all=True
        )
        assert result == folder_delete_schema

    async def test_get_folder(
        self, mock_storage_interface, folder_data_schema
    ):
        mock_storage_interface.get_folder.return_value = folder_data_schema
        result = await mock_storage_interface.get_folder(folder_path="/test")
        assert result == folder_data_schema

    async def test_rename_file(
        self, mock_storage_interface, mock_request, file_schema
    ):
        mock_storage_interface.rename_file.return_value = file_schema
        result = await mock_storage_interface.rename_file(
            old_path="/old.txt", new_file_name="new.txt", request=mock_request
        )
        assert result == file_schema

    async def test_get_file(self, mock_storage_interface, file_schema):
        mock_storage_interface.get_file.return_value = file_schema
        result = await mock_storage_interface.get_file(file_path="/test.txt")
        assert result == file_schema

    async def test_list_files(self, mock_storage_interface, file_schema):
        mock_storage_interface.list_files.return_value = [file_schema]
        result = await mock_storage_interface.list_files(
            prefix="/test", search_query="test", case_sensitive=True
        )
        assert result == [file_schema]

    async def test_list_folders(
        self, mock_storage_interface, folder_data_schema
    ):
        mock_storage_interface.list_folders.return_value = [folder_data_schema]
        result = await mock_storage_interface.list_folders(prefix="/test")
        assert result == [folder_data_schema]

    async def test_get_folder_contents(
        self, mock_storage_interface, folder_contents_schema
    ):
        mock_storage_interface.get_folder_contents.return_value = (
            folder_contents_schema
        )
        result = await mock_storage_interface.get_folder_contents(
            folder_path="/test"
        )
        assert result == folder_contents_schema
