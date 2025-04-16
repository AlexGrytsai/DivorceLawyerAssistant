class GoogleCloudStorageError(Exception):
    pass


class BlobNotFoundError(GoogleCloudStorageError):
    pass


class BlobAlreadyExistsError(GoogleCloudStorageError):
    pass
