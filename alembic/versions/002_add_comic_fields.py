"""add writer artist language and other fields to comics

Revision ID: 002_add_comic_fields
Revises: 001_expand_genres_publisher
Create Date: 2026-04-06

"""
from alembic import op
import sqlalchemy as sa

revision = '002_add_comic_fields'
down_revision = '001_expand_genres_publisher'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('comics', sa.Column('writer',       sa.String(256), nullable=True))
    op.add_column('comics', sa.Column('artist',       sa.String(256), nullable=True))
    op.add_column('comics', sa.Column('language',     sa.String(64),  nullable=True))
    op.add_column('comics', sa.Column('age_rating',   sa.String(64),  nullable=True))
    op.add_column('comics', sa.Column('format',       sa.String(128), nullable=True))
    op.add_column('comics', sa.Column('awards',       sa.Text,        nullable=True))
    op.add_column('comics', sa.Column('volume_count', sa.Integer,     nullable=True))
    op.add_column('comics', sa.Column('status',       sa.String(64),  nullable=True))


def downgrade() -> None:
    op.drop_column('comics', 'writer')
    op.drop_column('comics', 'artist')
    op.drop_column('comics', 'language')
    op.drop_column('comics', 'age_rating')
    op.drop_column('comics', 'format')
    op.drop_column('comics', 'awards')
    op.drop_column('comics', 'volume_count')
    op.drop_column('comics', 'status')