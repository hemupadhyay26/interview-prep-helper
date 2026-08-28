"""make resume global (drop resumes.session_id)

Revision ID: c9a1f4b2e7d0
Revises: b7e4c2a19f83
Create Date: 2026-08-28 12:00:00.000000

The resume is no longer scoped to a chat session - there is one resume
for the whole app, shared by every session. Drop the session_id column
(and with it its unique constraint and FK to chat_sessions).

Any rows from the old per-session model are left in place; the app now
treats the single most recent row as "the resume".
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9a1f4b2e7d0'
down_revision: Union[str, Sequence[str], None] = 'b7e4c2a19f83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('resumes') as batch_op:
        batch_op.drop_column('session_id')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('resumes') as batch_op:
        batch_op.add_column(
            sa.Column('session_id', sa.String(length=36), nullable=True)
        )
