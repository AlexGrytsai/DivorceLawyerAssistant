import asyncio
import unittest
from unittest.mock import patch, AsyncMock, MagicMock

from fastapi import UploadFile, HTTPException

from src.utils.validators.validate_file_mime import (
    get_real_mime_type,
    check_mime_type,
    validate_file_mime,
)

ALLOWED_MIME_TYPES_FOR_TEST = (
    "application/pdf",
    "application/msword",  # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
)


class TestValidateFileMime(unittest.TestCase):

    def test_get_real_mime_type(self):
        # Test with PDF content
        with patch("magic.Magic") as MockMagic:
            mock_instance = MockMagic.return_value
            mock_instance.from_buffer.return_value = "application/pdf"

            result = get_real_mime_type(b"fake pdf content")

            MockMagic.assert_called_once_with(mime=True)
            mock_instance.from_buffer.assert_called_once_with(
                b"fake pdf content"
            )
            self.assertEqual(result, "application/pdf")

    async def async_test(self, coroutine):
        return await coroutine

    def test_check_mime_type_valid(self):
        # Test with valid MIME type
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.read.return_value = b"fake pdf content"

        with patch(
            "src.utils.validators.validate_file_mime.get_real_mime_type",
            return_value="application/pdf",
        ):
            result = asyncio.run(check_mime_type(mock_file, ALLOWED_MIME_TYPES_FOR_TEST))

            is_valid, file = result
            self.assertTrue(is_valid)
            self.assertEqual(file, mock_file)

    def test_check_mime_type_invalid(self):
        # Test with invalid MIME type
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.read.return_value = b"fake content"

        with patch(
            "src.utils.validators.validate_file_mime.get_real_mime_type",
            return_value="application/x-msdownload",
        ):
            result = asyncio.run(check_mime_type(mock_file, ALLOWED_MIME_TYPES_FOR_TEST))

            is_valid, file = result
            self.assertFalse(is_valid)
            self.assertEqual(file, mock_file)

    def test_validate_files_all_valid(self):
        # Test when all files are valid
        mock_file1 = AsyncMock(spec=UploadFile)
        mock_file2 = AsyncMock(spec=UploadFile)
        mock_file1.read.return_value = b"fake pdf content"
        mock_file2.read.return_value = b"fake doc content"

        with patch(
            "src.utils.validators.validate_file_mime.get_real_mime_type",
            side_effect=["application/pdf", "application/msword"],
        ):
            result = asyncio.run(
                validate_file_mime([mock_file1, mock_file2], ALLOWED_MIME_TYPES_FOR_TEST)
            )

            self.assertTrue(result)

    def test_validate_files_one_invalid(self):
        # Test when one file is invalid
        mock_file1 = AsyncMock(spec=UploadFile)
        mock_file2 = AsyncMock(spec=UploadFile)
        mock_file1.read.return_value = b"fake pdf content"
        mock_file2.read.return_value = b"fake exe content"

        with patch(
            "src.utils.validators.validate_file_mime.get_real_mime_type",
            side_effect=["application/pdf", "application/x-msdownload"],
        ):
            with self.assertRaises(HTTPException):
                asyncio.run(
                    validate_file_mime([mock_file1, mock_file2], ALLOWED_MIME_TYPES_FOR_TEST)
                )

    def test_spoofed_extension(self):
        # Test a file with mismatched extension (exe disguised as pdf)
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "malicious.exe.pdf"
        mock_file.read.return_value = b"fake exe content"

        with patch(
            "src.utils.validators.validate_file_mime.get_real_mime_type",
            return_value="application/x-msdownload",
        ):
            result = asyncio.run(check_mime_type(mock_file, ALLOWED_MIME_TYPES_FOR_TEST))

            is_valid, file = result
            self.assertFalse(is_valid)
            self.assertEqual(file, mock_file)

    def test_validate_empty_file_list(self):
        # Test with empty file list
        result = asyncio.run(validate_file_mime([], ALLOWED_MIME_TYPES_FOR_TEST))
        self.assertTrue(result)

    def test_all_allowed_mime_types(self):
        # Test all allowed MIME types
        # sourcery skip: no-loop-in-tests
        for mime_type in ALLOWED_MIME_TYPES_FOR_TEST:
            mock_file = AsyncMock(spec=UploadFile)
            mock_file.read.return_value = b"fake content"

            with patch(
                "src.utils.validators.validate_file_mime.get_real_mime_type",
                return_value=mime_type,
            ):
                result = asyncio.run(check_mime_type(mock_file, ALLOWED_MIME_TYPES_FOR_TEST))

                is_valid, file = result
                self.assertTrue(is_valid)
                self.assertEqual(file, mock_file)
