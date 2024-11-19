"""Fix foreign key violation and NOT NULL constraint issues - curated on 07/11/2024 by David.

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
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Fix foreign key violation in hacks table
    foreign_keys = inspector.get_foreign_keys('hacks')
    foreign_key_exists = any(fk['constrained_columns'] == ['coin_bot_id'] for fk in foreign_keys)

    if not foreign_key_exists:
        op.create_foreign_key(
            'fk_hacks_coin_bot', 
            'hacks', 
            'coin_bot', 
            ['coin_bot_id'], 
            ['bot_id']  # Fixed: Using correct primary key column name
        )

    # Fix NOT NULL constraint on updated_at in introduction table
    columns_intro = inspector.get_columns('introduction')
    updated_at_column_intro = next((col for col in columns_intro if col['name'] == 'updated_at'), None)

    if updated_at_column_intro and updated_at_column_intro['nullable']:
        op.alter_column(
            'introduction', 
            'updated_at', 
            nullable=False, 
            server_default=sa.func.now()
        )

    # Fix NOT NULL constraint on updated_at in tokenomics table
    columns_tokenomics = inspector.get_columns('tokenomics')
    updated_at_column_tokenomics = next((col for col in columns_tokenomics if col['name'] == 'updated_at'), None)

    if updated_at_column_tokenomics and updated_at_column_tokenomics['nullable']:
        op.alter_column(
            'tokenomics', 
            'updated_at', 
            nullable=False, 
            server_default=sa.func.now()
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Remove foreign key constraint in hacks table if it exists
    foreign_keys = inspector.get_foreign_keys('hacks')
    foreign_key_exists = any(fk['constrained_columns'] == ['coin_bot_id'] for fk in foreign_keys)

    if foreign_key_exists:
        op.drop_constraint('fk_hacks_coin_bot', 'hacks', type_='foreignkey')

    # Remove NOT NULL constraint on updated_at in introduction table
    columns_intro = inspector.get_columns('introduction')
    updated_at_column_intro = next((col for col in columns_intro if col['name'] == 'updated_at'), None)

    if updated_at_column_intro and not updated_at_column_intro['nullable']:
        op.alter_column('introduction', 'updated_at', nullable=True)

    # Remove NOT NULL constraint on updated_at in tokenomics table
    columns_tokenomics = inspector.get_columns('tokenomics')
    updated_at_column_tokenomics = next((col for col in columns_tokenomics if col['name'] == 'updated_at'), None)

    if updated_at_column_tokenomics and not updated_at_column_tokenomics['nullable']:
        op.alter_column('tokenomics', 'updated_at', nullable=True)