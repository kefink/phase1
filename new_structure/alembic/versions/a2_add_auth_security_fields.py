"""Add authentication security fields to Teacher (A2 hardening)

Revision ID: a2_add_auth_security_fields
Revises: 9f7b62982fb0
Create Date: 2025-09-14
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a2_add_auth_security_fields'
down_revision = '9f7b62982fb0'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('teacher') as batch_op:
        batch_op.add_column(sa.Column('failed_login_attempts', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('locked_until', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('last_login', sa.DateTime(), nullable=True))
    # Set default 0 for existing rows
    op.execute("UPDATE teacher SET failed_login_attempts = 0 WHERE failed_login_attempts IS NULL")


def downgrade():
    with op.batch_alter_table('teacher') as batch_op:
        batch_op.drop_column('last_login')
        batch_op.drop_column('locked_until')
        batch_op.drop_column('failed_login_attempts')
