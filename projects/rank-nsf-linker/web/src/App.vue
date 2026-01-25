<script setup lang="ts">
import { onMounted } from "vue";
import { preloadMapTiles } from "./public/serviceWorker";
import WorldMap from "./components/WorldMap.vue";
onMounted(() => {
  preloadMapTiles();
});
setInterval(() => {
  caches.open("map-tiles-cache").then((cache) => {
    cache.keys().then((keys) => {
      console.log(`📊 Cached tiles: ${keys.length}`);
    });
  });
}, 10000); // Every 10 seconds
</script>

<template>
  <div id="app">
    <WorldMap />
  </div>
</template>
