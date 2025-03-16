import logging
import sqlite3

AVAILABLE_FAN_PINS = [18, 17, 23, 24, 25]
DB_FILE = 'airaware.db'

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def load_fan_assignments():
    logging.info("Loading fan assignments from database")
    fan_assignments = []
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT room, status, pin FROM fan_assignments')
        rows = cursor.fetchall()
        
        for row in rows:
            fan_assignments.append({
                'room': row['room'],
                'status': row['status'],
                'pin': row['pin']
            })
        conn.close()
        return fan_assignments
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return []

def vacuum_database():
    conn = None
    try:
        conn = get_db()
        conn.execute('VACUUM')
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error vacuuming database: {e}")
    finally:
        if conn:
            conn.close()

def save_fan_assignments(fan_assignments):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Begin transaction
        cursor.execute('BEGIN TRANSACTION')
        
        # Clear existing assignments
        cursor.execute('DELETE FROM fan_assignments')
        
        # Insert new assignments
        for fan in fan_assignments:
            cursor.execute(
                'INSERT INTO fan_assignments (room, status, pin) VALUES (?, ?, ?)',
                (fan['room'], fan['status'], fan['pin'])
            )
        
        # Verify the number of inserted rows
        cursor.execute('SELECT COUNT(*) FROM fan_assignments')
        count = cursor.fetchone()[0]
        if count != len(fan_assignments):
            raise sqlite3.Error(f"Database synchronization error: Expected {len(fan_assignments)} rows, got {count}")
            
        # Commit transaction
        conn.commit()
        logging.info(f"Successfully saved {count} fan assignments")
        
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        logging.error(f"Database error in save_fan_assignments: {e}")
        raise
    finally:
        if conn:
            conn.close()