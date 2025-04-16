from google.api_core.exceptions import ClientError
from google.auth.exceptions import GoogleAuthError


class ErrorWithAuthenticationInGCP(GoogleAuthError):
    pass


class ProblemWithRequestToGCP(ClientError):
    pass


class ProblemWithBucket(Exception):
    pass


class StorageError(Exception):
    pass


class ErrorSavingFile(StorageError):
    pass


class ErrorUploadingFile(StorageError):
    pass


class ErrorDeletingFile(StorageError):
    pass
