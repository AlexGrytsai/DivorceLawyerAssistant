from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union

from google.cloud import storage  # type: ignore
from google.cloud.storage import Blob, Bucket  # type: ignore


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
