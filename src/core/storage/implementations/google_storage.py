import logging
from typing import List, Optional, Union, Type

from dotenv import load_dotenv
from google.cloud import storage  # type: ignore
from google.cloud.storage import Blob, Bucket  # type: ignore
from google.cloud.storage_control_v2 import (
    StorageControlClient,
    CreateFolderRequest,
    DeleteFolderRequest,
    RenameFolderRequest,
    ListFoldersRequest,
)  # type: ignore

from src.core.storage.decorators import handle_cloud_storage_exceptions
from src.core.storage.interfaces.cloud_storage_interface import (
    CloudStorageInterface,
)
from src.core.storage.shemas import (
    FolderBaseSchema,
    FolderDeleteSchema,
    FolderDataSchema,
    FolderRenameSchema,
    FileSchema,
    FileDeleteSchema,
)

load_dotenv()

logger = logging.getLogger(__name__)


class GoogleCloudStorage(CloudStorageInterface):
    _BASE_STORAGE_CLOUD_URL = "https://storage.googleapis.com"

    def __init__(self, bucket_name: str, project_id: str) -> None:
        self.bucket_name = bucket_name
        self.project_id = project_id
        self._client: Optional[storage.Client] = None
        self._storage_control: Optional[StorageControlClient] = None
        self._bucket: Optional[Bucket] = None

    @property
    def base_url(self) -> str:
        return f"{self._BASE_STORAGE_CLOUD_URL}/{self.bucket_name}"

    @property
    @handle_cloud_storage_exceptions
    def client(self) -> storage.Client:
        """Get cloud storage client"""
        if self._client is None:
            self._client = storage.Client(project=self.project_id)
        return self._client

    @property
    @handle_cloud_storage_exceptions
    def storage_control(self) -> StorageControlClient:
        """
        Get storage control client instance.

        This property returns a StorageControlClient instance, which is used to
        manage storage resources.

        Returns:
            StorageControlClient: Storage control client instance.
        """
        if self._storage_control is None:
            self._storage_control = StorageControlClient()
        return self._storage_control

    @property
    @handle_cloud_storage_exceptions
    def bucket(self) -> Bucket:
        """
        Get bucket instance

        Returns:
            Bucket: Cloud storage bucket
        """
        if self._bucket is None:
            self._bucket = self.client.get_bucket(
                bucket_or_name=self.bucket_name
            )
        return self._bucket

    @handle_cloud_storage_exceptions
    async def upload_blob(
        self,
        file_path: str,
        content: Union[str, bytes],
        content_type: Optional[str] = None,
    ) -> FileSchema:
        blob: Blob = self.bucket.blob(file_path)

        if content_type:
            blob.content_type = content_type

        if isinstance(content, str):
            content = content.encode("utf-8")

        blob.upload_from_string(content, content_type=content_type)

        return FileSchema(
            filename=blob.name,
            url=blob.public_url,
            size=blob.size,
            content_type=blob.content_type,
        )

    @handle_cloud_storage_exceptions
    async def delete_blob(self, file_path: str) -> FileDeleteSchema:
        blob: Blob = self.bucket.blob(file_path)
        blob.delete()

        return FileDeleteSchema(file=file_path)

    @handle_cloud_storage_exceptions
    async def copy_blob(self, source_blob: Blob, new_name: str) -> FileSchema:
        new_blob = self.bucket.copy_blob(source_blob, self.bucket, new_name)

        return FileSchema(
            filename=new_blob.name,
            url=new_blob.public_url,
            size=new_blob.size,
            content_type=new_blob.content_type,
        )

    @handle_cloud_storage_exceptions
    async def list_blobs(
        self,
        prefix: str = "",
        delimiter=None,
    ) -> List[FileSchema]:
        blobs = list(
            self.bucket.list_blobs(prefix=prefix, delimiter=delimiter)
        )

        return [
            FileSchema(
                filename=blob.name,
                url=blob.public_url,
                size=blob.size,
                content_type=blob.content_type,
            )
            for blob in blobs
        ]

    @handle_cloud_storage_exceptions
    async def create_folder(
        self,
        folder_name: str,
        create_request: Type[CreateFolderRequest] = CreateFolderRequest,
    ) -> FolderBaseSchema:
        """Create a new folder"""
        parent = await self._get_bucket_path()

        response = self.storage_control.create_folder(
            request=create_request(
                parent=parent,
                folder_id=folder_name,
                recursive=True,
            )
        )
        folder_path = await self._get_common_folder_path(folder_name)

        return FolderDataSchema(
            folder_name=folder_name,
            folder_path=folder_path,
            create_time=response.create_time.replace(microsecond=0),
            update_time=response.update_time.replace(microsecond=0),
        )

    @handle_cloud_storage_exceptions
    async def delete_folder(
        self,
        folder_name: str,
        delete_request: Type[DeleteFolderRequest] = DeleteFolderRequest,
    ) -> FolderDeleteSchema:
        """Delete a folder"""
        folder_path = await self._get_folder_path(folder_name)

        self.storage_control.delete_folder(
            request=delete_request(
                name=folder_path,
            )
        )

        return FolderDeleteSchema(folder_name=folder_name)

    @handle_cloud_storage_exceptions
    async def rename_folder(
        self,
        old_name: str,
        new_name: str,
        rename_request: Type[RenameFolderRequest] = RenameFolderRequest,
    ) -> FolderRenameSchema:
        """Rename a folder"""
        old_folder_path = await self._get_folder_path(old_name)
        self.storage_control.rename_folder(
            request=rename_request(
                name=old_folder_path,
                destination_folder_id=new_name,
            )
        )

        folder_path = await self._get_common_folder_path(new_name)

        return FolderRenameSchema(
            folder_name=new_name,
            old_name=old_name,
            folder_path=folder_path,
        )

    async def list_folders(
        self,
        prefix: Optional[str] = None,
        list_folders_request: Type[ListFoldersRequest] = ListFoldersRequest,
    ) -> List[FolderDataSchema]:
        """List folders"""
        folders_raw = self.storage_control.list_folders(
            request=list_folders_request(
                parent=self.bucket,
                prefix=prefix,
            )
        )

        folders: List[FolderDataSchema] = []

        for folder in folders_raw:
            folder_path = await self._get_common_folder_path(folder.name)
            folders.append(
                FolderDataSchema(
                    folder_name=folder.name.split("/")[-2],
                    folder_path=folder_path,
                    create_time=folder.create_time.replace(microsecond=0),
                    update_time=folder.update_time.replace(microsecond=0),
                )
            )

        return folders

    async def _get_bucket_path(self) -> str:
        project_path = self.storage_control.common_project_path("_")

        return f"{project_path}/buckets/{self.bucket_name}"

    async def _get_folder_path(self, folder_name: str) -> str:
        return self.storage_control.folder_path(
            project="_", bucket=self.bucket_name, folder=folder_name
        )

    async def _get_common_folder_path(self, folder_name: str) -> str:
        folder_path = self.storage_control.common_folder_path(
            folder_name
        ).split("folders/")[-1]

        return folder_path if folder_path.endswith("/") else f"{folder_path}/"
