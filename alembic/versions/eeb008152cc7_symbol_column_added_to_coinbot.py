"""symbol column added to coinbot - curated

Revision ID: eeb008152cc7
Revises: 9e3e0f31ac3a
Create Date: 2024-09-19 16:42:16.177047

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = 'eeb008152cc7'
down_revision: Union[str, None] = '9e3e0f31ac3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_columns = [c['name'] for c in inspector.get_columns('coin_bot')]

    # Add 'gecko_id' column if it doesn't exist
    if 'gecko_id' not in existing_columns:
        op.add_column('coin_bot', sa.Column('gecko_id', sa.String(), nullable=True))
    
    # Add 'symbol' column if it doesn't exist
    if 'symbol' not in existing_columns:
        op.add_column('coin_bot', sa.Column('symbol', sa.String(), nullable=True))

def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_columns = [c['name'] for c in inspector.get_columns('coin_bot')]

    # Drop 'symbol' column if it exists
    if 'symbol' in existing_columns:
        op.drop_column('coin_bot', 'symbol')
    
    # Drop 'gecko_id' column if it exists
    if 'gecko_id' in existing_columns:
        op.drop_column('coin_bot', 'gecko_id')