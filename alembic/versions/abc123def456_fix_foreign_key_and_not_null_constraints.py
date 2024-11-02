"""Fix foreign key violation and NOT NULL constraint issues

Revision ID: abc123def456
Revises: e7ee74b7b181
Create Date: 2024-10-31 15:45:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'abc123def456'
down_revision: Union[str, None] = 'e7ee74b7b181'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fix foreign key violation in hacks table
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Check if foreign key already exists
    foreign_keys = inspector.get_foreign_keys('hacks')
    foreign_key_exists = any(fk['constrained_columns'] == ['coin_bot_id'] for fk in foreign_keys)

    if not foreign_key_exists:
        # Add foreign key constraint if it doesn't exist
        op.create_foreign_key('fk_hacks_coin_bot', 'hacks', 'coin_bot', ['coin_bot_id'], ['id'])
        print("Foreign key constraint 'fk_hacks_coin_bot' added to 'hacks' table.")
    else:
        print("Foreign key constraint 'fk_hacks_coin_bot' already exists in 'hacks' table. Skipping addition.")

    # Fix NOT NULL constraint on updated_at in introduction table
    columns_intro = inspector.get_columns('introduction')
    updated_at_column_intro = next((col for col in columns_intro if col['name'] == 'updated_at'), None)

    if updated_at_column_intro and updated_at_column_intro['nullable']:
        op.alter_column('introduction', 'updated_at', nullable=False, server_default=sa.func.now())
        print("NOT NULL constraint added to 'updated_at' column in 'introduction' table.")
    else:
        print("NOT NULL constraint on 'updated_at' column in 'introduction' table already exists or column missing. Skipping.")

    # Fix NOT NULL constraint on updated_at in tokenomics table
    columns_tokenomics = inspector.get_columns('tokenomics')
    updated_at_column_tokenomics = next((col for col in columns_tokenomics if col['name'] == 'updated_at'), None)

    if updated_at_column_tokenomics and updated_at_column_tokenomics['nullable']:
        op.alter_column('tokenomics', 'updated_at', nullable=False, server_default=sa.func.now())
        print("NOT NULL constraint added to 'updated_at' column in 'tokenomics' table.")
    else:
        print("NOT NULL constraint on 'updated_at' column in 'tokenomics' table already exists or column missing. Skipping.")


def downgrade() -> None:
    # Remove foreign key constraint in hacks table if it exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    foreign_keys = inspector.get_foreign_keys('hacks')
    foreign_key_exists = any(fk['constrained_columns'] == ['coin_bot_id'] for fk in foreign_keys)

    if foreign_key_exists:
        op.drop_constraint('fk_hacks_coin_bot', 'hacks', type_='foreignkey')
        print("Foreign key constraint 'fk_hacks_coin_bot' removed from 'hacks' table.")
    else:
        print("Foreign key constraint 'fk_hacks_coin_bot' not found in 'hacks' table. Skipping removal.")

    # Remove NOT NULL constraint on updated_at in introduction table
    columns_intro = inspector.get_columns('introduction')
    updated_at_column_intro = next((col for col in columns_intro if col['name'] == 'updated_at'), None)

    if updated_at_column_intro and not updated_at_column_intro['nullable']:
        op.alter_column('introduction', 'updated_at', nullable=True)
        print("NOT NULL constraint removed from 'updated_at' column in 'introduction' table.")
    else:
        print("NOT NULL constraint on 'updated_at' column in 'introduction' table not found or column already nullable. Skipping.")

    # Remove NOT NULL constraint on updated_at in tokenomics table
    columns_tokenomics = inspector.get_columns('tokenomics')
    updated_at_column_tokenomics = next((col for col in columns_tokenomics if col['name'] == 'updated_at'), None)

    if updated_at_column_tokenomics and not updated_at_column_tokenomics['nullable']:
        op.alter_column('tokenomics', 'updated_at', nullable=True)
        print("NOT NULL constraint removed from 'updated_at' column in 'tokenomics' table.")
    else:
        print("NOT NULL constraint on 'updated_at' column in 'tokenomics' table not found or column already nullable. Skipping.")
