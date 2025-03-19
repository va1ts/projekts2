import logging
import time
from hardware import turn_fan_on, turn_fan_off
from api_handler import fetch_room_data_cached  
from fan_handler import save_fan_assignments, load_fan_assignments

automation_in_progress = {}
manual_control = {}

def automation_worker(fan_assignments, fan_lock):
    """Background thread to automate fan control based on CO₂ levels."""
    while True:
        try:
            # Reload fan assignments and room data on each iteration
            current_assignments = load_fan_assignments()
            room_data = fetch_room_data_cached()
            
            # Create CO2 lookup dictionary
            co2_lookup = {
                room['roomGroupName']: room.get('co2', 0) 
                for room in room_data
            }
            
            for fan in current_assignments:
                room = fan['room']
                current_co2 = co2_lookup.get(room, 0)
                
                # Skip if under manual control
                if room in manual_control and manual_control[room]:
                    continue
                
                # Only act if CO2 crosses thresholds
                if current_co2 >= 1000:
                    if not automation_in_progress.get(room, False):
                        logging.info(f"CO2 high in {room}: {current_co2} ppm - Starting fan in {room}")
                        automation_in_progress[room] = True
                        with fan_lock:
                            turn_fan_on(fan["pin"])
                            # Update fan status directly in current_assignments
                            for f in current_assignments:
                                if f['room'] == room:
                                    f['status'] = 'ON'
                                    break  # Exit loop after updating the fan
                            save_fan_assignments(current_assignments)
                else:
                    if automation_in_progress.get(room, False):
                        logging.info(f"CO2 normal in {room}: {current_co2} ppm - Stopping fan in {room}")
                        automation_in_progress[room] = False
                        with fan_lock:
                            turn_fan_off(fan["pin"])
                            # Update fan status directly in current_assignments
                            for f in current_assignments:
                                if f['room'] == room:
                                    f['status'] = 'OFF'
                                    break  # Exit loop after updating the fan
                            save_fan_assignments(current_assignments)
                
            time.sleep(10)  # Check every 10 seconds
        except Exception as e:
            logging.error(f"Error in automation worker: {e}")
            time.sleep(10)  # Wait before retrying