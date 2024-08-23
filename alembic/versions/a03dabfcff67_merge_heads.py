"""Merge heads

Revision ID: a03dabfcff67
Revises: 0fa0c5ebd87d
Create Date: 2024-08-22 14:38:02.143189

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a03dabfcff67'
down_revision: Union[str, None] = '0fa0c5ebd87d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
