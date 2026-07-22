"""Agent tools for the staff module.

Each tool wraps an existing service method — no business logic duplication.
Permissions gate by staff RBAC string. All tools require a valid StaffContext.
"""

from app.core.agents.tools import Tool, ToolCategory

from .service import StaffProfileService, TaskService, FinanceService

from uuid import UUID


async def _update_task_status(ctx, task_id: str, status: str):
    task = await TaskService.get(ctx.db, UUID(task_id))
    return await TaskService.update_status(ctx.db, task, status, ctx.staff_id)


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="search_staff_profiles",
            description="Search and list all staff profiles. Returns id, name, email, role, status.",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
            handler=lambda ctx, **kw: StaffProfileService.list(ctx.db),
            permissions=["staff.read"],
            category=ToolCategory.READ,
            exposes_free_text=False,
        ),
        Tool(
            name="get_staff_profile",
            description="Get a single staff profile by ID.",
            parameters={
                "type": "object",
                "properties": {
                    "profile_id": {"type": "string", "format": "uuid", "description": "Staff profile UUID"},
                },
                "required": ["profile_id"],
            },
            handler=lambda ctx, profile_id, **kw: StaffProfileService.get(ctx.db, UUID(profile_id)),
            permissions=["staff.read"],
            category=ToolCategory.READ,
            exposes_free_text=False,
        ),
        Tool(
            name="list_tasks",
            description="List tasks with optional assignee, sprint, or status filter.",
            parameters={
                "type": "object",
                "properties": {
                    "assignee_id": {"type": "string", "format": "uuid", "description": "Filter by assignee"},
                    "sprint_id": {"type": "string", "format": "uuid", "description": "Filter by sprint"},
                    "status": {"type": "string", "description": "Filter by status: TODO, IN_PROGRESS, REVIEW, DONE"},
                },
                "required": [],
            },
            handler=lambda ctx, **kw: TaskService.list(
                ctx.db,
                assignee_id=UUID(kw["assignee_id"]) if kw.get("assignee_id") else None,
                sprint_id=UUID(kw["sprint_id"]) if kw.get("sprint_id") else None,
                status_filter=kw.get("status"),
            ),
            permissions=["tasks.read"],
            category=ToolCategory.READ,
            exposes_free_text=False,
        ),
        Tool(
            name="create_task",
            description="Create a new task and optionally assign it to a staff member.",
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title"},
                    "description": {"type": "string", "description": "Task description"},
                    "assignee_id": {"type": "string", "format": "uuid", "description": "Assignee staff profile UUID"},
                    "sprint_id": {"type": "string", "format": "uuid", "description": "Sprint UUID"},
                    "due_date": {"type": "string", "format": "date-time", "description": "Due date ISO 8601"},
                },
                "required": ["title"],
            },
            handler=lambda ctx, title, **kw: TaskService.create(
                ctx.db,
                {"title": title, **{k: v for k, v in kw.items() if v is not None}},
                ctx.staff_id,
            ),
            permissions=["tasks.write"],
            category=ToolCategory.WRITE,
            exposes_free_text=False,
        ),
        Tool(
            name="update_task_status",
            description="Transition a task's status: TODO → IN_PROGRESS → REVIEW → DONE.",
            parameters={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "format": "uuid", "description": "Task UUID"},
                    "status": {
                        "type": "string",
                        "enum": ["TODO", "IN_PROGRESS", "REVIEW", "DONE"],
                        "description": "New status",
                    },
                },
                "required": ["task_id", "status"],
            },
            handler=lambda ctx, task_id, status, **kw: _update_task_status(ctx, task_id, status),
            permissions=["tasks.write"],
            category=ToolCategory.WRITE,
            exposes_free_text=False,
        ),
        Tool(
            name="get_financial_summary",
            description="Get net profit calculation: gross revenue minus total expenses.",
            parameters={
                "type": "object",
                "properties": {
                    "period_start": {"type": "string", "format": "date-time", "description": "Start of period ISO 8601"},
                    "period_end": {"type": "string", "format": "date-time", "description": "End of period ISO 8601"},
                },
                "required": [],
            },
            handler=lambda ctx, **kw: FinanceService.get_summary(
                ctx.db,
                period_start=parse_iso(kw.get("period_start")) if kw.get("period_start") else None,
                period_end=parse_iso(kw.get("period_end")) if kw.get("period_end") else None,
            ),
            permissions=["finance.read"],
            category=ToolCategory.READ,
            exposes_free_text=False,
        ),
        Tool(
            name="get_staff_earnings",
            description="Calculate earnings for a specific staff member (net profit × share % minus paid).",
            parameters={
                "type": "object",
                "properties": {
                    "staff_id": {"type": "string", "format": "uuid", "description": "Staff profile UUID"},
                    "period_start": {"type": "string", "format": "date-time", "description": "Start of period ISO 8601"},
                    "period_end": {"type": "string", "format": "date-time", "description": "End of period ISO 8601"},
                },
                "required": ["staff_id"],
            },
            handler=lambda ctx, staff_id, **kw: FinanceService.get_staff_earnings(
                ctx.db,
                UUID(staff_id),
                period_start=parse_iso(kw.get("period_start")) if kw.get("period_start") else None,
                period_end=parse_iso(kw.get("period_end")) if kw.get("period_end") else None,
            ),
            permissions=["finance.read"],
            category=ToolCategory.READ,
            exposes_free_text=False,
        ),
    ]


from datetime import datetime
from uuid import UUID


def parse_iso(value: str) -> datetime | None:
    """Parse ISO 8601 string to datetime, or return None."""
    if not value:
        return None
    return datetime.fromisoformat(value)
