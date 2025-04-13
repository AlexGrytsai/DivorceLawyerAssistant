import logging
from typing import Dict, List, Any, Optional

from langchain_community.document_loaders import PyMuPDFLoader

from src.services.rag_service.decorators import (
    handle_document_processing,
)
from src.services.rag_service.document_processors import (
    LangChainDocumentProcessor,
)
from src.services.rag_service.interfaces import FileProcessorInterface
from src.services.rag_service.schemas import DocumentSchema

logger = logging.getLogger(__name__)


class PDFProcessor(FileProcessorInterface):
    def __init__(self, document_processor=None):
        self.document_processor = (
            document_processor or LangChainDocumentProcessor()
        )

    @handle_document_processing
    async def process_file(
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

        loader = PyMuPDFLoader(file_path)
        documents = loader.load()

        base_metadata = metadata or {}
        base_metadata["source"] = file_path

        return await self.document_processor.process_documents(
            documents=documents,
            file_path=file_path,
            index_name=index_name,
            namespace=namespace,
            metadata=base_metadata,
        )
