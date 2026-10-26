/* 離線快取：頁面先抓最新、沒網路時用快取；字型與 Firebase 程式庫用快取並在背景更新 */
const VERSION = "ngy-v48";
/* 字型與 Firebase 程式庫放在獨立的快取，版本更新時不刪（不然更新後第一次沒網路就無法同步） */
const LIB = "ngy-lib";
const isLib = (u) => /fonts\.(googleapis|gstatic)\.com$/.test(u.hostname) || (u.hostname === "www.gstatic.com" && u.pathname.startsWith("/firebasejs/"));
const CORE = ["./", "./index.html", "./manifest.webmanifest", "./icon-192.png", "./icon-512.png", "./apple-touch-icon.png", "./ghibli-map.jpg", "./ghibli-map-thumb.jpg", "./nagoya-trip.ics"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(CORE)).then(() => self.skipWaiting()));
});

/* 舊版快取裡的字型與程式庫先搬到 LIB，再刪舊版 */
async function keepLibs(old) {
  const from = await caches.open(old), to = await caches.open(LIB);
  for (const req of await from.keys()) {
    try { if (isLib(new URL(req.url)) && !(await to.match(req))) { const res = await from.match(req); if (res) await to.put(req, res); } } catch (_) {}
  }
}
self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k.startsWith("ngy-") && k !== VERSION && k !== LIB).map((k) => keepLibs(k).catch(() => {}).then(() => caches.delete(k)))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  // 自己的頁面與檔案：網路優先，失敗時用快取
  if (url.origin === self.location.origin) {
    e.respondWith(
      fetch(req, { cache: "no-cache" }).then((res) => {
        const copy = res.clone();
        caches.open(VERSION).then((c) => c.put(req, copy));
        return res;
      }).catch(() => caches.match(req).then((r) => r || caches.match("./index.html")))
    );
    return;
  }

  // 字型與 Firebase 程式庫：先用快取，背景更新
  if (isLib(url)) {
    e.respondWith(
      caches.open(LIB).then((c) => c.match(req).then((hit) => {
        const net = fetch(req).then((res) => { if (res.ok || res.type === "opaque") c.put(req, res.clone()); return res; }).catch(() => hit);
        return hit || net;
      }))
    );
  }
  // 其他（Firestore、天氣 API）交給頁面自己處理
});

// 點通知打開 App
self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((list) => {
    for (const c of list) { if ("focus" in c) return c.focus(); }
    return self.clients.openWindow("./");
  }));
});
