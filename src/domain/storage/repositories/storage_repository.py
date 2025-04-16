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
    """Generate current timestamp in consistent format"""
    return datetime.datetime.now().strftime("%H:%M:%S %m-%d-%Y")


class StorageRepository(ABC):
    """Interface for storage implementations.

    This abstract class defines the contract for all storage implementations,
    providing methods for file and folder operations.
    """

    async def __call__(
        self,
        request: Optional[Request] = None,
        file: Optional[UploadFile] = None,
        files: Optional[List[UploadFile]] = None,
        *args,
        **kwargs,
    ) -> Union[File, List[File]]:
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
        pass

    @abstractmethod
    async def multi_upload(
        self,
        files: List[UploadFile],
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ) -> List[File]:
        pass

    @abstractmethod
    async def delete_file(
        self,
        file_path: str,
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ) -> FileDelete:
        pass

    @abstractmethod
    async def create_folder(
        self,
        folder_path: str,
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ) -> FolderData:
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
        pass

    @abstractmethod
    async def get_folder(self, folder_path: str) -> FolderData:
        """
        Get folder information by path

        Args:
            folder_path: Path to folder

        Returns:
            FolderDataSchema: Folder information
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
        pass

    @abstractmethod
    async def get_file(self, file_path: str) -> File:
        pass

    @abstractmethod
    async def list_files(
        self,
        prefix: Optional[str] = "",
        search_query: Optional[str] = "",
        case_sensitive: Optional[bool] = False,
    ) -> List[File]:
        pass

    @abstractmethod
    async def list_folders(
        self, prefix: Optional[str] = None
    ) -> List[FolderData]:
        pass

    @abstractmethod
    async def get_folder_contents(self, folder_path: str) -> FolderContents:
        pass
