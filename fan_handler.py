import logging
import sqlite3
import os

AVAILABLE_FAN_PINS = [23, 24, 25]
DB_FILE = os.path.abspath('airaware.db') 

def get_db():
    """Establish a connection to the database."""
    logging.debug(f"Connecting to database file: {os.path.abspath(DB_FILE)}")  # Log the absolute path
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def load_fan_assignments():
    """Load fan assignments from the database."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Ensure the table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fan_assignments (
                room TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                pin INTEGER NOT NULL
            )
        ''')
        
        cursor.execute("SELECT room, status, pin FROM fan_assignments")
        rows = cursor.fetchall()
        
        fan_assignments = [{'room': row['room'], 'status': row['status'], 'pin': row['pin']} for row in rows]
        return fan_assignments
    except sqlite3.Error as e:
        logging.error(f"Error loading fan assignments: {e}")
        return []
    finally:
        conn.close()  # Ensure the connection is always closed
        logging.info("Database connection closed.")

def save_fan_assignments(fan_assignments):
    """Save fan assignments to the database."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fan_assignments")
        for fan in fan_assignments:
            cursor.execute(
                "INSERT INTO fan_assignments (room, status, pin) VALUES (?, ?, ?)",
                (fan['room'], fan['status'], fan['pin'])
            )
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error saving fan assignments: {e}")