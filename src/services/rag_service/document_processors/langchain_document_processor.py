import logging
import uuid
from typing import Dict, List, Any, Optional

from fastapi import HTTPException, status
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import TextSplitter

from src.core.config import settings
from src.services.rag_service.decorators import (
    handle_document_processing,
)
from src.services.rag_service.factory.vector_store_factory import (
    VectorStoreFactory,
)
from src.services.rag_service.interfaces import DocumentProcessorInterface
from src.services.rag_service.schemas import DocumentSchema
from src.services.rag_service.vector_stores.pinecone_factory import (
    PineconeVectorStoreFactory,
)

logger = logging.getLogger(__name__)


class LangChainDocumentProcessor(DocumentProcessorInterface):
    def __init__(
        self,
        embeddings: Optional[Embeddings] = None,
        text_splitter: Optional[TextSplitter] = None,
        vector_store: Optional[VectorStoreFactory] = None,
    ):
        self.embeddings = embeddings or settings.EMBEDDING_DEFAULT
        self.text_splitter = text_splitter or RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.vector_store = vector_store or PineconeVectorStoreFactory()

    @handle_document_processing
    async def process_documents(
        self,
        documents: List[Any],
        file_path: str,
        index_name: str,
        namespace: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentSchema]:
        # Split documents into chunks
        splits = self.text_splitter.split_documents(documents)

        if not splits:
            logger.warning(f"No content extracted from {file_path}")

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Error processing document",
                    "message": f"No content extracted from {file_path}",
                    "file_path": file_path,
                },
            )

        # Get vector store
        vector_store = self.vector_store.create_vector_store(
            index_name=index_name,
            namespace=namespace,
            embeddings=self.embeddings,
        )

        # Prepare document records
        doc_records = []
        base_metadata = metadata or {}

        # Prepare documents with IDs
        documents_with_ids = []
        for doc in splits:
            doc_id = str(uuid.uuid4())

            # Add document metadata
            doc.metadata.update(base_metadata)
            doc.metadata["chunk_id"] = doc_id

            documents_with_ids.append((doc_id, doc))

            # Create document record
            doc_records.append(
                DocumentSchema(
                    id=doc_id,
                    text=doc.page_content,
                    metadata=doc.metadata,
                    file_path=file_path,
                    index_name=index_name,
                    namespace=namespace,
                )
            )

        # Add documents to vector store
        vector_store.add_documents([doc for _, doc in documents_with_ids])

        return doc_records
