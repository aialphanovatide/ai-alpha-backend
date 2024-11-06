"""New migration

Revision ID: 66d1b0965260
Revises: 
Create Date: 2024-11-06 10:09:56.361632
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '66d1b0965260'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Aquí van las operaciones de la migración
    pass

def downgrade() -> None:
    # Aquí van las operaciones para revertir la migración
    pass