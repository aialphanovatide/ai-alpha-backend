"""Merge heads

Revision ID: e56c26ef855f
Revises: a03dabfcff67
Create Date: 2024-08-22 14:38:11.291160

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e56c26ef855f'
down_revision: Union[str, None] = 'a03dabfcff67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
