from datetime import datetime
import sqlite3
import logging

DB_FILE = 'airaware.db'

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def load_runtime_log():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Ensure the table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fan_runtime_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        
        cursor.execute('SELECT room, action, timestamp FROM fan_runtime_log')
        rows = cursor.fetchall()
        
        runtime_log = {}
        for row in rows:
            if row['room'] not in runtime_log:
                runtime_log[row['room']] = []
            runtime_log[row['room']].append({
                'action': row['action'],
                'timestamp': datetime.fromisoformat(row['timestamp'])
            })
        
        conn.close()
        return runtime_log
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return {}

def log_fan_action(room, action):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO fan_runtime_log (room, action, timestamp) VALUES (?, ?, ?)',
            (room, action, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logging.error(f"Error logging fan action: {e}")
        raise

def calculate_runtime_today(fan):
    runtime_log = load_runtime_log()
    if fan['room'] not in runtime_log:
        return 0
    
    today = datetime.now().date()
    events = runtime_log[fan['room']]
    total_runtime = 0
    last_on = None
    
    for event in events:
        if event['timestamp'].date() != today:
            continue
            
        if event['action'] == 'ON':
            last_on = event['timestamp']
        elif event['action'] == 'OFF' and last_on:
            runtime = (event['timestamp'] - last_on).total_seconds() / 3600
            total_runtime += runtime
            last_on = None
    
    if last_on and fan['status'] == 'ON':
        current_runtime = (datetime.now() - last_on).total_seconds() / 3600
        total_runtime += current_runtime
    
    return round(total_runtime, 1)

def calculate_total_runtime():
    runtime_log = load_runtime_log()
    total_hours = 0
    
    for room_events in runtime_log.values():
        last_on = None
        for event in room_events:
            if event['action'] == 'ON':
                last_on = event['timestamp']
            elif event['action'] == 'OFF' and last_on:
                runtime = (event['timestamp'] - last_on).total_seconds() / 3600
                total_hours += runtime
                last_on = None
    
    return round(total_hours, 1)

def get_last_active(fan):
    runtime_log = load_runtime_log()
    if fan['room'] not in runtime_log:
        return 'Never'
    
    events = runtime_log[fan['room']]
    if not events:
        return 'Never'
    
    last_event = max(events, key=lambda x: x['timestamp'])
    
    if fan['status'] == 'ON':
        return 'Current'
    
    delta = datetime.now() - last_event['timestamp']
    if delta.days > 0:
        return f"{delta.days}d ago"
    if delta.seconds // 3600 > 0:
        return f"{delta.seconds // 3600}h ago"
    return f"{delta.seconds // 60}m ago"

def calculate_efficiency(room_data, fan_data):
    if not fan_data:
        return 0
    
    high_co2_rooms = sum(1 for room in room_data if room.get('co2', 0) > 1000)
    active_fans = sum(1 for fan in fan_data if fan['status'] == 'ON')
    
    if high_co2_rooms == 0:
        return 100 if active_fans == 0 else 0
    
    efficiency = (active_fans / high_co2_rooms) * 100 if high_co2_rooms > 0 else 0
    return round(min(efficiency, 100), 1)

def calculate_co2_reduction(current_co2, fan):
    if fan['status'] == 'ON':
        target_co2 = 800  # Target CO2 level in ppm
        reduction = max(0, current_co2 - target_co2)
        return round(reduction)
    return 0