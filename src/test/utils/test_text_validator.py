import json
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.ai_service.ai_text_validator import (
    AIBaseValidator,
    OpenAITextAnalyzer,
)
from src.utils.validators.text_validator import TextWidgetValidatorUseAI


class MockWidget:
    def __init__(self, field_value="", text_fontsize=10, rect_width=100):
        self.field_value = field_value
        self.text_fontsize = text_fontsize
        self.rect = MagicMock()
        self.rect.width = rect_width


class TestTextWidgetValidatorUseAI(unittest.TestCase):
    def setUp(self):
        self.ai_assistant = AsyncMock(spec=OpenAITextAnalyzer)
        self.validator = TextWidgetValidatorUseAI(self.ai_assistant)

        base_dir = Path(__file__).parent.parent
        data_dir = base_dir / "data_for_tests"

        # Load test data
        with open(
            data_dir / "pdf_form_value_fields_for_tests_CASE_1.json"
        ) as f:
            self.test_values = json.load(f)

        with open(data_dir / "pdf_form_field_errors_CASE_1.json") as f:
            self.expected_errors = json.load(f)

    @patch("fitz.Font")
    async def test_validate_line_length_success(self, mock_font):
        # Setup
        mock_font_instance = MagicMock()
        mock_font_instance.text_length.return_value = 50
        mock_font.return_value = mock_font_instance

        widget = MockWidget(field_value="Test text", text_fontsize=12)

        # Execute
        result, message = await TextWidgetValidatorUseAI.validate_line_length(
            widget
        )

        # Assert
        self.assertTrue(result)
        self.assertEqual(message, "")
        mock_font_instance.text_length.assert_called_with("Test text", 12)

    @patch("fitz.Font")
    async def test_validate_line_length_too_long(self, mock_font):
        # Setup
        mock_font_instance = MagicMock()
        mock_font_instance.text_length.return_value = 150
        mock_font.return_value = mock_font_instance

        widget = MockWidget(
            field_value="Very long text", text_fontsize=12, rect_width=100
        )

        # Execute
        result, message = await TextWidgetValidatorUseAI.validate_line_length(
            widget
        )

        # Assert
        self.assertFalse(result)
        self.assertEqual(message, "Line length is too long")

    async def test_is_caps_lock_on_true(self):
        # Execute
        result, message = await TextWidgetValidatorUseAI.is_caps_lock_on(
            "CAPS LOCK TEXT"
        )

        # Assert
        self.assertTrue(result)
        self.assertEqual(message, "Caps lock is on")

    async def test_is_caps_lock_on_false(self):
        # Execute
        result, message = await TextWidgetValidatorUseAI.is_caps_lock_on(
            "Normal text"
        )

        # Assert
        self.assertFalse(result)
        self.assertEqual(message, "")

    async def test_email_validator_valid(self):
        # Execute
        result, message = await TextWidgetValidatorUseAI.email_validator(
            "test@example.com"
        )

        # Assert
        self.assertTrue(result)
        self.assertEqual(message, "")

    async def test_email_validator_invalid_format(self):
        # Execute
        result, message = await TextWidgetValidatorUseAI.email_validator(
            "invalid-email"
        )

        # Assert
        self.assertFalse(result)
        self.assertIn("is not valid", message)

    async def test_email_validator_uppercase(self):
        # Execute
        result, message = await TextWidgetValidatorUseAI.email_validator(
            "Test@Example.com"
        )

        # Assert
        self.assertFalse(result)
        self.assertEqual(
            message, "All letters in the email address must be lowercase."
        )

    async def test_date_validator_valid_mdy(self):
        # Execute
        result, message = await TextWidgetValidatorUseAI.date_validator(
            "01/21/2015"
        )

        # Assert
        self.assertTrue(result)
        self.assertEqual(message, "")

    async def test_date_validator_valid_bdy(self):
        # Execute
        result, message = await TextWidgetValidatorUseAI.date_validator(
            "January 21, 2015"
        )

        # Assert
        self.assertTrue(result)
        self.assertEqual(message, "")

    async def test_date_validator_invalid(self):
        # Execute
        result, message = await TextWidgetValidatorUseAI.date_validator(
            "21-01-2015"
        )

        # Assert
        self.assertFalse(result)
        self.assertEqual(message, "The date is indicated in the wrong format")

    async def test_phone_number_validator_valid(self):
        # Test cases for valid phone numbers
        valid_formats = [
            "(770) 012-3456",
            "770-012-3456",
            "770 012 3456",
            "7700123456",
        ]

        for phone in valid_formats:
            result, message = (
                await TextWidgetValidatorUseAI.phone_number_validator(phone)
            )
            self.assertTrue(result)
            self.assertEqual(message, "")

    async def test_phone_number_validator_invalid(self):
        # Execute
        result, message = (
            await TextWidgetValidatorUseAI.phone_number_validator("123-456")
        )

        # Assert
        self.assertFalse(result)
        self.assertEqual(message, "Phone number is not valid")

    async def test_address_validator_full_address(self):
        # Execute
        address = "123 Main Street NW Atlanta, GA 30303"
        result, message = await TextWidgetValidatorUseAI.address_validator(
            address
        )

        # Assert
        self.assertTrue(result)
        self.assertEqual(message, "Valid full address")

    async def test_address_validator_street_address(self):
        # Execute
        address = "123 Main Street"
        result, message = await TextWidgetValidatorUseAI.address_validator(
            address
        )

        # Assert
        self.assertTrue(result)
        self.assertEqual(message, "Valid street address")

    async def test_address_validator_city_state_zip(self):
        # Execute
        address = "Atlanta, GA 30303"
        result, message = await TextWidgetValidatorUseAI.address_validator(
            address
        )

        # Assert
        self.assertTrue(result)
        self.assertEqual(message, "Valid city, state, and ZIP")

    async def test_address_validator_missing_street_type(self):
        # Execute
        address = "123 Main Atlanta, GA 30303"
        result, message = await TextWidgetValidatorUseAI.address_validator(
            address
        )

        # Assert
        self.assertFalse(result)
        self.assertEqual(message, "Street type is missing or incorrect")

    async def test_address_validator_missing_state(self):
        # Execute
        address = "123 Main Street, Atlanta 30303"
        result, message = await TextWidgetValidatorUseAI.address_validator(
            address
        )

        # Assert
        self.assertFalse(result)
        self.assertEqual(message, "State abbreviation is missing or incorrect")

    async def test_add_error_to_dict(self):
        # Setup
        self.validator._errors_in_widgets = {}

        # Execute - adding first error
        await self.validator._add_error_to_dict("field1", "Error 1")

        # Assert
        self.assertEqual(
            self.validator._errors_in_widgets, {"field1": "Error 1"}
        )

        # Execute - adding second error to same field
        await self.validator._add_error_to_dict("field1", "Error 2")

        # Assert
        self.assertEqual(
            self.validator._errors_in_widgets, {"field1": "Error 1\nError 2"}
        )

    @patch(
        "src.utils.validators.text_validator.TextWidgetValidatorUseAI._check_widget_data_with_ai"
    )
    async def test_validate_widgets_comprehensive(self, mock_check_with_ai):
        # Setup
        widgets = {
            "fl_email": {
                "value": "Doejane@test.com",
                "widget_instance": MockWidget(field_value="Doejane@test.com"),
            },
            "fl_caps_field": {
                "value": "ALL CAPS TEXT",
                "widget_instance": MockWidget(field_value="ALL CAPS TEXT"),
            },
            "fl_long_field": {
                "value": "This is a very long text that should exceed the widget width",
                "widget_instance": MockWidget(
                    field_value="This is a very long text that should exceed the widget width"
                ),
            },
        }

        # Mock font.text_length to make long field validation fail
        with patch("fitz.Font") as mock_font:
            mock_font_instance = MagicMock()
            # Make long field fail, normal field pass
            mock_font_instance.text_length.side_effect = lambda text, size: (
                150 if len(text) > 30 else 50
            )
            mock_font.return_value = mock_font_instance

            # Mock AI response for address/date/phone detection
            mock_check_with_ai.return_value = {
                "dates": {"fl_long_field": "invalid-date"},
                "addresses": {"fl_caps_field": "123 Invalid Street"},
                "phone_numbers": {},
            }

            # Execute
            result = await self.validator.validate_widgets(widgets)

            # Assert
            self.assertIn("fl_email", result)
            self.assertIn("lowercase", result["fl_email"])

            self.assertIn("fl_caps_field", result)
            self.assertIn("Caps lock is on", result["fl_caps_field"])

            self.assertIn("fl_long_field", result)
            self.assertIn("Line length is too long", result["fl_long_field"])
            self.assertIn("date", result["fl_long_field"].lower())

    @patch(
        "src.utils.validators.text_validator.TextWidgetValidatorUseAI._check_widget_data_with_ai"
    )
    async def test_validate_widgets_real_data(self, mock_check_with_ai):
        # Create widgets dictionary from test data
        widgets = {}
        for field_name, value in self.test_values.items():
            widgets[field_name] = {
                "value": value,
                "widget_instance": MockWidget(field_value=value),
            }

        # Setup mock responses
        mock_check_with_ai.return_value = {
            "dates": {
                "fl_marriage_date": "01/21/2015",
                "birth date of minor child or children": "01/30/2012",
                "birth date of minor child or children 2": "10/30/2015",
                "Terminating month, day, year 2": "October 30th, 2032",
            },
            "addresses": {
                "fl_address_street": "2123 gascon rd Sw",
                "fl_address_city_state_zip": "Palm Bay ,  32908",
                "fl_address_street_spouse": "2123 gascon rd SW",
                "fl_address_city_state_zip_spouse": "Palm Bay,  32908",
            },
            "phone_numbers": {
                "fl_phone_number": "(770) 012-3456",
                "fl_phone_number_spouse": "(770) 123-4567",
            },
        }

        # Mock font.text_length to simulate line length validation
        with patch("fitz.Font") as mock_font:
            mock_font_instance = MagicMock()

            # Make some fields fail the line length check
            def mock_text_length(text, size):
                problematic_fields = [
                    "Other assets Petitioner shall receive",
                    "Other assets Petitioner shall receive 2",
                    "Charge/credit card accounts to be paid by Respondent 2",
                    "Charge/credit card accounts to be paid by Respondent 3",
                ]

                if any(field in text for field in problematic_fields):
                    return 1000  # Make it exceed widget width
                return 50  # Normal width

            mock_font_instance.text_length.side_effect = mock_text_length
            mock_font.return_value = mock_font_instance

            # Execute
            result = await self.validator.validate_widgets(widgets)

            # Assert - check if we got expected errors
            for field, error in self.expected_errors.items():
                if field in result:
                    # For multiline errors, check if each error line is present
                    for error_line in error.split("\n"):
                        self.assertIn(error_line, result[field])

    async def test_check_widget_data_with_ai(self):
        # Setup
        mock_ai = AsyncMock(spec=AIBaseValidator)
        mock_ai.analyze_text.return_value = {
            "dates": {"field1": "01/01/2020"},
            "addresses": {"field2": "123 Main St"},
            "phone_numbers": {"field3": "(123) 456-7890"},
        }

        widgets = {
            "field1": "01/01/2020",
            "field2": "123 Main St",
            "field3": "(123) 456-7890",
        }

        # Execute
        result = await TextWidgetValidatorUseAI._check_widget_data_with_ai(
            widgets=widgets,
            ai_assistant=mock_ai,
            assistant_prompt="test prompt",
        )

        # Assert
        self.assertEqual(len(result), 3)
        self.assertIn("dates", result)
        self.assertIn("addresses", result)
        self.assertIn("phone_numbers", result)
        mock_ai.analyze_text.assert_called_once()

    async def test_check_widget_data_with_ai_empty(self):
        # Setup
        mock_ai = AsyncMock(spec=AIBaseValidator)
        widgets = {}

        # Execute
        result = await TextWidgetValidatorUseAI._check_widget_data_with_ai(
            widgets=widgets,
            ai_assistant=mock_ai,
            assistant_prompt="test prompt",
        )

        # Assert
        self.assertEqual(result, {})
        mock_ai.analyze_text.assert_not_called()
