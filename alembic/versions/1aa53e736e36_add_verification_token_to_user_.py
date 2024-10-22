# alembic/versions/1aa53e736e36_add_verification_token.py

"""add verification token to user_verifications
Revision ID: 1aa53e736e36
Revises: ee782e57a2ca
Create Date: 2024-10-22 14:31:04.034488
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '1aa53e736e36'
down_revision: Union[str, None] = 'ee782e57a2ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Agregar la columna verification_token
    op.add_column('user_verifications',
        sa.Column('verification_token', sa.String(255), nullable=True)
    )
    
    # Crear un índice único para verification_token
    op.create_index(
        'ix_user_verifications_verification_token',
        'user_verifications',
        ['verification_token'],
        unique=True
    )

def downgrade() -> None:
    # Eliminar el índice primero
    op.drop_index('ix_user_verifications_verification_token', table_name='user_verifications')
    
    # Luego eliminar la columna
    op.drop_column('user_verifications', 'verification_token')