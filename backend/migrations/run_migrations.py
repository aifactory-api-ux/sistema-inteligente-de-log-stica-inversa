# backend/migrations/run_migrations.py

"""
Database migration runner
Usage: python -m migrations.run_migrations [up|down]
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from config import settings


def get_engine():
    """Get database engine"""
    return create_engine(settings.DATABASE_URL)


def create_migrations_table(connection):
    """Create migrations tracking table if not exists"""
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(50) PRIMARY KEY,
            applied_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """))


def get_applied_migrations(connection):
    """Get list of applied migrations"""
    result = connection.execute(text("SELECT version FROM schema_migrations ORDER BY applied_at"))
    return [row[0] for row in result]


def mark_migration_applied(connection, version: str):
    """Mark migration as applied"""
    connection.execute(text("INSERT INTO schema_migrations (version) VALUES (:version)"), {"version": version})


def remove_migration_record(connection, version: str):
    """Remove migration record"""
    connection.execute(text("DELETE FROM schema_migrations WHERE version = :version"), {"version": version})


MIGRATIONS = [
    ("001_initial_schema", "Initial database schema"),
    ("002_seed_data", "Seed data for development"),
]


def upgrade():
    """Run all pending migrations"""
    engine = get_engine()
    with engine.connect() as connection:
        create_migrations_table(connection)
        applied = get_applied_migrations(connection)

        for version, description in MIGRATIONS:
            if version not in applied:
                print(f"Applying migration {version}: {description}...")
                try:
                    module = __import__(f"migrations.{version}", fromlist=["upgrade"])
                    module.upgrade(connection)
                    mark_migration_applied(connection, version)
                    connection.commit()
                    print(f"  ✓ Migration {version} applied successfully")
                except Exception as e:
                    connection.rollback()
                    print(f"  ✗ Migration {version} failed: {e}")
                    sys.exit(1)
            else:
                print(f"Skipping migration {version} (already applied)")


def downgrade():
    """Rollback migrations in reverse order"""
    engine = get_engine()
    with engine.connect() as connection:
        create_migrations_table(connection)
        applied = get_applied_migrations(connection)

        for version, description in reversed(MIGRATIONS):
            if version in applied:
                print(f"Rolling back migration {version}: {description}...")
                try:
                    module = __import__(f"migrations.{version}", fromlist=["downgrade"])
                    module.downgrade(connection)
                    remove_migration_record(connection, version)
                    connection.commit()
                    print(f"  ✓ Migration {version} rolled back successfully")
                except Exception as e:
                    connection.rollback()
                    print(f"  ✗ Rollback of {version} failed: {e}")
                    sys.exit(1)
            else:
                print(f"Skipping migration {version} (not applied)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m migrations.run_migrations [up|down]")
        sys.exit(1)

    command = sys.argv[1].lower()
    if command == "up":
        upgrade()
    elif command == "down":
        downgrade()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python -m migrations.run_migrations [up|down]")
        sys.exit(1)
