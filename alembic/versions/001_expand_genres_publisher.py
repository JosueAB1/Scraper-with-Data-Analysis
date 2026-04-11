"""fix: expand genres and publisher fields to Text

Revision ID: 001_expand_genres_publisher
Revises: 
Create Date: 2026-04-01

"""
from alembic import op
import sqlalchemy as sa

revision = '001_expand_genres_publisher'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Applied manually via psql ALTER TABLE
    pass


def downgrade() -> None:
    op.alter_column('books', 'genres', type_=sa.String(512))
    op.alter_column('books', 'publisher', type_=sa.String(256))