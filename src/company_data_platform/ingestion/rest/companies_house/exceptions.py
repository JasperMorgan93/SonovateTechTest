"""Typed exception hierarchy for Companies House API errors."""


class CompaniesHouseError(Exception):
    """Base class for every error this client raises for a non-2xx response."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class AuthenticationError(CompaniesHouseError):
    """401 - the API key was rejected."""


class ValidationError(CompaniesHouseError):
    """400, 406, or 422 - the request itself was invalid."""


class NotFoundError(CompaniesHouseError):
    """404 - no resource exists at the requested path."""


class RateLimitError(CompaniesHouseError):
    """429 - rate limited, raised only once retries are exhausted."""


class ServerError(CompaniesHouseError):
    """5xx - a transient server error, raised only once retries are exhausted."""
