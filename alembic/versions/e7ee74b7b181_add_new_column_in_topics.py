"""Add new column in topics

Revision ID: e7ee74b7b181
Revises: 6562a81a7c5c
Create Date: 2024-10-09 13:20:05.423134

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e7ee74b7b181'
down_revision: Union[str, None] = '6562a81a7c5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Check if the 'type' column already exists in the 'topics' table
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = inspector.get_columns('topics')
    if 'type' not in [col['name'] for col in columns]:
        # If the column doesn't exist, add it
        op.add_column('topics', sa.Column('type', sa.String(), nullable=False, server_default='default'))
        print("Column 'type' added to 'topics' table.")
    else:
        print("Column 'type' already exists in 'topics' table. Skipping addition.")

def downgrade() -> None:
    # Check if the 'type' column exists in the 'topics' table before dropping
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = inspector.get_columns('topics')
    if 'type' in [col['name'] for col in columns]:
        # If the column exists, drop it
        op.drop_column('topics', 'type')
        print("Column 'type' dropped from 'topics' table.")
    else:
        print("Column 'type' does not exist in 'topics' table. Skipping drop operation.")