#!/usr/bin/env python3
"""
Apply vocabulary search indexes to the database
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from alembic.config import Config

from alembic import command


def apply_migration():
    """Apply the search indexes migration"""
    try:
        # Get Alembic configuration
        alembic_cfg = Config("alembic.ini")

        # Run the migration
        command.upgrade(alembic_cfg, "add_vocabulary_indexes")

    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    apply_migration()
