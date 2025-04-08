import logging
from typing import Dict, List, Any, Optional

from src.services.rag_service.interfaces import FileProcessorInterface
from src.services.rag_service.schemas import DocumentSchema

logger = logging.getLogger(__name__)


class NullProcessorInterface(FileProcessorInterface):
    """
    A fallback processor for unsupported file types.

    This processor implements the FileProcessorInterface but returns an empty
    document list when processing is attempted. It logs a warning message
    indicating that the file type is unsupported.

    Used by the FileProcessorFactory when no suitable processor is found for
    a given file extension.
    """

    async def process_file(
        self,
        file_path: str,
        index_name: str,
        namespace: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentSchema]:
        logger.warning(f"Unsupported file type: {file_path}")
        return []
