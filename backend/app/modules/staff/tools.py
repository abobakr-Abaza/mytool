"""Agent tools for the staff module."""

from app.core.agents.tools import Tool, ToolCategory

from .service import StaffProfileService, TaskService

from uuid import UUID


async def _update_task_status(ctx, task_id: str, status: str):
    task = await TaskService.get(ctx.db, UUID(task_id))
    return await TaskService.update_status(ctx.db, task, status, ctx.staff_id)


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="search_staff_profiles",
            description="Search and list all staff profiles.",
            parameters={"type": "object", "properties": {}, "required": []},
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
            description="List tasks with optional filters.",
            parameters={
                "type": "object",
                "properties": {
                    "assignee_id": {"type": "string", "format": "uuid"},
                    "sprint_id": {"type": "string", "format": "uuid"},
                    "status": {"type": "string", "enum": ["TODO", "IN_PROGRESS", "REVIEW", "DONE"]},
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
            description="Create a new task.",
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title"},
                    "assignee_id": {"type": "string", "format": "uuid"},
                    "sprint_id": {"type": "string", "format": "uuid"},
                },
                "required": ["title"],
            },
            handler=lambda ctx, title, **kw: TaskService.create(
                ctx.db, {"title": title, **{k: v for k, v in kw.items() if v is not None}}, ctx.staff_id,
            ),
            permissions=["tasks.write"],
            category=ToolCategory.WRITE,
            exposes_free_text=False,
        ),
        Tool(
            name="update_task_status",
            description="Transition a task's status.",
            parameters={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "format": "uuid"},
                    "status": {"type": "string", "enum": ["TODO", "IN_PROGRESS", "REVIEW", "DONE"]},
                },
                "required": ["task_id", "status"],
            },
            handler=lambda ctx, task_id, status, **kw: _update_task_status(ctx, task_id, status),
            permissions=["tasks.write"],
            category=ToolCategory.WRITE,
            exposes_free_text=False,
        ),
    ]


from uuid import UUID
