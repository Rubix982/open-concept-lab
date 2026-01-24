<script setup lang="ts">
import "@/assets/styles/pwa.css";
import "@/assets/styles/style.css";
import "@/assets/styles/worldMap.css";
import { ref, onMounted, onBeforeUnmount, watch, computed } from "vue";
import maplibregl from "maplibre-gl";
import { updatePointsLayer } from "@/utils/coloringUtils";
import { initializeMap, waitForBackendReady, loadMapData } from "@/utils/main";
import {
  vizMode,
  PIPELINE_STATUS,
  STATUS_CONFIG,
} from "@/config/pipelineStatus";
import { registerSW } from "virtual:pwa-register";

const pipelineStatusMessage = ref(PIPELINE_STATUS.PENDING);
const currentPipelineStatus = computed(
  () => STATUS_CONFIG[pipelineStatusMessage.value]
);
const mapContainer = ref<HTMLDivElement | null>(null);
const map = ref<maplibregl.Map | null>(null);

onMounted(async () => {
  await initializeMap(mapContainer, map);
  await waitForBackendReady(pipelineStatusMessage);
  await loadMapData(pipelineStatusMessage, map);
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

  <div v-if="currentPipelineStatus.showOverlay" class="processing-overlay">
    <div class="processing-message">
      <span>{{ currentPipelineStatus.message }}</span>
    </div>
  </div>

  <div
    v-show="pipelineStatusMessage === PIPELINE_STATUS.COMPLETED"
    class="app"
    id="appMap"
  >
    <div ref="mapContainer" id="map" class="map-container" />
  </div>
</template>
