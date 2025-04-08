import logging
from typing import Dict, Type

from src.services.rag_service.file_processors.pdf_processor import (
    PDFProcessorInterface,
)
from src.services.rag_service.interfaces import FileProcessorInterface

logger = logging.getLogger(__name__)


class FileProcessorFactory:
    """
    A factory class for creating file processors based on file extensions.

    This class manages a registry of file processor implementations and
    provides methods to:
    - Register new file processor types
    - Retrieve the appropriate processor for a given file
    - Fall back to a NullProcessor for unsupported file types

    Usage:
        factory = FileProcessorFactory()
        factory.register_processor("txt", TextProcessorInterface)
        processor = factory.get_processor("document.txt")
        documents = await processor.process_file(...)
    """

    def __init__(self):
        self._processors: Dict[str, Type[FileProcessorInterface]] = {}
        self._register_default_processors()

    def _register_default_processors(self):
        self.register_processor("pdf", PDFProcessorInterface)

    def register_processor(
        self, file_type: str, processor_class: Type[FileProcessorInterface]
    ):
        self._processors[file_type.lower()] = processor_class

    def get_processor(self, file_path: str) -> FileProcessorInterface:
        file_ext = file_path.split(".")[-1].lower()

        processor_class = self._processors.get(file_ext)
        if not processor_class:
            logger.warning(f"Unsupported file type: {file_path}")
            from src.services.rag_service.file_processors.null_processor import (
                NullProcessorInterface,
            )

            return NullProcessorInterface()

        return processor_class()
