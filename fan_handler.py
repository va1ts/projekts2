import csv
import logging
import os

FAN_ASSIGNMENTS_FILE = "fan_assignments.csv"
AVAILABLE_FAN_PINS = [18, 17, 23, 24, 25]

def load_fan_assignments():
    fan_assignments = []
    try:
        if os.path.exists(FAN_ASSIGNMENTS_FILE) and os.path.getsize(FAN_ASSIGNMENTS_FILE) > 0:
            with open(FAN_ASSIGNMENTS_FILE, "r") as file:
                # Skip empty lines and ensure headers are read correctly
                reader = csv.DictReader((line for line in file if line.strip()))
                for row in reader:
                    try:
                        fan_assignments.append({
                            "room": str(row.get("room", "")),
                            "status": str(row.get("status", "OFF")),
                            "pin": int(row.get("pin", 0))
                        })
                    except (ValueError, KeyError) as e:
                        logging.error(f"Error reading row {row}: {e}")
                        continue
    except FileNotFoundError:
        logging.warning(f"{FAN_ASSIGNMENTS_FILE} not found. No fan assignments loaded.")
    return fan_assignments

def save_fan_assignments(fan_assignments):
    try:
        with open(FAN_ASSIGNMENTS_FILE, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['room', 'status', 'pin'])
            writer.writeheader()
            writer.writerows(fan_assignments)
    except Exception as e:
        logging.error(f"Error saving fan assignments: {e}")
        raise