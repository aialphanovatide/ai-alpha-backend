"""Merge heads

Revision ID: 7390b414985a
Revises: 574453f8f426, 7f9a2b3c4d5e, absd12345, e7ee74b7b181
Create Date: 2024-11-06 17:07:26.322906

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7390b414985a'
down_revision: Union[str, None] = ('574453f8f426', '7f9a2b3c4d5e', 'absd12345', 'e7ee74b7b181')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
