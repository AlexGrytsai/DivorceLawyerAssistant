import pytest
from google.api_core import exceptions as google_exceptions

from src.domain.document.exceptions import (
    DocumentNotFoundError,
    ValidationError,
    DatabaseOperationError,
    DatabaseConnectionError,
)
from src.infrastructure.persistence.firestore.decorators import (
    handle_firestore_database_errors_sync,
    handle_firestore_database_errors_async,
)


# Test fixtures for synchronous functions
@pytest.fixture
def sync_success_func():
    @handle_firestore_database_errors_sync
    def test_func():
        return "success"

    return test_func


@pytest.fixture
def sync_not_found_func():
    @handle_firestore_database_errors_sync
    def test_func():
        raise google_exceptions.NotFound("Document not found")

    return test_func


@pytest.fixture
def sync_validation_error_func():
    @handle_firestore_database_errors_sync
    def test_func():
        raise ValueError("Invalid data")

    return test_func


@pytest.fixture
def sync_database_error_func():
    @handle_firestore_database_errors_sync
    def test_func():
        raise google_exceptions.GoogleAPIError("Operation failed")

    return test_func


# Test fixtures for asynchronous functions
@pytest.fixture
def async_success_func():
    @handle_firestore_database_errors_async
    async def test_func():
        return "success"

    return test_func


@pytest.fixture
def async_not_found_func():
    @handle_firestore_database_errors_async
    async def test_func():
        raise google_exceptions.NotFound("Document not found")

    return test_func


@pytest.fixture
def async_validation_error_func():
    @handle_firestore_database_errors_async
    async def test_func():
        raise ValueError("Invalid data")

    return test_func


@pytest.fixture
def async_database_error_func():
    @handle_firestore_database_errors_async
    async def test_func():
        raise google_exceptions.GoogleAPIError("Operation failed")

    return test_func


# Tests for synchronous functions
def test_sync_success(sync_success_func):
    result = sync_success_func()
    assert result == "success"


def test_sync_not_found(sync_not_found_func):
    with pytest.raises(DocumentNotFoundError) as exc_info:
        sync_not_found_func()
    assert "Document not found" in str(exc_info.value)


def test_sync_validation_error(sync_validation_error_func):
    with pytest.raises(ValidationError) as exc_info:
        sync_validation_error_func()
    assert "Validation failed" in str(exc_info.value)


def test_sync_database_error(sync_database_error_func):
    with pytest.raises(DatabaseOperationError) as exc_info:
        sync_database_error_func()
    assert "Operation failed" in str(exc_info.value)


# Tests for asynchronous functions
@pytest.mark.asyncio
async def test_async_success(async_success_func):
    result = await async_success_func()
    assert result == "success"


@pytest.mark.asyncio
async def test_async_not_found(async_not_found_func):
    with pytest.raises(DocumentNotFoundError) as exc_info:
        await async_not_found_func()
    assert "Document not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_async_validation_error(async_validation_error_func):
    with pytest.raises(ValidationError) as exc_info:
        await async_validation_error_func()
    assert "Validation failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_async_database_error(async_database_error_func):
    with pytest.raises(DatabaseOperationError) as exc_info:
        await async_database_error_func()
    assert "Operation failed" in str(exc_info.value)


# Edge cases tests
def test_preserves_function_signature():
    @handle_firestore_database_errors_sync
    def test_func(a: int, b: str) -> bool:
        return True

    assert test_func.__name__ == "test_func"
    assert test_func.__annotations__ == {"a": int, "b": str, "return": bool}


def test_unexpected_error():
    @handle_firestore_database_errors_sync
    def test_func():
        raise RuntimeError("Unexpected error")

    with pytest.raises(DatabaseConnectionError) as exc_info:
        test_func()
    assert "Unexpected error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_async_unexpected_error():
    @handle_firestore_database_errors_async
    async def test_func():
        raise RuntimeError("Unexpected error")

    with pytest.raises(DatabaseConnectionError) as exc_info:
        await test_func()
    assert "Unexpected error" in str(exc_info.value)


def test_nested_exceptions():
    @handle_firestore_database_errors_sync
    def test_func():
        try:
            raise ValueError("Inner error")
        except ValueError:
            raise google_exceptions.GoogleAPIError("Outer error")

    with pytest.raises(DatabaseOperationError) as exc_info:
        test_func()
    assert "Outer error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_async_nested_exceptions():
    @handle_firestore_database_errors_async
    async def test_func():
        try:
            raise ValueError("Inner error")
        except ValueError:
            raise google_exceptions.GoogleAPIError("Outer error")

    with pytest.raises(DatabaseOperationError) as exc_info:
        await test_func()
    assert "Outer error" in str(exc_info.value)
