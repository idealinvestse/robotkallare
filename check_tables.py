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
    
    # Check Message table structure
    if any('message' in table[0].lower() for table in tables):
        result = conn.execute(text('PRAGMA table_info(message)'))
        columns = result.fetchall()
        print('Message table columns:', columns)
