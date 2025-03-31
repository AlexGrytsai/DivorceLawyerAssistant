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
        "src.utils.validators.text_validator.TextWidgetValidatorUseAI._check_widget_data_with_ai"  # noqa
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
                "value": "This is a very long text that should exceed the widget width",  # noqa
                "widget_instance": MockWidget(
                    field_value=(
                        "This is a very long text that should exceed "
                        "the widget width"
                    )
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
        "src.utils.validators.text_validator.TextWidgetValidatorUseAI._check_widget_data_with_ai"  # noqa
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

                return 1000 if any(
                    field in text for field in problematic_fields
                ) else 50

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

    @patch(
        "src.utils.validators.text_validator.TextWidgetValidatorUseAI._check_widget_data_with_ai"  # noqa
    )
    async def test_validate_widgets_empty_values(self, mock_check_with_ai):
        # Setup
        mock_check_with_ai.return_value = {}
        widgets = {
            "field1": {"value": "", "widget_instance": MockWidget()},
            "field2": {"value": None, "widget_instance": MockWidget()},
        }

        # Execute
        result = await self.validator.validate_widgets(widgets)

        # Assert
        self.assertEqual(result, {})
        mock_check_with_ai.assert_called_once()

    @patch(
        "src.utils.validators.text_validator.TextWidgetValidatorUseAI._check_widget_data_with_ai"  # noqa
    )
    async def test_validate_widgets_ai_error(self, mock_check_with_ai):
        # Setup
        mock_check_with_ai.side_effect = Exception("AI Service Error")
        widgets = {
            "field1": {"value": "test", "widget_instance": MockWidget()}
        }

        # Execute
        result = await self.validator.validate_widgets(widgets)

        # Assert
        self.assertEqual(result, {})
        mock_check_with_ai.assert_called_once()

    @patch(
        "src.utils.validators.text_validator.TextWidgetValidatorUseAI._check_widget_data_with_ai"  # noqa
    )
    async def test_validate_widgets_multiple_errors(self, mock_check_with_ai):
        # Setup
        mock_check_with_ai.return_value = {
            "dates": {"date_field": "invalid_date"},
            "addresses": {"address_field": "invalid_address"},
            "phone_numbers": {"phone_field": "invalid_phone"},
        }
        widgets = {
            "email_field": {
                "value": "TEST@EXAMPLE.COM",
                "widget_instance": MockWidget(),
            },
            "date_field": {
                "value": "invalid_date",
                "widget_instance": MockWidget(),
            },
            "address_field": {
                "value": "invalid_address",
                "widget_instance": MockWidget(),
            },
            "phone_field": {
                "value": "invalid_phone",
                "widget_instance": MockWidget(),
            },
        }

        # Execute
        result = await self.validator.validate_widgets(widgets)

        # Assert
        self.assertIn("email_field", result)
        self.assertIn("date_field", result)
        self.assertIn("address_field", result)
        self.assertIn("phone_field", result)

    async def test_check_widget_data_with_ai_error_handling(self):
        # Setup
        widgets = {"field1": "value1"}
        self.ai_assistant.analyze_text.side_effect = Exception(
            "AI Service Error"
        )

        # Execute
        result = await TextWidgetValidatorUseAI._check_widget_data_with_ai(
            widgets=widgets,
            ai_assistant=self.ai_assistant,
            assistant_prompt="test prompt",
        )

        # Assert
        self.assertEqual(result, {})
        self.ai_assistant.analyze_text.assert_called_once()

    async def test_check_widget_data_with_ai_invalid_response(self):
        # Setup
        widgets = {"field1": "value1"}
        self.ai_assistant.analyze_text.return_value = "invalid_json"

        # Execute
        result = await TextWidgetValidatorUseAI._check_widget_data_with_ai(
            widgets=widgets,
            ai_assistant=self.ai_assistant,
            assistant_prompt="test prompt",
        )

        # Assert
        self.assertEqual(result, {})
        self.ai_assistant.analyze_text.assert_called_once()

    async def test_add_error_to_dict_multiple_errors(self):
        # Setup
        self.validator._errors_in_widgets = {}

        # Execute - adding multiple errors
        await self.validator._add_error_to_dict("field1", "Error 1")
        await self.validator._add_error_to_dict("field1", "Error 2")

        # Assert
        self.assertEqual(
            self.validator._errors_in_widgets, {"field1": "Error 1\nError 2"}
        )

    async def test_email_validator_special_characters(self):
        # Test cases for email with special characters
        test_cases = [
            ("test+label@example.com", True, ""),
            ("test.label@example.com", True, ""),
            ("test-label@example.com", True, ""),
            ("test@example.co.uk", True, ""),
            ("test@sub.example.com", True, ""),
            ("test@example.com.", False, "The email address is not valid"),
            ("test@.example.com", False, "The email address is not valid"),
            ("test@example..com", False, "The email address is not valid"),
        ]

        for email, expected_valid, expected_message in test_cases:
            result, message = await TextWidgetValidatorUseAI.email_validator(
                email
            )
            self.assertEqual(result, expected_valid)
            if not expected_valid:
                self.assertIn(expected_message, message)

    async def test_date_validator_edge_cases(self):
        # Test cases for date validation edge cases
        test_cases = [
            ("01/01/2000", True, ""),
            ("12/31/9999", True, ""),
            ("00/00/0000", False, "The date is indicated in the wrong format"),
            ("13/01/2020", False, "The date is indicated in the wrong format"),
            ("01/32/2020", False, "The date is indicated in the wrong format"),
            ("January 1, 2020", True, ""),
            ("December 31, 9999", True, ""),
            (
                "Invalid Month 1, 2020",
                False,
                "The date is indicated in the wrong format",
            ),
            (
                "January 32, 2020",
                False,
                "The date is indicated in the wrong format",
            ),
        ]

        for date_str, expected_valid, expected_message in test_cases:
            result, message = await TextWidgetValidatorUseAI.date_validator(
                date_str
            )
            self.assertEqual(result, expected_valid)
            if not expected_valid:
                self.assertEqual(message, expected_message)

    async def test_phone_number_validator_edge_cases(self):
        # Test cases for phone number validation edge cases
        test_cases = [
            ("123-456-7890", True, ""),
            ("(123) 456-7890", True, ""),
            ("123.456.7890", True, ""),
            ("123 456 7890", True, ""),
            ("1234567890", True, ""),
            ("123-456", False, "Phone number is not valid"),
            ("123456", False, "Phone number is not valid"),
            ("(123) 456", False, "Phone number is not valid"),
            ("123-456-789", False, "Phone number is not valid"),
            ("123-456-78901", False, "Phone number is not valid"),
        ]

        for phone, expected_valid, expected_message in test_cases:
            result, message = (
                await TextWidgetValidatorUseAI.phone_number_validator(phone)
            )
            self.assertEqual(result, expected_valid)
            if not expected_valid:
                self.assertEqual(message, expected_message)

    async def test_address_validator_edge_cases(self):
        # Test cases for address validation edge cases
        test_cases = [
            (
                "123 Main Street NW Atlanta, GA 30303",
                True,
                "Valid full address",
            ),
            ("123 Main Street NW", True, "Valid street address"),
            ("Atlanta, GA 30303", True, "Valid city, state, and ZIP"),
            (
                "123 Main Street NW Atlanta, GA 30303-1234",
                True,
                "Valid full address",
            ),
            (
                "123 Main Street NW Atlanta, GA 30303-12345",
                False,
                "ZIP code is missing or incorrect",
            ),
            (
                "123 Main Street NW Atlanta, GA 303",
                False,
                "ZIP code is missing or incorrect",
            ),
            (
                "123 Main Street NW Atlanta, XX 30303",
                False,
                "State abbreviation is missing or incorrect",
            ),
            (
                "123 Main Atlanta, GA 30303",
                False,
                "Street type is missing or incorrect",
            ),
            (
                "123 Main Street NW Atlanta, GA",
                False,
                "ZIP code is missing or incorrect",
            ),
            (
                "123 Main Street NW, GA 30303",
                False,
                "City, state, and ZIP format is incorrect",
            ),
        ]

        for address, expected_valid, expected_message in test_cases:
            result, message = await TextWidgetValidatorUseAI.address_validator(
                address
            )
            self.assertEqual(result, expected_valid)
            self.assertEqual(message, expected_message)

    @patch("fitz.Font")
    async def test_validate_line_length_edge_cases(self, mock_font):
        # Setup
        mock_font_instance = MagicMock()
        mock_font.return_value = mock_font_instance

        test_cases = [
            ("", 10, 100, True, ""),  # Empty string
            ("a", 10, 100, True, ""),  # Single character
            ("a" * 100, 10, 100, True, ""),  # Exact width
            (
                "a" * 101,
                10,
                100,
                False,
                "Line length is too long",
            ),  # One character too long
            (
                "a" * 1000,
                10,
                100,
                False,
                "Line length is too long",
            ),  # Very long string
        ]

        for (
            text,
            font_size,
            width,
            expected_valid,
            expected_message,
        ) in test_cases:
            mock_font_instance.text_length.return_value = len(text) * font_size
            widget = MockWidget(
                field_value=text, text_fontsize=font_size, rect_width=width
            )

            result, message = (
                await TextWidgetValidatorUseAI.validate_line_length(widget)
            )
            self.assertEqual(result, expected_valid)
            self.assertEqual(message, expected_message)

    async def test_validate_widgets_empty_dict(self):
        # Test validation with empty dictionary
        result = await self.validator.validate_widgets({})
        self.assertEqual(result, {})

    async def test_validate_widgets_invalid_dict_structure(self):
        # Test validation with invalid dictionary structure
        widgets = {
            "field1": {"invalid_key": "value"},
            "field2": {"value": "test", "widget_instance": None},
            "field3": {"value": None, "widget_instance": MockWidget()},
        }
        result = await self.validator.validate_widgets(widgets)
        self.assertEqual(result, {})
