import logging
import atexit
from gpiozero import OutputDevice, GPIOZeroError

from config import FAN_PIN

# Initialize Fan Control
try:
    fan_device = OutputDevice(FAN_PIN, active_high=False)
    logging.info("Fan OutputDevice initialized successfully.")
except GPIOZeroError as e:
    logging.error(f"Failed to initialize fan OutputDevice: {e}")
    fan_device = None

# Cleanup Function
def cleanup_gpio():
    if fan_device:
        fan_device.close()
        logging.info("GPIO cleanup completed.")

# Register cleanup on exit
atexit.register(cleanup_gpio)

# Fan Control Functions
def turn_fan_on():
    if fan_device:
        fan_device.on()
        logging.info("Fan is ON")
    else:
        logging.warning("Fan device is not initialized.")

def turn_fan_off():
    if fan_device:
        fan_device.off()
        logging.info("Fan is OFF")
    else:
        logging.warning("Fan device is not initialized.")
