import logging
from datetime import datetime
from typing import List, Optional

from fastapi import UploadFile, Request

from src.core.storage.exceptions import ErrorSavingFile
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

    async def upload(
        self, file: UploadFile, request: Request, *args, **kwargs
    ) -> FileDataSchema:
        """Upload a single file to storage"""
        try:
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
        except Exception as e:
            logger.error(f"Failed to upload file {file.filename}", e)
            raise ErrorSavingFile(
                f"Failed to upload file {file.filename}: {e}"
            )

    async def multi_upload(
        self, files: List[UploadFile], request: Request, *args, **kwargs
    ) -> List[FileDataSchema]:
        """Upload multiple files to storage"""
        results = []
        for file in files:
            result = await self.upload(file, request)
            results.append(result)
        return results

    async def delete(
        self, file_path: str, request: Request, *args, **kwargs
    ) -> FileDeleteSchema:
        """Delete a file from storage"""
        try:
            self._cloud_storage.delete_blob(file_path)
            return FileDeleteSchema(
                file=file_path,
                message="File deleted successfully",
                status_code=200,
                date_deleted=datetime.now().isoformat(),
                deleted_by=self._get_user_identifier(request),
            )
        except ErrorSavingFile as e:
            if "not found" in str(e):
                return FileDeleteSchema(
                    file=file_path,
                    message="File not found",
                    status_code=404,
                    date_deleted=datetime.now().isoformat(),
                    deleted_by=self._get_user_identifier(request),
                )
            raise

    async def create_folder(
        self, folder_path: str, request: Request, *args, **kwargs
    ) -> FolderDataSchema:
        """Create a new folder in storage"""
        try:
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
        except Exception as e:
            logger.error(f"Failed to create folder {folder_path}", e)
            raise ErrorSavingFile(
                f"Failed to create folder {folder_path}: {e}"
            )

    async def rename_folder(
        self, old_path: str, new_path: str, request: Request, *args, **kwargs
    ) -> FolderDataSchema:
        """Rename a folder in storage"""
        try:
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
        except Exception as e:
            logger.error(
                f"Failed to rename folder from {old_path} to {new_path}", e
            )
            raise ErrorSavingFile(
                f"Failed to rename folder from {old_path} to {new_path}: {e}"
            )

    async def delete_folder(
        self, folder_path: str, request: Request, *args, **kwargs
    ) -> FolderDeleteSchema:
        """Delete a folder and all its contents from storage"""
        try:
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
        except Exception as e:
            logger.error(f"Failed to delete folder {folder_path}", e)
            raise ErrorSavingFile(
                f"Failed to delete folder {folder_path}: {e}"
            )

    async def rename_file(
        self, old_path: str, new_path: str, request: Request, *args, **kwargs
    ) -> FileDataSchema:
        """Rename a file in storage"""
        try:
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
        except Exception as e:
            logger.error(
                f"Failed to rename file from {old_path} to {new_path}", e
            )
            raise ErrorSavingFile(
                f"Failed to rename file from {old_path} to {new_path}: {e}"
            )

    async def upload_file(
        self, file_path: str, destination_path: Optional[str] = None
    ) -> str:
        """
        Upload file to cloud storage

        Args:
            file_path: Path to file to upload
            destination_path: Optional destination path in cloud storage

        Returns:
            str: URL of uploaded file
        """
        if not file_path:
            raise ValueError("File path cannot be empty")

        destination = destination_path or self._path_handler.get_basename(
            file_path
        )
        return self._cloud_storage.upload_blob(file_path, destination)
