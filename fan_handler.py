import csv
import logging
import os

FAN_ASSIGNMENTS_FILE = "fan_assignments.csv"
AVAILABLE_FAN_PINS = [17, 18, 23, 24, 25,]  # List of GPIO pins for fans

def load_fan_assignments():
    fan_assignments = []
    try:
        with open("fan_assignments.csv", "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                fan_assignments.append({
                    "room": row["room"],
                    "status": row["status"],
                    "pin": int(row["pin"])  # Ensure the pin is treated as an integer
                })
    except FileNotFoundError:
        logging.warning("fan_assignments.csv not found. No fan assignments loaded.")
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
