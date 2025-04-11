from unittest.mock import Mock, patch, AsyncMock

import pytest
from fastapi import HTTPException, status
from pinecone import PineconeException

from src.services.rag_service.decorators import (
    handle_pinecone_exceptions,
    handle_async_exceptions,
    handle_async_document_exceptions,
    handle_document_processing,
    handle_async_search_exceptions,
    handle_pinecone_init_exceptions,
    handle_index_stats_exceptions,
    handle_list_operation_exceptions,
    handle_dict_operation_exceptions,
    handle_boolean_operation_exceptions,
    handle_index_operation_exceptions,
    handle_namespace_operation_exceptions,
    handle_folder_operation_exceptions,
)

# Common test data
TEST_RESULT = "success"
TEST_ARGS = (1, "arg2")
TEST_KWARGS = {"key": "value"}
PINECONE_ERROR_MESSAGE = "Pinecone test error"
GENERAL_ERROR_MESSAGE = "General test error"


# --- Test handle_pinecone_exceptions ---


@patch("src.services.rag_service.decorators.logger")
def test_handle_pinecone_exceptions_success(mock_logger):
    mock_func = Mock(return_value=TEST_RESULT)
    decorated_func = handle_pinecone_exceptions()(mock_func)

    result = decorated_func(*TEST_ARGS, **TEST_KWARGS)

    assert result == TEST_RESULT
    mock_func.assert_called_once_with(*TEST_ARGS, **TEST_KWARGS)
    mock_logger.error.assert_not_called()


@patch("src.services.rag_service.decorators.logger")
def test_handle_pinecone_exceptions_pinecone_exception(mock_logger):
    mock_func = Mock(side_effect=PineconeException(PINECONE_ERROR_MESSAGE))
    mock_func.__name__ = "test_pinecone_op"
    decorated_func = handle_pinecone_exceptions()(mock_func)

    with pytest.raises(HTTPException) as exc_info:
        decorated_func(*TEST_ARGS, **TEST_KWARGS)

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "Error with Pinecone operation" in exc_info.value.detail["error"]
    assert mock_func.__name__ in exc_info.value.detail["message"]
    assert PINECONE_ERROR_MESSAGE in exc_info.value.detail["message"]
    mock_logger.error.assert_called_once()
    assert mock_func.__name__ in mock_logger.error.call_args[0][0]
    assert PINECONE_ERROR_MESSAGE in mock_logger.error.call_args[0][0]


@patch("src.services.rag_service.decorators.logger")
def test_handle_pinecone_exceptions_general_exception(mock_logger):
    mock_func = Mock(side_effect=Exception(GENERAL_ERROR_MESSAGE))
    mock_func.__name__ = "test_general_op"
    decorated_func = handle_pinecone_exceptions()(mock_func)

    with pytest.raises(HTTPException) as exc_info:
        decorated_func(*TEST_ARGS, **TEST_KWARGS)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert (
        "Unexpected error in Pinecone operation"
        in exc_info.value.detail["error"]
    )
    assert mock_func.__name__ in exc_info.value.detail["message"]
    assert GENERAL_ERROR_MESSAGE in exc_info.value.detail["message"]
    mock_logger.error.assert_called_once()
    assert mock_func.__name__ in mock_logger.error.call_args[0][0]
    assert GENERAL_ERROR_MESSAGE in mock_logger.error.call_args[0][0]


# --- Test handle_async_exceptions ---


@pytest.mark.asyncio
async def test_handle_async_exceptions_success():
    mock_async_func = AsyncMock(return_value=TEST_RESULT)
    operation_type = "test_async_op"

    result = await handle_async_exceptions(
        mock_async_func, TEST_ARGS, TEST_KWARGS, operation_type
    )

    assert result == TEST_RESULT
    mock_async_func.assert_awaited_once_with(*TEST_ARGS, **TEST_KWARGS)


@pytest.mark.asyncio
@patch("src.services.rag_service.decorators.logger")
async def test_handle_async_exceptions_failure(mock_logger):
    mock_async_func = AsyncMock(side_effect=Exception(GENERAL_ERROR_MESSAGE))
    mock_async_func.__name__ = "failed_async_op"
    operation_type = "test_async_op_fail"

    with pytest.raises(HTTPException) as exc_info:
        await handle_async_exceptions(
            mock_async_func, TEST_ARGS, TEST_KWARGS, operation_type
        )

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert f"Error in {operation_type}" == exc_info.value.detail["error"]
    assert mock_async_func.__name__ in exc_info.value.detail["message"]
    assert GENERAL_ERROR_MESSAGE in exc_info.value.detail["message"]
    mock_logger.error.assert_called_once()
    assert operation_type in mock_logger.error.call_args[0][0]
    assert mock_async_func.__name__ in mock_logger.error.call_args[0][0]
    assert GENERAL_ERROR_MESSAGE in mock_logger.error.call_args[0][0]


# --- Test handle_async_document_exceptions & handle_document_processing ---

TEST_FILE_PATH = "/path/to/document.pdf"


@pytest.mark.asyncio
async def test_handle_async_document_exceptions_success():
    mock_async_func = AsyncMock(return_value=None)
    operation_type = "doc_processing"

    result = await handle_async_document_exceptions(
        mock_async_func, (), {"file_path": TEST_FILE_PATH}, operation_type
    )

    assert result is None
    mock_async_func.assert_awaited_once_with(file_path=TEST_FILE_PATH)


@pytest.mark.asyncio
@patch("src.services.rag_service.decorators.logger")
async def test_handle_async_document_exceptions_failure_with_kwargs(
    mock_logger,
):
    mock_async_func = AsyncMock(side_effect=Exception(GENERAL_ERROR_MESSAGE))
    mock_async_func.__name__ = "failed_doc_op_kwargs"
    operation_type = "doc_processing_fail_kwargs"

    with pytest.raises(HTTPException) as exc_info:
        await handle_async_document_exceptions(
            mock_async_func,
            (),
            {"file_path": TEST_FILE_PATH},
            operation_type,
        )

    assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Error processing document" == exc_info.value.detail["error"]
    assert mock_async_func.__name__ in exc_info.value.detail["message"]
    assert GENERAL_ERROR_MESSAGE in exc_info.value.detail["message"]
    assert exc_info.value.detail["file_path"] == TEST_FILE_PATH
    mock_logger.error.assert_called_once()
    assert operation_type in mock_logger.error.call_args[0][0]
    assert mock_async_func.__name__ in mock_logger.error.call_args[0][0]
    assert GENERAL_ERROR_MESSAGE in mock_logger.error.call_args[0][0]


@pytest.mark.asyncio
@patch("src.services.rag_service.decorators.logger")
async def test_handle_async_document_exceptions_failure_with_args(mock_logger):
    mock_async_func = AsyncMock(side_effect=Exception(GENERAL_ERROR_MESSAGE))
    mock_async_func.__name__ = "failed_doc_op_args"
    operation_type = "doc_processing_fail_args"
    args_with_path = (
        None,
        TEST_FILE_PATH,
    )  # Assuming file_path is the second arg

    with pytest.raises(HTTPException) as exc_info:
        await handle_async_document_exceptions(
            mock_async_func, args_with_path, {}, operation_type
        )

    assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Error processing document" == exc_info.value.detail["error"]
    assert mock_async_func.__name__ in exc_info.value.detail["message"]
    assert GENERAL_ERROR_MESSAGE in exc_info.value.detail["message"]
    assert exc_info.value.detail["file_path"] == TEST_FILE_PATH
    mock_logger.error.assert_called_once()


@pytest.mark.asyncio
@patch("src.services.rag_service.decorators.logger")
async def test_handle_async_document_exceptions_failure_no_path(mock_logger):
    mock_async_func = AsyncMock(side_effect=Exception(GENERAL_ERROR_MESSAGE))
    mock_async_func.__name__ = "failed_doc_op_no_path"
    operation_type = "doc_processing_fail_no_path"

    with pytest.raises(HTTPException) as exc_info:
        await handle_async_document_exceptions(
            mock_async_func, (), {}, operation_type
        )

    assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Error processing document" == exc_info.value.detail["error"]
    assert exc_info.value.detail["file_path"] == ""  # Should be empty
    mock_logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_handle_document_processing_decorator_success():
    mock_async_func = AsyncMock(return_value=None)
    decorated_func = handle_document_processing(mock_async_func)

    await decorated_func(file_path=TEST_FILE_PATH)
    mock_async_func.assert_awaited_once_with(file_path=TEST_FILE_PATH)


@pytest.mark.asyncio
@patch("src.services.rag_service.decorators.logger")
async def test_handle_document_processing_decorator_failure(mock_logger):
    mock_async_func = AsyncMock(side_effect=Exception(GENERAL_ERROR_MESSAGE))
    mock_async_func.__name__ = "failed_doc_processing_decorated"
    decorated_func = handle_document_processing(mock_async_func)

    with pytest.raises(HTTPException) as exc_info:
        await decorated_func(file_path=TEST_FILE_PATH)

    assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Error processing document" == exc_info.value.detail["error"]
    assert exc_info.value.detail["file_path"] == TEST_FILE_PATH
    mock_logger.error.assert_called_once()
    assert (
        "document processing" in mock_logger.error.call_args[0][0]
    )  # Checks operation_type
    assert mock_async_func.__name__ in mock_logger.error.call_args[0][0]


# --- Test handle_async_search_exceptions ---


@pytest.mark.asyncio
async def test_handle_async_search_exceptions_success():
    mock_async_func = AsyncMock(return_value=TEST_RESULT)
    decorated_func = handle_async_search_exceptions(mock_async_func)

    result = await decorated_func(*TEST_ARGS, **TEST_KWARGS)

    assert result == TEST_RESULT
    mock_async_func.assert_awaited_once_with(*TEST_ARGS, **TEST_KWARGS)


@pytest.mark.asyncio
@patch("src.services.rag_service.decorators.logger")
async def test_handle_async_search_exceptions_failure(mock_logger):
    mock_async_func = AsyncMock(side_effect=Exception(GENERAL_ERROR_MESSAGE))
    mock_async_func.__name__ = "failed_search_op"
    decorated_func = handle_async_search_exceptions(mock_async_func)

    with pytest.raises(HTTPException) as exc_info:
        await decorated_func(*TEST_ARGS, **TEST_KWARGS)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert (
        "Error in search" == exc_info.value.detail["error"]
    )  # Checks operation_type
    assert mock_async_func.__name__ in exc_info.value.detail["message"]
    assert GENERAL_ERROR_MESSAGE in exc_info.value.detail["message"]
    mock_logger.error.assert_called_once()
    assert "search operation" in mock_logger.error.call_args[0][0]
    assert mock_async_func.__name__ in mock_logger.error.call_args[0][0]


# --- Test handle_pinecone_init_exceptions ---


def test_handle_pinecone_init_exceptions_success():
    mock_func = Mock(return_value=TEST_RESULT)
    decorated_func = handle_pinecone_init_exceptions(mock_func)

    result = decorated_func(*TEST_ARGS, **TEST_KWARGS)

    assert result == TEST_RESULT
    mock_func.assert_called_once_with(*TEST_ARGS, **TEST_KWARGS)


@patch("src.services.rag_service.decorators.logger")
def test_handle_pinecone_init_exceptions_failure(mock_logger):
    mock_func = Mock(side_effect=Exception(GENERAL_ERROR_MESSAGE))
    mock_func.__name__ = "failed_init"
    decorated_func = handle_pinecone_init_exceptions(mock_func)

    with pytest.raises(HTTPException) as exc_info:
        decorated_func(*TEST_ARGS, **TEST_KWARGS)

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert (
        "Error with Pinecone client initialization"
        == exc_info.value.detail["error"]
    )
    assert GENERAL_ERROR_MESSAGE in exc_info.value.detail["message"]
    mock_logger.error.assert_called_once()
    assert (
        "Error initializing Pinecone client"
        in mock_logger.error.call_args[0][0]
    )
    assert GENERAL_ERROR_MESSAGE in mock_logger.error.call_args[0][0]


# --- Test handle_index_stats_exceptions ---


@patch("src.services.rag_service.decorators.logger")
def test_handle_index_stats_exceptions_calls_handle_pinecone(mock_logger):
    mock_func = Mock(side_effect=PineconeException(PINECONE_ERROR_MESSAGE))
    mock_func.__name__ = "stats_op"
    decorated_func = handle_index_stats_exceptions(mock_func)

    with pytest.raises(HTTPException) as exc_info:
        decorated_func()

    # Verify it behaves like handle_pinecone_exceptions
    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "Error with Pinecone operation" in exc_info.value.detail["error"]
    assert mock_func.__name__ in exc_info.value.detail["message"]
    mock_logger.error.assert_called_once()


# --- Test handle_list_operation_exceptions ---


@patch("src.services.rag_service.decorators.logger")
def test_handle_list_operation_exceptions_calls_handle_pinecone(mock_logger):
    mock_func = Mock(side_effect=Exception(GENERAL_ERROR_MESSAGE))
    mock_func.__name__ = "list_op"
    decorated_func = handle_list_operation_exceptions(mock_func)

    with pytest.raises(HTTPException) as exc_info:
        decorated_func()

    # Verify it behaves like handle_pinecone_exceptions
    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert (
        "Unexpected error in Pinecone operation"
        in exc_info.value.detail["error"]
    )
    assert mock_func.__name__ in exc_info.value.detail["message"]
    mock_logger.error.assert_called_once()


# --- Test handle_dict_operation_exceptions --- (Similar check) ---


@patch("src.services.rag_service.decorators.logger")
def test_handle_dict_operation_exceptions_calls_handle_pinecone(mock_logger):
    mock_func = Mock(side_effect=PineconeException(PINECONE_ERROR_MESSAGE))
    mock_func.__name__ = "dict_op"
    decorated_func = handle_dict_operation_exceptions(mock_func)

    with pytest.raises(HTTPException) as exc_info:
        decorated_func()

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    mock_logger.error.assert_called_once()


# --- Test handle_boolean_operation_exceptions --- (Similar check) ---


@patch("src.services.rag_service.decorators.logger")
def test_handle_boolean_operation_exceptions_calls_handle_pinecone(
    mock_logger,
):
    mock_func = Mock(side_effect=Exception(GENERAL_ERROR_MESSAGE))
    mock_func.__name__ = "bool_op"
    decorated_func = handle_boolean_operation_exceptions(mock_func)

    with pytest.raises(HTTPException) as exc_info:
        decorated_func()

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    mock_logger.error.assert_called_once()


# --- Test handle_index_operation_exceptions ---


@pytest.mark.asyncio
async def test_handle_index_operation_exceptions_success():
    mock_async_func = AsyncMock(return_value=TEST_RESULT)
    decorated_func = handle_index_operation_exceptions(mock_async_func)
    result = await decorated_func(*TEST_ARGS, **TEST_KWARGS)
    assert result == TEST_RESULT
    mock_async_func.assert_awaited_once_with(*TEST_ARGS, **TEST_KWARGS)


@pytest.mark.asyncio
@patch("src.services.rag_service.decorators.logger")
async def test_handle_index_operation_exceptions_failure(mock_logger):
    mock_async_func = AsyncMock(side_effect=Exception(GENERAL_ERROR_MESSAGE))
    mock_async_func.__name__ = "failed_index_op"
    decorated_func = handle_index_operation_exceptions(mock_async_func)

    with pytest.raises(HTTPException) as exc_info:
        await decorated_func(*TEST_ARGS, **TEST_KWARGS)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Error in index operation" == exc_info.value.detail["error"]
    assert mock_async_func.__name__ in exc_info.value.detail["message"]
    assert GENERAL_ERROR_MESSAGE in exc_info.value.detail["message"]
    mock_logger.error.assert_called_once()
    assert "index operation" in mock_logger.error.call_args[0][0]
    assert mock_async_func.__name__ in mock_logger.error.call_args[0][0]


# --- Test handle_namespace_operation_exceptions ---


@pytest.mark.asyncio
async def test_handle_namespace_operation_exceptions_success():
    mock_async_func = AsyncMock(return_value=TEST_RESULT)
    decorated_func = handle_namespace_operation_exceptions(mock_async_func)
    result = await decorated_func(*TEST_ARGS, **TEST_KWARGS)
    assert result == TEST_RESULT
    mock_async_func.assert_awaited_once_with(*TEST_ARGS, **TEST_KWARGS)


@pytest.mark.asyncio
@patch("src.services.rag_service.decorators.logger")
async def test_handle_namespace_operation_exceptions_failure(mock_logger):
    mock_async_func = AsyncMock(side_effect=Exception(GENERAL_ERROR_MESSAGE))
    mock_async_func.__name__ = "failed_namespace_op"
    decorated_func = handle_namespace_operation_exceptions(mock_async_func)

    with pytest.raises(HTTPException) as exc_info:
        await decorated_func(*TEST_ARGS, **TEST_KWARGS)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Error in namespace operation" == exc_info.value.detail["error"]
    assert mock_async_func.__name__ in exc_info.value.detail["message"]
    assert GENERAL_ERROR_MESSAGE in exc_info.value.detail["message"]
    mock_logger.error.assert_called_once()
    assert "namespace operation" in mock_logger.error.call_args[0][0]
    assert mock_async_func.__name__ in mock_logger.error.call_args[0][0]


# --- Test handle_folder_operation_exceptions ---


@pytest.mark.asyncio
async def test_handle_folder_operation_exceptions_success():
    mock_async_func = AsyncMock(return_value=TEST_RESULT)
    decorated_func = handle_folder_operation_exceptions(mock_async_func)
    result = await decorated_func(*TEST_ARGS, **TEST_KWARGS)
    assert result == TEST_RESULT
    mock_async_func.assert_awaited_once_with(*TEST_ARGS, **TEST_KWARGS)


@pytest.mark.asyncio
@patch("src.services.rag_service.decorators.logger")
async def test_handle_folder_operation_exceptions_failure(mock_logger):
    mock_async_func = AsyncMock(side_effect=Exception(GENERAL_ERROR_MESSAGE))
    mock_async_func.__name__ = "failed_folder_op"
    decorated_func = handle_folder_operation_exceptions(mock_async_func)

    with pytest.raises(HTTPException) as exc_info:
        await decorated_func(*TEST_ARGS, **TEST_KWARGS)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Error in folder operation" == exc_info.value.detail["error"]
    assert mock_async_func.__name__ in exc_info.value.detail["message"]
    assert GENERAL_ERROR_MESSAGE in exc_info.value.detail["message"]
    mock_logger.error.assert_called_once()
    assert "folder operation" in mock_logger.error.call_args[0][0]
    assert mock_async_func.__name__ in mock_logger.error.call_args[0][0]
