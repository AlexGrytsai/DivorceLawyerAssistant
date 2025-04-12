from abc import ABC, abstractmethod
from typing import List

from src.knowledge_storage.schemas import (
    KnowledgeSchema,
    KnowledgeRenameSchema,
    KnowledgeDeleteSchema,
)


class KnowledgeStorageInterface(ABC):
    @abstractmethod
    async def create_storage(self, name: str) -> KnowledgeSchema:
        pass

    @abstractmethod
    async def rename_storage(
        self, old_name: str, new_name: str
    ) -> KnowledgeRenameSchema:
        pass

    @abstractmethod
    async def delete_storage(self, name: str) -> KnowledgeDeleteSchema:
        pass

    @abstractmethod
    async def get_storage(self, name: str) -> KnowledgeRenameSchema:
        pass

    @abstractmethod
    async def list_storages(self) -> List[KnowledgeSchema]:
        pass
