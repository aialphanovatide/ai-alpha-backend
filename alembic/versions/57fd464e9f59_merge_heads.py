"""merge heads

Revision ID: 57fd464e9f59
Revises: 0a9abed6359c, 6e9593ea0a94
Create Date: 2024-08-05 15:46:08.283898

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '57fd464e9f59'
down_revision: Union[str, None] = ('0a9abed6359c', '6e9593ea0a94')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
