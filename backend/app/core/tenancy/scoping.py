"""Auto-scoping layer that injects ``clinic_id`` into queries.

This module provides an optional safety net for multi-tenant data
isolation. It hooks into the SQLAlchemy session lifecycle to detect
queries that are missing a ``clinic_id`` filter and logs a warning.

The scoping runs in **lenient** mode by default — it warns but does
not block queries. This allows existing code to work while the team
tightens tenant isolation incrementally.

Activation is controlled by the ``ENABLE_TENANT_SCOPING`` setting.
"""

import logging
from uuid import UUID

from sqlalchemy.event import listens_for
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Per-request tenant clinic_id is stored in Flask/FastAPI request state
# and propagated here via a contextvar or thread-local. For FastAPI we
# use a simple module-level slot that the ``get_db`` dependency sets
# before yielding the session.
_current_tenant_clinic_id: UUID | None = None


def set_tenant_clinic_id(clinic_id: UUID | None) -> None:
    """Set the tenant clinic_id for the current request scope."""
    global _current_tenant_clinic_id
    _current_tenant_clinic_id = clinic_id


def get_tenant_clinic_id() -> UUID | None:
    """Get the tenant clinic_id for the current request scope."""
    return _current_tenant_clinic_id


def install_scoping(session_maker) -> None:
    """Install auto-scoping event listeners on the session maker.

    Call once at startup from ``database.py``.
    """

    @listens_for(session_maker, "before_flush")
    def _warn_missing_clinic_filter(session: Session, flush_context, instances):
        """Log a warning when a multi-tenant table is flushed without
        a ``clinic_id`` filter on the primary model.

        This is a best-effort heuristic that checks new/updated instances.
        It does NOT inspect the full query — that would require deeper
        SQL compilation hooks — so it may miss some cases.
        """
        tenant_id = _current_tenant_clinic_id
        if tenant_id is None:
            return

        for instance in session.new:
            _check_instance(instance, tenant_id)

        for instance in session.dirty:
            _check_instance(instance, tenant_id)


    def _check_instance(instance, tenant_id: UUID) -> None:
        table = instance.__table__ if hasattr(instance, "__table__") else None
        if table is None:
            return
        # We only care about tables that have a ``clinic_id`` column
        if "clinic_id" not in table.columns:
            return
        value = getattr(instance, "clinic_id", None)
        if value is None:
            logger.warning(
                "Tenant scoping: %s instance inserted/updated without "
                "clinic_id (current tenant=%s). Table: %s",
                type(instance).__name__,
                tenant_id,
                table.name,
            )
