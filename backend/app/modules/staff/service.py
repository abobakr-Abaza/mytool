"""Business logic for staff, sprint/task, and expense operations."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.events import event_bus

from .events import (
    EXPENSE_CREATED,
    SPRINT_CREATED,
    SPRINT_STATUS_CHANGED,
    STAFF_CREATED,
    STAFF_ROLE_CHANGED,
    STAFF_STATUS_CHANGED,
    TASK_ASSIGNED,
    TASK_CREATED,
    TASK_STATUS_CHANGED,
)
from .models import (
    AuditLog,
    ChatMessage,
    ChatUnreadStatus,
    Expense,
    Sprint,
    StaffProfile,
    Task,
    TaskStatusLog,
)


# ---------------------------------------------------------------------------
# StaffProfileService
# ---------------------------------------------------------------------------


class StaffProfileService:
    """CRUD and lifecycle management for staff profiles."""

    @staticmethod
    async def list(db: AsyncSession) -> list[StaffProfile]:
        result = await db.execute(select(StaffProfile).order_by(StaffProfile.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, profile_id: UUID) -> StaffProfile | None:
        result = await db.execute(select(StaffProfile).where(StaffProfile.id == profile_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: UUID) -> StaffProfile | None:
        result = await db.execute(select(StaffProfile).where(StaffProfile.user_id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, data: dict, actor_id: UUID) -> StaffProfile:
        profile = StaffProfile(**data)
        db.add(profile)
        await db.flush()
        await _record_audit(db, actor_id, "staff.created", {"profile_id": str(profile.id), "role": profile.role})
        await event_bus.publish(STAFF_CREATED, {"profile_id": str(profile.id), "role": profile.role})
        return profile

    @staticmethod
    async def update(db: AsyncSession, profile: StaffProfile, data: dict, actor_id: UUID) -> StaffProfile:
        changed: list[str] = []
        for key, value in data.items():
            if hasattr(profile, key) and value is not None:
                setattr(profile, key, value)
                changed.append(key)
        await db.flush()
        if "role" in changed:
            await _record_audit(db, actor_id, "staff.role_changed", {
                "profile_id": str(profile.id), "old_role": None, "new_role": profile.role,
            })
            await event_bus.publish(STAFF_ROLE_CHANGED, {"profile_id": str(profile.id), "role": profile.role})
        if "status" in changed:
            await event_bus.publish(STAFF_STATUS_CHANGED, {"profile_id": str(profile.id), "status": profile.status})
        return profile

    @staticmethod
    async def update_status(db: AsyncSession, profile: StaffProfile, status: str, actor_id: UUID) -> StaffProfile:
        old_status = profile.status
        profile.status = status
        await db.flush()
        await _record_audit(db, actor_id, "staff.status_changed", {
            "profile_id": str(profile.id), "from": old_status, "to": status,
        })
        await event_bus.publish(STAFF_STATUS_CHANGED, {"profile_id": str(profile.id), "status": status})
        return profile

    @staticmethod
    async def update_role(db: AsyncSession, profile: StaffProfile, role: str, actor_id: UUID) -> StaffProfile:
        old_role = profile.role
        profile.role = role
        await db.flush()
        await _record_audit(db, actor_id, "staff.role_changed", {
            "profile_id": str(profile.id), "from": old_role, "to": role,
        })
        await event_bus.publish(STAFF_ROLE_CHANGED, {"profile_id": str(profile.id), "role": role})
        return profile


# ---------------------------------------------------------------------------
# SprintService
# ---------------------------------------------------------------------------


class SprintService:
    """CRUD for sprints."""

    @staticmethod
    async def list(db: AsyncSession) -> list[Sprint]:
        result = await db.execute(select(Sprint).order_by(Sprint.starts_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, sprint_id: UUID) -> Sprint | None:
        result = await db.execute(select(Sprint).where(Sprint.id == sprint_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, data: dict) -> Sprint:
        sprint = Sprint(**data)
        db.add(sprint)
        await db.flush()
        await event_bus.publish(SPRINT_CREATED, {"sprint_id": str(sprint.id), "name": sprint.name})
        return sprint

    @staticmethod
    async def update(db: AsyncSession, sprint: Sprint, data: dict) -> Sprint:
        status_changed = False
        for key, value in data.items():
            if value is not None:
                if key == "status" and value != sprint.status:
                    status_changed = True
                setattr(sprint, key, value)
        await db.flush()
        if status_changed:
            await event_bus.publish(SPRINT_STATUS_CHANGED, {"sprint_id": str(sprint.id), "status": sprint.status})
        return sprint


# ---------------------------------------------------------------------------
# TaskService
# ---------------------------------------------------------------------------


_TASK_VALID_TRANSITIONS: dict[str, list[str]] = {
    "TODO": ["IN_PROGRESS"],
    "IN_PROGRESS": ["REVIEW", "TODO"],
    "REVIEW": ["DONE", "IN_PROGRESS"],
    "DONE": [],
}


class TaskService:
    """CRUD and lifecycle for tasks with status-tracking."""

    @staticmethod
    async def list(
        db: AsyncSession,
        assignee_id: UUID | None = None,
        sprint_id: UUID | None = None,
        status_filter: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Task], int]:
        page_size = min(max(page_size, 1), 100)
        page = max(page, 1)
        offset = (page - 1) * page_size

        conditions = []
        if assignee_id:
            conditions.append(Task.assignee_id == assignee_id)
        if sprint_id:
            conditions.append(Task.sprint_id == sprint_id)
        if status_filter:
            conditions.append(Task.status == status_filter)

        total = (
            await db.execute(select(func.count(Task.id)).where(*conditions))
        ).scalar() or 0

        result = await db.execute(
            select(Task).where(*conditions).order_by(Task.created_at.desc()).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def get(db: AsyncSession, task_id: UUID) -> Task | None:
        from sqlalchemy.orm import selectinload

        result = await db.execute(
            select(Task)
            .options(selectinload(Task.assignee), selectinload(Task.sprint), selectinload(Task.status_logs))
            .where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, data: dict, actor_id: UUID) -> Task:
        task = Task(**data)
        db.add(task)
        await db.flush()
        TaskStatusLog(task_id=task.id, from_status=None, to_status=task.status, changed_by=actor_id)
        await db.flush()
        await event_bus.publish(TASK_CREATED, {"task_id": str(task.id), "title": task.title})
        if task.assignee_id:
            await event_bus.publish(TASK_ASSIGNED, {"task_id": str(task.id), "assignee_id": str(task.assignee_id)})
        return task

    @staticmethod
    async def update(db: AsyncSession, task: Task, data: dict) -> Task:
        for key, value in data.items():
            if value is not None:
                setattr(task, key, value)
        await db.flush()
        return task

    @staticmethod
    async def update_status(db: AsyncSession, task: Task, new_status: str, actor_id: UUID) -> Task:
        allowed = _TASK_VALID_TRANSITIONS.get(task.status, [])
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot transition from {task.status} to {new_status}. "
                f"Allowed: {allowed if allowed else 'terminal state'}.",
            )
        old_status = task.status
        task.status = new_status
        log = TaskStatusLog(task_id=task.id, from_status=old_status, to_status=new_status, changed_by=actor_id)
        db.add(log)
        await db.flush()
        await event_bus.publish(TASK_STATUS_CHANGED, {
            "task_id": str(task.id), "from": old_status, "to": new_status,
        })
        return task

    @staticmethod
    async def get_workload(db: AsyncSession) -> list[dict]:
        """Return active-task counts per staff member."""
        counts = (
            await db.execute(
                select(
                    Task.assignee_id,
                    func.count(Task.id).label("total"),
                    func.sum(case((Task.status == "TODO", 1), else_=0)).label("todo"),
                    func.sum(case((Task.status == "IN_PROGRESS", 1), else_=0)).label("in_progress"),
                    func.sum(case((Task.status == "REVIEW", 1), else_=0)).label("review"),
                    func.sum(case((Task.status == "DONE", 1), else_=0)).label("done"),
                ).where(Task.assignee_id.isnot(None)).group_by(Task.assignee_id)
            )
        ).all()

        result_rows = []
        for row in counts:
            profile = await db.get(StaffProfile, row.assignee_id)
            result_rows.append({
                "staff_id": row.assignee_id,
                "name": profile.name if profile else "Unknown",
                "total_tasks": row.total or 0,
                "todo": row.todo or 0,
                "in_progress": row.in_progress or 0,
                "review": row.review or 0,
                "done": row.done or 0,
            })
        return result_rows


# ---------------------------------------------------------------------------
# FinanceService — simplified to expense-only
# ---------------------------------------------------------------------------


class FinanceService:
    """Simple expense tracking."""

    @staticmethod
    async def list_expenses(db: AsyncSession) -> list[Expense]:
        result = await db.execute(select(Expense).order_by(Expense.date.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def create_expense(db: AsyncSession, data: dict, actor_id: UUID) -> Expense:
        expense = Expense(created_by=actor_id, **data)
        db.add(expense)
        await db.flush()
        await _record_audit(db, actor_id, "expense.created", {
            "expense_id": str(expense.id), "amount": str(expense.amount), "category": expense.category,
        })
        await event_bus.publish(EXPENSE_CREATED, {"expense_id": str(expense.id), "amount": str(expense.amount)})
        return expense

    @staticmethod
    async def delete_expense(db: AsyncSession, expense: Expense, actor_id: UUID) -> None:
        await db.delete(expense)
        await _record_audit(db, actor_id, "expense.deleted", {"expense_id": str(expense.id)})

    @staticmethod
    async def get_expense(db: AsyncSession, expense_id: UUID) -> Expense | None:
        result = await db.execute(select(Expense).where(Expense.id == expense_id))
        return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# AuditService
# ---------------------------------------------------------------------------


class AuditService:
    """Audit log recording and querying."""

    @staticmethod
    async def list(db: AsyncSession, page: int = 1, page_size: int = 50) -> tuple[list[AuditLog], int]:
        page_size = min(max(page_size, 1), 200)
        page = max(page, 1)
        offset = (page - 1) * page_size

        total = (await db.execute(select(func.count(AuditLog.id)))).scalar() or 0
        result = await db.execute(
            select(AuditLog).order_by(AuditLog.timestamp.desc()).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# ChatService
# ---------------------------------------------------------------------------


class ChatService:
    """Chat message persistence and retrieval."""

    @staticmethod
    async def get_history(
        db: AsyncSession,
        channel_type: str,
        channel_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[ChatMessage], int]:
        page_size = min(max(page_size, 1), 200)
        page = max(page, 1)
        offset = (page - 1) * page_size

        total = (
            await db.execute(
                select(func.count(ChatMessage.id)).where(
                    ChatMessage.channel_type == channel_type,
                    ChatMessage.channel_id == channel_id,
                )
            )
        ).scalar() or 0

        result = await db.execute(
            select(ChatMessage)
            .options(selectinload(ChatMessage.sender))
            .where(
                ChatMessage.channel_type == channel_type,
                ChatMessage.channel_id == channel_id,
            )
            .order_by(ChatMessage.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        messages = list(result.scalars().all())
        messages.reverse()
        return messages, total

    @staticmethod
    async def save_message(
        db: AsyncSession,
        sender_id: UUID,
        channel_type: str,
        channel_id: str,
        message_text: str,
        attachments: dict | None = None,
    ) -> ChatMessage:
        msg = ChatMessage(
            sender_id=sender_id,
            channel_type=channel_type,
            channel_id=channel_id,
            message_text=message_text,
            attachments=attachments,
        )
        db.add(msg)
        await db.flush()
        await db.refresh(msg)
        result = await db.execute(
            select(ChatMessage).options(selectinload(ChatMessage.sender)).where(ChatMessage.id == msg.id)
        )
        return result.scalar_one()

    @staticmethod
    async def mark_read(
        db: AsyncSession,
        staff_id: UUID,
        channel_type: str,
        channel_id: str,
    ) -> None:
        result = await db.execute(
            select(ChatUnreadStatus).where(
                ChatUnreadStatus.staff_id == staff_id,
                ChatUnreadStatus.channel_type == channel_type,
                ChatUnreadStatus.channel_id == channel_id,
            )
        )
        entry = result.scalar_one_or_none()
        if entry:
            entry.last_read_at = datetime.now()
        else:
            entry = ChatUnreadStatus(
                staff_id=staff_id,
                channel_type=channel_type,
                channel_id=channel_id,
            )
            db.add(entry)
        await db.flush()

    @staticmethod
    async def get_unread_counts(
        db: AsyncSession, staff_id: UUID
    ) -> list[dict]:
        result = await db.execute(
            select(ChatUnreadStatus).where(ChatUnreadStatus.staff_id == staff_id)
        )
        read_entries = {r.channel_type + ":" + r.channel_id: r.last_read_at for r in result.scalars().all()}

        channels_result = await db.execute(
            select(
                ChatMessage.channel_type,
                ChatMessage.channel_id,
                func.max(ChatMessage.created_at).label("last_msg_at"),
                func.count(ChatMessage.id).label("total"),
            ).group_by(ChatMessage.channel_type, ChatMessage.channel_id)
        )
        unread = []
        for row in channels_result.all():
            key = f"{row.channel_type}:{row.channel_id}"
            last_read = read_entries.get(key)
            if last_read is None or row.last_msg_at > last_read:
                count_cond = [
                    ChatMessage.channel_type == row.channel_type,
                    ChatMessage.channel_id == row.channel_id,
                ]
                if last_read is not None:
                    count_cond.append(ChatMessage.created_at > last_read)
                count_result = await db.execute(
                    select(func.count(ChatMessage.id)).where(*count_cond)
                )
                cnt = count_result.scalar() or 0
                if last_read is None:
                    cnt = row.total
                unread.append({
                    "channel_type": row.channel_type,
                    "channel_id": row.channel_id,
                    "unread_count": cnt,
                    "last_message_at": row.last_msg_at,
                })
        return unread


# ---------------------------------------------------------------------------
# WebSocket Connection Manager
# ---------------------------------------------------------------------------


class ConnectionManager:
    """Manage active WebSocket connections per channel room.

    Rooms follow the convention:
      - ``DIRECT:<staff_id_A>:<staff_id_B>`` (sorted IDs)
      - ``TASK:<task_id>``
      - ``SPRINT:<sprint_id>``
      - ``GENERAL``
    """

    def __init__(self) -> None:
        self._rooms: dict[str, set[object]] = {}

    def join(self, room: str, websocket: object) -> None:
        if room not in self._rooms:
            self._rooms[room] = set()
        self._rooms[room].add(websocket)

    def leave(self, room: str, websocket: object) -> None:
        self._rooms.get(room, set()).discard(websocket)
        if room in self._rooms and not self._rooms[room]:
            del self._rooms[room]

    def leave_all(self, websocket: object) -> None:
        for room in list(self._rooms.keys()):
            self._rooms[room].discard(websocket)
            if not self._rooms[room]:
                del self._rooms[room]

    async def broadcast(self, room: str, message: str) -> None:
        for ws in self._rooms.get(room, set()):
            try:
                await ws.send_text(message)
            except Exception:
                pass

    def get_room_size(self, room: str) -> int:
        return len(self._rooms.get(room, set()))


chat_manager = ConnectionManager()


async def _record_audit(db: AsyncSession, user_id: UUID, action: str, details: dict | None = None) -> None:
    """Record a sensitive action in the audit log."""
    log = AuditLog(user_id=user_id, action=action, details=details or {})
    db.add(log)
    await db.flush()



