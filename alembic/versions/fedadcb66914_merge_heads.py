"""merge heads
Revision ID: fedadcb66914
Revises: 40f27339fda221, ed76f5dc38dc
Create Date: 2024-09-14 23:09:49.148843
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
# revision identifiers, used by Alembic.
revision: str = 'fedadcb66914'
down_revision: Union[str, None] = 'e9b1d398537c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
def upgrade() -> None:
    pass
def downgrade() -> None:
    pass