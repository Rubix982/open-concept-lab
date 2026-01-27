/// <reference lib="webworker" />

// public/sw.js
const sw = self as unknown as ServiceWorkerGlobalScope;

import { logger } from "@/utils/logger";

const servicWorkerLogger = logger.child("service-worker");

const CACHE_NAME = "map-tiles-v1";
const DATA_CACHE = "university-data-v1";

sw.addEventListener("install", () => {
  servicWorkerLogger.debug("🔧 Service Worker installing...");
  sw.skipWaiting();
});

sw.addEventListener("activate", (event) => {
  servicWorkerLogger.debug("✅ Service Worker activated");
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME && cache !== DATA_CACHE) {
            servicWorkerLogger.debug("🗑️ Deleting old cache:", cache);
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

export async function preloadMapTiles() {
  if (!("caches" in window)) return;

  const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;

  if (!MAPBOX_TOKEN) {
    console.warn("⚠️ Cannot pre-cache: MAPBOX_TOKEN missing");
    return;
  }

  const cache = await caches.open(CACHE_NAME);

  const tilesToCache = [
    `https://api.mapbox.com/v4/mapbox.mapbox-streets-v8/4/3/5.vector.pbf?sku=101YMMqGVf3Cz&access_token=${MAPBOX_TOKEN}`,
    `https://api.mapbox.com/v4/mapbox.mapbox-streets-v8/4/4/5.vector.pbf?sku=101YMMqGVf3Cz&access_token=${MAPBOX_TOKEN}`,
    `https://api.mapbox.com/v4/mapbox.mapbox-streets-v8/4/5/5.vector.pbf?sku=101YMMqGVf3Cz&access_token=${MAPBOX_TOKEN}`,
  ];

  try {
    await Promise.all(
      tilesToCache.map((url) =>
        fetch(url)
          .then((response) => {
            if (response.ok) {
              return cache.put(url, response);
            }
          })
          .catch((err) => console.warn("Failed to cache:", url, err))
      )
    );

    servicWorkerLogger.debug("✅ Pre-cached", tilesToCache.length, "map tiles");
  } catch (err) {
    console.error("❌ Pre-cache error:", err);
  }
}
