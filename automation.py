import logging
import time
from hardware import turn_fan_on, turn_fan_off
from api_handler import fetch_room_data
from fan_handler import save_fan_assignments, load_fan_assignments

automation_in_progress = {}

def automation_worker(fan_assignments, fan_lock):
    """Background thread to automate fan control based on CO₂ levels."""
    while True:
        try:
            # Load current fan assignments to get the latest state
            current_assignments = load_fan_assignments()
            room_data = fetch_room_data()
            co2_lookup = {room["roomGroupName"]: room.get("co2", 0) for room in room_data}
            
            # Create a set of rooms that currently have fans assigned
            assigned_rooms = {fan['room'] for fan in current_assignments}
            
            # Clean up automation_in_progress for removed fans
            removed_rooms = set(automation_in_progress.keys()) - assigned_rooms
            for room in removed_rooms:
                del automation_in_progress[room]
            
            for fan in current_assignments:
                room = fan['room']
                current_co2 = co2_lookup.get(room, 0)
                
                if not automation_in_progress.get(room, False):
                    if current_co2 >= 1000:
                        logging.info(f"Automation triggered for {room} at CO₂ level: {current_co2} ppm")
                        automation_in_progress[room] = True
                        with fan_lock:
                            # Check again if fan still exists before taking action
                            if any(f['room'] == room for f in load_fan_assignments()):
                                turn_fan_on(fan["pin"])
                                fan['status'] = 'ON'
                                save_fan_assignments(current_assignments)
                                
                                # Break the sleep into smaller intervals for responsiveness
                                for _ in range(5):
                                    if not any(f['room'] == room for f in load_fan_assignments()):
                                        break
                                    time.sleep(1)
                                
                                # Check one final time before turning off
                                if any(f['room'] == room for f in load_fan_assignments()):
                                    turn_fan_off(fan["pin"])
                                    fan['status'] = 'OFF'
                                    save_fan_assignments(current_assignments)
                                    logging.info(f"Automation for {room} complete, fan turned off.")
                            automation_in_progress[room] = False
                    else:
                        if fan['status'] == 'ON':
                            with fan_lock:
                                # Check if fan still exists before turning off
                                if any(f['room'] == room for f in load_fan_assignments()):
                                    turn_fan_off(fan["pin"])
                                    fan['status'] = 'OFF'
                                    save_fan_assignments(current_assignments)
            
            time.sleep(10)
        except Exception as e:
            logging.error(f"Error in automation worker: {e}")
            time.sleep(10)
