"""Token Schema

Revision ID: 8c0527cff320
Revises: abc123def456
Create Date: 2024-09-16 15:03:48.299321

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = '8c0527cff320'
down_revision: Union[str, None] = 'abc123def456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def column_exists(table_name, column_name):
    inspector = Inspector.from_engine(op.get_bind())
    columns = inspector.get_columns(table_name)
    return any(column['name'] == column_name for column in columns)

def upgrade():
    if not column_exists('user_table', 'birth_date'):
        op.add_column('user_table', sa.Column('birth_date', sa.Date(), nullable=True))
    
    if not column_exists('admins', 'auth_token'):
        op.add_column('admins', sa.Column('auth_token', sa.String(), nullable=True))

def downgrade():
    if column_exists('user_table', 'birth_date'):
        op.drop_column('user_table', 'birth_date')
    
    if column_exists('admins', 'auth_token'):
        op.drop_column('admins', 'auth_token')