"""merge a41f623239fb and abc123def456

Revision ID: ca321a4118e6
Revises: abc123def456
Create Date: 2024-11-07 11:48:16.716696

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'ca321a4118e6'
down_revision: Union[Sequence[str], None] = ('a41f623239fb', 'abc123def456')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
