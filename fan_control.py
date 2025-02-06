import RPi.GPIO as GPIO
import time

# Define the GPIO pin for the fan
FAN_PIN = 18

# Set up GPIO using BCM numbering
GPIO.setmode(GPIO.BCM)
GPIO.setup(FAN_PIN, GPIO.OUT)

def turn_fan_on():
    GPIO.output(FAN_PIN, GPIO.HIGH)
    print("Fan is ON")

def turn_fan_off():
    GPIO.output(FAN_PIN, GPIO.LOW)
    print("Fan is OFF")

def main():
    while True:
        user_input = input("Enter 'on' to turn the fan on, 'off' to turn the fan off, or 'exit' to quit: ").strip().lower()
        
        if user_input == 'on':
            turn_fan_on()
        elif user_input == 'off':
            turn_fan_off()
        elif user_input == 'exit':
            GPIO.cleanup()
            print("Exiting program")
            break
        else:
            print("Invalid input. Please enter 'on', 'off', or 'exit'.")

if __name__ == "__main__":
    main()