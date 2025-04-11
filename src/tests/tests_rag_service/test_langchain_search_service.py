from unittest.mock import MagicMock

import pytest
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

from src.services.rag_service.factory.vector_store_factory import (
    VectorStoreFactory,
)
from src.services.rag_service.schemas import QueryResultSchema
from src.services.rag_service.search.langchain_search_service import (
    LangChainSearchService,
)


@pytest.fixture
def mock_embeddings():
    return MagicMock(spec=Embeddings)


@pytest.fixture
def mock_vector_store():
    return MagicMock(spec=VectorStore)


@pytest.fixture
def mock_vector_store_factory(mock_vector_store):
    factory = MagicMock(spec=VectorStoreFactory)
    factory.create_vector_store.return_value = mock_vector_store
    return factory


@pytest.fixture
def search_service(mock_embeddings, mock_vector_store_factory):
    return LangChainSearchService(
        embeddings=mock_embeddings,
        vector_store_factory=mock_vector_store_factory,
    )


class TestLangChainSearchService:
    async def test_search_success(self, search_service, mock_vector_store):
        # Setup
        query = "test query"
        index_name = "test_index"
        namespace = "test_namespace"
        top_k = 2

        mock_doc1 = MagicMock()
        mock_doc1.page_content = "Test content 1"
        mock_doc1.metadata = {"chunk_id": "id1", "source": "file1.pdf"}

        mock_doc2 = MagicMock()
        mock_doc2.page_content = "Test content 2"
        mock_doc2.metadata = {"chunk_id": "id2", "source": "file2.pdf"}

        mock_vector_store.similarity_search_with_score.return_value = [
            (mock_doc1, 0.9),
            (mock_doc2, 0.8),
        ]

        # Execute
        results = await search_service.search(
            query=query,
            index_name=index_name,
            namespace=namespace,
            top_k=top_k,
        )

        # Assert
        assert len(results) == 2
        assert isinstance(results[0], QueryResultSchema)
        assert results[0].id == "id1"
        assert results[0].text == "Test content 1"
        assert results[0].score == 0.9
        assert results[0].file_path == "file1.pdf"

        assert results[1].id == "id2"
        assert results[1].text == "Test content 2"
        assert results[1].score == 0.8
        assert results[1].file_path == "file2.pdf"

        mock_vector_store.similarity_search_with_score.assert_called_once_with(
            query=query, k=top_k, filter=None
        )

    async def test_search_with_filters(
        self, search_service, mock_vector_store
    ):
        # Setup
        query = "test query"
        index_name = "test_index"
        namespace = "test_namespace"
        filters = {"category": "test"}

        mock_doc = MagicMock()
        mock_doc.page_content = "Test content"
        mock_doc.metadata = {"chunk_id": "id1", "source": "file1.pdf"}

        mock_vector_store.similarity_search_with_score.return_value = [
            (mock_doc, 0.9)
        ]

        # Execute
        results = await search_service.search(
            query=query,
            index_name=index_name,
            namespace=namespace,
            filters=filters,
        )

        # Assert
        assert len(results) == 1
        mock_vector_store.similarity_search_with_score.assert_called_once_with(
            query=query, k=5, filter=filters  # default value
        )

    async def test_search_empty_results(
        self, search_service, mock_vector_store
    ):
        # Setup
        mock_vector_store.similarity_search_with_score.return_value = []

        # Execute
        results = await search_service.search(
            query="test", index_name="test", namespace="test"
        )

        # Assert
        assert len(results) == 0
        assert isinstance(results, list)
