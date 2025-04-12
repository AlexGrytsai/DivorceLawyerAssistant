from abc import ABC, abstractmethod
from typing import List

from src.knowledge_storage.schemas import (
    CategoryDeleteSchema,
    CategorySchema,
    CategoryRenameSchema,
    SubCategorySchema,
    SubCategoryDeleteSchema,
    SubCategoryRenameSchema,
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

    @abstractmethod
    async def create_subcategory(
        self, storage_name: str, category_name: str, subcategory_name: str
    ) -> SubCategorySchema:
        pass

    @abstractmethod
    async def delete_subcategory(
        self, storage_name: str, category_name: str, subcategory_name: str
    ) -> SubCategoryDeleteSchema:
        pass

    @abstractmethod
    async def rename_subcategory(
        self,
        storage_name: str,
        category_name: str,
        old_subcategory_name: str,
        new_subcategory_name: str,
    ) -> SubCategoryRenameSchema:
        pass

    @abstractmethod
    async def get_subcategory(
        self, storage_name: str, category_name: str, subcategory_name: str
    ) -> SubCategorySchema:
        pass

    @abstractmethod
    async def list_subcategories(
        self, storage_name: str, category_name: str
    ) -> List[SubCategorySchema]:
        pass
