import logging
from datetime import datetime
from typing import List, Optional

from fastapi import UploadFile, Request

from src.core.storage.decorators import (
    handle_upload_file_exceptions,
    handle_delete_file_exceptions,
)
from src.core.storage.implementations.google_storage import GoogleCloudStorage
from src.core.storage.interfaces.base_storage_interface import (
    BaseStorageInterface,
)
from src.core.storage.interfaces.cloud_storage_interface import (
    CloudStorageInterface,
)
from src.core.storage.shemas import (
    FileDataSchema,
    FileDeleteSchema,
    FolderDataSchema,
    FolderDeleteSchema,
)
from src.utils.path_handler import PathHandler
from src.core.exceptions.storage import ErrorSavingFile

logger = logging.getLogger(__name__)


class CloudStorage(BaseStorageInterface):
    def __init__(
        self,
        bucket_name: str,
        path_handler: Optional[PathHandler] = None,
        cloud_storage: Optional[CloudStorageInterface] = None,
    ):
        """
        Initialize Cloud Storage client

        Args:
            bucket_name: Name of the storage bucket
            path_handler: Utility for path operations
            cloud_storage: Cloud storage implementation
        """
        self.bucket_name = bucket_name
        self._path_handler = path_handler or PathHandler()
        self._cloud_storage = cloud_storage or GoogleCloudStorage(
            bucket_name=bucket_name,
        )
        self.base_url = f"https://storage.googleapis.com/{bucket_name}"

    @staticmethod
    def _get_user_identifier(request: Request) -> str:
        """Get user identifier from request"""
        user_identifier = request.scope.get("user")
        if not user_identifier and request.client:
            user_identifier = request.client.host
        return (
            str(user_identifier) if user_identifier is not None else "Unknown"
        )

    @handle_upload_file_exceptions
    async def upload(
        self, file: UploadFile, request: Request, *args, **kwargs
    ) -> FileDataSchema:
        """Upload a single file to storage"""
        content = await file.read()
        if not file.filename:
            raise ValueError("File name cannot be empty")

        blob_url = self._cloud_storage.upload_blob(
            file.filename, content, file.content_type
        )

        return FileDataSchema(
            path=file.filename,
            url=blob_url,
            filename=file.filename,
            content_type=file.content_type,
            size=len(content),
            status_code=200,
            message="File uploaded successfully",
            date_created=datetime.now().isoformat(),
            creator=self._get_user_identifier(request),
        )

    @handle_upload_file_exceptions
    async def multi_upload(
        self, files: List[UploadFile], request: Request, *args, **kwargs
    ) -> List[FileDataSchema]:
        """Upload multiple files to storage"""
        results = []
        for file in files:
            result = await self.upload(file, request)
            results.append(result)
        return results

    @handle_delete_file_exceptions
    async def delete(
        self, file_path: str, request: Request, *args, **kwargs
    ) -> FileDeleteSchema:
        """Delete a file from storage"""
        self._cloud_storage.delete_blob(file_path)
        return FileDeleteSchema(
            file=file_path,
            message="File deleted successfully",
            status_code=200,
            date_deleted=datetime.now().isoformat(),
            deleted_by=self._get_user_identifier(request),
        )

    @handle_upload_file_exceptions
    async def create_folder(
        self, folder_path: str, request: Request, *args, **kwargs
    ) -> FolderDataSchema:
        """Create a new folder in storage"""
        folder_path = self._path_handler.normalize_path(folder_path)
        self._cloud_storage.upload_blob(folder_path, b"")
        parent_folder = self._path_handler.get_parent_folder(folder_path)

        return FolderDataSchema(
            path=folder_path,
            name=self._path_handler.get_basename(folder_path),
            status_code=200,
            message="Folder created successfully",
            date_created=datetime.now().isoformat(),
            creator=self._get_user_identifier(request),
            parent_folder=parent_folder,
            is_empty=True,
        )

    @handle_upload_file_exceptions
    async def rename_folder(
        self, old_path: str, new_path: str, request: Request, *args, **kwargs
    ) -> FolderDataSchema:
        """Rename a folder in storage"""
        old_path = self._path_handler.normalize_path(old_path)
        new_path = self._path_handler.normalize_path(new_path)

        blobs = self._cloud_storage.list_blobs(prefix=old_path)
        for blob in blobs:
            new_name = blob.name.replace(old_path, new_path, 1)
            self._cloud_storage.copy_blob(blob, new_name)
            self._cloud_storage.delete_blob(blob.name)

        parent_folder = self._path_handler.get_parent_folder(new_path)

        return FolderDataSchema(
            path=new_path,
            name=self._path_handler.get_basename(new_path),
            status_code=200,
            message="Folder renamed successfully",
            date_created=datetime.now().isoformat(),
            creator=self._get_user_identifier(request),
            parent_folder=parent_folder,
            is_empty=not any(blobs),
        )

    @handle_delete_file_exceptions
    async def delete_folder(
        self, folder_path: str, request: Request, *args, **kwargs
    ) -> FolderDeleteSchema:
        """Delete a folder and all its contents from storage"""
        folder_path = self._path_handler.normalize_path(folder_path)
        blobs = self._cloud_storage.list_blobs(prefix=folder_path)
        deleted_files = len(blobs)

        for blob in blobs:
            self._cloud_storage.delete_blob(blob.name)

        return FolderDeleteSchema(
            folder=folder_path,
            message="Folder and its contents deleted successfully",
            status_code=200,
            date_deleted=datetime.now().isoformat(),
            deleted_by=self._get_user_identifier(request),
            deleted_files_count=deleted_files,
        )

    @handle_upload_file_exceptions
    async def rename_file(
        self, old_path: str, new_path: str, request: Request, *args, **kwargs
    ) -> FileDataSchema:
        """Rename a file in storage"""
        old_blob = self._cloud_storage.get_bucket().blob(old_path)
        new_blob = self._cloud_storage.copy_blob(old_blob, new_path)
        self._cloud_storage.delete_blob(old_path)

        return FileDataSchema(
            path=new_path,
            url=f"{self.base_url}/{new_path}",
            filename=self._path_handler.get_basename(new_path),
            content_type=new_blob.content_type,
            size=new_blob.size,
            status_code=200,
            message="File renamed successfully",
            date_created=datetime.now().isoformat(),
            creator=self._get_user_identifier(request),
        )

    @handle_upload_file_exceptions
    async def upload_file(
        self, file_path: str, destination_path: Optional[str] = None
    ) -> str:
        if not file_path:
            raise ValueError("File path cannot be empty")

        destination = destination_path or self._path_handler.get_basename(
            file_path
        )
        return self._cloud_storage.upload_blob(file_path, destination)

    async def get_file(self, file_path: str) -> FileDataSchema:
        """Get file by path"""
        blob = self._cloud_storage.get_bucket().blob(file_path)
        if not blob.exists():
            raise ErrorSavingFile(f"File {file_path} not found")

        return FileDataSchema(
            path=file_path,
            url=f"{self.base_url}/{file_path}",
            filename=self._path_handler.get_basename(file_path),
            content_type=blob.content_type,
            size=blob.size,
            status_code=200,
            message="File retrieved successfully",
            date_created=(
                blob.time_created.isoformat() if blob.time_created else None
            ),
            creator="",
        )

    async def list_files(
        self, prefix: Optional[str] = None
    ) -> List[FileDataSchema]:
        """List all files in storage"""
        blobs = self._cloud_storage.list_blobs(prefix=prefix)
        files = []

        for blob in blobs:
            if not blob.name.endswith("/"):  # Skip folders
                files.append(
                    FileDataSchema(
                        path=blob.name,
                        url=f"{self.base_url}/{blob.name}",
                        filename=self._path_handler.get_basename(blob.name),
                        content_type=blob.content_type,
                        size=blob.size,
                        status_code=200,
                        message="File listed successfully",
                        date_created=(
                            blob.time_created.isoformat()
                            if blob.time_created
                            else None
                        ),
                        creator="",
                    )
                )

        return files

    async def list_folders(
        self, prefix: Optional[str] = None
    ) -> List[FolderDataSchema]:
        """List all folders in storage"""
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
                date_created=None,
                parent_folder=self._path_handler.get_parent_folder(
                    folder_path
                ),
                is_empty=False,  # We don't have this information in GCS
            )
            for folder_path in sorted(folders)
        ]

    async def get_folder_contents(self, folder_path: str) -> dict:
        """Get contents of a specific folder"""
        if folder_path and not folder_path.endswith("/"):
            folder_path += "/"

        blobs = self._cloud_storage.list_blobs(prefix=folder_path)
        files = []
        folders = set()

        for blob in blobs:
            relative_path = (
                blob.name[len(folder_path) :] if folder_path else blob.name
            )
            if not relative_path:
                continue

            parts = relative_path.split("/")
            if len(parts) == 1:
                # This is a file in the current directory
                files.append(
                    {
                        "name": parts[0],
                        "path": blob.name,
                        "size": blob.size,
                        "updated": (
                            blob.updated.isoformat() if blob.updated else None
                        ),
                        "type": "file",
                    }
                )
            else:
                # This is a folder
                folder_path = (
                    f"{folder_path}/{parts[0]}" if folder_path else parts[0]
                )
                if folder_path not in folders:
                    folders.add(folder_path)

        folder_items = [
            {
                "name": self._path_handler.get_basename(folder_path),
                "path": folder_path,
                "type": "folder",
            }
            for folder_path in sorted(folders)
        ]

        return {
            "current_path": folder_path.rstrip("/") if folder_path else "",
            "items": sorted(
                folder_items + files,
                key=lambda x: (x["type"] == "file", x["name"]),
            ),
        }
