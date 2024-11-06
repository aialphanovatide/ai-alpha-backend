"""New migration

Revision ID: <absd12345>
Revises: 70376d9c8c8a
Create Date: 2024-11-06 09:09:56.361632
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'absd12345'
down_revision: Union[str, None] = '70376d9c8c8a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Aquí van las operaciones de la migración
    # op.create_table('new_table',
    #     sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    #     sa.Column('name', sa.String(), nullable=False),
    #     sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    #     sa.PrimaryKeyConstraint('id')
    # )
    pass

def downgrade() -> None:
    # Aquí van las operaciones para revertir la migración
    # op.drop_table('new_table')
    pass
