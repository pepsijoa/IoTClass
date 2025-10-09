import time
import threading
from flask import Flask, render_template, jsonify
import mariadb  # MariaDB 라이브러리
from datetime import datetime
import RPi.GPIO as GPIO

# DHT11 센서 관련 모듈 import (예외 처리)
DHT_AVAILABLE = False
dht = None
try:
    import board
    import adafruit_dht
    dht = adafruit_dht.DHT11(board.D26)  # GPIO 26번 핀
    DHT_AVAILABLE = True
    print("DHT11 sensor initialized successfully.")
except ImportError as e:
    print(f"DHT11 libraries not available: {e}")
    print("Using mock sensor data.")
except Exception as e:
    print(f"DHT11 initialization failed: {e}")
    print("Using mock sensor data.")

DB_CONFIG = {
    'host': 'localhost',
    'user': 'jyw',
    'password': 'yewon',
    'database': 'IOT'
}

LED_AIRCON_PIN = 17       # 에어컨 (LED 1)
LED_HEATER_PIN = 22       # 히터 (LED 2)
LED_DEHUMIDIFIER_PIN = 27 # 제습기 (LED 3)

ULTRASONIC_TRIG_PIN = 23 # 초음파 센서 Trig
ULTRASONIC_ECHO_PIN = 24 # 초음파 센서 Echo

TOUCH_SENSOR_PIN = 25     # 터치 센서

# 현실적인 초기값으로 설정 (일반적인 실내 환경)
sensor_data = {"temperature": 22.0, "humidity": 50.0, "distance": 100.0}
sensor_data_initialized = False  # 실제 센서에서 데이터를 읽었는지 확인하는 플래그
system_status = {"mode": "AUTO", "devices": {"aircon": "OFF", "heater": "OFF", "dehumidifier": "OFF"}}
previous_touch_state = 0
GPIO_AVAILABLE = False
app = Flask(__name__)



def setup_gpio():
    global GPIO_AVAILABLE
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(LED_AIRCON_PIN, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(LED_HEATER_PIN, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(LED_DEHUMIDIFIER_PIN, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(ULTRASONIC_TRIG_PIN, GPIO.OUT)
        GPIO.setup(ULTRASONIC_ECHO_PIN, GPIO.IN)
        GPIO.setup(TOUCH_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO_AVAILABLE = True
        print("GPIO setup completed.")
        return True
    except Exception as e:
        GPIO_AVAILABLE = False
        print(f"GPIO setup failed: {e}")
        return False

def control_led(pin, state):
    if not GPIO_AVAILABLE:
        return
    try:
        if state == "ON": GPIO.output(pin, GPIO.HIGH)
        else: GPIO.output(pin, GPIO.LOW)
    except Exception as e:
        print(f"LED control error: {e}")

def measure_distance():
    if not GPIO_AVAILABLE:
        # 모의 거리 데이터 반환
        import random
        return 50 + random.uniform(-30, 50)
    
    try:
        GPIO.output(ULTRASONIC_TRIG_PIN, True)
        time.sleep(0.00001)
        GPIO.output(ULTRASONIC_TRIG_PIN, False)
        
        # 타임아웃을 위한 시작 시간
        timeout_start = time.time()
        start_time = time.time()
        
        # Echo 핀이 HIGH가 될 때까지 대기 (타임아웃 1초)
        while GPIO.input(ULTRASONIC_ECHO_PIN) == 0:
            start_time = time.time()
            if time.time() - timeout_start > 1.0:
                return 999.0
        
        # Echo 핀이 LOW가 될 때까지 대기 (타임아웃 1초)
        timeout_start = time.time()
        stop_time = time.time()
        while GPIO.input(ULTRASONIC_ECHO_PIN) == 1:
            stop_time = time.time()
            if time.time() - timeout_start > 1.0:
                return 999.0
        
        distance = ((stop_time - start_time) * 34300) / 2
        return distance
    except Exception as e:
        print(f"Distance measurement error: {e}")
        return 999.0

# --- 데이터베이스 초기화 함수 ---
def init_db():
    try:
        conn = mariadb.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS readings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sensor_type VARCHAR(50) NOT NULL,
                value FLOAT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
        print("MariaDB database initialized.")
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        exit()

# --- Auto 모드 제어 로직 ---
def auto_control_logic():
    global sensor_data_initialized
    
    # 실제 센서 데이터를 읽기 전에는 제어하지 않음
    if not sensor_data_initialized:
        print("Waiting for real sensor data before auto control...")
        return
    
    # 센서 데이터 가져오기
    temp = sensor_data["temperature"]
    humidity = sensor_data["humidity"]
    
    # 온도 기반 기기 제어 (온도가 유효한 경우에만)
    if -10.0 <= temp <= 50.0:
        # 에어컨 제어
        new_aircon_state = "ON" if temp >= 28.0 else "OFF"
        if system_status["devices"]["aircon"] != new_aircon_state:
            system_status["devices"]["aircon"] = new_aircon_state
            control_led(LED_AIRCON_PIN, new_aircon_state)
            print(f"Aircon {new_aircon_state} (temp: {temp}°C)")
        
        # 히터 제어
        new_heater_state = "ON" if temp <= 15.0 else "OFF"
        if system_status["devices"]["heater"] != new_heater_state:
            system_status["devices"]["heater"] = new_heater_state
            control_led(LED_HEATER_PIN, new_heater_state)
            print(f"Heater {new_heater_state} (temp: {temp}°C)")
    else:
        print(f"Invalid temperature reading: {temp}°C. Skipping temperature-based control.")
    
    # 습도 기반 기기 제어 (습도가 유효한 경우에만)
    if 0.0 <= humidity <= 100.0:
        # 제습기 제어
        new_dehumidifier_state = "ON" if humidity >= 60.0 else "OFF"
        if system_status["devices"]["dehumidifier"] != new_dehumidifier_state:
            system_status["devices"]["dehumidifier"] = new_dehumidifier_state
            control_led(LED_DEHUMIDIFIER_PIN, new_dehumidifier_state)
            print(f"Dehumidifier {new_dehumidifier_state} (humidity: {humidity}%)")
    else:
        print(f"Invalid humidity reading: {humidity}%. Skipping humidity-based control.")

# --- 백그라운드 스레드: 실제 하드웨어 데이터 수집 및 DB 저장 ---
def update_hardware_data():
    global previous_touch_state, sensor_data_initialized
    while True:
        # 1. DHT11 센서에서 온도와 습도를 개별적으로 읽기 시도
        temperature = None
        humidity = None
        
        if DHT_AVAILABLE and dht is not None:
            try:
                # DHT11에서 데이터 읽기
                temp_read = dht.temperature
                hum_read = dht.humidity
                print(f"[DEBUG] Raw DHT11 read: Temp={temp_read}, Hum={hum_read}")
                # 온도 유효성 개별 검증
                if temp_read is not None and -10.0 <= temp_read <= 50.0:
                    temperature = temp_read
                else:
                    print(f"Invalid temperature reading: {temp_read}")
                # 습도 유효성 개별 검증  
                if hum_read is not None and 0.0 <= hum_read <= 100.0:
                    humidity = hum_read
                else:
                    print(f"Invalid humidity reading: {hum_read}")
            except RuntimeError as e:
                print(f"DHT11 read error: {e}")
            except Exception as e:
                print(f"DHT11 unexpected error: {e}")
        
        # 거리 센서 읽기
        distance = measure_distance()

        # 2. MariaDB에 데이터 저장 및 sensor_data 업데이트
        try:
            conn = mariadb.connect(**DB_CONFIG)
            cursor = conn.cursor()
            current_time = datetime.now()
            
            # 온도 데이터 개별 처리
            if temperature is not None:
                sensor_data["temperature"] = round(temperature, 1)
                sensor_data_initialized = True  # 실제 센서 데이터를 읽었음을 표시
                cursor.execute("INSERT INTO readings (sensor_type, value, timestamp) VALUES (%s, %s, %s)",
                               ('temperature', sensor_data["temperature"], current_time))
                print(f"Temperature updated: {sensor_data['temperature']}°C")
            
            # 습도 데이터 개별 처리
            if humidity is not None:
                sensor_data["humidity"] = round(humidity, 1)
                sensor_data_initialized = True  # 실제 센서 데이터를 읽었음을 표시
                cursor.execute("INSERT INTO readings (sensor_type, value, timestamp) VALUES (%s, %s, %s)",
                               ('humidity', sensor_data["humidity"], current_time))
                print(f"Humidity updated: {sensor_data['humidity']}%")

            # 거리 센서 데이터 유효성 검증 (0cm ~ 400cm)
            if 0.0 <= distance <= 400.0:
                sensor_data["distance"] = round(distance, 1)
                cursor.execute("INSERT INTO readings (sensor_type, value, timestamp) VALUES (%s, %s, %s)",
                               ('distance', sensor_data["distance"], current_time))
            else:
                print(f"Invalid distance reading: {distance}cm. Keeping previous value.")
            conn.commit()
            cursor.close()
            conn.close()
        except mariadb.Error as e:
            print(f"DB Error on insert: {e}")
        
        # 3. 터치 센서 감지
        if GPIO_AVAILABLE:
            try:
                current_touch_state = GPIO.input(TOUCH_SENSOR_PIN)
                if current_touch_state == 1 and previous_touch_state == 0:
                    system_status["mode"] = "MANUAL" if system_status["mode"] == "AUTO" else "AUTO"
                    print(f"Mode toggled to {system_status['mode']} by touch sensor.")
                    time.sleep(0.3) # 디바운싱 고려
                previous_touch_state = current_touch_state
            except Exception as e:
                print(f"Touch sensor error: {e}")

        # 4. Auto 모드일 경우, 제어 로직 실행
        if system_status["mode"] == "AUTO":
            auto_control_logic()


        time.sleep(5)

# --- Flask 라우팅 ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def get_data():
    return jsonify({
        "sensors": sensor_data, 
        "status": system_status,
        "data_initialized": sensor_data_initialized
    })

@app.route('/toggle_mode', methods=['POST'])
def toggle_mode():
    system_status["mode"] = "MANUAL" if system_status["mode"] == "AUTO" else "AUTO"
    return jsonify({"success": True, "mode": system_status["mode"]})

@app.route('/control/<device>/<action>', methods=['POST'])
def control_device(device, action):
    if system_status["mode"] == "MANUAL":
        action = action.upper()
        if device in system_status["devices"] and action in ["ON", "OFF"]:
            system_status["devices"][device] = action
            # [수정] 실제 LED 제어 함수 호출
            if device == 'aircon': control_led(LED_AIRCON_PIN, action)
            elif device == 'heater': control_led(LED_HEATER_PIN, action)
            elif device == 'dehumidifier': control_led(LED_DEHUMIDIFIER_PIN, action)
            return jsonify({"success": True})
    return jsonify({"success": False, "message": "Only available in Manual mode."})

@app.route('/history/<sensor_type>')
def history(sensor_type):
    if sensor_type not in ['temperature', 'humidity', 'distance']:
        return "Invalid sensor type", 404
    
    readings = []
    chart_data = {'labels': [], 'values': []}
    print(f"[DEBUG] sensor_type: {sensor_type}")
    
    
    try:
        conn = mariadb.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT timestamp, value FROM readings WHERE sensor_type = %s ORDER BY timestamp DESC LIMIT 50",
            (sensor_type,)
        )
        readings = cursor.fetchall()
        #print(f"[DEBUG] readings: {readings}")

        # 그래프 데이터 준비 (시간 순으로 정렬)
        if readings:
            readings_reversed = list(reversed(readings))
            labels = []
            values = []
            for reading in readings_reversed:
                try:
                    timestamp_str = reading['timestamp'].strftime('%m-%d %H:%M')
                    value = float(reading['value'])
                    labels.append(str(timestamp_str))
                    values.append(value)
                except (ValueError, TypeError, AttributeError) as e:
                    print(f"Data conversion error: {e}")
                    continue
            chart_data = {
                'labels': [str(label) for label in labels],
                'values': [float(value) for value in values]
            }
        print(f"[DEBUG] chart_data: {chart_data}")
        cursor.close()
        conn.close()
    except mariadb.Error as e:
        print(f"DB Error on select: {e}")
        chart_data = {'labels': [], 'values': []}
    except Exception as e:
        print(f"Unexpected error in history route: {e}")
        chart_data = {'labels': [], 'values': []}
    
    # 최종 데이터 검증 및 JSON 직렬화 보장
    if not isinstance(chart_data.get('labels'), list):
        chart_data['labels'] = []
    else:
        chart_data['labels'] = [str(item) for item in chart_data['labels']]
    
    if not isinstance(chart_data.get('values'), list):
        chart_data['values'] = []
    else:
        chart_data['values'] = [float(item) for item in chart_data['values'] if isinstance(item, (int, float))]
    
    # 센서 타입별 단위 및 제목 설정
    sensor_info = {
        'temperature': {'title': '온도', 'unit': '°C', 'color': '#ff6384'},
        'humidity': {'title': '습도', 'unit': '%', 'color': '#36a2eb'},
        'distance': {'title': '거리', 'unit': 'cm', 'color': '#4bc0c0'}
    }
    
    # 통계 데이터 계산
    stats = {'current': 0, 'max': 0, 'min': 0, 'avg': 0}
    has_data = False
    
    # chart_data['values']가 유효한 리스트인지 확인하고 처리
    if chart_data['values'] and len(chart_data['values']) > 0:
        try:
            values = list(chart_data['values'])  # 확실히 리스트로 변환
            has_data = True
            stats = {
                'current': values[-1],
                'max': max(values),
                'min': min(values),
                'avg': sum(values) / len(values)
            }
        except (TypeError, ValueError) as e:
            print(f"Error calculating stats: {e}")
            # 에러 발생 시 기본값 유지

    return render_template('history.html', 
                         sensor_type=sensor_type, 
                         readings=readings[:10],  # 테이블에는 최근 10개만 표시
                         chart_data=chart_data,
                         sensor_info=sensor_info[sensor_type],
                         stats=stats,
                         has_data=has_data)

# --- 메인 실행 부분 ---
if __name__ == '__main__':
    try:
        init_db()
        setup_gpio() # GPIO 초기화
        # 실제 하드웨어 데이터 수집 스레드 시작
        data_thread = threading.Thread(target=update_hardware_data, daemon=True)
        data_thread.start()
        app.run(debug=False, host='0.0.0.0', port=5001)
    finally:
        # 프로그램 종료 시 GPIO 리소스 정리
        if GPIO_AVAILABLE:
            print("Cleaning up GPIO.")
            try:
                GPIO.cleanup()
            except:
                pass