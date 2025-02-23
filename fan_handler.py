import csv
import logging
import os

FAN_ASSIGNMENTS_FILE = "fan_assignments.csv"
AVAILABLE_FAN_PINS = [17, 18, 23, 24, 25,] 

def load_fan_assignments():
    fan_assignments = []
    try:
        with open("fan_assignments.csv", "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                fan_assignments.append({
                    "room": row["room"],
                    "status": row["status"],
                    "pin": int(row["pin"])  
                })
    except FileNotFoundError:
        logging.warning("fan_assignments.csv not found. No fan assignments loaded.")
    return fan_assignments

def save_fan_assignments(fan_assignments):
    with open(FAN_ASSIGNMENTS_FILE, mode="w", newline="") as file:
        fieldnames = ["room", "status", "pin", "co2_level"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for fan in fan_assignments:
            writer.writerow(fan)

    logging.info("Fan assignments saved to CSV.")
