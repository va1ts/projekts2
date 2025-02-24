import csv
import logging

FAN_ASSIGNMENTS_FILE = "fan_assignments.csv"
AVAILABLE_FAN_PINS = [17, 18, 23, 24, 25]

def load_fan_assignments():
    fan_assignments = []
    try:
        with open(FAN_ASSIGNMENTS_FILE, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                fan_assignments.append({
                    "room": row["room"],
                    "status": row["status"],
                    "pin": int(row["pin"])
                })
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
