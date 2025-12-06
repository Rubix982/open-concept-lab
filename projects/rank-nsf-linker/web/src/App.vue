<script setup lang="ts">
import WorldMap from "./components/WorldMap.vue";
import StatsDashboard from "./components/StatsDashboard.vue";
import { ref } from "vue";

const worldMapRef = ref<InstanceType<typeof WorldMap> | null>(null);

function handleSelectUniversity(universityName: string) {
  // Find and select the university in WorldMap
  if (worldMapRef.value) {
    worldMapRef.value.selectUniversity(universityName);
  }
}
</script>

<template>
  <div id="app">
    <StatsDashboard @select-university="handleSelectUniversity" />
    <WorldMap ref="worldMapRef" />
  </div>
</template>

<style scoped>
#app {
  width: 100vw;
  height: 100vh;
  margin: 0;
  padding: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
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
