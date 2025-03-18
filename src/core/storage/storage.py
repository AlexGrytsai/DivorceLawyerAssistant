import asyncio
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union

from fastapi import UploadFile, status
from starlette.responses import JSONResponse

from src.core.storage.exceptions import ErrorSavingFile, ErrorUploadingFile
from src.core.storage.shemas import FileData

logger = logging.getLogger(__name__)


class BaseStorage(ABC):
    async def __call__(
        self,
        file: Optional[UploadFile] = None,
        files: Optional[List[UploadFile]] = None,
    ) -> Union[FileData, List[FileData], JSONResponse]:
        try:
            if file:
                return await self.upload(file=file)

            elif files:
                return await self.multi_upload(files=files)

            logger.warning("No file or files provided")
            return JSONResponse(
                content={
                    "error": "No file or files provided",
                    "message": "No file or files provided",
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except ErrorSavingFile as exc:
            logger.warning(f"Error saving file: {exc}")
            return JSONResponse(
                content={
                    "error": str(exc),
                    "message": "File upload was unsuccessful",
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @abstractmethod
    async def upload(self, file: UploadFile, *args, **kwargs) -> FileData:
        pass

    @abstractmethod
    async def multi_upload(
        self, *args, files: List[UploadFile]
    ) -> List[FileData]:
        pass

    @abstractmethod
    async def delete(self, *args, filename: str) -> JSONResponse:
        pass


class LocalStorage(BaseStorage):
    __slots__ = ("_path_to_storage",)

    def __init__(self, path_to_storage: str) -> None:
        self._path_to_storage = path_to_storage

    async def upload(self, file: UploadFile, *args, **kwargs) -> FileData:
        try:
            file_object = await file.read()

            storage_path = Path(self._path_to_storage)
            storage_path.mkdir(parents=True, exist_ok=True)

            file_path = Path(self._path_to_storage) / file.filename

            with open(file_path, "wb") as fh:
                fh.write(file_object)
            await file.close()

            return FileData(
                path=f"{self._path_to_storage}/{file.filename}",
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

    async def delete(self, *args, filename: str) -> JSONResponse:
        try:
            file_path = Path(self._path_to_storage) / filename

            if file_path.exists():
                os.remove(file_path)
                logger.info(f"{filename} deleted successfully")

                return JSONResponse(
                    content={"message": f"{filename} deleted successfully"},
                    status_code=status.HTTP_200_OK,
                )
            else:
                logger.warning(
                    f"{filename} not found in {self._path_to_storage} "
                    f"for deletion"
                )
                return JSONResponse(
                    content={
                        "error": "File not found",
                        "message": f"{filename} not found",
                    },
                    status_code=status.HTTP_404_NOT_FOUND,
                )

        except Exception as exc:
            logger.error(f"Error deleting file {filename}: {exc}")
            return JSONResponse(
                content={
                    "error": str(exc),
                    "message": f"Error deleting {filename}",
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
