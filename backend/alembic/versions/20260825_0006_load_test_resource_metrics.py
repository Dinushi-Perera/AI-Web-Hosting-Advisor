"""optional load-test resource monitoring evidence

Revision ID: 20260825_0006
Revises: 20260824_0005
"""
from alembic import op
import sqlalchemy as sa

revision="20260825_0006"
down_revision="20260824_0005"
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    if "load_test_resource_metrics" in sa.inspect(bind).get_table_names():return
    op.create_table("load_test_resource_metrics",sa.Column("id",sa.String(36),primary_key=True),sa.Column("load_test_result_id",sa.String(36),sa.ForeignKey("load_test_results.id",ondelete="CASCADE"),nullable=False,unique=True),sa.Column("cpu_peak_percent",sa.Float),sa.Column("cpu_avg_percent",sa.Float),sa.Column("ram_peak_percent",sa.Float),sa.Column("ram_avg_percent",sa.Float),sa.Column("database_cpu_peak_percent",sa.Float),sa.Column("database_connections_peak",sa.Integer),sa.Column("server_load_average",sa.Float),sa.Column("notes",sa.String(1000)),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),mysql_charset="utf8mb4",mysql_collate="utf8mb4_unicode_ci")
    op.create_index("ix_load_test_resource_metric_result","load_test_resource_metrics",["load_test_result_id"],unique=True)

def downgrade():op.drop_table("load_test_resource_metrics")
