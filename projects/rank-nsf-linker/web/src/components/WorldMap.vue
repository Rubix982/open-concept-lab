<template>
  <div id="map" class="map-container"></div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount } from 'vue'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

let map: maplibregl.Map | null = null

onMounted(() => {
  map = new maplibregl.Map({
    container: 'map',
    style: {
      version: 8,
      sources: {
        osm: {
          type: 'raster',
          tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
          tileSize: 256,
          attribution:
            '© <a href="http://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap contributors</a>'
        }
      },
      layers: [
        {
          id: 'osm',
          type: 'raster',
          source: 'osm'
        }
      ]
    },
    center: [7, 47.65],
    zoom: 4.5,
  })

  // Example: Add marker (for later)
  new maplibregl.Marker().setLngLat([7, 47.65]).addTo(map)
})

onBeforeUnmount(() => {
  map?.remove()
})
</script>

<style scoped>
.map-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
}
</style>
