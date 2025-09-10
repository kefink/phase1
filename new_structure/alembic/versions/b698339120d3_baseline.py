"""baseline

Revision ID: b698339120d3
Revises: 
Create Date: 2025-09-09 18:41:25.426700

"""
from alembic import op  # noqa
import sqlalchemy as sa  # noqa
from sqlalchemy.dialects import mysql  # noqa

# revision identifiers, used by Alembic.
revision = 'b698339120d3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Baseline migration (neutral). Marks current database schema as starting point without changes."""
    pass


def downgrade():
    """Baseline downgrade (neutral)."""
    pass
