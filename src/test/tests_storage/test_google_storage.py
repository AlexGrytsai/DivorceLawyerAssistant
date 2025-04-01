import unittest
from unittest.mock import MagicMock, patch

from google.cloud.storage import Blob, Bucket  # type: ignore

from src.core.storage.implementations.google_storage import GoogleCloudStorage


class TestGoogleCloudStorage(unittest.TestCase):
    def setUp(self):
        self.bucket_name = "test-bucket"
        self.project_id = "test-project"
        self.storage = GoogleCloudStorage(self.bucket_name, self.project_id)

    @patch("google.cloud.storage.Client")
    def test_initialization(self, mock_client):
        self.assertEqual(self.storage.bucket_name, self.bucket_name)
        self.assertEqual(self.storage.project_id, self.project_id)
        self.assertIsNone(self.storage._client)
        self.assertIsNone(self.storage._bucket)

    @patch("google.cloud.storage.Client")
    def test_get_client(self, mock_client):
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance

        client = self.storage.get_client
        self.assertEqual(client, mock_client_instance)
        mock_client.assert_called_once_with(project=self.project_id)

    @patch("google.cloud.storage.Client")
    def test_get_bucket(self, mock_client):
        mock_client_instance = MagicMock()
        mock_bucket = MagicMock(spec=Bucket)
        mock_client.return_value = mock_client_instance
        mock_client_instance.get_bucket.return_value = mock_bucket

        bucket = self.storage.get_bucket
        self.assertEqual(bucket, mock_bucket)
        mock_client_instance.get_bucket.assert_called_once_with(
            bucket_or_name=self.bucket_name
        )

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
            self.storage.get_client
