"""Add image_url column to narrative_trading table

Revision ID: 15_09_2024_add_image_url_to_narrative_trading
Revises: 14_09_2014_add_or_update_image_url
Create Date: 2024-09-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic
revision = '40f27339fda221'
down_revision = '40f27339fda2'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    if 'narrative_trading' in tables:
        columns = [c['name'] for c in inspector.get_columns('narrative_trading')]
        
        if 'image_url' not in columns:
            # Add the column as nullable initially
            op.add_column('narrative_trading', sa.Column('image_url', sa.String(), nullable=True))
            
            # Populate existing records with an empty string
            op.execute("UPDATE narrative_trading SET image_url = '' WHERE image_url IS NULL")
            
            # Now make it non-nullable
            op.alter_column('narrative_trading', 'image_url',
                            existing_type=sa.String(),
                            nullable=False,
                            server_default='')
        else:
            # If the column exists, update its properties
            op.alter_column('narrative_trading', 'image_url',
                            existing_type=sa.String(),
                            nullable=False,
                            server_default='')

def downgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    if 'narrative_trading' in tables:
        columns = [c['name'] for c in inspector.get_columns('narrative_trading')]
        
        if 'image_url' in columns:
            op.drop_column('narrative_trading', 'image_url')