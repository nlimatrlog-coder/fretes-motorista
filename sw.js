const CACHE = 'fretes-20260926203412';
const ARQUIVOS = ['./', './index.html', './manifest.webmanifest', './icone-192.png', './icone-512.png', './icone-180.png', './logo.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ARQUIVOS)));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((chaves) => Promise.all(chaves.filter((k) => k !== CACHE).map((k) => caches.delete(k)))));
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET' || new URL(e.request.url).origin !== self.location.origin) return;
  const daRede = fetch(e.request).then((r) => {
    const copia = r.clone();
    caches.open(CACHE).then((c) => c.put(e.request, copia));
    return r;
  });
  const limite = new Promise((_, falha) => setTimeout(() => falha(new Error('lento')), 4000));
  e.respondWith(
    Promise.race([daRede, limite]).catch(() =>
      caches.match(e.request, { ignoreSearch: true }).then((r) => r || caches.match('./index.html')).then((r) => r || daRede))
  );
});