import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.cloud.storage import Blob, Bucket
from google.cloud.storage_control_v2 import (
    CreateFolderRequest,
    DeleteFolderRequest,
    RenameFolderRequest,
)

from src.domain.storage.entities import File, FileDelete, FolderData
from src.domain.storage.entities.folder import FolderDelete, FolderRename
from src.infrastructure.storage.cloud.google_cloud.google_storage import (
    GoogleCloudStorage,
)


@pytest.fixture
def mock_storage_client():
    with patch(
        "src.infrastructure.storage.cloud.google_cloud.google_storage.storage.Client"
    ) as mock_client:
        yield mock_client


@pytest.fixture
def mock_storage_control_client():
    with patch(
        "src.infrastructure.storage.cloud.google_cloud.google_storage.StorageControlClient"
    ) as mock_control:
        yield mock_control


@pytest.fixture
def mock_bucket():
    bucket = MagicMock(spec=Bucket)
    bucket.name = "test-bucket"
    return bucket


@pytest.fixture
def mock_blob():
    blob = MagicMock(spec=Blob)
    blob.name = "test/file.txt"
    blob.public_url = (
        "https://storage.googleapis.com/test-bucket/test/file.txt"
    )
    blob.size = 1024
    blob.content_type = "text/plain"
    return blob


@pytest.fixture
def cloud_storage(
    mock_storage_client, mock_storage_control_client, mock_bucket
):
    storage = GoogleCloudStorage(
        bucket_name="test-bucket", project_id="test-project"
    )

    # Configure mocks
    mock_storage_client.return_value.get_bucket.return_value = mock_bucket
    storage._client = mock_storage_client.return_value
    storage._bucket = mock_bucket
    storage._storage_control = mock_storage_control_client.return_value

    return storage


class TestGoogleCloudStorage:

    def test_base_url(self, cloud_storage):
        assert (
            cloud_storage.base_url
            == "https://storage.googleapis.com/test-bucket"
        )

    def test_client_property(self, cloud_storage, mock_storage_client):
        # Set client to None to force the client property to create a new one
        cloud_storage._client = None
        client = cloud_storage.client
        mock_storage_client.assert_called_once_with(project="test-project")
        assert client == mock_storage_client.return_value

    def test_storage_control_property(
        self, cloud_storage, mock_storage_control_client
    ):
        # Set storage_control to None to force the property to create a new one
        cloud_storage._storage_control = None
        control = cloud_storage.storage_control
        mock_storage_control_client.assert_called_once()
        assert control == mock_storage_control_client.return_value

    def test_bucket_property(
        self, cloud_storage, mock_storage_client, mock_bucket
    ):
        cloud_storage._bucket = None
        bucket = cloud_storage.bucket
        mock_storage_client.return_value.get_bucket.assert_called_once_with(
            bucket_or_name="test-bucket"
        )
        assert bucket == mock_bucket

    @pytest.mark.asyncio
    async def test_upload_blob_string(
        self, cloud_storage, mock_bucket, mock_blob
    ):
        mock_bucket.blob.return_value = mock_blob

        result = await cloud_storage.upload_blob(
            file_path="test/file.txt",
            content="test content",
            content_type="text/plain",
        )

        mock_bucket.blob.assert_called_once_with("test/file.txt")
        mock_blob.upload_from_string.assert_called_once_with(
            b"test content", content_type="text/plain"
        )

        assert isinstance(result, File)
        assert result.filename == "file.txt"
        assert result.path == "/test/file.txt"
        assert result.url == mock_blob.public_url
        assert result.size == mock_blob.size
        assert result.content_type == mock_blob.content_type

    @pytest.mark.asyncio
    async def test_upload_blob_bytes(
        self, cloud_storage, mock_bucket, mock_blob
    ):
        mock_bucket.blob.return_value = mock_blob

        content = b"test content bytes"
        result = await cloud_storage.upload_blob(
            file_path="test/file.txt",
            content=content,
            content_type="text/plain",
        )

        mock_bucket.blob.assert_called_once_with("test/file.txt")
        mock_blob.upload_from_string.assert_called_once_with(
            content, content_type="text/plain"
        )

        assert isinstance(result, File)

    @pytest.mark.asyncio
    async def test_get_blob(self, cloud_storage, mock_bucket, mock_blob):
        mock_bucket.get_blob.return_value = mock_blob

        result = await cloud_storage.get_blob("/test/file.txt")

        mock_bucket.get_blob.assert_called_once_with("test/file.txt")

        assert isinstance(result, File)
        assert result.filename == "file.txt"
        assert result.path == "/test/file.txt"
        assert result.url == mock_blob.public_url
        assert result.size == mock_blob.size
        assert result.content_type == mock_blob.content_type

    @pytest.mark.asyncio
    async def test_delete_blob(self, cloud_storage, mock_bucket, mock_blob):
        mock_bucket.blob.return_value = mock_blob

        result = await cloud_storage.delete_blob("/test/file.txt")

        mock_bucket.blob.assert_called_once_with("test/file.txt")
        mock_blob.delete.assert_called_once()

        assert isinstance(result, FileDelete)
        assert result.file == "/test/file.txt"

    @pytest.mark.asyncio
    async def test_copy_blob(self, cloud_storage, mock_bucket, mock_blob):
        source_blob = MagicMock(spec=Blob)
        new_blob = MagicMock(spec=Blob)
        new_blob.name = "test/new_file.txt"
        new_blob.public_url = (
            "https://storage.googleapis.com/test-bucket/test/new_file.txt"
        )
        new_blob.size = 1024
        new_blob.content_type = "text/plain"

        mock_bucket.copy_blob.return_value = new_blob

        result = await cloud_storage.copy_blob(
            source_blob, "test/new_file.txt"
        )

        mock_bucket.copy_blob.assert_called_once_with(
            source_blob, mock_bucket, "test/new_file.txt"
        )

        assert isinstance(result, File)
        assert result.filename == "new_file.txt"
        assert result.path == "/test/new_file.txt"
        assert result.url == new_blob.public_url
        assert result.size == new_blob.size
        assert result.content_type == new_blob.content_type

    @pytest.mark.asyncio
    async def test_rename_blob(self, cloud_storage, mock_bucket, mock_blob):
        source_blob = MagicMock(spec=Blob)
        new_blob = MagicMock(spec=Blob)
        new_blob.name = "test/new_name.txt"
        new_blob.public_url = (
            "https://storage.googleapis.com/test-bucket/test/new_name.txt"
        )
        new_blob.size = 1024
        new_blob.content_type = "text/plain"

        mock_bucket.get_blob.return_value = source_blob
        mock_bucket.rename_blob.return_value = new_blob

        result = await cloud_storage.rename_blob(
            "/test/file.txt", "new_name.txt"
        )

        mock_bucket.get_blob.assert_called_once_with("test/file.txt")
        mock_bucket.rename_blob.assert_called_once()

        assert isinstance(result, File)
        assert result.filename == "new_name.txt"
        assert result.path == "/test/new_name.txt"
        assert result.url == new_blob.public_url
        assert result.size == new_blob.size
        assert result.content_type == new_blob.content_type

    @pytest.mark.asyncio
    async def test_list_blobs(self, cloud_storage, mock_bucket):
        blob1 = MagicMock(spec=Blob)
        blob1.name = "test/file1.txt"
        blob1.public_url = (
            "https://storage.googleapis.com/test-bucket/test/file1.txt"
        )
        blob1.size = 1024
        blob1.content_type = "text/plain"

        blob2 = MagicMock(spec=Blob)
        blob2.name = "test/file2.txt"
        blob2.public_url = (
            "https://storage.googleapis.com/test-bucket/test/file2.txt"
        )
        blob2.size = 2048
        blob2.content_type = "text/plain"

        folder_blob = MagicMock(spec=Blob)
        folder_blob.name = "test/folder/"

        mock_bucket.list_blobs.return_value = [blob1, blob2, folder_blob]

        result = await cloud_storage.list_blobs("/test")

        mock_bucket.list_blobs.assert_called_once_with(prefix="test")

        assert isinstance(result, list)
        assert len(result) == 2  # folder_blob должен быть исключен
        assert all(isinstance(item, File) for item in result)
        assert result[0].filename == "file1.txt"
        assert result[1].filename == "file2.txt"

    @pytest.mark.asyncio
    async def test_list_blobs_with_search(self, cloud_storage, mock_bucket):
        blob1 = MagicMock(spec=Blob)
        blob1.name = "test/file1.txt"
        blob1.public_url = (
            "https://storage.googleapis.com/test-bucket/test/file1.txt"
        )
        blob1.size = 1024
        blob1.content_type = "text/plain"

        blob2 = MagicMock(spec=Blob)
        blob2.name = "test/another.txt"
        blob2.public_url = (
            "https://storage.googleapis.com/test-bucket/test/another.txt"
        )
        blob2.size = 2048
        blob2.content_type = "text/plain"

        mock_bucket.list_blobs.return_value = [blob1, blob2]

        result = await cloud_storage.list_blobs("/test", search_query="file")

        mock_bucket.list_blobs.assert_called_once_with(prefix="test")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].filename == "file1.txt"

    @pytest.mark.asyncio
    async def test_create_folder(
        self, cloud_storage, mock_storage_control_client
    ):
        create_time = datetime.datetime.now()
        update_time = datetime.datetime.now()

        response_mock = MagicMock()
        response_mock.name = (
            "projects/_/buckets/test-bucket/folders/test_folder"
        )
        response_mock.create_time = create_time
        response_mock.update_time = update_time

        mock_storage_control_client.return_value.create_folder.return_value = (
            response_mock
        )
        mock_storage_control_client.return_value.common_project_path.return_value = (
            "projects/_"
        )
        mock_storage_control_client.return_value.common_folder_path.return_value = (
            "folders/test_folder/"
        )

        mock_create_request = MagicMock(spec=CreateFolderRequest)

        result = await cloud_storage.create_folder(
            folder_name="test_folder", create_request=mock_create_request
        )

        mock_storage_control_client.return_value.create_folder.assert_called_once()

        assert isinstance(result, FolderData)
        assert result.folder_name == "test_folder"
        assert result.folder_path == "test_folder/"
        assert result.create_time == create_time.replace(microsecond=0)
        assert result.update_time == update_time.replace(microsecond=0)

    @pytest.mark.asyncio
    async def test_get_folder(
        self, cloud_storage, mock_storage_control_client
    ):
        create_time = datetime.datetime.now()
        update_time = datetime.datetime.now()

        folder_mock = MagicMock()
        folder_mock.name = "projects/_/buckets/test-bucket/folders/test_folder"
        folder_mock.create_time = create_time
        folder_mock.update_time = update_time

        mock_storage_control_client.return_value.get_folder.return_value = (
            folder_mock
        )
        mock_storage_control_client.return_value.folder_path.return_value = (
            "projects/_/buckets/test-bucket/folders/test_folder"
        )
        mock_storage_control_client.return_value.common_folder_path.return_value = (
            "folders/test_folder/"
        )

        result = await cloud_storage.get_folder("test_folder")

        mock_storage_control_client.return_value.get_folder.assert_called_once()

        assert isinstance(result, FolderData)
        assert result.folder_name == "test_folder"
        assert result.folder_path == "test_folder/"
        assert result.create_time == create_time.replace(microsecond=0)
        assert result.update_time == update_time.replace(microsecond=0)

    @pytest.mark.asyncio
    async def test_delete_folder(
        self, cloud_storage, mock_storage_control_client
    ):
        with patch.object(
            cloud_storage, "_delete_folder", new_callable=AsyncMock
        ) as mock_delete_folder:
            mock_delete_folder.return_value = True

            result = await cloud_storage.delete_folder("test_folder")

            mock_delete_folder.assert_called_once_with("test_folder")

            assert isinstance(result, FolderDelete)
            assert result.folder_name == "test_folder"

    @pytest.mark.asyncio
    async def test_delete_folder_recursive(self, cloud_storage):
        with patch.object(
            cloud_storage,
            "_delete_all_files_in_folder",
            new_callable=AsyncMock,
        ) as mock_delete_files, patch.object(
            cloud_storage, "_delete_subfolders", new_callable=AsyncMock
        ) as mock_delete_subfolders:
            mock_delete_files.return_value = True
            mock_delete_subfolders.return_value = True

            result = await cloud_storage.delete_folder(
                "test_folder", is_delete_all=True
            )

            mock_delete_files.assert_called_once_with("test_folder")
            mock_delete_subfolders.assert_called_once_with("test_folder")

            assert isinstance(result, FolderDelete)
            assert result.folder_name == "test_folder"

    @pytest.mark.asyncio
    async def test_rename_folder(
        self, cloud_storage, mock_storage_control_client
    ):
        mock_storage_control_client.return_value.rename_folder.return_value = (
            MagicMock()
        )
        mock_storage_control_client.return_value.folder_path.return_value = (
            "projects/_/buckets/test-bucket/folders/old_folder"
        )
        mock_storage_control_client.return_value.common_folder_path.return_value = (
            "folders/new_folder/"
        )

        mock_rename_request = MagicMock(spec=RenameFolderRequest)

        result = await cloud_storage.rename_folder(
            old_name="old_folder",
            new_name="new_folder",
            rename_request=mock_rename_request,
        )

        mock_storage_control_client.return_value.rename_folder.assert_called_once()

        assert isinstance(result, FolderRename)
        assert result.folder_name == "new_folder"
        assert result.old_name == "old_folder"
        assert result.folder_path == "new_folder/"

    @pytest.mark.asyncio
    async def test_list_folders(
        self, cloud_storage, mock_storage_control_client
    ):
        folder1 = MagicMock()
        folder1.name = "projects/_/buckets/test-bucket/folders/folder1"
        folder1.create_time = datetime.datetime.now()
        folder1.update_time = datetime.datetime.now()

        folder2 = MagicMock()
        folder2.name = "projects/_/buckets/test-bucket/folders/folder2"
        folder2.create_time = datetime.datetime.now()
        folder2.update_time = datetime.datetime.now()

        mock_storage_control_client.return_value.list_folders.return_value = [
            folder1,
            folder2,
        ]
        mock_storage_control_client.return_value.common_project_path.return_value = (
            "projects/_"
        )
        mock_storage_control_client.return_value.common_folder_path.side_effect = (
            lambda x: f"folders/{x}/"
        )

        result = await cloud_storage.list_folders(prefix="test")

        mock_storage_control_client.return_value.list_folders.assert_called_once()

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(folder, FolderData) for folder in result)
        assert result[0].folder_name == "folder1"
        assert result[1].folder_name == "folder2"

    def test_get_bucket_path(self, cloud_storage, mock_storage_control_client):
        mock_storage_control_client.return_value.common_project_path.return_value = (
            "projects/_"
        )

        result = cloud_storage._get_bucket_path()

        assert result == "projects/_/buckets/test-bucket"

    def test_get_blob_path(self, cloud_storage):
        result = cloud_storage._get_blob_path("test/file.txt")
        assert result == "/test/file.txt"

    def test_get_blob_name(self, cloud_storage):
        result = cloud_storage._get_blob_name("test/file.txt")
        assert result == "file.txt"

    def test_get_folder_name(self, cloud_storage):
        # Base case
        result = cloud_storage._get_folder_name(
            "projects/_/buckets/test-bucket/folders/test_folder"
        )
        assert result == "test_folder"

        # Case when 'folders' is the last element
        result = cloud_storage._get_folder_name(
            "projects/_/buckets/test-bucket/folders"
        )
        assert result == "folders"

        # Case when 'folders' is the second to last element
        result = cloud_storage._get_folder_name(
            "projects/_/buckets/test-bucket/folders/test_folder/subfolder"
        )
        assert result == "subfolder"

        # Case when 'folders' is not present
        result = cloud_storage._get_folder_name(
            "projects/_/buckets/test-bucket/test_folder"
        )
        assert result == "test_folder"

        # Case with empty string
        result = cloud_storage._get_folder_name("")
        assert result == ""

        # Case with consecutive slashes
        result = cloud_storage._get_folder_name(
            "projects/_/buckets/test-bucket//folders//test_folder"
        )
        assert result == "test_folder"

        # Case with a relative path
        result = cloud_storage._get_folder_name("test_folder")
        assert result == "test_folder"

    def test_get_folder_path(self, cloud_storage, mock_storage_control_client):
        mock_storage_control_client.return_value.folder_path.return_value = (
            "projects/_/buckets/test-bucket/folders/test_folder"
        )

        result = cloud_storage._get_folder_path("/test_folder")

        mock_storage_control_client.return_value.folder_path.assert_called_once_with(
            project="_", bucket="test-bucket", folder="test_folder"
        )
        assert result == "projects/_/buckets/test-bucket/folders/test_folder"

    def test_get_common_folder_path(
        self, cloud_storage, mock_storage_control_client
    ):
        mock_storage_control_client.return_value.common_folder_path.return_value = (
            "folders/test_folder"
        )

        result = cloud_storage._get_common_folder_path("test_folder")

        assert result == "test_folder/"

    def test_normalize_file_path(self, cloud_storage):
        assert (
            cloud_storage._normalize_file_path("/test/file.txt")
            == "test/file.txt"
        )
        assert (
            cloud_storage._normalize_file_path("test/file.txt")
            == "test/file.txt"
        )
        assert cloud_storage._normalize_file_path(None) == ""

    @pytest.mark.asyncio
    async def test_delete_subfolders(self, cloud_storage):
        subfolder1 = FolderData(
            folder_name="subfolder1", folder_path="test_folder/subfolder1/"
        )
        subfolder2 = FolderData(
            folder_name="subfolder2", folder_path="test_folder/subfolder2/"
        )

        with patch.object(
            cloud_storage, "list_folders", new_callable=AsyncMock
        ) as mock_list_folders, patch.object(
            cloud_storage, "_delete_folder", new_callable=AsyncMock
        ) as mock_delete_folder:
            mock_list_folders.return_value = [subfolder1, subfolder2]
            mock_delete_folder.return_value = True

            result = await cloud_storage._delete_subfolders("test_folder")

            mock_list_folders.assert_called_once_with(prefix="test_folder")
            assert mock_delete_folder.call_count == 2
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_all_files_in_folder(self, cloud_storage):
        file1 = File(
            filename="file1.txt", path="/test_folder/file1.txt", url="url1"
        )
        file2 = File(
            filename="file2.txt", path="/test_folder/file2.txt", url="url2"
        )

        with patch.object(
            cloud_storage, "list_blobs", new_callable=AsyncMock
        ) as mock_list_blobs, patch.object(
            cloud_storage, "delete_blob", new_callable=AsyncMock
        ) as mock_delete_blob:
            mock_list_blobs.return_value = [file1, file2]
            mock_delete_blob.return_value = MagicMock()

            result = await cloud_storage._delete_all_files_in_folder(
                "test_folder"
            )

            mock_list_blobs.assert_called_once_with(prefix="test_folder")
            assert mock_delete_blob.call_count == 2
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_folder_internal(
        self, cloud_storage, mock_storage_control_client
    ):
        mock_delete_request = MagicMock(spec=DeleteFolderRequest)

        result = await cloud_storage._delete_folder(
            folder_path="test_folder", delete_request=mock_delete_request
        )

        mock_storage_control_client.return_value.delete_folder.assert_called_once()
        assert result is True

    def test_search_blobs_case_insensitive(self, cloud_storage):
        blob1 = MagicMock(spec=Blob)
        blob1.name = "test/file1.txt"
        blob1.public_url = "url1"
        blob1.content_type = "text/plain"
        blob1.size = 1024

        blob2 = MagicMock(spec=Blob)
        blob2.name = "test/FILE2.txt"
        blob2.public_url = "url2"
        blob2.content_type = "text/plain"
        blob2.size = 2048

        blob3 = MagicMock(spec=Blob)
        blob3.name = "test/folder/"
        blob3.content_type = "Folder"

        blobs = [blob1, blob2, blob3]

        result = cloud_storage._search_blobs(
            blobs, "file", case_sensitive=False
        )

        assert len(result) == 2
        assert result[0].filename == "file1.txt"
        assert result[1].filename == "FILE2.txt"

    def test_search_blobs_case_sensitive(self, cloud_storage):
        blob1 = MagicMock(spec=Blob)
        blob1.name = "test/file1.txt"
        blob1.public_url = "url1"
        blob1.content_type = "text/plain"
        blob1.size = 1024

        blob2 = MagicMock(spec=Blob)
        blob2.name = "test/FILE2.txt"
        blob2.public_url = "url2"
        blob2.content_type = "text/plain"
        blob2.size = 2048

        blobs = [blob1, blob2]

        result = cloud_storage._search_blobs(
            blobs, "file", case_sensitive=True
        )

        assert len(result) == 1
        assert result[0].filename == "file1.txt"
