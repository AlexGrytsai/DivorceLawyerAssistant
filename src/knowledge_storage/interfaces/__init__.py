from .base_entity_interface import BaseEntityInterface
from .knowledge_category_interface import KnowledgeCategoryInterface
from .knowledge_storage_interface import KnowledgeStorageInterface
from .permission_interface import PermissionInterface
from .searchable_interface import SearchableInterface
from .taggable_interface import TaggableInterface
from .versionable_interface import VersionalInterface

__all__ = [
    "KnowledgeStorageInterface",
    "KnowledgeCategoryInterface",
    "BaseEntityInterface",
    "TaggableInterface",
    "PermissionInterface",
    "VersionalInterface",
    "SearchableInterface",
]
