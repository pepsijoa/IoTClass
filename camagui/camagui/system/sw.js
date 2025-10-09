// sw.js (Service Worker 파일)

const CACHE_NAME = 'iot-pwa-cache-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/css/style.css',
  '/js/app.js',
  '/images/icon-192x192.png'
  // 모든 필수 정적 자산(assets)을 여기에 추가합니다.
];

// 1. Install 이벤트: Service Worker 설치 시 캐시에 자산 저장
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// 2. Fetch 이벤트: 네트워크 요청을 가로채서 캐시된 자산을 확인
self.addEventListener('fetch', event => {
  // API 호출(백엔드 통신)은 캐시하지 않고 네트워크로 바로 요청
  if (event.request.url.includes('/api/')) {
     return fetch(event.request);
  }

  // 그 외 정적 자산은 캐시에서 우선 확인
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // 캐시에 자산이 있으면 캐시된 응답 반환, 없으면 네트워크 요청
        return response || fetch(event.request);
      })
  );
});