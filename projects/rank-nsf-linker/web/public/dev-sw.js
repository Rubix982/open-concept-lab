// Kill switch for the offline service worker an earlier version installed. Browsers re-fetch
// this script to check for updates; this version deletes every cache, unregisters itself and
// reloads open tabs so they get the current site.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(keys.map((k) => caches.delete(k)));
      await self.registration.unregister();
      const tabs = await self.clients.matchAll({ type: "window" });
      tabs.forEach((tab) => tab.navigate(tab.url));
    })(),
  );
});
