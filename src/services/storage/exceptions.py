from google.api_core.exceptions import ClientError
from google.auth.exceptions import GoogleAuthError


class ErrorWithAuthenticationInGCP(GoogleAuthError):
    pass


class ProblemWithRequestToGCP(ClientError):
    pass


class ProblemWithBucket(Exception):
    pass


class ErrorSavingFile(Exception):
    pass


class ErrorUploadingFile(Exception):
    pass


class ErrorDeletingFile(Exception):
    pass
