"""API routes for tenant branding and onboarding."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.auth.dependencies import ClinicContext, get_clinic_context, require_permission
from app.core.schemas import ApiResponse
from app.database import get_db

from .models import TenantBranding
from .onboarding import TenantOnboardingError, onboard_tenant
from .schemas import (
    BrandingPublic,
    BrandingResponse,
    BrandingUpdate,
    TenantOnboardRequest,
    TenantOnboardResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["tenancy"])


def _verify_super_admin(api_key: str) -> None:
    """Check the ``X-Super-Admin-Key`` header against the configured key."""
    if not settings.SUPER_ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Super admin API key not configured on this instance",
        )
    if api_key != settings.SUPER_ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid super admin API key",
        )


# ── Public branding endpoint ─────────────────────────────────────


@router.get("/api/v1/branding", response_model=ApiResponse[BrandingPublic])
async def get_public_branding(
    request: Request,
) -> ApiResponse[BrandingPublic]:
    """Return branding for the resolved tenant domain.

    No authentication required. Reads the resolved ``clinic_id`` from
    the domain-resolution middleware (``request.state.tenant_clinic_id``).
    If no domain match, returns an empty branding response.
    """
    clinic_id_str: str | None = getattr(request.state, "tenant_clinic_id", None)
    if not clinic_id_str:
        return ApiResponse(data=BrandingPublic())

    from app.database import async_session_maker

    async with async_session_maker() as session:
        result = await session.execute(
            select(TenantBranding).where(TenantBranding.clinic_id == UUID(clinic_id_str))
        )
        branding = result.scalar_one_or_none()
        if not branding or not branding.is_active:
            return ApiResponse(data=BrandingPublic())

        return ApiResponse(
            data=BrandingPublic(
                logo_url=branding.logo_url,
                favicon_url=branding.favicon_url,
                primary_color=branding.primary_color,
                secondary_color=branding.secondary_color,
                accent_color=branding.accent_color,
                portal_title=branding.portal_title,
                custom_css=branding.custom_css,
            )
        )


# ── Admin branding CRUD ──────────────────────────────────────────


@router.get(
    "/api/v1/admin/branding/{clinic_id}",
    response_model=ApiResponse[BrandingResponse],
)
async def get_branding(
    clinic_id: UUID,
    _: Annotated[None, Depends(require_permission("admin.branding.read"))],
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[BrandingResponse]:
    """Get branding for a specific clinic (admin only)."""
    if ctx.role != "admin" and str(ctx.clinic_id) != str(clinic_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    result = await db.execute(
        select(TenantBranding).where(TenantBranding.clinic_id == clinic_id)
    )
    branding = result.scalar_one_or_none()
    if not branding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Branding not found"
        )
    return ApiResponse(data=BrandingResponse.model_validate(branding))


@router.put(
    "/api/v1/admin/branding/{clinic_id}",
    response_model=ApiResponse[BrandingResponse],
)
async def update_branding(
    clinic_id: UUID,
    data: BrandingUpdate,
    _: Annotated[None, Depends(require_permission("admin.branding.write"))],
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[BrandingResponse]:
    """Update branding for a specific clinic (admin only)."""
    if ctx.role != "admin" and str(ctx.clinic_id) != str(clinic_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    result = await db.execute(
        select(TenantBranding).where(TenantBranding.clinic_id == clinic_id)
    )
    branding = result.scalar_one_or_none()
    if not branding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Branding not found"
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(branding, field, value)

    await db.flush()
    await db.refresh(branding)
    return ApiResponse(data=BrandingResponse.model_validate(branding))


# ── Super admin tenant onboarding ─────────────────────────────────


@router.post(
    "/api/v1/admin/tenants",
    response_model=ApiResponse[TenantOnboardResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_tenant(
    request: Request,
    data: TenantOnboardRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[TenantOnboardResponse]:
    """Create a new tenant with clinic, branding, and admin user.

    Requires ``X-Super-Admin-Key`` header matching ``SUPER_ADMIN_API_KEY``.
    """
    api_key = request.headers.get("x-super-admin-key", "")
    _verify_super_admin(api_key)

    try:
        clinic, branding, user = await onboard_tenant(
            db,
            clinic_name=data.clinic_name,
            tax_id=data.tax_id,
            admin_email=data.admin_email,
            admin_password=data.admin_password,
            admin_first_name=data.admin_first_name,
            admin_last_name=data.admin_last_name,
            timezone=data.timezone,
            currency=data.currency,
            custom_domain=data.custom_domain,
            portal_title=data.portal_title,
        )
    except TenantOnboardingError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    await db.commit()

    return ApiResponse(
        data=TenantOnboardResponse(
            clinic_id=clinic.id,
            branding_id=branding.id,
            admin_user_id=user.id,
        )
    )
