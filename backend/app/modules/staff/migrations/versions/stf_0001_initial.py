"""staff: initial schema — profiles, sprints, tasks, finance, audit.

Revision ID: stf_0001
Revises: 0001
Create Date: 2026-07-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "stf_0001"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = ("staff",)
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "staff_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("probation_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_staff_profiles_user_id"), "staff_profiles", ["user_id"])

    op.create_table(
        "staff_sprints",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("goal", sa.Text(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PLANNED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "staff_tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("assignee_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="TODO"),
        sa.Column("sprint_id", sa.UUID(), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["assignee_id"], ["staff_profiles.id"],),
        sa.ForeignKeyConstraint(["sprint_id"], ["staff_sprints.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_staff_tasks_assignee_id"), "staff_tasks", ["assignee_id"])
    op.create_index(op.f("ix_staff_tasks_sprint_id"), "staff_tasks", ["sprint_id"])

    op.create_table(
        "staff_task_status_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column("from_status", sa.String(20), nullable=True),
        sa.Column("to_status", sa.String(20), nullable=False),
        sa.Column("changed_by", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["changed_by"], ["staff_profiles.id"],),
        sa.ForeignKeyConstraint(["task_id"], ["staff_tasks.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_staff_task_status_logs_task_id"), "staff_task_status_logs", ["task_id"])

    op.create_table(
        "staff_expenses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["staff_profiles.id"],),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "staff_gross_revenues",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["staff_profiles.id"],),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "staff_profit_shares",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("staff_id", sa.UUID(), nullable=False),
        sa.Column("share_percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("vesting_status", sa.String(20), nullable=False, server_default="LOCKED"),
        sa.Column("vesting_condition", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["staff_id"], ["staff_profiles.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_staff_profit_shares_staff_id"), "staff_profit_shares", ["staff_id"])

    op.create_table(
        "staff_payout_ledger",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("staff_id", sa.UUID(), nullable=False),
        sa.Column("amount_paid", sa.Numeric(12, 2), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("paid_by", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["paid_by"], ["staff_profiles.id"],),
        sa.ForeignKeyConstraint(["staff_id"], ["staff_profiles.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_staff_payout_ledger_staff_id"), "staff_payout_ledger", ["staff_id"])

    op.create_table(
        "staff_audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["staff_profiles.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_staff_audit_logs_user_id"), "staff_audit_logs", ["user_id"])


def downgrade() -> None:
    op.drop_table("staff_audit_logs")
    op.drop_table("staff_payout_ledger")
    op.drop_table("staff_profit_shares")
    op.drop_table("staff_gross_revenues")
    op.drop_table("staff_expenses")
    op.drop_table("staff_task_status_logs")
    op.drop_table("staff_tasks")
    op.drop_table("staff_sprints")
    op.drop_table("staff_profiles")
