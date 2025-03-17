import sqlite3
import logging
from werkzeug.security import generate_password_hash

logging.basicConfig(level=logging.INFO)

def migrate_database():
    try:
        # Create new database
        conn = sqlite3.connect('airaware.db')
        cursor = conn.cursor()

        # Create tables
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS fan_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT NOT NULL,
            status TEXT NOT NULL,
            pin INTEGER NOT NULL
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS fan_runtime_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        ''')

        # Create default admin user
        default_password = generate_password_hash('admin123', method='sha256')
        cursor.execute('''
        INSERT INTO users (username, password, role) 
        VALUES (?, ?, ?)
        ''', ('admin', default_password, 'admin'))

        conn.commit()
        logging.info("Database migration completed successfully")
        
    except sqlite3.Error as e:
        logging.error(f"Database migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()