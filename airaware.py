import sqlite3
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def init_database():
    try:
        conn = sqlite3.connect('airaware.db')
        cursor = conn.cursor()
        
        logging.info("Creating database tables...")
        
        # Create tables with improved schema
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_name TEXT UNIQUE NOT NULL,
            device_id TEXT UNIQUE NOT NULL,
            current_co2 INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS fans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pin INTEGER UNIQUE NOT NULL,
            room_id INTEGER,
            status TEXT DEFAULT 'OFF',
            last_status_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS fan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fan_id INTEGER,
            action TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            co2_level INTEGER,
            automated BOOLEAN DEFAULT 0,
            FOREIGN KEY (fan_id) REFERENCES fans(id)
        )
        ''')

        # Commit changes and close
        conn.commit()
        conn.close()
        logging.info("Database initialized successfully!")
        
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        raise
    except Exception as e:
        logging.error(f"Error: {e}")
        raise

if __name__ == '__main__':
    init_database()