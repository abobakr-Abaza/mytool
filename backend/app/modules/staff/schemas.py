"""Pydantic schemas for the staff module."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- Staff Profile ---------------------------------------------------------


class StaffProfileCreate(BaseModel):
    user_id: UUID
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(max_length=255)
    role: str = Field(pattern=r"^(SUPER_ADMIN|SENIOR_TECH|STAFF_EXECUTION)$")
    status: str = Field(default="ACTIVE", pattern=r"^(ACTIVE|PROBATION|SUSPENDED|OFFBOARDED)$")
    probation_ends_at: datetime | None = None


class StaffProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=255)
    role: str | None = Field(default=None, pattern=r"^(SUPER_ADMIN|SENIOR_TECH|STAFF_EXECUTION)$")
    status: str | None = Field(default=None, pattern=r"^(ACTIVE|PROBATION|SUSPENDED|OFFBOARDED)$")
    probation_ends_at: datetime | None = None


class StaffProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    email: str
    role: str
    status: str
    probation_ends_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StaffProfileBrief(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    status: str

    model_config = ConfigDict(from_attributes=True)


# --- Sprint ----------------------------------------------------------------


class SprintCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    goal: str | None = None
    starts_at: datetime
    ends_at: datetime
    status: str = Field(default="PLANNED", pattern=r"^(PLANNED|ACTIVE|COMPLETED|CANCELLED)$")


class SprintUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    goal: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: str | None = Field(default=None, pattern=r"^(PLANNED|ACTIVE|COMPLETED|CANCELLED)$")


class SprintResponse(BaseModel):
    id: UUID
    name: str
    goal: str | None
    starts_at: datetime
    ends_at: datetime
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Task ------------------------------------------------------------------


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    assignee_id: UUID | None = None
    status: str = Field(default="TODO", pattern=r"^(TODO|IN_PROGRESS|REVIEW|DONE)$")
    sprint_id: UUID | None = None
    due_date: datetime | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    assignee_id: UUID | None = None
    sprint_id: UUID | None = None
    due_date: datetime | None = None


class TaskStatusUpdate(BaseModel):
    status: str = Field(pattern=r"^(TODO|IN_PROGRESS|REVIEW|DONE)$")


class TaskStatusLogResponse(BaseModel):
    id: UUID
    task_id: UUID
    from_status: str | None
    to_status: str
    changed_by: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    assignee_id: UUID | None
    assignee: StaffProfileBrief | None = None
    status: str
    sprint_id: UUID | None
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime
    status_logs: list[TaskStatusLogResponse] | None = None

    model_config = ConfigDict(from_attributes=True)


class TaskBrief(BaseModel):
    id: UUID
    title: str
    assignee_id: UUID | None
    status: str
    due_date: datetime | None

    model_config = ConfigDict(from_attributes=True)


# --- Workload metrics ------------------------------------------------------


class WorkloadResponse(BaseModel):
    staff_id: UUID
    name: str
    total_tasks: int
    todo: int
    in_progress: int
    review: int
    done: int


# --- Expense ---------------------------------------------------------------


class ExpenseCreate(BaseModel):
    category: str = Field(pattern=r"^(SERVER|MARKETING|TOOLS|MISC)$")
    amount: Decimal = Field(gt=Decimal("0"), decimal_places=2)
    description: str | None = None
    date: datetime


class ExpenseResponse(BaseModel):
    id: UUID
    category: str
    amount: Decimal
    description: str | None
    date: datetime
    created_by: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Financial Summary -----------------------------------------------------


class SimpleFinancialSummary(BaseModel):
    total_expenses: Decimal
    period_start: datetime | None = None
    period_end: datetime | None = None


# --- Audit Log -------------------------------------------------------------


class AuditLogResponse(BaseModel):
    id: UUID
    user_id: UUID
    action: str
    details: dict | None
    timestamp: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Chat -------------------------------------------------------------------


class ChatMessageResponse(BaseModel):
    id: UUID
    sender_id: UUID
    sender_name: str | None = None
    channel_type: str
    channel_id: str
    message_text: str
    attachments: dict | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageResponse]
    total: int
    page: int
    page_size: int


class ChatReadRequest(BaseModel):
    channel_type: str
    channel_id: str
