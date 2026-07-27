"""inventory: add CHECK constraint to items.quantity >= 0.

Revision ID: inv_0002
Revises: inv_0001
Create Date: 2026-07-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "inv_0002"
down_revision: str | None = "inv_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_inventory_items_quantity_non_negative",
        "inventory_items",
        sa.text("quantity >= 0"),
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_inventory_items_quantity_non_negative",
        "inventory_items",
        type_="check",
    )
