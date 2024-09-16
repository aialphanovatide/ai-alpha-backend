"""updated PurchasedPlan schema: added ondelete CASCADE

Revision ID: 82e43a1c2ab4
Revises: f5d9fda86672
Create Date: 2024-09-13 17:44:57.350820

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82e43a1c2ab4'
down_revision: Union[str, None] = 'f5d9fda86672'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('purchased_plan_user_id_fkey', 'purchased_plan', type_='foreignkey')
    op.create_foreign_key(None, 'purchased_plan', 'user_table', ['user_id'], ['user_id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'purchased_plan', type_='foreignkey')
    op.create_foreign_key('purchased_plan_user_id_fkey', 'purchased_plan', 'user_table', ['user_id'], ['user_id'])
    # ### end Alembic commands ###