class DocumentDatabaseError(Exception):
    pass


class DocumentNotFoundError(DocumentDatabaseError):
    pass


class DatabaseConnectionError(DocumentDatabaseError):
    pass


class DatabaseOperationError(DocumentDatabaseError):
    pass


class ValidationError(DocumentDatabaseError):
    pass
