import os
from pathlib import Path
from typing import Optional


class PathHandler:
    """Utility class for handling file and folder paths"""

    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalize path by ensuring it ends with a slash"""
        return path.rstrip("/") + "/"

    @staticmethod
    def get_parent_folder(path: str) -> Optional[str]:
        """Get parent folder path"""
        parent = os.path.dirname(path.rstrip("/"))
        return parent if parent else None

    @staticmethod
    def get_basename(path: str) -> str:
        """Get basename of the path"""
        return os.path.basename(path.rstrip("/"))

    @staticmethod
    def join_paths(*paths: str) -> str:
        """Join multiple path components"""
        return os.path.join(*paths).replace(os.sep, "/")

    @staticmethod
    def is_empty_folder(path: str) -> bool:
        """Check if folder is empty"""
        return not any(Path(path).iterdir())
