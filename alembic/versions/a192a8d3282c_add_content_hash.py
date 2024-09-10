"""
Add content_hash field to messages model.

Revision ID: a192a8d3282c
Revises: 01b101590e74
Create Date: 2024-09-10 16:32:46.593911

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a192a8d3282c"
down_revision = "01b101590e74"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the current migration."""
    op.add_column("messages", sa.Column("content_hash", sa.String(), nullable=True))


def downgrade() -> None:
    """Revert the current migration."""
    op.drop_column("messages", "content_hash")
