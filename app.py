import logging
from flask import Flask, render_template, redirect, url_for, request, flash, session
from api_handler import fetch_room_data
from hardware import turn_fan_on, turn_fan_off, initialize_fan
from auth import auth
from fan_handler import load_fan_assignments, save_fan_assignments, AVAILABLE_FAN_PINS

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.register_blueprint(auth)

# Load fan assignments on startup
fan_assignments = load_fan_assignments()
used_pins = {fan["pin"] for fan in fan_assignments}  # Track used GPIO pins

# Fan assignments
fan_assignments = []

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/graph/<room>')
def room_graph(room):
    # Ensure user is logged in
    if 'user' not in session:
        flash("Please log in to view the graph.", "warning")
        return redirect(url_for('auth.login'))

    # Fetch the latest room data
    room_data = fetch_room_data()

    # Look for the room using the roomGroupName (adjust if your API uses a different key)
    device_id = None
    for r in room_data:
        if r.get('roomGroupName') == room:
            # Assuming the API returns a field 'id' that corresponds to the device ID
            device_id = r.get('id')
            break

    if not device_id:
        flash("No graph available for this room.", "warning")
        return redirect(url_for('dashboard'))

    # Construct the URL for the external graph
    graph_url = f"https://co2.mesh.lv/home/device-charts/{device_id}"

    return render_template("graph.html", graph_url=graph_url, room=room)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        flash("Please log in to access the dashboard.", "warning")
        return redirect(url_for('auth.login'))  # Fixed incorrect redirect
    
    global fan_assignments
    fan_assignments = load_fan_assignments()  # Load shared fan data
    
    room_data = fetch_room_data()
    room_data.sort(key=lambda room: room['roomGroupName'])

    # Remove rooms that already have a fan assigned
    available_rooms = [
        room for room in room_data
        if not any(fan['room'] == room['roomGroupName'] for fan in fan_assignments)
    ]

    if request.method == 'POST':
        room_name = request.form.get('room')
        

        if 'assign_fan' in request.form:
            # Ensure the room does not already have a fan
            if any(fan['room'] == room_name for fan in fan_assignments):
                flash("Fan is already assigned to this room.", "warning")
            else:
                # Assign an available GPIO pin
                available_pin = next((p for p in AVAILABLE_FAN_PINS if p not in used_pins), None)
                if available_pin is None:
                    flash("No available fans left.", "danger")
                else:
                    used_pins.add(available_pin)
                    initialize_fan(available_pin)  # Initialize fan
                    fan_assignments.append({'room': room_name, 'status': 'OFF', 'pin': available_pin})
                    save_fan_assignments(fan_assignments)
                    flash(f"Fan assigned to {room_name}.", "success")

        elif 'fan_control' in request.form:
            # Control fan (turn on/off)
            action = request.form['fan_control']

            for fan in fan_assignments:
                if fan['room'] == room_name:
                    if action == 'on':
                        turn_fan_on(fan["pin"])  # Now controls the correct fan
                        fan['status'] = 'ON'
                    elif action == 'off':
                        turn_fan_off(fan["pin"])
                        fan['status'] = 'OFF'
                    save_fan_assignments(fan_assignments)
                    flash(f"Fan for room {room_name} is now {fan['status']}.", "success")
                    logging.info(f"Fan for room {room_name} set to {fan['status']}.")
                    break
        
        elif 'remove_fan' in request.form:
            # Remove fan assignment
            for fan in fan_assignments:
                if fan['room'] == room_name:
                    used_pins.discard(fan["pin"])  # Free up the GPIO pin
                    fan_assignments.remove(fan)  # Remove from list
                    save_fan_assignments(fan_assignments)  # Save changes
                    flash(f"Fan removed from {room_name}.", "info")
                    logging.info(f"Fan for room {room_name} removed.")
                    break

        return redirect(url_for('dashboard'))

    # Update fan statuses based on CO2 levels and custom messages
    for fan in fan_assignments:
        for room in room_data:
            if room["roomGroupName"] == fan['room']:
                co2_level = room.get("co2", 0)
                if co2_level > 1000:
                    fan['co2_level'] = co2_level
                    fan['message'] = "Fan is ON because CO2 level is above 1000ppm."
                else:
                    fan['co2_level'] = co2_level
                    fan['message'] = "Fan is not needed as CO2 level is below 1000ppm."

    return render_template('dashboard.html', rooms=available_rooms, fan_assignments=fan_assignments)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5002)
