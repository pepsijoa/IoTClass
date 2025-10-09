// static/js/script.js

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(registration => {
        console.log('ServiceWorker registration successful with scope: ', registration.scope);
      }, err => {
        console.log('ServiceWorker registration failed: ', err);
      });
  });
}

// --- 스위치 ON/OFF 라벨 업데이트 함수 ---
function updateSwitchLabel(switchElement, labelElement) {
    if (labelElement) {
        labelElement.textContent = switchElement.checked ? 'ON' : 'OFF';
    }
}

// --- 모드에 따라 스위치 활성/비활성 제어 --- 
async function updateSwitchesByMode() {
    try {
        const res = await fetch('/gettouch', { cache: 'no-store' });
        const data = await res.json();
        const isManual = Number(data.current_state) === 1;

        const aircon = document.getElementById('airconSwitch');
        const heater = document.getElementById('heaterSwitch');
        const humidifier = document.getElementById('humidifierSwitch');

        [aircon, heater, humidifier].forEach(sw => {
            if (sw) sw.disabled = !isManual;
        });
    } catch (e) {
        console.error('스위치 모드 업데이트 오류:', e);
    }
}

async function updateDistance() {
    try {
        const res = await fetch("/getdistance");
        const data = await res.json();

        const distanceValueElement = document.getElementById("current-distance-value");
        const statusElement = document.getElementById("proximity-status");

        if (data.value !== "Out of Range" && data.value !== -1) {
            const distanceInCm = Math.round(data.value);
            distanceValueElement.textContent = distanceInCm;
        } else {
            distanceValueElement.textContent = "측정 불가";
        }

        if (data.alert) {
            statusElement.textContent = "Status: PROXIMITY ALERT!";
            statusElement.classList.remove("status-normal");
            statusElement.classList.add("status-alert");
        } else {
            statusElement.textContent = "Status: Normal";
            statusElement.classList.remove("status-alert");
            statusElement.classList.add("status-normal");
        }
    } catch (error) {
        console.error("Failed to fetch distance:", error);
        document.getElementById("current-distance-value").textContent = "연결 오류";
        const statusElement = document.getElementById("proximity-status");
        statusElement.textContent = "Status: Error";
        statusElement.classList.remove("status-alert");
        statusElement.classList.add("status-normal");
    }
}

async function updateTemperatureHumidity() {
    try {
        const res = await fetch("/gettemperature");
        const data = await res.json();

        const temperatureElement = document.getElementById("temperature-value");
        const humidityElement = document.getElementById("humidity-value");
        const climateStatusElement = document.getElementById("climate-status");
        const climateStatusTextElement = document.getElementById("climate-status-text");

        if (data.status === "success" && data.temperature !== null && data.humidity !== null) {
            temperatureElement.textContent = data.temperature.toFixed(1);
            humidityElement.textContent = data.humidity.toFixed(1);

            let statusText = "정상";
            let statusClass = "climate-normal";

            if (data.temperature < 10) {
                statusText = "추움";
                statusClass = "climate-cold";
            } else if (data.temperature > 30) {
                statusText = "더움";
                statusClass = "climate-hot";
            } else if (data.humidity > 80) {
                statusText = "습함";
                statusClass = "climate-humid";
            } else if (data.humidity < 30) {
                statusText = "건조함";
                statusClass = "climate-dry";
            }

            climateStatusTextElement.textContent = statusText;
            climateStatusElement.className = statusClass;
        } else {
            temperatureElement.textContent = "--";
            humidityElement.textContent = "--";
            climateStatusTextElement.textContent = "센서 오류";
            climateStatusElement.className = "climate-error";
        }
    } catch (error) {
        console.error("Failed to fetch temperature/humidity:", error);
        document.getElementById("temperature-value").textContent = "--";
        document.getElementById("humidity-value").textContent = "--";
        document.getElementById("climate-status-text").textContent = "연결 오류";
        document.getElementById("climate-status").className = "climate-error";
    }
}

// --- 페이지 로드 시 실행될 메인 로직 ---
document.addEventListener('DOMContentLoaded', () => {
    // 주기적으로 센서 값 업데이트
    setInterval(updateDistance, 1000);
    setInterval(updateTemperatureHumidity, 2000);
    
    // 모드 상태 주기적 확인 및 스위치 활성화/비활성화
    updateSwitchesByMode();
    setInterval(updateSwitchesByMode, 1000);

    // --- 각 스위치 요소 가져오기 ---
    const aircon = document.getElementById('airconSwitch');
    const heater = document.getElementById('heaterSwitch');
    const humidifier = document.getElementById('humidifierSwitch');

    const airconState = document.getElementById('airconState');
    const heaterState = document.getElementById('heaterState');
    const humidifierState = document.getElementById('humidifierState');

    // --- 페이지 로드 시 현재 스위치 상태에 맞춰 ON/OFF 라벨 초기화 ---
    updateSwitchLabel(aircon, airconState);
    updateSwitchLabel(heater, heaterState);
    updateSwitchLabel(humidifier, humidifierState);

    // --- 스위치(에어컨, 히터, 제습기) 상태 변경 시 서버에 전송 및 라벨 변경 ---
    if (aircon) {
        aircon.addEventListener('change', async () => {
            const state = aircon.checked ? 1 : 0;
            updateSwitchLabel(aircon, airconState); // 라벨 업데이트
            await fetch(`/0/${state}`);
        });
    }
    if (heater) {
        heater.addEventListener('change', async () => {
            const state = heater.checked ? 1 : 0;
            updateSwitchLabel(heater, heaterState); // 라벨 업데이트
            await fetch(`/1/${state}`);
        });
    }
    if (humidifier) {
        humidifier.addEventListener('change', async () => {
            const state = humidifier.checked ? 1 : 0;
            updateSwitchLabel(humidifier, humidifierState); // 라벨 업데이트
            await fetch(`/2/${state}`);
        });
    }
});