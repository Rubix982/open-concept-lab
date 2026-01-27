import { logger } from "@/utils/logger";

export function logCacheStats() {
  caches.open("map-tiles-cache").then((cache) => {
    cache.keys().then((keys) => {
      logger.debug(`📊 Cached tiles: ${keys.length}`);
    });
  });

  navigator.serviceWorker.getRegistrations().then((regs) => {
    logger.debug("Active service workers:", regs.length);
    regs.forEach((reg) => logger.debug("SW scope:", reg.scope));
  });

  // Check what's cached
  caches.keys().then((keys) => {
    logger.debug("Cache storage:", keys);
    keys.forEach((key) => {
      caches.open(key).then((cache) => {
        cache.keys().then((requests) => {
          logger.debug(`${key}: ${requests.length} entries`);
        });
      });
    });
  });
}
