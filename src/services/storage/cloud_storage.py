import asyncio
import logging
from typing import List, Optional, Union, Set, Tuple

from fastapi import UploadFile, Request, status, HTTPException
from google.cloud.storage import Blob  # type: ignore
from google.cloud.storage_control_v2 import RenameFolderRequest  # type: ignore

from src.services.storage.decorators import (
    handle_upload_file_exceptions,
    handle_delete_file_exceptions,
)
from src.services.storage.implementations import GoogleCloudStorage
from src.services.storage.interfaces import (
    CloudStorageInterface,
    BaseStorageInterface,
)
from src.services.storage.shemas import (
    FileSchema,
    FileDeleteSchema,
    FolderBaseSchema,
    FolderDeleteSchema,
    FileSchemaForFolder,
    FolderItem,
    FolderContentsSchema,
    FolderDataSchema,
)
from src.utils.path_handler import PathHandler

logger = logging.getLogger(__name__)


def _validate_blob_exists(
    cloud_storage: CloudStorageInterface,
    blob_name: str,
    error_code: int = status.HTTP_404_NOT_FOUND,
) -> None:
    """Validate that blob exists in cloud storage"""
    if not cloud_storage.bucket.blob(blob_name).exists():
        logger.warning(f"Blob {blob_name} not found")
        raise HTTPException(
            status_code=error_code,
            detail={
                "error": "Blob not found",
                "message": f"{blob_name} not found",
            },
        )


def _validate_blob_not_exists(
    cloud_storage: CloudStorageInterface,
    blob_name: str,
    error_code: int = status.HTTP_409_CONFLICT,
) -> None:
    """Validate that blob does not exist in cloud storage"""
    if cloud_storage.bucket.blob(blob_name).exists():
        logger.warning(f"Blob {blob_name} already exists")
        raise HTTPException(
            status_code=error_code,
            detail={
                "error": "Blob already exists",
                "message": f"{blob_name} already exists",
            },
        )


class CloudStorage(BaseStorageInterface):

    def __init__(
        self,
        project_id: str,
        bucket_name: str,
        path_handler: Optional[PathHandler] = None,
        cloud_storage: Optional[CloudStorageInterface] = None,
    ):

        self._path_handler = path_handler or PathHandler()
        self._cloud_storage = cloud_storage or GoogleCloudStorage(
            project_id=project_id,
            bucket_name=bucket_name,
        )

    @handle_upload_file_exceptions
    async def upload(
        self,
        file: UploadFile,
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ) -> FileSchema:
        content = await file.read()
        if not file.filename:
            raise ValueError("File name cannot be empty")

        return await self._cloud_storage.upload_blob(
            file.filename, content, file.content_type
        )

    @handle_upload_file_exceptions
    async def multi_upload(
        self,
        files: List[UploadFile],
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ) -> List[FileSchema]:
        tasks = [self.upload(file, request) for file in files]
        return await asyncio.gather(*tasks)

    @handle_delete_file_exceptions
    async def delete_file(
        self,
        file_path: str,
        request: Request,
        *args,
        **kwargs,
    ) -> FileDeleteSchema:
        return await self._cloud_storage.delete_blob(file_path)

    @handle_upload_file_exceptions
    async def rename_file(
        self,
        old_path: str,
        new_file_name: str,
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ) -> FileSchema:
        return await self._cloud_storage.rename_blob(old_path, new_file_name)

    @handle_upload_file_exceptions
    async def delete_all_files(
        self,
        prefix: str,
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ) -> List[FileDeleteSchema]:
        blobs: List[FileSchema] = await self._cloud_storage.list_blobs(
            prefix=prefix
        )
        tasks = [self.delete_file(blob.path, request) for blob in blobs]
        return await asyncio.gather(*tasks)

    @handle_upload_file_exceptions
    async def create_folder(
        self,
        folder_path: str,
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ) -> FolderBaseSchema:
        """Create a new folder in storage"""
        folder_path = self._path_handler.normalize_path(folder_path)
        _validate_blob_not_exists(self._cloud_storage, folder_path)

        return await self._cloud_storage.create_folder(folder_path)

    @handle_upload_file_exceptions
    async def rename_folder(
        self,
        old_path: str,
        new_path: str,
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ) -> RenameFolderRequest:
        """Rename existing folder"""
        return await self._cloud_storage.rename_folder(
            self._path_handler.normalize_path(old_path),
            self._path_handler.normalize_path(new_path),
        )

    @handle_delete_file_exceptions
    async def delete_folder(
        self,
        folder_path: str,
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ) -> FolderDeleteSchema:
        """Delete folder and all its contents"""
        return await self._cloud_storage.delete_folder(folder_path)

    @handle_upload_file_exceptions
    async def upload_file(
        self,
        file_path: str,
        destination_path: Optional[str] = None,
    ) -> FileSchema:
        if not file_path:
            raise ValueError("File path cannot be empty")

        destination = destination_path or self._path_handler.get_basename(
            file_path
        )
        return await self._cloud_storage.upload_blob(file_path, destination)

    async def get_file(self, file_path: str) -> FileSchema:
        return await self._cloud_storage.get_blob(file_path)

    async def list_files(
        self,
        prefix: Optional[str] = "",
        search_query: Optional[str] = "",
        case_sensitive: Optional[bool] = False,
    ) -> List[FileSchema]:
        return await self._cloud_storage.list_blobs(
            prefix=prefix,
            search_query=search_query,
            case_sensitive=case_sensitive,
        )

    async def list_folders(
        self,
        prefix: Optional[str] = None,
    ) -> List[FolderDataSchema]:
        """List managed folders"""
        return await self._cloud_storage.list_folders(prefix=prefix)

    async def get_folder(self, folder_path: str) -> FolderDataSchema:
        return await self._cloud_storage.get_folder(folder_path)

    async def get_folder_contents(
        self, folder_path: str
    ) -> FolderContentsSchema:
        """Get contents of a folder with files and subfolders"""
        normalized_path = self._normalize_folder_path(folder_path)
        blobs = await self._cloud_storage.list_blobs(prefix=normalized_path)

        files, folder_paths = self._separate_files_and_folders(
            blobs, normalized_path
        )

        folder_items = await self._get_folder_items(folder_paths)

        all_items = self._combine_items(files, folder_items)

        return FolderContentsSchema(
            current_path=(
                normalized_path.rstrip("/") if normalized_path else ""
            ),
            items=all_items,
        )

    def _separate_files_and_folders(
        self, blobs: List[FileSchema], folder_path: str
    ) -> Tuple[List[FileSchemaForFolder], Set[str]]:
        """Separate blobs into files and folders"""
        files: List[FileSchemaForFolder] = []
        folders: Set[str] = set()

        for blob in blobs:
            relative_path = self._get_relative_path(blob.path, folder_path)
            if not relative_path:
                continue

            if relative_path.startswith("/"):
                relative_path = relative_path[1:]

            parts = relative_path.split("/")
            if len(parts) == 1:
                files.append(
                    self._process_file_item(
                        filename=blob.filename,
                        path=blob.path,
                        url=blob.url,
                        size=blob.size,
                        content_type=blob.content_type,
                    )
                )
            else:
                current_folder = parts[0]
                current_path = (
                    f"{folder_path}{current_folder}"
                    if folder_path
                    else current_folder
                )
                if current_path not in folders:
                    folders.add(current_path)

        return files, folders

    async def _get_folder_items(
        self, folder_paths: Set[str]
    ) -> List[FolderItem]:
        """Process folder paths into folder items"""
        sorted_paths = sorted(folder_paths)
        tasks = [self._process_folder_item(path) for path in sorted_paths]
        return await asyncio.gather(*tasks)

    def _combine_items(
        self, files: List[FileSchemaForFolder], folder_items: List[FolderItem]
    ) -> List[Union[FileSchemaForFolder, FolderItem]]:
        """Combine and sort files and folders"""
        all_items: List[Union[FileSchemaForFolder, FolderItem]] = [
            *folder_items,
            *files,
        ]
        return self._sort_folder_items(all_items)

    @staticmethod
    def _normalize_folder_path(folder_path: str) -> str:
        if folder_path and folder_path.startswith("/"):
            folder_path = folder_path.removeprefix("/")
        if folder_path and not folder_path.endswith("/"):
            folder_path += "/"
        return folder_path

    @staticmethod
    def _get_relative_path(blob_name: str, folder_path: str) -> str:
        return blob_name[len(folder_path) :] if folder_path else blob_name

    @staticmethod
    def _process_file_item(
        filename: str,
        path: str,
        url: str,
        size: int,
        content_type: Optional[str] = None,
    ) -> FileSchemaForFolder:
        return FileSchemaForFolder(
            filename=filename,
            path=path,
            url=url,
            type="file",
            size=size,
            content_type=content_type,
        )

    async def _process_folder_item(self, folder_path: str) -> FolderItem:
        folder: FolderDataSchema = await self.get_folder(folder_path)
        return FolderItem(
            folder_name=folder.folder_name,
            folder_path=folder.folder_path,
            create_time=folder.create_time,
            type="folder",
        )

    @staticmethod
    def _sort_folder_items(
        items: List[Union[FileSchemaForFolder, FolderItem]],
    ) -> List[Union[FileSchemaForFolder, FolderItem]]:
        def sort_key(
            item: Union[FileSchemaForFolder, FolderItem],
        ) -> Tuple[bool, str]:
            if isinstance(item, FileSchemaForFolder):
                return True, item.filename or ""
            else:
                return False, item.folder_name

        return sorted(items, key=sort_key)

    @staticmethod
    def _get_user_identifier(request: Request) -> str:
        user_identifier = request.scope.get("user")
        if not user_identifier and request.client:
            user_identifier = request.client.host
        return (
            str(user_identifier) if user_identifier is not None else "Unknown"
        )
