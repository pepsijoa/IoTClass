// 캐시에 저장할 파일들의 목록
const CACHE_NAME = 'iot-controller-cache-v1';
const FILES_TO_CACHE = [
  '/', // 메인 페이지
  // CSS 및 JS 파일
  '/static/css/style.css',
  '/static/js/script.js',
  '/static/manifest.json',

  // 이미지
  '/static/images/kulogo.jpeg',
  '/static/images/aircon.png',
  '/static/images/heat.png',
  '/static/images/de.png',
  '/static/images/kulogo_192.png',
  '/static/images/kulogo_512.png',
  
  // 데이터
  '/history/temperature',
  '/history/humidity',
  '/history/distance',

  // 폰트
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css'
  
];

// 1. 서비스 워커 설치
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Install');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[ServiceWorker] Pre-caching offline page');
      return cache.addAll(FILES_TO_CACHE);
    })
  );
});

// 2. 캐시된 자원 반환 또는 네트워크 요청
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      // 캐시에 파일이 있으면 그것을 반환하고, 없으면 네트워크로 요청
      return response || fetch(event.request);
    })
  );
});