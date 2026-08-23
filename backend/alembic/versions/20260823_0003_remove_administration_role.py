"""remove the administration role

Revision ID: 20260823_0003
Revises: 20260823_0002
"""

from alembic import op

revision = "20260823_0003"
down_revision = "20260823_0002"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE users SET role = 'USER' WHERE role <> 'USER'")


def downgrade():
    pass
