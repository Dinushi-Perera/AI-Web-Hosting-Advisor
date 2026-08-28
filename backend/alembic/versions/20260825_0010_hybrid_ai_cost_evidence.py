"""persist hybrid AI decision and cost evidence

Revision ID: 20260825_0010
Revises: 20260825_0009
"""
from alembic import op
import sqlalchemy as sa

revision="20260825_0010"
down_revision="20260825_0009"
branch_labels=None
depends_on=None

def upgrade():
    columns={column["name"] for column in sa.inspect(op.get_bind()).get_columns("recommendations")}
    for name in ("decision_evidence","cost_optimization","llm_explanation"):
        if name not in columns:
            op.add_column("recommendations",sa.Column(name,sa.JSON(),nullable=True))
            op.execute(sa.text(f"UPDATE recommendations SET {name} = '{{}}' WHERE {name} IS NULL"))
            if op.get_bind().dialect.name == "sqlite":
                with op.batch_alter_table("recommendations") as batch:
                    batch.alter_column(name,existing_type=sa.JSON(),nullable=False)
            else:
                op.alter_column("recommendations",name,existing_type=sa.JSON(),nullable=False)
    if "llm_status" not in columns:
        op.add_column("recommendations",sa.Column("llm_status",sa.String(30),nullable=False,server_default="NOT_CONFIGURED"))
        if op.get_bind().dialect.name == "sqlite":
            with op.batch_alter_table("recommendations") as batch:
                batch.alter_column("llm_status",existing_type=sa.String(30),server_default=None)
        else:
            op.alter_column("recommendations","llm_status",existing_type=sa.String(30),server_default=None)
    if "llm_model" not in columns:
        op.add_column("recommendations",sa.Column("llm_model",sa.String(80),nullable=True))

def downgrade():
    for name in ("llm_model","llm_status","llm_explanation","cost_optimization","decision_evidence"):
        op.drop_column("recommendations",name)
