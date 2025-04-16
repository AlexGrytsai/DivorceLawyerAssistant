import pytest
from google.api_core.exceptions import ClientError, NotFound
from google.auth.exceptions import GoogleAuthError

from src.domain.storage.exceptions import (
    ErrorUploadingFile,
    ErrorDeletingFile,
    ErrorWithAuthenticationInGCP,
    ProblemWithRequestToGCP,
    FileNotFound,
    UnexpectedError,
)
from src.infrastructure.storage.cloud.google_cloud.decorators import (
    handle_google_storage_exceptions,
    async_handle_google_storage_exceptions,
)
from src.infrastructure.storage.decorators import (
    handle_upload_file_exceptions,
    handle_delete_file_exceptions,
)


class TestHandleUploadFileExceptions:
    @pytest.mark.asyncio
    async def test_successful_upload(self):
        @handle_upload_file_exceptions
        async def mock_upload():
            return "success"

        result = await mock_upload()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_upload_with_error(self):
        @handle_upload_file_exceptions
        async def mock_upload():
            raise ErrorUploadingFile("Test error")

        with pytest.raises(ErrorUploadingFile) as exc_info:
            await mock_upload()

        assert "Test error" in str(exc_info.value)


class TestHandleDeleteFileExceptions:
    @pytest.mark.asyncio
    async def test_successful_delete(self):
        @handle_delete_file_exceptions
        async def mock_delete(file_path="test.txt"):
            return "success"

        result = await mock_delete()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_delete_with_error(self):
        @handle_delete_file_exceptions
        async def mock_delete(file_path="test.txt"):
            raise ErrorDeletingFile("Test error")

        with pytest.raises(ErrorDeletingFile) as exc_info:
            await mock_delete(file_path="test.txt")

        assert "test.txt" in str(exc_info.value)


class TestHandleCloudStorageExceptions:
    def test_successful_operation(self):
        @handle_google_storage_exceptions
        def mock_operation():
            return "success"

        result = mock_operation()
        assert result == "success"

    def test_google_auth_error(self):
        @handle_google_storage_exceptions
        def mock_operation():
            raise GoogleAuthError("Auth error")

        with pytest.raises(ErrorWithAuthenticationInGCP) as exc_info:
            mock_operation()

        assert "Auth error" in str(exc_info.value)

    def test_client_error(self):
        @handle_google_storage_exceptions
        def mock_operation():
            raise ClientError("Client error")

        with pytest.raises(ProblemWithRequestToGCP) as exc_info:
            mock_operation()

        assert "Client error" in str(exc_info.value)

    def test_unexpected_error(self):
        @handle_google_storage_exceptions
        def mock_operation():
            raise Exception("Unexpected error")

        with pytest.raises(UnexpectedError) as exc_info:
            mock_operation()

        assert "Unexpected error" in str(exc_info.value)


class TestAsyncHandleCloudStorageExceptions:
    @pytest.mark.asyncio
    async def test_successful_operation(self):
        @async_handle_google_storage_exceptions
        async def mock_operation():
            return "success"

        result = await mock_operation()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_google_auth_error(self):
        @async_handle_google_storage_exceptions
        async def mock_operation():
            raise GoogleAuthError("Auth error")

        with pytest.raises(ErrorWithAuthenticationInGCP) as exc_info:
            await mock_operation()

        assert "Auth error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_not_found_error(self):
        @async_handle_google_storage_exceptions
        async def mock_operation():
            raise NotFound("Not found")

        with pytest.raises(FileNotFound) as exc_info:
            await mock_operation()

        assert "Not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_client_error(self):
        @async_handle_google_storage_exceptions
        async def mock_operation():
            raise ClientError("Client error")

        with pytest.raises(ProblemWithRequestToGCP) as exc_info:
            await mock_operation()

        assert "Client error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_unexpected_error(self):
        @async_handle_google_storage_exceptions
        async def mock_operation():
            raise Exception("Unexpected error")

        with pytest.raises(UnexpectedError) as exc_info:
            await mock_operation()

        assert "Unexpected error" in str(exc_info.value)
