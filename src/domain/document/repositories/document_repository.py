from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union

from src.domain.document.entities import DocumentDetailSchema, DocumentSchema
from src.domain.document.value_objects import SearchQuery


class DocumentRepository(ABC):
    @abstractmethod
    async def save(
        self, collection: str, document: DocumentDetailSchema
    ) -> str:
        pass

    @abstractmethod
    async def get_document(
        self, collection: str, document_name: str, is_detail: bool = False
    ) -> Union[DocumentSchema, DocumentDetailSchema]:
        pass

    @abstractmethod
    async def get_collection(
        self,
        collection: str,
        sort_direction: str,
        limit: Optional[int] = None,
        order_by: str = "name",
        is_detail: bool = False,
    ) -> List[Union[DocumentSchema, DocumentDetailSchema]]:
        pass

    @abstractmethod
    async def find(
        self,
        collection: str,
        query: List[SearchQuery],
        limit: Optional[int] = None,
        skip: Optional[int] = None,
    ) -> List[DocumentSchema]:
        pass

    @abstractmethod
    async def update(
        self,
        collection: str,
        document_name: str,
        updates: DocumentDetailSchema,
    ) -> None:
        pass

    @abstractmethod
    async def delete(self, collection: str, document_name: str) -> None:
        pass

    @abstractmethod
    async def filter(
        self,
        collection: str,
        field: str,
        operator: str,
        value: Any,
        limit: Optional[int] = None,
    ) -> List[DocumentDetailSchema]:
        pass
