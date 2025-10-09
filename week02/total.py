import RPi.GPIO as GPIO
import time
import board
import adafruit_dht

# --- GPIO 핀 번호 설정 ---
# LED 핀
led_R = 16  # 빨강
led_Y = 20  # 노랑
led_G = 21  # 초록
INPUT_PIN = 17  # 버튼 핀

# 센서 핀
trig_pin = 23       # 초음파 Trig
echo_pin = 24       # 초음파 Echo
dht_pin = board.D4  # 온습도 센서 (BCM 4번)

# --- GPIO 설정 ---
GPIO.setmode(GPIO.BCM)
GPIO.setup([led_R, led_Y, led_G], GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(INPUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(trig_pin, GPIO.OUT)
GPIO.setup(echo_pin, GPIO.IN)

# --- 온습도 센서 초기화 ---
dht_device = adafruit_dht.DHT11(dht_pin)

# --- 함수 정의 ---
def get_distance():
    """초음파 센서로 거리를 측정하는 함수"""
    GPIO.output(trig_pin, False)
    time.sleep(0.2)
    GPIO.output(trig_pin, True)
    time.sleep(0.00001)
    GPIO.output(trig_pin, False)

    while GPIO.input(echo_pin) == 0:
        pulse_start = time.time()
    while GPIO.input(echo_pin) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = round(pulse_duration * 17150, 1)
    return distance


def control_led(distance):
    """거리에 따라 LED를 제어하는 함수"""
    if 0 < distance <= 10:
        GPIO.output(led_R, GPIO.HIGH)
        GPIO.output(led_Y, GPIO.LOW)
        GPIO.output(led_G, GPIO.LOW)
        print(f"거리는 {distance}cm 입니다. 너무 가깝습니다. (빨간색 LED ON)")
    elif 10 < distance <= 20:
        GPIO.output(led_R, GPIO.LOW)
        GPIO.output(led_Y, GPIO.HIGH)
        GPIO.output(led_G, GPIO.LOW)
        print(f"거리는 {distance}cm 입니다. (노란색 LED ON)")
    else:
        GPIO.output(led_R, GPIO.LOW)
        GPIO.output(led_Y, GPIO.LOW)
        GPIO.output(led_G, GPIO.HIGH)
        print(f"거리는 {distance}cm 입니다. (초록색 LED ON)")


# --- 메인 코드 ---
print("시스템이 대기 상태입니다. 버튼을 눌러 시작하세요.")

is_on = False

try:
    while True:
        if GPIO.input(INPUT_PIN) == GPIO.HIGH:
            print("\n>> 시스템 작동 시작합니다.")
            is_on = True
        if is_on == True:
            try:
                # 온습도 측정
                temperature = dht_device.temperature
                humidity = dht_device.humidity
                if temperature is not None and humidity is not None:
                    print(f"온도는 {temperature:.1f}도, 습도는 {humidity}% 입니다.")
                else:
                    print("온습도 센서 값을 읽을 수 없습니다.")
            except RuntimeError:
                print("온습도 센서 읽기 오류. 재시도합니다.")
                time.sleep(1)
                continue

            # 거리 측정 및 LED 제어
            distance = get_distance()
            control_led(distance)

            print("-" * 30)
            time.sleep(1)

        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n>> 시스템 작동을 종료합니다.")
    GPIO.output([led_R, led_Y, led_G], GPIO.LOW)  # 모든 LED 끄기

finally:
    print("GPIO 설정을 초기화합니다.")
    GPIO.cleanup()
