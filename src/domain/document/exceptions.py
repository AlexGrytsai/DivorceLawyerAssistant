class DocumentDatabaseError(Exception):
    """Base exception for all document database related errors."""

    pass


class DocumentNotFoundError(DocumentDatabaseError):
    """Raised when a document cannot be found in the database."""

    pass


class DocumentAlreadyExistsError(DocumentDatabaseError):
    """Raised when attempting to create a document that already exists."""

    pass


class DatabaseConnectionError(DocumentDatabaseError):
    """Raised when there is an error connecting to the database."""

    pass


class DatabaseOperationError(DocumentDatabaseError):
    """Raised when a database operation fails."""

    pass


class ValidationError(DocumentDatabaseError):
    """Raised when document data fails validation."""

    pass


class InvalidQueryParameterError(DocumentDatabaseError):
    """Raised when a query contains invalid parameters."""

    pass


class UnsupportedOperatorError(DocumentDatabaseError):
    """Raised when an unsupported operator is used in a query."""

    pass
