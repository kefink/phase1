"""drop_legacy_plain_password_column

Revision ID: 874fb2be6ad0
Revises: 9f7b62982fb0
Create Date: 2025-09-09 21:05:29.982566

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '874fb2be6ad0'
down_revision = '9f7b62982fb0'
branch_labels = None
depends_on = None


def upgrade():
    # Optional: rename password_hash -> password for canonical naming after legacy removal
    conn = op.get_bind()
    inspector = inspect(conn)
    cols = {c['name'] for c in inspector.get_columns('teacher')}
    if 'password_hash' in cols and 'password' not in cols:
        with op.batch_alter_table('teacher') as batch_op:
            batch_op.alter_column('password_hash', new_column_name='password', existing_type=sa.String(length=255))


def downgrade():
    # Reverse rename if possible
    conn = op.get_bind()
    inspector = inspect(conn)
    cols = {c['name'] for c in inspector.get_columns('teacher')}
    if 'password' in cols and 'password_hash' not in cols:
        with op.batch_alter_table('teacher') as batch_op:
            batch_op.alter_column('password', new_column_name='password_hash', existing_type=sa.String(length=255))
