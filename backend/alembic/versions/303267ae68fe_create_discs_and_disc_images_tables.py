"""create discs and disc_images tables

Revision ID: 303267ae68fe
Revises:
Create Date: 2025-11-16 21:13:22.990695

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '303267ae68fe'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create discs table
    op.create_table(
        'discs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_name', sa.String(length=255), nullable=False),
        sa.Column('owner_contact', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='registered'),
        sa.Column('disc_model', sa.String(length=255), nullable=True),
        sa.Column('disc_color', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('registered_date', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('stolen_date', sa.TIMESTAMP(), nullable=True),
        sa.Column('found_date', sa.TIMESTAMP(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create disc_images table
    op.create_table(
        'disc_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('disc_id', sa.Integer(), nullable=False),
        sa.Column('image_url', sa.Text(), nullable=False),
        sa.Column('image_path', sa.Text(), nullable=True),
        sa.Column('model_name', sa.String(length=50), nullable=False),
        sa.Column('embedding', Vector(768), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['disc_id'], ['discs.id'], ondelete='CASCADE')
    )

    # Create indexes for fast similarity search
    op.execute("""
        CREATE INDEX clip_embeddings_idx
        ON disc_images USING ivfflat (embedding vector_cosine_ops)
        WHERE model_name = 'clip'
    """)

    op.execute("""
        CREATE INDEX dinov2_embeddings_idx
        ON disc_images USING ivfflat (embedding vector_cosine_ops)
        WHERE model_name = 'dinov2'
    """)

    # Create index on disc_id for faster lookups
    op.create_index('disc_images_disc_id_idx', 'disc_images', ['disc_id'])

    # Create index on status for filtering
    op.create_index('discs_status_idx', 'discs', ['status'])

    # Create trigger function to update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql'
    """)

    # Create trigger to automatically update updated_at
    op.execute("""
        CREATE TRIGGER update_discs_updated_at
        BEFORE UPDATE ON discs
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop trigger
    op.execute('DROP TRIGGER IF EXISTS update_discs_updated_at ON discs')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')

    # Drop indexes
    op.drop_index('discs_status_idx', table_name='discs')
    op.drop_index('disc_images_disc_id_idx', table_name='disc_images')
    op.execute('DROP INDEX IF EXISTS dinov2_embeddings_idx')
    op.execute('DROP INDEX IF EXISTS clip_embeddings_idx')

    # Drop tables
    op.drop_table('disc_images')
    op.drop_table('discs')

    # Drop extension
    op.execute('DROP EXTENSION IF EXISTS vector')
