"""
cascade delete channels on category deletion.

Revision ID: 408aac572bff
Revises: 25f3b8fb9961
Create Date: 2021-03-04 01:11:32.519071

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "408aac572bff"
down_revision = "25f3b8fb9961"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the current migration."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("channels_category_id_fkey", "channels", type_="foreignkey")
    op.create_foreign_key(None, "channels", "categories", ["category_id"], ["id"], ondelete="CASCADE")
    # ### end Alembic commands ###


def downgrade() -> None:
    """Revert the current migration."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "channels", type_="foreignkey")
    op.create_foreign_key("channels_category_id_fkey", "channels", "categories", ["category_id"], ["id"])
    # ### end Alembic commands ###
