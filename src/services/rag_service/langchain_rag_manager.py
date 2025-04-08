import logging
from typing import Dict, List, Optional, Any

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from src.core.config import settings
from src.services.rag_service import VectorDBInterface
from src.services.rag_service.decorators import handle_document_processing
from src.services.rag_service.document_processors import (
    LangChainDocumentProcessor,
)
from src.services.rag_service.factory.file_processor_factory import (
    FileProcessorFactory,
)
from src.services.rag_service.factory.vector_store_factory import (
    VectorStoreFactory,
)
from src.services.rag_service.file_processors import DirectoryProcessor
from src.services.rag_service.interfaces import (
    DocumentProcessorInterface,
    SearchServiceInterface,
)
from src.services.rag_service.pinecone_client import PineconeClient
from src.services.rag_service.schemas import DocumentSchema, QueryResultSchema
from src.services.rag_service.search.langchain_search_service import (
    LangChainSearchService,
)
from src.services.rag_service.vector_stores.pinecone_factory import (
    PineconeVectorStoreFactory,
)

logger = logging.getLogger(__name__)


class LangChainRAGManager:
    """
    Manager for Retrieval-Augmented Generation (RAG) operations using LangChain

    This class provides a unified interface for document processing,
    vector storage, and semantic search operations.
    It handles PDF file processing, directory processing, and vector search
    capabilities through various specialized components.

    Attributes:
        vector_db_client: Client for interacting with vector database
                          (Pinecone by default)
        embeddings: Model for creating text embeddings (OpenAI by default)
        document_processor: Processor for handling document chunking
                            splitting and embedding
        file_processor: Factory for creating file-specific processors
        directory_processor: Processor for handling directory of files
        search_service: Service for performing semantic searches
    """

    def __init__(
        self,
        vector_db_client: Optional[VectorDBInterface] = None,
        embeddings: Optional[Embeddings] = None,
        document_processor: Optional[DocumentProcessorInterface] = None,
        file_processor_factory: Optional[FileProcessorFactory] = None,
        search_service: Optional[SearchServiceInterface] = None,
        directory_processor: Optional[DirectoryProcessor] = None,
    ) -> None:
        self.vector_db_client = vector_db_client or PineconeClient()
        self.embeddings = embeddings or OpenAIEmbeddings(
            client=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL,
            dimensions=settings.DIMENSIONS_EMBEDDING,
        )
        self.document_processor = (
            document_processor
            or LangChainDocumentProcessor(embeddings=self.embeddings)
        )
        self.file_processor = file_processor_factory or FileProcessorFactory()
        self.directory_processor = directory_processor or DirectoryProcessor(
            file_processor_factory=self.file_processor
        )
        self.search_service = search_service or LangChainSearchService(
            embeddings=self.embeddings
        )

    def get_vector_store(
        self,
        index_name: str,
        namespace: str,
        vector_store: Optional[VectorStoreFactory] = None,
    ):
        vector_store = vector_store or PineconeVectorStoreFactory()
        return vector_store.create_vector_store(
            index_name=index_name,
            namespace=namespace,
            embeddings=self.embeddings,
        )

    @handle_document_processing
    async def process_pdf_file(
        self,
        file_path: str,
        index_name: str,
        namespace: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentSchema]:
        logger.info(
            f"Processing PDF file: {file_path} "
            f"for index: {index_name}, namespace: {namespace}"
        )

        processor = self.file_processor.get_processor(file_path)
        return await processor.process_file(
            file_path=file_path,
            index_name=index_name,
            namespace=namespace,
            metadata=metadata,
        )

    @handle_document_processing
    async def process_directory(
        self,
        directory_path: str,
        index_name: str,
        namespace: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentSchema]:
        logger.info(
            f"Processing of the directory: {directory_path} "
            f"for the index: {index_name}, namespaces: {namespace}"
        )

        return await self.directory_processor.process_directory(
            directory_path=directory_path,
            index_name=index_name,
            namespace=namespace,
            metadata=metadata,
        )

    async def search(
        self,
        query: str,
        index_name: str,
        namespace: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[QueryResultSchema]:
        return await self.search_service.search(
            query=query,
            index_name=index_name,
            namespace=namespace,
            top_k=top_k,
            filters=filters,
        )
