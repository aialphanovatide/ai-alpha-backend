"""Token Schema

Revision ID: 8c0527cff320
Revises: fedadcb66914
Create Date: 2024-09-16 15:03:48.299321

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c0527cff320'
down_revision: Union[str, None] = 'fedadcb66914'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('user_table', sa.Column('birth_date', sa.Date(), nullable=True))
    op.add_column('admins', sa.Column('auth_token', sa.String(), nullable=True))

def downgrade():
    op.drop_column('user_table', 'birth_date')
    op.drop_column('admins', 'auth_token')
