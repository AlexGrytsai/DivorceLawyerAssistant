import logging
from typing import List, Optional, Union

from dotenv import load_dotenv
from google.cloud import storage  # type: ignore
from google.cloud.storage import Blob, Bucket  # type: ignore
from google.cloud.storage_control_v2 import (
    StorageControlClient,
    CreateManagedFolderRequest,
)  # type: ignore

from src.core.storage.decorators import handle_cloud_storage_exceptions
from src.core.storage.interfaces.cloud_storage_interface import (
    CloudStorageInterface,
)
from src.core.storage.shemas import FolderDataSchema, CreatedFolderSchema

load_dotenv()

logger = logging.getLogger(__name__)


class GoogleCloudStorage(CloudStorageInterface):

    def __init__(self, bucket_name: str, project_id: str) -> None:
        self.bucket_name = bucket_name
        self.project_id = project_id
        self._client: Optional[storage.Client] = None
        self._storage_control: Optional[StorageControlClient] = None
        self._bucket: Optional[Bucket] = None

    @property
    @handle_cloud_storage_exceptions
    def get_client(self) -> storage.Client:
        if self._client is None:
            self._client = storage.Client(project=self.project_id)
        return self._client

    @property
    @handle_cloud_storage_exceptions
    def get_storage_control(self) -> StorageControlClient:
        if self._storage_control is None:
            self._storage_control = StorageControlClient()
        return self._storage_control

    @property
    @handle_cloud_storage_exceptions
    def get_bucket(self) -> Bucket:
        if self._bucket is None:
            self._bucket = self.get_client.get_bucket(
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
        blob: Blob = self.get_bucket.blob(file_path)

        if content_type:
            blob.content_type = content_type

        if isinstance(content, str):
            content = content.encode("utf-8")

        blob.upload_from_string(content, content_type=content_type)

        return blob.public_url

    @handle_cloud_storage_exceptions
    def delete_blob(self, file_path: str) -> None:
        blob: Blob = self.get_bucket.blob(file_path)
        blob.delete()

    @handle_cloud_storage_exceptions
    def copy_blob(self, source_blob: Blob, new_name: str) -> Blob:
        return self.get_bucket.copy_blob(
            source_blob, self.get_bucket, new_name
        )

    @handle_cloud_storage_exceptions
    def list_blobs(self, prefix: str = "") -> List[Blob]:
        return list(self.get_bucket.list_blobs(prefix=prefix))

    @handle_cloud_storage_exceptions
    def create_managed_folder(self, folder_name: str) -> CreatedFolderSchema:
        """Create a new managed folder"""
        project_path = self.get_storage_control.common_project_path("_")
        bucket_path = f"{project_path}/buckets/{self.bucket_name}"

        request = CreateManagedFolderRequest(
            parent=bucket_path,
            managed_folder_id=folder_name,
        )
        response = self.get_storage_control.create_managed_folder(
            request=request
        )

        return CreatedFolderSchema(
            name="/".join(response.name.split("/")[3:]),
            create_time=response.create_time.replace(microsecond=0),
            update_time=response.update_time.replace(microsecond=0),
        )

    def delete_managed_folder(self, folder_name: str) -> None:
        """Delete a managed folder"""
        pass

    def rename_folder(self, old_name: str, new_name: str) -> None:
        """Rename a managed folder"""
        pass

    def list_managed_folders(
        self, prefix: Optional[str] = None
    ) -> List[FolderDataSchema]:
        """List managed folders"""
        pass

    def get_managed_folder(self, folder_name: str) -> FolderDataSchema:
        """Get managed folder metadata"""
        pass


if __name__ == "__main__":
    google_cloud_storage = GoogleCloudStorage(
        bucket_name="data-for-rag", project_id="divorce-lawyer-assistant"
    )

    print(google_cloud_storage.create_managed_folder("test33/test_inner"))
