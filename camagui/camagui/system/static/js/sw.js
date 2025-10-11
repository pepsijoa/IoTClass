// 서비스 워커가 처음 설치될 때 실행되는 코드입니다.
self.addEventListener('install', (event) => {
  console.log('Service worker installing...');
  // 지금은 아무것도 하지 않아도 괜찮습니다.
});

// 서비스 워커가 fetch(네트워크 요청) 이벤트를 가로챌 때 실행됩니다.
// 이 부분이 있어야 '설치 가능한 앱'으로 인식됩니다.
self.addEventListener('fetch', (event) => {
  // 현재는 네트워크 요청에 아무런 조작도 하지 않고 그대로 보내줍니다.
  event.respondWith(fetch(event.request));
});