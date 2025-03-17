import logging
import sqlite3

AVAILABLE_FAN_PINS = [18, 17, 23, 24, 25]
DB_FILE = 'airaware.db'

def get_db():
    """Establish a connection to the database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def load_fan_assignments():
    """Load fan assignments from the database."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT room, status, pin FROM fan_assignments")
        rows = cursor.fetchall()
        
        fan_assignments = [{'room': row['room'], 'status': row['status'], 'pin': row['pin']} for row in rows]
        conn.close()
        return fan_assignments
    except sqlite3.Error as e:
        logging.error(f"Error loading fan assignments: {e}")
        return []

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
        conn.close()
    except sqlite3.Error as e:
        logging.error(f"Error saving fan assignments: {e}")