import os
import shutil
import tempfile
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import UploadFile, Request, HTTPException, status

from src.core.storage.local_storage import LocalStorage
from src.core.storage.shemas import FileDataSchema, FileDeleteSchema


class TestLocalStorage(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage = LocalStorage(self.test_dir)

        self.mock_request = MagicMock(spec=Request)
        self.mock_request.scope = {"user": "test_user"}
        self.mock_request.client = MagicMock()
        self.mock_request.client.host = "127.0.0.1"
        self.mock_request.base_url = "http://testserver"

        self.mock_file = MagicMock(spec=UploadFile)
        self.mock_file.filename = "test_file.txt"
        self.mock_file.content_type = "text/plain"
        self.mock_file.size = 123
        self.file_content = b"test content"
        self.mock_file.read = AsyncMock(return_value=self.file_content)
        self.mock_file.close = AsyncMock()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("src.core.storage.local_storage.os.path.join")
    @patch("src.core.storage.local_storage.open")
    @patch(
        "src.core.storage.decorators.handle_upload_file_exceptions",
        lambda func: func,
    )
    async def test_upload(self, mock_open, mock_join):
        # Arrange
        expected_path = os.path.join(
            self.test_dir, "test_user", "test_file.txt"
        )
        mock_join.return_value = expected_path

        mock_file_handle = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file_handle

        # Act
        result = await self.storage.upload(
            file=self.mock_file, request=self.mock_request
        )

        # Assert
        self.mock_file.read.assert_called_once()
        mock_file_handle.write.assert_called_once_with(self.file_content)
        self.mock_file.close.assert_called_once()

        self.assertIsInstance(result, FileDataSchema)
        self.assertEqual(result.path, expected_path)
        self.assertEqual(result.filename, "test_file.txt")
        self.assertEqual(result.content_type, "text/plain")
        self.assertEqual(result.size, 123)
        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        self.assertEqual(result.creator, "test_user")

    @patch("src.core.storage.local_storage.asyncio.gather")
    @patch(
        "src.core.storage.decorators.handle_upload_file_exceptions",
        lambda func: func,
    )
    async def test_multi_upload(self, mock_gather):
        # Arrange
        mock_file2 = MagicMock(spec=UploadFile)
        mock_file2.filename = "test_file2.txt"

        expected_result = [
            FileDataSchema(
                path=os.path.join(self.test_dir, "test_user", "test_file.txt"),
                url="http://testserver/path/to/test_file.txt",
                message="test_file.txt saved successfully",
                content_type="text/plain",
                size=123,
                filename="test_file.txt",
                status_code=status.HTTP_201_CREATED,
                date_created=datetime.now().strftime("%H:%M:%S %m-%d-%Y"),
                creator="test_user",
            ),
            FileDataSchema(
                path=os.path.join(
                    self.test_dir, "test_user", "test_file2.txt"
                ),
                url="http://testserver/path/to/test_file2.txt",
                message="test_file2.txt saved successfully",
                content_type="text/plain",
                size=123,
                filename="test_file2.txt",
                status_code=status.HTTP_201_CREATED,
                date_created=datetime.now().strftime("%H:%M:%S %m-%d-%Y"),
                creator="test_user",
            ),
        ]
        mock_gather.return_value = expected_result

        # Act
        result = await self.storage.multi_upload(
            files=[self.mock_file, mock_file2], request=self.mock_request
        )

        # Assert
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        mock_gather.assert_called_once()

    @patch("src.core.storage.local_storage.Path.exists")
    @patch("src.core.storage.local_storage.os.remove")
    @patch("src.core.storage.local_storage.logger")
    @patch(
        "src.core.storage.decorators.handle_delete_file_exceptions",
        lambda func: func,
    )
    async def test_delete_file_exists(
        self, mock_logger, mock_remove, mock_exists
    ):
        # Arrange
        file_path = os.path.join(self.test_dir, "test_user", "test_file.txt")
        mock_exists.return_value = True

        # Act
        result = await self.storage.delete(
            file_path=file_path, request=self.mock_request
        )

        # Assert
        mock_exists.assert_called_once()
        mock_remove.assert_called_once()
        mock_logger.info.assert_called_once_with(
            f"{file_path} deleted successfully"
        )

        self.assertIsInstance(result, FileDeleteSchema)
        self.assertEqual(result.file, file_path)
        self.assertEqual(result.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(result.deleted_by, "test_user")

    @patch("src.core.storage.local_storage.Path.exists")
    @patch("src.core.storage.local_storage.logger")
    @patch(
        "src.core.storage.decorators.handle_delete_file_exceptions",
        lambda func: func,
    )
    async def test_delete_file_not_exists(self, mock_logger, mock_exists):
        # Arrange
        file_path = os.path.join(self.test_dir, "test_user", "nonexistent.txt")
        mock_exists.return_value = False

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            await self.storage.delete(
                file_path=file_path, request=self.mock_request
            )

        # Assert
        mock_exists.assert_called_once()
        mock_logger.warning.assert_called_once()

        self.assertEqual(
            context.exception.status_code, status.HTTP_404_NOT_FOUND
        )
        error_detail = context.exception.detail
        self.assertEqual(error_detail["error"], "File not found")
        self.assertEqual(error_detail["message"], f"{file_path} not found")

    def test_get_user_identifier_from_user(self):
        # Arrange
        request = MagicMock(spec=Request)
        request.scope = {"user": "test_user"}

        # Act
        result = LocalStorage._get_user_identifier(request)

        # Assert
        self.assertEqual(result, "test_user")

    def test_get_user_identifier_from_client(self):
        # Arrange
        request = MagicMock(spec=Request)
        request.scope = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        # Act
        result = LocalStorage._get_user_identifier(request)

        # Assert
        self.assertEqual(result, "127.0.0.1")

    def test_get_user_identifier_unknown(self):
        # Arrange
        request = MagicMock(spec=Request)
        request.scope = {}
        request.client = None

        # Act
        result = LocalStorage._get_user_identifier(request)

        # Assert
        self.assertEqual(result, "Unknown")

    @patch("src.core.storage.local_storage.Path")
    def test_create_directory(self, mock_path):
        # Arrange
        mock_dir = MagicMock()
        mock_path.return_value.__truediv__.return_value = mock_dir

        # Act
        result = self.storage._create_directory(self.mock_request)

        # Assert
        mock_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        self.assertEqual(result, mock_dir)

    def test_create_url_path(self):
        # Arrange
        file_path = os.path.join(self.test_dir, "test_user", "test_file.txt")
        request = MagicMock(spec=Request)
        request.base_url = "http://testserver/"

        # Act
        result = LocalStorage._create_url_path(file_path, request)

        # Assert
        self.assertTrue(result.startswith("http://testserver/"))
        self.assertTrue("test_file.txt" in result)
