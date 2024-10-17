"""topic and notification table added

Revision ID: 6562a81a7c5c
Revises: 7f9a2b3c4d5e
Create Date: 2024-10-01 13:13:02.185114

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6562a81a7c5c'
down_revision: Union[str, None] = '7f9a2b3c4d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from sqlalchemy import inspect

def upgrade() -> None:
    # Get the current database connection
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check if 'topics' table exists before creating it
    if 'topics' not in inspector.get_table_names():
        op.create_table('topics',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('reference', sa.String(), nullable=True),
            sa.Column('timeframe', sa.String(), nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(), nullable=False),
            sa.Column('updated_at', sa.TIMESTAMP(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        print("Table 'topics' created.")
    else:
        print("Table 'topics' already exists. Skipping creation.")

    # Check if 'notifications' table exists before creating it
    if 'notifications' not in inspector.get_table_names():
        op.create_table('notifications',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('body', sa.String(), nullable=False),
            sa.Column('type', sa.String(), nullable=False),
            sa.Column('coin', sa.String(), nullable=True),
            sa.Column('topic_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.TIMESTAMP(), nullable=False),
            sa.Column('updated_at', sa.TIMESTAMP(), nullable=False),
            sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        print("Table 'notifications' created.")
    else:
        print("Table 'notifications' already exists. Skipping creation.")

    # Add more checks for other operations if needed


def downgrade() -> None:
    # Get the current database connection
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check if 'notifications' table exists before dropping
    if 'notifications' in inspector.get_table_names():
        op.drop_table('notifications')
        print("Table 'notifications' dropped.")
    else:
        print("Table 'notifications' does not exist. Skipping drop operation.")

    # Check if 'topics' table exists before dropping
    if 'topics' in inspector.get_table_names():
        op.drop_table('topics')
        print("Table 'topics' dropped.")
    else:
        print("Table 'topics' does not exist. Skipping drop operation.")

    # Add more checks for other operations if needed