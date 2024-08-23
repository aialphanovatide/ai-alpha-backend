from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6e9593ea0a94'
down_revision: Union[str, None] = '858bc67aa1c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def column_exists(table_name: str, column_name: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def table_exists(table_name: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return inspector.has_table(table_name)

def upgrade() -> None:
    # Drop the table if it exists
    if table_exists('admin'):
        op.drop_table('admin')

    # Add columns to tables if they do not already exist
    if not column_exists('alert', 'updated_at'):
        op.add_column('alert', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))

    if not column_exists('analysis', 'updated_at'):
        op.add_column('analysis', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))

    if not column_exists('analysis_image', 'updated_at'):
        op.add_column('analysis_image', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))

    if not column_exists('analyzed_article', 'updated_at'):
        op.add_column('analyzed_article', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))

    if not column_exists('article', 'updated_at'):
        op.add_column('article', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))

    if not column_exists('article_image', 'updated_at'):
        op.add_column('article_image', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))

    if not column_exists('blacklist', 'updated_at'):
        op.add_column('blacklist', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))

    if column_exists('category', 'updated_at'):
        op.alter_column('category', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.TIMESTAMP(timezone=True),
               nullable=False,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))

    if not column_exists('chart', 'updated_at'):
        op.add_column('chart', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))

    if not column_exists('coin_bot', 'updated_at'):
        op.add_column('coin_bot', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))

    if column_exists('competitor', 'key'):
        op.alter_column('competitor', 'key',
               existing_type=sa.VARCHAR(),
               nullable=False)

    if column_exists('competitor', 'value'):
        op.alter_column('competitor', 'value',
               existing_type=sa.VARCHAR(),
               nullable=False)

    if column_exists('competitor', 'updated_at'):
        op.alter_column('competitor', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.TIMESTAMP(timezone=True),
               nullable=False)

    if column_exists('dapps', 'updated_at'):
        op.alter_column('dapps', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.TIMESTAMP(timezone=True),
               nullable=False)

    if column_exists('hacks', 'updated_at'):
        op.alter_column('hacks', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.TIMESTAMP(timezone=True),
               nullable=False)

    if column_exists('introduction', 'updated_at'):
        op.alter_column('introduction', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.TIMESTAMP(timezone=True),
               nullable=False)

    if not column_exists('keyword', 'updated_at'):
        op.add_column('keyword', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))

    if not column_exists('narrative_trading', 'updated_at'):
        op.add_column('narrative_trading', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))

    if not column_exists('purchased_plan', 'updated_at'):
        op.add_column('purchased_plan', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))

    if column_exists('revenue_model', 'updated_at'):
        op.alter_column('revenue_model', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.TIMESTAMP(timezone=True),
               nullable=False)

    if not column_exists('site', 'updated_at'):
        op.add_column('site', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))

    if column_exists('token_distribution', 'updated_at'):
        op.alter_column('token_distribution', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.TIMESTAMP(timezone=True),
               nullable=False)

    if column_exists('token_utility', 'updated_at'):
        op.alter_column('token_utility', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.TIMESTAMP(timezone=True),
               nullable=False)

    if column_exists('tokenomics', 'updated_at'):
        op.alter_column('tokenomics', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.TIMESTAMP(timezone=True),
               nullable=False)

    if not column_exists('top_story', 'updated_at'):
        op.add_column('top_story', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))

    if not column_exists('top_story_image', 'updated_at'):
        op.add_column('top_story_image', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))

    if column_exists('upgrades', 'updated_at'):
        op.alter_column('upgrades', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.TIMESTAMP(timezone=True),
               nullable=False)

    if not column_exists('used_keywords', 'updated_at'):
        op.add_column('used_keywords', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))

    if column_exists('used_keywords', 'article_date'):
        op.alter_column('used_keywords', 'article_date',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.String(),
               existing_nullable=True)

    if not column_exists('user_table', 'auth0id'):
        op.add_column('user_table', sa.Column('auth0id', sa.String(), nullable=True))

    if not column_exists('user_table', 'provider'):
        op.add_column('user_table', sa.Column('provider', sa.String(), nullable=True))

    if not column_exists('user_table', 'updated_at'):
        op.add_column('user_table', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))

    if column_exists('value_accrual_mechanisms', 'updated_at'):
        op.alter_column('value_accrual_mechanisms', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.TIMESTAMP(timezone=True),
               nullable=False)

def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    if column_exists('value_accrual_mechanisms', 'updated_at'):
        op.alter_column('value_accrual_mechanisms', 'updated_at',
               existing_type=sa.TIMESTAMP(timezone=True),
               type_=postgresql.TIMESTAMP(),
               nullable=True)

    if column_exists('user_table', 'updated_at'):
        op.drop_column('user_table', 'updated_at')

    if column_exists('user_table', 'provider'):
        op.drop_column('user_table', 'provider')

    if column_exists('user_table', 'auth0id'):
        op.drop_column('user_table', 'auth0id')

    if column_exists('used_keywords', 'article_date'):
        op.alter_column('used_keywords', 'article_date',
               existing_type=sa.String(),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True)

    if column_exists('used_keywords', 'updated_at'):
        op.drop_column('used_keywords', 'updated_at')

    if column_exists('upgrades', 'updated_at'):
        op.alter_column('upgrades', 'updated_at',
               existing_type=sa.TIMESTAMP(timezone=True),
               type_=postgresql.TIMESTAMP(),
               nullable=True)

    if column_exists('top_story_image', 'updated_at'):
        op.drop_column('top_story_image', 'updated_at')

    if column_exists('top_story', 'updated_at'):
        op.drop_column('top_story', 'updated_at')

    if column_exists('tokenomics', 'updated_at'):
        op.alter_column('tokenomics', 'updated_at',
               existing_type=sa.TIMESTAMP(timezone=True),
               type_=postgresql.TIMESTAMP(),
               nullable=True)

    if column_exists('token_utility', 'updated_at'):
        op.alter_column('token_utility', 'updated_at',
               existing_type=sa.TIMESTAMP(timezone=True),
               type_=postgresql.TIMESTAMP(),
               nullable=True)

    if column_exists('token_distribution', 'updated_at'):
        op.alter_column('token_distribution', 'updated_at',
               existing_type=sa.TIMESTAMP(timezone=True),
               type_=postgresql.TIMESTAMP(),
               nullable=True)

    if column_exists('site', 'updated_at'):
        op.drop_column('site', 'updated_at')

    if column_exists('revenue_model', 'updated_at'):
        op.alter_column('revenue_model', 'updated_at',
               existing_type=sa.TIMESTAMP(timezone=True),
               type_=postgresql.TIMESTAMP(),
               nullable=True)

    if column_exists('purchased_plan', 'updated_at'):
        op.drop_column('purchased_plan', 'updated_at')

    if column_exists('narrative_trading', 'updated_at'):
        op.drop_column('narrative_trading', 'updated_at')

    if column_exists('keyword', 'updated_at'):
        op.drop_column('keyword', 'updated_at')

    if column_exists('introduction', 'updated_at'):
        op.alter_column('introduction', 'updated_at',
               existing_type=sa.TIMESTAMP(timezone=True),
               type_=postgresql.TIMESTAMP(),
               nullable=True)

    if column_exists('hacks', 'updated_at'):
        op.alter_column('hacks', 'updated_at',
               existing_type=sa.TIMESTAMP(timezone=True),
               type_=postgresql.TIMESTAMP(),
               nullable=True)

    if column_exists('dapps', 'updated_at'):
        op.alter_column('dapps', 'updated_at',
               existing_type=sa.TIMESTAMP(timezone=True),
               type_=postgresql.TIMESTAMP(),
               nullable=True)

    if column_exists('competitor', 'updated_at'):
        op.alter_column('competitor', 'updated_at',
               existing_type=sa.TIMESTAMP(timezone=True),
               type_=postgresql.TIMESTAMP(),
               nullable=True)

    if column_exists('competitor', 'value'):
        op.alter_column('competitor', 'value',
               existing_type=sa.VARCHAR(),
               nullable=True)

    if column_exists('competitor', 'key'):
        op.alter_column('competitor', 'key',
               existing_type=sa.VARCHAR(),
               nullable=True)

    if column_exists('coin_bot', 'updated_at'):
        op.drop_column('coin_bot', 'updated_at')

    if column_exists('chart', 'updated_at'):
        op.drop_column('chart', 'updated_at')

    if column_exists('category', 'updated_at'):
        op.alter_column('category', 'updated_at',
               existing_type=sa.TIMESTAMP(timezone=True),
               type_=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))

    if column_exists('blacklist', 'updated_at'):
        op.drop_column('blacklist', 'updated_at')

    if column_exists('article_image', 'updated_at'):
        op.drop_column('article_image', 'updated_at')

    if column_exists('article', 'updated_at'):
        op.drop_column('article', 'updated_at')

    if column_exists('analyzed_article', 'updated_at'):
        op.drop_column('analyzed_article', 'updated_at')

    if column_exists('analysis_image', 'updated_at'):
        op.drop_column('analysis_image', 'updated_at')

    if column_exists('analysis', 'updated_at'):
        op.drop_column('analysis', 'updated_at')

    if column_exists('alert', 'updated_at'):
        op.drop_column('alert', 'updated_at')

    # Recreate the 'admin' table if it was dropped
    if not table_exists('admin'):
        op.create_table('admin',
        sa.Column('admin_id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('mail', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column('username', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column('password', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint('admin_id', name='admin_pkey')
    )
    # ### end Alembic commands ###
