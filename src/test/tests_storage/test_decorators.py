import shutil
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException, status

from src.core.exceptions.storage import ErrorUploadingFile, ErrorDeletingFile
from src.services.storage.decorators import (
    handle_upload_file_exceptions,
    handle_delete_file_exceptions,
)
from src.services.storage.shemas import FileSchema, FileDeleteSchema


class TestUploadFileExceptionsDecorator(unittest.TestCase):
    """
    Tests for the handle_upload_file_exceptions decorator
    """

    def setUp(self):
        # Mock successful function
        self.mock_success_result = FileSchema(
            url="http://example.com/mock",
            filename="test.txt",
            content_type="text/plain",
            size=100,
        )

        # Create a mock async function that succeeds
        self.mock_success_func = AsyncMock(
            return_value=self.mock_success_result
        )
        self.decorated_success_func = handle_upload_file_exceptions(
            self.mock_success_func
        )

        # Create a mock async function that raises ErrorUploadingFile
        self.test_exception = ErrorUploadingFile("Test upload error")
        self.mock_error_func = AsyncMock(side_effect=self.test_exception)
        self.decorated_error_func = handle_upload_file_exceptions(
            self.mock_error_func
        )

        # Path to static directory that needs to be cleaned up after tests
        self.static_dir = Path("src/test/static")

    def tearDown(self):
        # Clean up the static directory after tests
        if self.static_dir.exists():
            shutil.rmtree(self.static_dir, ignore_errors=True)

    async def test_successful_function_execution(self):
        """Test decorator passes through the result when no exception occurs"""
        # Call the decorated function
        result = await self.decorated_success_func()

        # Verify the original function was called
        self.mock_success_func.assert_called_once()

        # Verify the result is unchanged
        self.assertEqual(result, self.mock_success_result)

    async def test_error_handling(self):
        """Test that the decorator handles ErrorUploadingFile exceptions"""
        # Call the decorated function which raises an exception
        with self.assertRaises(HTTPException) as context:
            await self.decorated_error_func()

        # Verify the original function was called
        self.mock_error_func.assert_called_once()

        # Verify the HTTPException has correct status code and detail
        exception = context.exception
        self.assertEqual(exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            exception.detail,
            {
                "error": str(self.test_exception),
                "message": "File upload was unsuccessful",
            },
        )

    @patch("src.core.storage.decorators.logger")
    async def test_logging(self, mock_logger):
        """Test that the decorator logs the error properly"""
        # Call the decorated function which raises an exception
        with self.assertRaises(HTTPException):
            await self.decorated_error_func()

        # Verify that warning was logged
        mock_logger.warning.assert_called_once()
        # Check that the log message contains the exception
        self.assertIn(
            str(self.test_exception), mock_logger.warning.call_args[0][0]
        )


class TestDeleteFileExceptionsDecorator(unittest.TestCase):
    """
    Tests for the handle_delete_file_exceptions decorator
    """

    def setUp(self):
        # Mock successful function
        self.mock_success_result = FileDeleteSchema(
            file="/mock/path/test.txt",
            date_deleted=datetime.strptime("2023-01-01", "%Y-%m-%d"),
        )

        # Create a mock async function that succeeds
        self.mock_success_func = AsyncMock(
            return_value=self.mock_success_result
        )
        self.decorated_success_func = handle_delete_file_exceptions(
            self.mock_success_func
        )

        # Create a mock async function that raises ErrorDeletingFile
        self.test_file_path = "/test/file/path.txt"
        self.test_exception = ErrorDeletingFile("Test delete error")
        self.mock_error_func = AsyncMock(side_effect=self.test_exception)
        self.decorated_error_func = handle_delete_file_exceptions(
            self.mock_error_func
        )

        # Path to static directory that needs to be cleaned up after tests
        self.static_dir = Path("src/test/static")

    def tearDown(self):
        # Clean up the static directory after tests
        if self.static_dir.exists():
            shutil.rmtree(self.static_dir, ignore_errors=True)

    async def test_successful_function_execution(self):
        """Test decorator passes through the result when no exception occurs"""
        # Call the decorated function
        result = await self.decorated_success_func()

        # Verify the original function was called
        self.mock_success_func.assert_called_once()

        # Verify the result is unchanged
        self.assertEqual(result, self.mock_success_result)

    async def test_error_handling_with_file_path(self):
        """Test error handling when file_path is provided as named argument"""
        # Call the decorated function which raises an exception
        with self.assertRaises(HTTPException) as context:
            await self.decorated_error_func(file_path=self.test_file_path)

        # Verify the original function was called with the file_path
        self.mock_error_func.assert_called_once_with(
            file_path=self.test_file_path
        )

        # Verify the HTTPException has correct status code and detail
        exception = context.exception
        self.assertEqual(
            exception.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        self.assertEqual(
            exception.detail,
            {
                "error": str(self.test_exception),
                "message": f"Error deleting {self.test_file_path}",
            },
        )

    async def test_error_handling_without_file_path(self):
        """Test error handling when file_path is not provided"""
        # Call the decorated function which raises an exception
        with self.assertRaises(HTTPException) as context:
            await self.decorated_error_func()

        # Verify the original function was called
        self.mock_error_func.assert_called_once_with()

        # Verify the HTTPException has correct status code and detail
        exception = context.exception
        self.assertEqual(
            exception.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        default_path = "file_path not transferred as a named argument"
        self.assertEqual(
            exception.detail,
            {
                "error": str(self.test_exception),
                "message": f"Error deleting {default_path}",
            },
        )

    @patch("src.core.storage.decorators.logger")
    async def test_logging(self, mock_logger):
        """Test that the decorator logs the error properly"""
        # Call the decorated function which raises an exception
        with self.assertRaises(HTTPException):
            await self.decorated_error_func(file_path=self.test_file_path)

        # Verify that error was logged
        mock_logger.error.assert_called_once()
        # Check that the log message contains the file path and exception
        log_message = mock_logger.error.call_args[0][0]
        self.assertIn(self.test_file_path, log_message)
        self.assertIn(str(self.test_exception), log_message)
