"""Heads migration

Revision ID: 66d1b0965260
Revises: 095f9e28f2f5, 574453f8f426, e7ee74b7b181
Create Date: 2024-11-04 14:31:43.370215

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66d1b0965260'
down_revision: Union[str, None] = ('095f9e28f2f5', '574453f8f426', 'e7ee74b7b181')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
