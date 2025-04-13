from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from fastapi import HTTPException, UploadFile, Request
from google.cloud.storage_control_v2 import RenameFolderRequest

from src.services.storage.cloud_storage import (
    _validate_blob_exists,
    _validate_blob_not_exists,
    CloudStorage,
)
from src.services.storage.interfaces import CloudStorageInterface
from src.services.storage.shemas import (
    FileSchema,
    FileDeleteSchema,
    FolderBaseSchema,
    FolderDeleteSchema,
    FileSchemaForFolder,
    FolderItem,
    FolderContentsSchema,
    FolderDataSchema,
)
from src.utils.path_handler import PathHandler


class MockBlob:
    def __init__(self, exists_value=True):
        self._exists = exists_value

    def exists(self):
        return self._exists


class MockBucket:
    def __init__(self, blobs=None):
        self.blobs = blobs or {}

    def blob(self, blob_name):
        if blob_name in self.blobs:
            return self.blobs[blob_name]
        return MockBlob(exists_value=False)


class MockCloudStorage(AsyncMock):
    def __init__(self, *args, **kwargs):
        super().__init__(spec=CloudStorageInterface)
        self.bucket = kwargs.get("bucket", MockBucket())
        self.base_url = "https://storage.example.com"

        # Configure default return values
        self.upload_blob.return_value = FileSchema(
            filename="test.txt",
            path="test.txt",
            url=f"{self.base_url}/test.txt",
            size=100,
            content_type="text/plain",
        )

        self.delete_blob.return_value = FileDeleteSchema(file="test.txt")

        self.get_blob.return_value = FileSchema(
            filename="test.txt",
            path="test.txt",
            url=f"{self.base_url}/test.txt",
            size=100,
            content_type="text/plain",
        )

        self.rename_blob.return_value = FileSchema(
            filename="new_test.txt",
            path="new_test.txt",
            url=f"{self.base_url}/new_test.txt",
            size=100,
            content_type="text/plain",
        )

        self.list_blobs.return_value = [
            FileSchema(
                filename="test1.txt",
                path="test1.txt",
                url=f"{self.base_url}/test1.txt",
                size=100,
                content_type="text/plain",
            ),
            FileSchema(
                filename="test2.txt",
                path="test2.txt",
                url=f"{self.base_url}/test2.txt",
                size=200,
                content_type="text/plain",
            ),
        ]

        self.create_folder.return_value = FolderBaseSchema(
            folder_name="test_folder"
        )

        self.get_folder.return_value = FolderDataSchema(
            folder_name="test_folder",
            folder_path="test_folder",
            create_time=None,
            update_time=None,
        )

        self.delete_folder.return_value = FolderDeleteSchema(
            folder_name="test_folder"
        )

        self.rename_folder.return_value = MagicMock(spec=RenameFolderRequest)

        self.list_folders.return_value = [
            FolderDataSchema(
                folder_name="folder1",
                folder_path="folder1",
                create_time=None,
                update_time=None,
            ),
            FolderDataSchema(
                folder_name="folder2",
                folder_path="folder2",
                create_time=None,
                update_time=None,
            ),
        ]


@pytest.fixture
def cloud_storage_mock():
    mock_bucket = MockBucket(
        {
            "test.txt": MockBlob(exists_value=True),
            "existing_file.txt": MockBlob(exists_value=True),
            "folder/": MockBlob(exists_value=True),
        }
    )
    return MockCloudStorage(bucket=mock_bucket)


@pytest.fixture
def path_handler_mock():
    return MagicMock(spec=PathHandler)


@pytest.fixture
def cloud_storage(cloud_storage_mock, path_handler_mock):
    path_handler_mock.normalize_path.side_effect = lambda x: x
    path_handler_mock.get_basename.side_effect = lambda x: x.split("/")[-1]

    return CloudStorage(
        project_id="test-project",
        bucket_name="test-bucket",
        path_handler=path_handler_mock,
        cloud_storage=cloud_storage_mock,
    )


@pytest.fixture
def upload_file_mock():
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.txt"
    mock_file.content_type = "text/plain"
    mock_file.read = AsyncMock(return_value=b"test content")
    return mock_file


@pytest.fixture
def request_mock():
    mock_request = MagicMock(spec=Request)
    mock_request.client.host = "127.0.0.1"
    mock_request.scope = {}
    return mock_request


# Tests for _validate_blob_exists
class TestValidateBlob:
    def test_validate_blob_exists_success(self, cloud_storage_mock):
        # Check that function does not raise exception if blob exists
        _validate_blob_exists(cloud_storage_mock, "test.txt")

    def test_validate_blob_exists_failure(self, cloud_storage_mock):
        # Check that function raises HTTPException if blob does not exist
        with pytest.raises(HTTPException) as exc_info:
            _validate_blob_exists(cloud_storage_mock, "non_existent.txt")

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail["message"]

    def test_validate_blob_exists_custom_error_code(self, cloud_storage_mock):
        # Check that function uses specified error code
        with pytest.raises(HTTPException) as exc_info:
            _validate_blob_exists(
                cloud_storage_mock, "non_existent.txt", error_code=400
            )

        assert exc_info.value.status_code == 400

    def test_validate_blob_not_exists_success(self, cloud_storage_mock):
        # Check that function does not raise exception if blob does not exist
        _validate_blob_not_exists(cloud_storage_mock, "non_existent.txt")

    def test_validate_blob_not_exists_failure(self, cloud_storage_mock):
        # Check that function raises HTTPException if blob exists
        with pytest.raises(HTTPException) as exc_info:
            _validate_blob_not_exists(cloud_storage_mock, "test.txt")

        assert exc_info.value.status_code == 409
        assert "already exists" in exc_info.value.detail["message"]

    def test_validate_blob_not_exists_custom_error_code(
        self, cloud_storage_mock
    ):
        # Check that function uses specified error code
        with pytest.raises(HTTPException) as exc_info:
            _validate_blob_not_exists(
                cloud_storage_mock, "test.txt", error_code=400
            )

        assert exc_info.value.status_code == 400


# Tests for CloudStorage
class TestCloudStorage:
    @pytest.mark.asyncio
    async def test_upload(self, cloud_storage, upload_file_mock, request_mock):
        # Check successful file upload
        result = await cloud_storage.upload(upload_file_mock, request_mock)

        assert isinstance(result, FileSchema)
        assert result.filename == "test.txt"
        # Check that cloud_storage.upload_blob was called with correct parameters
        cloud_storage._cloud_storage.upload_blob.assert_called_once_with(
            "test.txt", b"test content", "text/plain"
        )

    @pytest.mark.asyncio
    async def test_upload_empty_filename(self, cloud_storage, request_mock):
        # Check case when filename is empty
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = None
        mock_file.read = AsyncMock(return_value=b"test content")

        with pytest.raises(ValueError) as exc_info:
            await cloud_storage.upload(mock_file, request_mock)

        assert "File name cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_multi_upload(
        self, cloud_storage, upload_file_mock, request_mock
    ):
        # Create multiple files for testing multiple upload
        files = [upload_file_mock, upload_file_mock]

        result = await cloud_storage.multi_upload(files, request_mock)

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, FileSchema) for item in result)
        # Check that cloud_storage.upload_blob was called twice
        assert cloud_storage._cloud_storage.upload_blob.call_count == 2

    @pytest.mark.asyncio
    async def test_delete_file(self, cloud_storage, request_mock):
        result = await cloud_storage.delete_file("test.txt", request_mock)

        assert isinstance(result, FileDeleteSchema)
        cloud_storage._cloud_storage.delete_blob.assert_called_once_with(
            "test.txt"
        )

    @pytest.mark.asyncio
    async def test_rename_file(self, cloud_storage, request_mock):
        result = await cloud_storage.rename_file(
            "test.txt", "new_test.txt", request_mock
        )

        assert isinstance(result, FileSchema)
        assert result.filename == "new_test.txt"
        cloud_storage._cloud_storage.rename_blob.assert_called_once_with(
            "test.txt", "new_test.txt"
        )

    @pytest.mark.asyncio
    async def test_delete_all_files(self, cloud_storage, request_mock):
        # Configure return value for list_blobs
        cloud_storage._cloud_storage.list_blobs.return_value = [
            FileSchema(
                filename="test1.txt", path="prefix/test1.txt", url="url1"
            ),
            FileSchema(
                filename="test2.txt", path="prefix/test2.txt", url="url2"
            ),
        ]

        result = await cloud_storage.delete_all_files("prefix/", request_mock)

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, FileDeleteSchema) for item in result)
        cloud_storage._cloud_storage.list_blobs.assert_called_once_with(
            prefix="prefix/"
        )
        assert (
            cloud_storage._cloud_storage.delete_blob.call_count == 2
        )  # Should be 2 calls for each file

    @pytest.mark.asyncio
    async def test_create_folder(self, cloud_storage, request_mock):
        cloud_storage._path_handler.normalize_path.return_value = "test_folder"

        result = await cloud_storage.create_folder("test_folder", request_mock)

        assert isinstance(result, FolderBaseSchema)
        assert result.folder_name == "test_folder"
        cloud_storage._path_handler.normalize_path.assert_called_once_with(
            "test_folder"
        )
        cloud_storage._cloud_storage.create_folder.assert_called_once_with(
            "test_folder"
        )

    @pytest.mark.asyncio
    async def test_create_folder_already_exists(
        self, cloud_storage, request_mock
    ):
        # Configure mock to raise error for existing folder
        cloud_storage._path_handler.normalize_path.return_value = "folder"
        cloud_storage._cloud_storage.bucket = MockBucket(
            {"folder": MockBlob(exists_value=True)}
        )

        with pytest.raises(HTTPException) as exc_info:
            await cloud_storage.create_folder("folder", request_mock)

        assert exc_info.value.status_code == 409
        assert "already exists" in exc_info.value.detail["message"]

    @pytest.mark.asyncio
    async def test_rename_folder(self, cloud_storage, request_mock):
        cloud_storage._path_handler.normalize_path.side_effect = (
            lambda x: f"{x}/"
        )

        result = await cloud_storage.rename_folder(
            "old_folder", "new_folder", request_mock
        )

        assert isinstance(
            result, MagicMock
        )  # In test this will be MagicMock with spec=RenameFolderRequest
        # Check normalize_path calls for both paths
        assert cloud_storage._path_handler.normalize_path.call_count == 2
        cloud_storage._cloud_storage.rename_folder.assert_called_once_with(
            "old_folder/", "new_folder/"
        )

    @pytest.mark.asyncio
    async def test_delete_folder(self, cloud_storage, request_mock):
        result = await cloud_storage.delete_folder("test_folder", request_mock)

        assert isinstance(result, FolderDeleteSchema)
        assert result.folder_name == "test_folder"
        cloud_storage._cloud_storage.delete_folder.assert_called_once_with(
            "test_folder", is_delete_all=False
        )

    @pytest.mark.asyncio
    async def test_delete_folder_with_all_contents(
        self, cloud_storage, request_mock
    ):
        result = await cloud_storage.delete_folder(
            "test_folder", request_mock, is_delete_all=True
        )

        assert isinstance(result, FolderDeleteSchema)
        cloud_storage._cloud_storage.delete_folder.assert_called_once_with(
            "test_folder", is_delete_all=True
        )

    @pytest.mark.asyncio
    async def test_upload_file(self, cloud_storage):
        # Check file upload by path
        result = await cloud_storage.upload_file("local/path/test.txt")

        assert isinstance(result, FileSchema)
        # In this case PathHandler.get_basename should be called
        cloud_storage._path_handler.get_basename.assert_called_once_with(
            "local/path/test.txt"
        )
        cloud_storage._cloud_storage.upload_blob.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_file_with_destination(self, cloud_storage):
        # Check file upload with specified destination path
        result = await cloud_storage.upload_file(
            "local/path/test.txt", "custom/path/file.txt"
        )

        assert isinstance(result, FileSchema)
        # In this case PathHandler.get_basename should NOT be called
        cloud_storage._path_handler.get_basename.assert_not_called()
        cloud_storage._cloud_storage.upload_blob.assert_called_once_with(
            "local/path/test.txt", "custom/path/file.txt"
        )

    @pytest.mark.asyncio
    async def test_upload_file_empty_path(self, cloud_storage):
        # Check case with empty path
        with pytest.raises(ValueError) as exc_info:
            await cloud_storage.upload_file("")

        assert "File path cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_file(self, cloud_storage):
        result = await cloud_storage.get_file("test.txt")

        assert isinstance(result, FileSchema)
        assert result.filename == "test.txt"
        cloud_storage._cloud_storage.get_blob.assert_called_once_with(
            "test.txt"
        )

    @pytest.mark.asyncio
    async def test_list_files(self, cloud_storage):
        # Check standard call without parameters
        result = await cloud_storage.list_files()

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, FileSchema) for item in result)
        cloud_storage._cloud_storage.list_blobs.assert_called_once_with(
            prefix="", search_query="", case_sensitive=False
        )

    @pytest.mark.asyncio
    async def test_list_files_with_params(self, cloud_storage):
        # Check call with parameters
        result = await cloud_storage.list_files(
            prefix="test/", search_query="file", case_sensitive=True
        )

        assert isinstance(result, list)
        cloud_storage._cloud_storage.list_blobs.assert_called_once_with(
            prefix="test/", search_query="file", case_sensitive=True
        )

    @pytest.mark.asyncio
    async def test_list_folders(self, cloud_storage):
        result = await cloud_storage.list_folders()

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, FolderDataSchema) for item in result)
        cloud_storage._cloud_storage.list_folders.assert_called_once_with(
            prefix=None
        )

    @pytest.mark.asyncio
    async def test_list_folders_with_prefix(self, cloud_storage):
        await cloud_storage.list_folders(prefix="test/")

        cloud_storage._cloud_storage.list_folders.assert_called_once_with(
            prefix="test/"
        )

    @pytest.mark.asyncio
    async def test_get_folder(self, cloud_storage):
        result = await cloud_storage.get_folder("test_folder")

        assert isinstance(result, FolderDataSchema)
        assert result.folder_name == "test_folder"
        cloud_storage._cloud_storage.get_folder.assert_called_once_with(
            "test_folder"
        )

    @pytest.mark.asyncio
    async def test_get_folder_contents(self, cloud_storage):
        # Configure return values for required methods
        cloud_storage._normalize_folder_path = MagicMock(
            return_value="folder/"
        )

        cloud_storage._cloud_storage.list_blobs.return_value = [
            FileSchema(
                filename="file1.txt", path="folder/file1.txt", url="url1"
            ),
            FileSchema(
                filename="subfolder/file2.txt",
                path="folder/subfolder/file2.txt",
                url="url2",
            ),
        ]

        # Mock internal class methods
        with patch.object(
            cloud_storage, "_separate_files_and_folders"
        ) as mock_separate:
            files = [
                FileSchemaForFolder(
                    filename="file1.txt",
                    path="folder/file1.txt",
                    url="url1",
                    type="file",
                )
            ]
            folders = {"folder/subfolder"}
            mock_separate.return_value = (files, folders)

            with patch.object(
                cloud_storage, "_get_folder_items"
            ) as mock_get_items:
                folder_items = [
                    FolderItem(
                        folder_name="subfolder",
                        folder_path="folder/subfolder",
                        type="folder",
                    )
                ]
                mock_get_items.return_value = folder_items

                with patch.object(
                    cloud_storage, "_combine_items"
                ) as mock_combine:
                    combined_items = [*folder_items, *files]
                    mock_combine.return_value = combined_items

                    result = await cloud_storage.get_folder_contents("folder")

                    assert isinstance(result, FolderContentsSchema)
                    assert result.current_path == "folder"
                    assert result.items == combined_items

    def test_get_user_identifier_with_user(self, cloud_storage):
        mock_request = MagicMock(spec=Request)
        mock_request.scope = {"user": "test_user"}

        result = cloud_storage._get_user_identifier(mock_request)

        assert result == "test_user"

    def test_get_user_identifier_with_client(self, cloud_storage):
        mock_request = MagicMock(spec=Request)
        mock_request.scope = {}
        mock_request.client.host = "127.0.0.1"

        result = cloud_storage._get_user_identifier(mock_request)

        assert result == "127.0.0.1"

    def test_get_user_identifier_unknown(self, cloud_storage):
        mock_request = MagicMock(spec=Request)
        mock_request.scope = {}
        mock_request.client = None

        result = cloud_storage._get_user_identifier(mock_request)

        assert result == "Unknown"

    def test_separate_files_and_folders(self, cloud_storage):
        # Create test data
        blobs = [
            FileSchema(
                filename="file1.txt", path="folder/file1.txt", url="url1"
            ),
            FileSchema(
                filename="subfolder/file2.txt",
                path="folder/subfolder/file2.txt",
                url="url2",
            ),
            FileSchema(
                filename="subfolder/subfile/file3.txt",
                path="folder/subfolder/subfile/file3.txt",
                url="url3",
            ),
        ]

        # Mock internal method
        with patch.object(
            cloud_storage, "_process_file_item"
        ) as mock_process_file:
            mock_process_file.side_effect = (
                lambda **kwargs: FileSchemaForFolder(**kwargs, type="file")
            )

            files, folders = cloud_storage._separate_files_and_folders(
                blobs, "folder/"
            )

            # Check results
            assert len(files) == 1
            assert len(folders) == 1  # Only subfolder
            assert "folder/subfolder" in folders
            assert mock_process_file.call_count == 1  # Only for file1.txt

    def test_sort_folder_items(self, cloud_storage):
        # Create test items of different types
        folder1 = FolderItem(
            folder_name="folder_b", folder_path="path/folder_b", type="folder"
        )
        folder2 = FolderItem(
            folder_name="folder_a", folder_path="path/folder_a", type="folder"
        )
        file1 = FileSchemaForFolder(
            filename="file_b.txt",
            path="path/file_b.txt",
            url="url1",
            type="file",
        )
        file2 = FileSchemaForFolder(
            filename="file_a.txt",
            path="path/file_a.txt",
            url="url2",
            type="file",
        )

        items = [file1, folder1, file2, folder2]
        sorted_items = cloud_storage._sort_folder_items(items)

        # Check that folders come first (sorted by name), then files
        assert sorted_items[0] == folder2  # folder_a
        assert sorted_items[1] == folder1  # folder_b
        assert sorted_items[2] == file2  # file_a.txt
        assert sorted_items[3] == file1  # file_b.txt

    def test_normalize_folder_path(self, cloud_storage):
        # Test different input data
        assert CloudStorage._normalize_folder_path("folder") == "folder/"
        assert CloudStorage._normalize_folder_path("folder/") == "folder/"
        assert CloudStorage._normalize_folder_path("/folder") == "folder/"
        assert CloudStorage._normalize_folder_path("/folder/") == "folder/"
        assert CloudStorage._normalize_folder_path("") == ""

    def test_get_relative_path(self, cloud_storage):
        # Check relative path extraction
        assert (
            CloudStorage._get_relative_path("folder/file.txt", "folder/")
            == "file.txt"
        )
        assert (
            CloudStorage._get_relative_path(
                "folder/subfolder/file.txt", "folder/"
            )
            == "subfolder/file.txt"
        )
        assert CloudStorage._get_relative_path("file.txt", "") == "file.txt"

        # Edge case
        assert CloudStorage._get_relative_path("folder/", "folder/") == ""
