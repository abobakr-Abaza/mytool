"""Agent tools for the staff module."""

from uuid import UUID

from pydantic import BaseModel, Field

from app.core.agents import AgentContext, Tool, ToolCategory

from .service import StaffProfileService, TaskService


class NoArgs(BaseModel):
    pass


class ProfileArgs(BaseModel):
    profile_id: UUID = Field(description="Staff profile UUID")


class ListTasksArgs(BaseModel):
    assignee_id: UUID | None = Field(default=None, description="Filter by assignee UUID")
    sprint_id: UUID | None = Field(default=None, description="Filter by sprint UUID")
    status: str | None = Field(default=None, description="Filter by status: TODO, IN_PROGRESS, REVIEW, DONE")


class CreateTaskArgs(BaseModel):
    title: str = Field(min_length=1, description="Task title")
    assignee_id: UUID | None = Field(default=None, description="Assignee UUID")
    sprint_id: UUID | None = Field(default=None, description="Sprint UUID")


class UpdateTaskStatusArgs(BaseModel):
    task_id: UUID = Field(description="Task UUID")
    status: str = Field(description="New status: TODO, IN_PROGRESS, REVIEW, DONE")


async def _search_profiles(ctx: AgentContext, _params: NoArgs) -> dict:
    profiles = await StaffProfileService.list(ctx.db)
    return {
        "profiles": [
            {
                "id": str(p.id),
                "name": p.display_name or f"{p.first_name} {p.last_name}",
                "role": p.role,
                "status": p.status,
            }
            for p in profiles
        ],
        "total": len(profiles),
    }


async def _get_profile(ctx: AgentContext, params: ProfileArgs) -> dict:
    profile = await StaffProfileService.get(ctx.db, params.profile_id)
    if profile is None:
        return {"error": "not_found"}
    return {
        "id": str(profile.id),
        "name": profile.display_name or f"{profile.first_name} {profile.last_name}",
        "role": profile.role,
        "status": profile.status,
        "email": profile.email,
    }


async def _list_tasks(ctx: AgentContext, params: ListTasksArgs) -> dict:
    items, total = await TaskService.list(
        ctx.db,
        assignee_id=params.assignee_id,
        sprint_id=params.sprint_id,
        status_filter=params.status,
    )
    return {
        "tasks": [
            {
                "id": str(t.id),
                "title": t.title,
                "status": t.status,
                "assignee_id": str(t.assignee_id) if t.assignee_id else None,
            }
            for t in items
        ],
        "total": total,
    }


async def _create_task(ctx: AgentContext, params: CreateTaskArgs) -> dict:
    task = await TaskService.create(
        ctx.db,
        params.model_dump(exclude_none=True),
        ctx.staff_id,
    )
    return {"id": str(task.id), "title": task.title, "status": task.status}


async def _update_task_status(ctx: AgentContext, params: UpdateTaskStatusArgs) -> dict:
    task = await TaskService.get(ctx.db, params.task_id)
    if task is None:
        return {"error": "not_found"}
    task = await TaskService.update_status(ctx.db, task, params.status, ctx.staff_id)
    return {"id": str(task.id), "title": task.title, "status": task.status}


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="search_staff_profiles",
            description="Search and list all staff profiles.",
            parameters=NoArgs,
            handler=_search_profiles,
            permissions=["staff.read"],
            category=ToolCategory.READ,
        ),
        Tool(
            name="get_staff_profile",
            description="Get a single staff profile by ID.",
            parameters=ProfileArgs,
            handler=_get_profile,
            permissions=["staff.read"],
            category=ToolCategory.READ,
        ),
        Tool(
            name="list_tasks",
            description="List tasks with optional filters.",
            parameters=ListTasksArgs,
            handler=_list_tasks,
            permissions=["tasks.read"],
            category=ToolCategory.READ,
        ),
        Tool(
            name="create_task",
            description="Create a new task.",
            parameters=CreateTaskArgs,
            handler=_create_task,
            permissions=["tasks.write"],
            category=ToolCategory.WRITE,
        ),
        Tool(
            name="update_task_status",
            description="Transition a task's status.",
            parameters=UpdateTaskStatusArgs,
            handler=_update_task_status,
            permissions=["tasks.write"],
            category=ToolCategory.WRITE,
        ),
    ]
