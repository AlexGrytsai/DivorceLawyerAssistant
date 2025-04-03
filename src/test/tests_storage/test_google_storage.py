import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.core.storage.implementations.google_storage import GoogleCloudStorage
from src.core.storage.shemas import (
    FolderDataSchema,
    FolderDeleteSchema,
    FolderRenameSchema,
)


class TestGoogleCloudStorage(unittest.TestCase):
    def setUp(self):
        self.bucket_name = "test-bucket"
        self.project_id = "test-project"

        self.storage = GoogleCloudStorage(
            bucket_name=self.bucket_name, project_id=self.project_id
        )

        self.mock_client = MagicMock()
        self.mock_storage_control = MagicMock()
        self.mock_bucket = MagicMock()

        self.storage._client = self.mock_client
        self.storage._storage_control = self.mock_storage_control
        self.storage._bucket = self.mock_bucket

    def test_init(self):
        storage = GoogleCloudStorage(
            bucket_name="test", project_id="test-project"
        )
        self.assertEqual(storage.bucket_name, "test")
        self.assertEqual(storage.project_id, "test-project")
        self.assertIsNone(storage._client)
        self.assertIsNone(storage._storage_control)
        self.assertIsNone(storage._bucket)

    @patch("src.core.storage.implementations.google_storage.storage.Client")
    def test_client_property(self, mock_client_class):
        storage = GoogleCloudStorage(
            bucket_name="test", project_id="test-project"
        )
        storage._client = None

        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = storage.client

        mock_client_class.assert_called_once_with(project="test-project")
        self.assertEqual(client, mock_client_instance)
        self.assertEqual(storage._client, mock_client_instance)

        # Second call should use cached client
        storage.client
        mock_client_class.assert_called_once()

    @patch(
        "src.core.storage.implementations.google_storage.StorageControlClient"
    )
    def test_storage_control_property(self, mock_storage_control_class):
        storage = GoogleCloudStorage(
            bucket_name="test", project_id="test-project"
        )
        storage._storage_control = None

        mock_storage_control_instance = MagicMock()
        mock_storage_control_class.return_value = mock_storage_control_instance

        storage_control = storage.storage_control

        mock_storage_control_class.assert_called_once()
        self.assertEqual(storage_control, mock_storage_control_instance)
        self.assertEqual(
            storage._storage_control, mock_storage_control_instance
        )

        # Second call should use cached storage_control
        storage.storage_control
        mock_storage_control_class.assert_called_once()

    def test_bucket_property(self):
        mock_client = MagicMock()
        mock_bucket_instance = MagicMock()
        mock_client.get_bucket.return_value = mock_bucket_instance

        storage = GoogleCloudStorage(
            bucket_name="test-bucket", project_id="test-project"
        )
        storage._client = mock_client
        storage._bucket = None

        bucket = storage.bucket

        mock_client.get_bucket.assert_called_once_with(
            bucket_or_name="test-bucket"
        )
        self.assertEqual(bucket, mock_bucket_instance)
        self.assertEqual(storage._bucket, mock_bucket_instance)

        # Second call should use cached bucket
        storage.bucket
        mock_client.get_bucket.assert_called_once()

    def test_upload_blob(self):
        mock_blob = MagicMock()
        mock_blob.public_url = "https://example.com/test-file"
        self.mock_bucket.blob.return_value = mock_blob

        result = self.storage.upload_blob(
            file_path="test/file.txt",
            content="test content",
            content_type="text/plain",
        )

        self.mock_bucket.blob.assert_called_once_with("test/file.txt")
        mock_blob.upload_from_string.assert_called_once_with(
            b"test content", content_type="text/plain"
        )
        self.assertEqual(result, "https://example.com/test-file")

        # Test with bytes content
        self.mock_bucket.blob.reset_mock()
        mock_blob.upload_from_string.reset_mock()

        bytes_content = b"binary content"
        self.storage.upload_blob(
            file_path="test/binary.bin",
            content=bytes_content,
            content_type="application/octet-stream",
        )

        mock_blob.upload_from_string.assert_called_once_with(
            bytes_content, content_type="application/octet-stream"
        )

    def test_delete_blob(self):
        mock_blob = MagicMock()
        self.mock_bucket.blob.return_value = mock_blob

        self.storage.delete_blob(file_path="test/file.txt")

        self.mock_bucket.blob.assert_called_once_with("test/file.txt")
        mock_blob.delete.assert_called_once()

    def test_copy_blob(self):
        mock_source_blob = MagicMock()
        mock_new_blob = MagicMock()
        self.mock_bucket.copy_blob.return_value = mock_new_blob

        result = self.storage.copy_blob(
            source_blob=mock_source_blob, new_name="test/copy.txt"
        )

        self.mock_bucket.copy_blob.assert_called_once_with(
            mock_source_blob, self.mock_bucket, "test/copy.txt"
        )
        self.assertEqual(result, mock_new_blob)

    def test_list_blobs(self):
        mock_blobs = [MagicMock(), MagicMock()]
        self.mock_bucket.list_blobs.return_value = mock_blobs

        result = self.storage.list_blobs(prefix="test/", delimiter="/")

        self.mock_bucket.list_blobs.assert_called_once_with(
            prefix="test/", delimiter="/"
        )
        self.assertEqual(result, mock_blobs)

        # Test default parameters
        self.mock_bucket.list_blobs.reset_mock()
        self.storage.list_blobs()

        self.mock_bucket.list_blobs.assert_called_once_with(
            prefix="", delimiter=None
        )

    def test_create_folder(self):
        mock_response = MagicMock()
        mock_response.name = (
            "projects/test-project/buckets/test-bucket/folders/test-folder"
        )
        mock_response.create_time.replace.return_value = datetime(
            2023, 1, 1, tzinfo=timezone.utc
        )
        mock_response.update_time.replace.return_value = datetime(
            2023, 1, 1, tzinfo=timezone.utc
        )

        self.mock_storage_control.create_folder.return_value = mock_response
        self.mock_storage_control.common_project_path.return_value = (
            "projects/test-project"
        )
        self.mock_storage_control.common_folder_path.return_value = (
            "projects/test-project/buckets/test-bucket/folders/test-folder"
        )

        mock_create_request = MagicMock()

        result = self.storage.create_folder(
            folder_name="test-folder", create_request=mock_create_request
        )

        self.mock_storage_control.create_folder.assert_called_once()
        self.assertIsInstance(result, FolderDataSchema)
        self.assertEqual(result.folder_name, "test-folder")
        self.assertEqual(
            result.create_time, datetime(2023, 1, 1, tzinfo=timezone.utc)
        )
        self.assertEqual(
            result.update_time, datetime(2023, 1, 1, tzinfo=timezone.utc)
        )

    def test_delete_folder(self):
        self.mock_storage_control.folder_path.return_value = (
            "projects/test-project/buckets/test-bucket/folders/test-folder"
        )
        mock_delete_request = MagicMock()

        result = self.storage.delete_folder(
            folder_name="test-folder", delete_request=mock_delete_request
        )

        self.mock_storage_control.delete_folder.assert_called_once()
        self.assertIsInstance(result, FolderDeleteSchema)
        self.assertEqual(result.folder_name, "test-folder")

    def test_rename_folder(self):
        self.mock_storage_control.folder_path.return_value = (
            "projects/test-project/buckets/test-bucket/folders/old-folder"
        )
        self.mock_storage_control.common_folder_path.return_value = (
            "projects/test-project/buckets/test-bucket/folders/new-folder"
        )
        mock_rename_request = MagicMock()

        result = self.storage.rename_folder(
            old_name="old-folder",
            new_name="new-folder",
            rename_request=mock_rename_request,
        )

        self.mock_storage_control.rename_folder.assert_called_once()
        self.assertIsInstance(result, FolderRenameSchema)
        self.assertEqual(result.folder_name, "new-folder")
        self.assertEqual(result.old_name, "old-folder")

    def test_list_folders(self):
        folder1 = MagicMock()
        folder1.name = (
            "projects/test-project/buckets/test-bucket/folders/folder1"
        )
        folder1.create_time.replace.return_value = datetime(
            2023, 1, 1, tzinfo=timezone.utc
        )
        folder1.update_time.replace.return_value = datetime(
            2023, 1, 1, tzinfo=timezone.utc
        )

        folder2 = MagicMock()
        folder2.name = (
            "projects/test-project/buckets/test-bucket/folders/folder2"
        )
        folder2.create_time.replace.return_value = datetime(
            2023, 1, 2, tzinfo=timezone.utc
        )
        folder2.update_time.replace.return_value = datetime(
            2023, 1, 2, tzinfo=timezone.utc
        )

        self.mock_storage_control.list_folders.return_value = [
            folder1,
            folder2,
        ]
        self.mock_storage_control.common_project_path.return_value = (
            "projects/test-project"
        )
        self.mock_storage_control.common_folder_path.side_effect = (
            lambda name: name
        )

        result = self.storage.list_folders(prefix="test")

        self.mock_storage_control.list_folders.assert_called_once()
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], FolderDataSchema)
        self.assertIsInstance(result[1], FolderDataSchema)
        self.assertEqual(result[0].folder_name, "foldersfolder1")
        self.assertEqual(result[1].folder_name, "foldersfolder2")

    def test_get_bucket_path(self):
        self.mock_storage_control.common_project_path.return_value = (
            "projects/test-project"
        )

        result = self.storage._get_bucket_path()

        self.mock_storage_control.common_project_path.assert_called_once_with(
            "_"
        )
        self.assertEqual(result, "projects/test-project/buckets/test-bucket")

    def test_get_folder_path(self):
        self.mock_storage_control.folder_path.return_value = (
            "projects/test-project/buckets/test-bucket/folders/test-folder"
        )

        result = self.storage._get_folder_path("test-folder")

        self.mock_storage_control.folder_path.assert_called_once_with(
            project="_", bucket="test-bucket", folder="test-folder"
        )
        self.assertEqual(
            result,
            "projects/test-project/buckets/test-bucket/folders/test-folder",
        )

    def test_get_common_folder_path(self):
        self.mock_storage_control.common_folder_path.return_value = (
            "projects/test-project/buckets/test-bucket/folders/test-folder"
        )

        result = self.storage._get_common_folder_path("test-folder")

        self.mock_storage_control.common_folder_path.assert_called_once_with(
            "test-folder"
        )
        self.assertEqual(result, "test-folder")

    def test_edge_cases(self):
        # Test empty content
        mock_blob = MagicMock()
        mock_blob.public_url = "https://example.com/empty-file"
        self.mock_bucket.blob.return_value = mock_blob

        result = self.storage.upload_blob(
            file_path="test/empty.txt", content="", content_type="text/plain"
        )

        mock_blob.upload_from_string.assert_called_once_with(
            b"", content_type="text/plain"
        )
        self.assertEqual(result, "https://example.com/empty-file")

        # Test list_blobs with no results
        self.mock_bucket.list_blobs.reset_mock()
        self.mock_bucket.list_blobs.return_value = []

        result = self.storage.list_blobs(prefix="nonexistent/")
        self.assertEqual(result, [])

        # Test list_folders with no results
        self.mock_storage_control.list_folders.reset_mock()
        self.mock_storage_control.list_folders.return_value = []

        result = self.storage.list_folders(prefix="nonexistent")
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
