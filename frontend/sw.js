// Service Worker for RuralAssist Chatbot - Offline Support

const CACHE_NAME = 'ruralassist-chatbot-v6';
const urlsToCache = [
  "/",
  "/index.html",
  "/schemes.html",
  "/report.html",
  "/ocr.html",
  "/profile.html",
  "/chatbot_new.html",

  "/assets/css/style.css",
  "/assets/css/theme.css",
  "/assets/css/chatbot.css",

  "/assets/js/main.js",
  "/assets/js/config.js",
  "/assets/js/chat_float.js",
  "/assets/js/chatbot.js",
  "/assets/js/schemes.js",
  "/assets/js/faq.js",
  "/assets/js/report.js",
  "/assets/js/ocr.js",
  "/assets/js/profile.js",

  "/assets/images/logo.png",
  "/assets/images/icon-192.png",
  "/assets/images/icon-512.png"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(urlsToCache);
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) return caches.delete(key);
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(cached => {
      return cached || fetch(event.request).catch(() => caches.match("/index.html"));
    })
  );
});
