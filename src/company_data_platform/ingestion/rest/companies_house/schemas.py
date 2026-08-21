"""Tolerant Pydantic models for Companies House REST response payloads.

Every model here accepts and silently drops unknown fields, and treats
every field Companies House does not structurally guarantee as optional.
This is deliberate: the upstream schema is documented as subject to
change, and ingestion must not break when a new field appears or an
optional one is absent.
"""

from pydantic import BaseModel, ConfigDict


class Address(BaseModel):
    """A postal address as returned by Companies House.

    Used for both a company's registered office and, on other
    resources not modelled yet, a service address — the shape is
    identical either way.
    """

    model_config = ConfigDict(extra="ignore")

    premises: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    locality: str | None = None
    region: str | None = None
    postal_code: str | None = None
    country: str | None = None
