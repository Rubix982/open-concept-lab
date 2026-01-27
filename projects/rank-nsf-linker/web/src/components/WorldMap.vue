<script setup lang="ts">
// Libraries
import { ref, onMounted, onBeforeUnmount, computed, nextTick } from "vue";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { registerSW } from "virtual:pwa-register";

// Utils
import {
  initializeMap,
  waitForBackendReady,
  loadMapData,
} from "@/utils/main.ts";
import { PIPELINE_STATUS, STATUS_CONFIG } from "@/config/pipelineStatus.ts";
import { logger } from "@/utils/logger";

// Sub-components
import LeftPanel from "./LeftPanel.vue";

// Stores
import { mapInstance } from "@/config/mapSettings";

// Styles
import "@/assets/styles/pwa.css";
import "@/assets/styles/style.css";
import "@/assets/styles/worldMap.css";
import "@/assets/styles/mapInteractions.css";

const pipelineStatusMessage = ref(PIPELINE_STATUS.PENDING);
const currentPipelineStatus = computed(
  () => STATUS_CONFIG[pipelineStatusMessage.value]
);
const shouldShowMap = computed(
  () => pipelineStatusMessage.value === PIPELINE_STATUS.COMPLETED
);
const mapContainer = ref<HTMLDivElement | null>(null);
mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;

onMounted(async () => {
  await waitForBackendReady(pipelineStatusMessage);
  await nextTick();
  await initializeMap(mapContainer, mapInstance);
  await loadMapData(pipelineStatusMessage, mapInstance);
  if (mapContainer.value) {
    mapContainer.value.style.width = "100vw";
    mapContainer.value.style.height = "100vh";
  }
});

const needRefresh = ref(false);
const offlineReady = ref(false);
const updateServiceWorker = registerSW({
  onNeedRefresh() {
    needRefresh.value = true;
    logger.debug("🔄 New content available, click to update");
  },
  onOfflineReady() {
    offlineReady.value = true;
    logger.debug("✅ App ready to work offline");
  },
  onRegistered(registration) {
    logger.debug("✅ Service Worker registered:", registration);
  },
  onRegisterError(error) {
    console.error("❌ Service Worker registration failed:", error);
  },
});

function closePrompt() {
  needRefresh.value = false;
  offlineReady.value = false;
}

async function updateApp() {
  await updateServiceWorker(true);
  closePrompt();
}

onBeforeUnmount(() => {
  mapInstance.value?.remove();
});
</script>

<template>
  <!-- Update notification -->
  <div v-if="needRefresh" class="pwa-toast">
    <div class="pwa-message">
      <span>New content available, click to update.</span>
      <button @click="updateApp" class="pwa-button">Update</button>
      <button @click="closePrompt" class="pwa-button-cancel">Close</button>
    </div>
  </div>

  <!-- Offline ready notification -->
  <div v-if="offlineReady" class="pwa-toast">
    <div class="pwa-message">
      <span>App ready to work offline</span>
      <button @click="closePrompt" class="pwa-button">OK</button>
    </div>
  </div>

  <div v-if="!shouldShowMap" class="processing-overlay">
    <div class="processing-message">
      <span>{{ currentPipelineStatus.message }}</span>
    </div>
  </div>

  <LeftPanel />

  <div v-show="shouldShowMap" class="app" id="appMap">
    <div
      ref="mapContainer"
      id="map"
      class="map-container"
      style="width: 100vw; height: 100vh"
    />
  </div>
</template>
