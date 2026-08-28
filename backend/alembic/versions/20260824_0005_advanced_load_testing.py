"""advanced authorized k6 planning and evidence

Revision ID: 20260824_0005
Revises: 20260824_0004
"""
from alembic import op
import sqlalchemy as sa

revision="20260824_0005"
down_revision="20260824_0004"
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    inspector=sa.inspect(bind)
    existing_columns={c["name"] for c in inspector.get_columns("load_test_plans")}
    analysis_run_column=sa.Column("analysis_run_id",sa.String(36),nullable=True) if bind.dialect.name=="sqlite" else sa.Column("analysis_run_id",sa.String(36),sa.ForeignKey("analysis_runs.id",ondelete="SET NULL"),nullable=True)
    additions=[
        analysis_run_column,
        sa.Column("public_id",sa.String(36),nullable=True),
        sa.Column("authorization_confirmed",sa.Boolean(),nullable=False,server_default=sa.false()),
        sa.Column("risk_acknowledged",sa.Boolean(),nullable=False,server_default=sa.false()),
        sa.Column("expected_concurrent_users",sa.Integer(),nullable=True),
        sa.Column("estimated_rps",sa.Float(),nullable=True),sa.Column("peak_rps",sa.Float(),nullable=True),
        sa.Column("recommended_hosting",sa.String(30),nullable=True),sa.Column("recommended_vcpu",sa.Integer(),nullable=True),
        sa.Column("recommended_ram_gb",sa.Float(),nullable=True),sa.Column("confidence",sa.Float(),nullable=True),
        sa.Column("status",sa.String(30),nullable=False,server_default="GENERATED"),
        sa.Column("generator_version",sa.String(40),nullable=False,server_default="k6-generator-1.0.0"),
        sa.Column("workload_snapshot_json",sa.JSON(),nullable=True),sa.Column("ai_recommendation_snapshot_json",sa.JSON(),nullable=True),
        sa.Column("downloaded_at",sa.DateTime(timezone=True),nullable=True),
    ]
    for column in additions:
        if column.name not in existing_columns:op.add_column("load_test_plans",column)
    if bind.dialect.name=="mysql":
        op.execute("ALTER TABLE load_test_plans MODIFY COLUMN public_id VARCHAR(36) NOT NULL")
        op.execute("UPDATE load_test_plans SET public_id=id, workload_snapshot_json=COALESCE(workload_snapshot_json,JSON_OBJECT()), ai_recommendation_snapshot_json=COALESCE(ai_recommendation_snapshot_json,JSON_OBJECT())")
    else:
        op.execute("UPDATE load_test_plans SET public_id=id WHERE public_id IS NULL")
    inspector=sa.inspect(bind)
    uniques={u["name"] for u in inspector.get_unique_constraints("load_test_plans")}
    if "uq_load_test_plans_public_id" not in uniques and "uq_load_test_public_id" not in uniques:
        if bind.dialect.name=="sqlite":
            with op.batch_alter_table("load_test_plans") as batch:batch.create_unique_constraint("uq_load_test_plans_public_id",["public_id"])
        else:op.create_unique_constraint("uq_load_test_plans_public_id","load_test_plans",["public_id"])
    indexes={i["name"] for i in inspector.get_indexes("load_test_plans")}
    if "ix_load_test_plans_analysis_run_id" not in indexes and "ix_load_test_run" not in indexes:op.create_index("ix_load_test_plans_analysis_run_id","load_test_plans",["analysis_run_id"])
    if "ix_load_test_plans_status" not in indexes:op.create_index("ix_load_test_plans_status","load_test_plans",["status"])
    tables=set(inspector.get_table_names())
    if "load_test_stages" not in tables:
        op.create_table("load_test_stages",sa.Column("id",sa.String(36),primary_key=True),sa.Column("load_test_plan_id",sa.String(36),sa.ForeignKey("load_test_plans.id",ondelete="CASCADE"),nullable=False),sa.Column("stage_order",sa.Integer,nullable=False),sa.Column("duration_seconds",sa.Integer,nullable=False),sa.Column("target_virtual_users",sa.Integer,nullable=False),sa.Column("stage_type",sa.String(20),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.UniqueConstraint("load_test_plan_id","stage_order",name="uq_load_test_stage_order"))
        op.create_index("ix_load_test_stages_plan","load_test_stages",["load_test_plan_id"])
    elif "stage_type" not in {c["name"] for c in inspector.get_columns("load_test_stages")}:
        op.add_column("load_test_stages",sa.Column("stage_type",sa.String(20),nullable=False,server_default="RAMP_UP"))
    if "load_test_results" not in tables:
        op.create_table("load_test_results",sa.Column("id",sa.String(36),primary_key=True),sa.Column("public_id",sa.String(36),nullable=False,unique=True),sa.Column("load_test_plan_id",sa.String(36),sa.ForeignKey("load_test_plans.id",ondelete="CASCADE"),nullable=False),sa.Column("project_id",sa.String(36),sa.ForeignKey("projects.id",ondelete="CASCADE"),nullable=False),sa.Column("analysis_run_id",sa.String(36),sa.ForeignKey("analysis_runs.id",ondelete="SET NULL"),nullable=True),sa.Column("source_type",sa.String(30),nullable=False),sa.Column("started_at",sa.DateTime(timezone=True)),sa.Column("completed_at",sa.DateTime(timezone=True)),sa.Column("total_requests",sa.Integer),sa.Column("total_iterations",sa.Integer),sa.Column("average_rps",sa.Float),sa.Column("http_req_duration_avg_ms",sa.Float),sa.Column("http_req_duration_min_ms",sa.Float),sa.Column("http_req_duration_max_ms",sa.Float),sa.Column("http_req_duration_p50_ms",sa.Float),sa.Column("http_req_duration_p90_ms",sa.Float),sa.Column("http_req_duration_p95_ms",sa.Float),sa.Column("http_req_duration_p99_ms",sa.Float),sa.Column("http_req_failed_rate",sa.Float),sa.Column("checks_passed",sa.Integer),sa.Column("checks_failed",sa.Integer),sa.Column("data_received_bytes",sa.Integer),sa.Column("data_sent_bytes",sa.Integer),sa.Column("peak_vus",sa.Integer),sa.Column("thresholds_passed",sa.Boolean,nullable=False,server_default=sa.false()),sa.Column("overall_status",sa.String(30),nullable=False),sa.Column("ai_validation_status",sa.String(40),nullable=False),sa.Column("analysis_json",sa.JSON),sa.Column("raw_summary_json",sa.JSON),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),mysql_charset="utf8mb4",mysql_collate="utf8mb4_unicode_ci")
        for name,cols in (("ix_load_test_results_plan",["load_test_plan_id"]),("ix_load_test_results_project",["project_id"]),("ix_load_test_results_analysis",["analysis_run_id"]),("ix_load_test_results_status",["overall_status"])): op.create_index(name,"load_test_results",cols)
    if "load_test_environments" not in tables:
        op.create_table("load_test_environments",sa.Column("id",sa.String(36),primary_key=True),sa.Column("load_test_plan_id",sa.String(36),sa.ForeignKey("load_test_plans.id",ondelete="CASCADE"),nullable=False,unique=True),sa.Column("hosting_type",sa.String(40)),sa.Column("vcpu",sa.Integer),sa.Column("ram_gb",sa.Float),sa.Column("region",sa.String(80)),sa.Column("database_type",sa.String(80)),sa.Column("cdn_enabled",sa.Boolean),sa.Column("notes",sa.String(1000)),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),mysql_charset="utf8mb4",mysql_collate="utf8mb4_unicode_ci")

def downgrade():
    op.drop_table("load_test_environments");op.drop_table("load_test_results");op.drop_table("load_test_stages")
    op.drop_constraint("uq_load_test_plans_public_id","load_test_plans",type_="unique")
    for name in ["downloaded_at","ai_recommendation_snapshot_json","workload_snapshot_json","generator_version","status","confidence","recommended_ram_gb","recommended_vcpu","recommended_hosting","peak_rps","estimated_rps","expected_concurrent_users","risk_acknowledged","authorization_confirmed","public_id","analysis_run_id"]: op.drop_column("load_test_plans",name)
