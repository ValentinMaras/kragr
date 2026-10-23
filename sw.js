// kragr Service Worker: macht die App offline nutzbar.
// Seiten (HTML): zuerst aus dem Netz (immer aktuell), offline aus dem Speicher.
// Schriften und Symbole: zuerst aus dem Speicher.
// Bei jeder neuen Version VERSION hochzählen, dann werden alte Speicher gelöscht.
const VERSION = 'statiq-2026-10-23-1';
const FILES = ["./", "index.html", "calc.html", "size.html", "ref.html", "projekt.html", "rechtliches.html", "manifest.json", "lang/size.en.js", "lang/size.fr.js", "lang/size.es.js", "lang/ref.en.js", "lang/ref.fr.js", "lang/ref.es.js", "fonts/fonts.css", "fonts/figtree-latin-ext-wght-normal.woff2", "fonts/figtree-latin-wght-normal.woff2", "fonts/inter-greek-wght-normal.woff2", "fonts/jetbrains-mono-greek-wght-normal.woff2", "fonts/jetbrains-mono-latin-ext-wght-normal.woff2", "fonts/jetbrains-mono-latin-wght-normal.woff2", "icons/apple-touch-icon.png", "icons/favicon-32.png", "icons/icon-192.png", "icons/icon-512.png", "icons/icon-maskable-512.png"];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('statiq-') && k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request; if (req.method !== 'GET') return;
  const url = new URL(req.url); if (url.origin !== location.origin) return;
  const html = req.mode === 'navigate' || url.pathname.endsWith('.html') || url.pathname.endsWith('/');
  if (html) {
    e.respondWith(fetch(req).then(res => { if (res.ok) { const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); } return res; })
      .catch(() => caches.match(req, { ignoreSearch: true }).then(r => r || caches.match('index.html'))));
  } else {
    e.respondWith(caches.match(req).then(r => r || fetch(req).then(res => { if (res.ok) { const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); } return res; })));
  }
});
