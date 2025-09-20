"""Add password migration tracking column

This migration replaces the standalone database/migrate_to_bcrypt.py script
and adds proper version control for the password hash migration feature.

Revision ID: 10f18f66a1df
Revises: 879b4bfbd98e
Create Date: 2025-09-19 20:38:54.984758

"""
from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '10f18f66a1df'
down_revision: Union[str, Sequence[str], None] = '879b4bfbd98e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add password migration tracking column and mark existing users."""
    # Add the needs_password_migration column to users table
    op.add_column('users', sa.Column('needs_password_migration', sa.Boolean(), server_default='1'))
    
    # Update existing users to mark them for password migration
    # This handles users who have SHA256 passwords that need to be migrated to bcrypt
    connection = op.get_bind()
    connection.execute(
        text("""
            UPDATE users 
            SET needs_password_migration = 1,
                updated_at = :updated_at
            WHERE hashed_password IS NOT NULL AND hashed_password != ''
        """),
        {"updated_at": datetime.utcnow()}
    )


def downgrade() -> None:
    """Remove password migration tracking column."""
    op.drop_column('users', 'needs_password_migration')
