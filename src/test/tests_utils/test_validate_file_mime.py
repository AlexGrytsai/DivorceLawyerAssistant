import asyncio
import unittest
from unittest.mock import patch, AsyncMock, MagicMock

from fastapi import UploadFile, HTTPException

from src.utils.validators.validate_file_mime import (
    get_real_mime_type,
    check_mime_type,
    validate_files,
    ALLOWED_MIME_TYPES_FOR_FORMS,
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
            result = asyncio.run(check_mime_type(mock_file))

            is_valid, file = result
            self.assertTrue(is_valid)
            self.assertEqual(file, mock_file)

    def test_check_mime_type_invalid(self):
        # Test with invalid MIME type
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.read.return_value = b"fake exe content"

        with patch(
            "src.utils.validators.validate_file_mime.get_real_mime_type",
            return_value="application/x-msdownload",
        ):
            result = asyncio.run(check_mime_type(mock_file))

            is_valid, file = result
            self.assertFalse(is_valid)
            self.assertEqual(file, mock_file)

    def test_validate_files_all_valid(self):
        # Test when all files are valid
        mock_file1 = AsyncMock(spec=UploadFile)
        mock_file1.filename = "test1.pdf"
        mock_file2 = AsyncMock(spec=UploadFile)
        mock_file2.filename = "test2.doc"

        with patch(
            "src.utils.validators.validate_file_mime.check_mime_type"
        ) as mock_check:
            # Use a simpler approach: just return pre-defined values
            mock_check.side_effect = lambda file: asyncio.Future(
                loop=asyncio.get_event_loop_policy().get_event_loop()
            ).set_result((True, file)) or asyncio.Future(
                loop=asyncio.get_event_loop_policy().get_event_loop()
            )

            # Create a mock that will run asynchronously but return a known value
            async def async_return(file):
                return (True, file)

            mock_check.side_effect = async_return

            result = asyncio.run(validate_files([mock_file1, mock_file2]))

            self.assertEqual(result, [mock_file1, mock_file2])
            # Check that both files were processed
            self.assertEqual(mock_check.call_count, 2)
            for file in result:
                file.seek.assert_called_once_with(0)

    def test_validate_files_one_invalid(self):
        # Test when one file is invalid
        mock_file1 = AsyncMock(spec=UploadFile)
        mock_file1.filename = "test1.pdf"
        mock_file2 = AsyncMock(spec=UploadFile)
        mock_file2.filename = "test2.exe"

        with patch(
            "src.utils.validators.validate_file_mime.check_mime_type"
        ) as mock_check:
            # Return different results based on which file is passed
            async def async_side_effect(file):
                if file.filename == "test1.pdf":
                    return (True, file)
                else:
                    return (False, file)

            mock_check.side_effect = async_side_effect

            with self.assertRaises(HTTPException) as context:
                asyncio.run(validate_files([mock_file1, mock_file2]))

            self.assertEqual(context.exception.status_code, 400)
            self.assertIn(
                "test2.exe has wrong MIME type", context.exception.detail
            )

    def test_spoofed_extension(self):
        # Test a file with mismatched extension (exe disguised as pdf)
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "malicious.pdf"  # Looks like PDF but isn't
        mock_file.read.return_value = (
            b"MZ\x90\x00\x03\x00\x00\x00"  # Typical EXE header
        )

        with patch(
            "src.utils.validators.validate_file_mime.get_real_mime_type",
            return_value="application/x-msdownload",
        ):  # EXE mime type
            result = asyncio.run(check_mime_type(mock_file))

            is_valid, file = result
            self.assertFalse(is_valid)  # Should detect it's not actually a PDF

    def test_validate_empty_file_list(self):
        # Test with empty file list
        result = asyncio.run(validate_files([]))
        self.assertEqual(result, [])

    def test_all_allowed_mime_types(self):
        # Test all allowed MIME types
        for mime_type in ALLOWED_MIME_TYPES_FOR_FORMS:
            mock_file = AsyncMock(spec=UploadFile)
            mock_file.filename = f"test.{mime_type.split('/')[-1]}"

            with patch(
                "src.utils.validators.validate_file_mime.get_real_mime_type",
                return_value=mime_type,
            ):
                result = asyncio.run(check_mime_type(mock_file))

                is_valid, file = result
                self.assertTrue(is_valid)
