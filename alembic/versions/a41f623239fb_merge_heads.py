"""Merge heads

Revision ID: a41f623239fb
Revises: 66d1b0965260, 7390b414985a
Create Date: 2024-11-06 17:14:42.622501

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a41f623239fb'
down_revision: Union[str, None] = ('66d1b0965260', '7390b414985a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
