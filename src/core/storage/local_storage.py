import asyncio
import datetime
import logging
import os
import urllib
from pathlib import Path
from typing import List

from fastapi import UploadFile, Request, status, HTTPException
from starlette.responses import JSONResponse

from src.core.storage.decorators import handle_upload_file_exceptions
from src.core.storage.exceptions import ErrorUploadingFile, ErrorDeletingFile
from src.core.storage.shemas import FileDataSchema
from src.core.storage.storage import BaseStorage

logger = logging.getLogger(__name__)


class LocalStorage(BaseStorage):
    __slots__ = ("_path_to_storage",)

    def __init__(self, path_to_storage: str) -> None:
        self._path_to_storage = path_to_storage

    @staticmethod
    def _get_user_identifier(request: Request) -> str:
        user_identifier = request.scope.get("user", request.client.host)
        if isinstance(user_identifier, dict):
            user_identifier = user_identifier.get("id", request.client.host)

        user_identifier = str(user_identifier).replace(" ", "_")

        return user_identifier

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
            self._create_directory(request), file.filename
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
            creator=request.scope.get("user", request.client.host),
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

    async def delete(self, *args, filename: str) -> JSONResponse:
        try:
            file_path = Path(self._path_to_storage) / filename

            if file_path.exists():
                os.remove(file_path)
                logger.info(f"{filename} deleted successfully")

                return JSONResponse(
                    content={"message": f"{filename} deleted successfully"},
                    status_code=status.HTTP_204_NO_CONTENT,
                )
            else:
                logger.warning(
                    f"{filename} not found in {self._path_to_storage} "
                    f"for deletion"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": "File not found",
                        "message": f"{filename} not found",
                    },
                )

        except ErrorDeletingFile as exc:
            logger.error(f"Error deleting file {filename}: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": str(exc),
                    "message": f"Error deleting {filename}",
                },
            )
