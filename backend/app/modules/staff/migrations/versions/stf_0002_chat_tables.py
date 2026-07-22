"""staff: add chat_messages and chat_unread_status tables.

Revision ID: stf_0002
Revises: stf_0001
Create Date: 2026-07-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "stf_0002"
down_revision: str | None = "stf_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "staff_chat_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("sender_id", sa.UUID(), nullable=False),
        sa.Column("channel_type", sa.String(10), nullable=False),
        sa.Column("channel_id", sa.String(100), nullable=False),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("attachments", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["sender_id"], ["staff_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_staff_chat_messages_sender_id"), "staff_chat_messages", ["sender_id"])
    op.create_index(op.f("ix_staff_chat_messages_channel_id"), "staff_chat_messages", ["channel_id"])

    op.create_table(
        "staff_chat_unread_status",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("staff_id", sa.UUID(), nullable=False),
        sa.Column("channel_type", sa.String(10), nullable=False),
        sa.Column("channel_id", sa.String(100), nullable=False),
        sa.Column("last_read_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["staff_id"], ["staff_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("staff_id", "channel_type", "channel_id", name="uq_staff_channel_read"),
    )
    op.create_index(op.f("ix_staff_chat_unread_status_staff_id"), "staff_chat_unread_status", ["staff_id"])


def downgrade() -> None:
    op.drop_table("staff_chat_unread_status")
    op.drop_table("staff_chat_messages")
