from abc import ABC, abstractmethod
from typing import List, Optional, Union

from google.cloud import storage  # type: ignore
from google.cloud.storage import Blob, Bucket  # type: ignore
from google.cloud.storage_control_v2 import (
    StorageControlClient,
)  # type: ignore

from src.core.storage.shemas import FolderDataSchema, FolderDeleteSchema


class CloudStorageInterface(ABC):
    """Interface for cloud storage implementations"""

    @abstractmethod
    def get_client(self) -> storage.Client:
        """Get cloud storage client"""
        pass

    @property
    @abstractmethod
    def get_bucket(self) -> Bucket:
        """
        Get bucket instance

        Returns:
            Bucket: Cloud storage bucket
        """
        pass

    @property
    @abstractmethod
    def get_storage_control(self) -> StorageControlClient:
        """
        Get storage control client instance.

        This property returns a StorageControlClient instance, which is used to
        manage storage resources.

        Returns:
            StorageControlClient: Storage control client instance.
        """
        pass

    @abstractmethod
    def upload_blob(
        self,
        file_path: str,
        content: Union[str, bytes],
        content_type: Optional[str] = None,
    ) -> str:
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
    def delete_blob(self, file_path: str) -> None:
        """
        Delete blob from storage

        Args:
            file_path: Path to file to delete

        Raises:
            ErrorSavingFile: If deletion fails
        """
        pass

    @abstractmethod
    def copy_blob(self, source_blob: Blob, new_name: str) -> Blob:
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
    def list_blobs(self, prefix: Optional[str] = "") -> List[Blob]:
        """
        List blobs in storage

        Args:
            prefix: Optional prefix to filter blobs

        Returns:
            List[Blob]: List of blobs
        """
        pass

    @abstractmethod
    def create_folder(self, folder_name: str) -> FolderDataSchema:
        """Create a new managed folder"""
        pass

    @abstractmethod
    def delete_managed_folder(self, folder_name: str) -> FolderDeleteSchema:
        """Delete a managed folder"""
        pass

    @abstractmethod
    def rename_folder(self, old_name: str, new_name: str) -> None:
        """Rename a managed folder"""
        pass

    @abstractmethod
    def list_managed_folders(
        self, prefix: Optional[str] = None
    ) -> List[FolderDataSchema]:
        """List managed folders"""
        pass

    @abstractmethod
    def get_managed_folder(self, folder_name: str) -> FolderDataSchema:
        """Get managed folder metadata"""
        pass
