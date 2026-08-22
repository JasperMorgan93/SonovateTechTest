import pytest

from company_data_platform.ingestion.rest.companies_house.exceptions import (
    AuthenticationError,
    CompaniesHouseError,
    NotFoundError,
    RateLimitError,
    RequestValidationError,
    ServerError,
    TransportError,
)


@pytest.mark.parametrize(
    "exception_class",
    [AuthenticationError, RequestValidationError, NotFoundError, RateLimitError, ServerError, TransportError],
)
def test_each_exception_is_a_companies_house_error_carrying_status_and_message(exception_class):
    error = exception_class(418, "something went wrong")

    assert isinstance(error, CompaniesHouseError)
    assert error.status_code == 418
    assert error.message == "something went wrong"
    assert str(error) == "something went wrong"
