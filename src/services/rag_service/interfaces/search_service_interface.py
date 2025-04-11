from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from src.services.rag_service.schemas import QueryResultSchema


class SearchServiceInterface(ABC):
    @abstractmethod
    async def search(
        self,
        query: str,
        index_name: str,
        namespace: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[QueryResultSchema]:
        pass
