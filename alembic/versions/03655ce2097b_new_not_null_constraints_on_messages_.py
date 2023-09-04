"""
New NOT NULL constraints on messages and users table.

Revision ID: 03655ce2097b
Revises: 563a15b2a76e
Create Date: 2023-09-04 20:17:03.543328

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "03655ce2097b"
down_revision = "563a15b2a76e"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("messages", "channel_id",
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column("messages", "author_id",
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column("messages", "is_deleted",
               existing_type=sa.BOOLEAN(),
               nullable=False)
    op.alter_column("users", "bot",
               existing_type=sa.BOOLEAN(),
               nullable=False)
    op.alter_column("users", "in_guild",
               existing_type=sa.BOOLEAN(),
               nullable=False)
    op.alter_column("users", "pending",
               existing_type=sa.BOOLEAN(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("users", "pending",
               existing_type=sa.BOOLEAN(),
               nullable=True)
    op.alter_column("users", "in_guild",
               existing_type=sa.BOOLEAN(),
               nullable=True)
    op.alter_column("users", "bot",
               existing_type=sa.BOOLEAN(),
               nullable=True)
    op.alter_column("messages", "is_deleted",
               existing_type=sa.BOOLEAN(),
               nullable=True)
    op.alter_column("messages", "author_id",
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column("messages", "channel_id",
               existing_type=sa.VARCHAR(),
               nullable=True)
    # ### end Alembic commands ###
