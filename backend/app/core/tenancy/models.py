"""Tenant branding and domain resolution models."""

from uuid import uuid4

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin


class TenantBranding(Base, TimestampMixin):
    """White-label branding for a single clinic/tenant.

    One-to-one with ``Clinic``. Stores everything needed to customise
    the look, feel, and domain of a tenant's portal.
    """

    __tablename__ = "tenant_brandings"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False, unique=True, index=True
    )
    logo_url: Mapped[str | None] = mapped_column(String(512))
    favicon_url: Mapped[str | None] = mapped_column(String(512))
    primary_color: Mapped[str | None] = mapped_column(String(7))
    secondary_color: Mapped[str | None] = mapped_column(String(7))
    accent_color: Mapped[str | None] = mapped_column(String(7))
    custom_domain: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    portal_title: Mapped[str | None] = mapped_column(String(200))
    custom_css: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    clinic = relationship("Clinic", backref="branding", uselist=False)
