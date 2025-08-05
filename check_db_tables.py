from tests.fixtures.database_test_fixtures import TestDatabaseManager
import logging
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
db = TestDatabaseManager()
engine = db.create_engine()

with engine.connect() as conn:
    result = conn.execute(text('SELECT name FROM sqlite_master WHERE type="table"'))
    tables = result.fetchall()
    print('Tables:', tables)
    print('Message tables:', [t for t in tables if 'message' in t[0].lower()])
