import logging
import threading
import time
from flask import Flask, render_template, redirect, url_for, request, flash, session
from api_handler import fetch_room_data
from hardware import turn_fan_on, turn_fan_off, initialize_fan
from auth import auth
from fan_handler import load_fan_assignments, save_fan_assignments, AVAILABLE_FAN_PINS
from flask import jsonify
from automation import automation_worker, manual_control



app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = 'your_secret_key'
app.register_blueprint(auth)

fan_assignments = load_fan_assignments()
used_pins = {fan["pin"] for fan in fan_assignments}

automation_in_progress = {}
fan_lock = threading.Lock()

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

@app.route('/api/fan_status')
def fan_status():
    global fan_assignments
    fan_assignments = load_fan_assignments()
    return jsonify(fan_assignments)

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
            action = request.form.get('fan_control')
            try:
                with fan_lock:
                    for fan in fan_assignments:
                        if fan['room'] == room_name:
                            if action == 'on':
                                turn_fan_on(fan["pin"])
                                fan['status'] = 'ON'
                            elif action == 'off':
                                turn_fan_off(fan["pin"])
                                fan['status'] = 'OFF'
                            save_fan_assignments(fan_assignments)
                            return jsonify({
                                "success": True,
                                "status": fan['status']
                            })
                    return jsonify({"success": False, "error": "Fan not found"})
            except Exception as e:
                logging.error(f"Error controlling fan: {e}")
                return jsonify({"success": False, "error": str(e)}), 500
        elif 'fan_control' in request.form:
            action = request.form.get('fan_control')
            try:
                with fan_lock:
                    for fan in fan_assignments:
                        if fan['room'] == room_name:
                            if action == 'on':
                                turn_fan_on(fan["pin"])
                                fan['status'] = 'ON'
                                manual_control[room_name] = True  # Mark as manually controlled
                            elif action == 'off':
                                turn_fan_off(fan["pin"])
                                fan['status'] = 'OFF'
                                manual_control.pop(room_name, None)  # Remove manual control tracking
                            save_fan_assignments(fan_assignments)
                            return jsonify({"success": True, "status": fan['status']})
                return jsonify({"success": False, "error": "Fan not found"})
            except Exception as e:
                logging.error(f"Error controlling fan: {e}")
                return jsonify({"success": False, "error": str(e)}), 500
            return redirect(url_for('dashboard'))

 # Update each fan with the latest CO2 level from room_data
    for fan in fan_assignments:
        for room in room_data:
            if room["roomGroupName"] == fan['room']:
                co2_level = room.get("co2", 0)
                fan['co2_level'] = co2_level

    return render_template('dashboard.html', rooms=available_rooms, fan_assignments=fan_assignments, room_data = room_data)

if __name__ == '__main__':
    automation_thread = threading.Thread(target=automation_worker, args=(fan_assignments, fan_lock), daemon=True)
    automation_thread.start()
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5002)