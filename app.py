import json
import requests
import RPi.GPIO as GPIO
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/')
def home():
    return redirect(url_for('login'))  # Redirect to the login page initially


# GPIO Setup (assuming fan is connected to GPIO pin 17)
#GPIO.setmode(GPIO.BCM)
fan_pin = 18
#GPIO.setup(fan_pin, GPIO.OUT)

# Example user database (in-memory, for simplicity)
users = {}

# Change fan_assignments to be a list instead of a dictionary
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

    print(f"Response Status Code: {response.status_code}")  # Print status code


    # Check if the request was successful and attempt to parse JSON
    if response.status_code == 200:
        try:
            return response.json()  # Try to parse as JSON
        except ValueError as e:
            print(f"JSON decoding error: {e}")
            return []  # Return empty list if JSON parsing fails
    else:
        print(f"Request failed with status code {response.status_code}")
        return []  # Return empty list if the request failed

# Function to handle fan activation
def activate_fan():
    #GPIO.output(fan_pin, GPIO.HIGH)  # Turn on fan
    print("Fan activated.")

def deactivate_fan():
    #GPIO.output(fan_pin, GPIO.LOW)  # Turn off fan
    print("Fan deactivated.")

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')
        
        # Store the user in the in-memory database
        users[username] = hashed_password
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
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials, please try again."
    return render_template('login.html')

# Dashboard route (to show room data and control the fan)
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    room_data = fetch_room_data()

    # Sort rooms alphabetically by their name
    room_data.sort(key=lambda room: room['roomGroupName'])

    # Remove rooms that already have a fan assigned
    available_rooms = [room for room in room_data if not any(fan['room'] == room['roomGroupName'] for fan in fan_assignments)]

    # Add fan functionality
    if request.method == 'POST':
        room_name = request.form['room']
        
        # Check if the room already has a fan assigned
        if any(fan['room'] == room_name for fan in fan_assignments):
            message = "Fan is already assigned to this room."
            return render_template('dashboard.html', rooms=room_data, fan_assignments=fan_assignments, message=message)

        # Add fan with default OFF status
        fan_assignments.append({'room': room_name, 'status': 'OFF'})

        # Recheck CO2 levels and update fan status immediately after adding the fan
        for fan in fan_assignments:
            for room in room_data:
                if room["roomGroupName"] == fan['room']:
                    # CO2 level check to update fan status
                    if room.get("co2", 0) > 1000:
                        fan['status'] = 'ON'
                    else:
                        fan['status'] = 'OFF'

        return render_template('dashboard.html', rooms=room_data, fan_assignments=fan_assignments)

    # Check CO2 levels and update fan statuses based on the latest CO2 data
    for fan in fan_assignments:
        for room in room_data:
            if room["roomGroupName"] == fan['room']:
                # CO2 level check to update fan status
                if room.get("co2", 0) > 1000:
                    fan['status'] = 'ON'
                else:
                    fan['status'] = 'OFF'

    return render_template('dashboard.html', rooms=available_rooms, fan_assignments=fan_assignments, message=None)



# Run the Flask app
if __name__ == '__main__':
    users['admin'] = generate_password_hash('123', method='sha256')
    app.run(debug=True, host='0.0.0.0', port=5001)

#GPIO.cleanup()
# End of app.py