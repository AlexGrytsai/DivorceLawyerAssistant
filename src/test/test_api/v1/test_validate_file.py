import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from starlette.datastructures import UploadFile

from src.api.v1.check_pdf_forms.validate_file import validate_files


class TestValidateFiles(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.get_real_mime_type = (
            "src.api.v1.check_pdf_forms.validate_file.get_real_mime_type"
        )

    async def test_validate_files_success(self):
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.read.return_value = b"dummy data"
        mock_file.seek.return_value = None

        with patch(
            self.get_real_mime_type,
            return_value="application/pdf",
        ):
            files = await validate_files([mock_file])

        self.assertEqual(files, [mock_file])
        mock_file.seek.assert_called_once_with(0)

    async def test_validate_files_invalid_mime(self):
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "test.exe"
        mock_file.read.return_value = b"dummy data"

        with patch(
            self.get_real_mime_type,
            return_value="application/x-msdownload",
        ):
            with self.assertRaises(HTTPException) as exc:
                await validate_files([mock_file])

        self.assertEqual(exc.exception.status_code, 400)
        self.assertIn("has wrong MIME type", exc.exception.detail)

    async def test_validate_files_fake_mime_type(self):
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.read.return_value = b"fake pdf data"

        with patch(
            self.get_real_mime_type,
            return_value="application/x-executable",
        ):
            with self.assertRaises(HTTPException) as exc:
                await validate_files([mock_file])

        self.assertEqual(exc.exception.status_code, 400)
        self.assertIn("has wrong MIME type", exc.exception.detail)
