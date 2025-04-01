import io
import json
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.storage.shemas import FileDataSchema
from src.services.ai_service.ai_text_validator import OpenAITextAnalyzer
from src.services.check_pdf_fields import (
    scrap_pdf_fields,
    prepare_scraped_data,
    validate_pdf_fields,
    check_fields_in_pdf_file,
    main_check_pdf_fields,
)
from src.services.pdf_tools.parser_pdf import ParserPDFBase, ParserPDFWidget
from src.services.pdf_tools.scraper_pdf import ScrapedPage
from src.utils.validators.text_validator import (
    TextBaseValidator,
    TextWidgetValidatorUseAI,
)


class TestCheckPdfFields(unittest.TestCase):
    def setUp(self):
        # Setup common test data
        self.test_pdf_path = "test_file.pdf"
        data_dir_path = os.path.dirname(__file__)
        self.test_data_dir = os.path.join(
            data_dir_path, "..", "data_for_tests"
        )

        # Load test data from JSON files
        fields_file = "pdf_form_value_fields_for_tests_CASE_1.json"
        fields_path = os.path.join(self.test_data_dir, fields_file)
        with open(fields_path, "r") as f:
            self.test_widget_data = json.load(f)

        errors_file = "pdf_form_field_errors_CASE_1.json"
        errors_path = os.path.join(self.test_data_dir, errors_file)
        with open(errors_path, "r") as f:
            self.test_errors = json.load(f)

        # Create mocks
        self.mock_ai_assistant = AsyncMock(spec=OpenAITextAnalyzer)
        self.mock_parser = AsyncMock(spec=ParserPDFBase)
        self.mock_validator = AsyncMock(spec=TextBaseValidator)
        self.mock_scraped_page = MagicMock(spec=ScrapedPage)
        self.mock_scraped_page.widgets = []
        self.mock_scraped_page.text_data = []
        self.mock_scraped_page.tables = []

    @patch("src.services.check_pdf_fields.ScraperWidgetFromPDF")
    async def test_scrap_pdf_fields(self, mock_scraper_class):
        # Arrange
        mock_scraper_instance = mock_scraper_class.return_value
        mock_scraper_instance.scrap_data.return_value = [
            self.mock_scraped_page
        ]

        # Act
        result = await scrap_pdf_fields(self.test_pdf_path)

        # Assert
        mock_scraper_class.assert_called_once_with(self.test_pdf_path)
        mock_scraper_instance.scrap_data.assert_called_once()
        self.assertEqual(result, [self.mock_scraped_page])

    async def test_prepare_scraped_data(self):
        # Arrange
        mock_scraped_data = [self.mock_scraped_page]

        # Act
        await prepare_scraped_data(self.mock_parser, mock_scraped_data)

        # Assert
        self.mock_parser.prepare_data.assert_called_once_with(
            mock_scraped_data
        )

    async def test_validate_pdf_fields(self):
        # Arrange
        widget_data = {"widget_name": {"value": "test_value"}}
        self.mock_parser.widget_data_dict = widget_data
        self.mock_validator.validate_widgets.return_value = {
            "widget_name": "error_message"
        }

        # Act
        result = await validate_pdf_fields(
            self.mock_parser.widget_data_dict, self.mock_validator
        )

        # Assert
        call_arg = self.mock_parser.widget_data_dict
        self.mock_validator.validate_widgets.assert_called_once_with(call_arg)
        self.assertEqual(result, {"widget_name": "error_message"})

    @patch("src.services.check_pdf_fields.scrap_pdf_fields")
    @patch("src.services.check_pdf_fields.prepare_scraped_data")
    @patch("src.services.check_pdf_fields.validate_pdf_fields")
    @patch("src.services.check_pdf_fields.add_comments_to_widgets")
    async def test_check_fields_in_pdf_file(
        self, mock_add_comments, mock_validate, mock_prepare, mock_scrap
    ):
        # Arrange
        mock_scrap.return_value = [self.mock_scraped_page]
        self.mock_parser.widget_data_dict = self.test_widget_data
        mock_validate.return_value = self.test_errors
        pdf_buffer = io.BytesIO(b"test pdf content")
        mock_add_comments.return_value = (pdf_buffer, self.test_pdf_path)

        # Act
        result = await check_fields_in_pdf_file(
            self.test_pdf_path, self.mock_parser, self.mock_validator
        )

        # Assert
        mock_scrap.assert_called_once_with(self.test_pdf_path)
        mock_prepare.assert_called_once_with(
            self.mock_parser, [self.mock_scraped_page]
        )
        test_data = self.test_widget_data
        test_validator = self.mock_validator
        mock_validate.assert_called_once_with(test_data, test_validator)
        mock_add_comments.assert_called_once_with(
            pdf_path=self.test_pdf_path, comments=self.test_errors
        )
        self.assertEqual(result, (pdf_buffer, self.test_pdf_path))

    @patch("src.services.check_pdf_fields.check_fields_in_pdf_file")
    @patch("src.services.check_pdf_fields.multi_save_pdf_to_new_file")
    async def test_main_check_pdf_fields(self, mock_save, mock_check):
        # Arrange
        pdf_paths = [self.test_pdf_path, "test_file2.pdf"]
        pdf_buffers = [
            (io.BytesIO(b"test pdf 1"), pdf_paths[0]),
            (io.BytesIO(b"test pdf 2"), pdf_paths[1]),
        ]
        mock_check.side_effect = pdf_buffers

        expected_file_data = [
            FileDataSchema(
                path="path/to/file1.pdf",
                url="http://example.com/file1.pdf",
                size=100,
                filename="file1.pdf",
                content_type="application/pdf",
                status_code=200,
                message="File saved",
                date_created="2023-01-01",
                creator="test",
            ),
            FileDataSchema(
                path="path/to/file2.pdf",
                url="http://example.com/file2.pdf",
                size=200,
                filename="file2.pdf",
                content_type="application/pdf",
                status_code=200,
                message="File saved",
                date_created="2023-01-01",
                creator="test",
            ),
        ]
        mock_save.return_value = expected_file_data

        # Act
        result = await main_check_pdf_fields(
            urls_to_pdf=pdf_paths,
            ai_assistant=self.mock_ai_assistant,
            widget_parser_type=ParserPDFWidget,
            validator_type=TextWidgetValidatorUseAI,
            extra_kwarg="test",
        )

        # Assert
        # Verify check_fields_in_pdf_file was called twice
        self.assertEqual(mock_check.call_count, 2)
        # Check first call
        args1, kwargs1 = mock_check.call_args_list[0]
        self.assertEqual(kwargs1["path_to_pdf"], pdf_paths[0])
        self.assertIsInstance(kwargs1["parser_instance"], ParserPDFWidget)
        self.assertEqual(kwargs1["extra_kwarg"], "test")

        # Verify multi_save_pdf_to_new_file was called correctly
        mock_save.assert_called_once()
        args, kwargs = mock_save.call_args
        self.assertEqual(kwargs["list_pdf_buffer"], pdf_buffers)
        self.assertEqual(kwargs["extra_kwarg"], "test")

        # Verify result
        self.assertEqual(result, expected_file_data)
