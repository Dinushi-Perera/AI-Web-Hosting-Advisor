"""remove simple/advanced experience mode

Revision ID: 20260823_0002
Revises: 20260821_0001
"""

from alembic import op
import sqlalchemy as sa

revision = "20260823_0002"
down_revision = "20260821_0001"
branch_labels = None
depends_on = None


def upgrade():
    columns={column["name"] for column in sa.inspect(op.get_bind()).get_columns("user_preferences")}
    with op.batch_alter_table("user_preferences") as batch_op:
        if "experience_mode" in columns:
            batch_op.drop_column("experience_mode")
        if "onboarding_completed" not in columns:
            batch_op.add_column(sa.Column("onboarding_completed",sa.Boolean(),nullable=False,server_default=sa.false()))


def downgrade():
    columns={column["name"] for column in sa.inspect(op.get_bind()).get_columns("user_preferences")}
    with op.batch_alter_table("user_preferences") as batch_op:
        if "onboarding_completed" in columns:
            batch_op.drop_column("onboarding_completed")
        if "experience_mode" not in columns:
            batch_op.add_column(sa.Column("experience_mode", sa.String(20), nullable=False, server_default="ADVANCED"))
