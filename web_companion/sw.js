const CACHE_PREFIX = "dokureader-companion-";
const CACHE = "dokureader-companion-v9";
// Wächter (tests/pwa_mobile_smoke.test.mjs): Hash über alle ASSETS inkl. Manifest und Icons; bei jeder Änderung daran CACHE erhöhen und Hash erneuern.
const ASSET_HASH = "bfe19e577cef";
const ASSETS = [
  "./",
  "./index.html",
  "./style.css",
  "./app.js",
  "./i18n.js",
  "./library.js",
  "./manifest.webmanifest",
  "./icons/dokureader-companion-180.png",
  "./icons/dokureader-companion-192.png",
  "./icons/Icon-192.png",
  "./icons/Icon-512.png",
  "./icons/Icon-maskable-192.png",
  "./icons/Icon-maskable-512.png"
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(k => k.startsWith(CACHE_PREFIX) && k !== CACHE)
          .map(k => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then(cached => cached || fetch(e.request).catch(() => new Response("Offline", { status: 503, headers: { "Content-Type": "text/plain" } })))
  );
});
