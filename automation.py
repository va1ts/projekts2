import logging
import time
from hardware import turn_fan_on, turn_fan_off
from api_handler import fetch_room_data
from fan_handler import save_fan_assignments, load_fan_assignments

automation_in_progress = {}
manual_control = {}  # Track manually controlled fans


def automation_worker(fan_assignments, fan_lock):
    """Background thread to automate fan control based on CO₂ levels."""
    while True:
        try:
            current_assignments = load_fan_assignments()
            room_data = fetch_room_data()
            co2_lookup = {room["roomGroupName"]: room.get("co2", 0) for room in room_data}
            # Immediately check for removed fans
            with fan_lock:
                for room in list(automation_in_progress.keys()):
                    if not any(fan['room'] == room for fan in current_assignments):
                        if room in automation_in_progress:
                            del automation_in_progress[room]
                            logging.info(f"Automation stopped for removed fan in room {room}")
            

            
            # Create a set of rooms that currently have fans assigned
            assigned_rooms = {fan['room'] for fan in current_assignments}
            
            # Clean up automation_in_progress and shutdown removed fans
            removed_rooms = set(automation_in_progress.keys()) - assigned_rooms
            for room in removed_rooms:
                # Find the fan that was removed
                for fan in fan_assignments:
                    if fan['room'] == room:
                        with fan_lock:
                            # Ensure fan is turned off
                            turn_fan_off(fan["pin"])
                            fan['status'] = 'OFF'
                            save_fan_assignments(current_assignments)
                            logging.info(f"Fan for room {room} was removed, shutting down pin {fan['pin']}")
                del automation_in_progress[room]
            
            # Update fan_assignments with current state
            fan_assignments.clear()
            fan_assignments.extend(current_assignments)
            
            for fan in current_assignments:
                room = fan['room']
                current_co2 = co2_lookup.get(room, 0)

                if room in manual_control and manual_control[room]:  
                    # Skip automation if the fan was manually turned on
                    continue
                
                # Check if fan still exists in current assignments
                if not any(f['room'] == room for f in current_assignments):
                    continue
                
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
