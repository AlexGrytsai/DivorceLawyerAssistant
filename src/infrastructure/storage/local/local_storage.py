import asyncio
import datetime
import logging
import os
import urllib
from pathlib import Path
from typing import List, Optional

from fastapi import UploadFile, Request

from src.domain.storage.entities import File, FileDelete
from src.domain.storage.entities.folder import (
    FolderDelete,
    FolderData,
    FolderRename,
)
from src.domain.storage.exceptions import (
    ErrorSavingFile,
    PathNotFoundError,
    PathAlreadyExistsError,
    FileNotFound,
    FileAlreadyExistsError,
    SourceFileNotFound,
)
from src.domain.storage.repositories import StorageRepository
from src.infrastructure.storage.decorators import (
    handle_upload_file_exceptions,
    handle_delete_file_exceptions,
)

logger = logging.getLogger(__name__)


def _validate_path_exists(
    path: Path,
    entity: str,
) -> None:
    """Validate that path exists"""
    if not path.exists():
        logger.warning(f"{entity} {path} not found")
        raise PathNotFoundError(f"{entity} {path} not found")


def _validate_path_not_exists(
    path: Path,
    entity: str,
) -> None:
    """Validate that path does not exist"""
    if path.exists():
        logger.warning(f"{entity} {path} already exists")
        raise PathAlreadyExistsError(f"{entity} {path} already exists")


class LocalStorage(StorageRepository):
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
    ) -> File:
        file_object = await file.read()

        file_path = os.path.join(
            self._create_directory(request), file.filename or "file"
        )

        with open(file_path, "wb") as fh:
            fh.write(file_object)
        await file.close()

        return File(
            filename=file.filename or "Unknown",
            path=file_path,
            url=self._create_url_path(file_path, request),
            content_type=file.content_type,
            size=file.size,
        )

    async def multi_upload(
        self,
        files: List[UploadFile],
        request: Optional[Request] = None,
        *args,
        **kwargs,
    ) -> List[File]:
        uploaded = await asyncio.gather(
            *[self.upload(file=file, request=request) for file in files]
        )
        return list(uploaded)

    @handle_delete_file_exceptions
    async def delete_file(
        self, file_path: str, request: Request, *args, **kwargs
    ) -> FileDelete:
        if Path(file_path).exists():
            os.remove(Path(file_path))
            logger.info(f"{file_path} deleted successfully")

            return FileDelete(
                file=file_path,
            )
        else:
            logger.warning(
                f"{file_path} not found in {self._path_to_storage} "
                f"for deletion"
            )
            raise FileNotFound(f"{file_path} not found")

    @handle_delete_file_exceptions
    async def delete_folder(
        self, folder_path: str, request: Request, *args, **kwargs
    ) -> FolderDelete:
        """Delete a folder and all its contents"""
        folder = Path(folder_path)
        _validate_path_exists(folder, "Folder")

        deleted_files = 0
        for root, dirs, files in os.walk(folder, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
                deleted_files += 1
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(folder)

        logger.info(f"{folder_path} deleted successfully")
        return FolderDelete(
            folder_name=folder_path,
        )

    @handle_upload_file_exceptions
    async def create_folder(
        self, folder_path: str, request: Request, *args, **kwargs
    ) -> FolderData:
        """Create a new folder in storage"""
        folder = Path(folder_path)
        _validate_path_not_exists(folder, "Folder")

        folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Folder {folder_path} created successfully")

        return FolderData(
            folder_path=str(folder),
            folder_name=folder.name,
            create_time=datetime.datetime.now(),
            update_time=datetime.datetime.now(),
        )

    @handle_upload_file_exceptions
    async def rename_folder(
        self, old_path: str, new_path: str, request: Request, *args, **kwargs
    ) -> FolderRename:
        """Rename existing folder"""
        old_folder = Path(old_path)
        new_folder = Path(new_path)

        _validate_path_exists(old_folder, "Source folder")
        _validate_path_not_exists(new_folder, "Target folder")

        old_folder.rename(new_folder)
        logger.info(f"Folder renamed from {old_path} to {new_path}")

        return FolderRename(
            folder_name=new_folder.name,
            old_name=old_folder.name,
            folder_path=str(new_folder),
        )

    @handle_upload_file_exceptions
    async def rename_file(
        self,
        old_path: str,
        new_file_name: str,
        request: Request,
        *args,
        **kwargs,
    ) -> File:
        """Rename existing file"""
        old_file = Path(old_path)
        new_file = Path(new_file_name)

        if old_file.exists():
            if not new_file.exists():
                old_file.rename(new_file)
                logger.info(f"File renamed from {old_path} to {new_file_name}")

                return File(
                    filename=new_file.name,
                    path=str(new_file),
                    url=self._create_url_path(str(new_file), request),
                    content_type=None,
                    size=None,
                )
            else:
                logger.warning(f"Target file {new_file_name} already exists")
                raise FileAlreadyExistsError(
                    f"Target file {new_file_name} already exists"
                )
        else:
            logger.warning(f"Source file {old_path} not found")
            raise SourceFileNotFound(f"Source file {old_path} not found")

    @handle_upload_file_exceptions
    async def get_file(
        self,
        file_path: str,
        request: Request,
    ) -> File:
        """Get file by path"""
        file = Path(file_path)
        if not file.exists():
            raise ErrorSavingFile(f"File {file_path} not found")

        return File(
            filename=file.name,
            path=str(file),
            url=self._create_url_path(str(file), request),
            content_type=None,
            size=file.stat().st_size,
        )

    @handle_upload_file_exceptions
    async def list_files(
        self,
        request: Request,
        prefix: Optional[str] = None,
    ) -> List[File]:
        """List all files in storage"""
        storage_path = Path(self._path_to_storage)
        if prefix:
            storage_path = storage_path / prefix

        files = []
        for file_path in storage_path.rglob("*"):
            if file_path.is_file():
                file_data = File(
                    filename=file_path.name,
                    path=str(file_path),
                    url=self._create_url_path(str(file_path), request),
                    content_type=None,
                    size=file_path.stat().st_size,
                )
                files.append(file_data)

        return sorted(files, key=lambda x: x.filename or "")

    @handle_upload_file_exceptions
    async def list_folders(
        self, prefix: Optional[str] = None
    ) -> List[FolderData]:
        """List all folders in storage"""
        storage_path = Path(self._path_to_storage)
        if prefix:
            storage_path = storage_path / prefix

        folders = []
        for folder_path in storage_path.rglob("*"):
            if folder_path.is_dir():
                folder_data = FolderData(
                    folder_path=str(folder_path),
                    folder_name=folder_path.name,
                    create_time=None,
                    update_time=None,
                )
                folders.append(folder_data)

        return folders

    @handle_upload_file_exceptions
    async def get_folder(self, folder_path: str) -> FolderData:
        """Get folder information by path"""
        folder = Path(folder_path)
        _validate_path_exists(folder, "Folder")

        return FolderData(
            folder_path=str(folder),
            folder_name=folder.name,
        )

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

    @handle_upload_file_exceptions
    async def search_files_by_name(
        self,
        search_query: str,
        request: Request,
        case_sensitive: bool = False,
    ) -> List[File]:
        """Search files by name with optional case sensitivity"""
        storage_path = Path(self._path_to_storage)
        files = []

        search_query = search_query if case_sensitive else search_query.lower()

        for file_path in storage_path.rglob("*"):
            if file_path.is_file():
                filename = file_path.name
                if not case_sensitive:
                    filename = filename.lower()

                if search_query in filename:
                    file_data = File(
                        filename=file_path.name,
                        path=str(file_path),
                        url=self._create_url_path(str(file_path), request),
                        content_type=None,
                        size=file_path.stat().st_size,
                    )
                    files.append(file_data)

        return sorted(files, key=lambda x: x.filename or "")

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
