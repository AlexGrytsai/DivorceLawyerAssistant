from google.api_core.exceptions import ClientError
from google.auth.exceptions import GoogleAuthError


class ErrorWithAuthenticationInGCP(GoogleAuthError):
    """Exception raised when authentication with Google Cloud Platform fails."""

    pass


class ProblemWithRequestToGCP(ClientError):
    """Exception raised when a request to Google Cloud Platform encounters an error."""

    pass


class ProblemWithBucket(Exception):
    """Exception raised when there is an issue with a storage bucket."""

    pass


class StorageError(Exception):
    """Base exception for all storage-related errors."""

    pass


class NoFileProvided(StorageError):
    """
    Exception raised when no file is provided for an operation
    that requires one.
    """

    pass


class FileNotFound(StorageError):
    """Exception raised when a file is not found in storage."""

    pass


class FileAlreadyExistsError(StorageError):
    """Exception raised when a file already exists in storage."""

    pass


class SourceFileNotFound(StorageError):
    """
    Exception raised when the source file for a rename operation is not found.
    """

    pass


class ErrorSavingFile(StorageError):
    """Exception raised when there is an error saving a file to storage."""

    pass


class ErrorUploadingFile(StorageError):
    """Exception raised when there is an error uploading a file to storage."""

    pass


class ErrorDeletingFile(StorageError):
    """Exception raised when there is an error deleting a file from storage."""

    pass


class PathNotFoundError(StorageError):
    """Exception raised when a specified path is not found in storage."""

    pass


class PathAlreadyExistsError(StorageError):
    """Exception raised when a specified path already exists in storage."""

    pass
