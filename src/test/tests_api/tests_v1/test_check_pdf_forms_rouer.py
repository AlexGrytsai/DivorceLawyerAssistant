import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import UploadFile, Request
from fastapi.testclient import TestClient

from src.api.v1.check_pdf_forms.router import (
    router_pdf_check,
    simple_check_pdf_forms,
    delete_file,
)
from src.core.storage.shemas import FileDataSchema, FileDeleteSchema
from src.services.ai_service.ai_text_validator import OpenAITextAnalyzer


class TestCheckPDFFormsRouter(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(router_pdf_check)
        self.mock_request = MagicMock(spec=Request)
        self.mock_request.scope = {"user": "test_user"}
        self.mock_request.client = MagicMock()
        self.mock_request.client.host = "127.0.0.1"
        self.mock_request.base_url = "http://testserver"

        # Create mock for uploaded file
        self.mock_file = MagicMock(spec=UploadFile)
        self.mock_file.filename = "test_form.pdf"
        self.mock_file.content_type = "application/pdf"
        self.mock_file.size = 1024
        self.file_content = b"test pdf content"
        self.mock_file.read = AsyncMock(return_value=self.file_content)
        self.mock_file.close = AsyncMock()

        # Create mock for file upload result
        self.uploaded_file_data = FileDataSchema(
            path="/mock/path/test_form.pdf",
            url="http://testserver/mock/path/test_form.pdf",
            filename="test_form.pdf",
            content_type="application/pdf",
            size=1024,
            status_code=201,
            message="Success",
            date_created="2023-01-01",
            creator="test_user",
        )

        # Create mock for PDF checking result
        self.checked_file_data = FileDataSchema(
            path="/mock/path/test_form_with_simple_check.pdf",
            url="http://testserver/mock/path/test_form_with_simple_check.pdf",
            filename="test_form_with_simple_check.pdf",
            content_type="application/pdf",
            size=1536,
            status_code=201,
            message="Success",
            date_created="2023-01-01",
            creator="test_user",
        )

        # Create mock for file deletion result
        self.deleted_file_data = FileDeleteSchema(
            file="/mock/path/test_form.pdf",
            message="File deleted successfully",
            status_code=204,
            date_deleted="2023-01-01",
            deleted_by="test_user",
        )

    @patch("src.utils.validators.validate_file_mime.validate_files")
    @patch("src.core.settings.STORAGE")
    @patch("src.services.check_pdf_fields.main_check_pdf_fields")
    async def test_simple_check_pdf_forms_success(
        self, mock_main_check_pdf_fields, mock_storage, mock_validate_files
    ):
        """Test successful PDF form checking."""
        # Configure mocks
        mock_validate_files.return_value = [self.mock_file]
        mock_storage.return_value = [self.uploaded_file_data]
        mock_main_check_pdf_fields.return_value = [self.checked_file_data]

        # Execute request
        response = await simple_check_pdf_forms(
            request=self.mock_request, files=[self.mock_file]
        )

        # Verify results
        self.assertEqual(response, [self.checked_file_data])
        mock_validate_files.assert_called_once_with([self.mock_file])
        mock_storage.assert_called_once_with(
            files=[self.mock_file], request=self.mock_request
        )
        mock_main_check_pdf_fields.assert_called_once_with(
            [str(self.uploaded_file_data.path)],
            ai_assistant=unittest.mock.ANY,
            request=self.mock_request,
        )
        # Verify that correct AI analyzer instance was passed
        ai_assistant_arg = mock_main_check_pdf_fields.call_args[0][1]
        self.assertIsInstance(ai_assistant_arg, OpenAITextAnalyzer)

    @patch("src.utils.validators.validate_file_mime.validate_files")
    @patch("src.core.settings.STORAGE")
    @patch("src.services.check_pdf_fields.main_check_pdf_fields")
    async def test_simple_check_pdf_forms_with_single_file(
        self, mock_main_check_pdf_fields, mock_storage, mock_validate_files
    ):
        """Test PDF form checking with a single file.

        This test simulates a scenario where the storage returns
        a single object instead of a list.
        """
        # Configure mocks to simulate return of a single object
        # instead of a list
        mock_validate_files.return_value = [self.mock_file]
        # Return a single object
        mock_storage.return_value = self.uploaded_file_data
        mock_main_check_pdf_fields.return_value = [self.checked_file_data]

        # Execute request
        response = await simple_check_pdf_forms(
            request=self.mock_request, files=[self.mock_file]
        )

        # Verify results
        self.assertEqual(response, [self.checked_file_data])
        mock_validate_files.assert_called_once_with([self.mock_file])
        mock_storage.assert_called_once_with(
            files=[self.mock_file], request=self.mock_request
        )
        mock_main_check_pdf_fields.assert_called_once_with(
            [str(self.uploaded_file_data.path)],
            ai_assistant=unittest.mock.ANY,
            request=self.mock_request,
        )

    @patch("src.core.settings.STORAGE.delete")
    async def test_delete_file_success(self, mock_delete):
        """Test successful file deletion."""
        # Configure mock
        mock_delete.return_value = self.deleted_file_data
        file_path = "/mock/path/test_form.pdf"

        # Execute request
        response = await delete_file(
            request=self.mock_request, file_path=file_path
        )

        # Verify results
        self.assertEqual(response, self.deleted_file_data)
        mock_delete.assert_called_once_with(
            file_path=file_path, request=self.mock_request
        )

    @patch("src.utils.validators.validate_file_mime.validate_files")
    async def test_validate_files_integration(self, mock_validate_files):
        """Test integration with file validator."""
        # Configure mock
        mock_validate_files.return_value = [self.mock_file]

        # Simulate validator call
        validated_files = await mock_validate_files([self.mock_file])

        # Verify results
        self.assertEqual(validated_files, [self.mock_file])
        mock_validate_files.assert_called_once_with([self.mock_file])
