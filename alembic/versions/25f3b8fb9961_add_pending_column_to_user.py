"""
add pending column to user.

Revision ID: 25f3b8fb9961
Revises: a259ab5efcec
Create Date: 2020-12-21 17:42:04.566930

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "25f3b8fb9961"
down_revision = "a259ab5efcec"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the current migration."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("users", sa.Column("pending", sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Revert the current migration."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("users", "pending")
    # ### end Alembic commands ###
