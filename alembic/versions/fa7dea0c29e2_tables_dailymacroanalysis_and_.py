"""tables DailyMacroAnalysis and SpotlightAnalysis columns category rename to category_name

Revision ID: fa7dea0c29e2
Revises: 1f20f52fc896
Create Date: 2024-12-12 21:43:30.654447

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fa7dea0c29e2'
down_revision: Union[str, None] = '1f20f52fc896'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def get_column_names(table_name):
    """Get column names for a given table"""
    conn = op.get_bind()
    insp = Inspector.from_engine(conn)
    return [column['name'] for column in insp.get_columns(table_name)]

def upgrade() -> None:
    # Get current column names for both tables
    daily_macro_columns = get_column_names('daily_macro_analysis')
    spotlight_columns = get_column_names('spotlight_analysis')

    # DailyMacroAnalysis table
    if 'category' in daily_macro_columns and 'category_name' not in daily_macro_columns:
        # 1. Add new column as nullable first
        op.add_column('daily_macro_analysis', sa.Column('category_name', sa.String(length=100), nullable=True))
        # 2. Copy data
        op.execute('UPDATE daily_macro_analysis SET category_name = category')
        # 3. Set not null constraint
        op.alter_column('daily_macro_analysis', 'category_name',
                       existing_type=sa.String(length=100),
                       nullable=False)
        # 4. Drop old column
        op.drop_column('daily_macro_analysis', 'category')

    # SpotlightAnalysis table
    if 'category' in spotlight_columns and 'category_name' not in spotlight_columns:
        # 1. Add new column as nullable first
        op.add_column('spotlight_analysis', sa.Column('category_name', sa.String(length=100), nullable=True))
        # 2. Copy data
        op.execute('UPDATE spotlight_analysis SET category_name = category')
        # 3. Set not null constraint
        op.alter_column('spotlight_analysis', 'category_name',
                       existing_type=sa.String(length=100),
                       nullable=False)
        # 4. Drop old column
        op.drop_column('spotlight_analysis', 'category')

def downgrade() -> None:
    # Get current column names for both tables
    daily_macro_columns = get_column_names('daily_macro_analysis')
    spotlight_columns = get_column_names('spotlight_analysis')

    # DailyMacroAnalysis table
    if 'category_name' in daily_macro_columns and 'category' not in daily_macro_columns:
        # 1. Add old column as nullable first
        op.add_column('daily_macro_analysis', sa.Column('category', sa.VARCHAR(length=100), nullable=True))
        # 2. Copy data
        op.execute('UPDATE daily_macro_analysis SET category = category_name')
        # 3. Set not null constraint
        op.alter_column('daily_macro_analysis', 'category',
                       existing_type=sa.VARCHAR(length=100),
                       nullable=False)
        # 4. Drop new column
        op.drop_column('daily_macro_analysis', 'category_name')

    # SpotlightAnalysis table
    if 'category_name' in spotlight_columns and 'category' not in spotlight_columns:
        # 1. Add old column as nullable first
        op.add_column('spotlight_analysis', sa.Column('category', sa.VARCHAR(length=100), nullable=True))
        # 2. Copy data
        op.execute('UPDATE spotlight_analysis SET category = category_name')
        # 3. Set not null constraint
        op.alter_column('spotlight_analysis', 'category',
                       existing_type=sa.VARCHAR(length=100),
                       nullable=False)
        # 4. Drop new column
        op.drop_column('spotlight_analysis', 'category_name')