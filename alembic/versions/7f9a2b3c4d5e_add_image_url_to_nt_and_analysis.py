"""add image_url to analysis and narrative_trading tables

Revision ID: 7f9a2b3c4d5e
Revises: eeb008152cc7
Create Date: 2024-09-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '7f9a2b3c4d5e'
down_revision: Union[str, None] = 'eeb008152cc7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # Check and update 'analysis' table
    analysis_columns = [c['name'] for c in inspector.get_columns('analysis')]
    if 'image_url' not in analysis_columns:
        op.add_column('analysis', sa.Column('image_url', sa.String(), nullable=True))

    # Check and update 'narrative_trading' table
    narrative_columns = [c['name'] for c in inspector.get_columns('narrative_trading')]
    if 'image_url' not in narrative_columns:
        op.add_column('narrative_trading', sa.Column('image_url', sa.String(), nullable=True))
        
        # Update existing rows with a default value
        op.execute("UPDATE narrative_trading SET image_url = '' WHERE image_url IS NULL")
        
        # Now alter the column to be non-nullable
        op.alter_column('narrative_trading', 'image_url', nullable=False, server_default='')


def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # Check and revert 'analysis' table
    analysis_columns = [c['name'] for c in inspector.get_columns('analysis')]
    if 'image_url' in analysis_columns:
        op.drop_column('analysis', 'image_url')

    # Check and revert 'narrative_trading' table
    narrative_columns = [c['name'] for c in inspector.get_columns('narrative_trading')]
    if 'image_url' in narrative_columns:
        op.alter_column('narrative_trading', 'image_url', nullable=True)
        op.drop_column('narrative_trading', 'image_url')