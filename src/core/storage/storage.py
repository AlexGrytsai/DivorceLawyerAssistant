import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Union

from fastapi import UploadFile, status, HTTPException, Request

from src.core.storage.exceptions import ErrorSavingFile
from src.core.storage.shemas import FileDataSchema, FileDeleteSchema

logger = logging.getLogger(__name__)


class BaseStorage(ABC):
    @property
    @abstractmethod
    def path_to_storage(self) -> str:
        pass

    async def __call__(
        self,
        request: Request,
        file: Optional[UploadFile] = None,
        files: Optional[List[UploadFile]] = None,
    ) -> Union[FileDataSchema, List[FileDataSchema]]:
        try:
            if file:
                return await self.upload(file=file, request=request)

            elif files:
                return await self.multi_upload(files=files, request=request)

            logger.warning("No file or files provided")

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file or files provided",
            )
        except ErrorSavingFile as exc:
            logger.warning(f"Error saving file: {exc}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": str(exc),
                    "message": "File upload was unsuccessful",
                },
            )

    @abstractmethod
    async def upload(
        self, file: UploadFile, request: Request, *args, **kwargs
    ) -> FileDataSchema:
        pass

    @abstractmethod
    async def multi_upload(
        self, files: List[UploadFile], request: Request, *args, **kwargs
    ) -> List[FileDataSchema]:
        pass

    @abstractmethod
    async def delete(
        self, file_path: str, request: Request, *args, **kwargs
    ) -> FileDeleteSchema:
        pass
