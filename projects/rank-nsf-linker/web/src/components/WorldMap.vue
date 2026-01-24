<script setup lang="ts">
import "@/assets/styles/worldMap.css";
import { ref, onMounted, onBeforeUnmount, watch } from "vue";
import maplibregl from "maplibre-gl";
import "maplibregl/dist/maplibre-gl.css";
import { updatePointsLayer, updateSelectedFilter } from "@/utils/coloringUtils";
import { initializeMap, waitForBackendReady, loadMapData } from "@/utils/main";
import { vizMode } from "@/config/pipelineStatus";

const mapContainer = ref<HTMLDivElement | null>(null);
const map = ref<maplibregl.Map | null>(null);
const selectedId = ref<string | null>(null);

const pipelineStatusMessage = ref("");
const popupRef = ref<maplibregl.Popup | null>(null);

onMounted(async () => {
  initializeMap(mapContainer, map);
  await waitForBackendReady(pipelineStatusMessage);
  await loadMapData(pipelineStatusMessage, map);
});

watch(vizMode, () => {
  if (map.value) {
    updatePointsLayer(map.value);
  }
});

watch(selectedId, (id) => {
  if (map.value) {
    updateSelectedFilter(map.value, id ?? null);
  }
});

onBeforeUnmount(() => {
  popupRef.value?.remove();
  map.value?.remove();
});
</script>

<template>
  <div v-if="pipelineStatusMessage === ''" class="processing-overlay">
    <div class="processing-message">
      <span>Rendering map ...</span>
    </div>
  </div>

  <div
    v-if="pipelineStatusMessage === 'in-progress'"
    class="processing-overlay"
  >
    <div class="processing-message">
      <span>The server is currently being updated. Please wait ...</span>
    </div>
  </div>

  <div v-if="pipelineStatusMessage === 'failed'" class="processing-overlay">
    <div class="processing-message">
      <span
        >Server has run into an issue. Please reach out at
        saifulislam84210@gmail.com</span
      >
    </div>
  </div>

  <div v-if="pipelineStatusMessage === 'completed'" class="app" id="appMap">
    <div ref="mapContainer" id="map" class="map-container" />
  </div>
</template>
