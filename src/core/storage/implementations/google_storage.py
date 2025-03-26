import logging
from typing import List, Optional, Union

from dotenv import load_dotenv
from google.cloud import storage  # type: ignore
from google.cloud.storage import Blob, Bucket  # type: ignore

from src.core.exceptions.storage import (
    ErrorSavingFile,
)
from src.core.storage.decorators import handle_cloud_storage_exceptions
from src.core.storage.interfaces.cloud_storage_interface import (
    CloudStorageInterface,
)

load_dotenv()

logger = logging.getLogger(__name__)


class GoogleCloudStorage(CloudStorageInterface):

    def __init__(self, bucket_name: str, project_id: str) -> None:
        self.bucket_name = bucket_name
        self.project_id = project_id
        self._client: Optional[storage.Client] = None
        self._bucket: Optional[Bucket] = None

    @property
    @handle_cloud_storage_exceptions
    def get_client(self) -> storage.Client:
        if self._client is None:
            self._client = storage.Client(project=self.project_id)
        return self._client

    @property
    @handle_cloud_storage_exceptions
    def get_bucket(self) -> Bucket:
        if self._bucket is None:
            self._bucket: Bucket = self.get_client.get_bucket(
                bucket_or_name=self.bucket_name
            )
        return self._bucket

    @handle_cloud_storage_exceptions
    def upload_blob(
        self,
        file_path: str,
        content: Union[str, bytes],
        content_type: Optional[str] = None,
    ) -> str:
        blob = self.get_bucket.blob(file_path)

        if content_type:
            blob.content_type = content_type

        if isinstance(content, str):
            content = content.encode("utf-8")

        blob.upload_from_string(content, content_type=content_type)

        return blob.public_url

    @handle_cloud_storage_exceptions
    def delete_blob(self, file_path: str) -> None:
        blob = self.get_bucket.blob(file_path)
        blob.delete()

    def copy_blob(self, source_blob: Blob, new_name: str) -> Blob:
        try:
            new_blob = self.get_bucket.copy_blob(
                source_blob, self.get_bucket, new_name
            )
            return new_blob
        except Exception as e:
            logger.error(f"Failed to copy blob to {new_name}", e)
            raise ErrorSavingFile(f"Failed to copy blob to {new_name}: {e}")

    @handle_cloud_storage_exceptions
    def list_blobs(self, prefix: str = "") -> List[Blob]:
        return list(self.get_bucket.list_blobs(prefix=prefix))
