# PostgreSQL Migration Plan

## Overview

This document outlines the plan to migrate the LangPlug application from SQLite to PostgreSQL for production deployment. SQLite is not suitable for production web applications due to its limitations with concurrent access and scalability.

## Current State

- Database: SQLite
- Connection: Direct file-based access
- Session Storage: Database-backed (user_sessions table)
- Schema: Defined in `schema.sql`

## Target State

- Database: PostgreSQL
- Connection: Connection pooling via SQLAlchemy
- Session Storage: Database-backed (same user_sessions table)
- Schema: Migrated to PostgreSQL-compatible format

## Migration Steps

### 1. Environment Setup

- Install PostgreSQL server
- Create database and user for LangPlug
- Configure PostgreSQL settings for optimal performance

### 2. Schema Migration

- Convert SQLite schema to PostgreSQL-compatible format
- Handle data type differences:
  - SQLite `INTEGER` → PostgreSQL `SERIAL` for auto-incrementing IDs
  - SQLite `VARCHAR` → PostgreSQL `VARCHAR(n)` or `TEXT`
  - SQLite `TIMESTAMP` → PostgreSQL `TIMESTAMP`
- Update indexes and constraints for PostgreSQL syntax

### 3. Code Changes

- Update database connection strings
- Modify DatabaseManager to use PostgreSQL
- Update repository classes to work with PostgreSQL
- Test all database operations

### 4. Data Migration

- Export data from SQLite
- Transform data to match PostgreSQL schema
- Import data into PostgreSQL
- Validate data integrity

### 5. Testing

- Test all application features with PostgreSQL
- Performance testing under load
- Verify data consistency
- Test failover and recovery procedures

## Configuration Changes

### Environment Variables

```bash
# Current SQLite configuration
DATABASE_URL=sqlite:///./vocabulary.db

# New PostgreSQL configuration
DATABASE_URL=postgresql://username:password@localhost:5432/langplug
```

### Connection Pooling

```python
# Current SQLite connection
engine = create_engine("sqlite:///./vocabulary.db")

# New PostgreSQL connection with pooling
engine = create_engine(
    "postgresql://username:password@localhost:5432/langplug",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

## Required Dependencies

Add to `requirements.txt`:

```
psycopg2-binary>=2.9.0
```

## Docker Configuration

Update `docker-compose.yml` to include PostgreSQL service:

```yaml
version: "3.8"
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: langplug
      POSTGRES_USER: langplug_user
      POSTGRES_PASSWORD: langplug_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  app:
    build: .
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://langplug_user:langplug_password@db:5432/langplug

volumes:
  postgres_data:
```

## Migration Timeline

1. Week 1: Environment setup and schema conversion
2. Week 2: Code changes and testing
3. Week 3: Data migration and validation
4. Week 4: Performance testing and deployment

## Rollback Plan

- Maintain SQLite backup during migration
- Quick rollback procedure to SQLite if issues arise
- Monitor application performance post-migration
