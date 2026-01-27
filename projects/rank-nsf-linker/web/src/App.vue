<script setup lang="ts">
import { onMounted } from "vue";
import { preloadMapTiles } from "./public/serviceWorker";
import WorldMap from "./components/WorldMap.vue";
import { logCacheStats } from "./utils/backgroundServices";
onMounted(() => {
  preloadMapTiles();
});
setInterval(() => {
  logCacheStats();
}, 10000); // Every 10 seconds
</script>

<template>
  <div id="app">
    <WorldMap />
  </div>
</template>
