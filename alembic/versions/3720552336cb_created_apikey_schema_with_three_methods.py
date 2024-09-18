"""Created APIKey schema with three methods

Revision ID: 3720552336cb
Revises: e173b2d6f7a7
Create Date: 2024-09-16 19:12:48.277657

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3720552336cb'
down_revision: Union[str, None] = 'e173b2d6f7a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if the api_keys table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'api_keys' not in inspector.get_table_names():
        # Create api_keys table
        op.create_table('api_keys',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('key', sa.String(64), nullable=False),
            sa.Column('last_used', sa.TIMESTAMP(), nullable=True),
            sa.Column('admin_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create unique constraint on key
        op.create_unique_constraint('uq_api_keys_key', 'api_keys', ['key'])
    
    # Check if admin_id column exists
    if 'admin_id' not in [c['name'] for c in inspector.get_columns('api_keys')]:
        op.add_column('api_keys', sa.Column('admin_id', sa.Integer(), nullable=False))
    
    # Check if unique constraint on admin_id exists
    if 'uq_api_keys_admin_id' not in [c['name'] for c in inspector.get_unique_constraints('api_keys')]:
        op.create_unique_constraint('uq_api_keys_admin_id', 'api_keys', ['admin_id'])
    
    # Check if foreign key constraint exists
    if 'fk_api_keys_admin_id_admins' not in [fk['name'] for fk in inspector.get_foreign_keys('api_keys')]:
        op.create_foreign_key('fk_api_keys_admin_id_admins', 'api_keys', 'admins', ['admin_id'], ['admin_id'], ondelete='CASCADE')


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint('fk_api_keys_admin_id_admins', 'api_keys', type_='foreignkey')
    
    # Drop unique constraints
    op.drop_constraint('uq_api_keys_admin_id', 'api_keys', type_='unique')
    op.drop_constraint('uq_api_keys_key', 'api_keys', type_='unique')
    
    # Drop api_keys table
    op.drop_table('api_keys')
