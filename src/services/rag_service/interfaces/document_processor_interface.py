from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from src.services.rag_service.schemas import DocumentSchema


class DocumentProcessorInterface(ABC):
    @abstractmethod
    async def process_documents(
        self,
        documents: List[Any],
        file_path: str,
        index_name: str,
        namespace: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentSchema]:
        pass
