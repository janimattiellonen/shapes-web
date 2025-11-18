"""add upload_status column to discs table

Revision ID: 5c8d9f0e3b2g
Revises: 4b7c8e9d2a1f
Create Date: 2025-03-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c8d9f0e3b2g'
down_revision: Union[str, Sequence[str], None] = '4b7c8e9d2a1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add upload_status column to track disc upload workflow."""

    # Add upload_status column
    op.add_column('discs',
                  sa.Column('upload_status', sa.String(length=50),
                           nullable=False,
                           server_default='PENDING'))

    # Create index on upload_status for filtering
    op.create_index('discs_upload_status_idx', 'discs', ['upload_status'])

    # Update existing records to have SUCCESS status
    op.execute("UPDATE discs SET upload_status = 'SUCCESS' WHERE upload_status = 'PENDING'")


def downgrade() -> None:
    """Remove upload_status column."""

    # Drop index
    op.drop_index('discs_upload_status_idx', table_name='discs')

    # Drop column
    op.drop_column('discs', 'upload_status')
