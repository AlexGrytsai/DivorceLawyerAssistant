from google.auth.exceptions import GoogleAuthError


class ErrorWithAuthenticationInGCP(GoogleAuthError):
    pass


class ErrorSavingFile(Exception):
    pass


class ErrorUploadingFile(Exception):
    pass


class ErrorDeletingFile(Exception):
    pass
