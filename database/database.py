import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from .models import Base

# Local, SQLite database (Zero Cloud)
try:
    from core.config import DATABASE_URL as _cfg_url
    SQLALCHEMY_DATABASE_URL = _cfg_url
except ImportError:
    SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/db.sqlite")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _migrate_columns():
    """Add any missing columns to existing tables (lightweight auto-migration)."""
    inspector = inspect(engine)
    # Map of table_name -> list of (column_name, column_type_sql)
    migrations = {
        "clients": [
            ("surname", "VARCHAR"),
            ("address", "TEXT"),
        ],
        "draft_outputs": [
            ("rejected", "BOOLEAN DEFAULT 0"),
            ("rejected_at", "DATETIME"),
        ],
    }
    with engine.connect() as conn:
        for table, columns in migrations.items():
            if not inspector.has_table(table):
                continue
            existing = {col["name"] for col in inspector.get_columns(table)}
            for col_name, col_type in columns:
                if col_name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
        conn.commit()


def init_db():
    Base.metadata.create_all(bind=engine)
    _migrate_columns()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
