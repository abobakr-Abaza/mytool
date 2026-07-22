"""Tenant onboarding service.

Creates a Clinic, TenantBranding, admin User, and ClinicMembership
in a single transaction. Intended for SUPER_ADMIN use only.
"""

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership, User
from app.core.auth.service import hash_password as get_password_hash

from .models import TenantBranding


class TenantOnboardingError(Exception):
    """Raised when onboarding fails for a known reason."""


async def onboard_tenant(
    db: AsyncSession,
    *,
    clinic_name: str,
    tax_id: str,
    admin_email: str,
    admin_password: str,
    admin_first_name: str,
    admin_last_name: str,
    timezone: str = "Europe/Madrid",
    currency: str = "EUR",
    custom_domain: str | None = None,
    portal_title: str | None = None,
) -> tuple[Clinic, TenantBranding, User]:
    """Create a new tenant with clinic, branding, and admin user.

    Returns the ``(Clinic, TenantBranding, User)`` tuple.

    Raises ``TenantOnboardingError`` on duplicate email or domain.
    """
    # Check for duplicate email
    result = await db.execute(select(User).where(User.email == admin_email))
    if result.scalar_one_or_none():
        raise TenantOnboardingError(f"User with email '{admin_email}' already exists")

    # Check for duplicate custom domain
    if custom_domain:
        result = await db.execute(
            select(TenantBranding).where(TenantBranding.custom_domain == custom_domain)
        )
        if result.scalar_one_or_none():
            raise TenantOnboardingError(
                f"Tenant with domain '{custom_domain}' already exists"
            )

    clinic_id = uuid4()
    user_id = uuid4()
    branding_id = uuid4()

    clinic = Clinic(
        id=clinic_id,
        name=clinic_name,
        tax_id=tax_id,
        timezone=timezone,
        currency=currency,
    )
    db.add(clinic)

    user = User(
        id=user_id,
        email=admin_email,
        password_hash=get_password_hash(admin_password),
        first_name=admin_first_name,
        last_name=admin_last_name,
        is_active=True,
    )
    db.add(user)

    membership = ClinicMembership(
        user_id=user_id,
        clinic_id=clinic_id,
        role="admin",
    )
    db.add(membership)

    branding = TenantBranding(
        id=branding_id,
        clinic_id=clinic_id,
        custom_domain=custom_domain,
        portal_title=portal_title,
        is_active=True,
    )
    db.add(branding)

    await db.flush()

    return clinic, branding, user
