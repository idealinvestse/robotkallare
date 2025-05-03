import sqlite3
import uuid
from datetime import datetime

# Path to the SQLite database
DB_PATH = "dialer.db"

def create_sms_template():
    """Create a sample SMS message template in the database"""
    print(f"Connecting to database at {DB_PATH}...")
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if SMS template already exists
        cursor.execute("SELECT id FROM message WHERE name = 'Emergency SMS Alert'")
        existing = cursor.fetchone()
        
        if not existing:
            # Generate a new UUID
            message_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            # Create the SMS template
            cursor.execute("""
                INSERT INTO message (id, name, content, is_template, message_type, created_at, updated_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                message_id,
                "Emergency SMS Alert",
                "EMERGENCY ALERT: This is an important notification. Please check your email or voicemail for more details.",
                1,  # is_template = True
                "sms",  # message_type
                now,
                now
            ))
            conn.commit()
            print(f"Created new SMS message template with ID: {message_id}")
            
            # Create a "both" type template too
            message_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO message (id, name, content, is_template, message_type, created_at, updated_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                message_id,
                "Emergency Voice & SMS Alert",
                "This is an emergency alert. Please respond to confirm receipt of this message.",
                1,  # is_template = True
                "both",  # message_type
                now,
                now
            ))
            conn.commit()
            print(f"Created new combined voice & SMS message template with ID: {message_id}")
        else:
            print(f"SMS message template already exists with ID: {existing[0]}")
            
    except Exception as e:
        print(f"Error creating SMS template: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_sms_template()