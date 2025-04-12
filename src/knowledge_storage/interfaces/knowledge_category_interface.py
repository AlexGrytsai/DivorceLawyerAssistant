from abc import ABC, abstractmethod
from typing import List

from src.knowledge_storage.schemas import (
    CategoryDeleteSchema,
    CategorySchema,
    CategoryRenameSchema,
)


class KnowledgeCategoryInterface(ABC):
    @abstractmethod
    async def create_category(
        self, storage_name: str, name: str
    ) -> CategorySchema:
        pass

    @abstractmethod
    async def rename_category(
        self, storage_name: str, old_name: str, new_name: str
    ) -> CategoryRenameSchema:
        pass

    @abstractmethod
    async def delete_category(
        self, storage_name: str, name: str
    ) -> CategoryDeleteSchema:
        pass

    @abstractmethod
    async def get_category(
        self, storage_name: str, name: str
    ) -> CategorySchema:
        pass

    @abstractmethod
    async def list_categories(self, storage_name: str) -> List[CategorySchema]:
        pass
