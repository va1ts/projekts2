import logging
import time
from hardware import turn_fan_on, turn_fan_off
from api_handler import fetch_room_data_cached  # Use cached API call
from fan_handler import save_fan_assignments, load_fan_assignments

automation_in_progress = {}
manual_control = {}  # Track manually controlled fans

def automation_worker(fan_assignments, fan_lock):
    """Background thread to automate fan control based on CO₂ levels."""
    while True:
        try:
            current_assignments = load_fan_assignments()
            room_data = fetch_room_data_cached()
            co2_lookup = {room["roomGroupName"]: room.get("co2", 0) for room in room_data}
            
            # Check for removed fans
            with fan_lock:
                for room in list(automation_in_progress.keys()):
                    if not any(fan['room'] == room for fan in current_assignments):
                        del automation_in_progress[room]
                        logging.info(f"Automation stopped for removed fan in room {room}")
            
            assigned_rooms = {fan['room'] for fan in current_assignments}

            # Shutdown removed fans
            removed_rooms = set(automation_in_progress.keys()) - assigned_rooms
            for room in removed_rooms:
                for fan in fan_assignments:
                    if fan['room'] == room:
                        with fan_lock:
                            turn_fan_off(fan["pin"])
                            fan['status'] = 'OFF'
                            save_fan_assignments(current_assignments)
                            logging.info(f"Fan for room {room} was removed, shutting down pin {fan['pin']}")
                del automation_in_progress[room]

            # Update assignments
            fan_assignments.clear()
            fan_assignments.extend(current_assignments)

            for fan in current_assignments:
                room = fan['room']
                current_co2 = co2_lookup.get(room, 0)

                if room in manual_control and manual_control[room]:
                    continue  # Skip automation if manually controlled
                
                if not automation_in_progress.get(room, False):
                    if current_co2 >= 1000:
                        logging.info(f"Turning ON fan in {room} due to high CO₂: {current_co2} ppm")
                        automation_in_progress[room] = True
                        with fan_lock:
                            if any(f['room'] == room for f in load_fan_assignments()):
                                turn_fan_on(fan["pin"])
                                fan['status'] = 'ON'
                                save_fan_assignments(current_assignments)
                else:
                    if current_co2 < 1000:
                        logging.info(f"Turning OFF fan in {room}, CO₂ is now {current_co2} ppm")
                        automation_in_progress[room] = False
                        with fan_lock:
                            if any(f['room'] == room for f in load_fan_assignments()):
                                turn_fan_off(fan["pin"])
                                fan['status'] = 'OFF'
                                save_fan_assignments(current_assignments)

            time.sleep(10)
        except Exception as e:
            logging.error(f"Error in automation worker: {e}")
            time.sleep(10)