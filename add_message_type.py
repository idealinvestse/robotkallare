import sqlite3
import os

# Path to the SQLite database
DB_PATH = "dialer.db"

def add_message_type_column():
    """Add message_type column to the message table with default value 'voice'"""
    print(f"Updating database at {DB_PATH}...")
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(message)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if "message_type" not in column_names:
            print("Adding message_type column to message table...")
            # Add the column with default value 'voice'
            cursor.execute("ALTER TABLE message ADD COLUMN message_type TEXT DEFAULT 'voice'")
            conn.commit()
            print("Column added successfully.")
        else:
            print("Column message_type already exists. No changes needed.")
        
        # Verify column was added
        cursor.execute("SELECT id, name, message_type FROM message LIMIT 5")
        messages = cursor.fetchall()
        print(f"Sample messages with message_type:")
        for msg in messages:
            print(f"  ID: {msg[0]}, Name: {msg[1]}, Type: {msg[2]}")
            
    except Exception as e:
        print(f"Error updating database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_message_type_column()