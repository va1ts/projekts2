import logging
import threading
import time
from flask import Flask, render_template, redirect, url_for, request, flash, session
from api_handler import fetch_room_data
from hardware import turn_fan_on, turn_fan_off, initialize_fan
from auth import auth
from fan_handler import load_fan_assignments, save_fan_assignments, AVAILABLE_FAN_PINS
from flask import jsonify


app = Flask(__name__, static_folder='static')
app.secret_key = 'your_secret_key'
app.register_blueprint(auth)

fan_assignments = load_fan_assignments()
used_pins = {fan["pin"] for fan in fan_assignments}

automation_in_progress = {}

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/api/get_co2_levels')
def get_co2_levels():
    room_data = fetch_room_data() 
    co2_levels = []
    for room in room_data:
        co2_levels.append({
            "roomGroupName": room["roomGroupName"],
            "co2": room.get("co2", 0)
        })

    return jsonify(co2_levels)

@app.route('/graph/<room>')
def room_graph(room):
    if 'user' not in session:
        flash("Please log in to view the graph.", "warning")
        return redirect(url_for('auth.login'))

    room_data = fetch_room_data()
    device_id = None
    for r in room_data:
        if r.get('roomGroupName') == room:
            device_id = r.get('id')
            break
    if not device_id:
        flash("No graph available for this room.", "warning")
        return redirect(url_for('dashboard'))
    graph_url = f"https://co2.mesh.lv/home/device-charts/{device_id}"
    return render_template("graph.html", graph_url=graph_url, room=room)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        flash("Please log in to access the dashboard.", "warning")
        return redirect(url_for('auth.login'))  
    
    global fan_assignments
    fan_assignments = load_fan_assignments()  
    
    room_data = fetch_room_data()
    room_data.sort(key=lambda room: room['roomGroupName'])

    available_rooms = [
        room for room in room_data
        if not any(fan['room'] == room['roomGroupName'] for fan in fan_assignments)
    ]

    if request.method == 'POST':
        room_name = request.form.get('room')
        

        if 'assign_fan' in request.form:
            if any(fan['room'] == room_name for fan in fan_assignments):
                flash("Fan is already assigned to this room.", "warning")
            else:
                available_pin = next((p for p in AVAILABLE_FAN_PINS if p not in used_pins), None)
                if available_pin is None:
                    flash("No available fans left.", "danger")
                else:
                    used_pins.add(available_pin)
                    initialize_fan(available_pin)  
                    fan_assignments.append({'room': room_name, 'status': 'OFF', 'pin': available_pin})
                    save_fan_assignments(fan_assignments)
                    flash(f"Fan assigned to {room_name}.", "success")

        elif 'fan_control' in request.form:
            action = request.form['fan_control']

            for fan in fan_assignments:
                if fan['room'] == room_name:
                    if action == 'on':
                        turn_fan_on(fan["pin"]) 
                        fan['status'] = 'ON'
                    elif action == 'off':
                        turn_fan_off(fan["pin"])
                        fan['status'] = 'OFF'
                    save_fan_assignments(fan_assignments)

        
        elif 'remove_fan' in request.form:
            for fan in fan_assignments:
                if fan['room'] == room_name:
                    used_pins.discard(fan["pin"]) 
                    fan_assignments.remove(fan)
                    save_fan_assignments(fan_assignments) 
                    flash(f"Fan removed from {room_name}.", "info")
                    logging.info(f"Fan for room {room_name} removed.")
                    break

        return redirect(url_for('dashboard'))

    for fan in fan_assignments:
        for room in room_data:
            if room["roomGroupName"] == fan['room']:
                co2_level = room.get("co2", 0)
                if co2_level > 1000:
                    fan['co2_level'] = co2_level
                else:
                    fan['co2_level'] = co2_level

    return render_template('dashboard.html', rooms=available_rooms, fan_assignments=fan_assignments, room_data = room_data)

def automation_worker():
    """Background thread to automate fan control based on CO₂ levels."""
    while True:
        room_data = fetch_room_data()
        co2_lookup = {room["roomGroupName"]: room.get("co2", 0) for room in room_data}

        for fan in fan_assignments:
            room = fan['room']
            current_co2 = co2_lookup.get(room, 0)

            if not automation_in_progress.get(room, False):
                if current_co2 >= 1000:
                    logging.info(f"Automation triggered for {room} at CO₂ level: {current_co2} ppm")
                    automation_in_progress[room] = True
                    turn_fan_on(fan["pin"])
                    fan['status'] = 'ON'
                    save_fan_assignments(fan_assignments)  # Save the ON status
                    time.sleep(5)  
                    turn_fan_off(fan["pin"])
                    fan['status'] = 'OFF'
                    save_fan_assignments(fan_assignments)  # Save the OFF status
                    logging.info(f"Automation for {room} complete, fan turned off.")
                    automation_in_progress[room] = False
                    return

                else:
                    if fan['status'] == 'ON':
                        turn_fan_off(fan["pin"])
                        fan['status'] = 'OFF'
                        save_fan_assignments()

        time.sleep(10)
        save_fan_assignments(fan_assignments)

automation_thread = threading.Thread(target=automation_worker, daemon=True)
automation_thread.start()

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5002)