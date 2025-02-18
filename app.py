import json
import os
import csv
import requests
import logging
import atexit
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from gpiozero import OutputDevice, GPIOZeroError
import RPi.GPIO as GPIO

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Logging configuration
logging.basicConfig(level=logging.DEBUG)

FAN_PIN = 18

CSV_FILE = 'fan_assignments.csv'

# Initialize the OutputDevice for the fan
try:
    fan_device = OutputDevice(FAN_PIN, active_high=False)
    logging.info("Fan OutputDevice initialized successfully.")
except GPIOZeroError as e:
    logging.error(f"Failed to initialize fan OutputDevice: {e}")

# Function to handle GPIO cleanup
def cleanup_gpio():
    if fan_device:
        fan_device.close()
        logging.info("GPIO cleanup completed.")

    
if fan_device:
    fan_device.on()
# Ensure cleanup on exit
atexit.register(cleanup_gpio)

def load_fan_assignments():
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='r') as file:
            reader = csv.DictReader(file)
            return [row for row in reader]
    return []

def save_fan_assignments():
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["room", "status"])
        writer.writeheader()
        for fan in fan_assignments:
            writer.writerow(fan)

# Example user database (in-memory, for simplicity)
users = {}

# Fan assignments
fan_assignments = []

# Fetch room data from the API endpoint
def fetch_room_data(building_id="512"):
    url = "https://co2.mesh.lv/api/device/list"  # Correct API endpoint
    payload = {
        "buildingId": building_id,
        "captchaToken": None
    }

    headers = {
        'Content-Type': 'application/json',  # Ensure correct content type
        'Accept': 'application/json',  # Accept JSON response
        'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',  # Optional: user-agent to match browser
    }

    # Make a POST request with the payload and headers
    response = requests.post(url, json=payload, headers=headers)

    logging.info(f"Response Status Code: {response.status_code}")  # Log status code

    # Check if the request was successful and attempt to parse JSON
    if response.status_code == 200:
        try:
            return response.json()  # Try to parse as JSON
        except ValueError as e:
            logging.error(f"JSON decoding error: {e}")
            return []  # Return empty list if JSON parsing fails
    else:
        logging.error(f"Request failed with status code {response.status_code}")
        return []  # Return empty list if the request failed

# Functions to handle fan activation
def turn_fan_on():
    if fan_device:
        fan_device.on()
        logging.info("Fan is ON")
        print("Fan is ON")
    else:
        logging.warning("Fan device is not initialized. Cannot turn fan ON.")

def turn_fan_off():
    if fan_device:
        fan_device.off()
        logging.info("Fan is OFF")
        print("Fan is OFF")
    else:
        logging.warning("Fan device is not initialized. Cannot turn fan OFF.")

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')
        
        if username in users:
            flash("Username already exists. Please choose a different one.", "warning")
            return redirect(url_for('register'))

        users[username] = hashed_password
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users and check_password_hash(users[username], password):
            session['user'] = username
            flash("Login successful.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials, please try again.", "danger")
    return render_template('login.html')

# Root route
@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

# Logout route
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

# Dashboard route
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        flash("Please log in to access the dashboard.", "warning")
        return redirect(url_for('login'))
    

    fan_assignments = load_fan_assignments()

    room_data = fetch_room_data()
    room_data.sort(key=lambda room: room['roomGroupName'])

    # Remove rooms that already have a fan assigned
    available_rooms = [
        room for room in room_data
        if not any(fan['room'] == room['roomGroupName'] for fan in fan_assignments)
    ]

    if request.method == 'POST':
        if 'assign_fan' in request.form:
            # Assign fan to room
            room_name = request.form['room']
            if any(fan['room'] == room_name for fan in fan_assignments):
                flash("Fan is already assigned to this room.", "warning")
            else:
                fan_assignments.append({'room': room_name, 'status': 'OFF'})
                flash(f"Fan assigned to room {room_name}.", "success")
                logging.info(f"Fan assigned to room {room_name}.")
        elif 'fan_control' in request.form:
            # Control fan (turn on/off)
            action = request.form['fan_control']
            room_name = request.form['room']

            for fan in fan_assignments:
                if fan['room'] == room_name:
                    if action == 'on':
                        turn_fan_on()
                        fan['status'] = 'ON'
                    elif action == 'off':
                        turn_fan_off()
                        fan['status'] = 'OFF'
                    save_fan_assignments()  # Save to CSV
                    flash(f"Fan for room {room_name} is now {fan['status']}.", "success")
                    logging.info(f"Fan for room {room_name} set to {fan['status']}.")
                    break

        return redirect(url_for('dashboard'))

    # Update fan statuses based on CO2 levels
    for fan in fan_assignments:
        for room in room_data:
            if room["roomGroupName"] == fan['room']:
                if room.get("co2", 0) > 1000:
                    fan['status'] = 'ON'
                else:
                    fan['status'] = 'OFF'

    save_fan_assignments()  # Save updated fan statuses to CSV  

    return render_template('dashboard.html', rooms=available_rooms, fan_assignments=fan_assignments)

# Run the Flask app
if __name__ == '__main__':
    # Initialize admin user
    users['admin'] = generate_password_hash('123', method='sha256')
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5002)
