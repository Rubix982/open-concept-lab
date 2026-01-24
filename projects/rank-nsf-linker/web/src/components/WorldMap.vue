<script setup lang="ts">
import "@/assets/styles/worldMap.css";
import { ref, onMounted, onBeforeUnmount, watch, computed } from "vue";
import maplibregl from "maplibre-gl";
import "maplibregl/dist/maplibre-gl.css";
import { updatePointsLayer } from "@/utils/coloringUtils";
import { initializeMap, waitForBackendReady, loadMapData } from "@/utils/main";
import {
  vizMode,
  PIPELINE_STATUS,
  STATUS_CONFIG,
} from "@/config/pipelineStatus";

const pipelineStatusMessage = ref(PIPELINE_STATUS.PENDING);
const currentPipelineStatus = computed(
  () => STATUS_CONFIG[pipelineStatusMessage.value]
);
const mapContainer = ref<HTMLDivElement | null>(null);
const map = ref<maplibregl.Map | null>(null);

onMounted(async () => {
  initializeMap(mapContainer, map);
  await waitForBackendReady(pipelineStatusMessage);
  await loadMapData(pipelineStatusMessage, map);
});

watch(vizMode, () => {
  updatePointsLayer(map.value);
});

onBeforeUnmount(() => {
  map.value?.remove();
});
</script>

<template>
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
