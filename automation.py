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
                if current_co2 >= 1000 and not automation_in_progress.get(room, False):
                    logging.info(f"CO2 high in {room}: {current_co2} ppm - Starting fan")
                    automation_in_progress[room] = True
                    with fan_lock:
                        turn_fan_on(fan["pin"])
                        fan['status'] = 'ON'
                        save_fan_assignments(current_assignments)
                elif current_co2 < 1000 and automation_in_progress.get(room, False):
                    logging.info(f"CO2 normal in {room}: {current_co2} ppm - Stopping fan")
                    automation_in_progress[room] = False
                    with fan_lock:
                        turn_fan_off(fan["pin"])
                        fan['status'] = 'OFF'
                        save_fan_assignments(current_assignments)
                
            time.sleep(10)  # Check every 10 seconds
        except Exception as e:
            logging.error(f"Error in automation worker: {e}")
            time.sleep(10)  # Wait before retrying