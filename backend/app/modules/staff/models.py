"""Staff, sprint, task, finance, and audit log models."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.core.auth.models import User


class StaffProfile(Base, TimestampMixin):
    __tablename__ = "staff_profiles"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    probation_ends_at: Mapped[date | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship()


class Sprint(Base, TimestampMixin):
    __tablename__ = "staff_sprints"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    goal: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PLANNED")


class Task(Base, TimestampMixin):
    __tablename__ = "staff_tasks"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    assignee_id: Mapped[UUID | None] = mapped_column(ForeignKey("staff_profiles.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="TODO")
    sprint_id: Mapped[UUID | None] = mapped_column(ForeignKey("staff_sprints.id"), index=True)
    due_date: Mapped[date | None] = mapped_column(DateTime(timezone=True))

    assignee: Mapped[StaffProfile | None] = relationship(foreign_keys=[assignee_id])
    sprint: Mapped[Sprint | None] = relationship()
    status_logs: Mapped[list[TaskStatusLog]] = relationship(back_populates="task", cascade="all, delete-orphan")


class TaskStatusLog(Base, TimestampMixin):
    __tablename__ = "staff_task_status_logs"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("staff_tasks.id"), index=True, nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_by: Mapped[UUID] = mapped_column(ForeignKey("staff_profiles.id"), nullable=False)

    task: Mapped[Task] = relationship(back_populates="status_logs")
    changer: Mapped[StaffProfile] = relationship(foreign_keys=[changed_by])


class Expense(Base, TimestampMixin):
    __tablename__ = "staff_expenses"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    date: Mapped[date] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("staff_profiles.id"), nullable=False)

    creator: Mapped[StaffProfile] = relationship(foreign_keys=[created_by])


class GrossRevenue(Base, TimestampMixin):
    __tablename__ = "staff_gross_revenues"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    date: Mapped[date] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("staff_profiles.id"), nullable=False)

    creator: Mapped[StaffProfile] = relationship(foreign_keys=[created_by])


class ProfitShare(Base, TimestampMixin):
    __tablename__ = "staff_profit_shares"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    staff_id: Mapped[UUID] = mapped_column(ForeignKey("staff_profiles.id"), index=True, nullable=False)
    share_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    vesting_status: Mapped[str] = mapped_column(String(20), nullable=False, default="LOCKED")
    vesting_condition: Mapped[str | None] = mapped_column(Text)

    staff: Mapped[StaffProfile] = relationship(foreign_keys=[staff_id])


class PayoutLedger(Base, TimestampMixin):
    __tablename__ = "staff_payout_ledger"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    staff_id: Mapped[UUID] = mapped_column(ForeignKey("staff_profiles.id"), index=True, nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    period_start: Mapped[date] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[date] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    paid_by: Mapped[UUID] = mapped_column(ForeignKey("staff_profiles.id"), nullable=False)

    staff: Mapped[StaffProfile] = relationship(foreign_keys=[staff_id])
    payer: Mapped[StaffProfile] = relationship(foreign_keys=[paid_by])


class AuditLog(Base, TimestampMixin):
    __tablename__ = "staff_audit_logs"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("staff_profiles.id"), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[StaffProfile] = relationship()


class ChatMessage(Base, TimestampMixin):
    __tablename__ = "staff_chat_messages"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    sender_id: Mapped[UUID] = mapped_column(
        ForeignKey("staff_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel_type: Mapped[str] = mapped_column(String(10), nullable=False)
    channel_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    attachments: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    sender: Mapped[StaffProfile] = relationship(foreign_keys=[sender_id])


class ChatUnreadStatus(Base, TimestampMixin):
    __tablename__ = "staff_chat_unread_status"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    staff_id: Mapped[UUID] = mapped_column(
        ForeignKey("staff_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel_type: Mapped[str] = mapped_column(String(10), nullable=False)
    channel_id: Mapped[str] = mapped_column(String(100), nullable=False)
    last_read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("staff_id", "channel_type", "channel_id", name="uq_staff_channel_read"),
    )
