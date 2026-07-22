"""Staff module — internal staff lifecycle, task/sprint management, and finance.

System-level operations module (not per-clinic). Manages staff profiles,
sprints/tasks with status-tracking, internal expenses/revenue, profit-share
calculation, payout ledger, and audit logging. Independent of clinical modules.
"""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import (
    AuditLog,
    ChatMessage,
    ChatUnreadStatus,
    Expense,
    GrossRevenue,
    PayoutLedger,
    ProfitShare,
    Sprint,
    StaffProfile,
    Task,
    TaskStatusLog,
)
from .router import router


class StaffModule(BaseModule):
    """Internal staff, task, and financial operations."""

    manifest = {
        "name": "staff",
        "version": "0.1.0",
        "summary": "Staff management, sprint/task tracking, and internal finance.",
        "author": "LaminarDent Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": [],
        "installable": True,
        "auto_install": True,
        "removable": False,
        "role_permissions": {},
        "frontend": {
            "layer_path": "frontend",
        },
    }

    def get_models(self) -> list:
        return [StaffProfile, Sprint, Task, TaskStatusLog, Expense, GrossRevenue, ProfitShare, PayoutLedger, AuditLog, ChatMessage, ChatUnreadStatus]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["staff.read", "staff.write", "tasks.read", "tasks.write", "tasks.own", "finance.read", "finance.write", "finance.own", "audit.read"]

    def get_tools(self) -> list:
        from . import tools
        return tools.get_tools()
