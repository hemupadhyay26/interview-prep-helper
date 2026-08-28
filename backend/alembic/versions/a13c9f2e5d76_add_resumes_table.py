"""add resumes table

Revision ID: a13c9f2e5d76
Revises: 957fafa26dec
Create Date: 2026-08-28 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a13c9f2e5d76'
down_revision: Union[str, Sequence[str], None] = '957fafa26dec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('resumes',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('session_id', sa.String(length=36), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('raw_text', sa.Text(), nullable=False),
    sa.Column('profile', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('session_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('resumes')
