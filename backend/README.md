# Disc Identification Backend

FastAPI backend for the disc golf disc identification system.

## Database Migrations

This project uses [Alembic](https://alembic.sqlalchemy.org/) for database migrations. Alembic tracks changes to your database schema over time and provides version control for your database structure.

### How to Create a New Migration File

When you need to modify the database schema (add tables, columns, indexes, etc.), create a new migration:

```bash
# Auto-generate migration from model changes (requires SQLAlchemy models)
alembic revision --autogenerate -m "add new column to discs table"

# Create empty migration file for manual edits
alembic revision -m "add custom index"
```

The migration file will be created in `alembic/versions/` with a unique revision ID.

### How to Execute Available Migrations

Apply pending migrations to update your database to the latest schema:

```bash
# Upgrade to the latest version
alembic upgrade head

# Upgrade to a specific revision
alembic upgrade <revision_id>

# Upgrade by relative steps
alembic upgrade +1  # Apply next migration
alembic upgrade +2  # Apply next two migrations
```

### How to Rollback Previously Executed Migration

Rollback database changes by downgrading to a previous version:

```bash
# Downgrade to previous version
alembic downgrade -1

# Downgrade to a specific revision
alembic downgrade <revision_id>

# Downgrade all the way to the beginning
alembic downgrade base
```

**Warning:** Downgrades may result in data loss depending on the migration operations.

### How to Check Current Migration Status

View the current state of migrations:

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show verbose history with details
alembic history --verbose

# Show all revisions and mark the current one
alembic history --indicate-current
```

### Migration Files

Migration files are stored in `alembic/versions/`. Each file contains:
- `upgrade()`: Function that applies the migration
- `downgrade()`: Function that reverts the migration
- Unique revision ID for tracking

### Configuration

- Database connection is configured via the `DATABASE_URL` environment variable
- Configuration is loaded from `app/disc_identification/config.py`
- Alembic settings are in `alembic.ini` and `alembic/env.py`
