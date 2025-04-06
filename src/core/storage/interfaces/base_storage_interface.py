import datetime
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Union

from fastapi import UploadFile, status, HTTPException, Request

from src.core.exceptions.storage import ErrorSavingFile
from src.core.storage.shemas import (
    FileDeleteSchema,
    FolderBaseSchema,
    FolderDeleteSchema,
    FolderContentsSchema,
    FileSchema,
    FolderDataSchema,
)

logger = logging.getLogger(__name__)


def current_timestamp() -> str:
    """Generate current timestamp in consistent format"""
    return datetime.datetime.now().strftime("%H:%M:%S %m-%d-%Y")


def log_operation(message: str, level: str = "info") -> None:
    """Log operation with specified level"""
    log_func = getattr(logger, level)
    log_func(message)


class BaseStorageInterface(ABC):
    """Interface for storage implementations.

    This abstract class defines the contract for all storage implementations,
    providing methods for file and folder operations.
    """

    async def __call__(
        self,
        request: Request,
        file: Optional[UploadFile] = None,
        files: Optional[List[UploadFile]] = None,
    ) -> Union[FileSchema, List[FileSchema]]:
        """
        Handle file upload requests

        Args:
            request: FastAPI request object
            file: Optional single file to upload
            files: Optional list of files to upload

        Returns:
            Union[FileSchema, List[FileSchema]]: Upload result(s)

        Raises:
            HTTPException: If no files provided or upload fails
        """
        try:
            if file:
                return await self.upload(file=file, request=request)

            elif files:
                return await self.multi_upload(files=files, request=request)

            logger.warning("No file or files provided")

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file or files provided",
            )
        except ErrorSavingFile as exc:
            logger.warning(f"Error saving file: {exc}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": str(exc),
                    "message": "File upload was unsuccessful",
                },
            ) from exc

    @abstractmethod
    async def upload(
        self, file: UploadFile, request: Request, *args, **kwargs
    ) -> FileSchema:
        """
        Upload a single file to storage

        Args:
            file: File to upload
            request: FastAPI request object
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            FileSchema: Upload result
        """
        pass

    @abstractmethod
    async def multi_upload(
        self, files: List[UploadFile], request: Request, *args, **kwargs
    ) -> List[FileSchema]:
        """
        Upload multiple files to storage

        Args:
            files: List of files to upload
            request: FastAPI request object
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            List[FileSchema]: List of upload results
        """
        pass

    @abstractmethod
    async def delete_file(
        self, file_path: str, request: Request, *args, **kwargs
    ) -> FileDeleteSchema:
        """
        Delete a file from storage

        Args:
            file_path: Path to file to delete
            request: FastAPI request object
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            FileDeleteSchema: Delete operation result
        """
        pass

    @abstractmethod
    async def create_folder(
        self, folder_path: str, request: Request, *args, **kwargs
    ) -> FolderDataSchema:
        """
        Create a new folder in storage

        Args:
            folder_path: Path to create folder at
            request: FastAPI request object
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            FolderBaseSchema: Folder creation result
        """
        pass

    @abstractmethod
    async def rename_folder(
        self, old_path: str, new_path: str, request: Request, *args, **kwargs
    ) -> FolderDataSchema:
        """
        Rename existing folder

        Args:
            old_path: Current folder path
            new_path: New folder path
            request: FastAPI request object
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            FolderBaseSchema: Folder rename result
        """
        pass

    @abstractmethod
    async def delete_folder(
        self, folder_path: str, request: Request, *args, **kwargs
    ) -> FolderDeleteSchema:
        """
        Delete folder and all its contents

        Args:
            folder_path: Path to folder to delete
            request: FastAPI request object
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            FolderDeleteSchema: Result with count of deleted files
        """
        pass

    @abstractmethod
    async def rename_file(
        self,
        old_path: str,
        new_file_name: str,
        request: Request,
        *args,
        **kwargs,
    ) -> FileSchema:
        """
        Rename existing file

        Args:
            old_path: Current file path
            new_file_name: New file name
            request: FastAPI request object
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            FileSchema: File rename result
        """
        pass

    @abstractmethod
    async def get_file(self, file_path: str) -> FileSchema:
        """
        Get file by path

        Args:
            file_path: Path to file

        Returns:
            FileSchema: File information

        Raises:
            ErrorSavingFile: If file not found
        """
        pass

    @abstractmethod
    async def list_files(
        self,
        prefix: Optional[str] = "",
        search_query: Optional[str] = "",
        case_sensitive: Optional[bool] = False,
    ) -> List[FileSchema]:
        """
        List all files in storage, with optional filtering by prefix and
        search query.

        Args:
            prefix (str, optional): Optional prefix to filter files.
                                    Defaults to "".
            search_query (str, optional): Optional search term to filter files.
                                          Defaults to "".
            case_sensitive (bool, optional): Whether the search should
                                             be case-sensitive.
                                             Defaults to False.

        Returns:
            List[FileSchema]: A list of file schemas representing the matching
                              files.
        """
        pass

    @abstractmethod
    async def list_folders(
        self, prefix: Optional[str] = None
    ) -> List[FolderDataSchema]:
        """
        List all folders in storage

        Args:
            prefix: Optional prefix to filter folders

        Returns:
            List[FolderBaseSchema]: List of folders
        """
        pass

    @abstractmethod
    async def get_folder_contents(
        self, folder_path: str
    ) -> FolderContentsSchema:
        """
        Get contents of a folder

        Args:
            folder_path: Path to folder

        Returns:
            FolderContentsSchema: Contents of the folder
        """
        pass
