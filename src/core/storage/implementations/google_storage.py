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
        """
        Get cloud storage client instance.

        This property returns a Google Cloud Storage Client instance,
        which is used to interact with Google Cloud Storage.
        The client is initialized with the project ID specified during
        class initialization.

        Returns:
            storage.Client: Google Cloud Storage client instance
        """
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
        Get the cloud storage bucket instance.

        This property returns a Bucket instance for the bucket specified during
        class initialization.
        The bucket is used for all blob (file) operations.
        The bucket is lazily initialized on first access.

        Returns:
            Bucket: Google Cloud Storage bucket instance
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
            filename=blob.name.split("/")[-1],
            path="/".join(blob.name.split("/")[:-1]),
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
            filename=new_blob.name.split("/")[-1],
            path="/".join(new_blob.name.split("/")[:-1]),
            url=new_blob.public_url,
            size=new_blob.size,
            content_type=new_blob.content_type,
        )

    @handle_cloud_storage_exceptions
    async def rename_blob(
        self, source_blob: Blob, new_name: str
    ) -> FileSchema:
        new_blob = self.bucket.rename_blob(source_blob, new_name)

        return FileSchema(
            filename=new_blob.name.split("/")[-1],
            path="/".join(new_blob.name.split("/")[:-1]),
            url=new_blob.public_url,
            size=new_blob.size,
            content_type=new_blob.content_type,
        )

    @handle_cloud_storage_exceptions
    async def list_blobs(
        self,
        prefix: Optional[str] = "",
        search_query: Optional[str] = None,
        case_sensitive: Optional[bool] = False,
    ) -> List[FileSchema]:
        blobs = list(
            self.bucket.list_blobs(
                prefix=prefix,
            )
        )
        if not case_sensitive:
            search_query = search_query.lower()

        if search_query:
            return await self._search_blobs(
                blobs, search_query, case_sensitive
            )

        return [
            FileSchema(
                filename=blob.name.split("/")[-1],
                path=blob.name,
                url=blob.public_url,
                size=blob.size,
                content_type=blob.content_type,
            )
            for blob in blobs
            if blob.content_type != "Folder"
        ]

    @handle_cloud_storage_exceptions
    async def create_folder(
        self,
        folder_name: str,
        create_request: Type[CreateFolderRequest] = CreateFolderRequest,
    ) -> FolderBaseSchema:
        """
        Create a new managed folder in the storage.

        This method creates a new folder in Google Cloud Storage
        using the Storage Control API.
        It constructs the necessary request with the parent bucket path
        and folder ID.

        Args:
            folder_name: Name of the folder to create
            create_request: Type of CreateFolderRequest to use
                            (for testing/mocking)

        Returns:
            FolderDataSchema: Information about the created folder including
                              folder path and timestamps

        Raises:
            Exception: If folder creation fails (handled by decorator)
        """
        parent = self._get_bucket_path()

        response = self.storage_control.create_folder(
            request=create_request(
                parent=parent,
                folder_id=folder_name,
                recursive=True,
            )
        )

        return FolderDataSchema(
            folder_name=folder_name.split("/")[-1],
            folder_path=folder_name,
            create_time=response.create_time.replace(microsecond=0),
            update_time=response.update_time.replace(microsecond=0),
        )

    @handle_cloud_storage_exceptions
    async def delete_folder(
        self,
        folder_path: str,
        delete_request: Type[DeleteFolderRequest] = DeleteFolderRequest,
    ) -> FolderDeleteSchema:
        """
        Delete a managed folder from the storage.

        This method deletes a folder from Google Cloud Storage using
        the Storage Control API.
        It constructs the necessary request with the full folder path.

        Args:
            folder_path: Path of the folder to delete
            delete_request: Type of DeleteFolderRequest to use
                            (for testing/mocking)

        Returns:
            FolderDeleteSchema: Information about the deleted folder

        Raises:
            Exception: If folder deletion fails (handled by decorator)
        """
        folder_full_path = self._get_folder_path(folder_path)

        self.storage_control.delete_folder(
            request=delete_request(
                name=folder_full_path,
            )
        )

        return FolderDeleteSchema(folder_name=folder_path)

    @handle_cloud_storage_exceptions
    async def rename_folder(
        self,
        old_name: str,
        new_name: str,
        rename_request: Type[RenameFolderRequest] = RenameFolderRequest,
    ) -> FolderRenameSchema:
        """
        Rename a managed folder in the storage.

        This method renames a folder in Google Cloud Storage using
        the Storage Control API.
        It constructs the necessary request with the old folder path and
        new folder ID.

        Args:
            old_name: Current name of the folder
            new_name: New name for the folder
            rename_request: Type of RenameFolderRequest to use
                            (for testing/mocking)

        Returns:
            FolderRenameSchema: Information about the renamed folder

        Raises:
            Exception: If folder renaming fails (handled by decorator)
        """
        old_folder_path = self._get_folder_path(old_name)
        self.storage_control.rename_folder(
            request=rename_request(
                name=old_folder_path,
                destination_folder_id=new_name,
            )
        )

        folder_path = self._get_common_folder_path(new_name)

        return FolderRenameSchema(
            folder_name=new_name,
            old_name=old_name,
            folder_path=folder_path,
        )

    async def list_folders(
        self,
        prefix: Optional[str] = None,
    ) -> List[FolderDataSchema]:
        """
        List managed folders in the storage.

        This method lists folders in Google Cloud Storage using
        the Storage Control API.
        It constructs the necessary request with the parent bucket path and
        optional prefix.

        Args:
            prefix: Optional prefix to filter results

        Returns:
            List[FolderDataSchema]: List of folder schemas representing
                                    the matching folders
        """
        list_folders_request = ListFoldersRequest(
            parent=self._get_bucket_path(),
            prefix=prefix if prefix else "",
        )
        folders_raw = self.storage_control.list_folders(
            request=list_folders_request
        )

        folders: List[FolderDataSchema] = []

        folders.extend(
            FolderDataSchema(
                folder_name=folder.name.split("/")[-2],
                folder_path=self._get_common_folder_path(folder.name),
                create_time=folder.create_time.replace(microsecond=0),
                update_time=folder.update_time.replace(microsecond=0),
            )
            for folder in folders_raw
        )
        return folders

    def _get_bucket_path(self) -> str:
        """
        Get the full path to the bucket in Google Cloud Storage.

        This method constructs the full path to the bucket using
        the project path and bucket name. The path is used for operations that
        require the full bucket path, such as folder creation.

        Returns:
            str: The full path to the bucket in the format
                 "projects/{project_id}/buckets/{bucket_name}"
        """
        project_path = self.storage_control.common_project_path("_")

        return f"{project_path}/buckets/{self.bucket_name}"

    def _get_folder_path(self, folder_name: str) -> str:
        """
        Get the full path to a folder in Google Cloud Storage.

        This method constructs the full path to a folder using the storage
        control client's folder_path method. The path is used for operations
        that require the full folder path, such as folder deletion or renaming.

        Args:
            folder_name: Name of the folder to get the path for

        Returns:
            str: The full path to the folder in the format required by the
                 Storage Control API
        """
        return self.storage_control.folder_path(
            project="_", bucket=self.bucket_name, folder=folder_name
        )

    def _get_common_folder_path(self, folder_name: str) -> str:
        """
        Get a standardized folder path format for consistent usage.

        This method takes a folder name and converts it to a standardized path
        format by extracting the relevant part from the common_folder_path
        and ensuring it ends with a trailing slash. This standardized format
        is used for consistent folder path representation across
        the application.

        Args:
            folder_name: Name of the folder to get the standardized path for

        Returns:
            str: The standardized folder path with a trailing slash
        """
        folder_path = self.storage_control.common_folder_path(
            folder_name
        ).split("folders/")[-1]

        return folder_path if folder_path.endswith("/") else f"{folder_path}/"

    @staticmethod
    async def _search_blobs(
        blobs: List[Blob],
        search_query: str,
        case_sensitive: Optional[bool] = False,
    ) -> List[FileSchema]:
        """
        Search for blobs that match a given query string.

        This method filters a list of blobs based on whether their names
        contain the specified search query. The search can be case-sensitive
        or case-insensitive based on the provided parameter.

        Args:
            blobs: List of Blob objects to search through
            search_query: The string to search for in blob names
            case_sensitive: Whether the search should be case-sensitive
                            (default: False)

        Returns:
            List[FileSchema]: A list of FileSchema objects representing
                              the blobs whose names contain the search query
        """
        if not case_sensitive:
            search_query = search_query.lower()

        matching_files: List[FileSchema] = []
        for blob in blobs:
            if blob.content_type != "Folder":
                blob_name = blob.name.split("/")[-1]
                if not case_sensitive:
                    blob_name = blob_name.lower()

                if search_query in blob_name:
                    matching_files.append(
                        FileSchema(
                            filename=blob_name,
                            path=blob.name,
                            url=blob.public_url,
                            content_type=blob.content_type,
                            size=blob.size,
                        )
                    )

        return matching_files
