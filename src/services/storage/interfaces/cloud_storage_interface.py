from abc import ABC, abstractmethod
from typing import List, Optional, Union

from google.cloud import storage  # type: ignore
from google.cloud.storage import Blob, Bucket  # type: ignore
from google.cloud.storage_control_v2 import RenameFolderRequest

from src.services.storage.shemas import (
    FolderBaseSchema,
    FolderDeleteSchema,
    FileSchema,
    FileDeleteSchema,
    FolderDataSchema,
)


class CloudStorageInterface(ABC):
    """
    Abstract interface for cloud storage implementations.

    This interface defines a standard set of operations for interacting with
    cloud storage services, such as Google Cloud Storage, AWS S3, etc.
    It provides methods for file (blob) operations like upload, delete,
    copy, rename, and list, as well as folder management operations.

    Implementations of this interface should handle the specifics
    of connecting to and authenticating with the particular cloud storage
    provider.
    """

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
        Upload blob (file) to cloud storage.

        Args:
            file_path: Path where the file should be stored in the bucket
            content: The content to upload (either string or bytes)
            content_type: Optional MIME type of the content
                          (e.g., 'application/pdf')

        Returns:
            FileSchema: Information about the uploaded file including its URL

        Raises:
            ErrorSavingFile: If upload operation fails
        """
        pass

    @abstractmethod
    async def delete_blob(self, file_path: str) -> FileDeleteSchema:
        """
        Delete blob (file) from cloud storage.

        Args:
            file_path: Path to the file to delete in the bucket

        Returns:
            FileDeleteSchema: Information about the deleted file

        Raises:
            ErrorSavingFile: If deletion operation fails
        """
        pass

    @abstractmethod
    async def get_blob(self, file_path: str) -> FileSchema:
        """
        Get blob (file) from cloud storage.

        Args:
            file_path: Path to the file to retrieve in the bucket

        Returns:
            FileSchema: Information about the retrieved file
        """
        pass

    @abstractmethod
    async def copy_blob(self, source_blob: Blob, new_name: str) -> FileSchema:
        """
        Copy blob (file) to a new location in cloud storage.

        Args:
            source_blob: Source blob object to copy
            new_name: New name/path for the copied blob

        Returns:
            FileSchema: Information about the copied file

        Raises:
            Exception: If copy operation fails
        """
        pass

    @abstractmethod
    async def rename_blob(
        self, source_blob_path: str, new_name: str
    ) -> FileSchema:
        """
        Rename blob (file) in cloud storage.

        Args:
            source_blob_path: Source blob path object to rename
            new_name: New name/path for the blob

        Returns:
            FileSchema: Information about the renamed file

        Raises:
            Exception: If rename operation fails
        """
        pass

    @abstractmethod
    async def list_blobs(
        self,
        prefix: Optional[str] = "",
        search_query: Optional[str] = None,
        case_sensitive: Optional[bool] = False,
    ) -> List[FileSchema]:
        """
        List blobs in storage with optional filtering.

        Args:
            prefix: Optional prefix to filter results (default: empty string)
            search_query: Optional search term to filter results
            case_sensitive: Whether the search should be case-sensitive
                            (default: False)

        Returns:
            List[FileSchema]: List of file schemas representing
                              the matching files
        """
        pass

    @abstractmethod
    async def create_folder(self, folder_name: str) -> FolderBaseSchema:
        """
        Create a new managed folder in the storage.

        Args:
            folder_name: Name of the folder to create

        Returns:
            FolderBaseSchema: Information about the created folder

        Raises:
            Exception: If folder creation fails
        """
        pass

    @abstractmethod
    async def delete_folder(self, folder_name: str) -> FolderDeleteSchema:
        """
        Delete a managed folder from the storage.

        Args:
            folder_name: Name of the folder to delete

        Returns:
            FolderDeleteSchema: Information about the deleted folder

        Raises:
            Exception: If folder deletion fails
        """
        pass

    @abstractmethod
    async def rename_folder(
        self, old_name: str, new_name: str
    ) -> RenameFolderRequest:
        """
        Rename a managed folder in the storage.

        Args:
            old_name: Current name of the folder
            new_name: New name for the folder

        Returns:
            RenameFolderRequest: Information about the rename operation

        Raises:
            Exception: If folder renaming fails
        """
        pass

    @abstractmethod
    async def list_folders(
        self, prefix: Optional[str] = None
    ) -> List[FolderDataSchema]:
        """
        List managed folders in the storage.

        Args:
            prefix: Optional prefix to filter results

        Returns:
            List[FolderDataSchema]: List of folder schemas representing
            the matching folders
        """
        pass
