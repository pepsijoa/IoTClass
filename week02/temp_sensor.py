import time
import board
import adafruit_dht

dht_device = adafruit_dht.DHT11(board.D26)

print("온습도 측정을 시작합니다. (Ctrl+C 로 종료)")

try:
    while True:
        try:
            temperature = dht_device.temperature
            humidity = dht_device.humidity

            if humidity is not None and temperature is not None:
                print(f"온도 : {temperature:.1f}도, 습도 : {humidity} %")
            else:
                print("센서 값을 읽는 데 실패했습니다.")

        except RuntimeError as error:
            print(error.args[0])
            time.sleep(3)
            continue
        
        time.sleep(3)

except KeyboardInterrupt:
    print("\n프로그램을 종료합니다.")

finally:
    dht_device.exit()