"""is essential added to chart - curated by David on 09/11/2024

Revision ID: a6fd97d66e5a
Revises: ca321a4118e6
Create Date: 2024-11-07 11:51:01.087708

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a6fd97d66e5a'
down_revision: Union[str, None] = '70376d9c8c8a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.Inspector.from_engine(conn)


    # If 'is_essential' does not exist in the 'chart' table, add the column
    columns = [column['name'] for column in inspector.get_columns('chart')]
    if 'is_essential' not in columns:
        op.add_column('chart', sa.Column('is_essential', sa.Boolean(), default=False))

    # Add updated_at column to tokens table if it doesn't exist
    tokens_columns = [column['name'] for column in inspector.get_columns('tokens')]
    if 'updated_at' not in tokens_columns:
        op.add_column('tokens', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False))


def downgrade() -> None:
    # Drop columns added in upgrade
    op.drop_column('chart', 'is_essential')
    op.drop_column('tokens', 'updated_at')