from abc import ABC, abstractmethod
from typing import List, Optional, Union

from google.cloud import storage  # type: ignore
from google.cloud.storage import Blob, Bucket  # type: ignore
from google.cloud.storage_control_v2 import RenameFolderRequest

from src.core.storage.shemas import (
    FolderBaseSchema,
    FolderDeleteSchema,
    FileSchema,
    FileDeleteSchema,
)


class CloudStorageInterface(ABC):
    """Interface for cloud storage implementations"""

    @property
    @abstractmethod
    def base_url(self) -> str:
        """
        Base URL for accessing storage.

        Returns:
            str: The base URL.
        """
        pass

    @property
    @abstractmethod
    def bucket(self) -> Bucket:
        """
        Get the cloud storage bucket instance.

        This property returns a Bucket instance, which represents a bucket in
        the cloud storage.
        The bucket is used to store and manage files.

        Returns:
            Bucket: The cloud storage bucket instance.
        """
        pass

    @abstractmethod
    async def upload_blob(
        self,
        file_path: str,
        content: Union[str, bytes],
        content_type: Optional[str] = None,
    ) -> FileSchema:
        """
        Upload blob to storage

        Args:
            file_path: Path to file in storage
            content: File content
            content_type: Optional content type

        Returns:
            str: Public URL of uploaded file

        Raises:
            ErrorSavingFile: If upload fails
        """
        pass

    @abstractmethod
    async def delete_blob(self, file_path: str) -> FileDeleteSchema:
        """
        Delete blob from storage

        Args:
            file_path: Path to file to delete

        Raises:
            ErrorSavingFile: If deletion fails
        """
        pass

    @abstractmethod
    async def copy_blob(self, source_blob: Blob, new_name: str) -> FileSchema:
        """
        Copy blob to new location

        Args:
            source_blob: Source blob to copy
            new_name: New name for copied blob

        Returns:
            Blob: Copied blob
        """
        pass

    @abstractmethod
    async def rename_blob(
        self, source_blob: Blob, new_name: str
    ) -> FileSchema:
        """
        Rename blob

        Args:
            source_blob: Source blob to rename
            new_name: New name for blob

        Returns:
            Blob: Renamed blob
        """
        pass

    @abstractmethod
    async def list_blobs(self, prefix: Optional[str] = "") -> List[Blob]:
        """
        List blobs in storage

        Args:
            prefix: Optional prefix to filter blobs

        Returns:
            List[Blob]: List of blobs
        """
        pass

    @abstractmethod
    async def create_folder(self, folder_name: str) -> FolderBaseSchema:
        """Create a new managed folder"""
        pass

    @abstractmethod
    async def delete_folder(self, folder_name: str) -> FolderDeleteSchema:
        """Delete a managed folder"""
        pass

    @abstractmethod
    async def rename_folder(
        self, old_name: str, new_name: str
    ) -> RenameFolderRequest:
        """Rename a managed folder"""
        pass

    @abstractmethod
    async def list_folders(
        self, prefix: Optional[str] = None
    ) -> List[FolderBaseSchema]:
        """List managed folders"""
        pass
