import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Set test environment
os.environ.setdefault('ENV_FILE', '.env.test')

# Import and check settings
from app.config import get_settings
settings = get_settings()
print(f"Settings DATABASE_URL: {getattr(settings, 'DATABASE_URL', 'Not found')}")

# Import database module and check engine
from app.database import engine, create_db_and_tables
print(f"Database engine URL: {engine.url}")

# Check if tables exist
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT name FROM sqlite_master WHERE type="table"'))
    tables = result.fetchall()
    print('Tables in main engine:', tables)
    print('Message table exists:', any('message' in t[0].lower() for t in tables))

# Import models and check metadata
from sqlmodel import SQLModel
from app.models import Message
print(f"Message table name in metadata: {Message.__tablename__ if hasattr(Message, '__tablename__') else 'message'}")
print(f"Tables in SQLModel metadata: {list(SQLModel.metadata.tables.keys())}")

# Try to create tables
print("Creating tables...")
create_db_and_tables()
print("Tables created.")

# Check tables again
with engine.connect() as conn:
    result = conn.execute(text('SELECT name FROM sqlite_master WHERE type="table"'))
    tables = result.fetchall()
    print('Tables after creation:', tables)
    print('Message table exists after creation:', any('message' in t[0].lower() for t in tables))
