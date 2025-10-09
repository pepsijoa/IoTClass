import RPi.GPIO as GPIO
import time

ledPin = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup(ledPin, GPIO.OUT, initial=GPIO.LOW)

try:
    while True:
        GPIO.output(ledPin, GPIO.HIGH)  # LED 켜기
        print("LED On")
        time.sleep(1)  # 1초 대기

        GPIO.output(ledPin, GPIO.LOW)   # LED 끄기
        print("LED Off")
        time.sleep(1)  # 1초 대기

except KeyboardInterrupt:
    print("\nProgram Terminated")

finally:
    GPIO.cleanup()
