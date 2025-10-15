<script setup lang="ts">
import WorldMap from './components/WorldMap.vue';
</script>

<template>
  <div class="app">
    <WorldMap />
  </div>
</template>

<style scoped>
.app {
  width: 100vw;
  height: 100vh;
  margin: 0;
  padding: 0;
  overflow: hidden;
}
</style>

<style>
/* Ensure html and body also fill viewport */
html,
body,
#app {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
}
</style>
