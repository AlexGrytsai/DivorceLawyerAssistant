import logging
from datetime import datetime
from typing import List, Optional, Union, Set, Tuple

from fastapi import UploadFile, Request, status, HTTPException

from src.core.exceptions.storage import ErrorSavingFile
from src.core.storage.decorators import (
    handle_upload_file_exceptions,
    handle_delete_file_exceptions,
)
from src.core.storage.implementations.google_storage import GoogleCloudStorage
from src.core.storage.interfaces.base_storage_interface import (
    BaseStorageInterface,
    current_timestamp,
    log_operation,
)
from src.core.storage.interfaces.cloud_storage_interface import (
    CloudStorageInterface,
)
from src.core.storage.shemas import (
    FileDataSchema,
    FileDeleteSchema,
    FolderDataSchema,
    FolderDeleteSchema,
    FileItem,
    FolderItem,
    FolderContents,
)
from src.utils.path_handler import PathHandler

logger = logging.getLogger(__name__)


def _validate_blob_exists(
    cloud_storage: CloudStorageInterface,
    blob_name: str,
    error_code: int = status.HTTP_404_NOT_FOUND,
) -> None:
    """Validate that blob exists in cloud storage"""
    if not cloud_storage.get_bucket.blob(blob_name).exists():
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
    if cloud_storage.get_bucket.blob(blob_name).exists():
        log_operation(f"Blob {blob_name} already exists", "warning")
        raise HTTPException(
            status_code=error_code,
            detail={
                "error": "Blob already exists",
                "message": f"{blob_name} already exists",
            },
        )


class CloudStorage(BaseStorageInterface):
    BASE_STORAGE_CLOUD_URL = "https://storage.googleapis.com"

    def __init__(
        self,
        project_id: str,
        bucket_name: str,
        path_handler: Optional[PathHandler] = None,
        cloud_storage: Optional[CloudStorageInterface] = None,
    ):

        self.bucket_name = bucket_name
        self._path_handler = path_handler or PathHandler()
        self._cloud_storage = cloud_storage or GoogleCloudStorage(
            project_id=project_id,
            bucket_name=bucket_name,
        )
        self.base_url = f"{self.BASE_STORAGE_CLOUD_URL}/{bucket_name}"

    @handle_upload_file_exceptions
    async def upload(
        self,
        file: UploadFile,
        request: Request,
        *args,
        **kwargs,
    ) -> FileDataSchema:
        content = await file.read()
        if not file.filename:
            raise ValueError("File name cannot be empty")

        blob_url = self._cloud_storage.upload_blob(
            file.filename, content, file.content_type
        )

        return FileDataSchema(
            url=blob_url,
            filename=file.filename,
            content_type=file.content_type,
            size=len(content),
            message=f"File {file.filename} uploaded successfully",
        )

    @handle_upload_file_exceptions
    async def multi_upload(
        self,
        files: List[UploadFile],
        request: Request,
        *args,
        **kwargs,
    ) -> List[FileDataSchema]:
        results = []
        for file in files:
            result = await self.upload(file, request)
            results.append(result)
        return results

    @handle_delete_file_exceptions
    async def delete(
        self,
        file_path: str,
        request: Request,
        *args,
        **kwargs,
    ) -> FileDeleteSchema:
        self._cloud_storage.delete_blob(file_path)
        return FileDeleteSchema(
            file=file_path,
            message=f"File {file_path} deleted successfully",
            date_deleted=datetime.now().isoformat(),
            deleted_by=self._get_user_identifier(request),
        )

    @handle_upload_file_exceptions
    async def create_folder(
        self,
        folder_path: str,
        request: Request,
        *args,
        **kwargs,
    ) -> FolderDataSchema:
        """Create a new folder in storage"""
        folder_path = self._path_handler.normalize_path(folder_path)
        _validate_blob_not_exists(self._cloud_storage, folder_path)

        self._cloud_storage.upload_blob(folder_path, b"")
        parent_folder = self._path_handler.get_parent_folder(folder_path)
        log_operation(f"Folder {folder_path} created successfully")

        return FolderDataSchema(
            path=folder_path,
            name=self._path_handler.get_basename(folder_path),
            message=f"Folder {folder_path} created successfully",
            parent_folder=parent_folder,
            is_empty=True,
        )

    @handle_upload_file_exceptions
    async def rename_folder(
        self,
        old_path: str,
        new_path: str,
        request: Request,
        *args,
        **kwargs,
    ) -> FolderDataSchema:
        """Rename existing folder"""
        old_path = self._path_handler.normalize_path(old_path)
        new_path = self._path_handler.normalize_path(new_path)

        _validate_blob_exists(self._cloud_storage, old_path)
        _validate_blob_not_exists(self._cloud_storage, new_path)

        blobs = self._cloud_storage.list_blobs(prefix=old_path)
        for blob in blobs:
            new_name = blob.name.replace(old_path, new_path, 1)
            self._cloud_storage.copy_blob(blob, new_name)
            self._cloud_storage.delete_blob(blob.name)

        parent_folder = self._path_handler.get_parent_folder(new_path)
        log_operation(f"Folder renamed from {old_path} to {new_path}")

        return FolderDataSchema(
            path=new_path,
            name=self._path_handler.get_basename(new_path),
            status_code=status.HTTP_200_OK,
            message=f"Folder renamed from {old_path} to {new_path}",
            creator=self._get_user_identifier(request),
            parent_folder=parent_folder,
            is_empty=not any(blobs),
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

        blobs = self._cloud_storage.list_blobs(prefix=folder_path)
        deleted_files = len(blobs)

        for blob in blobs:
            self._cloud_storage.delete_blob(blob.name)

        log_operation(f"Folder {folder_path} deleted successfully")
        return FolderDeleteSchema(
            folder=folder_path,
            message=f"Folder {folder_path} deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT,
            date_deleted=current_timestamp(),
            deleted_by=self._get_user_identifier(request),
            deleted_files_count=deleted_files,
        )

    @handle_upload_file_exceptions
    async def rename_file(
        self,
        old_path: str,
        new_path: str,
        request: Request,
        *args,
        **kwargs,
    ) -> FileDataSchema:
        old_blob = self._cloud_storage.get_bucket.blob(old_path)
        if not old_blob.exists():
            raise ErrorSavingFile(f"Source file {old_path} does not exist")

        new_blob = self._cloud_storage.copy_blob(old_blob, new_path)
        self._cloud_storage.delete_blob(old_path)

        return FileDataSchema(
            url=f"{self.base_url}/{new_path}",
            filename=self._path_handler.get_basename(new_path),
            content_type=new_blob.content_type,
            size=new_blob.size,
            status_code=200,
            message="File renamed successfully",
            creator=self._get_user_identifier(request),
        )

    @handle_upload_file_exceptions
    async def upload_file(
        self,
        file_path: str,
        destination_path: Optional[str] = None,
    ) -> str:
        if not file_path:
            raise ValueError("File path cannot be empty")

        destination = destination_path or self._path_handler.get_basename(
            file_path
        )
        return self._cloud_storage.upload_blob(file_path, destination)

    async def get_file(self, file_path: str) -> FileDataSchema:
        blob = self._cloud_storage.get_bucket.blob(file_path)
        if not blob.exists():
            raise ErrorSavingFile(f"File {file_path} not found")

        return FileDataSchema(
            url=f"{self.base_url}/{file_path}",
            filename=self._path_handler.get_basename(file_path),
            content_type=blob.content_type,
            size=blob.size,
            status_code=200,
            message="File retrieved successfully",
            creator="",
        )

    async def list_files(
        self,
        prefix: Optional[str] = "",
    ) -> List[FileDataSchema]:
        blobs = self._cloud_storage.list_blobs(prefix=prefix)
        files: List[FileDataSchema] = []

        files.extend(
            FileDataSchema(
                filename=self._path_handler.get_basename(blob.name),
                url=f"{self.base_url}/{blob.name}",
                content_type=blob.content_type,
                size=blob.size,
                status_code=200,
                message="File listed successfully",
                creator="",
            )
            for blob in blobs
            if not blob.name.endswith("/")
        )
        return files

    async def list_folders(
        self,
        prefix: Optional[str] = None,
    ) -> List[FolderDataSchema]:
        blobs = self._cloud_storage.list_blobs(prefix=prefix)
        folders = set()

        for blob in blobs:
            parts = blob.name.split("/")
            if len(parts) > 1:  # Skip root level files
                folder_path = "/".join(parts[:-1])
                if folder_path not in folders:
                    folders.add(folder_path)

        return [
            FolderDataSchema(
                path=folder_path,
                name=self._path_handler.get_basename(folder_path),
                status_code=200,
                message="Folder listed successfully",
                parent_folder=self._path_handler.get_parent_folder(
                    folder_path
                ),
                is_empty=False,  # We don't have this information in GCS
            )
            for folder_path in sorted(folders)
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
        name: str, path: str, size: int, updated: Optional[datetime]
    ) -> FileItem:
        return FileItem(
            name=name,
            path=path,
            type="file",
            size=size,
            updated=updated.isoformat() if updated else None,
        )

    def _process_folder_item(self, folder_path: str) -> FolderItem:
        return FolderItem(
            name=self._path_handler.get_basename(folder_path),
            path=folder_path,
            type="folder",
        )

    @staticmethod
    def _sort_folder_items(
        items: List[Union[FileItem, FolderItem]],
    ) -> List[Union[FileItem, FolderItem]]:
        def sort_key(item: Union[FileItem, FolderItem]) -> Tuple[bool, str]:
            is_file = isinstance(item, FileItem)
            name = item.name or ""
            return is_file, name

        return sorted(items, key=sort_key)

    async def get_folder_contents(self, folder_path: str) -> FolderContents:
        folder_path = self._normalize_folder_path(folder_path)
        blobs = self._cloud_storage.list_blobs(prefix=folder_path)
        files: List[FileItem] = []
        folders: Set[str] = set()

        for blob in blobs:
            relative_path = self._get_relative_path(blob.name, folder_path)
            if not relative_path:
                continue

            parts = relative_path.split("/")
            if len(parts) == 1:
                files.append(
                    self._process_file_item(
                        name=parts[0],
                        path=blob.name,
                        size=blob.size,
                        updated=blob.updated,
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

        all_items: List[Union[FileItem, FolderItem]] = [*folder_items, *files]

        return FolderContents(
            current_path=folder_path.rstrip("/") if folder_path else "",
            items=self._sort_folder_items(all_items),
        )

    async def search_files_by_name(
        self,
        search_query: str,
        case_sensitive: bool = False,
    ) -> List[FileDataSchema]:
        blobs = self._cloud_storage.list_blobs()
        files = []

        search_query = search_query if case_sensitive else search_query.lower()

        for blob in blobs:
            if not blob.name.endswith("/"):  # Skip folders
                filename = self._path_handler.get_basename(blob.name)
                if not case_sensitive:
                    filename = filename.lower()

                if search_query in filename:
                    files.append(
                        FileDataSchema(
                            filename=self._path_handler.get_basename(
                                blob.name
                            ),
                            url=f"{self.base_url}/{blob.name}",
                            content_type=blob.content_type,
                            size=blob.size,
                            status_code=200,
                            message="File found successfully",
                            creator="",
                        )
                    )

        return sorted(files, key=lambda x: x.filename or "")

    @staticmethod
    def _get_user_identifier(request: Request) -> str:
        user_identifier = request.scope.get("user")
        if not user_identifier and request.client:
            user_identifier = request.client.host
        return (
            str(user_identifier) if user_identifier is not None else "Unknown"
        )
