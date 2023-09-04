"""
add channel categories.

Revision ID: 6b52b1e7680b
Revises: d42a9cc66591
Create Date: 2020-08-25 05:10:43.945126

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "6b52b1e7680b"
down_revision = "d42a9cc66591"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the current migration."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table("categories",
    sa.Column("id", sa.BigInteger(), nullable=False),
    sa.Column("name", sa.String(), nullable=False),
    sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("channels", sa.Column("category_id", sa.BigInteger(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Revert the current migration."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("channels", "category_id")
    op.drop_table("categories")
    # ### end Alembic commands ###
