<template>
  <div ref="deckContainer" class="map-container" />
</template>

<script lang="ts" setup>
import { onMounted, ref } from "vue";
import mapboxgl from "mapbox-gl";
import { Deck } from "@deck.gl/core";
import { ScatterplotLayer } from "@deck.gl/layers";

const deckContainer = ref<HTMLElement>();

onMounted(async () => {
  mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;
  const response = await fetch("http://localhost:8080/api/data");
  const apiData = await response.json();

  const map = new mapboxgl.Map({
    container: deckContainer.value!,
    style: "mapbox://styles/mapbox/light-v11",
    center: [-100, 40],
    zoom: 3,
    preserveDrawingBuffer: true,
  });

  const deck = new Deck({
    canvas: map.getCanvas(),
    width: "100%",
    height: "100%",
    initialViewState: {
      longitude: -100,
      latitude: 40,
      zoom: 3,
      pitch: 0,
      bearing: 0,
    },
    controller: true,
    layers: [
      new ScatterplotLayer({
        id: "scatter",
        data: apiData,
        getPosition: (d) => d.position,
        getRadius: (d) => d.size,
        getFillColor: [255, 0, 0],
        radiusMinPixels: 5,
      }),
    ],
  });

  map.on("style.load", () => {
    deck.setProps({ viewState: deck.props.viewState });
  });
});
</script>

<style lang="css" scoped>
.map-container {
  width: 100%;
  height: 100vh;
}
</style>
