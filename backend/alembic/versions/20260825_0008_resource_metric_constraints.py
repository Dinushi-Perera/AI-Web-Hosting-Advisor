"""enforce valid optional monitoring evidence

Revision ID: 20260825_0008
Revises: 20260825_0007
"""
from alembic import op

revision="20260825_0008"
down_revision="20260825_0007"
branch_labels=None
depends_on=None

PERCENTAGES="(cpu_peak_percent IS NULL OR cpu_peak_percent BETWEEN 0 AND 100) AND (cpu_avg_percent IS NULL OR cpu_avg_percent BETWEEN 0 AND 100) AND (ram_peak_percent IS NULL OR ram_peak_percent BETWEEN 0 AND 100) AND (ram_avg_percent IS NULL OR ram_avg_percent BETWEEN 0 AND 100) AND (database_cpu_peak_percent IS NULL OR database_cpu_peak_percent BETWEEN 0 AND 100)"

def upgrade():
    if op.get_bind().dialect.name=="mysql":
        op.create_check_constraint("ck_load_test_resource_percentages","load_test_resource_metrics",PERCENTAGES)
        op.create_check_constraint("ck_load_test_resource_nonnegative","load_test_resource_metrics","(database_connections_peak IS NULL OR database_connections_peak >= 0) AND (server_load_average IS NULL OR server_load_average >= 0)")

def downgrade():
    if op.get_bind().dialect.name=="mysql":
        op.drop_constraint("ck_load_test_resource_nonnegative","load_test_resource_metrics",type_="check")
        op.drop_constraint("ck_load_test_resource_percentages","load_test_resource_metrics",type_="check")
