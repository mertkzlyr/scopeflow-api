"""add task updated audit action

Revision ID: 61c98480469e
Revises: d5e92210f256
Create Date: 2026-07-09 14:10:32.059858

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61c98480469e'
down_revision: Union[str, Sequence[str], None] = 'd5e92210f256'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'TASK_UPDATED'"
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
