"""full token added

Revision ID: 7b2c360b1115
Revises: e56c26ef855f
Create Date: 2024-08-22 14:42:10.488308

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b2c360b1115'
down_revision: Union[str, None] = 'e56c26ef855f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_table', sa.Column('auth_token', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    pass