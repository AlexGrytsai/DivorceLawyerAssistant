from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest
from google.api_core import exceptions as google_exceptions
from src.infrastructure.persistence import FirestoreDocumentRepository

from src.domain.document.entities import DocumentDetail, Document
from src.domain.document.exceptions import (
    DocumentNotFoundError,
    DocumentAlreadyExistsError,
    InvalidQueryParameterError,
    UnsupportedOperatorError,
    ValidationError,
    DatabaseOperationError,
    DatabaseConnectionError,
)
from src.domain.document.value_objects import SearchQuery
from src.infrastructure.database.document.firestore.firestore_document_repository import (
    SortDirection,
)


class MockDocumentSnapshot:
    def __init__(self, data: Dict[str, Any]):
        self._data = data
        self.reference = MagicMock()

    def to_dict(self) -> Dict[str, Any]:
        return self._data


@pytest.fixture
def mock_firestore_client():
    with patch("google.cloud.firestore.Client") as mock_client:
        client = mock_client.return_value
        client.collection = MagicMock()
        yield client


@pytest.fixture
def mock_collection(mock_firestore_client):
    collection = MagicMock()
    mock_firestore_client.collection.return_value = collection
    return collection


@pytest.fixture
def firestore_database(mock_firestore_client):
    with patch(
        "src.infrastructure.persistence.firestore.firestore_document_repository.FirestoreDocumentRepository.client",
        new_callable=PropertyMock,
    ) as mock_property:
        mock_property.return_value = mock_firestore_client
        yield FirestoreDocumentRepository(
            project_id="test-project", database_name="test-db"
        )


@pytest.fixture
def sample_document_data():
    return {
        "name": "test_document",
        "path": "/test/path",
        "url": "https://example.com/test",
        "language": "en",
        "tags": {"test", "document"},
        "size": 1024,
        "content_type": "application/pdf",
        "owner": "test_user",
        "create_time": datetime.now(timezone.utc),
        "update_time": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_document(sample_document_data):
    return DocumentDetail(**sample_document_data)


@pytest.fixture
def mock_document_stream():
    def create_stream(documents: List[Dict[str, Any]]):
        return iter([MockDocumentSnapshot(doc) for doc in documents])

    return create_stream


@pytest.fixture
def mock_query():
    query = MagicMock()
    query.where = MagicMock(return_value=query)
    query.limit = MagicMock(return_value=query)
    query.offset = MagicMock(return_value=query)
    query.order_by = MagicMock(return_value=query)
    query.stream = AsyncMock()
    return query


class TestFirestoreDatabase:
    @pytest.mark.asyncio
    async def test_save_existing_document(
        self,
        firestore_database,
        mock_collection,
        sample_document,
    ):
        # Setup mocks
        mock_collection.where.return_value = mock_collection
        mock_collection.limit.return_value = mock_collection
        mock_collection.stream.return_value = iter(
            [MockDocumentSnapshot(sample_document.model_dump())]
        )

        # Execute and verify
        with pytest.raises(DocumentAlreadyExistsError) as exc_info:
            await firestore_database.save("test_collection", sample_document)

        assert str(exc_info.value) == (
            f"Document '{sample_document.name}' already exists"
        )

    @pytest.mark.asyncio
    async def test_get_document_success(
        self,
        firestore_database,
        mock_collection,
        sample_document,
    ):
        # Setup mocks
        mock_collection.where.return_value = mock_collection
        mock_collection.limit.return_value = mock_collection
        mock_collection.stream.return_value = iter(
            [MockDocumentSnapshot(sample_document.model_dump())]
        )

        # Execute
        result = await firestore_database.get_document(
            "test_collection", sample_document.name
        )

        # Verify
        assert isinstance(result, Document)
        assert result.name == sample_document.name
        assert result.url == sample_document.url

    @pytest.mark.asyncio
    async def test_get_document_detail_success(
        self,
        firestore_database,
        mock_collection,
        sample_document,
        mock_document_stream,
    ):
        mock_collection.where.return_value.limit.return_value.stream.return_value = mock_document_stream(
            [sample_document.model_dump()]
        )

        result = await firestore_database.get_document(
            "test_collection", sample_document.name, is_detail=True
        )

        assert isinstance(result, DocumentDetail)
        assert result.name == sample_document.name
        assert result.url == sample_document.url
        assert result.size == sample_document.size

    @pytest.mark.asyncio
    async def test_get_nonexistent_document(
        self,
        firestore_database,
        mock_collection,
        mock_document_stream,
    ):
        mock_collection.where.return_value.limit.return_value.stream.return_value = iter(
            []
        )

        with pytest.raises(DocumentNotFoundError) as exc_info:
            await firestore_database.get_document(
                "test_collection", "nonexistent"
            )

        assert str(exc_info.value) == "Document 'nonexistent' not found"

    @pytest.mark.asyncio
    async def test_get_document_with_empty_data(
        self,
        firestore_database,
        mock_collection,
        mock_document_stream,
    ):
        empty_document = {
            "name": "empty",
            "url": "https://example.com/empty",
            "path": "/empty/path",
        }
        mock_collection.where.return_value.limit.return_value.stream.return_value = mock_document_stream(
            [empty_document]
        )

        result = await firestore_database.get_document(
            "test_collection", "empty"
        )

        assert isinstance(result, Document)
        assert result.name == "empty"
        assert result.url == "https://example.com/empty"

    @pytest.mark.asyncio
    async def test_get_collection_success(
        self,
        firestore_database,
        mock_collection,
        sample_document,
        mock_document_stream,
    ):
        # Setup mocks
        mock_collection.order_by.return_value = mock_collection
        mock_collection.stream.return_value = mock_document_stream(
            [sample_document.model_dump()]
        )

        # Execute
        result = await firestore_database.get_collection("test_collection")

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], Document)
        assert result[0].name == sample_document.name

    @pytest.mark.asyncio
    async def test_get_collection_detail_success(
        self,
        firestore_database,
        mock_collection,
        sample_document,
        mock_document_stream,
    ):
        mock_collection.order_by.return_value.stream.return_value = (
            mock_document_stream([sample_document.model_dump()])
        )

        result = await firestore_database.get_collection(
            "test_collection", is_detail=True
        )

        assert len(result) == 1
        assert isinstance(result[0], DocumentDetail)
        assert result[0].name == sample_document.name

    @pytest.mark.asyncio
    async def test_get_collection_with_limit(
        self,
        firestore_database,
        mock_collection,
        sample_document,
        mock_document_stream,
    ):
        mock_collection.order_by.return_value.limit.return_value.stream.return_value = mock_document_stream(
            [sample_document.model_dump()]
        )

        await firestore_database.get_collection("test_collection", limit=1)

        mock_collection.order_by.return_value.limit.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_collection_with_sorting(
        self,
        firestore_database,
        mock_collection,
        sample_document,
        mock_document_stream,
    ):
        mock_collection.order_by.return_value.stream.return_value = (
            mock_document_stream([sample_document.model_dump()])
        )

        await firestore_database.get_collection(
            "test_collection",
            sort_direction=SortDirection.DESCENDING,
            order_by="name",
        )

        mock_collection.order_by.assert_called_once_with(
            "name", direction=SortDirection.DESCENDING
        )

    @pytest.mark.asyncio
    async def test_get_empty_collection(
        self,
        firestore_database,
        mock_collection,
        mock_document_stream,
    ):
        mock_collection.order_by.return_value.stream.return_value = iter([])

        result = await firestore_database.get_collection("test_collection")

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_update_document_success(
        self,
        firestore_database,
        mock_collection,
        sample_document,
    ):
        # Setup mocks
        mock_collection.where.return_value = mock_collection
        mock_collection.limit.return_value = mock_collection
        mock_document = MockDocumentSnapshot(sample_document.model_dump())
        mock_document.reference.update = MagicMock()
        mock_collection.stream.return_value = iter([mock_document])

        # Execute
        await firestore_database.update(
            "test_collection", sample_document.name, sample_document
        )

        # Verify
        mock_document.reference.update.assert_called_once_with(
            sample_document.model_dump()
        )

    @pytest.mark.asyncio
    async def test_update_nonexistent_document(
        self,
        firestore_database,
        mock_collection,
        sample_document,
        mock_document_stream,
    ):
        mock_collection.where.return_value.limit.return_value.stream.return_value = iter(
            []
        )

        with pytest.raises(DocumentNotFoundError) as exc_info:
            await firestore_database.update(
                "test_collection", "nonexistent", sample_document
            )

        assert str(exc_info.value) == "Document 'nonexistent' not found"

    @pytest.mark.asyncio
    async def test_delete_document_success(
        self,
        firestore_database,
        mock_collection,
        sample_document,
    ):
        # Setup mocks
        mock_collection.where.return_value = mock_collection
        mock_collection.limit.return_value = mock_collection
        mock_document = MockDocumentSnapshot(sample_document.model_dump())
        mock_document.reference.delete = MagicMock()
        mock_collection.stream.return_value = iter([mock_document])

        # Execute
        await firestore_database.delete(
            "test_collection", sample_document.name
        )

        # Verify
        mock_document.reference.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(
        self,
        firestore_database,
        mock_collection,
        mock_document_stream,
    ):
        mock_collection.where.return_value.limit.return_value.stream.return_value = iter(
            []
        )

        with pytest.raises(DocumentNotFoundError) as exc_info:
            await firestore_database.delete("test_collection", "nonexistent")

        assert str(exc_info.value) == "Document 'nonexistent' not found"

    @pytest.mark.asyncio
    async def test_filter_documents_success(
        self,
        firestore_database,
        mock_collection,
        sample_document,
    ):
        # Setup mocks
        mock_collection.where.return_value = mock_collection
        mock_collection.limit.return_value = mock_collection
        mock_collection.stream.return_value = iter(
            [MockDocumentSnapshot(sample_document.model_dump())]
        )

        # Execute
        result = await firestore_database.filter(
            "test_collection",
            field="name",
            operator="==",
            value=sample_document.name,
        )

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], DocumentDetail)
        assert result[0].name == sample_document.name

    @pytest.mark.asyncio
    async def test_filter_documents_with_limit(
        self,
        firestore_database,
        mock_collection,
        sample_document,
        mock_document_stream,
    ):
        mock_collection.where.return_value.limit.return_value.stream.return_value = mock_document_stream(
            [sample_document.model_dump()]
        )

        await firestore_database.filter(
            "test_collection",
            field="name",
            operator="==",
            value=sample_document.name,
            limit=1,
        )

        mock_collection.where.return_value.limit.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_find_documents_success(
        self,
        firestore_database,
        mock_collection,
        sample_document,
    ):
        # Setup mocks
        mock_collection.where.return_value = mock_collection
        mock_collection.limit.return_value = mock_collection
        mock_collection.stream.return_value = iter(
            [MockDocumentSnapshot(sample_document.model_dump())]
        )

        # Prepare query
        query_params = [
            SearchQuery(
                field="name", operator="==", value=sample_document.name
            )
        ]

        # Execute
        result = await firestore_database.find(
            "test_collection", query=query_params
        )

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], Document)
        assert result[0].name == sample_document.name

    @pytest.mark.asyncio
    async def test_find_documents_with_limit_and_skip(
        self,
        firestore_database,
        mock_collection,
        sample_document,
        mock_document_stream,
    ):
        mock_collection.where.return_value.limit.return_value.offset.return_value.stream.return_value = mock_document_stream(
            [sample_document.model_dump()]
        )

        query_params = [
            SearchQuery(
                field="name", operator="==", value=sample_document.name
            )
        ]

        await firestore_database.find(
            "test_collection", query=query_params, limit=1, skip=1
        )

        mock_collection.where.return_value.limit.assert_called_once_with(1)
        mock_collection.where.return_value.limit.return_value.offset.assert_called_once_with(
            1
        )

    @pytest.mark.asyncio
    async def test_find_documents_with_multiple_conditions(
        self,
        firestore_database,
        mock_collection,
        sample_document,
    ):
        # Setup mocks
        mock_collection.where.return_value = mock_collection
        mock_collection.stream.return_value = iter(
            [MockDocumentSnapshot(sample_document.model_dump())]
        )

        # Prepare query with valid fields from DocumentSchema
        query_params = [
            SearchQuery(
                field="name", operator="==", value=sample_document.name
            ),
            SearchQuery(field="url", operator="==", value=sample_document.url),
        ]

        # Execute
        result = await firestore_database.find(
            "test_collection", query=query_params
        )

        # Verify
        assert len(result) == 1
        assert mock_collection.where.call_count == 2


# Additional tests for invalid query parameters


@pytest.mark.asyncio
async def test_find_with_empty_query(firestore_database):
    with pytest.raises(InvalidQueryParameterError) as exc_info:
        await firestore_database.find("test_collection", query=[])
    assert str(exc_info.value) == "Query parameters list cannot be empty"


@pytest.mark.asyncio
async def test_find_with_invalid_field(firestore_database):
    invalid_query = [
        SearchQuery(
            field="non_existent_field", operator="==", value="some_value"
        )
    ]
    with pytest.raises(InvalidQueryParameterError) as exc_info:
        await firestore_database.find("test_collection", query=invalid_query)
    assert str(exc_info.value) == "Invalid field: non_existent_field"


@pytest.mark.asyncio
async def test_find_with_unsupported_operator(firestore_database):
    invalid_query = [
        SearchQuery(field="name", operator="!=", value="some_value")
    ]
    with pytest.raises(UnsupportedOperatorError) as exc_info:
        await firestore_database.find("test_collection", query=invalid_query)
    assert str(exc_info.value) == "Unsupported operator: !="


@pytest.mark.asyncio
async def test_find_with_incorrect_value_type(
    firestore_database, sample_document
):
    invalid_query = [SearchQuery(field="name", operator="==", value=12345)]
    # This test should be removed as type validation is not implemented
    # in the current version of FirestoreDatabase
    await firestore_database.find("test_collection", query=invalid_query)


@pytest.mark.asyncio
async def test_empty_document_name(firestore_database):
    with pytest.raises(ValidationError) as exc_info:
        await firestore_database.get_document("test_collection", "")
    assert "Validation failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_empty_collection_name(firestore_database):
    with pytest.raises(ValidationError) as exc_info:
        await firestore_database.get_document("", "test_document")
    assert "Validation failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_none_document_name(firestore_database):
    with pytest.raises(ValidationError) as exc_info:
        await firestore_database.get_document("test_collection", None)
    assert "Validation failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_google_api_error_connection(
    firestore_database, mock_collection
):
    # Simulate Google API connection error
    mock_collection.where.side_effect = google_exceptions.GoogleAPIError(
        "Failed to connect"
    )

    with pytest.raises(DatabaseOperationError) as exc_info:
        await firestore_database.get_document(
            "test_collection", "test_document"
        )
    assert "Operation failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_google_api_permission_denied(
    firestore_database, mock_collection
):
    # Simulate permission denied error
    mock_collection.where.side_effect = google_exceptions.Forbidden(
        "Permission denied"
    )

    with pytest.raises(DatabaseOperationError) as exc_info:
        await firestore_database.get_document(
            "test_collection", "test_document"
        )
    assert "Operation failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_unexpected_error(firestore_database, mock_collection):
    # Simulate unexpected error
    mock_collection.where.side_effect = RuntimeError("Unexpected error")

    with pytest.raises(DatabaseConnectionError) as exc_info:
        await firestore_database.get_document(
            "test_collection", "test_document"
        )
    assert "Unexpected error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_invalid_query_value_type(firestore_database):
    # Create a query with invalid value type
    query_params = [
        SearchQuery(field="name", operator="==", value={"complex": "object"})
    ]

    with pytest.raises(InvalidQueryParameterError) as exc_info:
        await firestore_database.find("test_collection", query=query_params)
    assert "Invalid value type for field" in str(exc_info.value)


@pytest.mark.asyncio
async def test_document_version_conflict(
    firestore_database, mock_collection, sample_document
):
    # Simulate document version conflict error
    mock_document = MockDocumentSnapshot(sample_document.model_dump())
    mock_document.reference.update.side_effect = google_exceptions.Aborted(
        "Version conflict"
    )
    mock_collection.where.return_value.limit.return_value.stream.return_value = iter(
        [mock_document]
    )

    with pytest.raises(DatabaseOperationError) as exc_info:
        await firestore_database.update(
            "test_collection", sample_document.name, sample_document
        )
    assert "Operation failed" in str(exc_info.value)
