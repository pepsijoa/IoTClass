// static/js/script.js

async function updateCounter() {
    try {
        const res = await fetch("/getcounter");
        const data = await res.json();
        document.getElementById("counter").textContent = data.value;
    } catch (error) {
        console.error("Failed to fetch counter:", error);
    }
}

async function updateDistance() {
    try {
        const res = await fetch("/getdistance");
        const data = await res.json();

        const distanceValueElement = document.getElementById("current-distance-value");
        const statusElement = document.getElementById("proximity-status");

        if (data.value !== "Out of Range" && data.value !== -1) {
            // cm 단위로 정수 표시
            const distanceInCm = Math.round(data.value);
            distanceValueElement.textContent = distanceInCm;
        } else {
            distanceValueElement.textContent = "측정 불가";
        }

        // 알람 상태에 따라 스타일 변경
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

async function updateTouch() {
    try {
        const res = await fetch("/gettouch");
        const data = await res.json();

        const touchStatusElement = document.getElementById("touch-status");
        const touchIndicatorElement = document.getElementById("touch-indicator");

        // 터치 상태 텍스트 업데이트
        if (data.touched) {
            touchStatusElement.textContent = "터치 감지됨";
        } else {
            touchStatusElement.textContent = "터치 없음";
        }

        // 터치 상태에 따라 스타일 변경
        if (data.touched) {
            touchIndicatorElement.textContent = "Status: TOUCHED!";
            touchIndicatorElement.classList.remove("touch-inactive");
            touchIndicatorElement.classList.add("touch-active");
        } else {
            touchIndicatorElement.textContent = "Status: No Touch";
            touchIndicatorElement.classList.remove("touch-active");
            touchIndicatorElement.classList.add("touch-inactive");
        }

    } catch (error) {
        console.error("Failed to fetch touch:", error);
        document.getElementById("touch-status").textContent = "연결 오류";
        const touchIndicatorElement = document.getElementById("touch-indicator");
        touchIndicatorElement.textContent = "Status: Error";
        touchIndicatorElement.classList.remove("touch-active");
        touchIndicatorElement.classList.add("touch-inactive");
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
            // 온도와 습도 업데이트
            temperatureElement.textContent = data.temperature.toFixed(1);
            humidityElement.textContent = data.humidity.toFixed(1);

            // 온도에 따른 상태 분류
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
            // 에러 처리
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


document.addEventListener('DOMContentLoaded', () => {
    updateCounter();
    updateDistance();
    updateTouch();
    updateTemperatureHumidity();

    setInterval(updateCounter, 1000);
    setInterval(updateDistance, 1000);
    setInterval(updateTouch, 500); // 터치는 더 빠른 업데이트로 반응성 향상
    setInterval(updateTemperatureHumidity, 2000); // 온도/습도는 2초마다 업데이트
});