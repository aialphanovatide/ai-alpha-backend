"""fusionar cabezas divergentes

Revision ID: 4959f6741db6
Revises: 6177935136ea, abc123def456
Create Date: 2024-11-20 10:26:19.701874

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4959f6741db6'
down_revision: Union[str, None] = ('6177935136ea', 'abc123def456')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
