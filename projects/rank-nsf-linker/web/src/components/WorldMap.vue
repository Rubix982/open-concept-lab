<script setup lang="ts">
import {
  ref,
  onMounted,
  onBeforeUnmount,
  watch,
  computed,
  nextTick,
} from "vue";
import { updatePointsLayer } from "@/utils/coloringUtils.ts";
import {
  initializeMap,
  waitForBackendReady,
  loadMapData,
} from "@/utils/main.ts";
import {
  vizMode,
  PIPELINE_STATUS,
  STATUS_CONFIG,
} from "@/config/pipelineStatus.ts";
import { registerSW } from "virtual:pwa-register";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

import "@/assets/styles/pwa.css";
import "@/assets/styles/style.css";
import "@/assets/styles/worldMap.css";

const pipelineStatusMessage = ref(PIPELINE_STATUS.PENDING);
const currentPipelineStatus = computed(
  () => STATUS_CONFIG[pipelineStatusMessage.value]
);
const shouldShowMap = computed(
  () => pipelineStatusMessage.value === PIPELINE_STATUS.COMPLETED
);
const mapContainer = ref<HTMLDivElement | null>(null);
const map = ref<mapboxgl.Map | null>(null);
mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;

onMounted(async () => {
  await waitForBackendReady(pipelineStatusMessage);
  await nextTick();

  console.log("Container dimensions:", {
    width: mapContainer.value?.offsetWidth,
    height: mapContainer.value?.offsetHeight,
  });

  await initializeMap(mapContainer, map);
  await loadMapData(pipelineStatusMessage, map);
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
    console.log("🔄 New content available, click to update");
  },
  onOfflineReady() {
    offlineReady.value = true;
    console.log("✅ App ready to work offline");
  },
  onRegistered(registration) {
    console.log("✅ Service Worker registered:", registration);
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

watch(vizMode, () => {
  updatePointsLayer(map.value);
});

onBeforeUnmount(() => {
  map.value?.remove();
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

  <div v-show="shouldShowMap" class="app" id="appMap">
    <div
      ref="mapContainer"
      id="map"
      class="map-container"
      style="width: 100vw; height: 100vh"
    />
  </div>
</template>
