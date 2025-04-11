from typing import Dict, Any
from unittest.mock import Mock, AsyncMock

import pytest
from fastapi import HTTPException
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_text_splitters import TextSplitter

from src.services.rag_service.document_processors.langchain_document_processor import (
    LangChainDocumentProcessor,
)
from src.services.rag_service.factory.vector_store_factory import (
    VectorStoreFactory,
)
from src.services.rag_service.schemas import DocumentSchema


class MockDocument:
    def __init__(self, page_content: str, metadata: Dict[str, Any]):
        self.page_content = page_content
        self.metadata = metadata


@pytest.fixture
def mock_embeddings():
    return Mock(spec=Embeddings)


@pytest.fixture
def mock_text_splitter():
    return Mock(spec=TextSplitter)


@pytest.fixture
def mock_vector_store():
    return Mock(spec=VectorStore)


@pytest.fixture
def mock_vector_store_factory(mock_vector_store):
    factory = Mock(spec=VectorStoreFactory)
    factory.create_vector_store.return_value = mock_vector_store
    return factory


@pytest.fixture
def document_processor(
    mock_embeddings, mock_text_splitter, mock_vector_store_factory
):
    return LangChainDocumentProcessor(
        embeddings=mock_embeddings,
        text_splitter=mock_text_splitter,
        vector_store=mock_vector_store_factory,
    )


@pytest.fixture
def sample_documents():
    return [
        MockDocument(
            page_content="Test document 1",
            metadata={"source": "test1"},
        ),
        MockDocument(
            page_content="Test document 2",
            metadata={"source": "test2"},
        ),
    ]


@pytest.mark.asyncio
async def test_process_documents_success(
    document_processor,
    mock_text_splitter,
    mock_vector_store,
    sample_documents,
):
    mock_text_splitter.split_documents.return_value = sample_documents
    mock_vector_store.add_documents = AsyncMock()

    result = await document_processor.process_documents(
        documents=sample_documents,
        file_path="test.pdf",
        index_name="test_index",
        namespace="test_namespace",
        metadata={"additional": "data"},
    )

    assert len(result) == len(sample_documents)
    assert all(isinstance(doc, DocumentSchema) for doc in result)
    mock_text_splitter.split_documents.assert_called_once_with(
        sample_documents
    )
    mock_vector_store.add_documents.assert_called_once()


@pytest.mark.asyncio
async def test_process_documents_empty_documents(
    document_processor,
    mock_text_splitter,
):
    # Setup mock to return empty list instead of Mock object
    mock_text_splitter.split_documents.return_value = []

    with pytest.raises(HTTPException) as exc_info:
        await document_processor.process_documents(
            documents=[],
            file_path="test.pdf",
            index_name="test_index",
            namespace="test_namespace",
        )

    assert exc_info.value.status_code == 422
    assert "No content extracted" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_process_documents_with_custom_parameters(
    mock_embeddings,
    mock_text_splitter,
    mock_vector_store_factory,
    sample_documents,
):
    processor = LangChainDocumentProcessor(
        embeddings=mock_embeddings,
        text_splitter=mock_text_splitter,
        vector_store=mock_vector_store_factory,
    )

    mock_text_splitter.split_documents.return_value = sample_documents
    mock_vector_store_factory.create_vector_store.return_value.add_documents = (
        AsyncMock()
    )

    result = await processor.process_documents(
        documents=sample_documents,
        file_path="test.pdf",
        index_name="test_index",
        namespace="test_namespace",
    )

    assert len(result) == len(sample_documents)
    mock_vector_store_factory.create_vector_store.assert_called_once()


@pytest.mark.asyncio
async def test_process_documents_with_invalid_documents(
    document_processor,
    mock_text_splitter,
):
    invalid_documents = [{"invalid": "format"}]
    mock_text_splitter.split_documents.return_value = []

    with pytest.raises(HTTPException) as exc_info:
        await document_processor.process_documents(
            documents=invalid_documents,
            file_path="test.pdf",
            index_name="test_index",
            namespace="test_namespace",
        )

    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_process_documents_with_large_documents(
    document_processor,
    mock_text_splitter,
    mock_vector_store,
):
    large_document = MockDocument(
        page_content="a" * 10000,
        metadata={"source": "large"},
    )
    mock_text_splitter.split_documents.return_value = [large_document]
    mock_vector_store.add_documents = AsyncMock()

    result = await document_processor.process_documents(
        documents=[large_document],
        file_path="test.pdf",
        index_name="test_index",
        namespace="test_namespace",
    )

    assert len(result) == 1
    assert len(result[0].text) == 10000


@pytest.mark.asyncio
async def test_process_documents_with_complex_metadata(
    document_processor,
    mock_text_splitter,
    mock_vector_store,
    sample_documents,
):
    complex_metadata = {
        "nested": {"key": "value"},
        "list": [1, 2, 3],
        "boolean": True,
        "number": 42,
    }

    mock_text_splitter.split_documents.return_value = sample_documents
    mock_vector_store.add_documents = AsyncMock()

    result = await document_processor.process_documents(
        documents=sample_documents,
        file_path="test.pdf",
        index_name="test_index",
        namespace="test_namespace",
        metadata=complex_metadata,
    )

    assert len(result) == len(sample_documents)
    assert all(
        complex_metadata.items() <= doc.metadata.items() for doc in result
    )


@pytest.mark.asyncio
async def test_process_documents_vector_store_error(
    document_processor,
    mock_text_splitter,
    mock_vector_store_factory,
    sample_documents,
):
    mock_text_splitter.split_documents.return_value = sample_documents
    mock_vector_store_factory.create_vector_store.side_effect = Exception(
        "Vector store error"
    )

    with pytest.raises(Exception) as exc_info:
        await document_processor.process_documents(
            documents=sample_documents,
            file_path="test.pdf",
            index_name="test_index",
            namespace="test_namespace",
        )

    assert "Vector store error" in str(exc_info.value)
