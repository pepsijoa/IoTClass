# app.py
from flask import Flask, render_template, redirect, jsonify
import mariadb
import threading
import time
import signal
import sys
import atexit

from config import DB_CONFIG, ALERT_THRESHOLD, SENSOR_POLL_INTERVAL
from sensor_utils import *

# LED GPIO
leds = [17, 22, 27]
ledStates = [0, 0, 0]
GPIO.setup(leds, GPIO.OUT)

distance_cm = -1
proximity_alert = False

def DistanceMonitorTask():
    global distance_cm, proximity_alert
    while True:
        dist = get_distance()
        distance_cm = dist
        if dist != -1:
            proximity_alert = dist <= ALERT_THRESHOLD
        else:
            proximity_alert = False
        time.sleep(0.5)

app = Flask(__name__)

def updateLeds():
    for num, value in enumerate(ledStates):
        GPIO.output(leds[num], value)

def cleanup_resources(led_pins):
    print("리소스 정리 시작...")
    for pin in led_pins:
        try:
            GPIO.output(pin, GPIO.LOW)
        except Exception as e:
            print(f"LED {pin} 정리 중 오류: {e}")
    cleanup_gpio()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history/<string:sensor_type>')
def history(sensor_type):
    if sensor_type == 'temperature':
        column, title, unit = 'temperature', '온도', '°C'
    elif sensor_type == 'humidity':
        column, title, unit = 'humidity', '습도', '%'
    elif sensor_type == 'distance':
        column, title, unit = 'distance', '주변 침입자 거리', 'cm'
    else:
        return "Not Found", 404
    
    conn = None
    cursor = None
    logs = []
    try:
        conn = mariadb.connect(**DB_CONFIG)
        cursor = conn.cursor()
        # 'log_time' 컬럼을 사용하도록 수정
        query = f"SELECT log_time, {column} FROM Controller3 WHERE {column} IS NOT NULL ORDER BY log_time DESC LIMIT 10"
        cursor.execute(query)
        logs = cursor.fetchall()
    except mariadb.Error as e:
        print(f"DB 조회 오류: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
        
    return render_template('history.html', logs=logs, title=title, unit=unit)

@app.route('/<int:LEDn>/<int:state>')
def ledswitch(LEDn, state):
    if 0 <= LEDn < len(leds):
        ledStates[LEDn] = state
        updateLeds()
    return redirect('/')

@app.route('/getdistance')
def getdistance_api():
    if distance_cm == -1:
        return jsonify(value="Out of Range", alert=proximity_alert)
    return jsonify(value=distance_cm, alert=proximity_alert)

@app.route('/gettouch')
def gettouch_api():
    touch_status = get_touch()
    return jsonify(touched=touch_status, current_state=GPIO.input(TOUCH_PIN))

@app.route('/gettemperature')
def gettemperature_api():
    humidity, temperature = get_temperature()   
    if humidity is not None and temperature is not None:
        return jsonify(temperature=round(temperature, 1), humidity=round(humidity, 1), status="success")
    return jsonify(status="error", message="센서 읽기 실패")
    
def signal_handler(sig, frame):
    print("\nCtrl+C 감지됨, 프로그램 종료.")
    sys.exit(0)

def save_to_db(temp, humid, dist, touch):
    conn = None
    cursor = None
    try:
        conn = mariadb.connect(**DB_CONFIG)
        cursor = conn.cursor()
        # [수정] 새 테이블 구조에 맞는 INSERT 쿼리
        query = """
            INSERT INTO Controller3 (temperature, humidity, distance, touch_detected)
            VALUES (?, ?, ?, ?)
        """
        dist_to_save = dist if dist != -1 and dist < 400 else None
        touch_to_save = 1 if touch else 0
        
        cursor.execute(query, (temp, humid, dist_to_save, touch_to_save))
        conn.commit()
        print(f"DB 저장 완료: Temp={temp}, Humid={humid}, Dist={dist_to_save}, Touch={touch}")
    except mariadb.Error as e:
        print(f"DB 저장 오류: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def LoggerTask():
    while True:
        humidity, temperature = get_temperature()
        distance = distance_cm 
        touch = get_touch()
        save_to_db(temperature, humidity, distance, touch)
        time.sleep(SENSOR_POLL_INTERVAL)
        
if __name__ == '__main__':
    atexit.register(cleanup_resources, led_pins=leds)
    signal.signal(signal.SIGINT, signal_handler)
    
    threading.Thread(target=DistanceMonitorTask, daemon=True).start()
    threading.Thread(target=LoggerTask, daemon=True).start()
    
    print("IoT 시스템 웹 서버 시작됨...")
    app.run(port=8080, host='0.0.0.0')

