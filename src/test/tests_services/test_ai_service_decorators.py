import unittest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException, status
from openai import (
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    RateLimitError,
)
from src.services.ai_service.decorators import reconnection_async


class TestReconnectionAsync(unittest.TestCase):
    def setUp(self):
        # Create a mock async function that we'll decorate
        self.mock_func = AsyncMock()

    async def test_successful_execution(self):
        """Test successful execution without any retries"""
        self.mock_func.return_value = "success"

        decorated_func = reconnection_async(attempts=3)(self.mock_func)
        result = await decorated_func()

        self.assertEqual(result, "success")
        self.mock_func.assert_called_once()

    async def test_timeout_retry_success(self):
        """Test successful execution after timeout retry"""
        self.mock_func.side_effect = [APITimeoutError("Timeout"), "success"]

        decorated_func = reconnection_async(attempts=3)(self.mock_func)
        result = await decorated_func()

        self.assertEqual(result, "success")
        self.assertEqual(self.mock_func.call_count, 2)

    async def test_max_attempts_exceeded(self):
        """Test when maximum attempts are exceeded"""
        self.mock_func.side_effect = APITimeoutError("Timeout")

        decorated_func = reconnection_async(attempts=2)(self.mock_func)

        with self.assertRaises(HTTPException) as context:
            await decorated_func()

        self.assertEqual(
            context.exception.status_code, status.HTTP_408_REQUEST_TIMEOUT
        )
        self.assertEqual(self.mock_func.call_count, 2)

    async def test_authentication_error(self):
        """Test handling of authentication error"""
        self.mock_func.side_effect = AuthenticationError("Invalid API key")

        decorated_func = reconnection_async(attempts=3)(self.mock_func)

        with self.assertRaises(HTTPException) as context:
            await decorated_func()

        self.assertEqual(
            context.exception.status_code, status.HTTP_503_SERVICE_UNAVAILABLE
        )
        self.mock_func.assert_called_once()

    async def test_internal_server_error(self):
        """Test handling of internal server error"""
        self.mock_func.side_effect = InternalServerError("Server error")

        decorated_func = reconnection_async(attempts=3)(self.mock_func)

        with self.assertRaises(HTTPException) as context:
            await decorated_func()

        self.assertEqual(
            context.exception.status_code, status.HTTP_503_SERVICE_UNAVAILABLE
        )
        self.mock_func.assert_called_once()

    async def test_rate_limit_error(self):
        """Test handling of rate limit error"""
        self.mock_func.side_effect = RateLimitError("Rate limit exceeded")

        decorated_func = reconnection_async(attempts=3)(self.mock_func)

        with self.assertRaises(HTTPException) as context:
            await decorated_func()

        self.assertEqual(
            context.exception.status_code, status.HTTP_503_SERVICE_UNAVAILABLE
        )
        self.mock_func.assert_called_once()

    async def test_http_exception_propagation(self):
        """Test that HTTP exceptions are propagated"""
        self.mock_func.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request"
        )

        decorated_func = reconnection_async(attempts=3)(self.mock_func)

        with self.assertRaises(HTTPException) as context:
            await decorated_func()

        self.assertEqual(
            context.exception.status_code, status.HTTP_400_BAD_REQUEST
        )
        self.mock_func.assert_called_once()

    async def test_custom_attempts(self):
        """Test with custom number of attempts"""
        self.mock_func.side_effect = [
            APITimeoutError("Timeout"),
            APITimeoutError("Timeout"),
            "success",
        ]

        decorated_func = reconnection_async(attempts=5)(self.mock_func)
        result = await decorated_func()

        self.assertEqual(result, "success")
        self.assertEqual(self.mock_func.call_count, 3)
