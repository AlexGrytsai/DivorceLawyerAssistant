import unittest
from unittest.mock import MagicMock, patch

from google.cloud.storage import Blob, Bucket  # type: ignore

from src.core.storage.implementations.google_storage import GoogleCloudStorage
from src.core.storage.shemas import FolderBaseSchema


class TestGoogleCloudStorage(unittest.TestCase):
    def setUp(self):
        self.bucket_name = "test-bucket"
        self.project_id = "test-project"
        self.storage = GoogleCloudStorage(self.project_id, self.bucket_name)

    @patch("google.cloud.storage.Client")
    def test_initialization(self, mock_client):
        self.assertEqual(self.storage._bucket_name, self.bucket_name)
        self.assertIsNotNone(self.storage.client)
        self.assertIsNotNone(self.storage._path_handler)

    @property
    @handle_cloud_storage_exceptions
    def test_get_bucket(self, mock_client):
        mock_bucket = MagicMock(spec=Bucket)
        self.storage.client.bucket.return_value = mock_bucket
        bucket = self.storage.get_bucket
        self.assertEqual(bucket, mock_bucket)
        self.storage.client.bucket.assert_called_once_with(self.bucket_name)

    def test_create_managed_folder(self):
        folder_path = "test_folder/"
        self.storage.client._connection.api_request.return_value = {}

        self.storage.create_folder(folder_path)

        self.storage.client._connection.api_request.assert_called_once_with(
            method="POST",
            path=f"/b/{self.bucket_name}/managedFolders",
            data={"name": folder_path, "bucket": self.bucket_name},
        )

    def test_delete_managed_folder(self):
        folder_path = "test_folder/"
        self.storage.client._connection.api_request.return_value = {}

        self.storage.delete_folder(folder_path)

        self.storage.client._connection.api_request.assert_called_once_with(
            method="DELETE",
            path=f"/b/{self.bucket_name}/managedFolders/{folder_path}",
            query_params={},
        )

    def test_delete_managed_folder_allow_non_empty(self):
        folder_path = "test_folder/"
        self.storage.client._connection.api_request.return_value = {}

        self.storage.delete_folder(folder_path, allow_non_empty=True)

        self.storage.client._connection.api_request.assert_called_once_with(
            method="DELETE",
            path=f"/b/{self.bucket_name}/managedFolders/{folder_path}",
            query_params={"allowNonEmpty": True},
        )

    def test_rename_managed_folder(self):
        old_path = "old_folder/"
        new_path = "new_folder/"
        self.storage.client._connection.api_request.return_value = {}

        self.storage.rename_folder(old_path, new_path)

        self.storage.client._connection.api_request.assert_called_once_with(
            method="POST",
            path=f"/b/{self.bucket_name}/managedFolders:rename",
            data={"sourceFolder": old_path, "destinationFolder": new_path},
        )

    def test_list_managed_folders(self):
        mock_response = {
            "managedFolders": [
                {
                    "name": "folder1/",
                    "timeCreated": "2024-01-01T00:00:00Z",
                    "updated": "2024-01-01T00:00:00Z",
                }
            ]
        }
        self.storage.client._connection.api_request.return_value = (
            mock_response
        )
        self.storage.list_blobs.return_value = []

        folders = self.storage.list_folders()

        self.assertEqual(len(folders), 1)
        self.assertIsInstance(folders[0], FolderBaseSchema)
        self.assertEqual(folders[0].path, "folder1/")
        self.assertTrue(folders[0].is_managed)
        self.assertTrue(folders[0].is_empty)

    def test_get_managed_folder(self):
        mock_response = {
            "name": "test_folder/",
            "timeCreated": "2024-01-01T00:00:00Z",
            "updated": "2024-01-01T00:00:00Z",
        }
        self.storage.client._connection.api_request.return_value = (
            mock_response
        )
        self.storage.list_blobs.return_value = []

        folder = self.storage.get_folder("test_folder/")

        self.assertIsInstance(folder, FolderBaseSchema)
        self.assertEqual(folder.path, "test_folder/")
        self.assertTrue(folder.is_managed)
        self.assertTrue(folder.is_empty)

    def test_get_managed_folder_iam_policy(self):
        mock_policy = {"bindings": []}
        self.storage.client._connection.api_request.return_value = mock_policy

        policy = self.storage.get_managed_folder_iam_policy("test_folder/")

        self.assertEqual(policy, mock_policy)
        self.storage.client._connection.api_request.assert_called_once_with(
            method="GET",
            path=f"/b/{self.bucket_name}/managedFolders/test_folder/iam",
        )

    def test_set_managed_folder_iam_policy(self):
        mock_policy = {"bindings": []}
        self.storage.client._connection.api_request.return_value = mock_policy

        result = self.storage.set_managed_folder_iam_policy(
            "test_folder/", mock_policy
        )

        self.assertEqual(result, mock_policy)
        self.storage.client._connection.api_request.assert_called_once_with(
            method="PUT",
            path=f"/b/{self.bucket_name}/managedFolders/test_folder/iam",
            data=mock_policy,
        )

    @patch("google.cloud.storage.Client")
    def test_get_client(self, mock_client):
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance

        client = self.storage.client
        self.assertEqual(client, mock_client_instance)
        mock_client.assert_called_once_with(project=self.project_id)

    @patch("google.cloud.storage.Client")
    def test_upload_blob_string_content(self, mock_client):
        mock_client_instance = MagicMock()
        mock_bucket = MagicMock(spec=Bucket)
        mock_blob = MagicMock(spec=Blob)
        mock_client.return_value = mock_client_instance
        mock_client_instance.get_bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.public_url = "https://test-url.com"

        content = "test content"
        file_path = "test/file.txt"
        content_type = "text/plain"

        result = self.storage.upload_blob(file_path, content, content_type)

        self.assertEqual(result, "https://test-url.com")
        mock_bucket.blob.assert_called_once_with(file_path)
        mock_blob.upload_from_string.assert_called_once_with(
            content.encode("utf-8"), content_type=content_type
        )

    @patch("google.cloud.storage.Client")
    def test_upload_blob_bytes_content(self, mock_client):
        mock_client_instance = MagicMock()
        mock_bucket = MagicMock(spec=Bucket)
        mock_blob = MagicMock(spec=Blob)
        mock_client.return_value = mock_client_instance
        mock_client_instance.get_bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.public_url = "https://test-url.com"

        content = b"test content"
        file_path = "test/file.txt"
        content_type = "text/plain"

        result = self.storage.upload_blob(file_path, content, content_type)

        self.assertEqual(result, "https://test-url.com")
        mock_bucket.blob.assert_called_once_with(file_path)
        mock_blob.upload_from_string.assert_called_once_with(
            content, content_type=content_type
        )

    @patch("google.cloud.storage.Client")
    def test_delete_blob(self, mock_client):
        mock_client_instance = MagicMock()
        mock_bucket = MagicMock(spec=Bucket)
        mock_blob = MagicMock(spec=Blob)
        mock_client.return_value = mock_client_instance
        mock_client_instance.get_bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        file_path = "test/file.txt"
        self.storage.delete_blob(file_path)

        mock_bucket.blob.assert_called_once_with(file_path)
        mock_blob.delete.assert_called_once()

    @patch("google.cloud.storage.Client")
    def test_copy_blob(self, mock_client):
        mock_client_instance = MagicMock()
        mock_bucket = MagicMock(spec=Bucket)
        mock_source_blob = MagicMock(spec=Blob)
        mock_new_blob = MagicMock(spec=Blob)
        mock_client.return_value = mock_client_instance
        mock_client_instance.get_bucket.return_value = mock_bucket
        mock_bucket.copy_blob.return_value = mock_new_blob

        new_name = "new_file.txt"
        result = self.storage.copy_blob(mock_source_blob, new_name)

        self.assertEqual(result, mock_new_blob)
        mock_bucket.copy_blob.assert_called_once_with(
            mock_source_blob, mock_bucket, new_name
        )

    @patch("google.cloud.storage.Client")
    def test_list_blobs(self, mock_client):
        mock_client_instance = MagicMock()
        mock_bucket = MagicMock(spec=Bucket)
        mock_blobs = [MagicMock(spec=Blob) for _ in range(3)]
        mock_client.return_value = mock_client_instance
        mock_client_instance.get_bucket.return_value = mock_bucket
        mock_bucket.list_blobs.return_value = mock_blobs

        prefix = "test/"
        result = self.storage.list_blobs(prefix)

        self.assertEqual(result, mock_blobs)
        mock_bucket.list_blobs.assert_called_once_with(prefix=prefix)

    @patch("google.cloud.storage.Client")
    def test_list_blobs_empty_prefix(self, mock_client):
        mock_client_instance = MagicMock()
        mock_bucket = MagicMock(spec=Bucket)
        mock_blobs = [MagicMock(spec=Blob) for _ in range(3)]
        mock_client.return_value = mock_client_instance
        mock_client_instance.get_bucket.return_value = mock_bucket
        mock_bucket.list_blobs.return_value = mock_blobs

        result = self.storage.list_blobs()

        self.assertEqual(result, mock_blobs)
        mock_bucket.list_blobs.assert_called_once_with(prefix="")

    @patch("google.cloud.storage.Client")
    def test_handle_cloud_storage_exceptions(self, mock_client):
        mock_client.side_effect = Exception("Test error")

        with self.assertRaises(Exception):
            self.storage.client
