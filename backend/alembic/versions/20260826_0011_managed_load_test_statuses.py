"""allow managed k6 execution lifecycle statuses

Revision ID: 20260826_0011
Revises: 20260825_0010
"""

from alembic import op


revision = "20260826_0011"
down_revision = "20260825_0010"
branch_labels = None
depends_on = None


_CURRENT = "status IN ('DRAFT','GENERATED','READY_TO_RUN','RUNNING','DOWNLOADED','RESULT_IMPORTED','ANALYSED','RUN_FAILED','ARCHIVED')"
_PREVIOUS = "status IN ('DRAFT','GENERATED','DOWNLOADED','RESULT_IMPORTED','ANALYSED','ARCHIVED')"


def upgrade():
    if op.get_bind().dialect.name == "mysql":
        op.drop_constraint("ck_load_test_status", "load_test_plans", type_="check")
        op.create_check_constraint("ck_load_test_status", "load_test_plans", _CURRENT)


def downgrade():
    if op.get_bind().dialect.name == "mysql":
        op.execute("UPDATE load_test_plans SET status='GENERATED' WHERE status IN ('READY_TO_RUN','RUNNING','RUN_FAILED')")
        op.drop_constraint("ck_load_test_status", "load_test_plans", type_="check")
        op.create_check_constraint("ck_load_test_status", "load_test_plans", _PREVIOUS)
