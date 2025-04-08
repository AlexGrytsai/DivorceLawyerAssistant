from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from src.services.rag_service.schemas import DocumentSchema


class FileProcessorInterface(ABC):
    @abstractmethod
    async def process_file(
        self,
        file_path: str,
        index_name: str,
        namespace: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentSchema]:
        pass
