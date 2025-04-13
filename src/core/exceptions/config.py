from .base import CoreException


class ConfigError(CoreException):
    """Raised when there is an error in configuration."""

    pass


class MissingEnvironmentVariable(ConfigError):
    """Raised when a required environment variable is missing."""

    pass
