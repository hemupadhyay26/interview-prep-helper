"""add job_postings table

Revision ID: b7e4c2a19f83
Revises: a13c9f2e5d76
Create Date: 2026-08-28 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e4c2a19f83'
down_revision: Union[str, Sequence[str], None] = 'a13c9f2e5d76'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('job_postings',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('session_id', sa.String(length=36), nullable=False),
    sa.Column('source_url', sa.String(length=2048), nullable=False),
    sa.Column('raw_text', sa.Text(), nullable=False),
    sa.Column('details', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('session_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('job_postings')
