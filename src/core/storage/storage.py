import asyncio
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union

from fastapi import UploadFile

from core.storage.exceptions import ErrorSavingFile, ErrorUploadingFile
from core.storage.shemas import FileData

logger = logging.getLogger(__name__)


class BaseStorage(ABC):
    async def __call__(
        self,
        file: Optional[UploadFile] = None,
        files: Optional[List[UploadFile]] = None,
    ) -> Union[FileData, List[FileData]]:
        try:
            if file:
                return await self.upload(file=file)

            elif files:
                return await self.multi_upload(files=files)
            else:
                logger.warning("No file or files provided")
                return FileData(
                    status=False,
                    error="No file or files provided",
                    message="No file or files provided",
                )
        except ErrorSavingFile as exc:
            logger.warning(f"Error saving file: {exc}")
            return FileData(
                status=False,
                error=str(exc),
                message="File upload was unsuccessful",
            )

    @abstractmethod
    async def upload(self, *args, file: UploadFile) -> FileData:
        pass

    @abstractmethod
    async def multi_upload(
        self, *args, files: List[UploadFile]
    ) -> List[FileData]:
        pass


class LocalStorage(BaseStorage):
    __slots__ = ("_path_to_storage",)

    def __init__(self, path_to_storage: str) -> None:
        self._path_to_storage = path_to_storage

    async def upload(self, *args, file: UploadFile) -> FileData:
        try:
            file_object = await file.read()

            storage_path = Path(self._path_to_storage)
            storage_path.mkdir(parents=True, exist_ok=True)

            file_path = Path(self._path_to_storage) / file.filename

            with open(file_path, "wb") as fh:
                fh.write(file_object)
            await file.close()

            return FileData(
                path=self._path_to_storage,
                message=f"{file.filename} saved successfully",
                content_type=file.content_type,
                size=file.size,
                filename=file.filename,
            )
        except ErrorUploadingFile as exc:
            logger.warning(
                f"Error uploading file: {exc} in {self.__class__.__name__}"
            )

            return FileData(
                status=False, error=str(exc), message=f"Unable to save file"
            )

    async def multi_upload(
        self, *args, files: List[UploadFile]
    ) -> List[FileData]:
        uploaded = await asyncio.gather(
            *[self.upload(file=file) for file in files]
        )
        return list(uploaded)
