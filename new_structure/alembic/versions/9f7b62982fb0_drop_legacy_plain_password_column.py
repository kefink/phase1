"""drop_legacy_plain_password_column

Revision ID: 9f7b62982fb0
Revises: f7a3bbd8bb25
Create Date: 2025-09-09 21:05:14.830156

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '9f7b62982fb0'
down_revision = 'f7a3bbd8bb25'
branch_labels = None
depends_on = None


def upgrade():
    # Safety: ensure password_hash column exists and legacy column exists.
    conn = op.get_bind()
    inspector = inspect(conn)
    cols = {c['name'] for c in inspector.get_columns('teacher')}
    if 'password_hash' not in cols:
        raise RuntimeError("password_hash column missing; cannot drop legacy password column")
    if 'password' in cols:
        # Before dropping, ensure no NULL password_hash rows
        null_count = conn.execute(sa.text("SELECT COUNT(*) FROM teacher WHERE password_hash IS NULL")).scalar()
        if null_count:
            raise RuntimeError(f"Refusing to drop password column; {null_count} NULL password_hash rows remain")
        with op.batch_alter_table('teacher') as batch_op:
            batch_op.drop_column('password')


def downgrade():
    # Re-create legacy password column as nullable (data cannot be restored)
    conn = op.get_bind()
    inspector = inspect(conn)
    cols = {c['name'] for c in inspector.get_columns('teacher')}
    if 'password' not in cols:
        with op.batch_alter_table('teacher') as batch_op:
            batch_op.add_column(sa.Column('password', sa.String(length=100), nullable=True))
