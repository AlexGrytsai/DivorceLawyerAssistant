import datetime
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Union

from fastapi import UploadFile, Request

from src.domain.storage.entities import File, FileDelete, FolderData
from src.domain.storage.entities.folder import FolderDelete, FolderContents
from src.domain.storage.exceptions import ErrorSavingFile, NoFileProvided

logger = logging.getLogger(__name__)


def current_timestamp() -> str:
    """
    Generate a formatted timestamp string for the current time.

    Returns:
        str: Formatted timestamp in the format "HH:MM:SS MM-DD-YYYY"
    """
    return datetime.datetime.now().strftime("%H:%M:%S %m-%d-%Y")


class StorageRepository(ABC):
    """
    Abstract base class defining the contract for storage repositories.

    This interface provides methods for file and folder operations such as:
    - Uploading single and multiple files
    - Deleting files
    - Creating, renaming, and deleting folders
    - Listing files and folders
    - Getting file and folder information

    Implementations of this interface should handle the specifics of different
    storage backends (local filesystem, cloud storage, etc.).
    """

    async def __call__(
        self,
        request: Optional[Request] = None,
        file: Optional[UploadFile] = None,
        files: Optional[List[UploadFile]] = None,
        *args,
        **kwargs,
    ) -> Union[File, List[File]]:
        """
        Make the repository instance callable for convenient file uploads.

        This method provides a shorthand for uploading files by making
        the repository instance callable. It automatically determines whether
        to use single or multi-upload based on the provided parameters.

        Args:
            request: Optional FastAPI request object for context
            file: Optional single file to upload
            files: Optional list of files to upload
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Union[File, List[File]]: File entity or list of File entities
            representing uploaded files

        Raises:
            NoFileProvided: If neither file nor files parameter is provided
            ErrorSavingFile: If an error occurs during file upload
        """
        try:
            if file:
                return await self.upload(file=file, request=request)

            elif files:
                return await self.multi_upload(files=files, request=request)

            logger.warning("No file or files provided")

            raise NoFileProvided("No file or files provided")
        except ErrorSavingFile as exc:
            logger.warning(f"Error saving file: {exc}")

            raise ErrorSavingFile("File upload was unsuccessful") from exc

    @abstractmethod
    async def upload(
        self,
        file: UploadFile,
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ) -> File:
        """
        Upload a single file to storage.

        Args:
            file: The file to upload
            request: Optional FastAPI request object for context
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            File: File entity representing the uploaded file

        Raises:
            ErrorSavingFile: If an error occurs during file upload
        """
        pass

    @abstractmethod
    async def multi_upload(
        self,
        files: List[UploadFile],
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ) -> List[File]:
        """
        Upload multiple files to storage.

        Args:
            files: List of files to upload
            request: Optional FastAPI request object for context
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            List[File]: List of File entities representing the uploaded files

        Raises:
            ErrorSavingFile: If an error occurs during file upload
        """
        pass

    @abstractmethod
    async def delete_file(
        self,
        file_path: str,
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ) -> FileDelete:
        """
        Delete a file from storage.

        Args:
            file_path: Path to the file to delete
            request: Optional FastAPI request object for context
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            FileDelete: Entity containing information about the deleted file

        Raises:
            ErrorDeletingFile: If an error occurs during file deletion
        """
        pass

    @abstractmethod
    async def create_folder(
        self,
        folder_path: str,
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ) -> FolderData:
        """
        Create a new folder in storage.

        Args:
            folder_path: Path where the folder should be created
            request: Optional FastAPI request object for context
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            FolderData: Entity containing information about the created folder

        Raises:
            ProblemWithBucket: If an error occurs with the storage bucket
        """
        pass

    @abstractmethod
    async def rename_folder(
        self,
        old_path: str,
        new_path: str,
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ) -> FolderData:
        """
        Rename a folder in storage.

        Args:
            old_path: Current path of the folder
            new_path: New path for the folder
            request: Optional FastAPI request object for context
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            FolderData: Entity containing information about the renamed folder

        Raises:
            ProblemWithBucket: If an error occurs with the storage bucket
        """
        pass

    @abstractmethod
    async def delete_folder(
        self,
        folder_path: str,
        request: Optional[Request] = None,
        is_delete_all: bool = False,
        *args,
        **kwargs,
    ) -> FolderDelete:
        """
        Delete a folder from storage.

        Args:
            folder_path: Path to the folder to delete
            request: Optional FastAPI request object for context
            is_delete_all: If True, delete all contents of the folder
                           recursively
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            FolderDelete: Entity containing information about
                          the deleted folder

        Raises:
            ErrorDeletingFile: If an error occurs during folder deletion
        """
        pass

    @abstractmethod
    async def get_folder(self, folder_path: str) -> FolderData:
        """
        Get information about a folder.

        Args:
            folder_path: Path to the folder

        Returns:
            FolderData: Entity containing information about the folder

        Raises:
            ProblemWithBucket: If an error occurs with the storage bucket
        """
        pass

    @abstractmethod
    async def rename_file(
        self,
        old_path: str,
        new_file_name: str,
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ) -> File:
        """
        Rename a file in storage.

        Args:
            old_path: Current path of the file
            new_file_name: New name for the file
            request: Optional FastAPI request object for context
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            File: Entity containing information about the renamed file

        Raises:
            ProblemWithBucket: If an error occurs with the storage bucket
        """
        pass

    @abstractmethod
    async def get_file(self, file_path: str) -> File:
        """
        Get information about a file.

        Args:
            file_path: Path to the file

        Returns:
            File: Entity containing information about the file

        Raises:
            ProblemWithBucket: If an error occurs with the storage bucket
        """
        pass

    @abstractmethod
    async def list_files(
        self,
        prefix: Optional[str] = "",
        search_query: Optional[str] = "",
        case_sensitive: Optional[bool] = False,
    ) -> List[File]:
        """
        List files in storage with optional filtering.

        Args:
            prefix: Optional prefix to filter files by path
            search_query: Optional search query to filter files by name
            case_sensitive: Whether the search should be case-sensitive

        Returns:
            List[File]: List of File entities matching the criteria

        Raises:
            ProblemWithBucket: If an error occurs with the storage bucket
        """
        pass

    @abstractmethod
    async def list_folders(
        self, prefix: Optional[str] = None
    ) -> List[FolderData]:
        """
        List folders in storage with optional filtering.

        Args:
            prefix: Optional prefix to filter folders by path

        Returns:
            List[FolderData]: List of FolderData entities matching the criteria

        Raises:
            ProblemWithBucket: If an error occurs with the storage bucket
        """
        pass

    @abstractmethod
    async def get_folder_contents(self, folder_path: str) -> FolderContents:
        """
        Get the contents of a folder.

        Args:
            folder_path: Path to the folder

        Returns:
            FolderContents: Entity containing the folder's contents
                            (files and subfolders)

        Raises:
            ProblemWithBucket: If an error occurs with the storage bucket
        """
        pass
