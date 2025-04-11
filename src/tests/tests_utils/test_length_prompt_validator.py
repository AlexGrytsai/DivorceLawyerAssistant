import unittest
from unittest.mock import patch

from src.utils.validators.length_prompt_validator import (
    is_length_prompt_valid,
    get_length_prompt,
)


class TestLengthPromptValidator(unittest.TestCase):
    @patch("src.utils.validators.length_prompt_validator.settings")
    @patch("tiktoken.encoding_for_model")
    def test_is_length_prompt_valid_within_limit(
        self, mock_encoding, mock_settings
    ):
        # Configure mock to return token length within limit
        mock_settings.get_token_limit = 10
        mock_settings.BASE_AI_MODEL = "test-model"
        mock_encode = mock_encoding.return_value.encode
        mock_encode.return_value = [1, 2, 3]  # 3 tokens < 10 limit

        self.assertTrue(is_length_prompt_valid("short prompt"))
        mock_encoding.assert_called_once_with("test-model")

    @patch("src.utils.validators.length_prompt_validator.settings")
    @patch("tiktoken.encoding_for_model")
    def test_is_length_prompt_valid_exceeds_limit(
        self, mock_encoding, mock_settings
    ):
        # Configure mock to return token length exceeding limit
        mock_settings.get_token_limit = 10
        mock_settings.BASE_AI_MODEL = "test-model"
        mock_encode = mock_encoding.return_value.encode
        mock_encode.return_value = list(range(15))  # 15 tokens > 10 limit

        self.assertFalse(is_length_prompt_valid("long prompt"))
        mock_encoding.assert_called_once_with("test-model")

    @patch("src.utils.validators.length_prompt_validator.settings")
    @patch("tiktoken.encoding_for_model")
    def test_is_length_prompt_valid_zero_limit(
        self, mock_encoding, mock_settings
    ):
        # Edge case: zero token limit
        mock_settings.get_token_limit = 0
        mock_settings.BASE_AI_MODEL = "test-model"
        mock_encode = mock_encoding.return_value.encode
        mock_encode.return_value = [1]  # 1 token > 0 limit

        self.assertFalse(is_length_prompt_valid("any prompt"))
        mock_encoding.assert_not_called()

    @patch("src.utils.validators.length_prompt_validator.settings")
    @patch("tiktoken.encoding_for_model")
    def test_get_length_prompt(self, mock_encoding, mock_settings):
        # Test length calculation function
        mock_settings.BASE_AI_MODEL = "test-model"
        mock_encode = mock_encoding.return_value.encode
        mock_encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens

        self.assertEqual(get_length_prompt("test prompt"), 5)
        mock_encoding.assert_called_once_with("test-model")

    @patch("src.utils.validators.length_prompt_validator.settings")
    @patch("tiktoken.encoding_for_model")
    def test_get_length_prompt_empty_string(
        self, mock_encoding, mock_settings
    ):
        # Edge case: empty string
        mock_settings.BASE_AI_MODEL = "test-model"
        mock_encode = mock_encoding.return_value.encode
        mock_encode.return_value = []  # 0 tokens

        self.assertEqual(get_length_prompt(""), 0)
        mock_encoding.assert_called_once_with("test-model")
