"""Domain-resolution middleware for multi-tenant branding.

Reads the ``Host`` header (or ``X-Tenant-Domain`` for dev) and resolves
it to a ``clinic_id`` via the ``TenantBranding.custom_domain`` column.
Attaches the resolved ``clinic_id`` to ``request.state.tenant_clinic_id``
so downstream auto-scoping and the public branding endpoint can use it.

Middleware is registered in ``app.main`` and runs on every request.
"""

import logging

from fastapi import Request, Response
from sqlalchemy import select

from app.database import async_session_maker

from .models import TenantBranding

logger = logging.getLogger(__name__)


async def resolve_tenant_middleware(request: Request, call_next):
    """Resolve tenant from domain early in the request lifecycle.

    Order of precedence:
      1. ``X-Tenant-Domain`` header (dev / internal proxy)
      2. ``Host`` header (production)

    Stores the resolved ``clinic_id`` (str or None) on
    ``request.state.tenant_clinic_id``.
    """
    host = request.headers.get("x-tenant-domain") or request.headers.get("host")
    if host:
        # Strip port if present
        host = host.split(":")[0].strip().lower()
        try:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(TenantBranding.clinic_id).where(
                        TenantBranding.custom_domain == host,
                        TenantBranding.is_active.is_(True),
                    )
                )
                row = result.scalar_one_or_none()
                if row:
                    request.state.tenant_clinic_id = str(row)
                else:
                    request.state.tenant_clinic_id = None
        except Exception:
            logger.exception("Tenant resolution failed for host %s", host)
            request.state.tenant_clinic_id = None
    else:
        request.state.tenant_clinic_id = None

    response: Response = await call_next(request)
    return response
