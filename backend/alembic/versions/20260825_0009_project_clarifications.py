"""persist dynamic project clarification answers

Revision ID: 20260825_0009
Revises: 20260825_0008
"""
from alembic import op
import sqlalchemy as sa

revision="20260825_0009"
down_revision="20260825_0008"
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    if "project_clarifications" in sa.inspect(bind).get_table_names():return
    op.create_table(
        "project_clarifications",
        sa.Column("id",sa.String(36),primary_key=True),
        sa.Column("project_id",sa.String(36),sa.ForeignKey("projects.id",ondelete="CASCADE"),nullable=False),
        sa.Column("analysis_run_id",sa.String(36),nullable=True),
        sa.Column("question_key",sa.String(120),nullable=False),
        sa.Column("question_text",sa.Text,nullable=False),
        sa.Column("input_type",sa.String(40),nullable=False),
        sa.Column("answer_value",sa.Text,nullable=True),
        sa.Column("answered_at",sa.DateTime(timezone=True),nullable=True),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        mysql_charset="utf8mb4",mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_project_clarifications_project","project_clarifications",["project_id"])
    op.create_index("ix_project_clarifications_run","project_clarifications",["analysis_run_id"])

def downgrade():op.drop_table("project_clarifications")
