from abc import ABC, abstractmethod
from typing import List, Optional, Union

from fastapi import UploadFile
from pydantic import HttpUrl

from src.knowledge_storage.schemas import (
    CategoryDeleteSchema,
    CategorySchema,
    CategoryRenameSchema,
    SubCategorySchema,
    SubCategoryDeleteSchema,
    SubCategoryRenameSchema,
    ItemCreateSchema,
    ItemDeleteSchema,
    ItemRenameSchema,
    ItemDetailSchema,
    CategoryDetailSchema,
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
        self, storage_name: str, name: str, is_detail: bool = False
    ) -> Union[CategorySchema, CategoryDetailSchema]:
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

    @abstractmethod
    async def create_item(
        self,
        storage_name: str,
        category_name: str,
        item_name: str,
        item: Union[HttpUrl, str, UploadFile],
        subcategory_name: Optional[str] = None,
    ) -> ItemCreateSchema:
        pass

    @abstractmethod
    async def rename_item(
        self,
        storage_name: str,
        category_name: str,
        item_name: str,
        new_item_name: str,
        subcategory_name: Optional[str] = None,
    ) -> ItemRenameSchema:
        pass

    @abstractmethod
    async def delete_item(
        self,
        storage_name: str,
        category_name: str,
        item_name: str,
        subcategory_name: Optional[str] = None,
    ) -> ItemDeleteSchema:
        pass

    @abstractmethod
    async def get_item(
        self,
        storage_name: str,
        category_name: str,
        item_name: str,
        subcategory_name: Optional[str] = None,
    ) -> ItemDetailSchema:
        pass

    @abstractmethod
    async def list_items(
        self,
        storage_name: str,
        category_name: str,
        subcategory_name: Optional[str] = None,
    ) -> List[ItemDetailSchema]:
        pass
