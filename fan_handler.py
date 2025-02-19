import csv
import logging
import os

FAN_ASSIGNMENTS_FILE = "fan_assignments.csv"
AVAILABLE_FAN_PINS = [18, 23, 24, 25]  # List of GPIO pins for fans

# Load existing fan assignments from CSV
def load_fan_assignments(file_path='fan_assignments.csv'):
    fan_assignments = []
    try:
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)  # Use DictReader to access columns by name
            for row in reader:
                # Ensure 'pin' exists in the row
                if 'pin' in row:
                    fan_assignments.append({"room": row["room"], "status": row["status"], "pin": int(row["pin"])})
                else:
                    logging.warning(f"Row skipped due to missing 'pin': {row}")
    except FileNotFoundError:
        logging.error(f"{file_path} not found.")
    except Exception as e:
        logging.error(f"Error loading fan assignments: {e}")
    
    return fan_assignments

# Save fan assignments to CSV
def save_fan_assignments(fan_assignments):
    with open(FAN_ASSIGNMENTS_FILE, mode="w", newline="") as file:
        fieldnames = ["room", "status", "pin"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for fan in fan_assignments:
            writer.writerow(fan)

    logging.info("Fan assignments saved to CSV.")
