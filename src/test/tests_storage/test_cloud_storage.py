import unittest
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from fastapi import UploadFile, Request

from src.core.exceptions.storage import ErrorSavingFile
from src.core.storage.cloud_storage import CloudStorage
from src.core.storage.shemas import (
    FileDataSchema,
    FileDeleteSchema,
    FolderBaseSchema,
    FolderDeleteSchema,
    FileItem,
    FolderItem,
    FolderContents,
)


class TestCloudStorage(unittest.TestCase):
    def setUp(self):
        self.project_id = "test-project"
        self.bucket_name = "test-bucket"
        self.mock_cloud_storage = Mock()
        self.mock_path_handler = Mock()
        self.mock_request = Mock(spec=Request)
        self.mock_request.client.host = "127.0.0.1"

        self.storage = CloudStorage(
            project_id=self.project_id,
            bucket_name=self.bucket_name,
            path_handler=self.mock_path_handler,
            cloud_storage=self.mock_cloud_storage,
        )

    async def test_upload_success(self):
        # Arrange
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(return_value=b"test content")

        self.mock_cloud_storage.upload_blob.return_value = (
            "https://storage.googleapis.com/test-bucket/test.txt"
        )

        # Act
        result = await self.storage.upload(mock_file, self.mock_request)

        # Assert
        self.assertIsInstance(result, FileDataSchema)
        self.assertEqual(result.filename, "test.txt")
        self.assertEqual(result.content_type, "text/plain")
        self.assertEqual(result.size, 12)

    async def test_upload_empty_filename(self):
        # Arrange
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = ""

        # Act & Assert
        with self.assertRaises(ValueError):
            await self.storage.upload(mock_file, self.mock_request)

    async def test_multi_upload_success(self):
        # Arrange
        mock_files = [
            Mock(
                spec=UploadFile,
                filename=f"test{i}.txt",
                content_type="text/plain",
            )
            for i in range(3)
        ]
        for file in mock_files:
            file.read = AsyncMock(return_value=b"test content")

        self.mock_cloud_storage.upload_blob.return_value = (
            "https://storage.googleapis.com/test-bucket/test.txt"
        )

        # Act
        results = await self.storage.multi_upload(
            mock_files, self.mock_request
        )

        # Assert
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, FileDataSchema)

    async def test_delete_success(self):
        # Arrange
        file_path = "test.txt"

        # Act
        result = await self.storage.delete(file_path, self.mock_request)

        # Assert
        self.assertIsInstance(result, FileDeleteSchema)
        self.assertEqual(result.file, file_path)
        self.assertEqual(result.deleted_by, "127.0.0.1")
        self.mock_cloud_storage.delete_blob.assert_called_once_with(file_path)

    async def test_create_folder_success(self):
        # Arrange
        folder_path = "test_folder"
        self.mock_path_handler.normalize_path.return_value = folder_path
        self.mock_path_handler.get_basename.return_value = "test_folder"
        self.mock_path_handler.get_parent_folder.return_value = ""

        # Act
        result = await self.storage.create_folder(
            folder_path, self.mock_request
        )

        # Assert
        self.assertIsInstance(result, FolderBaseSchema)
        self.assertEqual(result.path, folder_path)
        self.assertTrue(result.is_empty)
        self.assertTrue(result.is_managed)
        self.mock_cloud_storage.create_managed_folder.assert_called_once_with(
            folder_path
        )

    async def test_rename_folder_success(self):
        # Arrange
        old_path = "old_folder"
        new_path = "new_folder"
        self.mock_path_handler.normalize_path.side_effect = [
            old_path,
            new_path,
        ]
        self.mock_path_handler.get_basename.return_value = "new_folder"
        self.mock_path_handler.get_parent_folder.return_value = ""

        mock_folder = FolderBaseSchema(
            path=new_path,
            name="new_folder",
            parent_folder="",
            is_empty=True,
            is_managed=True,
        )
        self.mock_cloud_storage.rename_managed_folder.return_value = (
            mock_folder
        )

        # Act
        result = await self.storage.rename_folder(
            old_path, new_path, self.mock_request
        )

        # Assert
        self.assertIsInstance(result, FolderBaseSchema)
        self.assertEqual(result.path, new_path)
        self.assertTrue(result.is_empty)
        self.assertTrue(result.is_managed)
        self.mock_cloud_storage.rename_managed_folder.assert_called_once_with(
            old_path, new_path
        )

    async def test_delete_folder_success(self):
        # Arrange
        folder_path = "test_folder"
        self.mock_path_handler.normalize_path.return_value = folder_path

        mock_blobs = [
            Mock(name=f"{folder_path}/file1.txt"),
            Mock(name=f"{folder_path}/file2.txt"),
        ]
        self.mock_cloud_storage.list_blobs.return_value = mock_blobs

        # Act
        result = await self.storage.delete_folder(
            folder_path, self.mock_request
        )

        # Assert
        self.assertIsInstance(result, FolderDeleteSchema)
        self.assertEqual(result.folder, folder_path)
        self.assertEqual(result.deleted_by, "127.0.0.1")
        self.assertEqual(result.deleted_files_count, 2)
        self.assertEqual(self.mock_cloud_storage.delete_blob.call_count, 2)
        self.mock_cloud_storage.delete_managed_folder.assert_called_once_with(
            folder_path, allow_non_empty=True
        )

    async def test_rename_file_success(self):
        # Arrange
        old_path = "old.txt"
        new_path = "new.txt"
        mock_old_blob = Mock()
        mock_old_blob.exists.return_value = True
        mock_old_blob.content_type = "text/plain"
        mock_old_blob.size = 100

        self.mock_cloud_storage.get_bucket.blob.return_value = mock_old_blob
        self.mock_path_handler.get_basename.return_value = "new.txt"

        # Act
        result = await self.storage.rename_file(
            old_path, new_path, self.mock_request
        )

        # Assert
        self.assertIsInstance(result, FileDataSchema)
        self.mock_cloud_storage.copy_blob.assert_called_once()
        self.mock_cloud_storage.delete_blob.assert_called_once_with(old_path)

    async def test_rename_file_not_exists(self):
        # Arrange
        old_path = "nonexistent.txt"
        new_path = "new.txt"
        mock_old_blob = Mock()
        mock_old_blob.exists.return_value = False

        self.mock_cloud_storage.get_bucket.blob.return_value = mock_old_blob

        # Act & Assert
        with self.assertRaises(ErrorSavingFile):
            await self.storage.rename_file(
                old_path, new_path, self.mock_request
            )

    async def test_get_file_success(self):
        # Arrange
        file_path = "test.txt"
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.content_type = "text/plain"
        mock_blob.size = 100
        mock_blob.time_created = datetime.now()

        self.mock_cloud_storage.get_bucket.blob.return_value = mock_blob
        self.mock_path_handler.get_basename.return_value = "test.txt"

        # Act
        result = await self.storage.get_file(file_path)

        # Assert
        self.assertIsInstance(result, FileDataSchema)
        self.assertEqual(result.filename, "test.txt")

    async def test_get_file_not_exists(self):
        # Arrange
        file_path = "nonexistent.txt"
        mock_blob = Mock()
        mock_blob.exists.return_value = False

        self.mock_cloud_storage.get_bucket.blob.return_value = mock_blob

        # Act & Assert
        with self.assertRaises(ErrorSavingFile):
            await self.storage.get_file(file_path)

    async def test_list_files_success(self):
        # Arrange
        mock_blobs = [
            Mock(
                name="file1.txt",
                content_type="text/plain",
                size=100,
                time_created=datetime.now(),
            ),
            Mock(
                name="file2.txt",
                content_type="text/plain",
                size=200,
                time_created=datetime.now(),
            ),
        ]
        self.mock_cloud_storage.list_blobs.return_value = mock_blobs
        self.mock_path_handler.get_basename.side_effect = [
            "file1.txt",
            "file2.txt",
        ]

        # Act
        results = await self.storage.list_files()

        # Assert
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIsInstance(result, FileDataSchema)

    async def test_list_folders_success(self):
        # Arrange
        mock_folders = [
            FolderBaseSchema(
                path="folder1/",
                name="folder1",
                parent_folder="",
                is_empty=True,
                is_managed=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            FolderBaseSchema(
                path="folder2/",
                name="folder2",
                parent_folder="",
                is_empty=False,
                is_managed=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]
        self.mock_cloud_storage.list_managed_folders.return_value = (
            mock_folders
        )

        # Act
        results = await self.storage.list_folders()

        # Assert
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIsInstance(result, FolderBaseSchema)
            self.assertTrue(result.is_managed)

    async def test_search_files_by_name_success(self):
        # Arrange
        mock_blobs = [
            Mock(
                name="test1.txt",
                content_type="text/plain",
                size=100,
                time_created=datetime.now(),
            ),
            Mock(
                name="test2.txt",
                content_type="text/plain",
                size=200,
                time_created=datetime.now(),
            ),
        ]
        self.mock_cloud_storage.list_blobs.return_value = mock_blobs
        self.mock_path_handler.get_basename.side_effect = [
            "test1.txt",
            "test2.txt",
        ]

        # Act
        results = await self.storage.search_files_by_name("test")

        # Assert
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIsInstance(result, FileDataSchema)
            self.assertIn("test", result.filename)

    async def test_search_files_by_name_case_sensitive(self):
        # Arrange
        mock_blobs = [
            Mock(
                name="Test1.txt",
                content_type="text/plain",
                size=100,
                time_created=datetime.now(),
            ),
            Mock(
                name="test2.txt",
                content_type="text/plain",
                size=200,
                time_created=datetime.now(),
            ),
        ]
        self.mock_cloud_storage.list_blobs.return_value = mock_blobs
        self.mock_path_handler.get_basename.side_effect = [
            "Test1.txt",
            "test2.txt",
        ]

        # Act
        results = await self.storage.search_files_by_name(
            "Test", case_sensitive=True
        )

        # Assert
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].filename, "Test1.txt")

    async def test_get_folder_contents_success(self):
        # Arrange
        folder_path = "test_folder"
        mock_blobs = [
            Mock(
                name="test_folder/file1.txt", size=100, updated=datetime.now()
            ),
            Mock(
                name="test_folder/subfolder/file2.txt",
                size=200,
                updated=datetime.now(),
            ),
        ]
        self.mock_cloud_storage.list_blobs.return_value = mock_blobs

        # Act
        result = await self.storage.get_folder_contents(folder_path)

        # Assert
        self.assertIsInstance(result, FolderContents)
        self.assertEqual(result.current_path, folder_path)
        self.assertEqual(len(result.items), 2)
        self.assertTrue(
            any(isinstance(item, FileItem) for item in result.items)
        )
        self.assertTrue(
            any(isinstance(item, FolderItem) for item in result.items)
        )

    async def test_get_folder_contents_empty(self):
        # Arrange
        folder_path = "empty_folder"
        self.mock_cloud_storage.list_blobs.return_value = []

        # Act
        result = await self.storage.get_folder_contents(folder_path)

        # Assert
        self.assertIsInstance(result, FolderContents)
        self.assertEqual(result.current_path, folder_path)
        self.assertEqual(len(result.items), 0)

    async def test_upload_network_error(self):
        # Arrange
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(return_value=b"test content")

        self.mock_cloud_storage.upload_blob.side_effect = Exception(
            "Network error"
        )

        # Act & Assert
        with self.assertRaises(ErrorSavingFile) as context:
            await self.storage.upload(mock_file, self.mock_request)
        self.assertIn("Network error", str(context.exception))

    async def test_upload_storage_full(self):
        # Arrange
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(return_value=b"test content")

        self.mock_cloud_storage.upload_blob.side_effect = Exception(
            "Storage quota exceeded"
        )

        # Act & Assert
        with self.assertRaises(ErrorSavingFile) as context:
            await self.storage.upload(mock_file, self.mock_request)
        self.assertIn("Storage quota exceeded", str(context.exception))

    async def test_upload_invalid_file_type(self):
        # Arrange
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.exe"
        mock_file.content_type = "application/x-msdownload"
        mock_file.read = AsyncMock(return_value=b"test content")

        self.mock_cloud_storage.upload_blob.side_effect = Exception(
            "Invalid file type"
        )

        # Act & Assert
        with self.assertRaises(ErrorSavingFile) as context:
            await self.storage.upload(mock_file, self.mock_request)
        self.assertIn("Invalid file type", str(context.exception))

    async def test_upload_file_read_error(self):
        # Arrange
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(side_effect=Exception("File read error"))

        # Act & Assert
        with self.assertRaises(ErrorSavingFile) as context:
            await self.storage.upload(mock_file, self.mock_request)
        self.assertIn("File read error", str(context.exception))

    async def test_multi_upload_partial_failure(self):
        # Arrange
        mock_files = [
            Mock(
                spec=UploadFile,
                filename=f"test{i}.txt",
                content_type="text/plain",
            )
            for i in range(3)
        ]
        for file in mock_files:
            file.read = AsyncMock(return_value=b"test content")

        self.mock_cloud_storage.upload_blob.side_effect = [
            "https://storage.googleapis.com/test-bucket/test0.txt",
            Exception("Upload failed for test1.txt"),
            "https://storage.googleapis.com/test-bucket/test2.txt",
        ]

        # Act & Assert
        with self.assertRaises(ErrorSavingFile) as context:
            await self.storage.multi_upload(mock_files, self.mock_request)
        self.assertIn("Upload failed for test1.txt", str(context.exception))

    async def test_delete_file_not_exists(self):
        # Arrange
        file_path = "nonexistent.txt"
        self.mock_cloud_storage.delete_blob.side_effect = Exception(
            "File not found"
        )

        # Act & Assert
        with self.assertRaises(ErrorSavingFile) as context:
            await self.storage.delete(file_path, self.mock_request)
        self.assertIn("File not found", str(context.exception))

    async def test_delete_permission_error(self):
        # Arrange
        file_path = "protected.txt"
        self.mock_cloud_storage.delete_blob.side_effect = Exception(
            "Permission denied"
        )

        # Act & Assert
        with self.assertRaises(ErrorSavingFile) as context:
            await self.storage.delete(file_path, self.mock_request)
        self.assertIn("Permission denied", str(context.exception))

    async def test_delete_network_error(self):
        # Arrange
        file_path = "test.txt"
        self.mock_cloud_storage.delete_blob.side_effect = Exception(
            "Network error"
        )

        # Act & Assert
        with self.assertRaises(ErrorSavingFile) as context:
            await self.storage.delete(file_path, self.mock_request)
        self.assertIn("Network error", str(context.exception))

    async def test_get_folder_iam_policy_success(self):
        # Arrange
        folder_path = "test_folder"
        mock_policy = {"bindings": []}
        self.mock_path_handler.normalize_path.return_value = folder_path
        self.mock_cloud_storage.get_managed_folder_iam_policy.return_value = (
            mock_policy
        )

        # Act
        result = await self.storage.get_folder_iam_policy(folder_path)

        # Assert
        self.assertEqual(result, mock_policy)
        self.mock_cloud_storage.get_managed_folder_iam_policy.assert_called_once_with(
            folder_path
        )

    async def test_set_folder_iam_policy_success(self):
        # Arrange
        folder_path = "test_folder"
        mock_policy = {"bindings": []}
        self.mock_path_handler.normalize_path.return_value = folder_path
        self.mock_cloud_storage.set_managed_folder_iam_policy.return_value = (
            mock_policy
        )

        # Act
        result = await self.storage.set_folder_iam_policy(
            folder_path, mock_policy
        )

        # Assert
        self.assertEqual(result, mock_policy)
        self.mock_cloud_storage.set_managed_folder_iam_policy.assert_called_once_with(
            folder_path, mock_policy
        )
