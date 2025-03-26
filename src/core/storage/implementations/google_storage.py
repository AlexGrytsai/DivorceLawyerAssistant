import logging
from typing import List, Optional, Union

from dotenv import load_dotenv
from google.api_core import exceptions
from google.cloud import storage  # type: ignore
from google.cloud.storage import Blob, Bucket  # type: ignore

from src.core.exceptions.storage import ErrorSavingFile
from src.core.storage.interfaces.cloud_storage_interface import (
    CloudStorageInterface,
)

load_dotenv()

logger = logging.getLogger(__name__)


class GoogleCloudStorage(CloudStorageInterface):

    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self._client: Optional[storage.Client] = None
        self._bucket: Optional[Bucket] = None

    @property
    def get_client(self) -> storage.Client:
        if self._client is None:
            try:
                self._client = storage.Client()
            except Exception as e:
                logger.error("Failed to initialize GCS client", e)
                raise ErrorSavingFile(f"Failed to initialize GCS client: {e}")
        return self._client

    @property
    def get_bucket(self) -> Bucket:
        if self._bucket is None:
            try:
                self._bucket = self.get_client.bucket(self.bucket_name)
            except Exception as e:
                logger.error(f"Failed to get bucket {self.bucket_name}", e)
                raise ErrorSavingFile(
                    f"Failed to get bucket {self.bucket_name}: {e}"
                )
        return self._bucket

    def upload_blob(
        self,
        file_path: str,
        content: Union[str, bytes],
        content_type: Optional[str] = None,
    ) -> str:
        try:
            blob = self.get_bucket.blob(file_path)

            if content_type:
                blob.content_type = content_type

            if isinstance(content, str):
                content = content.encode("utf-8")

            blob.upload_from_string(content, content_type=content_type)

            return blob.public_url
        except Exception as e:
            logger.error(f"Failed to upload file {file_path}", e)
            raise ErrorSavingFile(f"Failed to upload file: {e}")

    def delete_blob(self, file_path: str) -> None:
        try:
            blob = self.get_bucket.blob(file_path)
            blob.delete()
        except exceptions.NotFound:
            logger.warning(f"Blob {file_path} not found")
            raise ErrorSavingFile(f"Blob {file_path} not found")
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}", e)
            raise ErrorSavingFile(f"Failed to delete file: {e}")

    def copy_blob(self, source_blob: Blob, new_name: str) -> Blob:
        try:
            new_blob = self.get_bucket.copy_blob(
                source_blob, self.get_bucket, new_name
            )
            return new_blob
        except Exception as e:
            logger.error(f"Failed to copy blob to {new_name}", e)
            raise ErrorSavingFile(f"Failed to copy blob to {new_name}: {e}")

    def list_blobs(self, prefix: str = "") -> List[Blob]:
        try:
            return list(self.get_bucket.list_blobs(prefix=prefix))
        except Exception as e:
            logger.error(f"Failed to list blobs with prefix {prefix}", e)
            raise ErrorSavingFile(
                f"Failed to list blobs with prefix {prefix}: {e}"
            )
