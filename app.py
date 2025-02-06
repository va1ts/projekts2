import json
import sqlite3
import requests
import RPi.GPIO as GPIO
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database Setup
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS fan_assignments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        room TEXT UNIQUE NOT NULL,
                        status TEXT NOT NULL)''')
    conn.commit()
    conn.close()

init_db()  # Initialize database

# GPIO Setup
fan_pin = 18
#GPIO.setmode(GPIO.BCM)
#GPIO.setup(fan_pin, GPIO.OUT)

# Fetch room data
def fetch_room_data(building_id="512"):
    url = "https://co2.mesh.lv/api/device/list"
    payload = {"buildingId": building_id, "captchaToken": None}
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    response = requests.post(url, json=payload, headers=headers)
    return response.json() if response.status_code == 200 else []

# Database functions
def save_user(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def save_fan_assignment(room, status="OFF"):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO fan_assignments (room, status) VALUES (?, ?)", (room, status))
    conn.commit()
    conn.close()

def load_fan_assignments():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT room, status FROM fan_assignments")
    assignments = [{"room": row[0], "status": row[1]} for row in cursor.fetchall()]
    conn.close()
    return assignments

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'], method='sha256')
        try:
            save_user(username, password)
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists. Choose a different one."
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user(username)
        if user and check_password_hash(user[0], password):
            session['user'] = username
            return redirect(url_for('dashboard'))
        return "Invalid credentials, please try again."
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    room_data = fetch_room_data()
    room_data.sort(key=lambda room: room['roomGroupName'])
    fan_assignments = load_fan_assignments()
    available_rooms = [room for room in room_data if not any(fan['room'] == room['roomGroupName'] for fan in fan_assignments)]

    if request.method == 'POST':
        room_name = request.form['room']
        if any(fan['room'] == room_name for fan in fan_assignments):
            return render_template('dashboard.html', rooms=room_data, fan_assignments=fan_assignments, message="Fan is already assigned.")
        save_fan_assignment(room_name, 'OFF')
        fan_assignments = load_fan_assignments()
    
    for fan in fan_assignments:
        for room in room_data:
            if room["roomGroupName"] == fan['room']:
                fan_status = 'ON' if room.get("co2", 0) > 1000 else 'OFF'
                save_fan_assignment(fan['room'], fan_status)
    
    fan_assignments = load_fan_assignments()
    return render_template('dashboard.html', rooms=available_rooms, fan_assignments=fan_assignments, message=None)

if __name__ == '__main__':
    save_user('admin', generate_password_hash('123', method='sha256'))
    app.run(debug=True, host='0.0.0.0', port=5001)
