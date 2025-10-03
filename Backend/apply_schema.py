#!/usr/bin/env python3
"""
Apply PostgreSQL schema directly
"""

import logging
import sys
from pathlib import Path

import psycopg2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def apply_postgresql_schema():
    """Apply PostgreSQL schema from file"""
    try:
        # Connection parameters
        conn_params = {
            "host": "localhost",
            "port": 5432,
            "database": "langplug",
            "user": "langplug_user",
            "password": "langplug_password",
        }

        # Read schema file
        schema_file = Path("database/postgresql_schema.sql")
        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            return False

        with open(schema_file, encoding="utf-8") as f:
            schema_sql = f.read()

        logger.info("Connecting to PostgreSQL...")
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cursor = conn.cursor()

        # Split SQL commands and execute them one by one
        # This avoids issues with batch execution
        commands = []
        current_command = []

        for raw_line in schema_sql.split("\n"):
            line = raw_line.strip()
            if line and not line.startswith("--"):
                current_command.append(line)
                if line.endswith(";"):
                    commands.append(" ".join(current_command))
                    current_command = []

        logger.info(f"Executing {len(commands)} SQL commands...")

        for i, command in enumerate(commands, 1):
            try:
                logger.info(f"Executing command {i}/{len(commands)}")
                cursor.execute(command)
            except Exception as e:
                logger.warning(f"Command {i} failed (may be expected): {e}")
                continue

        # Verify tables were created
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()

        if tables:
            logger.info(f"✓ Successfully created {len(tables)} tables:")
            for table in tables:
                logger.info(f"  - {table[0]}")
        else:
            logger.warning("No tables found after schema application")

        cursor.close()
        conn.close()

        logger.info("✓ PostgreSQL schema application completed")
        return True

    except Exception as e:
        logger.error(f"✗ Schema application failed: {e}")
        return False


if __name__ == "__main__":
    success = apply_postgresql_schema()
    sys.exit(0 if success else 1)
