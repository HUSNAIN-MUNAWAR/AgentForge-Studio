"""AgentForge Studio v2 queue, memory, metrics metadata

Revision ID: 0002_v2_queue_memory
Revises: 0001_initial
Create Date: 2026-06-26
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_v2_queue_memory"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The local MVP also calls SQLAlchemy Base.metadata.create_all for development.
    # This migration documents the v2 schema additions for teams using Alembic explicitly.
    pass


def downgrade() -> None:
    pass
