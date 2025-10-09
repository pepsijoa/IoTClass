# app.py
from flask import Flask, render_template, url_for, redirect, jsonify
import RPi.GPIO as GPIO
import threading
import time
import signal
import sys
import atexit
import adafruit_dht
import board

# GPIO 설정
GPIO.setmode(GPIO.BCM)
leds = [17, 22, 27]  # 17 -> Y 22 -> R 27 -> G
ledStates = [0, 0, 0]  

#LED GPIO 설정
GPIO.setup(leds[0], GPIO.OUT)
GPIO.setup(leds[1], GPIO.OUT)
GPIO.setup(leds[2], GPIO.OUT)


# 센서 관련 변수 및 함수
TRIG = 23 
ECHO = 24    
TOUCH_PIN = 25

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(TOUCH_PIN, GPIO.IN)

# 터치 센서 상태 관리
last_touch_state = 0
touch_detected = False


# 온습도 센서
dhtDevice = adafruit_dht.DHT11(board.D26)
def get_temperature():
    try:
        humidity = dhtDevice.humidity
        temperature = dhtDevice.temperature
        
        # 센서에서 None 값이 반환되는 경우 처리
        if humidity is not None and temperature is not None:
            return humidity, temperature
        else:
            return None, None
        time.sleep(1)
    except RuntimeError as error:
        print(f"DHT 센서 읽기 실패 (재시도 필요): {error.args[0]}")
        time.sleep(1)
        return None, None
    except Exception as e:
        print(f"DHT 센서 읽기 오류: {e}")
        time.sleep(1)
        return None, None

# GPIO 정리 함수
def cleanup_gpio():
    """GPIO 설정을 안전하게 정리하는 함수"""
    print("GPIO 정리 중...")
    # 모든 LED OFF
    for led_pin in leds:
        try:
            GPIO.output(led_pin, GPIO.LOW)
        except:
            pass
    
    # GPIO 정리
    try:
        GPIO.cleanup()
        print("GPIO 정리 완료")
    except Exception as e:
        print(f"GPIO 정리 중 오류: {e}")

# 시그널 핸들러 (Ctrl+C 등)
def signal_handler(sig, frame):
    print("\n프로그램 종료 신호 받음...")
    cleanup_gpio()
    sys.exit(0)

# 프로그램 종료 시 자동으로 GPIO 정리
atexit.register(cleanup_gpio)

def get_touch():
    global last_touch_state, touch_detected
    try:
        current_state = GPIO.input(TOUCH_PIN)
        
        # 상태 변화 감지 (rising edge detection)
        if current_state == 1 and last_touch_state == 0:
            touch_detected = True
            last_touch_state = current_state
            return True
        elif current_state == 0 and last_touch_state == 1:
            touch_detected = False
            last_touch_state = current_state
            return False
        
        last_touch_state = current_state
        return touch_detected
    except Exception as e:
        print(f"터치 센서 읽기 오류: {e}")
        return False


distance_cm = -1 # 현재 거리 값 (초기값 -1)
proximity_alert = False # 근접 알람 상태 (True: 알람, False: 정상)
ALERT_THRESHOLD = 20 # 근접 알람 기준 거리 (cm)

def get_distance():
    try:
        GPIO.output(TRIG, False)
        time.sleep(0.5)

        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)

        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()

        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()

        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150
        distance = round(distance, 1)

        return distance
    except Exception as e:
        print(f"거리 센서 읽기 오류: {e}")
        return -1


def DistanceMonitorTask():
    global distance_cm, proximity_alert
    while True:
        dist = get_distance()
        if dist != -1:
            distance_cm = dist
            if distance_cm <= ALERT_THRESHOLD:
                proximity_alert = True
                #print(f"!!! PROXIMITY ALERT: {distance_cm} cm !!!")
            else:
                proximity_alert = False
        else:
            distance_cm = -1
            proximity_alert = False
        time.sleep(0.5)


# Flask 애플리케이션 초기화
app = Flask(__name__, static_folder='static', static_url_path='/static')

def updateLeds():
    #print('Here is UpdateLEDs')
    try:
        for num, value in enumerate(ledStates):
            GPIO.output(leds[num], value)
    except Exception as e:
        print(f"LED 업데이트 오류: {e}")

counter = 0
def MultiTask():
    global counter
    while True:
        counter += 1
        time.sleep(1) # 1초마다 카운터 증가

# --- 라우트 정의 ---
@app.route('/')
def index():
    touch_status = get_touch()
    humidity, temperature = get_temperature()
    return render_template('index.html', 
                         ledStates=ledStates, 
                         distance=distance_cm, 
                         alert=proximity_alert,
                         touch_detected=touch_status,
                         temperature=temperature,
                         humidity=humidity)

@app.route('/<int:LEDn>/<int:state>')
def ledswitch(LEDn, state):
    if 0 <= LEDn < len(leds): # 유효한 LED 번호인지 확인
        ledStates[LEDn] = state
        updateLeds() # LED 상태 업데이트
    return redirect(url_for('index')) # 메인 페이지로 리다이렉트

@app.route('/getcounter')
def getcounter():
    return jsonify(value=counter)

@app.route('/getdistance')
def getdistance():
    if distance_cm == -1:
        return jsonify(value="Out of Range", alert=proximity_alert)
    else:
        return jsonify(value=distance_cm, alert=proximity_alert)

@app.route('/gettouch')
def gettouch():
    try:
        touch_status = get_touch()
        current_gpio_state = GPIO.input(TOUCH_PIN)
        return jsonify(touched=touch_status, current_state=current_gpio_state)
    except Exception as e:
        print(f"터치 상태 API 오류: {e}")
        return jsonify(touched=False, current_state=0, error="센서 읽기 오류")

@app.route('/gettemperature')
def gettemperature():
    try:
        humidity, temperature = get_temperature()
        if humidity is not None and temperature is not None:
            return jsonify(
                temperature=round(temperature, 1), 
                humidity=round(humidity, 1),
                status="success"
            )
        else:
            return jsonify(
                temperature=None, 
                humidity=None, 
                status="error", 
                message="센서 읽기 실패"
            )
    except Exception as e:
        print(f"온도/습도 API 오류: {e}")
        return jsonify(
            temperature=None, 
            humidity=None, 
            status="error", 
            message="센서 연결 오류"
        )

# --- 애플리케이션 실행 ---
if __name__ == '__main__':
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # 종료 신호
    
    try:
        # 백그라운드 스레드 시작
        threading.Thread(target=MultiTask, daemon=True).start()
        threading.Thread(target=DistanceMonitorTask, daemon=True).start()
        
        print("IoT 시스템 시작됨...")
        print("종료하려면 Ctrl+C를 누르세요")
        
        # Flask 앱 실행
        app.run(port=8080, host='0.0.0.0')
        
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt 감지됨")
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
    finally:
        cleanup_gpio()