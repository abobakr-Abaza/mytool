"""Pydantic schemas for tenant branding and onboarding."""

from uuid import UUID

from pydantic import BaseModel, Field


class BrandingPublic(BaseModel):
    """Public branding data returned without authentication.

    Exposed on the login / landing pages so the frontend can apply
    theme before the user authenticates.
    """

    logo_url: str | None = None
    favicon_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    accent_color: str | None = None
    portal_title: str | None = None
    custom_css: str | None = None


class BrandingUpdate(BaseModel):
    """Admin payload to update tenant branding."""

    logo_url: str | None = None
    favicon_url: str | None = None
    primary_color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    secondary_color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    accent_color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    custom_domain: str | None = Field(None, max_length=255)
    portal_title: str | None = Field(None, max_length=200)
    custom_css: str | None = None
    is_active: bool | None = None


class BrandingResponse(BrandingPublic):
    """Full branding record returned to admin."""

    id: UUID
    clinic_id: UUID
    custom_domain: str | None = None
    is_active: bool


class TenantOnboardRequest(BaseModel):
    """Payload to create a new tenant (clinic + branding + admin user)."""

    clinic_name: str = Field(..., min_length=1, max_length=200)
    tax_id: str = Field(..., min_length=1, max_length=20)
    admin_email: str = Field(..., max_length=255)
    admin_password: str = Field(..., min_length=8)
    admin_first_name: str = Field(..., min_length=1, max_length=100)
    admin_last_name: str = Field(..., min_length=1, max_length=100)
    timezone: str = Field(default="Africa/Cairo", max_length=64)
    currency: str = Field(default="EGP", max_length=3)
    custom_domain: str | None = Field(None, max_length=255)
    portal_title: str | None = Field(None, max_length=200)


class TenantOnboardResponse(BaseModel):
    """Result of a tenant onboarding operation."""

    clinic_id: UUID
    branding_id: UUID
    admin_user_id: UUID
