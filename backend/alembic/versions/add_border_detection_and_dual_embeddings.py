"""add border detection and dual embeddings

Revision ID: 4b7c8e9d2a1f
Revises: 303267ae68fe
Create Date: 2025-01-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '4b7c8e9d2a1f'
down_revision: Union[str, Sequence[str], None] = '303267ae68fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to support border detection and dual embeddings."""

    # Drop old embedding indexes first
    op.execute('DROP INDEX IF EXISTS clip_embeddings_idx')
    op.execute('DROP INDEX IF EXISTS dinov2_embeddings_idx')

    # Drop the old embedding column
    op.drop_column('disc_images', 'embedding')

    # Add new columns for dual embeddings
    op.add_column('disc_images',
                  sa.Column('original_embedding', Vector(768), nullable=True))
    op.add_column('disc_images',
                  sa.Column('cropped_embedding', Vector(768), nullable=True))

    # Add border detection metadata columns
    op.add_column('disc_images',
                  sa.Column('border_info', JSONB, nullable=True))
    op.add_column('disc_images',
                  sa.Column('cropped_image_path', sa.Text(), nullable=True))
    op.add_column('disc_images',
                  sa.Column('preprocessing_metadata', JSONB, nullable=True))

    # Create indexes for original embeddings
    op.execute("""
        CREATE INDEX clip_original_embeddings_idx
        ON disc_images USING ivfflat (original_embedding vector_cosine_ops)
        WHERE model_name = 'clip' AND original_embedding IS NOT NULL
    """)

    op.execute("""
        CREATE INDEX dinov2_original_embeddings_idx
        ON disc_images USING ivfflat (original_embedding vector_cosine_ops)
        WHERE model_name = 'dinov2' AND original_embedding IS NOT NULL
    """)

    # Create indexes for cropped embeddings
    op.execute("""
        CREATE INDEX clip_cropped_embeddings_idx
        ON disc_images USING ivfflat (cropped_embedding vector_cosine_ops)
        WHERE model_name = 'clip' AND cropped_embedding IS NOT NULL
    """)

    op.execute("""
        CREATE INDEX dinov2_cropped_embeddings_idx
        ON disc_images USING ivfflat (cropped_embedding vector_cosine_ops)
        WHERE model_name = 'dinov2' AND cropped_embedding IS NOT NULL
    """)

    # Create index on border_info for queries filtering by border detection
    op.execute("""
        CREATE INDEX disc_images_border_info_idx
        ON disc_images USING gin (border_info)
    """)


def downgrade() -> None:
    """Downgrade schema back to single embedding column."""

    # Drop new indexes
    op.execute('DROP INDEX IF EXISTS disc_images_border_info_idx')
    op.execute('DROP INDEX IF EXISTS dinov2_cropped_embeddings_idx')
    op.execute('DROP INDEX IF EXISTS clip_cropped_embeddings_idx')
    op.execute('DROP INDEX IF EXISTS dinov2_original_embeddings_idx')
    op.execute('DROP INDEX IF EXISTS clip_original_embeddings_idx')

    # Drop new columns
    op.drop_column('disc_images', 'preprocessing_metadata')
    op.drop_column('disc_images', 'cropped_image_path')
    op.drop_column('disc_images', 'border_info')
    op.drop_column('disc_images', 'cropped_embedding')
    op.drop_column('disc_images', 'original_embedding')

    # Restore old embedding column
    op.add_column('disc_images',
                  sa.Column('embedding', Vector(768), nullable=True))

    # Recreate old indexes
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
