"""Tenant context and resolution interfaces.

See ``docs/technical/multi-tenancy.md`` for the architectural overview.
"""

from .context import TenantContext
from .middleware import resolve_tenant_middleware
from .models import TenantBranding
from .onboarding import TenantOnboardingError, onboard_tenant
from .resolver import TenantResolver
from .schemas import (
    BrandingPublic,
    BrandingResponse,
    BrandingUpdate,
    TenantOnboardRequest,
    TenantOnboardResponse,
)
from .scoping import get_tenant_clinic_id, install_scoping, set_tenant_clinic_id
from .single import SingleTenantResolver

__all__ = [
    "BrandingPublic",
    "BrandingResponse",
    "BrandingUpdate",
    "get_tenant_clinic_id",
    "install_scoping",
    "onboard_tenant",
    "resolve_tenant_middleware",
    "set_tenant_clinic_id",
    "SingleTenantResolver",
    "TenantBranding",
    "TenantContext",
    "TenantOnboardRequest",
    "TenantOnboardingError",
    "TenantOnboardResponse",
    "TenantResolver",
]
