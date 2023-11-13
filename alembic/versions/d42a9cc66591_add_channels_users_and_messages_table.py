"""
add channels, users and messages table.

Revision ID: d42a9cc66591
Revises: 4d293b37634c
Create Date: 2020-08-25 03:10:21.282787

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "d42a9cc66591"
down_revision = "4d293b37634c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the current migration."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table("channels",
    sa.Column("id", sa.BigInteger(), nullable=False),
    sa.Column("name", sa.String(), nullable=False),
    sa.Column("is_staff", sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint("id"),
    )
    op.create_table("users",
    sa.Column("id", sa.BigInteger(), nullable=False),
    sa.Column("name", sa.String(), nullable=False),
    sa.Column("avatar_hash", sa.String(), nullable=True),
    sa.Column("joined_at", sa.DateTime(), nullable=False),
    sa.Column("created_at", sa.DateTime(), nullable=False),
    sa.Column("is_staff", sa.Boolean(), nullable=False),
    sa.Column("opt_out", sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint("id"),
    )
    op.create_table("messages",
    sa.Column("id", sa.BigInteger(), nullable=False),
    sa.Column("channel_id", sa.BigInteger(), nullable=True),
    sa.Column("author_id", sa.BigInteger(), nullable=True),
    sa.Column("created_at", sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
    sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
    sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Revert the current migration."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("messages")
    op.drop_table("users")
    op.drop_table("channels")
    # ### end Alembic commands ###
