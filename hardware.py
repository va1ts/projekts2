import logging
import atexit
from gpiozero import OutputDevice, GPIOZeroError

# Dictionary to store relay devices and their states
fan_devices = {}
fan_states = {}

def initialize_fan(pin, initial_state=False):
    """
    Initialize a relay for a specific pin with a given initial state
    Args:
        pin (int): GPIO pin number
        initial_state (bool): True for ON, False for OFF
    """
    if pin not in fan_devices:
        try:
            relay = OutputDevice(pin)
            fan_devices[pin] = relay
            fan_states[pin] = initial_state
            
            # Force initial state
            if initial_state:
                relay.on()
            else:
                relay.off()
            
            logging.info(f"Relay at GPIO {pin} initialized and set to {'ON' if initial_state else 'OFF'}")
        except GPIOZeroError as e:
            logging.error(f"Failed to initialize relay at GPIO {pin}: {e}")
            raise

def turn_fan_on(pin):
    """Turn on the relay for a specific pin"""
    if pin not in fan_devices:
        initialize_fan(pin)
    try:
        # Simple on command like in test_fan.py
        fan_devices[pin].on()
        fan_states[pin] = True
        logging.info(f"Relay at GPIO {pin} turned ON")
    except Exception as e:
        logging.error(f"Error turning on relay at GPIO {pin}: {e}")
        raise

# Update the turn_fan_off function
def turn_fan_off(pin):
    """Turn off the relay for a specific pin"""
    if pin not in fan_devices:
        initialize_fan(pin)
    try:
        # Force the OFF state
        relay = fan_devices[pin]
        relay.off()
        fan_states[pin] = False
        logging.info(f"Relay at GPIO {pin} turned OFF")
    except Exception as e:
        logging.error(f"Error turning off relay at GPIO {pin}: {e}")
        raise

def cleanup_gpio():
    """Clean up all GPIO resources"""
    for pin, device in fan_devices.items():
        try:
            device.off()
            device.close()
            logging.info(f"GPIO {pin} cleaned up")
        except Exception as e:
            logging.error(f"Error cleaning up GPIO {pin}: {e}")
    fan_devices.clear()
    fan_states.clear()

# Register cleanup handler
atexit.register(cleanup_gpio)