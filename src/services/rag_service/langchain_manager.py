import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyMuPDFLoader,
)
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import TextSplitter

from src.core.config import settings
from src.services.rag_service import VectorDBInterface
from src.services.rag_service.interfaces.vector_store_factory import (
    VectorStoreFactory,
)
from src.services.rag_service.pinecone_client import PineconeClient
from src.services.rag_service.schemas import (
    DocumentSchema,
    QueryResultSchema,
)
from src.services.rag_service.vector_stores.pinecone_factory import (
    PineconeVectorStoreFactory,
)
from src.services.storage.interfaces.base_storage_interface import (
    BaseStorageInterface,
)

logger = logging.getLogger(__name__)


class LangChainManager:
    def __init__(
        self,
        vector_db_client: VectorDBInterface = PineconeClient(),
        embeddings: Embeddings = OpenAIEmbeddings(
            client=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL,
            dimensions=settings.DIMENSIONS_EMBEDDING,
        ),
        text_splitter: TextSplitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        ),
    ):
        self.vector_db_client = vector_db_client
        self.embeddings = embeddings
        self.text_splitter = text_splitter

    def get_vector_store(
        self,
        index_name: str,
        namespace: str,
        vector_store: VectorStoreFactory = PineconeVectorStoreFactory(),
    ) -> VectorStore:
        return vector_store.create_vector_store(
            index_name=index_name,
            namespace=namespace,
            embeddings=self.embeddings,
        )

    async def process_pdf_file(
        self,
        file_path: str,
        index_name: str,
        namespace: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentSchema]:
        try:
            logger.info(
                f"Processing PDF file: {file_path} "
                f"for index: {index_name}, namespace: {namespace}"
            )

            # Load and split the document
            loader = PyMuPDFLoader(file_path)
            documents = loader.load()

            # Add a file path to metadata if not provided
            base_metadata = metadata or {}
            base_metadata["source"] = file_path

            # Process and store documents
            return await self._process_and_store_documents(
                documents=documents,
                file_path=file_path,
                index_name=index_name,
                namespace=namespace,
                metadata=base_metadata,
            )
        except Exception as e:
            logger.error(f"Error processing PDF file {file_path}: {e}")
            return []

    async def process_directory(
        self,
        directory_path: str,
        index_name: str,
        namespace: str,
        metadata: Optional[Dict[str, Any]] = None,
        rag_storage: BaseStorageInterface = settings.RAG_STORAGE,
    ) -> List[DocumentSchema]:
        try:
            logger.info(
                f"Processing of the directory: {directory_path} "
                f"for the index: {index_name}, namespaces: {namespace}"
            )

            # Add a directory path to metadata if not provided
            base_metadata = metadata or {}
            base_metadata["source_directory"] = directory_path

            folder_contents = await rag_storage.get_folder_contents(
                directory_path
            )

            documents_result = []

            for item in folder_contents.items:
                if item.type == "file":
                    file_documents = await self._process_file_by_type(
                        file_path=item.url,
                        index_name=index_name,
                        namespace=namespace,
                        metadata=base_metadata,
                    )
                    documents_result.extend(file_documents)

            return documents_result
        except Exception as e:
            logger.error(f"Directory processing error {directory_path}: {e}")
            return []

    async def _process_file_by_type(
        self,
        file_path: str,
        index_name: str,
        namespace: str,
        metadata: Dict[str, Any],
    ) -> List[DocumentSchema]:
        file_ext = file_path.split(".")[-1].lower()
        
        if file_ext == "pdf":
            return await self.process_pdf_file(
                file_path=file_path,
                index_name=index_name,
                namespace=namespace,
                metadata=metadata,
            )
        elif file_ext in ["txt", "md", "rst"]:
            # Future implementation for text files processing
            logger.warning(
                f"Support for text files is not yet implemented: {file_path}"
            )
            return []
        elif file_ext in ["docx", "doc"]:
            # Future implementation for Word documents processing
            logger.warning(
                f"Support for Word documents not implemented: {file_path}"
            )
            return []
        elif file_ext in ["xlsx", "xls"]:
            # Future implementation for Excel files processing
            logger.warning(
                f"Support for Excel files is not yet implemented: {file_path}"
            )
            return []
        else:
            logger.warning(f"Unsupported file type: {file_path}")
            return []

    async def search(
        self,
        query: str,
        index_name: str,
        namespace: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[QueryResultSchema]:
        try:
            vector_store = self.get_vector_store(index_name, namespace)

            search_results = vector_store.similarity_search_with_score(
                query=query,
                k=top_k,
                filter=filters,
            )

            # Format results
            results = []
            results.extend(
                QueryResultSchema(
                    id=doc.metadata.get("chunk_id", ""),
                    text=doc.page_content,
                    metadata=doc.metadata,
                    score=float(score),
                    file_path=doc.metadata.get("source", ""),
                )
                for doc, score in search_results
            )
            return results
        except Exception as e:
            logger.error(f"Error searching in {index_name}/{namespace}: {e}")
            return []

    @staticmethod
    def _get_glob_pattern_from_mime_types(mime_types: Dict[str, str]) -> str:
        """Converts MIME-type to Glob Pattern for searching files."""
        extensions = list(mime_types.values())
        return f"**/*.{{{','.join(extensions)}}}"

    async def _process_and_store_documents(
        self,
        documents: List[Any],
        file_path: str,
        index_name: str,
        namespace: str,
        metadata: Dict[str, Any],
    ) -> List[DocumentSchema]:
        # Split documents into chunks
        splits = self.text_splitter.split_documents(documents)

        if not splits:
            logger.warning(f"No content extracted from {file_path}")
            return []

        # Get vector store
        vector_store = self.get_vector_store(index_name, namespace)

        # Prepare document records for tracking
        doc_records = []

        # Create IDs and prepare documents for adding to vector store
        documents_with_ids = []
        for doc in splits:
            doc_id = str(uuid.uuid4())

            # Add document metadata
            doc.metadata.update(metadata)
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


if __name__ == "__main__":
    chain = LangChainManager()
    print(
        asyncio.run(
            chain.process_pdf_file(
                file_path="https://storage.googleapis.com/data-for-rag/test33/%D0%92%D0%B5%D0%BB%D0%B8%D0%BA%D0%B0_%D0%9A%D1%96%D0%BB%D1%8C%D1%86%D0%B5%D0%B2%D0%B0_4%D0%91_%D0%9B%D0%B8%D1%81%D1%82_%D0%B4%D0%BB%D1%8F_%D0%B4%D0%BE%D0%B2%D1%96%D0%B4%D0%BA%D0%B8.pdf"
            )
        )
    )
