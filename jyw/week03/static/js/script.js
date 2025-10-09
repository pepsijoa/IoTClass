// DOM이 완전히 로드된 후 스크립트 실행
document.addEventListener('DOMContentLoaded', () => {
    // --- DOM 요소 가져오기 ---
    const tempValue = document.getElementById('temp-value');
    const humidityValue = document.getElementById('humidity-value');
    const distanceValue = document.getElementById('distance-value');
    const distanceCard = document.getElementById('distance-card');

    const autoBtn = document.getElementById('auto-btn');
    const manualBtn = document.getElementById('manual-btn');
    const footerNote = document.getElementById('footer-note');

    const deviceToggles = {
        aircon: document.getElementById('aircon-toggle'),
        heater: document.getElementById('heater-toggle'),
        dehumidifier: document.getElementById('dehumidifier-toggle')
    };

    // --- 데이터 업데이트 함수 ---
    // 서버로부터 최신 데이터를 주기적으로 가져와 화면에 반영
    async function fetchData() {
        try {
            const response = await fetch('/data');
            const data = await response.json();
            console.log('센서 fetch 결과:', data);

            // 1. 센서 데이터 업데이트
            tempValue.textContent = `${data.sensors.temperature.toFixed(1)} °C`;
            humidityValue.textContent = `${data.sensors.humidity.toFixed(1)} %`;
            const distanceInMeters = (data.sensors.distance / 100.0).toFixed(2);
            distanceValue.textContent = `${distanceInMeters} m`;

            // 2. 거리 경고 처리
            if (data.sensors.distance <= 10.0) {
                distanceCard.classList.add('warning');
            } else {
                distanceCard.classList.remove('warning');
            }

            // 3. 모드 상태 업데이트
            const currentMode = data.status.mode;
            updateModeUI(currentMode);

            // 4. 기기 상태 업데이트
            for (const device in data.status.devices) {
                const toggle = deviceToggles[device];
                if (toggle) {
                    toggle.checked = (data.status.devices[device] === 'ON');
                }
            }

        } catch (error) {
            console.error('Error fetching data:', error);
        }
    }

    // --- UI 업데이트 함수 ---
    // 현재 모드에 따라 UI (버튼 활성화, 푸터 텍스트, 토글 활성/비활성) 변경
    function updateModeUI(mode) {
        const isAuto = mode === 'AUTO';

        autoBtn.classList.toggle('active', isAuto);
        manualBtn.classList.toggle('active', !isAuto);

        footerNote.textContent = isAuto
            ? '모드: AUTO — AUTO일 때는 개별 기기 ON/OFF가 비활성화됩니다.'
            : '모드: MANUAL — 웹페이지에서 각 기기를 직접 제어할 수 있습니다.';

        for (const device in deviceToggles) {
            const toggle = deviceToggles[device];
            const switchLabel = toggle.parentElement;
            if (isAuto) {
                switchLabel.classList.add('disabled');
            } else {
                switchLabel.classList.remove('disabled');
            }
        }
    }
    
    // --- 이벤트 리스너 설정 ---

    // 모드 변경 버튼 클릭
    autoBtn.addEventListener('click', () => {
        if (!autoBtn.classList.contains('active')) {
            fetch('/toggle_mode', { method: 'POST' });
        }
    });

    manualBtn.addEventListener('click', () => {
        if (!manualBtn.classList.contains('active')) {
            fetch('/toggle_mode', { method: 'POST' });
        }
    });

    // 각 기기 토글 스위치 변경
    for (const device in deviceToggles) {
        deviceToggles[device].addEventListener('change', (event) => {
            // Manual 모드일 때만 서버로 제어 명령 전송
            if (!autoBtn.classList.contains('active')) {
                const action = event.target.checked ? 'ON' : 'OFF';
                fetch(`/control/${device}/${action}`, { method: 'POST' });
            }
        });
    }

    // --- 초기화 ---
    // 페이지 로드 시 첫 데이터 가져오기
    fetchData(); 
    // 5초마다 주기적으로 데이터 업데이트
    setInterval(fetchData, 5000); 
});
