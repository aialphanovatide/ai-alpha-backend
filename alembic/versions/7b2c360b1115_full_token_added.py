"""full token added - curated.

Revision ID: 7b2c360b1115
Revises: e56c26ef855f
Create Date: 2024-08-22 14:42:10.488308

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b2c360b1115'
down_revision: Union[str, None] = 'e9b1d398537c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Check if the column exists before adding it
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('user_table')]
    if 'auth_token' not in columns:
        op.add_column('user_table', sa.Column('auth_token', sa.String(), nullable=True))
    
    if 'full_name' not in columns:
        op.add_column('user_table', sa.Column('full_name', sa.String(), nullable=True))

def downgrade():
    # Check if the column exists before dropping it
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('user_table')]
    if 'auth_token' in columns:
        op.drop_column('user_table', 'auth_token')

    if 'full_name' in columns:
        op.drop_column('user_table', 'full_name')
 