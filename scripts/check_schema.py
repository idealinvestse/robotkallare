#!/usr/bin/env python3
"""Check database schema."""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_schema():
    """Check and print database schema."""
    conn = sqlite3.connect('gdial.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("=== DATABASE TABLES ===")
    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print("  Columns:")
        for col in columns:
            print(f"    - {col[1]} ({col[2]})")
    
    conn.close()

if __name__ == "__main__":
    check_schema()
