# config.py
# 이 파일은 프로젝트 전체에서 사용하는 설정 값들을 보관합니다.

# DB info
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'camagui',
    'password': 'power2',
    'database': 'IOT'
}

# sensor settings
ALERT_THRESHOLD = 10
SENSOR_POLL_INTERVAL = 5  # seconds

