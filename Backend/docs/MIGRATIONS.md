# LangPlug Backend - Database Migrations Guide

**Version**: 1.0
**Last Updated**: 2025-10-03

Complete guide for managing database migrations with Alembic.

---

## Table of Contents

1. [Overview](#overview)
2. [Migration Workflow](#migration-workflow)
3. [Creating Migrations](#creating-migrations)
4. [Applying Migrations](#applying-migrations)
5. [Rollback Procedures](#rollback-procedures)
6. [Testing Migrations](#testing-migrations)
7. [Production Deployment](#production-deployment)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### What are Migrations?

Database migrations are **version-controlled schema changes** that allow you to:
- Evolve database schema over time
- Apply changes consistently across environments
- Roll back problematic changes
- Track schema history

### Alembic

LangPlug uses **Alembic** for database migrations:
- Auto-generates migrations from SQLAlchemy models
- Supports upgrade and downgrade paths
- Works with SQLite and PostgreSQL
- Version control friendly (migrations are Python scripts)

### Migration Directory Structure

```
Backend/
└── alembic/
    ├── versions/                    # Migration scripts (version-controlled)
    │   ├── 879b4bfbd98e_initial_migration.py
    │   ├── 0b9cb76a1e84_migrate_to_lemma_based_vocabulary.py
    │   └── 10f18f66a1df_add_password_migration_tracking_column.py
    ├── env.py                       # Alembic environment configuration
    ├── script.py.mako              # Migration template
    └── alembic.ini                 # Alembic configuration (root directory)
```

---

## Migration Workflow

### Development Workflow

```
1. Modify SQLAlchemy Models
   └─► database/models.py

2. Generate Migration
   └─► alembic revision --autogenerate -m "Description"

3. Review Generated Migration
   └─► alembic/versions/xxxxx_description.py

4. Edit if Necessary
   └─► Add data migrations, custom logic

5. Test Migration
   └─► alembic upgrade head (dev database)
   └─► alembic downgrade -1 (test rollback)
   └─► Run tests

6. Commit Migration
   └─► git add alembic/versions/xxxxx_description.py
   └─► git commit -m "migration: description"

7. Deploy
   └─► alembic upgrade head (staging)
   └─► alembic upgrade head (production)
```

---

## Creating Migrations

### Prerequisites

Ensure virtual environment is activated and database is initialized:

```bash
# Activate virtual environment
source api_venv/bin/activate

# Verify current migration version
alembic current

# Should show current version or "No revision" if fresh database
```

### Auto-generating Migrations

**Step 1**: Modify SQLAlchemy models in `database/models.py`:

```python
# Example: Add new column to User model
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)

    # NEW COLUMN
    phone_number = Column(String, nullable=True)  # Add this
```

**Step 2**: Generate migration with descriptive message:

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "add phone number to user model"

# Output:
# Generating alembic/versions/abc123def456_add_phone_number_to_user_model.py ... done
```

**Step 3**: Review generated migration:

```bash
# Open the generated migration file
cat alembic/versions/abc123def456_add_phone_number_to_user_model.py
```

Example generated migration:

```python
"""add phone number to user model

Revision ID: abc123def456
Revises: previous_revision
Create Date: 2025-10-03 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'abc123def456'
down_revision = 'previous_revision'  # Points to previous migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema"""
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))


def downgrade() -> None:
    """Rollback database schema"""
    op.drop_column('users', 'phone_number')
```

### Manual Migrations (Complex Changes)

For complex changes, create empty migration and edit manually:

```bash
# Create empty migration
alembic revision -m "complex data migration"

# Edit the generated file
nano alembic/versions/xxxxx_complex_data_migration.py
```

Example manual migration (data transformation):

```python
"""complex data migration

Revision ID: def789ghi012
Revises: abc123def456
Create Date: 2025-10-03 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


revision = 'def789ghi012'
down_revision = 'abc123def456'


def upgrade() -> None:
    """Migrate old format to new format"""
    # Create temporary table reference
    vocabulary = table('vocabulary',
        column('id', sa.String),
        column('word', sa.String),
        column('lemma', sa.String)
    )

    # Data migration: populate lemma from word (if null)
    conn = op.get_bind()
    conn.execute(
        vocabulary.update()
        .where(vocabulary.c.lemma == None)
        .values(lemma=vocabulary.c.word.lower())
    )


def downgrade() -> None:
    """Reverse migration if possible"""
    # Some data migrations can't be reversed
    # Document this in comments
    pass
```

### Migration Best Practices

✅ **DO**:
- Write descriptive migration messages
- Review auto-generated migrations before applying
- Test upgrade AND downgrade
- Add comments for complex logic
- Keep migrations small and focused
- Commit migrations with code changes

❌ **DON'T**:
- Edit applied migrations (create new ones instead)
- Combine unrelated changes
- Skip testing migrations
- Assume auto-generation is perfect
- Delete old migrations
- Break backward compatibility without plan

---

## Applying Migrations

### Development Environment

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific number of migrations
alembic upgrade +2  # Apply next 2 migrations

# Apply to specific revision
alembic upgrade abc123def456

# Show SQL without applying (dry run)
alembic upgrade head --sql
```

### Check Migration Status

```bash
# Show current migration version
alembic current

# Expected output:
# abc123def456 (head)

# Show migration history
alembic history

# Expected output:
# abc123def456 -> def789ghi012 (head), add phone number
# previous_rev -> abc123def456, migrate vocabulary lemma
# <base> -> previous_rev, initial migration

# Show pending migrations
alembic heads

# Show detailed history
alembic history --verbose
```

---

## Rollback Procedures

### Rolling Back Migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade abc123def456

# Rollback all migrations (⚠️ DANGEROUS - destroys all data)
alembic downgrade base

# Show SQL for rollback (dry run)
alembic downgrade -1 --sql
```

### Emergency Rollback (Production)

If a migration causes production issues:

**Step 1**: Immediately roll back:

```bash
# Connect to production server
ssh production-server

# Activate environment
cd /app/backend
source venv/bin/activate

# Roll back problematic migration
alembic downgrade -1

# Verify application is working
curl http://localhost:8000/health
```

**Step 2**: Investigate and fix:

```bash
# Review migration that caused issue
cat alembic/versions/problematic_migration.py

# Fix the issue (create new migration with fix)
# DO NOT edit the problematic migration

# Test fix in staging
```

**Step 3**: Deploy fix:

```bash
# Create fixed migration
alembic revision --autogenerate -m "fix migration issue"

# Test in staging
alembic upgrade head

# Deploy to production
alembic upgrade head
```

---

## Testing Migrations

### Local Testing

```bash
# 1. Backup current database
cp data/langplug.db data/langplug.db.backup

# 2. Apply migration
alembic upgrade head

# 3. Run application tests
python -m pytest

# 4. Test rollback
alembic downgrade -1

# 5. Verify database state
sqlite3 data/langplug.db ".schema"

# 6. Re-apply if rollback worked
alembic upgrade head

# 7. If everything works, restore backup and re-apply fresh
rm data/langplug.db
mv data/langplug.db.backup data/langplug.db
alembic upgrade head
```

### Testing with PostgreSQL

```bash
# Start test PostgreSQL
docker compose -f docker-compose.postgresql.yml up -d db

# Apply migrations
USE_TEST_POSTGRES=1 \
DATABASE_URL="postgresql+asyncpg://langplug_user:langplug_password@localhost:5432/langplug" \
alembic upgrade head

# Run tests
USE_TEST_POSTGRES=1 \
TEST_POSTGRES_URL="postgresql+asyncpg://langplug_user:langplug_password@localhost:5432/langplug" \
python -m pytest

# Clean up
docker compose -f docker-compose.postgresql.yml down -v
```

### Migration Testing Checklist

Before deploying migration:

- [ ] Migration applies successfully (`alembic upgrade head`)
- [ ] Migration rolls back successfully (`alembic downgrade -1`)
- [ ] Application starts after migration
- [ ] All tests pass after migration
- [ ] No data loss during migration
- [ ] Performance is acceptable (large tables)
- [ ] Tested on both SQLite and PostgreSQL (if supporting both)
- [ ] Backward compatible (if zero-downtime deployment)

---

## Production Deployment

### Pre-deployment Checklist

- [ ] Migration tested in development
- [ ] Migration tested in staging (production-like environment)
- [ ] Database backup created
- [ ] Rollback plan documented
- [ ] Team notified (if downtime required)
- [ ] Monitoring ready (watch for errors)

### Zero-Downtime Migrations

For large production databases, use **expand-contract pattern**:

**Phase 1: Expand** (backward compatible)
```python
# Add new column (nullable, with default)
def upgrade():
    op.add_column('users', sa.Column('new_field', sa.String(), nullable=True, server_default='default'))
```

Deploy application code that writes to both old and new fields.

**Phase 2: Migrate Data**
```python
# Populate new field from old field
def upgrade():
    conn = op.get_bind()
    conn.execute(
        "UPDATE users SET new_field = old_field WHERE new_field IS NULL"
    )
```

**Phase 3: Contract** (remove old field)
```python
# Drop old column
def upgrade():
    op.drop_column('users', 'old_field')
```

Deploy application code that only uses new field.

### Production Deployment Commands

```bash
# 1. Connect to production
ssh production-server

# 2. Backup database (CRITICAL!)
pg_dump -U langplug_user langplug > backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Pull latest code
cd /app/backend
git pull origin main

# 4. Activate environment
source venv/bin/activate

# 5. Show pending migrations
alembic current
alembic heads

# 6. Apply migrations
alembic upgrade head

# 7. Restart application
systemctl restart langplug-backend

# 8. Verify health
curl http://localhost:8000/health

# 9. Monitor logs
tail -f logs/langplug.log
```

---

## Troubleshooting

### Issue: "Can't locate revision abc123def456"

**Cause**: Migration file missing or not in correct directory

**Solution**:
```bash
# Verify migration file exists
ls alembic/versions/abc123def456_*.py

# If missing, restore from git
git checkout main -- alembic/versions/abc123def456_*.py

# Re-run
alembic upgrade head
```

### Issue: "Multiple head revisions present"

**Cause**: Parallel development created branching migrations

**Solution**:
```bash
# List heads
alembic heads

# Merge migrations
alembic merge heads -m "merge migrations"

# This creates a merge migration
# Review and apply
alembic upgrade head
```

### Issue: Migration fails mid-execution

**Cause**: Syntax error, data issue, or constraint violation

**Solution**:
```bash
# 1. Check current migration state
alembic current

# 2. If partially applied, manually fix database or rollback
alembic downgrade -1

# 3. Fix migration script
nano alembic/versions/problematic_migration.py

# 4. Test migration
alembic upgrade head

# 5. If auto-generated migration is wrong, delete and recreate
rm alembic/versions/problematic_migration.py
alembic revision --autogenerate -m "fixed description"
```

### Issue: "Target database is not up to date"

**Cause**: Database version doesn't match migration history

**Solution**:
```bash
# Check database version
alembic current

# Check migration history
alembic history

# Stamp database to specific revision (if known correct state)
alembic stamp head  # ⚠️ Use with caution

# Or start fresh (DEVELOPMENT ONLY)
rm data/langplug.db
alembic upgrade head
```

### Issue: Slow migration on large table

**Cause**: Adding index or column to large table

**Solution**:
```python
# Use batch operations for large tables
def upgrade():
    with op.batch_alter_table('large_table') as batch_op:
        batch_op.add_column(sa.Column('new_field', sa.String()))
        batch_op.create_index('idx_new_field', ['new_field'])

# Or use concurrent index creation (PostgreSQL)
from alembic import op

def upgrade():
    op.create_index(
        'idx_new_field',
        'large_table',
        ['new_field'],
        postgresql_concurrently=True  # Don't lock table
    )

# Note: Concurrent creation requires connection not in transaction
# May need to adjust alembic/env.py
```

---

## Advanced Topics

### Custom Migration Scripts

For complex transformations, write custom Python:

```python
"""custom data transformation

Revision ID: xyz789abc012
"""
import csv
from alembic import op
from sqlalchemy.orm import Session


def upgrade():
    # Get database connection
    bind = op.get_bind()
    session = Session(bind=bind)

    # Example: Import data from CSV
    with open('/tmp/data.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            session.execute(
                "INSERT INTO vocabulary (word, lemma, level) VALUES (:word, :lemma, :level)",
                {
                    "word": row['word'],
                    "lemma": row['lemma'],
                    "level": row['level']
                }
            )

    session.commit()


def downgrade():
    # Reverse transformation
    bind = op.get_bind()
    session = Session(bind=bind)

    # Delete imported data
    session.execute("DELETE FROM vocabulary WHERE source = 'csv_import'")
    session.commit()
```

### Multi-database Migrations

If supporting multiple databases (SQLite + PostgreSQL):

```python
"""database-specific migration

Revision ID: multi123db456
"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    # Check database type
    bind = op.get_bind()

    if bind.dialect.name == 'sqlite':
        # SQLite-specific syntax
        op.execute('ALTER TABLE users ADD COLUMN new_field TEXT')
    elif bind.dialect.name == 'postgresql':
        # PostgreSQL-specific syntax
        op.add_column('users', sa.Column('new_field', sa.Text()))


def downgrade():
    op.drop_column('users', 'new_field')
```

---

## Related Documentation

- **[DEVELOPER_SETUP.md](DEVELOPER_SETUP.md)** - Database setup instructions
- **[CONFIGURATION.md](CONFIGURATION.md)** - Database configuration
- **[ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)** - System architecture
- **[Alembic Documentation](https://alembic.sqlalchemy.org/)** - Official docs

---

## Migration History

| Revision | Date | Description |
|----------|------|-------------|
| `879b4bfbd98e` | 2024-09-01 | Initial migration |
| `0b9cb76a1e84` | 2024-09-15 | Migrate to lemma-based vocabulary |
| `10f18f66a1df` | 2024-10-01 | Add password migration tracking |

**Current Version**: `10f18f66a1df` (as of 2025-10-03)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-03
**Maintained By**: Development Team
