from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, TYPE_CHECKING

from src.core.config import settings
from src.services.rag_service.decorators import (
    handle_document_processing,
)
from src.services.rag_service.schemas import DocumentSchema
from src.services.storage.interfaces import BaseStorageInterface
from src.services.storage.shemas import FileSchemaForFolder, FolderItem

if TYPE_CHECKING:
    from src.services.rag_service.factory.file_processor_factory import (
        FileProcessorFactory,
    )

logger = logging.getLogger(__name__)


class DirectoryProcessor:
    """
    Processes directories containing files for RAG indexing.

    This class handles the recursive processing of directories,
    filtering files, and delegating file processing to appropriate file
    processors based on a file type.

    Attributes:
        file_processor_factory: Factory for creating file processors based
                                on file type
        rag_storage: Storage interface for accessing directory contents
    """

    def __init__(
        self,
        file_processor_factory: FileProcessorFactory,
        rag_storage: Optional[BaseStorageInterface] = None,
    ):
        self.file_processor_factory = file_processor_factory
        self.rag_storage = rag_storage or settings.RAG_STORAGE

    @handle_document_processing
    async def process_directory(
        self,
        directory_path: str,
        index_name: str,
        namespace: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentSchema]:
        logger.info(
            f"Processing directory: {directory_path} "
            f"for index: {index_name}, namespace: {namespace}"
        )

        # Add a directory path to metadata if not provided
        base_metadata = metadata or {}
        base_metadata["source_directory"] = directory_path

        folder_contents = await self.rag_storage.get_folder_contents(
            directory_path
        )

        filter_files = self._filter_files(folder_contents.items)

        return await self._process_files(
            filter_files, index_name, namespace, base_metadata
        )

    @staticmethod
    def _filter_files(
        folder_contents_items: List[Union[FileSchemaForFolder, FolderItem]],
    ) -> List[FileSchemaForFolder]:
        return [
            item for item in folder_contents_items if item["type"] == "file"
        ]

    async def _process_single_file(
        self,
        item: FileSchemaForFolder,
        index_name: str,
        namespace: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentSchema]:
        processor = self.file_processor_factory.get_processor(item.url)

        return await processor.process_file(
            file_path=item.url,
            index_name=index_name,
            namespace=namespace,
            metadata=metadata,
        )

    async def _process_files(
        self,
        files: List[FileSchemaForFolder],
        index_name: str,
        namespace: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentSchema]:

        file_documents_lists = await asyncio.gather(
            *[
                self._process_single_file(
                    item, index_name, namespace, metadata
                )
                for item in files
            ]
        )

        documents_result = []
        for file_docs in file_documents_lists:
            documents_result.extend(file_docs)

        return documents_result
