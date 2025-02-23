import logging
import time
from hardware import turn_fan_on, turn_fan_off
from api_handler import fetch_room_data
from fan_handler import save_fan_assignments, load_fan_assignments

automation_in_progress = {}

def automation_worker(fan_assignments, fan_lock):
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
                    with fan_lock:
                        turn_fan_on(fan["pin"])
                        fan['status'] = 'ON'
                        save_fan_assignments(fan_assignments)
                    # Break the sleep into smaller intervals for responsiveness
                    for _ in range(5):
                        time.sleep(1)
                    with fan_lock:
                        turn_fan_off(fan["pin"])
                        fan['status'] = 'OFF'
                        save_fan_assignments(fan_assignments)
                    logging.info(f"Automation for {room} complete, fan turned off.")
                    automation_in_progress[room] = False
                else:
                    if fan['status'] == 'ON':
                        with fan_lock:
                            turn_fan_off(fan["pin"])
                            fan['status'] = 'OFF'
                            save_fan_assignments(fan_assignments)
        time.sleep(10)
        with fan_lock:
            save_fan_assignments(fan_assignments)
