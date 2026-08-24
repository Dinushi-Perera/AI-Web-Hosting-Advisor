"""allow unavailable recommendation costs in MySQL generated columns

Revision ID: 20260824_0004
Revises: 20260823_0003
"""

from alembic import op

revision = "20260824_0004"
down_revision = "20260823_0003"
branch_labels = None
depends_on = None


def upgrade():
    if op.get_bind().dialect.name != "mysql":
        return
    op.execute(
        """
        ALTER TABLE recommendations
        MODIFY COLUMN estimated_min_monthly_cost_usd DECIMAL(12,2)
          GENERATED ALWAYS AS (
            CAST(NULLIF(JSON_UNQUOTE(JSON_EXTRACT(estimated_cost, '$.min')), 'null') AS DECIMAL(12,2))
          ) STORED,
        MODIFY COLUMN estimated_max_monthly_cost_usd DECIMAL(12,2)
          GENERATED ALWAYS AS (
            CAST(NULLIF(JSON_UNQUOTE(JSON_EXTRACT(estimated_cost, '$.max')), 'null') AS DECIMAL(12,2))
          ) STORED
        """
    )


def downgrade():
    if op.get_bind().dialect.name != "mysql":
        return
    op.execute(
        """
        ALTER TABLE recommendations
        MODIFY COLUMN estimated_min_monthly_cost_usd DECIMAL(12,2)
          GENERATED ALWAYS AS (
            CAST(JSON_UNQUOTE(JSON_EXTRACT(estimated_cost, '$.min')) AS DECIMAL(12,2))
          ) STORED,
        MODIFY COLUMN estimated_max_monthly_cost_usd DECIMAL(12,2)
          GENERATED ALWAYS AS (
            CAST(JSON_UNQUOTE(JSON_EXTRACT(estimated_cost, '$.max')) AS DECIMAL(12,2))
          ) STORED
        """
    )
