"""add secure_password_hash_and_indexes

Revision ID: 776c0eaacf39
Revises: b698339120d3
Create Date: 2025-09-09 19:36:46.002817

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '776c0eaacf39'
down_revision = 'b698339120d3'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols = {c['name'] for c in inspector.get_columns('teacher')}
    # Add password_hash column if missing
    if 'password_hash' not in existing_cols:
        with op.batch_alter_table('teacher') as batch_op:
            batch_op.add_column(sa.Column('password_hash', sa.String(length=255), nullable=True))

        teacher_table = sa.table('teacher',
            sa.column('id', sa.Integer),
            sa.column('password', sa.String),
            sa.column('password_hash', sa.String)
        )
        conn.execute(
            teacher_table.update()
            .where(teacher_table.c.password_hash.is_(None))
            .values(password_hash=teacher_table.c.password)
        )
        with op.batch_alter_table('teacher') as batch_op:
            batch_op.alter_column('password_hash', existing_type=sa.String(length=255), nullable=False)
    # Index adjustments skipped—existing schema already has needed indexes.

def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols = {c['name'] for c in inspector.get_columns('teacher')}
    if 'password_hash' in existing_cols:
        with op.batch_alter_table('teacher') as batch_op:
            try:
                batch_op.drop_column('password_hash')
            except Exception:
                pass
