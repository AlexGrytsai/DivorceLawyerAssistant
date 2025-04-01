import unittest
from typing import Optional, List
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import UploadFile, Request, HTTPException

from src.core.exceptions.storage import ErrorSavingFile
from src.core.storage.interfaces.base_storage_interface import (
    BaseStorageInterface,
)
from src.core.storage.shemas import (
    FileDataSchema,
    FileDeleteSchema,
    FolderDataSchema,
    FolderDeleteSchema,
    FolderContents,
    FileItem,
    FolderItem,
)


class TestBaseStorage(unittest.TestCase):
    class MockStorage(BaseStorageInterface):
        """Mock implementation of BaseStorage for testing"""

        async def upload(self, file, request, *args, **kwargs):
            return FileDataSchema(
                path="/mock/path",
                url="http://example.com/mock",
                filename="test.txt",
                content_type="text/plain",
                status_code=200,
                message="Success",
                date_created="2023-01-01",
                creator="test",
            )

        async def multi_upload(self, files, request, *args, **kwargs):
            return [
                FileDataSchema(
                    path=f"/mock/path/{i}",
                    url=f"http://example.com/mock/{i}",
                    filename=f"test{i}.txt",
                    content_type="text/plain",
                    status_code=200,
                    message="Success",
                    date_created="2023-01-01",
                    creator="test",
                )
                for i in range(len(files))
            ]

        async def delete(self, file_path, request, *args, **kwargs):
            return FileDeleteSchema(
                file=file_path,
                message="Deleted",
                status_code=200,
                date_deleted="2023-01-01",
                deleted_by="test",
            )

        async def create_folder(self, folder_path, request, *args, **kwargs):
            return FolderDataSchema(
                path=folder_path,
                name="mock_folder",
                status_code=200,
                message="Folder created",
                date_created="2023-01-01",
                creator="test",
                parent_folder="/mock",
                is_empty=True,
            )

        async def rename_folder(
            self, old_path, new_path, request, *args, **kwargs
        ):
            return FolderDataSchema(
                path=new_path,
                name="renamed_folder",
                status_code=200,
                message="Folder renamed",
                date_created="2023-01-01",
                creator="test",
                parent_folder="/mock",
                is_empty=True,
            )

        async def delete_folder(self, folder_path, request, *args, **kwargs):
            return FolderDeleteSchema(
                folder=folder_path,
                message="Folder deleted",
                status_code=200,
                date_deleted="2023-01-01",
                deleted_by="test",
                deleted_files_count=0,
            )

        async def rename_file(
            self, old_path, new_path, request, *args, **kwargs
        ):
            return FileDataSchema(
                path=new_path,
                url=f"http://example.com/mock/{new_path}",
                filename="renamed.txt",
                status_code=200,
                message="File renamed",
                date_created="2023-01-01",
                creator="test",
            )

        async def get_file(self, file_path: str) -> FileDataSchema:
            return FileDataSchema(
                path=file_path,
                url=f"http://example.com/mock/{file_path}",
                filename="test.txt",
                content_type="text/plain",
                status_code=200,
                message="Success",
                date_created="2023-01-01",
                creator="test",
            )

        async def get_folder_contents(
            self, folder_path: str
        ) -> FolderContents:
            return FolderContents(
                current_path=folder_path,
                items=[
                    FileItem(
                        name="file1.txt",
                        path=f"{folder_path}/file1.txt",
                        type="file",
                        size=100,
                        updated="2023-01-01",
                    ),
                    FolderItem(
                        name="subfolder",
                        path=f"{folder_path}/subfolder",
                        type="folder",
                    ),
                ],
            )

        async def list_files(
            self, prefix: Optional[str] = None
        ) -> List[FileDataSchema]:
            return [
                FileDataSchema(
                    path=f"{prefix or ''}/file1.txt",
                    url=f"http://example.com/mock/{prefix or ''}/file1.txt",
                    filename="file1.txt",
                    content_type="text/plain",
                    status_code=200,
                    message="Success",
                    date_created="2023-01-01",
                    creator="test",
                )
            ]

        async def list_folders(
            self, prefix: Optional[str] = None
        ) -> List[FolderDataSchema]:
            return [
                FolderDataSchema(
                    path=f"{prefix or ''}/subfolder",
                    name="subfolder",
                    status_code=200,
                    message="Success",
                    date_created="2023-01-01",
                    creator="test",
                    parent_folder=prefix or "",
                    is_empty=True,
                )
            ]

        async def search_files_by_name(
            self, search_query: str, case_sensitive: bool = False
        ) -> List[FileDataSchema]:
            return [
                FileDataSchema(
                    path="/mock/path/file.txt",
                    url="http://example.com/mock/file.txt",
                    filename="file.txt",
                    content_type="text/plain",
                    status_code=200,
                    message="Success",
                    date_created="2023-01-01",
                    creator="test",
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
        self.assertIsInstance(result, FileDataSchema)
        self.assertEqual(result.filename, "test.txt")
        self.assertEqual(result.path, "/mock/path")
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
        self.assertIsInstance(result[0], FileDataSchema)
        self.assertEqual(result[0].path, "/mock/path/0")
        self.assertEqual(result[1].path, "/mock/path/1")

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
