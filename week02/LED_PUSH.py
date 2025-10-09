import RPi.GPIO as GPIO
import time

ledPin = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup(ledPin, GPIO.OUT, initial=GPIO.LOW)

try:
    while True:
        GPIO.output(ledPin, GPIO.HIGH)  # LED 켜기

except KeyboardInterrupt:
    print("\nProgram Terminated")

finally:
    GPIO.cleanup()
