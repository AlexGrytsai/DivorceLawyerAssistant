import asyncio
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
    GetFolderRequest,
)  # type: ignore

from src.domain.storage.entities import File, FileDelete, FolderData
from src.domain.storage.entities.folder import FolderDelete, FolderRename
from src.domain.storage.repositories import CloudStorageRepository
from src.infrastructure.storage.cloud.google_cloud.decorators import (
    handle_google_storage_exceptions,
    async_handle_google_storage_exceptions,
)

load_dotenv()

logger = logging.getLogger(__name__)


class GoogleCloudStorage(CloudStorageRepository):
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
    @handle_google_storage_exceptions
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
    @handle_google_storage_exceptions
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
    @handle_google_storage_exceptions
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

    @async_handle_google_storage_exceptions
    async def upload_blob(
        self,
        file_path: str,
        content: Union[str, bytes],
        content_type: Optional[str] = None,
    ) -> File:
        blob: Blob = self.bucket.blob(file_path)

        if content_type:
            blob.content_type = content_type

        if isinstance(content, str):
            content = content.encode("utf-8")

        blob.upload_from_string(content, content_type=content_type)

        return File(
            filename=self._get_blob_name(blob.name),
            path=self._get_blob_path(blob.name),
            url=blob.public_url,
            size=blob.size,
            content_type=blob.content_type,
        )

    @async_handle_google_storage_exceptions
    async def get_blob(self, file_path: str) -> File:
        """Get blob (file) by path"""
        blob: Blob = self.bucket.get_blob(self._normalize_file_path(file_path))

        return File(
            filename=self._get_blob_name(blob.name),
            path=self._get_blob_path(blob.name),
            url=blob.public_url,
            size=blob.size,
            content_type=blob.content_type,
        )

    @async_handle_google_storage_exceptions
    async def delete_blob(self, file_path: str) -> FileDelete:
        blob: Blob = self.bucket.blob(self._normalize_file_path(file_path))
        blob.delete()

        return FileDelete(file=file_path)

    @async_handle_google_storage_exceptions
    async def copy_blob(self, source_blob: Blob, new_name: str) -> File:
        new_blob = self.bucket.copy_blob(source_blob, self.bucket, new_name)

        return File(
            filename=self._get_blob_name(new_blob.name),
            path=self._get_blob_path(new_blob.name),
            url=new_blob.public_url,
            size=new_blob.size,
            content_type=new_blob.content_type,
        )

    @async_handle_google_storage_exceptions
    async def rename_blob(self, source_blob_path: str, new_name: str) -> File:

        source_blob = self.bucket.get_blob(
            self._normalize_file_path(source_blob_path)
        )

        folder_ = self._normalize_file_path(source_blob_path).split("/")[:-1]
        new_blob = self.bucket.rename_blob(
            source_blob, f"{folder_}/{new_name}"
        )

        return File(
            filename=self._get_blob_name(new_blob.name),
            path=self._get_blob_path(new_blob.name),
            url=new_blob.public_url,
            size=new_blob.size,
            content_type=new_blob.content_type,
        )

    @async_handle_google_storage_exceptions
    async def list_blobs(
        self,
        prefix: Optional[str] = "",
        search_query: Optional[str] = None,
        case_sensitive: Optional[bool] = False,
    ) -> List[File]:
        blobs: List[Blob] = list(
            self.bucket.list_blobs(
                prefix=self._normalize_file_path(prefix),
            )
        )

        if search_query:
            if not case_sensitive:
                search_query = search_query.lower()
            return self._search_blobs(blobs, search_query, case_sensitive)

        return [
            File(
                filename=self._get_blob_name(blob.name),
                path=self._get_blob_path(blob.name),
                url=blob.public_url,
                size=blob.size,
                content_type=blob.content_type,
            )
            for blob in blobs
            if not blob.name.endswith("/")
        ]

    @async_handle_google_storage_exceptions
    async def create_folder(
        self,
        folder_name: str,
        create_request: Type[CreateFolderRequest] = CreateFolderRequest,
        *args,
        **kwargs,
    ) -> FolderData:
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
                              a folder path and timestamps

        Raises:
            Exception: If folder creation fails (handled by decorator)
        """
        response = self.storage_control.create_folder(
            request=create_request(
                parent=self._get_bucket_path(),
                folder_id=folder_name,
                recursive=False,
            )
        )

        return FolderData(
            folder_name=self._get_folder_name(response.name),
            folder_path=self._get_common_folder_path(folder_name),
            create_time=response.create_time.replace(microsecond=0),
            update_time=response.update_time.replace(microsecond=0),
        )

    @async_handle_google_storage_exceptions
    async def get_folder(self, folder_path: str) -> FolderData:
        """
        Get information about a managed folder in the storage.

        This method gets folder information from Google Cloud Storage
        """
        folder = self.storage_control.get_folder(
            request=GetFolderRequest(name=self._get_folder_path(folder_path))
        )

        return FolderData(
            folder_name=self._get_folder_name(folder.name),
            folder_path=self._get_common_folder_path(folder.name),
            create_time=folder.create_time.replace(microsecond=0),
            update_time=folder.update_time.replace(microsecond=0),
        )

    @async_handle_google_storage_exceptions
    async def delete_folder(
        self,
        folder_path: str,
        delete_request: Type[DeleteFolderRequest] = DeleteFolderRequest,
        is_delete_all: bool = False,
    ) -> FolderDelete:
        """
        Delete a managed folder from the storage.

        This method deletes a folder from Google Cloud Storage using
        the Storage Control API.
        It constructs the necessary request with the full folder path.

        Args:
            folder_path: Path of the folder to delete
            delete_request: Type of DeleteFolderRequest to use
                            (for testing/mocking)
            is_delete_all: If True, deletes all nested files and folders

        Returns:
            FolderDeleteSchema: Information about the deleted folder
        """
        folder_path = self._normalize_file_path(folder_path)
        if is_delete_all:
            await self._delete_all_files_in_folder(folder_path)

            await self._delete_subfolders(folder_path)
        else:
            await self._delete_folder(folder_path)

        return FolderDelete(folder_name=folder_path)

    @async_handle_google_storage_exceptions
    async def rename_folder(
        self,
        old_name: str,
        new_name: str,
        rename_request: Type[RenameFolderRequest] = RenameFolderRequest,
    ) -> FolderRename:
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
        self.storage_control.rename_folder(
            request=rename_request(
                name=self._get_folder_path(old_name),
                destination_folder_id=new_name,
            )
        )

        folder_path = self._get_common_folder_path(new_name)

        return FolderRename(
            folder_name=new_name,
            old_name=old_name,
            folder_path=folder_path,
        )

    @async_handle_google_storage_exceptions
    async def list_folders(
        self,
        prefix: Optional[str] = None,
    ) -> List[FolderData]:
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
            prefix=self._normalize_file_path(prefix) if prefix else "",
        )
        folders_raw = self.storage_control.list_folders(
            request=list_folders_request
        )

        folders: List[FolderData] = []

        folders.extend(
            FolderData(
                folder_name=self._get_folder_name(folder.name),
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

    @staticmethod
    def _get_blob_path(blob_name: str) -> str:
        return f"/{blob_name}"

    @staticmethod
    def _get_blob_name(blob_path: str) -> str:
        return blob_path.split("/")[-1]

    @staticmethod
    def _get_folder_name(folder_path: str) -> str:
        parts = folder_path.split("/")
        if "folders" in parts:
            folders_index = parts.index("folders")
            if folders_index + 1 < len(parts):
                return parts[-1] or parts[-2]
        return parts[-1] or (parts[-2] if len(parts) > 1 else "")

    def _get_folder_path(self, folder_path: str) -> str:
        """
        Get the full path to a folder in Google Cloud Storage.

        This method constructs the full path to a folder using the storage
        control client's folder_path method. The path is used for operations
        that require the full folder path, such as folder deletion or renaming.

        Args:
            folder_path: Folder path (format: "folders/{folder_id}/")

        Returns:
            str: The full path to the folder in the format required by the
                 Storage Control API
        """
        folder_path = folder_path.removeprefix("/")
        return self.storage_control.folder_path(
            project="_", bucket=self.bucket_name, folder=folder_path
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
    def _normalize_file_path(file_path: Optional[str] = None) -> str:
        if file_path:
            return file_path[1:] if file_path.startswith("/") else file_path

        return ""

    async def _delete_subfolders(self, folder_path: str) -> bool:
        subfolders: List[FolderData] = await self.list_folders(
            prefix=folder_path
        )
        if subfolders:
            subfolders.reverse()
            for subfolder in subfolders:
                await self._delete_folder(subfolder.folder_path)

        return True

    async def _delete_all_files_in_folder(self, folder_path: str) -> bool:
        files: List[File] = await self.list_blobs(prefix=folder_path)
        delete_tasks = [self.delete_blob(file.path) for file in files]

        await asyncio.gather(*delete_tasks)

        return True

    async def _delete_folder(
        self,
        folder_path: str,
        delete_request: Type[DeleteFolderRequest] = DeleteFolderRequest,
    ) -> bool:
        self.storage_control.delete_folder(
            request=delete_request(
                name=self._get_folder_path(folder_path),
            )
        )
        return True

    def _search_blobs(
        self,
        blobs: List[Blob],
        search_query: str,
        case_sensitive: Optional[bool] = False,
    ) -> List[File]:
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

        matching_files: List[File] = []
        for blob in blobs:
            if blob.content_type != "Folder":
                original_name = blob.name.split("/")[-1]

                if (
                    case_sensitive
                    and search_query in original_name
                    or not case_sensitive
                    and search_query in original_name.lower()
                ):
                    matching_files.append(
                        File(
                            filename=original_name,
                            path=self._get_blob_path(blob.name),
                            url=blob.public_url,
                            content_type=blob.content_type,
                            size=blob.size,
                        )
                    )
        return matching_files
