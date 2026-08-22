"""HTTP Basic authentication for Companies House: API key as username,
empty password."""

from pydantic import SecretStr
from requests.auth import HTTPBasicAuth


def build_auth(api_key: SecretStr) -> HTTPBasicAuth:
    """Build the HTTPBasicAuth Companies House expects from a SecretStr key."""
    return HTTPBasicAuth(api_key.get_secret_value(), "")
