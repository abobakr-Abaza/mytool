"""core: add clinic.slug column for public booking.

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("clinics", sa.Column("slug", sa.String(length=120), nullable=True))
    op.create_index(op.f("ix_clinics_slug"), "clinics", ["slug"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_clinics_slug"), table_name="clinics")
    op.drop_column("clinics", "slug")
