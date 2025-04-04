import asyncio
import logging
from typing import List, Optional, Union, Set, Tuple

from fastapi import UploadFile, Request, status, HTTPException
from google.cloud.storage import Blob  # type: ignore
from google.cloud.storage_control_v2 import RenameFolderRequest  # type: ignore

from src.core.exceptions.storage import ErrorSavingFile
from src.core.storage.decorators import (
    handle_upload_file_exceptions,
    handle_delete_file_exceptions,
)
from src.core.storage.implementations.google_storage import GoogleCloudStorage
from src.core.storage.interfaces.base_storage_interface import (
    BaseStorageInterface,
    log_operation,
)
from src.core.storage.interfaces.cloud_storage_interface import (
    CloudStorageInterface,
)
from src.core.storage.shemas import (
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
        log_operation(f"Blob {blob_name} not found", "warning")
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
        log_operation(f"Blob {blob_name} already exists", "warning")
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
        request: Request,
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
        request: Request,
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
        new_path: str,
        request: Request,
        *args,
        **kwargs,
    ) -> FileSchema:
        old_blob = self._cloud_storage.bucket.blob(old_path)
        if not old_blob.exists():
            raise ErrorSavingFile(f"Source file {old_path} does not exist")

        new_blob = await self._cloud_storage.copy_blob(old_blob, new_path)
        await self._cloud_storage.delete_blob(old_path)

        return FileSchema(
            url=f"{self._cloud_storage.base_url}/{new_path}",
            filename=self._path_handler.get_basename(new_path),
            content_type=new_blob.content_type,
            size=new_blob.size,
        )

    @handle_upload_file_exceptions
    async def delete_all_files(
        self,
        prefix: str,
        request: Request,
        *args,
        **kwargs,
    ) -> List[FileDeleteSchema]:
        blobs: List[Blob] = await self._cloud_storage.list_blobs(prefix=prefix)
        tasks = [self.delete_file(blob.name, request) for blob in blobs]
        return await asyncio.gather(*tasks)

    @handle_upload_file_exceptions
    async def create_folder(
        self,
        folder_path: str,
        request: Request,
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
        request: Request,
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
        request: Request,
        *args,
        **kwargs,
    ) -> FolderDeleteSchema:
        """Delete folder and all its contents"""
        folder_path = self._path_handler.normalize_path(folder_path)
        _validate_blob_exists(self._cloud_storage, folder_path)

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
        blob = self._cloud_storage.bucket.blob(file_path)
        if not blob.exists():
            raise ErrorSavingFile(f"File {file_path} not found")

        return FileSchema(
            filename=blob.name,
            url=blob.public_url,
            size=blob.size,
            content_type=blob.content_type,
        )

    async def list_files(
        self,
        prefix: Optional[str] = "",
    ) -> List[FileSchema]:
        blobs: List[Blob] = await self._cloud_storage.list_blobs(prefix=prefix)
        files: List[FileSchema] = []

        files.extend(
            FileSchema(
                filename=self._path_handler.get_basename(blob.name),
                url=blob.public_url,
                content_type=blob.content_type,
                size=blob.size,
            )
            for blob in blobs
        )

        return files

    async def list_folders(
        self,
        prefix: Optional[str] = None,
    ) -> List[FolderDataSchema]:
        """List managed folders"""
        folders = await self._cloud_storage.list_folders(prefix=prefix)
        return [
            FolderDataSchema(
                folder_name=folder.folder_name,
                folder_path=folder.folder_name,
                create_time=None,
                update_time=None,
            )
            for folder in folders
        ]

    @staticmethod
    def _normalize_folder_path(folder_path: str) -> str:
        if folder_path and not folder_path.endswith("/"):
            folder_path += "/"
        return folder_path

    @staticmethod
    def _get_relative_path(blob_name: str, folder_path: str) -> str:
        return blob_name[len(folder_path) :] if folder_path else blob_name

    @staticmethod
    def _process_file_item(
        filename: str,
        url: str,
        size: int,
        content_type: Optional[str] = None,
    ) -> FileSchemaForFolder:
        return FileSchemaForFolder(
            filename=filename,
            url=url,
            type="file",
            size=size,
            content_type=content_type,
        )

    def _process_folder_item(self, folder_path: str) -> FolderItem:
        return FolderItem(
            folder_name=self._path_handler.get_basename(folder_path),
            folder_path=folder_path,
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

    async def get_folder_contents(
        self, folder_path: str
    ) -> FolderContentsSchema:
        folder_path = self._normalize_folder_path(folder_path)
        blobs: List[Blob] = await self._cloud_storage.list_blobs(
            prefix=folder_path
        )
        files: List[FileSchemaForFolder] = []
        folders: Set[str] = set()

        for blob in blobs:
            relative_path = self._get_relative_path(blob.name, folder_path)
            if not relative_path:
                continue

            parts = relative_path.split("/")
            if len(parts) == 1:
                files.append(
                    self._process_file_item(
                        filename=parts[0],
                        url=blob.public_url,
                        size=blob.size,
                        content_type=blob.content_type,
                    )
                )
            else:
                current_folder_path = (
                    f"{folder_path}/{parts[0]}" if folder_path else parts[0]
                )
                if current_folder_path not in folders:
                    folders.add(current_folder_path)

        folder_items = [
            self._process_folder_item(folder_path)
            for folder_path in sorted(folders)
        ]

        all_items: List[Union[FileSchemaForFolder, FolderItem]] = [
            *folder_items,
            *files,
        ]

        return FolderContentsSchema(
            current_path=folder_path.rstrip("/") if folder_path else "",
            items=self._sort_folder_items(all_items),
        )

    async def search_files_by_name(
        self,
        search_query: str,
        case_sensitive: bool = False,
    ) -> List[FileSchema]:
        blobs: List[Blob] = await self._cloud_storage.list_blobs()
        if not case_sensitive:
            search_query = search_query.lower()

        matching_files: List[FileSchema] = []
        for blob in blobs:
            blob_name = blob.name
            if not case_sensitive:
                blob_name = blob_name.lower()

            if search_query in blob_name:
                matching_files.append(
                    FileSchema(
                        filename=self._path_handler.get_basename(blob.name),
                        url=blob.public_url,
                        content_type=blob.content_type,
                        size=blob.size,
                    )
                )

        return matching_files

    @staticmethod
    def _get_user_identifier(request: Request) -> str:
        user_identifier = request.scope.get("user")
        if not user_identifier and request.client:
            user_identifier = request.client.host
        return (
            str(user_identifier) if user_identifier is not None else "Unknown"
        )
