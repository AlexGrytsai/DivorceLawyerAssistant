import logging
from typing import Dict, List, Any, Optional

from langchain_core.embeddings import Embeddings

from src.core.config import settings
from src.services.rag_service.decorators import handle_async_search_exceptions
from src.services.rag_service.factory.vector_store_factory import (
    VectorStoreFactory,
)
from src.services.rag_service.interfaces import SearchServiceInterface
from src.services.rag_service.schemas import QueryResultSchema
from src.services.rag_service.vector_stores.pinecone_factory import (
    PineconeVectorStoreFactory,
)

logger = logging.getLogger(__name__)


class LangChainSearchService(SearchServiceInterface):
    def __init__(
        self,
        embeddings: Optional[Embeddings] = None,
        vector_store_factory: Optional[VectorStoreFactory] = None,
    ):
        self.embeddings = embeddings or settings.BASE_EMBEDDING
        self.vector_store = (
            vector_store_factory or PineconeVectorStoreFactory()
        )

    @handle_async_search_exceptions
    async def search(
        self,
        query: str,
        index_name: str,
        namespace: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[QueryResultSchema]:
        vector_store = self.vector_store.create_vector_store(
            index_name=index_name,
            namespace=namespace,
            embeddings=self.embeddings,
        )

        search_results = vector_store.similarity_search_with_score(
            query=query,
            k=top_k,
            filter=filters,
        )

        # Format results
        search_results_format: List[QueryResultSchema] = []
        search_results_format.extend(
            QueryResultSchema(
                id=doc.metadata.get("chunk_id", ""),
                text=doc.page_content,
                metadata=doc.metadata,
                score=float(score),
                file_path=doc.metadata.get("source", ""),
            )
            for doc, score in search_results
        )
        return search_results_format
