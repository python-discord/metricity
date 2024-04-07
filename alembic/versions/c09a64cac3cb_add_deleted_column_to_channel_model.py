"""
Add deleted column to channel model.

Revision ID: c09a64cac3cb
Revises: 03655ce2097b
Create Date: 2024-04-07 22:58:53.186355

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "c09a64cac3cb"
down_revision = "03655ce2097b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the current migration."""
    op.add_column("channels", sa.Column("deleted", sa.Boolean(), nullable=False, server_default="False", default=False))


def downgrade() -> None:
    """Revert the current migration."""
    op.drop_column("channels", "deleted")
