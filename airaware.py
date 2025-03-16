import sqlite3
import csv
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def init_database():
    try:
        conn = sqlite3.connect('airaware.db')
        cursor = conn.cursor()
        
        logging.info("Creating database tables...")
        
        # Create tables
        cursor.execute('''
        CREATE TABLE users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE fan_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT NOT NULL,
            status TEXT NOT NULL,
            pin INTEGER NOT NULL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE fan_runtime_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp TEXT NOT NULL
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