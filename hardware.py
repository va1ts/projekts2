import logging
import atexit
from gpiozero import OutputDevice, GPIOZeroError

fan_devices = {}

def initialize_fan(pin):
    """Initialize fan at a specific GPIO pin if not already initialized."""
    if pin not in fan_devices:
        try:
            fan_devices[pin] = OutputDevice(pin, active_high=False)
            logging.info(f"Fan at GPIO {pin} initialized successfully.")
        except GPIOZeroError as e:
            logging.error(f"Failed to initialize fan at GPIO {pin}: {e}")

def turn_fan_on(pin):
    """Turn on the fan at a specific pin."""
    if pin not in fan_devices:
        logging.warning(f"Fan at GPIO {pin} is not initialized. Initializing now.")
        initialize_fan(pin)  # Ensure the fan is initialized before use
    fan_devices[pin].on()
    logging.info(f"Fan at GPIO {pin} is ON.")

def turn_fan_off(pin):
    """Turn off the fan at a specific pin."""
    if pin not in fan_devices:
        logging.warning(f"Fan at GPIO {pin} is not initialized. Initializing now.")
        initialize_fan(pin)
    fan_devices[pin].off()
    logging.info(f"Fan at GPIO {pin} is OFF.")

def cleanup_gpio():
    """Cleanup all initialized fans."""
    for pin, device in fan_devices.items():
        device.close()
        logging.info(f"GPIO {pin} cleaned up.")
    fan_devices.clear()

# Register cleanup on exit
atexit.register(cleanup_gpio)