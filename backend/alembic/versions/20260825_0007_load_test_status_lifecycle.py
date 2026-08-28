"""allow the complete load-test plan lifecycle

Revision ID: 20260825_0007
Revises: 20260825_0006
"""
from alembic import op

revision="20260825_0007"
down_revision="20260825_0006"
branch_labels=None
depends_on=None

def upgrade():
    if op.get_bind().dialect.name=="mysql":
        op.drop_constraint("ck_load_test_status","load_test_plans",type_="check")
        op.create_check_constraint("ck_load_test_status","load_test_plans","status IN ('DRAFT','GENERATED','READY_TO_RUN','RUNNING','DOWNLOADED','RESULT_IMPORTED','ANALYSED','RUN_FAILED','ARCHIVED')")

def downgrade():
    if op.get_bind().dialect.name=="mysql":
        op.execute("UPDATE load_test_plans SET status='DOWNLOADED' WHERE status IN ('RESULT_IMPORTED','ANALYSED')")
        op.drop_constraint("ck_load_test_status","load_test_plans",type_="check")
        op.create_check_constraint("ck_load_test_status","load_test_plans","status IN ('DRAFT','GENERATED','DOWNLOADED','ARCHIVED')")
