"""core — add tenant_brandings table.

White-label branding records linked 1-to-1 with clinics, including
custom domains, theme colors, logos, and portal title.

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-21

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenant_brandings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("logo_url", sa.String(length=512), nullable=True),
        sa.Column("favicon_url", sa.String(length=512), nullable=True),
        sa.Column("primary_color", sa.String(length=7), nullable=True),
        sa.Column("secondary_color", sa.String(length=7), nullable=True),
        sa.Column("accent_color", sa.String(length=7), nullable=True),
        sa.Column("custom_domain", sa.String(length=255), nullable=True),
        sa.Column("portal_title", sa.String(length=200), nullable=True),
        sa.Column("custom_css", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id"),
        sa.UniqueConstraint("custom_domain"),
    )
    op.create_index(
        op.f("ix_tenant_brandings_clinic_id"),
        "tenant_brandings",
        ["clinic_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_tenant_brandings_custom_domain"),
        "tenant_brandings",
        ["custom_domain"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_tenant_brandings_custom_domain"), table_name="tenant_brandings")
    op.drop_index(op.f("ix_tenant_brandings_clinic_id"), table_name="tenant_brandings")
    op.drop_table("tenant_brandings")
