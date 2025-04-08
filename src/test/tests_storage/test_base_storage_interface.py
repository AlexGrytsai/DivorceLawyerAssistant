import datetime
import unittest
from typing import Optional, List
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import UploadFile, Request, HTTPException

from src.core.exceptions.storage import ErrorSavingFile
from src.services.storage.interfaces.base_storage_interface import (
    BaseStorageInterface,
)
from src.services.storage.shemas import (
    FileDeleteSchema,
    FolderDeleteSchema,
    FolderContentsSchema,
    FileSchemaForFolder,
    FolderItem,
    FolderDataSchema,
    FolderRenameSchema,
    FileSchema,
)


class TestBaseStorage(unittest.TestCase):
    class MockStorage(BaseStorageInterface):
        """Mock implementation of BaseStorage for testing"""

        async def upload(self, file, request, *args, **kwargs):
            return FileSchema(
                url="http://example.com/mock/test.txt",
                filename="test.txt",
                content_type="text/plain",
            )

        async def multi_upload(self, files, request, *args, **kwargs):
            return [
                FileSchema(
                    url="http://example.com/mock/test.txt",
                    filename="test.txt",
                    content_type="text/plain",
                )
            ]

        async def delete_file(self, file_path, request, *args, **kwargs):
            return FileDeleteSchema(
                file=file_path,
                date_deleted=datetime.datetime.strptime(
                    "2023-01-01", "%Y-%m-%d"
                ),
            )

        async def create_folder(self, folder_path, request, *args, **kwargs):
            return FolderDataSchema(
                folder_name="mock_folder",
                folder_path=folder_path,
                create_time=datetime.datetime.now(),
                update_time=datetime.datetime.now(),
            )

        async def rename_folder(
            self, old_path, new_path, request, *args, **kwargs
        ):
            return FolderRenameSchema(
                folder_name="renamed_folder",
                old_name="mock_folder",
                folder_path=new_path,
            )

        async def delete_folder(self, folder_path, request, *args, **kwargs):
            return FolderDeleteSchema(
                folder_name="mock_folder",
                deleted_time=datetime.datetime.now(),
            )

        async def rename_file(
            self, old_path, new_file_name, request, *args, **kwargs
        ):
            return FileSchema(
                url=f"http://example.com/mock/{new_file_name}",
                filename="renamed.txt",
            )

        async def get_file(self, file_path: str) -> FileSchema:
            return FileSchema(
                url=f"http://example.com/mock/{file_path}",
                filename="test.txt",
                content_type="text/plain",
            )

        async def get_folder_contents(
            self, folder_path: str
        ) -> FolderContentsSchema:
            return FolderContentsSchema(
                current_path=folder_path,
                items=[
                    FileSchemaForFolder(
                        filename="file1.txt",
                        url=f"{folder_path}/file1.txt",
                        content_type="file",
                        type="file",
                        size=100,
                    ),
                    FolderItem(
                        folder_name="subfolder",
                        folder_path=f"{folder_path}/subfolder",
                        type="folder",
                    ),
                ],
            )

        async def list_files(
            self, prefix: Optional[str] = None
        ) -> List[FileSchema]:
            return [
                FileSchema(
                    url=f"http://example.com/mock/{prefix or ''}/file1.txt",
                    filename="file1.txt",
                    content_type="text/plain",
                )
            ]

        async def list_folders(
            self, prefix: Optional[str] = None
        ) -> List[FolderDataSchema]:
            return [
                FolderDataSchema(
                    folder_path="subfolder",
                    folder_name="subfolder",
                )
            ]

        async def search_files_by_name(
            self, search_query: str, case_sensitive: bool = False
        ) -> List[FileSchema]:
            return [
                FileSchema(
                    url="http://example.com/mock/file.txt",
                    filename="file.txt",
                    content_type="text/plain",
                )
            ]

    def setUp(self):
        self.storage = self.MockStorage()
        self.mock_request = MagicMock(spec=Request)
        self.mock_file = MagicMock(spec=UploadFile)
        self.mock_file.filename = "test.txt"
        self.mock_file.content_type = "text/plain"

    @patch("src.core.storage.storage.logger")
    async def test_call_with_file(self, mock_logger):
        # Arrange

        # Act
        result = await self.storage(
            request=self.mock_request, file=self.mock_file
        )

        # Assert
        self.assertIsInstance(result, FileSchema)
        self.assertEqual(result.filename, "test.txt")
        self.assertEqual(result.url, "http://example.com/mock")

    @patch("src.core.storage.storage.logger")
    async def test_call_with_files(self, mock_logger):
        # Arrange
        mock_files = [self.mock_file, self.mock_file]

        # Act
        result = await self.storage(
            request=self.mock_request, files=mock_files
        )

        # Assert
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], FileSchema)

    @patch("src.core.storage.storage.logger")
    async def test_call_with_no_files(self, mock_logger):
        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            await self.storage(request=self.mock_request)

        # Assert
        self.assertEqual(context.exception.status_code, 400)
        error_msg = "No file or files provided"
        self.assertEqual(context.exception.detail, error_msg)
        mock_logger.warning.assert_called_once_with(error_msg)

    @patch("src.core.storage.storage.logger")
    async def test_call_with_error_saving_file(self, mock_logger):
        # Arrange
        error_message = "Error saving file test"
        self.storage.upload = AsyncMock(
            side_effect=ErrorSavingFile(error_message)
        )

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            await self.storage(request=self.mock_request, file=self.mock_file)

        # Assert
        self.assertEqual(context.exception.status_code, 500)
        error_detail = context.exception.detail
        self.assertEqual(error_detail["error"], error_message)
        self.assertEqual(
            error_detail["message"], "File upload was unsuccessful"
        )
        mock_logger.warning.assert_called_once_with(
            f"Error saving file: {error_message}"
        )
