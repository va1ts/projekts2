import json
import requests
import logging
import atexit
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from gpiozero import OutputDevice, GPIOZeroError, Device
from gpiozero.pins.rpigpio import RPiGPIOFactory
import RPi.GPIO as GPIO

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Logging configuration
logging.basicConfig(level=logging.DEBUG)

# Set the default pin factory to RPiGPIOFactory to avoid conflicts
Device.pin_factory = RPiGPIOFactory()

# GPIO Setup
FAN_PIN = 18
fan = None

# Function to handle GPIO cleanup
def cleanup_gpio():
    if fan:
        fan.close()
        logging.info("GPIO cleanup completed.")
    GPIO.cleanup()

# Ensure cleanup on exit
atexit.register(cleanup_gpio)

# Initialize the OutputDevice for the fan with error handling
try:
    fan = OutputDevice(FAN_PIN, active_high=False)  # Set active_high to False to invert logic
    logging.info("Fan initialized successfully.")
except GPIOZeroError as e:
    logging.error(f"Error initializing fan: {e}")
except Exception as e:
    logging.error(f"Unexpected error: {e}")

# Example user database (in-memory, for simplicity)
users = {}

# Fan assignments
fan_assignments = []

# This function fetches room data from the given API endpoint
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

# Function to handle fan activation
def activate_fan():
    if fan:
        fan.on()
        logging.info("Fan activated.")
    else:
        logging.warning("Fan initialization failed. Cannot activate fan.")

def deactivate_fan():
    if fan:
        fan.off()
        logging.info("Fan deactivated.")
    else:
        logging.warning("Fan initialization failed. Cannot deactivate fan.")

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')
        
        # Store the user in the in-memory database
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
        
        # Check if user exists and password matches
        if username in users and check_password_hash(users[username], password):
            session['user'] = username  # Store the username in the session
            flash("Login successful.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials, please try again.", "danger")
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

# Dashboard route (to show room data and control the fan)
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        flash("Please log in to access the dashboard.", "warning")
        return redirect(url_for('login'))
    
    room_data = fetch_room_data()

    # Sort rooms alphabetically by their name
    room_data.sort(key=lambda room: room['roomGroupName'])

    # Remove rooms that already have a fan assigned
    available_rooms = [room for room in room_data if not any(fan['room'] == room['roomGroupName'] for fan in fan_assignments)]

    if request.method == 'POST':
        if 'room' in request.form:
            room_name = request.form['room']
            
            # Check if the room already has a fan assigned
            if any(fan['room'] == room_name for fan in fan_assignments):
                flash("Fan is already assigned to this room.", "warning")
            else:
                # Add fan with default OFF status
                fan_assignments.append({'room': room_name, 'status': 'OFF'})
                flash("Fan assigned successfully.", "success")

        elif 'fan_control' in request.form:
            action = request.form['fan_control']
            room_name = request.form['room']
            for fan in fan_assignments:
                if fan['room'] == room_name:
                    if action == 'on':
                        activate_fan()
                        fan['status'] = 'ON'
                    elif action == 'off':
                        deactivate_fan()
                        fan['status'] = 'OFF'
                    flash(f"Fan for room {room_name} is now {fan['status']}.", "success")
                    break

        return redirect(url_for('dashboard'))

    # Check CO2 levels and update fan statuses based on the latest CO2 data
    for fan in fan_assignments:
        for room in room_data:
            if room["roomGroupName"] == fan['room']:
                # CO2 level check to update fan status
                if room.get("co2", 0) > 1000:
                    fan['status'] = 'ON'
                else:
                    fan['status'] = 'OFF'

    return render_template('dashboard.html', rooms=available_rooms, fan_assignments=fan_assignments)

# Run the Flask app
if __name__ == '__main__':
    users['admin'] = generate_password_hash('123', method='sha256')
    app.run(debug=True, host='0.0.0.0', port=5001)