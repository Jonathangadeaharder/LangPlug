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
from sqlalchemy import inspect, text


# revision identifiers, used by Alembic.
revision: str = '10f18f66a1df'
down_revision: Union[str, Sequence[str], None] = '879b4bfbd98e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add password migration tracking column and mark existing users."""
    # Add the needs_password_migration column to users table
    op.add_column('users', sa.Column('needs_password_migration', sa.Boolean(), server_default=sa.true()))

    connection = op.get_bind()
    inspector = inspect(connection)
    user_columns = {column['name'] for column in inspector.get_columns('users')}

    update_target = None
    if 'hashed_password' in user_columns:
        update_target = 'hashed_password'
    elif 'password_hash' in user_columns:
        update_target = 'password_hash'

    if update_target:
        connection.execute(
            text(
                f"""
                UPDATE users
                SET needs_password_migration = :needs_migration,
                    updated_at = :updated_at
                WHERE {update_target} IS NOT NULL AND {update_target} != ''
                """
            ),
            {
                "updated_at": datetime.utcnow(),
                "needs_migration": True,
            }
        )


def downgrade() -> None:
    """Remove password migration tracking column."""
    op.drop_column('users', 'needs_password_migration')
