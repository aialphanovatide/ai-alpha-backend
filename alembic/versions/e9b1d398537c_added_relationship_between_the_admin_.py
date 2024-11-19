"""added relationship between the Admin and the API Key schema

Revision ID: e9b1d398537c
Revises: 3720552336cb
Create Date: 2024-09-17 13:19:33.806277

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = 'e9b1d398537c'
down_revision: Union[str, None] = '3720552336cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Check upgrade function
def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.Inspector.from_engine(conn)
    
    # Check if the tokens table exists
    if 'tokens' in inspector.get_table_names():
        foreign_keys = inspector.get_foreign_keys('tokens')
        
        # Check if the foreign key already exists
        fk_exists = any(fk['referred_table'] == 'admins' and 
                        fk['referred_columns'] == ['admin_id'] and 
                        fk['constrained_columns'] == ['admin_id'] 
                        for fk in foreign_keys)
        
        if not fk_exists:
            # Drop existing foreign key if any
            for fk in foreign_keys:
                if fk['referred_table'] == 'admins':
                    op.drop_constraint(fk['name'], 'tokens', type_='foreignkey')
            
            # Create the correct foreign key constraint
            op.create_foreign_key(
                'fk_tokens_admin_id_admins',
                'tokens',
                'admins',
                ['admin_id'],
                ['admin_id'],
                ondelete='CASCADE'
            )
    
    # Ensure admin_id in tokens table is not nullable
    tokens_columns = inspector.get_columns('tokens')
    admin_id_column = next((col for col in tokens_columns if col['name'] == 'admin_id'), None)
    if admin_id_column and admin_id_column['nullable']:
        op.alter_column('tokens', 'admin_id',
                        existing_type=sa.INTEGER(),
                        nullable=False)

def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.Inspector.from_engine(conn)
    
    if 'tokens' in inspector.get_table_names():
        foreign_keys = inspector.get_foreign_keys('tokens')
        for fk in foreign_keys:
            if fk['referred_table'] == 'admins':
                op.drop_constraint(fk['name'], 'tokens', type_='foreignkey')
        
        # Make admin_id nullable again
        op.alter_column('tokens', 'admin_id',
                        existing_type=sa.INTEGER(),
                        nullable=True)
