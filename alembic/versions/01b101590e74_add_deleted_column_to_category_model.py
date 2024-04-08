"""
Add deleted column to Category model.

Revision ID: 01b101590e74
Revises: c09a64cac3cb
Create Date: 2024-04-08 04:39:00.198882

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "01b101590e74"
down_revision = "c09a64cac3cb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the current migration."""
    op.add_column(
        "categories",
        sa.Column("deleted", sa.Boolean(), nullable=False, server_default="False", default=False),
    )


def downgrade() -> None:
    """Revert the current migration."""
    op.drop_column("categories", "deleted")
