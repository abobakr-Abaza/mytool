"""Staff authentication dependencies — separate from clinic RBAC.

Staff roles (SUPER_ADMIN / SENIOR_TECH / STAFF_EXECUTION) are orthogonal
to clinic membership roles (admin / dentist / hygienist / ...). This
module provides ``get_staff_context`` (checks for an active StaffProfile
linked to the current user) and ``require_staff_permission`` (gates
endpoints by staff role).
"""

from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user
from app.core.auth.models import User
from app.database import get_db

from .models import StaffProfile

STAFF_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "SUPER_ADMIN": ["*"],
    "SENIOR_TECH": ["staff.read", "tasks.*", "audit.read", "chat.*"],
    "STAFF_EXECUTION": ["tasks.own", "finance.own", "chat.own"],
}


class StaffContext:
    """Context for a staff-authenticated request."""

    def __init__(self, user: User, profile: StaffProfile):
        self.user = user
        self.profile = profile
        self.staff_id: UUID = profile.id
        self.staff_role: str = profile.role
        self.user_id: UUID = user.id


async def get_staff_context(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StaffContext:
    """Resolve the current user's staff profile.

    Raises 403 if the user has no StaffProfile or is suspended/offboarded.
    """
    result = await db.execute(
        select(StaffProfile).where(StaffProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have a staff profile",
        )

    if profile.status == "SUSPENDED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff account is suspended",
        )

    if profile.status == "OFFBOARDED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff account has been offboarded",
        )

    return StaffContext(user=current_user, profile=profile)


def _staff_permission_matches(required: str, granted: str) -> bool:
    """Check if a granted permission satisfies a required permission.

    Supports wildcards:
    - ``*`` matches everything
    - ``module.*`` matches ``module.resource.action``
    """
    if granted == "*":
        return True
    if granted.endswith(".*"):
        prefix = granted[:-1]
        return required.startswith(prefix)
    return required == granted


def require_staff_permission(permission: str) -> Callable:
    """FastAPI dependency factory that gates by staff role.

    Usage::

        @router.get("/tasks")
        async def list_tasks(
            ctx: Annotated[StaffContext, Depends(get_staff_context)],
            _: Annotated[None, Depends(require_staff_permission("tasks.read"))],
        ):
            ...
    """

    async def permission_checker(
        ctx: Annotated[StaffContext, Depends(get_staff_context)],
    ) -> None:
        role_perms = STAFF_ROLE_PERMISSIONS.get(ctx.staff_role, [])
        if not any(_staff_permission_matches(permission, p) for p in role_perms):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Staff permission denied: {permission}",
            )

    return permission_checker
