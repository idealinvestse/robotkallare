import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Set test environment
os.environ.setdefault('ENV_FILE', '.env.test')
os.environ.setdefault('ENVIRONMENT', 'testing')

print(f"ENV_FILE: {os.environ.get('ENV_FILE')}")
print(f"ENVIRONMENT: {os.environ.get('ENVIRONMENT')}")
print(f"DATABASE_URL from env: {os.environ.get('DATABASE_URL')}")

# Import and check settings
try:
    from app.config import get_settings
    settings = get_settings()
    print(f"Settings DATABASE_URL: {getattr(settings, 'DATABASE_URL', 'Not found')}")
except Exception as e:
    print(f"Settings loading error: {e}")

# Import database module and check engine
try:
    from app.database import engine, create_db_and_tables
    print(f"Database engine URL: {engine.url}")
    
    # Check if tables exist
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text('SELECT name FROM sqlite_master WHERE type="table"'))
        tables = result.fetchall()
        print('Tables in engine:', tables)
        print('Message table exists:', any('message' in t[0].lower() for t in tables))
except Exception as e:
    print(f"Database import error: {e}")

# Import models and check metadata
try:
    from sqlmodel import SQLModel
    from app.models import Message
    print(f"Message table name in metadata: {Message.__tablename__ if hasattr(Message, '__tablename__') else 'message'}")
    print(f"Tables in SQLModel metadata: {list(SQLModel.metadata.tables.keys())}")
except Exception as e:
    print(f"Model import error: {e}")
