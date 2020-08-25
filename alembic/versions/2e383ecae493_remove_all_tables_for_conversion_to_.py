"""remove all tables for conversion to string keys

Revision ID: 2e383ecae493
Revises: b1fdfe71fcb7
Create Date: 2020-08-25 16:31:05.025135

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e383ecae493'
down_revision = 'b1fdfe71fcb7'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('messages')
    op.drop_table('users')
    op.drop_table('channels')
    op.drop_table('categories')


def downgrade():
    pass
