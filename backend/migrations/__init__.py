# backend/migrations/__init__.py

"""
Database migrations package for Sistema Inteligente de Logística Inversa
"""

MIGRATIONS = [
    ("001_initial_schema", "Initial database schema"),
    ("002_seed_data", "Seed data for development"),
]


def run_migrations(direction: str = "up"):
    """
    Run database migrations

    Args:
        direction: "up" to apply, "down" to rollback
    """
    from migrations.run_migrations import upgrade, downgrade

    if direction == "up":
        upgrade()
    elif direction == "down":
        downgrade()
    else:
        raise ValueError(f"Invalid direction: {direction}. Use 'up' or 'down'.")
