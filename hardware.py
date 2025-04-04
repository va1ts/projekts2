# filepath: /home/izm/testing/projekts2/hardware.py
import logging
import atexit
import time
from gpiozero import OutputDevice, GPIOZeroError

# Dictionary to store relay devices and their states
fan_devices = {}
fan_states = {}

def initialize_fan(pin):
    if pin not in fan_devices:
        try:
            fan_devices[pin] = OutputDevice(pin, active_high=False)  # Changed to True
            logging.info(f"Fan at GPIO {pin} initialized successfully.")
        except GPIOZeroError as e:
            logging.error(f"Failed to initialize fan at GPIO {pin}: {e}")

def turn_fan_on(pin):
    if pin not in fan_devices:
        logging.warning(f"Fan at GPIO {pin} is not initialized. Initializing now.")
        initialize_fan(pin)
    fan_devices[pin].on()
    logging.info(f"Fan at GPIO {pin} is ON.")

def turn_fan_off(pin):
    if pin not in fan_devices:
        logging.warning(f"Fan at GPIO {pin} is not initialized. Initializing now.")
        initialize_fan(pin)
    fan_devices[pin].off()
    logging.info(f"Fan at GPIO {pin} is OFF.")

def cleanup_gpio():
    for pin, device in fan_devices.items():
        device.close()
        logging.info(f"GPIO {pin} cleaned up.")
    fan_devices.clear()

atexit.register(cleanup_gpio)