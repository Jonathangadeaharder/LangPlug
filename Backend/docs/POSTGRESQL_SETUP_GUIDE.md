# PostgreSQL Setup Guide for LangPlug Migration

## Overview

This guide provides multiple options for setting up PostgreSQL to complete the database migration from SQLite.

## Option 1: Local PostgreSQL Installation (Recommended)

### Windows Installation

1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. Run the installer and follow the setup wizard
3. Set a strong password for the `postgres` user
4. Note the port (default: 5432)
5. Complete the installation

### Post-Installation Setup

```sql
-- Connect to PostgreSQL as postgres user
psql -U postgres

-- Create database and user for LangPlug
CREATE DATABASE langplug;
CREATE USER langplug_user WITH ENCRYPTED PASSWORD 'langplug_password';
GRANT ALL PRIVILEGES ON DATABASE langplug TO langplug_user;
GRANT CREATE ON SCHEMA public TO langplug_user;
\q
```

### Environment Configuration

1. Copy `.env.postgresql` to `.env`
2. Update the PostgreSQL connection details:

```bash
LANGPLUG_DB_TYPE=postgresql
LANGPLUG_POSTGRES_HOST=localhost
LANGPLUG_POSTGRES_PORT=5432
LANGPLUG_POSTGRES_DB=langplug
LANGPLUG_POSTGRES_USER=langplug_user
LANGPLUG_POSTGRES_PASSWORD=langplug_password
```

## Option 2: Cloud PostgreSQL (Alternative)

### ElephantSQL (Free Tier)

1. Sign up at https://www.elephantsql.com/
2. Create a new PostgreSQL instance
3. Copy the connection details to `.env`

### Supabase (Free Tier)

1. Sign up at https://supabase.com/
2. Create a new project
3. Get the database URL from Project Settings > Database
4. Update `.env` with the connection string

## Option 3: Docker Alternative (If Docker becomes available)

```bash
# Start PostgreSQL container
docker-compose -f docker-compose.postgresql.yml up -d

# Check container status
docker-compose -f docker-compose.postgresql.yml ps
```

## Migration Steps

### 1. Verify PostgreSQL Connection

```bash
# Activate virtual environment
.\api_venv\Scripts\Activate.ps1

# Test PostgreSQL connection
python database/test_postgresql_migration.py
```

### 2. Create PostgreSQL Schema

```bash
# Apply PostgreSQL schema
psql -h localhost -U langplug_user -d langplug -f database/postgresql_schema.sql
```

### 3. Migrate Data from SQLite

```bash
# Run data migration script
python database/migrate_to_postgresql.py
```

### 4. Verify Migration Success

```bash
# Run comprehensive tests
python database/test_postgresql_migration.py
```

## Troubleshooting

### Connection Issues

- Verify PostgreSQL service is running
- Check firewall settings for port 5432
- Verify username/password combination
- Ensure database exists

### Permission Issues

```sql
-- Grant additional permissions if needed
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO langplug_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO langplug_user;
```

### SSL Issues

Add to `.env` if SSL is required:

```bash
LANGPLUG_POSTGRES_SSL_MODE=require
```

## Verification Checklist

- [ ] PostgreSQL installed and running
- [ ] Database and user created
- [ ] Environment variables configured
- [ ] Schema applied successfully
- [ ] Data migration completed
- [ ] All tests passing
- [ ] Application starts with PostgreSQL

## Rollback Plan

If issues occur, rollback to SQLite:

1. Change `.env`: `LANGPLUG_DB_TYPE=sqlite`
2. Restart the application
3. SQLite database will be used as fallback

## Performance Optimization

After successful migration:

1. Create indexes on frequently queried columns
2. Configure connection pooling parameters
3. Set up regular database maintenance tasks
4. Monitor query performance

## Next Steps

1. Choose your preferred PostgreSQL setup option
2. Follow the installation steps
3. Update environment configuration
4. Run migration and tests
5. Verify application functionality

Contact support if you encounter issues during migration.
