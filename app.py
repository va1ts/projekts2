import logging
import threading
import time
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from api_handler import fetch_room_data_cached 
from hardware import turn_fan_on, turn_fan_off, initialize_fan
from auth import auth
from fan_handler import load_fan_assignments, save_fan_assignments, AVAILABLE_FAN_PINS
from automation import automation_worker, manual_control
from analytics_handler import (
    log_fan_action,
    calculate_total_runtime,
    calculate_runtime_today,
    get_last_active,
    load_runtime_log,
    calculate_efficiency,
    calculate_co2_reduction
)
import os

logging.basicConfig(level=logging.WARNING)
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = 'your_secret_key'
app.register_blueprint(auth)

# Add this after app initialization
DB_FILE = 'airaware.db'
if not os.path.exists(DB_FILE):
    from airaware import init_database
    init_database()

# Verify database is writable
if not os.access(DB_FILE, os.W_OK):
    logging.error(f"Database file {DB_FILE} is not writable!")
    raise PermissionError(f"Database file {DB_FILE} is not writable!")

fan_assignments = load_fan_assignments()
used_pins = {fan["pin"] for fan in fan_assignments}

automation_in_progress = {}
fan_lock = threading.Lock()

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route("/schedule")
def schedule():
    return render_template("schedule.html")

@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/alerts")
def alerts():
    return render_template("alerts.html")

@app.route('/api/available_rooms')
def available_rooms():
    room_data = fetch_room_data_cached()
    fan_assignments = load_fan_assignments()
    assigned_rooms = {fan['room'] for fan in fan_assignments}
    available = [room['roomGroupName'] for room in room_data if room['roomGroupName'] not in assigned_rooms]
    return jsonify(available)

@app.route('/api/get_co2_levels')
def get_co2_levels():
    room_data = fetch_room_data_cached()
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

    room_data = fetch_room_data_cached()
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

    if request.method == 'POST':
        if 'assign_fan' in request.form:
            room_name = request.form.get('room')
            if any(fan['room'] == room_name for fan in fan_assignments):
                return jsonify({'success': False, 'error': "Fan is already assigned to this room."})
            
            available_pin = next((p for p in AVAILABLE_FAN_PINS if p not in used_pins), None)
            if available_pin is None:
                return jsonify({'success': False, 'error': "No available fans left."})
            
            try:
                used_pins.add(available_pin)
                initialize_fan(available_pin)
                new_fan = {'room': room_name, 'status': 'OFF', 'pin': available_pin}
                fan_assignments.append(new_fan)
                save_fan_assignments(fan_assignments)
                
                return jsonify({
                    'success': True,
                    'message': f"Fan assigned to {room_name}.",
                    'fan': new_fan
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        elif 'fan_control' in request.form:
            room_name = request.form.get('room')
            action = request.form.get('fan_control')
            try:
                with fan_lock:
                    for fan in fan_assignments:
                        if fan['room'] == room_name:
                            if action == 'on':
                                turn_fan_on(fan["pin"])
                                fan['status'] = 'ON'
                                manual_control[room_name] = True
                                log_fan_action(room_name, 'ON')
                            elif action == 'off':
                                turn_fan_off(fan["pin"])
                                fan['status'] = 'OFF'
                                manual_control.pop(room_name, None)
                                log_fan_action(room_name, 'OFF')
                            save_fan_assignments(fan_assignments)
                            return jsonify({"success": True, "status": fan['status']})
                    return jsonify({"success": False, "error": "Fan not found"})
            except Exception as e:
                logging.error(f"Error controlling fan: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        elif 'remove_fan' in request.form:
            room_name = request.form.get('room')
            try:
                with fan_lock:
                    fan_to_remove = next((fan for fan in fan_assignments if fan['room'] == room_name), None)
                    if fan_to_remove:
                        if fan_to_remove['status'] == 'ON':
                            turn_fan_off(fan_to_remove["pin"])
                        fan_assignments.remove(fan_to_remove)
                        used_pins.discard(fan_to_remove["pin"])
                        save_fan_assignments(fan_assignments)
                        flash(f"Fan removed from {room_name}.", "success")
                        return jsonify({"success": True, "message": f"Fan removed from {room_name}"})
                    else:
                        return jsonify({"success": False, "error": "Fan not found"})
            except Exception as e:
                logging.error(f"Error removing fan: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

    room_data = fetch_room_data_cached()
    room_data.sort(key=lambda room: room['roomGroupName'])

    available_rooms = [
        room for room in room_data
        if not any(fan['room'] == room['roomGroupName'] for fan in fan_assignments)
    ]

    for fan in fan_assignments:
        for room in room_data:
            if room["roomGroupName"] == fan['room']:
                fan['co2_level'] = room.get("co2", 0)

    return render_template('dashboard.html', rooms=available_rooms, fan_assignments=fan_assignments, room_data=room_data)

@app.route('/analytics')
def analytics():
    if 'user' not in session:
        flash("Please log in to access analytics.", "warning")
        return redirect(url_for('auth.login'))
    
    fan_data = load_fan_assignments()
    room_data = fetch_room_data_cached()
    
    active_fans = sum(1 for fan in fan_data if fan['status'] == 'ON')
    
    analytics_data = {
        'totalRuntime': calculate_total_runtime(),
        'activeFans': f"{active_fans}/{len(fan_data)}",
        'efficiency': calculate_efficiency(room_data, fan_data),
        'fans': []
    }

    for fan in fan_data:
        room_co2 = next(
            (room['co2'] for room in room_data 
             if room['roomGroupName'] == fan['room']), 
            0
        )
        
        fan_info = {
            'room': fan['room'],
            'status': fan['status'],
            'runtimeToday': calculate_runtime_today(fan),
            'lastActive': get_last_active(fan),
            'co2Reduced': calculate_co2_reduction(room_co2, fan)
        }
        analytics_data['fans'].append(fan_info)
    
    return render_template('analytics.html', analytics=analytics_data)

# Add a new route for API updates
@app.route('/api/analytics')
def get_fan_analytics():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Same code as above but returns JSON
    fan_data = load_fan_assignments()
    room_data = fetch_room_data_cached()
    
    active_fans = sum(1 for fan in fan_data if fan['status'] == 'ON')
    
    analytics_data = {
        'totalRuntime': calculate_total_runtime(),
        'activeFans': f"{active_fans}/{len(fan_data)}",
        'efficiency': calculate_efficiency(room_data, fan_data),
        'fans': []
    }

    for fan in fan_data:
        room_co2 = next(
            (room['co2'] for room in room_data 
             if room['roomGroupName'] == fan['room']), 
            0
        )
        
        fan_info = {
            'room': fan['room'],
            'status': fan['status'],
            'runtimeToday': calculate_runtime_today(fan),
            'lastActive': get_last_active(fan),
            'co2Reduced': calculate_co2_reduction(room_co2, fan)
        }
        analytics_data['fans'].append(fan_info)
    
    return jsonify(analytics_data)

if __name__ == '__main__':
    automation_thread = threading.Thread(target=automation_worker, args=(fan_assignments, fan_lock), daemon=True)
    automation_thread.start()
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=5000)
