from pydantic import SecretStr

from company_data_platform.ingestion.rest.companies_house.auth import build_auth


def test_build_auth_uses_api_key_as_username_and_empty_password():
    auth = build_auth(SecretStr("test-api-key"))

    assert auth.username == "test-api-key"
    assert auth.password == ""
