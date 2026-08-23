"""initial schema
Revision ID: 20260821_0001
Revises: 
"""
from alembic import op
from app.core.database import Base
import app.models.entities
revision="20260821_0001"
down_revision=None
branch_labels=None
depends_on=None
def upgrade(): Base.metadata.create_all(bind=op.get_bind())
def downgrade(): Base.metadata.drop_all(bind=op.get_bind())
