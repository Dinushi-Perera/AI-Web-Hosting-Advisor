"""remove location targeting and user currency preferences

Revision ID: 20260827_0012
Revises: 20260826_0011
"""

from alembic import op
import sqlalchemy as sa


revision = "20260827_0012"
down_revision = "20260826_0011"
branch_labels = None
depends_on = None


def _columns(table: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}


def _indexes(table: str) -> set[str]:
    return {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table)}


def _drop_column(table: str, column: str) -> None:
    if column not in _columns(table):
        return
    with op.batch_alter_table(table) as batch:
        batch.drop_column(column)


def upgrade():
    for index in ("ix_hosting_provider_region", "ix_hosting_plans_region"):
        if index in _indexes("hosting_plans"):
            op.drop_index(index, table_name="hosting_plans")

    _drop_column("users", "default_region")
    _drop_column("user_preferences", "default_currency")
    _drop_column("user_preferences", "default_region")
    _drop_column("projects", "target_region")
    _drop_column("load_test_environments", "region")
    _drop_column("hosting_plans", "region")


def downgrade():
    additions = (
        ("users", sa.Column("default_region", sa.String(80), nullable=True)),
        ("user_preferences", sa.Column("default_currency", sa.String(3), nullable=False, server_default="USD")),
        ("user_preferences", sa.Column("default_region", sa.String(80), nullable=True)),
        ("projects", sa.Column("target_region", sa.String(80), nullable=True)),
        ("load_test_environments", sa.Column("region", sa.String(80), nullable=True)),
        ("hosting_plans", sa.Column("region", sa.String(80), nullable=True)),
    )
    for table, column in additions:
        if column.name not in _columns(table):
            with op.batch_alter_table(table) as batch:
                batch.add_column(column)
