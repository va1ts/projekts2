import logging
from flask import Flask, render_template, redirect, url_for, request, flash, session
from api_handler import fetch_room_data
from hardware import turn_fan_on, turn_fan_off
from auth import auth

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.register_blueprint(auth)

# Fan assignments
fan_assignments = []

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        flash("Please log in to access the dashboard.", "warning")
        return redirect(url_for('login'))
    
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

    return render_template('dashboard.html', rooms=available_rooms, fan_assignments=fan_assignments)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5001)
