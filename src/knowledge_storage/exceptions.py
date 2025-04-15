from typing import Optional


class KnowledgeStorageError(Exception):
    """Base exception for knowledge storage system errors."""

    pass


class StorageNotFoundError(KnowledgeStorageError):
    """Raised when a storage is not found."""

    def __init__(self, storage_name: str):
        self.storage_name = storage_name
        super().__init__(f"Storage '{storage_name}' not found")


class CategoryNotFoundError(KnowledgeStorageError):
    """Raised when a category is not found."""

    def __init__(self, storage_name: str, category_name: str):
        self.storage_name = storage_name
        self.category_name = category_name
        super().__init__(
            f"Category '{category_name}' not found in storage '{storage_name}'"
        )


class SubCategoryNotFoundError(KnowledgeStorageError):
    """Raised when a subcategory is not found."""

    def __init__(
        self, storage_name: str, category_name: str, subcategory_name: str
    ):
        self.storage_name = storage_name
        self.category_name = category_name
        self.subcategory_name = subcategory_name
        super().__init__(
            f"Subcategory '{subcategory_name}' not found in category "
            f"'{category_name}' of storage '{storage_name}'"
        )


class ItemNotFoundError(KnowledgeStorageError):
    """Raised when an item is not found."""

    def __init__(
        self,
        storage_name: str,
        category_name: str,
        item_name: str,
        subcategory_name: Optional[str] = None,
    ):
        self.storage_name = storage_name
        self.category_name = category_name
        self.item_name = item_name
        self.subcategory_name = subcategory_name

        location = (
            f"subcategory '{subcategory_name}' of category '{category_name}'"
            if subcategory_name
            else f"category '{category_name}'"
        )
        super().__init__(
            f"Item '{item_name}' not found in {location} "
            f"of storage '{storage_name}'"
        )


class UserNotFoundError(KnowledgeStorageError):
    """Raised when a user is not found."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"User with ID '{user_id}' not found")


class PermissionErrors(KnowledgeStorageError):
    """Raised when a user lacks required permissions."""

    def __init__(self, message: str):
        super().__init__(f"Permission denied: {message}")
