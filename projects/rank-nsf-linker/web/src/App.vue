<script setup lang="ts">
import WorldMap from "./components/WorldMap.vue";
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
