"""removes relationship between article and section schemas

Revision ID: 1f20f52fc896
Revises: 5e090c886fb3
Create Date: 2024-11-15 13:36:05.799297

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from typing import Sequence, Union
    
# revision identifiers, used by Alembic.
revision: str = '1f20f52fc896'
down_revision: Union[str, None] = '5e090c886fb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Get connection and inspector
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Check for foreign key constraints referencing sections table
    fks = inspector.get_foreign_keys('article')
    for fk in fks:
        if fk['referred_table'] == 'sections':
            op.drop_constraint(fk['name'], 'article', type_='foreignkey')
            print(f"Dropped foreign key constraint: {fk['name']}")
    
    # Check if section_id column exists before trying to drop it
    columns = [c['name'] for c in inspector.get_columns('article')]
    if 'section_id' in columns:
        op.drop_column('article', 'section_id')
        print("Dropped section_id column from article table")

def downgrade() -> None:
    # Get connection and inspector
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Check if section_id doesn't exist before adding it back
    columns = [c['name'] for c in inspector.get_columns('article')]
    if 'section_id' not in columns:
        # Add section_id column
        op.add_column('article', sa.Column('section_id', sa.Integer(), nullable=True))
        
        # Create foreign key constraint
        op.create_foreign_key(
            'fk_article_section_id',
            'article',
            'sections',
            ['section_id'],
            ['id'],
            ondelete='CASCADE'
        )