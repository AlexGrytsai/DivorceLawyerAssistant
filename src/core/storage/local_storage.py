import asyncio
import datetime
import logging
import os
import urllib
from pathlib import Path
from typing import List, Optional

from fastapi import UploadFile, Request, status, HTTPException

from src.core.storage.decorators import (
    handle_upload_file_exceptions,
    handle_delete_file_exceptions,
)
from src.core.storage.interfaces.base_storage_interface import (
    BaseStorageInterface,
)
from src.core.storage.shemas import (
    FileDataSchema,
    FileDeleteSchema,
    FolderDataSchema,
    FolderDeleteSchema,
)
from src.core.exceptions.storage import ErrorSavingFile

logger = logging.getLogger(__name__)


class LocalStorage(BaseStorageInterface):
    __slots__ = ("_path_to_storage",)

    def __init__(self, path_to_upload_dir: str) -> None:
        self._path_to_storage = path_to_upload_dir

    @handle_upload_file_exceptions
    async def upload(
        self,
        file: UploadFile,
        request: Request,
        *args,
        **kwargs,
    ) -> FileDataSchema:
        file_object = await file.read()

        file_path = os.path.join(
            self._create_directory(request), file.filename or "file"
        )

        with open(file_path, "wb") as fh:
            fh.write(file_object)
        await file.close()

        return FileDataSchema(
            path=file_path,
            url=self._create_url_path(file_path, request),
            message=f"{file.filename} saved successfully",
            content_type=file.content_type,
            size=file.size,
            filename=file.filename,
            status_code=status.HTTP_201_CREATED,
            date_created=datetime.datetime.now().strftime("%H:%M:%S %m-%d-%Y"),
            creator=self._get_user_identifier(request),
        )

    async def multi_upload(
        self,
        files: List[UploadFile],
        request: Request,
        *args,
        **kwargs,
    ) -> List[FileDataSchema]:
        uploaded = await asyncio.gather(
            *[self.upload(file=file, request=request) for file in files]
        )
        return list(uploaded)

    @handle_delete_file_exceptions
    async def delete(
        self, file_path: str, request: Request, *args, **kwargs
    ) -> FileDeleteSchema:
        if Path(file_path).exists():
            os.remove(Path(file_path))
            logger.info(f"{file_path} deleted successfully")

            return FileDeleteSchema(
                file=file_path,
                message=f"{file_path} deleted successfully",
                status_code=status.HTTP_204_NO_CONTENT,
                date_deleted=datetime.datetime.now().strftime(
                    "%H:%M:%S %m-%d-%Y"
                ),
                deleted_by=self._get_user_identifier(request),
            )
        else:
            logger.warning(
                f"{file_path} not found in {self._path_to_storage} "
                f"for deletion"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "File not found",
                    "message": f"{file_path} not found",
                },
            )

    @handle_delete_file_exceptions
    async def delete_folder(
        self, folder_path: str, request: Request, *args, **kwargs
    ) -> FolderDeleteSchema:
        """Delete a folder and all its contents"""
        folder = Path(folder_path)
        if folder.exists():
            deleted_files = 0
            for root, dirs, files in os.walk(folder, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                    deleted_files += 1
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(folder)

            logger.info(f"{folder_path} deleted successfully")
            return FolderDeleteSchema(
                folder=folder_path,
                message=f"{folder_path} deleted successfully",
                status_code=status.HTTP_204_NO_CONTENT,
                date_deleted=datetime.datetime.now().strftime(
                    "%H:%M:%S %m-%d-%Y"
                ),
                deleted_by=self._get_user_identifier(request),
                deleted_files_count=deleted_files,
            )
        else:
            logger.warning(
                f"{folder_path} not found in {self._path_to_storage} "
                f"for deletion"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Folder not found",
                    "message": f"{folder_path} not found",
                },
            )

    @handle_upload_file_exceptions
    async def create_folder(
        self, folder_path: str, request: Request, *args, **kwargs
    ) -> FolderDataSchema:
        """Create a new folder in storage"""
        folder = Path(folder_path)
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Folder {folder_path} created successfully")

            return FolderDataSchema(
                path=str(folder),
                name=folder.name,
                status_code=status.HTTP_201_CREATED,
                message=f"Folder {folder_path} created successfully",
                date_created=datetime.datetime.now().strftime(
                    "%H:%M:%S %m-%d-%Y"
                ),
                creator=self._get_user_identifier(request),
                parent_folder=str(folder.parent),
                is_empty=True,
            )
        else:
            logger.warning(f"Folder {folder_path} already exists")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Folder already exists",
                    "message": f"Folder {folder_path} already exists",
                },
            )

    @handle_upload_file_exceptions
    async def rename_folder(
        self, old_path: str, new_path: str, request: Request, *args, **kwargs
    ) -> FolderDataSchema:
        """Rename existing folder"""
        old_folder = Path(old_path)
        new_folder = Path(new_path)

        if old_folder.exists():
            if not new_folder.exists():
                old_folder.rename(new_folder)
                logger.info(f"Folder renamed from {old_path} to {new_path}")

                return FolderDataSchema(
                    path=str(new_folder),
                    name=new_folder.name,
                    status_code=status.HTTP_200_OK,
                    message=f"Folder renamed from {old_path} to {new_path}",
                    date_created=datetime.datetime.now().strftime(
                        "%H:%M:%S %m-%d-%Y"
                    ),
                    creator=self._get_user_identifier(request),
                    parent_folder=str(new_folder.parent),
                    is_empty=not any(new_folder.iterdir()),
                )
            else:
                logger.warning(f"Target folder {new_path} already exists")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": "Target folder exists",
                        "message": f"Target folder {new_path} already exists",
                    },
                )
        else:
            logger.warning(f"Source folder {old_path} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Source folder not found",
                    "message": f"Source folder {old_path} not found",
                },
            )

    @handle_upload_file_exceptions
    async def rename_file(
        self, old_path: str, new_path: str, request: Request, *args, **kwargs
    ) -> FileDataSchema:
        """Rename existing file"""
        old_file = Path(old_path)
        new_file = Path(new_path)

        if old_file.exists():
            if not new_file.exists():
                old_file.rename(new_file)
                logger.info(f"File renamed from {old_path} to {new_path}")

                return FileDataSchema(
                    path=str(new_file),
                    url=self._create_url_path(str(new_file), request),
                    filename=new_file.name,
                    status_code=status.HTTP_200_OK,
                    message=f"File renamed from {old_path} to {new_path}",
                    date_created=datetime.datetime.now().strftime(
                        "%H:%M:%S %m-%d-%Y"
                    ),
                    creator=self._get_user_identifier(request),
                )
            else:
                logger.warning(f"Target file {new_path} already exists")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": "Target file exists",
                        "message": f"Target file {new_path} already exists",
                    },
                )
        else:
            logger.warning(f"Source file {old_path} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Source file not found",
                    "message": f"Source file {old_path} not found",
                },
            )

    @handle_upload_file_exceptions
    async def get_file(
        self,
        file_path: str,
        request: Request,
    ) -> FileDataSchema:
        """Get file by path"""
        file = Path(file_path)
        if not file.exists():
            raise ErrorSavingFile(f"File {file_path} not found")

        return FileDataSchema(
            path=str(file),
            url=self._create_url_path(str(file), request),
            filename=file.name,
            content_type=None,
            size=file.stat().st_size,
            status_code=200,
            message="File retrieved successfully",
            date_created=datetime.datetime.fromtimestamp(
                file.stat().st_ctime
            ).isoformat(),
            creator="",
        )

    @handle_upload_file_exceptions
    async def list_files(
        self,
        request: Request,
        prefix: Optional[str] = None,
    ) -> List[FileDataSchema]:
        """List all files in storage"""
        storage_path = Path(self._path_to_storage)
        if prefix:
            storage_path = storage_path / prefix

        files = []
        for file_path in storage_path.rglob("*"):
            if file_path.is_file():
                created_time = datetime.datetime.fromtimestamp(
                    file_path.stat().st_ctime
                ).isoformat()
                file_data = FileDataSchema(
                    path=str(file_path),
                    url=self._create_url_path(str(file_path), request),
                    filename=file_path.name,
                    content_type=None,
                    size=file_path.stat().st_size,
                    status_code=200,
                    message="File listed successfully",
                    date_created=created_time,
                    creator="",
                )
                files.append(file_data)

        return files

    @handle_upload_file_exceptions
    async def list_folders(
        self, prefix: Optional[str] = None
    ) -> List[FolderDataSchema]:
        """List all folders in storage"""
        storage_path = Path(self._path_to_storage)
        if prefix:
            storage_path = storage_path / prefix

        folders = []
        for folder_path in storage_path.rglob("*"):
            if folder_path.is_dir():
                created_time = datetime.datetime.fromtimestamp(
                    folder_path.stat().st_ctime
                ).isoformat()
                folder_data = FolderDataSchema(
                    path=str(folder_path),
                    name=folder_path.name,
                    status_code=200,
                    message="Folder listed successfully",
                    date_created=created_time,
                    creator="",
                    parent_folder=str(folder_path.parent),
                    is_empty=not any(folder_path.iterdir()),
                )
                folders.append(folder_data)

        return folders

    @handle_upload_file_exceptions
    async def get_folder_contents(self, folder_path: str) -> dict:
        """Get contents of a specific folder"""
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            raise ErrorSavingFile(f"Folder {folder_path} not found")

        files = []
        folders = []

        for item in folder.iterdir():
            if item.is_file():
                files.append(
                    {
                        "name": item.name,
                        "path": str(item),
                        "size": item.stat().st_size,
                        "updated": datetime.datetime.fromtimestamp(
                            item.stat().st_mtime
                        ).isoformat(),
                        "type": "file",
                    }
                )
            else:
                folders.append(
                    {"name": item.name, "path": str(item), "type": "folder"}
                )

        return {
            "current_path": str(folder),
            "items": sorted(
                folders + files, key=lambda x: (x["type"] == "file", x["name"])
            ),
        }

    @staticmethod
    def _get_user_identifier(request: Request) -> str:
        user_identifier = request.scope.get("user")
        if not user_identifier and request.client:
            user_identifier = request.client.host
        return (
            str(user_identifier) if user_identifier is not None else "Unknown"
        )

    def _create_directory(self, request: Request) -> Path:
        storage_path = Path(self._path_to_storage) / self._get_user_identifier(
            request
        )

        storage_path.mkdir(parents=True, exist_ok=True)

        return storage_path

    @staticmethod
    def _create_url_path(file_path: str, request: Request) -> str:
        base_url = str(request.base_url).rstrip("/")
        url_path = urllib.parse.quote(file_path.replace(os.sep, "/"))

        return f"{base_url}/{url_path}"
