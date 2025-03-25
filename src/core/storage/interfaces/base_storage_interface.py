import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Union

from fastapi import UploadFile, status, HTTPException, Request

from src.core.exceptions.storage import ErrorSavingFile
from src.core.storage.shemas import (
    FileDataSchema,
    FileDeleteSchema,
    FolderDataSchema,
    FolderDeleteSchema,
)

logger = logging.getLogger(__name__)


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
    ) -> Union[FileDataSchema, List[FileDataSchema]]:
        """
        Handle file upload requests

        Args:
            request: FastAPI request object
            file: Optional single file to upload
            files: Optional list of files to upload

        Returns:
            Union[FileDataSchema, List[FileDataSchema]]: Upload result(s)

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
            )

    @abstractmethod
    async def upload(
        self, file: UploadFile, request: Request, *args, **kwargs
    ) -> FileDataSchema:
        """
        Upload a single file to storage

        Args:
            file: File to upload
            request: FastAPI request object
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            FileDataSchema: Upload result
        """
        pass

    @abstractmethod
    async def multi_upload(
        self, files: List[UploadFile], request: Request, *args, **kwargs
    ) -> List[FileDataSchema]:
        """
        Upload multiple files to storage

        Args:
            files: List of files to upload
            request: FastAPI request object
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            List[FileDataSchema]: List of upload results
        """
        pass

    @abstractmethod
    async def delete(
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
            FolderDataSchema: Folder creation result
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
            FolderDataSchema: Folder rename result
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
        self, old_path: str, new_path: str, request: Request, *args, **kwargs
    ) -> FileDataSchema:
        """
        Rename existing file

        Args:
            old_path: Current file path
            new_path: New file path
            request: FastAPI request object
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            FileDataSchema: File rename result
        """
        pass
