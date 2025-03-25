import io
import unittest
from unittest.mock import MagicMock, patch

import pymupdf as fitz

from src.services.pdf_tools.annotator import (
    add_comments_to_widgets,
    get_comment_position,
)


class TestAnnotator(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_pdf_path = "test.pdf"
        self.test_comments = {
            "field1": "Test comment 1",
            "field2": "Test comment 2",
        }

    def test_get_comment_position(self):
        """Test the get_comment_position function."""
        # Create a mock widget with rect attribute
        mock_widget = MagicMock(spec=fitz.Widget)
        mock_rect = MagicMock()
        mock_rect.y0 = 100
        mock_widget.rect = mock_rect
        page_width = 500

        # Test the function
        x, y = get_comment_position(page_width, mock_widget)

        # Assert the results
        self.assertEqual(x, page_width - 25)
        self.assertEqual(y, mock_widget.rect.y0)

    @patch("pymupdf.open")
    async def test_add_comments_to_widgets_success(self, mock_fitz_open):
        """Test successful addition of comments to widgets."""
        # Create mock document and page
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.rect.width = 500

        # Create mock widgets
        mock_widget1 = MagicMock(spec=fitz.Widget)
        mock_widget1.field_name = "field1"
        mock_widget2 = MagicMock(spec=fitz.Widget)
        mock_widget2.field_name = "field2"

        # Setup the mock chain
        mock_page.widgets.return_value = [mock_widget1, mock_widget2]
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz_open.return_value = mock_doc

        # Execute the function
        pdf_buffer, pdf_path = await add_comments_to_widgets(
            self.test_pdf_path, self.test_comments
        )

        # Assertions
        self.assertIsInstance(pdf_buffer, io.BytesIO)
        self.assertEqual(pdf_path, self.test_pdf_path)

        # Verify that add_text_annot was called for each widget
        self.assertEqual(mock_page.add_text_annot.call_count, 2)

        # Verify the calls to add_text_annot
        mock_page.add_text_annot.assert_any_call(
            (475, mock_widget1.rect.y0),  # page_width - 25, widget.rect.y0
            "Test comment 1",
            icon="Note",
        )
        mock_page.add_text_annot.assert_any_call(
            (475, mock_widget2.rect.y0), "Test comment 2", icon="Note"
        )

    @patch("pymupdf.open")
    async def test_add_comments_to_widgets_no_matching_fields(
        self, mock_fitz_open
    ):
        """Test when no widget fields match the comments."""
        # Create mock document and page
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.rect.width = 500

        # Create mock widget with non-matching field name
        mock_widget = MagicMock(spec=fitz.Widget)
        mock_widget.field_name = "non_matching_field"

        # Setup the mock chain
        mock_page.widgets.return_value = [mock_widget]
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz_open.return_value = mock_doc

        # Execute the function
        pdf_buffer, pdf_path = await add_comments_to_widgets(
            self.test_pdf_path, self.test_comments
        )

        # Assertions
        self.assertIsInstance(pdf_buffer, io.BytesIO)
        self.assertEqual(pdf_path, self.test_pdf_path)

        # Verify that add_text_annot was not called
        mock_page.add_text_annot.assert_not_called()

    @patch("pymupdf.open")
    async def test_add_comments_to_widgets_empty_page(self, mock_fitz_open):
        """Test when page has no widgets."""
        # Create mock document and page
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.rect.width = 500

        # Setup the mock chain with empty widgets list
        mock_page.widgets.return_value = []
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz_open.return_value = mock_doc

        # Execute the function
        pdf_buffer, pdf_path = await add_comments_to_widgets(
            self.test_pdf_path, self.test_comments
        )

        # Assertions
        self.assertIsInstance(pdf_buffer, io.BytesIO)
        self.assertEqual(pdf_path, self.test_pdf_path)

        # Verify that add_text_annot was not called
        mock_page.add_text_annot.assert_not_called()

    @patch("pymupdf.open")
    async def test_add_comments_to_widgets_empty_comments(
        self, mock_fitz_open
    ):
        """Test when comments dictionary is empty."""
        # Create mock document and page
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.rect.width = 500

        # Create mock widget
        mock_widget = MagicMock(spec=fitz.Widget)
        mock_widget.field_name = "field1"

        # Setup the mock chain
        mock_page.widgets.return_value = [mock_widget]
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz_open.return_value = mock_doc

        # Execute the function with empty comments
        pdf_buffer, pdf_path = await add_comments_to_widgets(
            self.test_pdf_path, {}
        )

        # Assertions
        self.assertIsInstance(pdf_buffer, io.BytesIO)
        self.assertEqual(pdf_path, self.test_pdf_path)

        # Verify that add_text_annot was not called
        mock_page.add_text_annot.assert_not_called()
