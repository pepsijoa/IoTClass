# sensor_utils.py
# 이 파일은 센서 하드웨어 제어에 필요한 모든 것을 포함합니다.
import RPi.GPIO as GPIO
import adafruit_dht
import board
import time
import threading

# 2. Setups
GPIO.setmode(GPIO.BCM)

# Sensor Pins
TRIG = 23
ECHO = 24
TOUCH_PIN = 25
DHT_PIN = board.D26

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(TOUCH_PIN, GPIO.IN)

# Sensor Objects
dhtDevice = adafruit_dht.DHT11(DHT_PIN)

# 여러 스레드에서 센서를 동시에 접근하는 것을 막기 위한 Lock
sensor_lock = threading.Lock()

# Touch Sensor State
last_touch_state = 0
touch_detected = False

distance_cm = -1
proximity_alert = False
ALERT_THRESHOLD = 10

# 3. sensor functions
def get_temperature():
    """온도와 습도를 읽어 반환합니다."""
    for attempt in range(3):
        try:
            with sensor_lock:
                humidity = dhtDevice.humidity
                temperature = dhtDevice.temperature
            if humidity is not None and temperature is not None:
                return humidity, temperature
            time.sleep(1)
        except RuntimeError as error:
            print(f"DHT 센서 읽기 실패 (시도 {attempt+1}/3): {error.args[0]}")
            time.sleep(1)
        except Exception as e:
            print(f"DHT 센서 읽기 오류 (시도 {attempt+1}/3): {e}")
            time.sleep(1)
    return None, None

def get_touch():
    """터치 센서의 상태를 감지하여 반환합니다."""
    global last_touch_state, touch_detected
    try:
        current_state = GPIO.input(TOUCH_PIN)
        if current_state == 1 and last_touch_state == 0:
            touch_detected = True
        elif current_state == 0 and last_touch_state == 1:
            touch_detected = False
        last_touch_state = current_state
        return touch_detected
    except Exception as e:
        print(f"터치 센서 읽기 오류: {e}")
        return False

def get_distance():
    """초음파 센서로 거리를 측정하여 반환합니다."""
    try:
        with sensor_lock:
            GPIO.output(TRIG, False)
            time.sleep(0.2)
            GPIO.output(TRIG, True)
            time.sleep(0.00001)
            GPIO.output(TRIG, False)

            pulse_start = time.time()
            pulse_end = time.time()
            timeout = pulse_start + 0.1

            while GPIO.input(ECHO) == 0 and pulse_start < timeout:
                pulse_start = time.time()

            while GPIO.input(ECHO) == 1 and pulse_end < timeout:
                pulse_end = time.time()

            pulse_duration = pulse_end - pulse_start
            distance = pulse_duration * 17150
            return round(distance, 1) if distance < 400 else -1
    except Exception as e:
        print(f"거리 센서 읽기 오류: {e}")
        return -1

def cleanup_gpio():
    """프로그램 종료 시 GPIO를 정리합니다."""
    print("GPIO 정리 중...")
    try:
        GPIO.cleanup()
        print("GPIO 정리 완료")
    except Exception as e:
        print(f"GPIO 정리 중 오류: {e}")
