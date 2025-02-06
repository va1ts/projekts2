from gpiozero import OutputDevice
import time

# Define the GPIO pin for the fan
FAN_PIN = 18

# Initialize the fan pin as an output device with inverted logic
fan = OutputDevice(FAN_PIN, active_high=False)

def turn_fan_on():
    fan.on()
    print("Fan is ON")
    print(f"Fan state: {fan.value}")

def turn_fan_off():
    fan.off()
    print("Fan is OFF")
    print(f"Fan state: {fan.value}")

def main():
    try:
        while True:
            user_input = input("Enter 'on' to turn the fan on, 'off' to turn the fan off, or 'exit' to quit: ").strip().lower()
            
            if user_input == 'on':
                turn_fan_on()
            elif user_input == 'off':
                turn_fan_off()
            elif user_input == 'exit':
                print("Exiting program")
                break
            else:
                print("Invalid input. Please enter 'on', 'off', or 'exit'.")
    except KeyboardInterrupt:
        print("\nExiting program")
    finally:
        fan.off()
        print("Fan is OFF")
        print(f"Fan state: {fan.value}")

if __name__ == "__main__":
    main()