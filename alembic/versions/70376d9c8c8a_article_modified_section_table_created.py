"""article modified, section table created - curated by David on 08/11/2024

Revision ID: 70376d9c8c8a
Revises: 49f84e4fce31
Create Date: 2024-10-28 14:44:56.592764

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '70376d9c8c8a'
down_revision: Union[str, None] = '49f84e4fce31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Upgrade and downgrade fucntion were commented as they are trying to add a contrain to teh article table, but the table is not being used anymore.

def upgrade() -> None:
#     conn = op.get_bind()
#     inspector = sa.inspect(conn)
#     existing_columns = [col['name'] for col in inspector.get_columns('article')]

#     if 'section_id' not in existing_columns:
#         # Add section_id column and create foreign key relationship
#         op.add_column('article', sa.Column('section_id', sa.Integer(), nullable=False))
#         op.create_foreign_key(None, 'article', 'sections', ['section_id'], ['id'], ondelete='CASCADE')
    pass

def downgrade() -> None:
    # Remove the foreign key first, then the column
#     op.drop_constraint(None, 'article', type_='foreignkey')
#     op.drop_column('article', 'section_id')
    pass
