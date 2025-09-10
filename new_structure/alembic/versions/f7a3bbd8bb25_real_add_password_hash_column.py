"""real_add_password_hash_column

Revision ID: f7a3bbd8bb25
Revises: 776c0eaacf39
Create Date: 2025-09-09 20:16:42.463529

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer

# revision identifiers, used by Alembic.
revision = 'f7a3bbd8bb25'
down_revision = '776c0eaacf39'
branch_labels = None
depends_on = None


def upgrade():
    # Add password_hash column (nullable first for backfill)
    with op.batch_alter_table('teacher') as batch_op:
        batch_op.add_column(sa.Column('password_hash', sa.String(length=255), nullable=True))

    # Reflect minimal teacher table for data migration
    teacher = table('teacher',
        column('id', Integer),
        column('password', String(length=255)),
        column('password_hash', String(length=255)),
    )
    conn = op.get_bind()

    # Copy existing plain password into password_hash temporarily (will be hashed at app layer on next password change)
    conn.execute(
        teacher.update()
        .where(teacher.c.password_hash.is_(None))
        .values(password_hash=teacher.c.password)
    )

    # Make column non-nullable
    with op.batch_alter_table('teacher') as batch_op:
        batch_op.alter_column('password_hash', existing_type=sa.String(length=255), nullable=False)


def downgrade():
    with op.batch_alter_table('teacher') as batch_op:
        batch_op.drop_column('password_hash')
