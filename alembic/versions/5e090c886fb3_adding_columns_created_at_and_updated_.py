"""Adding columns created_at and updated_at to the roles table

Revision ID: 5e090c886fb3
Revises: a6fd97d66e5a
Create Date: 2024-11-13 15:39:47.780644
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '5e090c886fb3'
down_revision: Union[str, None] = 'a6fd97d66e5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Get connection and inspector
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Get existing columns in roles table
    existing_columns = [col['name'] for col in inspector.get_columns('roles')]
    
    # Add created_at if it doesn't exist
    if 'created_at' not in existing_columns:
        op.add_column('roles', sa.Column('created_at', sa.TIMESTAMP(timezone=True), 
                     server_default=sa.text('now()'), nullable=False))
    
    # Add updated_at if it doesn't exist
    if 'updated_at' not in existing_columns:
        op.add_column('roles', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), 
                     server_default=sa.text('now()'), nullable=False))

def downgrade() -> None:
    # Get connection and inspector
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Get existing columns in roles table
    existing_columns = [col['name'] for col in inspector.get_columns('roles')]
    
    # Drop columns if they exist
    if 'updated_at' in existing_columns:
        op.drop_column('roles', 'updated_at')
    if 'created_at' in existing_columns:
        op.drop_column('roles', 'created_at')