/// <reference lib="webworker" />

// public/sw.js
const sw = self as unknown as ServiceWorkerGlobalScope;

const CACHE_NAME = "map-tiles-v1";
const DATA_CACHE = "university-data-v1";

sw.addEventListener("install", (event) => {
  console.log("🔧 Service Worker installing...");
  sw.skipWaiting();
});

sw.addEventListener("activate", (event) => {
  console.log("✅ Service Worker activated");
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME && cache !== DATA_CACHE) {
            console.log("🗑️ Deleting old cache:", cache);
            return caches.delete(cache);
          }
        })
      );
    })
  );
});

sw.addEventListener("fetch", (event) => {
  const url = event.request.url;

  // Cache map tiles
  if (url.includes("basemaps.cartocdn.com") || url.includes("tiles")) {
    event.respondWith(
      caches.open(CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((response) => {
          if (response) {
            return response;
          }

          return fetch(event.request)
            .then((fetchResponse) => {
              if (fetchResponse && fetchResponse.status === 200) {
                cache.put(event.request, fetchResponse.clone());
              }
              return fetchResponse;
            })
            .catch(() => {
              return new Response("", { status: 503 });
            });
        });
      })
    );
  }

  // Cache API data
  else if (url.includes("/api/")) {
    event.respondWith(
      caches.open(DATA_CACHE).then((cache) => {
        return fetch(event.request)
          .then((response) => {
            if (response && response.status === 200) {
              cache.put(event.request, response.clone());
            }
            return response;
          })
          .catch(() => {
            return cache.match(event.request).then((response) => {
              return (
                response ||
                new Response('{"error": "Network error"}', {
                  status: 503,
                  headers: { "Content-Type": "application/json" },
                })
              );
            });
          });
      })
    );
  } else {
    event.respondWith(fetch(event.request));
  }
});
